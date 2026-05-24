"""Zoomed screenshots of individual charts on the Rice and Aqua tabs."""
from playwright.sync_api import sync_playwright
from pathlib import Path

HTML = Path(r"C:/Users/kd475/RES/BGD_MIX/deploy_repo/index.html").resolve()
OUT  = Path(r"C:/Users/kd475/RES/BGD_MIX/deploy_repo/output")
URL  = HTML.as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width":1440,"height":900}, device_scale_factor=2)
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_timeout(800)

    # Rice tab
    page.click("button[data-tab='t-rice']")
    page.wait_for_timeout(1500)
    # Locate the riceFamilies chart's wrapper
    page.locator("canvas#riceFamilies").screenshot(path=str(OUT/"infodesign_zoom_rice_families.png"))
    page.locator("canvas#riceGrower").screenshot(path=str(OUT/"infodesign_zoom_rice_grower.png"))

    # Aqua tab
    page.click("button[data-tab='t-aqua']")
    page.wait_for_timeout(1500)
    page.locator("canvas#aquaTS").screenshot(path=str(OUT/"infodesign_zoom_aqua_ts.png"))
    page.locator("canvas#aquaPoly").screenshot(path=str(OUT/"infodesign_zoom_aqua_poly.png"))

    # Map tab national
    page.click("button[data-tab='t-map']")
    page.wait_for_timeout(1500)
    page.locator("canvas#natRice").screenshot(path=str(OUT/"infodesign_zoom_nat_rice.png"))
    page.locator("canvas#natAqua").screenshot(path=str(OUT/"infodesign_zoom_nat_aqua.png"))

    browser.close()
print("done")
