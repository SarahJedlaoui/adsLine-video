"""Build the AdsLine promo from ONE continuous voiceover (vo/vo_full.mp3 + vo/lines.json).

Scenes switch at the pauses between script lines: every pause in the narration is found
with ffmpeg silencedetect, then for each line boundary the longest pause near where that
line should end (by its share of the script's characters) is chosen.
If a scene switches in the wrong place, override with the printed times, e.g.
  $env:VO_BOUNDS="5.1,9.8,14.2,19.0,24.3,27.1,32.6"

Usage: $env:VO_DIR="vo"; python video/promo_build.py
"""
import json, os, re, shutil, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
VO_DIR = Path(os.environ.get("VO_DIR", HERE.parent / "vo"))
VO = next(VO_DIR.glob("vo_full.*"))
LINES = json.loads((VO_DIR / "lines.json").read_text())
FPS, DELAY, END_HOLD = 30, 0.5, 2.2     # audio starts 0.5s in; end card holds 2.2s after the last word


def duration(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True).stdout
    return float(out)


def pauses(f):
    err = subprocess.run(["ffmpeg", "-i", str(f), "-af", "silencedetect=noise=-38dB:d=0.15", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(starts, ends))


# Real ad clip for the phone scene: ad.mp4 in the kit root -> adclip/f_0001.jpg ...
AD = HERE.parent / "ad.mp4"
if AD.exists():
    clip = HERE.parent / "adclip"
    shutil.rmtree(clip, ignore_errors=True); clip.mkdir()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(AD), "-vf", "fps=30,scale=540:960",
                    "-q:v", "3", str(clip / "f_%04d.jpg")], check=True)

DUR = duration(VO)
if os.environ.get("VO_BOUNDS"):
    bounds = [float(x) for x in os.environ["VO_BOUNDS"].split(",")]
else:
    sil = [p for p in pauses(VO) if 0.3 < p[0] < DUR - 0.3]
    chars = [len(l) for l in LINES]
    total = sum(chars)
    bounds, last = [], 0.0
    for k in range(1, len(LINES)):
        expected = DUR * sum(chars[:k]) / total
        # sentence-final pauses are longer than comma pauses: among pauses near the
        # expected point, prefer the longest, lightly penalised by distance
        near = [p for p in sil if p[0] > last + 0.8 and abs((p[0] + p[1]) / 2 - expected) < 1.6]
        cands = near or [p for p in sil if p[0] > last + 0.8] or [(expected, expected)]
        s, e = max(cands, key=lambda p: (p[1] - p[0]) - 0.1 * abs((p[0] + p[1]) / 2 - expected))
        bounds.append(round(s + 0.05, 2))          # switch just as the previous line ends
        last = s
assert len(bounds) == len(LINES) - 1, "VO_BOUNDS needs one time per line boundary (7 values)"
print("line boundaries in the voiceover (s):", ",".join(str(b) for b in bounds))

S = [0.0] + [round(DELAY + b, 2) for b in bounds]
TOTAL = round(DELAY + DUR + END_HOLD, 2)
E = S[1:] + [TOTAL]
L = [E[i] - S[i] for i in range(len(S))]
for i, l in enumerate(L):
    if l < 2.5:
        print(f"warning: scene {i} is only {l:.1f}s; check VO_BOUNDS")
print("scene starts", S, "total", TOTAL)


def a(i, off):
    return round(S[i] + off, 2)


HTML = (HERE / "promo_template.html").read_text(encoding="utf-8")
subs = {}
for i in range(len(S)):
    subs[f"S{i}"], subs[f"E{i}"] = S[i], E[i]
    for k, off in enumerate([0.15, 0.5, 0.9, 1.4, 1.8]):
        subs[f"S{i}_{k}"] = a(i, off)
subs["MID1"], subs["MID2"] = a(1, L[1] * 0.55), a(2, L[2] * 0.62)
subs["P0"], subs["P1"], subs["P2"] = a(6, L[6] * 0.33), a(6, L[6] * 0.55), a(6, L[6] * 0.74)
for k, v in subs.items():
    HTML = HTML.replace("{{" + k + "}}", str(v))
(HERE / "promo.html").write_text(HTML, encoding="utf-8")

frames = HERE / "frames"
shutil.rmtree(frames, ignore_errors=True)
frames.mkdir()
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto((HERE / "promo.html").as_uri())
    pg.wait_for_timeout(500)
    for f in range(int(TOTAL * FPS)):
        pg.evaluate(f"render({f / FPS})")
        pg.screenshot(path=str(frames / f"f_{f:05d}.jpg"), type="jpeg", quality=94)
    b.close()

# One continuous take: gentle fades, loudness to -16 LUFS (web standard), no compression pumping.
ms = int(DELAY * 1000)
audio = (f"[0:a]aresample=48000,afade=t=in:d=0.04,adelay={ms}|{ms},highpass=f=70,"
         f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=whole_dur={TOTAL}[out]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(VO), "-filter_complex", audio,
                "-map", "[out]", "-t", str(TOTAL), "-ac", "2", str(HERE / "vo_track.wav")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f_%05d.jpg"),
                "-i", str(HERE / "vo_track.wav"), "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL),
                "-movflags", "+faststart", str(HERE / "adsline-promo-v4.mp4")], check=True)
print("done ->", HERE / "adsline-promo-v4.mp4")
