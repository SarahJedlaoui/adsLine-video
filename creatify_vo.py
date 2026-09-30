"""AdsLine promo voiceover with Creatify TTS: one continuous take, not 8 clips.

Why one take: separate clips each start and stop cold, so the read sounds chopped.
A single request lets the voice carry its intonation from line to line, like a person
reading the whole script. promo_build.py then finds the pauses and times each scene to them.

Run on your machine (keys stay in the terminal session):
  $env:CREATIFY_API_ID="..."; $env:CREATIFY_API_KEY="..."     (PowerShell)
  python creatify_vo.py audition            # same line in up to 6 female English voices
  python creatify_vo.py generate <accent_id>

Outputs in ./vo/: audition_*.mp3, vo_full.mp3, lines.json
"""
import os, sys, time, json, re
from pathlib import Path
import requests

API = "https://api.creatify.ai/api"
H = {"X-API-ID": os.environ["CREATIFY_API_ID"],
     "X-API-KEY": os.environ["CREATIFY_API_KEY"],
     "Content-Type": "application/json"}
OUT = Path("vo")

# Written to be spoken: contractions, commas for breath, one idea per line.
LINES = [
    "Most AI video tools wait for you to paste a link and ask for an ad.",
    "AdsLine works the other way around. It watches your Shopify store.",
    "When a product comes back in stock, or a new one arrives, the ad is already drafted.",
    "Every ad is built from your real product photos, so shoppers see exactly what they'll get.",
    "It learns your brand the moment you install, so every ad looks like your store.",
    "Let it run on autopilot, or review each draft yourself.",
    "Every ad lands in one gallery, ready to launch.",
    "AdsLine. Video ads on autopilot, for your Shopify store. Try it free on the Shopify App Store.",
]
SAMPLE = "AdsLine works the other way around. It watches your Shopify store. When a product comes back in stock, the ad is already drafted."


def _voices():
    r = requests.get(f"{API}/voices/", headers=H, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("results", data) if isinstance(data, dict) else data


def _tts(script, name):
    r = requests.post(f"{API}/text_to_speech/", headers=H, timeout=30,
                      json={"script": script, "accent": name[1], "name": name[0]})
    r.raise_for_status()
    job = r.json()["id"]
    while True:
        item = requests.get(f"{API}/text_to_speech/{job}/", headers=H, timeout=30).json()
        if item.get("status") == "done" and item.get("output"):
            return requests.get(item["output"], timeout=120).content
        if item.get("status") in ("failed", "error"):
            sys.exit(f"{name[0]} failed: {json.dumps(item)[:500]}")
        time.sleep(3)


def voices():
    for v in _voices():
        for a in v.get("accents", []):
            print(f"{a.get('id')}  {v.get('name')!s:<20} {v.get('gender')!s:<8} "
                  f"{(a.get('accent_name') or a.get('name'))!s:<18} {a.get('preview_url') or ''}")


def audition():
    """Render the same short passage in up to 6 female English voices so you can compare by ear."""
    OUT.mkdir(exist_ok=True)
    picks = []
    for v in _voices():
        if not str(v.get("gender", "")).lower().startswith("f"):
            continue
        for a in v.get("accents", []):
            label = str(a.get("accent_name") or a.get("name") or "")
            if re.search(r"americ|\bus\b|english|british|austral", label, re.I):
                picks.append((f"{v.get('name')}_{label}", a["id"]))
                break
        if len(picks) == 6:
            break
    if not picks:
        v = _voices()[:1]
        sys.exit(f"No female English voices matched. First voice record, to adjust the filter: {json.dumps(v)[:800]}")
    for label, accent in picks:
        safe = re.sub(r"[^A-Za-z0-9]+", "-", label).strip("-")
        (OUT / f"audition_{safe}_{accent}.mp3").write_bytes(_tts(SAMPLE, (f"audition-{safe}", accent)))
        print(f"saved vo/audition_{safe}_{accent}.mp3")
    print("\nListen, then: python creatify_vo.py generate <accent id from the file name>")


def generate(accent):
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("vo_[0-9].*"):
        old.unlink()                          # old per-line clips would confuse the build
    script = "\n\n".join(LINES)               # paragraph breaks = slightly longer breaths between scenes
    (OUT / "vo_full.mp3").write_bytes(_tts(script, ("adsline-promo-full", accent)))
    (OUT / "lines.json").write_text(json.dumps(LINES, indent=2))
    print("saved vo/vo_full.mp3 and vo/lines.json -> now run: python video/promo_build.py")


if __name__ == "__main__":
    cmd = sys.argv[1:] or [""]
    if cmd[0] == "voices":
        voices()
    elif cmd[0] == "audition":
        audition()
    elif cmd[0] == "generate" and len(cmd) == 2:
        generate(cmd[1])
    else:
        print(__doc__)
