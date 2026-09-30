"""Render AdsLine Shopify listing images at exactly 1600x900.
Swap files in crops/ (ideally captured at 2x) and re-run: python3 build.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

CSS = """
@font-face{font-family:Brico;src:url(fonts/bricolage-grotesque-latin-800-normal.woff2);font-weight:800}
@font-face{font-family:Brico;src:url(fonts/bricolage-grotesque-latin-600-normal.woff2);font-weight:600}
@font-face{font-family:Inter;src:url(fonts/inter-latin-500-normal.woff2);font-weight:500}
@font-face{font-family:Inter;src:url(fonts/inter-latin-700-normal.woff2);font-weight:700}
:root{--paper:#F2F4FB;--ink:#101634;--muted:#565E7E;--blue:#2F5BFF;--violet:#6B3BEA;--cyan:#21C4EE}
*{margin:0;box-sizing:border-box}
html,body{width:1600px;height:900px;overflow:hidden;background:var(--paper);font-family:Inter,sans-serif;color:var(--ink)}
.copy{position:absolute;left:96px;top:0;bottom:0;width:560px;display:flex;flex-direction:column;justify-content:center;gap:28px}
h1{font-family:Brico;font-weight:800;font-size:78px;line-height:.98;letter-spacing:-.025em}
.sub{font-size:26px;line-height:1.4;color:var(--muted);font-weight:500;max-width:460px}
.mark{position:absolute;left:96px;bottom:64px;display:flex;align-items:center;gap:6px;font-family:Inter;font-weight:700;font-size:22px;color:var(--blue)}
.mark b{background:var(--blue);color:#fff;border-radius:8px;padding:2px 8px}
.slab{position:absolute;left:700px;right:-40px;top:56px;bottom:56px;border-radius:40px 0 0 40px;overflow:hidden}
.slab .bg{position:absolute;inset:-80px;background-size:cover;background-position:center;filter:blur(46px) saturate(1.35)}
.slab .tint{position:absolute;inset:0;background:linear-gradient(135deg,rgba(47,91,255,.72),rgba(107,59,234,.62))}
.ui{position:absolute;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 34px 70px -18px rgba(16,22,52,.55),0 0 0 1px rgba(16,22,52,.06)}
.ui img{display:block;width:100%;height:auto}
.link{position:absolute;border-left:3px dashed rgba(255,255,255,.85);}
.tag{position:absolute;font-family:Inter;font-weight:700;font-size:19px;color:#fff;background:rgba(16,22,52,.45);padding:8px 14px;border-radius:999px;backdrop-filter:blur(6px)}
.full{position:absolute;inset:0;overflow:hidden}
.full .bg{position:absolute;inset:-80px;background-size:cover;background-position:center;filter:blur(60px) saturate(1.3)}
.full .tint{position:absolute;inset:0;background:linear-gradient(140deg,rgba(33,196,238,.55),rgba(47,91,255,.78) 45%,rgba(107,59,234,.85))}
.hero{position:absolute;left:0;right:0;top:112px;text-align:center;color:#fff;font-size:84px;letter-spacing:-.03em}
.markw{position:absolute;left:56px;top:40px;display:flex;align-items:center;gap:6px;font-weight:700;font-size:22px;color:#fff}
.markw b{background:#fff;color:var(--blue);border-radius:8px;padding:2px 8px}
.win{border-radius:18px 18px 0 0}
.win .bar{height:34px;background:#F4F5F9;border-bottom:1px solid #E6E8F0;display:flex;gap:8px;align-items:center;padding-left:16px}
.win .bar i{width:11px;height:11px;border-radius:50%;background:#D5D8E3}
.phone{position:absolute;background:#0B0920;border-radius:48px;padding:11px;box-shadow:0 40px 90px -20px rgba(8,6,30,.7)}
.phone .scr{border-radius:38px;overflow:hidden;aspect-ratio:9/16;background:#000}
.phone .scr img{width:100%;height:100%;object-fit:cover;display:block}
.phone .notch{position:absolute;top:22px;left:50%;transform:translateX(-50%);width:84px;height:24px;border-radius:14px;background:#0B0920}
.float{position:absolute;background:#fff;border-radius:16px;padding:14px 18px;box-shadow:0 24px 50px -14px rgba(8,6,30,.55)}
.float img{display:block;width:100%}
.float .lbl{font-weight:700;font-size:15px;color:var(--muted);margin:0 0 10px 2px}
.dark{position:absolute;inset:0;background:radial-gradient(600px 520px at 72% 48%,rgba(124,77,255,.55),transparent 70%),radial-gradient(700px 500px at 8% 100%,rgba(47,91,255,.45),transparent 70%),#150F45}
.icon{width:120px;height:120px;border-radius:28px;background:var(--blue);color:#fff;display:grid;place-items:center;font-family:Inter;font-weight:700;font-size:40px;box-shadow:0 0 0 6px rgba(255,255,255,.08)}
.brandlock{position:absolute;left:110px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:30px}
.brandlock .row{display:flex;align-items:center;gap:30px}
.brandlock h1{color:#fff;font-size:118px;letter-spacing:-.035em}
.brandlock p{color:#C9CCFF;font-size:36px;font-weight:500}
.bright{position:absolute;inset:0;background:radial-gradient(700px 600px at 0% 0%,rgba(33,196,238,.55),transparent 65%),linear-gradient(125deg,#2F5BFF 30%,#5B3BEA)}
.bcopy{position:absolute;left:96px;top:0;bottom:0;width:600px;display:flex;flex-direction:column;justify-content:center;gap:34px}
.bcopy h1{color:#fff;font-size:88px;line-height:.98;letter-spacing:-.03em}
"""

def page(body, bg=None):
    slab = ""
    if bg:
        slab = f'<div class="slab"><div class="bg" style="background-image:url({bg})"></div><div class="tint"></div></div>'
    return f"<!doctype html><html><head><meta charset=utf-8><style>{CSS}</style></head><body>{slab}{body}</body></html>"

def copy(h1, sub):
    return f'<div class="copy"><h1>{h1}</h1><p class="sub">{sub}</p></div><div class="mark"><b>Ads</b>Line</div>'

IMAGES = {
    # Feature image: the output itself, one focal point.
    "01_feature": page(
        copy("Video ads made from your own products", "On brand, ready to review, no shoot needed.")
        + "".join(
            f'<div class="ui" style="left:{x}px;top:{y}px;width:250px;border-radius:24px"><img src="crops/reel{i}.png"></div>'
            for i, x, y in [(0, 770, 170), (1, 1048, 270), (2, 1326, 140)]
        ),
        bg="crops/reel0.png",
    ),
    "02_gallery": page(
        copy("Every ad you generate, in one place", "Preview each video, see how well it fits your brand, and mark it launched.")
        + '<div class="ui" style="left:745px;top:191px;width:822px"><img src="crops/gallery_row.png"></div>',
        bg="crops/reel2.png",
    ),
    "03_store_watches": page(
        copy("Restocks and launches turn into ads", "Turn on a watch once. When a product comes back or goes live, a drafted ad is waiting for you.")
        + '<div class="ui" style="left:745px;top:320px;width:630px"><img src="crops/watches.png"></div>'
        + '<div class="link" style="left:1375px;top:407px;width:30px;height:0;border-left:0;border-top:3px dashed rgba(255,255,255,.85)"></div>'
        + '<div class="tag" style="left:745px;top:500px">Heaven’s Gate Tee came back in stock</div>'
        + '<div class="ui" style="left:1405px;top:215px;width:176px;border-radius:16px"><img src="crops/card_restock.png"></div>',
        bg="crops/reel3.png",
    ),
    "04_brand": page(
        copy("Learns your brand the moment you install", "Products, palette, imagery, and voice, read straight from your store.")
        + '<div class="ui" style="left:745px;top:340px;width:822px;padding:18px 0 10px"><img src="crops/brand_card.png"></div>',
        bg="crops/reel1.png",
    ),
    "05_suggested": page(
        copy("See why each ad is suggested", "Every draft shows what changed in your store and the angle it takes. Generate it or dismiss it.")
        + '<div class="ui" style="left:745px;top:292px;width:822px"><img src="crops/suggested.png"></div>',
        bg="crops/reel0.png",
    ),
    "06_studio": page(
        copy("Start from any product URL", "Choose an AI presenter, a product video, scripts only, or upload your own footage.")
        + '<div class="ui" style="left:745px;top:301px;width:823px"><img src="crops/studio.png"></div>',
        bg="crops/reel1.png",
    ),
    # Main feature image: whole app in one frame, full-bleed brand panel.
    "00_main": page(
        '<div class="full"><div class="bg" style="background-image:url(crops/reel0.png)"></div><div class="tint"></div></div>'
        '<div class="markw"><b>Ads</b>Line</div>'
        '<h1 class="hero">Video ads that keep up with your store</h1>'
        '<div class="ui win" style="left:222px;top:262px;width:1156px"><div class="bar"><i></i><i></i><i></i></div><img src="crops/app_window.png"></div>'
    ),
    # Attempt A: brand lockup + one hero output + one floating UI chip (Smart Pricing pattern)
    "00_main_a": page(
        '<div class="dark"></div>'
        '<div class="brandlock"><div class="row"><div class="icon">Ads</div><h1>AdsLine</h1></div><p>AI video ads from your own products</p></div>'
        '<div class="phone" style="left:1060px;top:140px;width:300px"><div class="scr"><img src="crops/screen0.png"></div><div class="notch"></div></div>'
        '<div class="float" style="left:830px;top:640px;width:520px"><img src="crops/chip_restock.png"></div>'
    ),
    # Attempt B: headline + catalog -> ad story (AppLovin pattern)
    "00_main_b": page(
        '<div class="bright"></div>'
        '<div class="bcopy"><div class="markw" style="position:static"><b>Ads</b>Line</div><h1>Your catalog, turned into video ads</h1></div>'
        '<div class="float" style="left:740px;top:225px;width:500px"><div class="lbl">Your Shopify products</div><img src="crops/catalog.png"></div>'
        '<div class="phone" style="left:1200px;top:175px;width:290px"><div class="scr"><img src="crops/screen2.png"></div><div class="notch"></div></div>'
        '<div class="float" style="left:720px;top:640px;width:640px;padding:10px 12px"><img src="crops/chip_watch.png"></div>'
    ),
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1)
    for name, html in IMAGES.items():
        f = ROOT / f"{name}.html"
        f.write_text(html)
        pg.goto(f.as_uri())
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    b.close()
print("done")
