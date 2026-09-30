"""Listing images v2 (autopilot / product-faithful positioning). Reuses CSS + helpers from build.py.
Run: python3 build_v2.py  -> out/v2_*.png (1600x900)"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
src = (ROOT / "build.py").read_text(encoding="utf-8")
exec(src.split("IMAGES = {")[0])          # CSS, page(), copy(), ROOT, OUT

EXTRA = """
.lbl2{position:absolute;font-family:Inter;font-weight:700;font-size:20px;color:#fff;background:rgba(16,22,52,.45);padding:8px 16px;border-radius:999px}
.arrow{position:absolute;height:4px;background:rgba(255,255,255,.9);border-radius:2px}
.arrow:after{content:"";position:absolute;right:-4px;top:-9px;border-left:18px solid rgba(255,255,255,.9);border-top:11px solid transparent;border-bottom:11px solid transparent}
.stack img{margin:0 auto}
"""

def p(body, bg=None):
    return page(body, bg).replace("</style>", EXTRA + "</style>")

PHONE = lambda l, t, w, img: (f'<div class="phone" style="left:{l}px;top:{t}px;width:{w}px"><div class="scr">'
                              f'<img src="{img}"></div><div class="notch"></div></div>')

IMAGES = {
    "v2_00_feature": p(
        '<div class="bright"></div>'
        '<div class="bcopy"><div class="markw" style="position:static"><b>Ads</b>Line</div>'
        '<h1>Video ads on autopilot</h1><p class="sub" style="color:#E4E7FF;max-width:520px">Your inventory moves. Your ads follow.</p></div>'
        '<div class="float" style="left:740px;top:215px;width:360px"><div class="lbl">Your Shopify products</div><img src="crops/n_thumbs.png"></div>'
        + PHONE(1200, 150, 300, "crops/n_adframe.jpg") +
        '<div class="float" style="left:720px;top:640px;width:600px;padding:8px 10px"><img src="crops/n_chip_launch.png"></div>'
    ),
    "v2_01_autopilot": p(
        copy("Restocks and new arrivals become ads", "No prompts. AdsLine drafts the ad the moment your inventory moves.")
        + '<div class="ui" style="left:745px;top:300px;width:600px"><img src="crops/n_watches.png"></div>'
        + '<div class="link" style="left:1345px;top:497px;width:45px;height:0;border-left:0;border-top:3px dashed rgba(255,255,255,.85)"></div>'
        + '<div class="ui" style="left:1390px;top:190px;width:190px;border-radius:16px"><img src="crops/n_card_launch.png"></div>',
        bg="crops/vscreen0.png",
    ),
    "v2_02_faithful": p(
        copy("Ads that never distort your product", "Every ad is built from your own product photos, so shoppers get exactly what they see.")
        + '<div class="lbl2" style="left:790px;top:170px">Your product photo</div>'
        + '<div class="ui" style="left:760px;top:230px;width:380px;border-radius:24px"><img src="crops/n_packshot.png"></div>'
        + '<div class="arrow" style="left:1170px;top:448px;width:70px"></div>'
        + '<div class="lbl2" style="left:1300px;top:95px">Your ad</div>'
        + PHONE(1270, 150, 300, "crops/n_adframe.jpg"),
        bg="crops/vscreen0.png",
    ),
    "v2_03_brand": p(
        copy("On brand from day one", "AdsLine learns your brand the moment you install. No setup.")
        + '<div class="ui stack" style="left:790px;top:250px;width:740px;padding:30px 34px">'
          '<img src="crops/n_tags.png" style="width:420px;margin:0 0 22px 0">'
          '<img src="crops/n_thumbs.png" style="width:420px;margin:0 0 26px 0">'
          '<img src="crops/n_palette.png" style="width:672px;margin:0"></div>',
        bg="crops/vscreen1.png",
    ),
    "v2_04_control": p(
        copy("Full autopilot, or approve each one", "Let AdsLine run on its own, or review every draft before it's made.")
        + '<div class="ui" style="left:1180px;top:130px;width:300px;padding:10px 14px;border-radius:999px"><img src="crops/n_autopilot.png"></div>'
        + '<div class="ring" style="left:1170px;top:120px;width:320px;height:78px"></div>'
        + '<div class="ui" style="left:745px;top:290px;width:820px;padding:6px 0 14px">'
          '<img src="crops/n_sug_head.png"><img src="crops/n_sug_copy.png">'
          '<img src="crops/n_sug_btns.png" style="width:256px;margin-left:0"></div>',
        bg="crops/vscreen3.png",
    ),
    "v2_05_gallery": p(
        copy("Every ad, ready to launch", "Every creative AdsLine makes, in one gallery.")
        + '<div class="ui" style="left:745px;top:190px;width:824px"><img src="crops/n_gallery.png"></div>',
        bg="crops/vscreen2.png",
    ),
}

EXTRA_CSS_FROM_TEMPLATE = ".ring{position:absolute;border:4px solid #fff;border-radius:999px;box-shadow:0 0 0 6px rgba(33,196,238,.45)}"
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1)
    for name, html in IMAGES.items():
        html = html.replace("</style>", EXTRA_CSS_FROM_TEMPLATE + "</style>")
        f = ROOT / f"{name}.html"
        f.write_text(html, encoding="utf-8")
        pg.goto(f.as_uri()); pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f"{name}.png"))
    b.close()
print("done")
