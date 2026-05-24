"""
Capture each line chart on the MIXTAPE dashboard at 1440x900 for editorial audit.
Each shot crops to the chart's containing .chart-wrap so the reviewer sees what
the reader sees - title, legend, axis, gridlines, lines - and nothing else.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "file:///C:/Users/kd475/RES/BGD_MIX/deploy_repo/index.html"
OUT = Path("C:/Users/kd475/RES/BGD_MIX/deploy_repo/output")

# (tab_id, canvas_id, output_filename, label)
shots = [
    ("t-map",  "natRice",      "audit_charts_01_map_natRice.png",       "Tab 1 / Rice variety families (national, weighted)"),
    ("t-map",  "natAqua",      "audit_charts_02_map_natAqua.png",       "Tab 1 / Aquaculture indicators (national, weighted)"),
    ("t-rice", "riceFamilies", "audit_charts_03_rice_riceFamilies.png", "Tab 2 / Variety families, national weighted prevalence"),
    ("t-rice", "riceGrower",   "audit_charts_04_rice_riceGrower.png",   "Tab 2 / Any rice grower"),
    ("t-aqua", "aquaTS",       "audit_charts_05_aqua_aquaTS.png",       "Tab 3 / Aquaculture indicators, national weighted prevalence"),
    ("t-aqua", "aquaPoly",     "audit_charts_06_aqua_aquaPoly.png",     "Tab 3 / WorldFish-linked practices"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              device_scale_factor=2)
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2500)

    current_tab = None
    for tab_id, canvas_id, fname, label in shots:
        if tab_id != current_tab:
            page.evaluate(f"""() => {{
              const btn = document.querySelector('button[data-tab="{tab_id}"]');
              if (btn) btn.click();
            }}""")
            page.wait_for_timeout(1800)
            current_tab = tab_id

        # find the .chart-wrap that contains this canvas
        canvas = page.locator(f"#{canvas_id}").first
        canvas.scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        wrap = page.evaluate_handle(
            f"document.getElementById('{canvas_id}').closest('.chart-wrap')"
        )
        # clip to the wrap's bounding box
        box = page.evaluate("""el => {
            const r = el.getBoundingClientRect();
            return {x: r.left, y: r.top, w: r.width, h: r.height};
        }""", wrap)
        clip = {"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]}
        page.screenshot(path=str(OUT / fname), clip=clip)
        print(f"wrote {fname}  ({label})")

    # also save a full-page shot of each tab so we can see context
    for tab_id, fname in [
        ("t-map",  "audit_charts_tab1_full.png"),
        ("t-rice", "audit_charts_tab2_full.png"),
        ("t-aqua", "audit_charts_tab3_full.png"),
        ("t-spia", "audit_charts_tab4_full.png"),
        ("t-mech", "audit_charts_tab5_full.png"),
    ]:
        page.evaluate(f"""() => {{
          const btn = document.querySelector('button[data-tab="{tab_id}"]');
          if (btn) btn.click();
        }}""")
        page.wait_for_timeout(1800)
        page.screenshot(path=str(OUT / fname), full_page=False)
        print(f"wrote {fname}  (full viewport)")

    browser.close()
