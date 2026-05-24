"""Take screenshots of the MIXTAPE dashboard for info-design review."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

HTML = Path(r"C:/Users/kd475/RES/BGD_MIX/deploy_repo/index.html").resolve()
OUT  = Path(r"C:/Users/kd475/RES/BGD_MIX/deploy_repo/output")
URL  = HTML.as_uri()

VIEWPORTS = [
    ("desktop", 1440, 900),
    ("tablet",  1024, 768),
    ("mobile",   390, 844),
]

# Tabs to capture
TABS = [
    ("rice", "t-rice"),
    ("aqua", "t-aqua"),
    ("map",  "t-map"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, w, h in VIEWPORTS:
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(URL)
        # First, capture map tab full page (default)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / f"infodesign_{name}_map.png"), full_page=False)

        # Rice tab
        page.click("button[data-tab='t-rice']")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / f"infodesign_{name}_rice.png"), full_page=False)
        # Full page rice
        page.screenshot(path=str(OUT / f"infodesign_{name}_rice_full.png"), full_page=True)

        # Aqua tab
        page.click("button[data-tab='t-aqua']")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / f"infodesign_{name}_aqua.png"), full_page=False)
        page.screenshot(path=str(OUT / f"infodesign_{name}_aqua_full.png"), full_page=True)

        ctx.close()
    browser.close()
print("done")
