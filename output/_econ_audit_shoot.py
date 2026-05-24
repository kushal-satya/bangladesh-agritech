from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "file:///C:/Users/kd475/RES/BGD_MIX/deploy_repo/index.html"
OUT = Path("C:/Users/kd475/RES/BGD_MIX/deploy_repo/output")

tabs = [
    ("t-map",  "econ_audit_01_map.png"),
    ("t-rice", "econ_audit_02_rice.png"),
    ("t-aqua", "econ_audit_03_aqua.png"),
    ("t-spia", "econ_audit_04_spia.png"),
    ("t-mech", "econ_audit_05_mech.png"),
    ("t-tech", "econ_audit_06_tech.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2500)
    for tab_id, fname in tabs:
        page.evaluate(f"""() => {{
          const btn = document.querySelector('button[data-tab="{tab_id}"]');
          if (btn) btn.click();
          window.scrollTo(0,0);
        }}""")
        page.wait_for_timeout(1500)
        # full-page screenshot so we capture every chart
        page.screenshot(path=str(OUT / fname), full_page=True)
        print("wrote", fname)
    browser.close()
