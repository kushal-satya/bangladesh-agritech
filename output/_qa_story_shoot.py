from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "file:///C:/Users/kd475/RES/BGD_MIX/deploy_repo/index.html"
OUT = Path("C:/Users/kd475/RES/BGD_MIX/deploy_repo/output")

tabs = [
    ("t-map",  "qa_story_01_map.png"),
    ("t-rice", "qa_story_02_rice.png"),
    ("t-aqua", "qa_story_03_aqua.png"),
    ("t-spia", "qa_story_04_spia.png"),
    ("t-mech", "qa_story_05_mech.png"),
    ("t-tech", "qa_story_06_tech.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1600, "height": 1100})
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2500)
    for tab_id, fname in tabs:
        page.evaluate(f"""() => {{
          const btn = document.querySelector('button[data-tab="{tab_id}"]');
          if (btn) btn.click();
        }}""")
        page.wait_for_timeout(1800)
        page.screenshot(path=str(OUT / fname), full_page=False)
        print("wrote", fname)
    browser.close()
