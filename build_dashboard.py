"""Build the MIXTAPE dashboard.

Reads the data files in data/, the text and colors in content.toml, and
writes a fully self-contained index.html next to this script. Deploys on
GitHub Pages as-is.

To change any wording or color on the dashboard, edit content.toml and
rerun this script.
"""
import json, os, base64, tomllib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

with open(os.path.join(ROOT, "content.toml"), "rb") as fh:
    C = tomllib.load(fh)
THEME = C["theme"]

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)

GEO  = load("mixtape_geo.json")
RICE = load("mixtape_rice.json")
AQUA = load("mixtape_aqua.json")
MECH = load("mixtape_mech.json")
DNA  = load("mixtape_dna.json")
NAT  = load("mixtape_national.json")
SUM  = load("mixtape_summary.json")
TECH = load("mixtape_technologies.json")

# embed logo as base64 so the HTML is truly single-file
with open(os.path.join(DATA, "MIXTAPE-logo-800x800.png"), "rb") as fh:
    LOGO_B64 = "data:image/png;base64," + base64.b64encode(fh.read()).decode()

def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

# Text bundle handed to the page's JavaScript (labels, glosses, chart titles)
TXT_JS = {
    "labels":      C["labels"],
    "map_catalog": C["map_catalog"],
    "glosses":     C["glosses"],
    "charts":      C["charts"],
    "kpi":         C["kpi"],
    "map":         {k: C["map"][k] for k in
                    ("info_title", "info_hover_hint", "legend_units", "gloss_suffix",
                     "kpi_national", "kpi_change", "kpi_highest", "kpi_lowest")},
    "misc":        C["misc"],
    "tables":      {"rice_1": C["rice"]["top_table_1"], "rice_2": C["rice"]["top_table_2"],
                    "aqua_1": C["aqua"]["top_table_1"], "aqua_2": C["aqua"]["top_table_2"]},
    "tech":        {k: C["tech"][k] for k in
                    ("primary_ref_eyebrow", "report_link_label", "github_link_label", "no_match")},
}

HTML_TMPL = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>__PAGE_TITLE__</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="icon" type="image/png" href="__LOGO__"/>
<style>
  :root{
    /* All values come from the [theme] section of content.toml. */
__ROOT_VARS__
    --accent:var(--rice);
    --accent-dark:var(--rice-dark);
    --accent-soft:var(--rice-soft);
  }
  body.cat-rice{--accent:var(--rice);--accent-dark:var(--rice-dark);--accent-soft:var(--rice-soft)}
  body.cat-aqua{--accent:var(--aqua);--accent-dark:var(--aqua-dark);--accent-soft:var(--aqua-soft)}
  body.cat-mech{--accent:var(--mech);--accent-dark:var(--mech-dark);--accent-soft:var(--mech-soft)}
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Helvetica,Arial,system-ui,sans-serif;
      line-height:1.55;-webkit-font-smoothing:antialiased;font-size:14.5px}

  /* Two column layout: sticky side rail, main column */
  .layout{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh;
      max-width:1500px;margin:0 auto}
  @media (max-width:980px){.layout{grid-template-columns:1fr}}

  /* Side rail */
  aside.rail{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;
      padding:30px 22px 24px;border-right:1px solid var(--line);background:var(--rail-bg)}
  aside.rail::-webkit-scrollbar{width:6px}
  aside.rail::-webkit-scrollbar-thumb{background:#d8dad4;border-radius:3px}
  @media (max-width:980px){
    aside.rail{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);
        padding:16px 18px}
  }
  .brand{display:flex;align-items:center;gap:12px;margin-bottom:24px}
  .brand img{width:40px;height:40px;background:transparent;flex-shrink:0;object-fit:contain;
      mix-blend-mode:multiply}
  .brand .name{display:flex;flex-direction:column;gap:1px;min-width:0}
  .brand .name .acro{font-size:14px;font-weight:700;color:var(--ink);letter-spacing:.02em;line-height:1}
  .brand .name .full{font-size:10.5px;color:var(--mute);line-height:1.35;margin-top:3px}

  /* Side nav */
  nav.tabs{display:flex;flex-direction:column;gap:1px;margin:0 0 22px;border:0}
  nav.tabs button{font-family:inherit;background:transparent;border:0;padding:9px 12px;font-size:13px;
      color:var(--text);cursor:pointer;font-weight:500;text-align:left;letter-spacing:-0.003em;
      border-left:2px solid transparent;border-radius:0;
      transition:background .12s ease,color .12s ease;
      display:flex;align-items:center;gap:10px}
  nav.tabs button:hover{background:var(--tint);color:var(--ink)}
  nav.tabs button.on{color:var(--accent);background:var(--accent-soft);border-left-color:var(--accent);
      font-weight:600}
  nav.tabs button .num{font-size:11px;color:var(--mute);font-variant-numeric:tabular-nums;
      min-width:14px;text-align:right;flex-shrink:0}
  nav.tabs button.on .num{color:var(--accent)}
  @media (max-width:980px){
    aside.rail{padding:14px 16px 0;position:relative}
    nav.tabs{flex-direction:row;overflow-x:auto;gap:0;margin:6px -16px 0;padding:0 16px 0 16px;
        scrollbar-width:none;-webkit-overflow-scrolling:touch}
    nav.tabs::-webkit-scrollbar{display:none}
    nav.tabs button{border-left:0;border-bottom:2px solid transparent;border-radius:0;white-space:nowrap;
        padding:13px 16px;min-height:44px;background:transparent;flex-shrink:0}
    nav.tabs button.on{background:transparent;border-bottom-color:var(--accent)}
    /* Right-edge fade hints at more tabs to scroll */
    aside.rail::after{content:"";position:absolute;right:0;bottom:0;width:36px;height:48px;pointer-events:none;
        background:linear-gradient(to right,transparent,var(--rail-bg))}
  }

  /* Rail meta and footer */
  .rail-meta{font-size:11.5px;color:var(--mute);margin-top:6px;padding-top:18px;border-top:1px solid var(--line)}
  .rail-meta .lbl{font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:600;
      color:var(--mute);margin-bottom:8px}
  .rail-meta .row{display:flex;justify-content:space-between;align-items:baseline;padding:3px 0;
      font-variant-numeric:tabular-nums}
  .rail-meta .row span:first-child{color:var(--text);font-weight:500}
  .rail-meta .row span:last-child{color:var(--ink);font-weight:600}
  .rail-foot{margin-top:18px;padding-top:14px;border-top:1px solid var(--line);font-size:11.5px;
      color:var(--mute);line-height:1.55}
  .rail-foot a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--line2)}
  .rail-foot a:hover{border-bottom-color:var(--accent)}
  @media (max-width:980px){.rail-meta,.rail-foot{display:none}}

  /* Main column */
  main.wrap{padding:36px 38px 80px;max-width:1180px;width:100%;min-width:0}
  @media (max-width:980px){main.wrap{padding:18px 16px 48px}}

  /* Title block */
  header.title{padding-bottom:18px;margin-bottom:22px;border-bottom:1px solid var(--line)}
  header.title .eyebrow{font-size:10.5px;color:var(--mute);letter-spacing:.14em;text-transform:uppercase;
      font-weight:600;margin-bottom:8px}
  header.title h1{margin:0;font-size:22px;line-height:1.3;letter-spacing:-0.015em;color:var(--ink);
      font-weight:600;max-width:820px}
  header.title .meta{margin-top:12px;font-size:12px;color:var(--mute);
      display:flex;flex-wrap:wrap;gap:4px 18px;font-variant-numeric:tabular-nums}
  header.title .meta b{font-weight:600;color:var(--ink)}
  header.title .disclaimer{margin-top:10px;font-size:11.5px;color:var(--mute);max-width:880px;line-height:1.55;
      padding:8px 12px;background:var(--tint);border-left:2px solid var(--line2)}
  header.title .disclaimer a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--line2)}
  header.title .disclaimer a:hover{border-bottom-color:var(--accent)}
  @media (max-width:680px){
    header.title{padding-bottom:14px;margin-bottom:16px}
    header.title .eyebrow{font-size:9.5px;letter-spacing:.12em;margin-bottom:6px}
    header.title h1{font-size:17px;line-height:1.28}
    header.title .meta{margin-top:8px;font-size:11.5px;gap:2px 14px}
  }

  /* Brief: full text on desktop, collapsible on mobile */
  .brief{padding:0;margin:0 0 24px;font-size:13.5px;color:var(--text);max-width:920px;line-height:1.65}
  .brief b{color:var(--ink);font-weight:600}
  @media (max-width:680px){
    .brief{font-size:12.5px;line-height:1.55;margin-bottom:18px;
        max-height:5.5em;overflow:hidden;position:relative;cursor:pointer}
    .brief::after{content:"Read more";position:absolute;bottom:0;right:0;
        background:linear-gradient(to right,transparent 0,var(--bg) 36%);padding:0 0 0 28px;
        color:var(--accent);font-weight:600;font-size:11.5px}
    .brief.open{max-height:none;cursor:default}
    .brief.open::after{display:none}
  }

  .tab{display:none}
  .tab.on{display:block}

  /* Section headings */
  h2.section{font-size:22px;color:var(--ink);margin:32px 0 6px;letter-spacing:-0.015em;font-weight:600}
  h3.sub{font-size:14.5px;color:var(--ink);margin:22px 0 6px;font-weight:600;letter-spacing:-0.005em}
  p.lede{color:var(--text);font-size:13.5px;margin:4px 0 14px;max-width:880px;line-height:1.6}
  p.note{font-size:12px;color:var(--mute);margin:6px 0 18px}
  @media (max-width:680px){
    h2.section{font-size:17px;margin:24px 0 6px}
    h3.sub{font-size:13.5px;margin:18px 0 6px}
    p.lede{font-size:12.5px}
  }

  /* ------- Layout ------- */
  .row{display:grid;gap:18px}
  .row-2{grid-template-columns:1fr 1fr}
  .row-3{grid-template-columns:1fr 1fr 1fr}
  @media (max-width:920px){.row-2,.row-3{grid-template-columns:1fr}}

  /* ------- Cards & KPIs ------- */
  .card{background:var(--panel);border:1px solid var(--line);padding:14px 16px}
  .card h4{margin:0 0 6px 0;font-size:11px;color:var(--mute);font-weight:600;letter-spacing:.06em;
      text-transform:uppercase}
  .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin:14px 0 24px;
      border-top:1px solid var(--line);border-left:1px solid var(--line);background:var(--panel)}
  @media (max-width:820px){.kpi{grid-template-columns:repeat(2,1fr)}}
  .kpi .box{padding:14px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);display:flex;flex-direction:column}
  .kpi .box .spark{display:block;height:28px;width:100%;margin-top:8px}
  .kpi .box .chip{display:inline-flex;gap:4px;align-items:center;font-size:10.5px;font-variant-numeric:tabular-nums;color:var(--mute);margin-top:6px;font-weight:500}
  .kpi .box .chip.up{color:var(--positive)}
  .kpi .box .chip.dn{color:var(--negative)}
  .kpi .box .chip .tri{font-size:9px;line-height:1}
  .kpi .big{font-size:24px;color:var(--ink);font-weight:600;letter-spacing:-.02em;margin:2px 0 0;
      font-variant-numeric:tabular-nums}
  .kpi .lbl{font-size:10.5px;color:var(--mute);text-transform:uppercase;letter-spacing:.08em;font-weight:500}

  /* ------- Compact tables ------- */
  table.tbl{width:100%;border-collapse:collapse;font-size:13px;background:var(--panel);
      border:1px solid var(--line)}
  table.tbl th,table.tbl td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:right;
      font-variant-numeric:tabular-nums}
  table.tbl th{background:var(--tint);color:var(--ink);text-align:right;font-weight:600;font-size:11px;
      text-transform:uppercase;letter-spacing:.04em}
  table.tbl td:first-child,table.tbl th:first-child{text-align:left;font-variant-numeric:normal}
  table.tbl tr:last-child td{border-bottom:none}

  /* Map */
  .map-wrap{position:relative;height:540px;overflow:hidden;background:#fff;border:1px solid var(--line)}
  @media (max-width:980px){.map-wrap{height:440px}}

  /* Map + side panel layout */
  .map-pair{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:18px;align-items:stretch;margin-top:4px}
  @media (max-width:980px){.map-pair{grid-template-columns:1fr}}
  .map-side{display:flex;flex-direction:column;gap:14px}
  .map-side .blk{background:var(--panel);border:1px solid var(--line);padding:12px 14px}
  .map-side .blk .lbl{font-size:10px;color:var(--mute);text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:8px}
  .map-side .blk ol{margin:0;padding:0;list-style:none;font-size:12.5px}
  .map-side .blk li{display:flex;justify-content:space-between;align-items:baseline;padding:5px 0;
      border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums;gap:8px}
  .map-side .blk li:last-child{border-bottom:0}
  .map-side .blk li span:first-child{color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .map-side .blk li span:last-child{color:var(--accent-dark);font-weight:600;flex-shrink:0}
  .map-side .blk .empty{color:var(--mute);font-size:12px;font-style:italic}

  /* Per-indicator plain-English gloss */
  .ind-gloss{font-size:13px;color:var(--text);background:var(--tint);border-left:2px solid var(--accent);
      padding:10px 14px;margin:0 0 14px;max-width:920px;line-height:1.6}
  .ind-gloss b{color:var(--ink);font-weight:600}
  .ind-gloss em{color:var(--mute);font-style:normal;font-size:12px;display:block;margin-top:4px}
  .leaflet-container{background:var(--bg);font-family:inherit}
  /* Leaflet zoom moves to top right so it never collides with the hover info box */
  .leaflet-top.leaflet-left{display:none}
  .leaflet-top.leaflet-right{top:12px;right:12px}

  /* Charts */
  .chart-wrap{position:relative;height:340px;background:var(--panel);border:1px solid var(--line);
      padding:14px 16px}
  .chart-wrap.tall{height:420px}
  @media (max-width:680px){
    .chart-wrap{height:280px;padding:10px}
    .chart-wrap.tall{height:360px}
  }

  /* Controls */
  .controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:10px 0 14px}
  .controls label{font-size:11px;color:var(--mute);font-weight:600;text-transform:uppercase;letter-spacing:.06em}
  .controls select{font-family:inherit;font-size:13px;padding:7px 32px 7px 12px;
      border:1px solid var(--line2);background:#fff;color:var(--ink);cursor:pointer;
      min-width:260px;max-width:100%;appearance:none;border-radius:2px;
      background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'><path d='M3 4.5l3 3 3-3' stroke='%231a1f1c' stroke-width='1.4' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>");
      background-repeat:no-repeat;background-position:right 10px center;background-size:11px}
  .controls select:focus{outline:1px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
  @media (max-width:680px){.controls select{min-width:0;width:100%}}

  /* Segmented controls: flat joined buttons, sharp corners */
  .cat-pills, .year-pills, .wave-pills{display:inline-flex;border:1px solid var(--line2);background:#fff;
      border-radius:2px;overflow:hidden}
  .cat-pills button, .year-pills button, .wave-pills button{
      font-family:inherit;font-size:13px;padding:7px 14px;border:0;
      background:#fff;color:var(--text);cursor:pointer;font-weight:500;
      border-right:1px solid var(--line);transition:background .12s ease,color .12s ease}
  .cat-pills button:last-child, .year-pills button:last-child, .wave-pills button:last-child{border-right:0}
  .cat-pills button:hover:not(.on), .year-pills button:hover:not(.on), .wave-pills button:hover:not(.on){
      background:var(--tint);color:var(--ink)}
  .cat-pills button.on, .year-pills button.on, .wave-pills button.on{
      background:var(--accent);color:#fff;font-weight:600}

  .controls button.pill{font-family:inherit;font-size:13px;padding:6px 12px;background:#fff;
      border:1px solid var(--line2);border-radius:2px;color:var(--text);cursor:pointer;font-weight:500}
  .controls button.pill.on{background:var(--accent);color:#fff;border-color:var(--accent)}

  .legend{display:flex;gap:8px;align-items:center;font-size:12px;color:var(--text)}
  .legend .sw{width:14px;height:10px;display:inline-block;margin-right:4px}

  /* ------- Full tables ------- */
  .fulltbl-wrap{background:var(--panel);border:1px solid var(--line);padding:14px 16px 16px}
  .fulltbl-toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:2px 0 12px}
  .fulltbl-toolbar input.search{font-family:inherit;font-size:13px;padding:7px 12px;
      border:1px solid var(--line2);border-radius:2px;color:var(--ink);min-width:220px;background:#fff}
  .fulltbl-toolbar input.search:focus{outline:1px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
  .fulltbl-toolbar .dl{font-family:inherit;font-size:12.5px;padding:7px 14px;
      background:var(--accent);color:#fff;border:0;border-radius:2px;cursor:pointer;font-weight:600;
      transition:background .12s ease}
  .fulltbl-toolbar .dl:hover{background:var(--accent-dark)}
  .fulltbl-toolbar .meta{color:var(--mute);font-size:12px;margin-left:auto}
  .fulltbl-scroll{max-height:540px;overflow:auto;border:1px solid var(--line);background:#fff}
  table.full{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;
      font-variant-numeric:tabular-nums;
      font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  table.full thead th{position:sticky;top:0;background:var(--ink);color:#fff;padding:9px 12px;text-align:right;
      font-weight:600;font-size:11.5px;letter-spacing:.02em;white-space:nowrap;cursor:pointer;user-select:none;
      border-right:1px solid rgba(255,255,255,.08);font-variant-numeric:normal}
  table.full thead th:last-child{border-right:0}
  table.full thead th:first-child, table.full thead th:nth-child(2){text-align:left}
  table.full thead th .arr{opacity:.45;margin-left:4px;font-size:10px}
  table.full thead th.sort-asc .arr, table.full thead th.sort-desc .arr{opacity:1}
  table.full tbody td{padding:7px 12px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
  table.full tbody td:first-child, table.full tbody td:nth-child(2){text-align:left;color:var(--ink);
      font-variant-numeric:normal}
  table.full tbody tr:hover{background:var(--tint)}
  table.full tbody tr.natrow{background:var(--accent-soft);font-weight:600}
  table.full tbody tr.natrow:hover{background:#d8e5dc}
  table.full tbody tr.natrow td:first-child{color:var(--accent-dark);letter-spacing:.03em;
      text-transform:uppercase;font-size:11px}

  /* ------- Footer ------- */
  .footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;color:var(--mute)}
  .footer .contact{color:var(--ink);font-size:13.5px;margin-bottom:6px;font-weight:500}
  .footer .contact a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--line2)}
  .footer .contact a:hover{border-bottom-color:var(--accent)}
  .footer .attrib{font-size:12.5px;color:var(--mute);max-width:880px;line-height:1.6}
  .src{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:11.5px;color:var(--mute)}

  /* Map overlays. Info top left, legend bottom left, zoom top right; no collisions. */
  .info{position:absolute;top:12px;left:12px;background:#fff;padding:10px 14px;
      font-size:12px;color:var(--ink);max-width:240px;z-index:500;border:1px solid var(--line2);
      box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .info h5{margin:0 0 4px;font-size:10px;color:var(--mute);font-weight:600;
      text-transform:uppercase;letter-spacing:.08em}
  .info .val{font-size:17px;color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums;
      letter-spacing:-0.01em;display:block;margin:2px 0}
  .info .ctx{font-size:11px;color:var(--mute);margin-top:2px;display:block}
  .mini-legend{position:absolute;bottom:14px;left:12px;background:#fff;padding:10px 12px;
      font-size:11.5px;color:var(--text);z-index:500;max-width:240px;border:1px solid var(--line2);
      line-height:1.5;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .mini-legend b{display:block;color:var(--ink);font-size:10px;text-transform:uppercase;
      letter-spacing:.08em;margin-bottom:4px;font-weight:600}
  .mini-legend .sub{display:block;color:var(--mute);font-size:11px;margin-bottom:6px;line-height:1.4}
  .mini-legend .row-l{display:flex;gap:8px;align-items:center;margin:2px 0;font-variant-numeric:tabular-nums}
  .mini-legend .sw{width:20px;height:10px;display:inline-block;border:1px solid rgba(0,0,0,.06)}
  @media (max-width:680px){
    .info,.mini-legend{max-width:180px;font-size:11px}
    .info .val{font-size:15px}
  }

  /* ------- Tags & details ------- */
  .tag{display:inline-block;background:var(--tint);color:var(--text);padding:2px 8px;
      font-size:10.5px;margin-right:4px;letter-spacing:.04em;text-transform:uppercase;font-weight:600;
      border:1px solid var(--line)}
  .tag.green{background:var(--accent-soft);color:var(--accent-dark);border-color:#cddcd3}
  .tag.teal{background:var(--accent-soft);color:var(--accent-dark);border-color:#cddcd3}
  .tag.orange{background:var(--tint);color:var(--text);border-color:var(--line)}

  details.tech{background:var(--panel);padding:12px 16px;margin:6px 0;font-size:13px;
      border:1px solid var(--line)}
  details.tech summary{cursor:pointer;color:var(--ink);font-weight:600;list-style:none}
  details.tech summary::-webkit-details-marker{display:none}
  details.tech summary::before{content:"+";display:inline-block;margin-right:10px;color:var(--accent);
      font-weight:600;width:10px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:12px}
  details.tech[open] summary::before{content:"–"}
  details.tech p{margin:8px 0 0;color:var(--text);line-height:1.6}
  small.cap{color:var(--mute);font-size:11.5px}

  /* Leaflet zoom controls: sharp default look */
  .leaflet-bar{border:1px solid var(--line2) !important;border-radius:2px !important;background:#fff;
      box-shadow:none !important}
  .leaflet-bar a,.leaflet-bar a:hover{background:#fff;color:var(--ink);border-radius:0 !important}
  .leaflet-bar a:hover{background:var(--tint)}
  .leaflet-bar a:first-child{border-radius:1px 1px 0 0 !important}
  .leaflet-bar a:last-child{border-radius:0 0 1px 1px !important}
  .leaflet-bar a{border-bottom-color:var(--line) !important}

  /* ------- Headline findings strip (hero scorecard on Map tab) ------- */
  .findings{display:grid;grid-template-columns:repeat(3,1fr);gap:0;
      border-top:1px solid var(--line);border-left:1px solid var(--line);
      margin:4px 0 22px}
  @media (max-width:980px){.findings{grid-template-columns:1fr}}
  .finding{display:block;text-decoration:none;color:inherit;padding:16px 18px 18px;
      border-right:1px solid var(--line);border-bottom:1px solid var(--line);
      background:var(--panel);border-top:3px solid var(--accent);position:relative;
      transition:background .12s ease;cursor:pointer}
  .finding:hover{background:var(--tint)}
  .finding.f-rice{border-top-color:var(--rice)}
  .finding.f-aqua{border-top-color:var(--aqua)}
  .finding.f-mech{border-top-color:var(--mech)}
  .finding .eyebrow{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;
      font-weight:600;margin-bottom:8px;color:var(--mute);padding-right:110px}
  .finding.f-rice .eyebrow{color:var(--rice-dark)}
  .finding.f-aqua .eyebrow{color:var(--aqua-dark)}
  .finding.f-mech .eyebrow{color:var(--mech-dark)}
  .finding .big{font-size:32px;font-weight:600;color:var(--ink);letter-spacing:-.02em;
      font-variant-numeric:tabular-nums;line-height:1.05;margin:0}
  .finding .big .unit{font-size:18px;font-weight:500;color:var(--mute);margin-left:2px}
  .finding .ctx{font-size:12.5px;color:var(--text);line-height:1.55;margin-top:8px}
  .finding .ctx b{color:var(--ink);font-weight:600}
  .finding .delta{display:inline-block;font-size:11px;color:var(--mute);margin-top:6px;
      font-variant-numeric:tabular-nums;font-weight:500}
  .finding .delta.up{color:var(--positive)}
  .finding .delta.dn{color:var(--negative)}
  .finding .arrow{position:absolute;top:16px;right:18px;color:var(--mute);
      font-size:13px;font-weight:500;letter-spacing:.02em}

  /* Methodology details block */
  details.method{background:var(--panel);border:1px solid var(--line);padding:10px 14px;
      margin:0 0 14px;font-size:12.5px;color:var(--text)}
  details.method summary{cursor:pointer;color:var(--mute);font-size:11.5px;font-weight:600;
      letter-spacing:.04em;list-style:none;line-height:1.4}
  details.method summary::-webkit-details-marker{display:none}
  details.method summary::before{content:"+";display:inline-block;margin-right:8px;
      color:var(--accent);font-weight:600;width:10px;
      font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:12px}
  details.method[open] summary::before{content:"–"}
  details.method .body{margin-top:10px;line-height:1.6;color:var(--text)}
  details.method .body b{color:var(--ink)}
  details.method .denom-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:0;
      border-top:1px solid var(--line);border-left:1px solid var(--line);margin:10px 0 4px}
  @media (max-width:680px){details.method .denom-grid{grid-template-columns:repeat(2,1fr)}}
  details.method .denom-grid .cell{padding:8px 10px;border-right:1px solid var(--line);
      border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
  details.method .denom-grid .cell .yr{font-size:10px;color:var(--mute);text-transform:uppercase;
      letter-spacing:.06em;font-weight:600;margin-bottom:4px}
  details.method .denom-grid .cell .all{font-size:13px;color:var(--ink);font-weight:600}
  details.method .denom-grid .cell .agri{font-size:12px;color:var(--mute);margin-top:1px}

  /* Tech Index */
  .ref-card{background:var(--panel);border:1px solid var(--line);padding:18px 20px;margin:8px 0 20px}
  .ref-eyebrow{font-size:10.5px;color:var(--accent);letter-spacing:.14em;text-transform:uppercase;font-weight:600;margin-bottom:6px}
  .ref-title{font-size:15px;color:var(--ink);font-weight:600;line-height:1.35;margin-bottom:4px}
  .ref-meta{font-size:12.5px;color:var(--text);line-height:1.55;margin-bottom:8px}
  .ref-links{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:8px}
  .ref-links a{font-size:12.5px;color:var(--accent);text-decoration:none;border-bottom:1px solid var(--line2);font-weight:500}
  .ref-links a:hover{border-bottom-color:var(--accent)}
  .ref-note{font-size:12px;color:var(--mute);line-height:1.55;font-style:italic;max-width:780px}

  .inst-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--line);border-left:1px solid var(--line);margin:8px 0 28px}
  @media (max-width:980px){.inst-grid{grid-template-columns:repeat(2,1fr)}}
  @media (max-width:680px){.inst-grid{grid-template-columns:1fr}}
  .inst-card{background:var(--panel);padding:14px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
  .inst-acro{font-size:11px;color:var(--accent);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:2px}
  .inst-name{font-size:13.5px;color:var(--ink);font-weight:600;margin-bottom:6px;line-height:1.35}
  .inst-role{font-size:12px;color:var(--text);line-height:1.55;margin-bottom:8px}
  .inst-links{display:flex;flex-direction:column;gap:3px}
  .inst-links a{font-size:11.5px;color:var(--accent);text-decoration:none;line-height:1.4}
  .inst-links a:hover{text-decoration:underline}

  .tech-controls{align-items:flex-start}
  .tech-controls .cat-pills{flex-wrap:wrap;max-width:100%}
  .tech-controls .cat-pills button{padding:6px 12px;font-size:12.5px}
  .tech-search{font-family:inherit;font-size:13px;padding:7px 12px;border:1px solid var(--line2);border-radius:2px;color:var(--ink);min-width:240px;background:#fff}
  .tech-search:focus{outline:1px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
  .tech-count{font-size:11.5px;color:var(--mute);font-variant-numeric:tabular-nums;margin-left:auto}

  .tech-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--line);border-left:1px solid var(--line)}
  @media (max-width:980px){.tech-grid{grid-template-columns:repeat(2,1fr)}}
  @media (max-width:680px){.tech-grid{grid-template-columns:1fr}}
  .tech-card{background:var(--panel);padding:14px 16px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);display:flex;flex-direction:column}
  .tech-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:8px}
  .tech-chip{font-size:10px;letter-spacing:.06em;text-transform:uppercase;font-weight:600;padding:2px 8px;border:1px solid var(--line)}
  .chip-rice{color:var(--rice-dark);background:var(--rice-soft);border-color:#cddcd3}
  .chip-aqua{color:var(--aqua-dark);background:var(--aqua-soft);border-color:#c9d6e2}
  .chip-mech{color:var(--mech-dark);background:var(--mech-soft);border-color:#dbcfb8}
  .tech-year{font-size:11.5px;color:var(--mute);font-variant-numeric:tabular-nums;font-weight:600}
  .tech-name{margin:0 0 4px;font-size:14px;color:var(--ink);font-weight:600;line-height:1.3}
  .tech-meta{font-size:11.5px;color:var(--mute);line-height:1.45;margin-bottom:8px}
  .cgiar-badge{display:inline-block;font-size:10.5px;color:var(--accent-dark);background:var(--accent-soft);
      padding:2px 8px;margin-bottom:8px;font-weight:600;letter-spacing:.03em;border:1px solid var(--line)}
  .tech-desc{font-size:12.5px;color:var(--text);line-height:1.55;margin:0 0 10px;flex:1}
  .tech-srcs{display:flex;flex-direction:column;gap:2px;padding-top:8px;border-top:1px solid var(--line)}
  .tech-srcs a{font-size:11.5px;color:var(--accent);text-decoration:none;line-height:1.4}
  .tech-srcs a:hover{text-decoration:underline}
  .empty{padding:24px;background:var(--panel);border:1px solid var(--line);color:var(--mute);font-size:13px;text-align:center}
</style>
</head>
<body class="cat-rice">
<div class="layout">

<aside class="rail">
  <div class="brand">
    <img src="__LOGO__" alt="MIXTAPE logo"/>
    <div class="name">
      <div class="acro">__RAIL_ACRO__</div>
      <div class="full">__RAIL_SUBTITLE__</div>
    </div>
  </div>
  <nav class="tabs" id="tabs">
__NAV_TABS__
  </nav>
  <div class="rail-meta">
    <div class="lbl">__RAIL_PANEL_LBL__</div>
__RAIL_PANEL_ROWS__
    <div class="lbl" style="margin-top:12px">__RAIL_AGRI_LBL__</div>
__RAIL_AGRI_ROWS__
    <div class="row" style="margin-top:6px;border-top:1px dashed var(--line);padding-top:6px;font-size:10.5px;line-height:1.45">
      <span style="color:var(--mute);font-weight:500">__RAIL_NOTE__</span>
    </div>
  </div>
  <div class="rail-foot">
    __RAIL_CONTACT_NAME__<br><a href="mailto:__RAIL_CONTACT_EMAIL__">__RAIL_CONTACT_EMAIL__</a><br>
    __RAIL_CONTACT_AFFIL__<br>
    <br>
    __RAIL_REPL_TEXT__ <a href="__RAIL_REPL_URL__" target="_blank" rel="noopener">__RAIL_REPL_LABEL__</a>
  </div>
</aside>

<main class="wrap">

<header class="title">
  <div class="eyebrow">__PAGE_EYEBROW__</div>
  <h1>__PAGE_H1__</h1>
  <div class="meta">
    <span>__PAGE_META_LEFT__</span>
    <span>__PAGE_META_RIGHT__</span>
  </div>
</header>

<div class="brief"><b>About.</b> __BRIEF__</div>

<!-- ============================== TAB 1 :: MAP ============================== -->
<section id="t-map" class="tab on">
  <h2 class="section">__MAP_H2__</h2>
  <p class="lede">__MAP_LEDE__</p>

  <div class="findings">
__FINDINGS__
  </div>

  <details class="method">
    <summary>__METHOD_SUMMARY__</summary>
    <div class="body">
      __METHOD_BODY__
      <div class="denom-grid">
__DENOM_GRID__
      </div>
      <small class="cap">__METHOD_CAP__</small>
    </div>
  </details>

  <h3 class="sub">__MAP_SUB_MAP__</h3>
  <p class="lede">__MAP_LEDE_MAP__</p>

  <div class="controls">
    <div class="cat-pills" id="mapCatPills">
__MAP_CAT_PILLS__
    </div>
    <select id="mapIndicator" aria-label="Indicator"></select>
    <div class="year-pills" id="mapYearPills">
      <button class="pill" data-year="2011">2011/12</button>
      <button class="pill" data-year="2015">2015</button>
      <button class="pill" data-year="2019">2018/19</button>
      <button class="pill on" data-year="2024">2024</button>
    </div>
  </div>

  <p class="ind-gloss" id="indGloss">&nbsp;</p>

  <div class="kpi" id="kpiMap"></div>

  <div class="map-pair">
    <div class="map-wrap">
      <div id="map" style="height:100%"></div>
      <div class="info" id="mapInfo"><h5>__MAP_INFO_TITLE__</h5><div class="val">–</div><small class="cap">__MAP_INFO_HINT__</small></div>
      <div class="mini-legend" id="mapLegend"></div>
    </div>
    <div class="map-side">
      <div class="blk"><div class="lbl">__MAP_TOP_LBL__</div><ol id="mapTopList"></ol></div>
      <div class="blk"><div class="lbl">__MAP_BOT_LBL__</div><ol id="mapBotList"></ol></div>
    </div>
  </div>

  <h3 class="sub">__MAP_SUB_TREND__</h3>
  <p class="lede">__MAP_LEDE_TREND__</p>
  <div class="row row-2">
    <div class="chart-wrap"><canvas id="natRice"></canvas></div>
    <div class="chart-wrap"><canvas id="natAqua"></canvas></div>
  </div>

  <p class="note">__MAP_NOTE__</p>
</section>

<!-- ============================== TAB 2 :: RICE ============================== -->
<section id="t-rice" class="tab">
  <h2 class="section">__RICE_H2__</h2>
  <p class="lede">__RICE_LEDE__</p>

  <div class="kpi" id="kpiRice"></div>

  <div class="row row-2">
    <div class="chart-wrap"><canvas id="riceFamilies"></canvas></div>
    <div class="chart-wrap"><canvas id="riceGrower"></canvas></div>
  </div>

  <h3 class="sub">__RICE_SUB_DIST__</h3>
  <div class="controls">
    <label>Family</label>
    <select id="riceDistFam"></select>
  </div>
  <div class="chart-wrap tall"><canvas id="riceDistChart"></canvas></div>

  <h3 class="sub">__RICE_SUB_TOP__</h3>
  <div id="riceTopTables" class="row row-2"></div>

  <h3 class="sub">__RICE_SUB_FULL__</h3>
  <p class="lede">__RICE_LEDE_FULL__</p>
  <div class="fulltbl-wrap" id="riceFullTbl"></div>

  <p class="note">__RICE_NOTE__</p>
</section>

<!-- ============================== TAB 3 :: AQUA ============================== -->
<section id="t-aqua" class="tab">
  <h2 class="section">__AQUA_H2__</h2>
  <p class="lede">__AQUA_LEDE__</p>

  <div class="kpi" id="kpiAqua"></div>

  <div class="row row-2">
    <div class="chart-wrap"><canvas id="aquaTS"></canvas></div>
    <div class="chart-wrap"><canvas id="aquaPoly"></canvas></div>
  </div>

  <h3 class="sub">__AQUA_SUB_DIST__</h3>
  <div class="controls">
    <label>Indicator</label>
    <select id="aquaDistInd"></select>
  </div>
  <div class="chart-wrap tall"><canvas id="aquaDistChart"></canvas></div>

  <h3 class="sub">__AQUA_SUB_TOP__</h3>
  <div id="aquaTopTables" class="row row-2"></div>

  <h3 class="sub">__AQUA_SUB_FULL__</h3>
  <p class="lede">__AQUA_LEDE_FULL__</p>
  <div class="fulltbl-wrap" id="aquaFullTbl"></div>

  <p class="note">__AQUA_NOTE__</p>
</section>

<!-- ============================== TAB 4 :: 2024 SPIA ============================== -->
<section id="t-spia" class="tab">
  <h2 class="section">__SPIA_H2__</h2>

  <div class="ref-card">
    <div class="ref-eyebrow">__SPIA_REF_EYEBROW__</div>
    <div class="ref-title">__SPIA_REF_TITLE__</div>
    <div class="ref-meta">__SPIA_REF_CITATION__</div>
    <div class="ref-links">
      <a href="__SPIA_REF_REPORT_URL__" target="_blank" rel="noopener">__SPIA_REF_REPORT_LABEL__</a>
      <a href="__SPIA_REF_GITHUB_URL__" target="_blank" rel="noopener">__SPIA_REF_GITHUB_LABEL__</a>
    </div>
    <div class="ref-note">__SPIA_REF_NOTE__</div>
  </div>

  <p class="lede">__SPIA_LEDE__</p>

  <div class="kpi" id="kpiSpia"></div>

  <h3 class="sub">__SPIA_SUB_DNA__</h3>
  <p class="lede">__SPIA_LEDE_DNA__</p>
  <div class="row row-2">
    <div class="chart-wrap"><canvas id="dnaByVariety"></canvas></div>
    <div class="chart-wrap"><canvas id="dnaByCluster"></canvas></div>
  </div>

  <h3 class="sub">__SPIA_SUB_PRACT__</h3>
  <p class="lede">__SPIA_LEDE_PRACT__</p>
  <div class="chart-wrap"><canvas id="spiaPractices"></canvas></div>

  <h3 class="sub">__SPIA_SUB_EQUIP__</h3>
  <div class="chart-wrap"><canvas id="spiaEquip"></canvas></div>

  <h3 class="sub">__SPIA_SUB_FULL__</h3>
  <p class="lede">__SPIA_LEDE_FULL__</p>
  <div class="fulltbl-wrap" id="spiaFullTbl"></div>

  <div class="row row-2" style="margin-top:16px">
    <div>
      <h3 class="sub">__SPIA_SUB_DNAVAR__</h3>
      <p class="lede">__SPIA_LEDE_DNAVAR__</p>
      <div class="fulltbl-wrap" id="spiaDnaVariety"></div>
    </div>
    <div>
      <h3 class="sub">__SPIA_SUB_DNACLUST__</h3>
      <p class="lede">__SPIA_LEDE_DNACLUST__</p>
      <div class="fulltbl-wrap" id="spiaDnaCluster"></div>
    </div>
  </div>

  <p class="note">__SPIA_NOTE__</p>
</section>

<!-- ============================== TAB 5 :: MECH ============================== -->
<section id="t-mech" class="tab">
  <h2 class="section">__MECH_H2__</h2>
  <p class="lede">__MECH_LEDE__</p>

  <div class="kpi" id="kpiMech"></div>

  <div class="row row-2">
    <div class="chart-wrap"><canvas id="mechOwn"></canvas></div>
    <div class="chart-wrap"><canvas id="mechUse"></canvas></div>
  </div>

  <h3 class="sub">__MECH_SUB_DIST__</h3>
  <div class="controls">
    <label>Indicator</label>
    <select id="mechDistInd"></select>
  </div>
  <div class="chart-wrap tall"><canvas id="mechDistChart"></canvas></div>

  <h3 class="sub">__MECH_SUB_FULL__</h3>
  <p class="lede">__MECH_LEDE_FULL__</p>
  <div class="fulltbl-wrap" id="mechFullTbl"></div>

  <p class="note">__MECH_NOTE__</p>
</section>

<!-- ============================== TAB 6 :: TECH INDEX ============================== -->
<section id="t-tech" class="tab">
  <h2 class="section">__TECH_H2__</h2>
  <p class="lede">__TECH_LEDE__</p>

  <div class="primary-ref" id="primaryRef"></div>

  <h3 class="sub">__TECH_SUB_INST__</h3>
  <div class="inst-grid" id="instGrid"></div>

  <h3 class="sub">__TECH_SUB_BROWSE__</h3>
  <div class="controls tech-controls">
    <div class="cat-pills" id="techCatPills"></div>
    <input type="search" class="search tech-search" placeholder="__TECH_SEARCH_PH__" id="techSearch"/>
    <span class="tech-count" id="techCount"></span>
  </div>
  <div class="tech-grid" id="techGrid"></div>
</section>

<div class="footer">
<div class="contact">
  __FOOT_NAME__ &middot; <a href="mailto:__FOOT_EMAIL__">__FOOT_EMAIL__</a> &middot; __FOOT_AFFIL__
</div>
<div class="attrib">
  __FOOT_ATTRIB__
</div>
</div>

</main>
</div><!-- /layout -->

<script>
/* ==============================  DATA  ============================== */
const GEO  = __GEO__;
const RICE = __RICE__;
const AQUA = __AQUA__;
const MECH = __MECH__;
const DNA  = __DNA__;
const NAT  = __NAT__;
const SUM  = __SUM__;
const TECH = __TECH__;
/* All display text comes from content.toml */
const TXT   = __TXT__;
const THEME = __THEME__;

const WAVES = ["2011","2015","2019","2024"];
const WAVE_LBL = {"2011":"2011/12","2015":"2015","2019":"2018/19","2024":"2024"};

const RICE_FAM_LBL = TXT.labels.rice;
const AQUA_IND_LBL = TXT.labels.aqua;
const MECH_IND_LBL = TXT.labels.mech;

/* ==============================  COLORS  ============================== */
/* Semantic palette from the [theme] section of content.toml. */
const COL = {slate:THEME.ink, slate2:THEME.chart_text,
             leaf:THEME.rice.main, leaf2:THEME.rice.light,
             teal:THEME.aqua.main, teal2:THEME.aqua.light,
             accent:THEME.mech.main, accent2:THEME.mech.light,
             cream:THEME.tint, ink:THEME.ink, mute:THEME.mute};
/* Monochrome series palettes per tab. Dark to light shades within one hue family
   keep multi-line charts coherent. */
const SERIES_RICE = THEME.series.rice;
const SERIES_AQUA = THEME.series.aqua;
const SERIES_MECH = THEME.series.mech;
const SERIES_COL = SERIES_RICE; /* default (kept for any code that still references it) */

Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
Chart.defaults.font.size   = 11.5;
Chart.defaults.color       = COL.slate2;
Chart.defaults.borderColor = THEME.line;
Chart.defaults.plugins.legend.labels.boxWidth = 10;
Chart.defaults.plugins.legend.labels.boxHeight = 2;
Chart.defaults.plugins.legend.labels.padding = 8;
Chart.defaults.plugins.legend.labels.font = {size: 11};

/* ==============================  TABS  ============================== */
const chartRefs = {};
const tabInit   = {};
const TAB_CAT = {"t-map":"rice","t-rice":"rice","t-aqua":"aqua","t-spia":"rice","t-mech":"mech","t-tech":"rice"};
function setBodyCat(cat){
  document.body.classList.remove("cat-rice","cat-aqua","cat-mech");
  document.body.classList.add("cat-"+cat);
}
document.getElementById("tabs").addEventListener("click", e => {
  const btn = e.target.closest("button"); if(!btn) return;
  const id = btn.dataset.tab;
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.toggle("on", b === btn));
  document.querySelectorAll("section.tab").forEach(s => s.classList.toggle("on", s.id === id));
  setBodyCat(TAB_CAT[id] || "rice");
  lazyInit(id);
  window.scrollTo({top:0,behavior:"instant"});
});
function lazyInit(id){ if(tabInit[id]) return; tabInit[id]=true; (INITS[id]||(()=>{}))(); }

/* Mobile-only: expand the brief on tap */
document.querySelectorAll(".brief").forEach(el=>{
  el.addEventListener("click", ()=>{ if(window.matchMedia("(max-width:680px)").matches) el.classList.add("open"); });
});

/* Findings cards on the hero: click jumps to the matching tab (and updates the rail) */
document.querySelectorAll(".finding[data-jump]").forEach(el=>{
  const go = ()=>{
    const id = el.dataset.jump;
    const btn = document.querySelector(`nav.tabs button[data-tab="${id}"]`);
    if(btn) btn.click();
  };
  el.addEventListener("click", go);
  el.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); go(); } });
});

/* ==============================  MAP  ============================== */
function ramp(v, stops){
  if(v==null || isNaN(v)) return THEME.map_nodata;
  for(const [t,c] of stops) if(v<=t) return c;
  return stops[stops.length-1][1];
}
/* Three sequential ramps from content.toml. Rice green, aquaculture blue,
   mechanisation warm earth. The lightest step must always contrast with the
   page background. */
const MAP_RAMPS = {
  rice:{stops:THEME.map_ramps.rice},
  aqua:{stops:THEME.map_ramps.aqua},
  mech:{stops:THEME.map_ramps.mech}
};
function stopsFor(ind){
  if(["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA","SUPP_FEED","HORMONE","DISEASE_CTL"].includes(ind))
    return MAP_RAMPS.aqua.stops;
  if(ind.startsWith("USE_")||ind in MECH_IND_LBL) return MAP_RAMPS.mech.stops;
  return MAP_RAMPS.rice.stops;
}
function indicatorSource(ind){
  if(ind in RICE_FAM_LBL) return RICE;
  if(ind in MECH_IND_LBL) return MECH;
  return AQUA;
}
const MAP_CATALOG = TXT.map_catalog;
const DEFAULT_MAP_IND = {rice:"BRRI_CORE28_29", aqua:"ANY_POND", mech:"POWER_TILLER"};

/* Plain language notes per indicator, from the [glosses] section of content.toml. */
const IND_GLOSS = TXT.glosses;
let map, geoLayer, mapCat = "rice", mapYear = "2024";

function rebuildIndicatorSelect(){
  const sel = document.getElementById("mapIndicator");
  sel.innerHTML = "";
  MAP_CATALOG[mapCat].items.forEach(([lbl,key])=>{
    const o = document.createElement("option");
    o.value = key; o.textContent = lbl;
    if(key === DEFAULT_MAP_IND[mapCat]) o.selected = true;
    sel.appendChild(o);
  });
}

function initMap(){
  rebuildIndicatorSelect();
  map = L.map("map",{zoomControl:true,attributionControl:false}).setView([23.8,90.35],6.6);
  drawMap();
  document.getElementById("mapIndicator").onchange = drawMap;
  document.getElementById("mapCatPills").addEventListener("click", e=>{
    const btn = e.target.closest("button"); if(!btn) return;
    mapCat = btn.dataset.cat;
    document.querySelectorAll("#mapCatPills button").forEach(b=>b.classList.toggle("on", b.dataset.cat===mapCat));
    setBodyCat(mapCat);
    rebuildIndicatorSelect();
    drawMap();
  });
  document.getElementById("mapYearPills").addEventListener("click", e=>{
    if(e.target.tagName!=="BUTTON") return;
    mapYear = e.target.dataset.year;
    document.querySelectorAll("#mapYearPills button").forEach(b=>b.classList.toggle("on", b.dataset.year===mapYear));
    drawMap();
  });
}
function setMapInfoDefault(ind, year, src, data){
  const natRow = data.__NATIONAL__ || {};
  const natNow = natRow[ind];
  const natN   = natRow.n_hh;
  const item   = MAP_CATALOG[mapCat].items.find(x=>x[1]===ind);
  const lbl    = item ? item[0] : ind;
  const box    = document.getElementById("mapInfo");
  if(!box) return;
  const valTxt = (natNow==null||isNaN(natNow)) ? "n/a" : natNow.toFixed(1)+"%";
  box.innerHTML = `<h5>${TXT.map.info_title}</h5>
    <div class="val">${valTxt}</div>
    <small class="cap">${lbl} &middot; ${WAVE_LBL[year]} &middot; n = ${natN??"–"} agricultural households</small>
    <small class="cap" style="display:block;margin-top:4px;color:var(--mute);font-size:10.5px">${TXT.map.info_hover_hint}</small>`;
}
function drawMap(){
  const ind  = document.getElementById("mapIndicator").value;
  const year = mapYear;
  const src  = indicatorSource(ind);
  const data = (src.by_wave[year]||{});
  if(geoLayer){ map.removeLayer(geoLayer); }
  const stops = stopsFor(ind);
  const features = Object.entries(GEO.districts).map(([name,d])=>({
    type:"Feature",
    properties:{name, division:d.division},
    geometry:d.geometry
  }));
  geoLayer = L.geoJSON({type:"FeatureCollection",features},{
    style:f=>{
      const row = data[f.properties.name];
      const v = row ? row[ind] : null;
      return {color:"#ffffff",weight:0.7,opacity:1,fillOpacity:0.95,fillColor:ramp(v,stops)};
    },
    onEachFeature:(f,layer)=>{
      const row = data[f.properties.name];
      const v = row ? row[ind] : null;
      const n = row ? row.n_hh : null;
      layer.on({
        mouseover:()=>{
          layer.setStyle({weight:2,color:COL.slate});
          const box=document.getElementById("mapInfo");
          box.innerHTML = `<h5>${f.properties.name} <small>(${f.properties.division})</small></h5>
            <div class="val">${v==null?"n/a":v.toFixed(1)+"%"}</div>
            <small class="cap">${WAVE_LBL[year]} &middot; n = ${n??"–"} agricultural households</small>`;
        },
        mouseout:()=>{ geoLayer.resetStyle(layer); setMapInfoDefault(ind, year, src, data); },
        click:()=>map.fitBounds(layer.getBounds(),{padding:[20,20]})
      });
    }
  }).addTo(map);
  setMapInfoDefault(ind, year, src, data);

  // legend
  const lg = document.getElementById("mapLegend");
  const item = MAP_CATALOG[mapCat].items.find(x=>x[1]===ind);
  const title = item ? item[0] : "";
  let html = `<b>${MAP_CATALOG[mapCat].label}</b><br>${title}<br><small class="cap">${TXT.map.legend_units} &middot; ${WAVE_LBL[year]}</small>`;
  // Skip the first stop (collapsed into "0%") and label the cap row as "35%+".
  stops.forEach((s,i)=>{
    if(i===0) return;
    const hi = s[0]; const lo = stops[i-1][0];
    const label = hi===100 ? `${lo.toFixed(0)}%+` : `${lo.toFixed(0)}–${hi.toFixed(0)}%`;
    html += `<div class="row-l"><span class="sw" style="background:${s[1]}"></span>${label}</div>`;
  });
  lg.innerHTML = html;

  /* --- Per-indicator gloss strip (plain English: what is this technology, why does it matter) --- */
  const gloss = document.getElementById("indGloss");
  if(gloss){
    const gtxt = IND_GLOSS[ind] || `<b>${title}</b>`;
    gloss.innerHTML = gtxt +
      `<em>${TXT.map.gloss_suffix.replace("{year}", WAVE_LBL[year])}</em>`;
  }

  /* --- District rows for this indicator + year (NATIONAL row excluded) --- */
  const rows = [];
  Object.entries(data).forEach(([dist, r])=>{
    if(dist === "__NATIONAL__") return;
    const v = r[ind];
    if(v == null || isNaN(v)) return;
    rows.push({name:dist, v:+v, n:r.n_hh});
  });
  rows.sort((a,b)=>b.v - a.v);

  /* --- Headline KPI strip (4 boxes that change with indicator and year) --- */
  const natRow = data.__NATIONAL__ || {};
  const natNow = natRow[ind];
  const natSeries = ["2011","2015","2019","2024"].map(w=>{
    const nr = (src.by_wave[w]||{}).__NATIONAL__;
    return (nr && nr[ind] != null && !isNaN(nr[ind])) ? +nr[ind] : null;
  });
  const firstReal = natSeries.find(x=>x!=null);
  const realIdx = natSeries.findIndex(x=>x!=null);
  const firstWaveLbl = realIdx>=0 ? WAVE_LBL[["2011","2015","2019","2024"][realIdx]] : "";
  let deltaTxt = "n/a";
  if(natNow != null && firstReal != null){
    const d = natNow - firstReal;
    const tri = d >= 0 ? "▲" : "▼";
    deltaTxt = `${tri} ${Math.abs(d).toFixed(1)} pp <small style="color:var(--mute);font-weight:500;font-size:11px">since ${firstWaveLbl}</small>`;
  }
  const top = rows[0], bot = rows[rows.length-1];
  const kpiEl = document.getElementById("kpiMap");
  if(kpiEl){
    const fmtPct = v => (v==null||isNaN(v)) ? "n/a" : v.toFixed(1)+"%";
    const distFmt = r => `${r.name} <small style="color:var(--mute);font-weight:500;font-size:11px"> · ${fmtPct(r.v)}</small>`;
    kpiEl.innerHTML = [
      {lbl:TXT.map.kpi_national.replace("{year}", WAVE_LBL[year]), val:fmtPct(natNow)},
      {lbl:TXT.map.kpi_change,  val:deltaTxt},
      {lbl:TXT.map.kpi_highest, val: top ? distFmt(top) : "n/a"},
      {lbl:TXT.map.kpi_lowest,  val: bot ? distFmt(bot) : "n/a"}
    ].map(o => `<div class="box"><div class="lbl">${o.lbl}</div><div class="big">${o.val}</div></div>`).join("");
  }

  /* --- Top 5 and bottom 5 district lists beside the map --- */
  const topEl = document.getElementById("mapTopList");
  const botEl = document.getElementById("mapBotList");
  if(topEl && botEl){
    if(rows.length === 0){
      topEl.innerHTML = `<li class="empty">${TXT.misc.no_district_data}</li>`;
      botEl.innerHTML = `<li class="empty">${TXT.misc.no_district_data}</li>`;
    } else {
      const t5 = rows.slice(0,5);
      const b5 = rows.slice(-5).reverse();
      const li = r => `<li><span title="${r.name}">${r.name}</span><span>${r.v.toFixed(1)}%</span></li>`;
      topEl.innerHTML = t5.map(li).join("");
      botEl.innerHTML = b5.map(li).join("");
    }
  }
}

/* ==============================  FULL TABLE HELPERS  ============================== */
/* Render a full district-level table for a (source, wave).  Columns:
   District | Division | n_hh | weight_sum | [every indicator, % weighted].
   Adds: live text filter, sortable headers, CSV download, sticky header.
   The `__NATIONAL__` row is rendered first and styled. */
function _fmt(v){
  if(v==null || v==="" || (typeof v==="number" && isNaN(v))) return "";
  if(typeof v === "number") return v.toFixed(2);
  return String(v);
}
function buildFullRows(src, wave, indicators){
  const data = src.by_wave[wave] || {};
  const rows = [];
  const nat = data["__NATIONAL__"];
  if(nat){
    const r = {district:"NATIONAL (weighted)", division:"–", n_hh:nat.n_hh, weight_sum:nat.weight_sum};
    indicators.forEach(k => r[k] = nat[k] ?? null);
    r._is_nat = true;
    rows.push(r);
  }
  Object.entries(data).forEach(([dist, row]) => {
    if(dist === "__NATIONAL__") return;
    const r = {district:dist, division:(GEO.districts[dist]||{}).division||"", n_hh:row.n_hh, weight_sum:row.weight_sum};
    indicators.forEach(k => r[k] = row[k] ?? null);
    rows.push(r);
  });
  return rows;
}
function csvDownload(filename, rows, colKeys, colLabels){
  const esc = v => {
    if(v==null) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
  };
  const lines = [colLabels.map(esc).join(",")];
  rows.forEach(r => lines.push(colKeys.map(k => esc(r[k])).join(",")));
  const blob = new Blob([lines.join("\n")], {type:"text/csv;charset=utf-8"});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  setTimeout(()=>{URL.revokeObjectURL(url); a.remove();}, 300);
}
function renderFullTable(container, src, indicators, indicatorLabels, csvBase, opts){
  /* container: DOM element
     src: RICE | AQUA | MECH (or any {by_wave:{...}})
     indicators: ordered list of indicator keys
     indicatorLabels: map key->label
     csvBase: filename prefix
     opts: {waves:[strings], defaultWave:string, showWavePills:bool} */
  opts = Object.assign({waves:["2011","2015","2019","2024"], defaultWave:"2024", showWavePills:true}, opts||{});
  const pillsHtml = opts.showWavePills
    ? `<div class="wave-pills">${opts.waves.map(w=>`<button data-w="${w}" class="${w===opts.defaultWave?"on":""}">${WAVE_LBL[w]}</button>`).join("")}</div>`
    : "";
  container.innerHTML = `
    <div class="fulltbl-toolbar">
      ${pillsHtml}
      <input type="search" class="search" placeholder="${TXT.misc.filter_placeholder}"/>
      <button class="dl">${TXT.misc.download_csv}</button>
      <span class="meta"></span>
    </div>
    <div class="fulltbl-scroll"><table class="full"></table></div>`;
  let currentWave = opts.defaultWave;
  const waveGetter = ()=>currentWave;

  const colKeys   = ["district","division","n_hh","weight_sum", ...indicators];
  const colLabels = ["District","Division","n (households)","Σ weight", ...indicators.map(k=>indicatorLabels[k]||k)];
  let sortKey = "weight_sum", sortDir = -1;

  function render(){
    const wave = waveGetter();
    let rows = buildFullRows(src, wave, indicators);
    const q = container.querySelector("input.search").value.trim().toLowerCase();
    if(q) rows = rows.filter(r => r._is_nat || (r.district.toLowerCase().includes(q) || (r.division||"").toLowerCase().includes(q)));
    // sort non-national rows; keep NATIONAL pinned at top
    const nat = rows.filter(r => r._is_nat);
    const rest= rows.filter(r => !r._is_nat).sort((a,b)=>{
      const av=a[sortKey], bv=b[sortKey];
      if(av==null && bv==null) return 0;
      if(av==null) return 1;
      if(bv==null) return -1;
      if(typeof av === "number" && typeof bv === "number") return (av-bv)*sortDir;
      return (String(av).localeCompare(String(bv)))*sortDir;
    });
    rows = nat.concat(rest);

    const tbl = container.querySelector("table");
    tbl.innerHTML = "";
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    colKeys.forEach((k,i)=>{
      const th = document.createElement("th");
      th.innerHTML = `${colLabels[i]}<span class="arr">${sortKey===k?(sortDir===1?"▲":"▼"):"↕"}</span>`;
      th.dataset.k = k;
      if(sortKey===k) th.classList.add(sortDir===1?"sort-asc":"sort-desc");
      th.onclick = ()=>{ if(sortKey===k) sortDir*=-1; else {sortKey=k; sortDir=(k==="district"||k==="division")?1:-1;} render(); };
      trh.appendChild(th);
    });
    thead.appendChild(trh);
    tbl.appendChild(thead);
    const tbody = document.createElement("tbody");
    rows.forEach(r=>{
      const tr = document.createElement("tr");
      if(r._is_nat) tr.className = "natrow";
      colKeys.forEach(k=>{
        const td = document.createElement("td");
        td.textContent = (k==="n_hh" ? (r[k]??"") : _fmt(r[k]));
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tbl.appendChild(tbody);
    const meta = container.querySelector(".meta");
    const total = rows.filter(r=>!r._is_nat).length;
    meta.textContent = `${total} districts · ${WAVE_LBL[wave]}`;
  }

  const pillsEl = container.querySelector(".wave-pills");
  if(pillsEl){
    pillsEl.addEventListener("click", e=>{
      if(e.target.tagName!=="BUTTON") return;
      currentWave = e.target.dataset.w;
      pillsEl.querySelectorAll("button").forEach(b=>b.classList.toggle("on", b===e.target));
      render();
    });
  }
  container.querySelector("input.search").addEventListener("input", render);
  container.querySelector("button.dl").addEventListener("click", ()=>{
    const wave = waveGetter();
    const rows = buildFullRows(src, wave, indicators);
    csvDownload(`${csvBase}_${wave}.csv`, rows, colKeys, colLabels);
  });
  render();
}

/* ==============================  KPI HELPER  ============================== */
/* Render a KPI tile. When `series` (a 4-element array over BIHS rounds) and
   `colour` are provided, a 28px sparkline plus a "+N.N pp vs 2011/12" delta
   chip are appended; otherwise the tile renders bare (used for SPIA counts). */
function kpiBox(opts){
  const lbl = opts.lbl, val = opts.val;
  const series = opts.series, colour = opts.colour;
  if(!series || !colour){
    return `<div class="box"><div class="lbl">${lbl}</div><div class="big">${val}</div></div>`;
  }
  const xs = series.filter(v => v != null && !isNaN(v));
  if(xs.length < 2){
    return `<div class="box"><div class="lbl">${lbl}</div><div class="big">${val}</div></div>`;
  }
  const base = xs[0], last = xs[xs.length - 1], d = last - base;
  const sign = d >= 0 ? "up" : "dn";
  const tri  = d >= 0 ? "▲" : "▼";
  const w = 120, h = 28;
  const mn = Math.min.apply(null, xs);
  const mx = Math.max.apply(null, xs);
  const r  = (mx - mn) || 1;
  const pts = xs.map((v, i) =>
    `${(i / (xs.length - 1) * w).toFixed(1)},${(h - ((v - mn) / r) * h).toFixed(1)}`
  ).join(" ");
  const lastY = (h - ((last - mn) / r) * h).toFixed(1);
  const baseLbl = opts.baseLbl || "2011/12";
  return `<div class="box">
    <div class="lbl">${lbl}</div>
    <div class="big">${val}</div>
    <svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <polyline fill="none" stroke="${colour}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" points="${pts}"/>
      <circle cx="${w}" cy="${lastY}" r="2.6" fill="${colour}"/>
    </svg>
    <span class="chip ${sign}"><span class="tri">${tri}</span>${d >= 0 ? "+" : ""}${d.toFixed(1)} pp vs ${baseLbl}</span>
  </div>`;
}

/* ==============================  CHART HELPERS  ============================== */
/* Editorial-line defaults per the audit:
 *  - terminal point only (radius 0 mid-series, 4 at the 2024 end)
 *  - tooltip mode 'index' so the whole vertical slice is visible on hover
 *  - no Y-axis title; ticks suffixed with '%'
 *  - hero-line emphasis when opts.heroIdx is given: hero line 2.5px full color,
 *    other lines 1px at 50% alpha so the eye knows where to land first
 */
function _hex2rgba(hex, a){
  hex = (hex||"").replace("#","");
  if(hex.length===3) hex = hex.split("").map(c=>c+c).join("");
  const n = parseInt(hex,16);
  return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`;
}
function lineChart(canvas, labels, datasets, opts){
  if(chartRefs[canvas]) chartRefs[canvas].destroy();
  opts = opts || {};
  const heroIdx = opts.heroIdx;  // optional dataset index to highlight
  datasets = datasets.map((d, i) => {
    const isHero = (heroIdx == null) || (i === heroIdx);
    const colour = d.borderColor || d.backgroundColor || SERIES_RICE[0];
    return Object.assign({
      tension: 0.25,
      borderWidth: isHero ? 2.5 : 1,
      borderColor: isHero ? colour : _hex2rgba(colour, 0.55),
      backgroundColor: isHero ? colour : _hex2rgba(colour, 0.55),
      pointRadius: labels.map((_, j) => j === labels.length - 1 ? (isHero ? 4 : 3) : 0),
      pointHoverRadius: 5,
      fill: false,
      borderDash: d.borderDash || (isHero ? [] : (i % 2 ? [3,3] : []))
    }, d);
  });
  const merged = Object.assign({
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      title: { display: !!(opts.plugins && opts.plugins.title), color: COL.slate, font: { size: 13, weight: "600" }, padding: { bottom: 4 } },
      subtitle: { display: !!(opts.plugins && opts.plugins.subtitle), color: COL.mute, font: { size: 11.5, style: "normal" }, padding: { bottom: 10 } },
      legend: { position: "top", align: "start", labels: { boxWidth: 10, boxHeight: 2, padding: 6, font: { size: 11 } } },
      tooltip: { mode: "index", intersect: false }
    },
    scales: {
      y: { beginAtZero: true, grid: { color: THEME.chart_grid, drawTicks: false }, ticks: { callback: v => v + "%" }, title: { display: false } },
      x: { grid: { display: false } }
    }
  }, opts);
  chartRefs[canvas] = new Chart(document.getElementById(canvas), { type: "line", data: { labels, datasets }, options: merged });
}
function barChart(canvas, labels, datasets, opts){
  if(chartRefs[canvas]) chartRefs[canvas].destroy();
  chartRefs[canvas] = new Chart(document.getElementById(canvas),{
    type:"bar",
    data:{labels,datasets},
    options:Object.assign({
      responsive:true,maintainAspectRatio:false,indexAxis:"y",
      plugins:{title:{display:true,color:COL.slate,font:{size:13,weight:"600"},padding:{bottom:8}},
               legend:{display:false}},
      scales:{x:{beginAtZero:true,grid:{color:THEME.chart_grid,drawTicks:false},ticks:{callback:v=>v+"%"},title:{display:false}},
              y:{grid:{display:false}}}
    },opts||{})
  });
}

/* ==============================  TAB 1 INIT  ============================== */
INITS = {};
INITS["t-map"] = function(){
  initMap();
  const riceKeys = ["BRRI_CORE28_29","BRRI_NEW_POST2012","HYBRID","LOCAL","BRRI_STRESS","BINA"];
  lineChart("natRice", WAVES.map(w=>WAVE_LBL[w]),
    riceKeys.map((k,i)=>({label:RICE_FAM_LBL[k], data:NAT.rice[k], borderColor:SERIES_RICE[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.natRice.title},
              subtitle:{display:true,text:TXT.charts.natRice.subtitle}}});
  const aquaKeys = ["ANY_POND","POLY_CARP_2PLUS","TILAPIA","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"];
  lineChart("natAqua", WAVES.map(w=>WAVE_LBL[w]),
    aquaKeys.map((k,i)=>({label:AQUA_IND_LBL[k], data:NAT.aqua[k], borderColor:SERIES_AQUA[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.natAqua.title},
              subtitle:{display:true,text:TXT.charts.natAqua.subtitle}}});
};

/* ==============================  TAB 2 INIT (RICE)  ============================== */
INITS["t-rice"] = function(){
  const nat24 = RICE.by_wave["2024"].__NATIONAL__;
  const kpi = document.getElementById("kpiRice");
  const cR = COL.leaf;
  kpi.innerHTML = [
    {lbl:TXT.kpi.rice.grower,    val:nat24.RICE_GROWER.toFixed(1)+"%",       series:NAT.rice.RICE_GROWER,       colour:cR},
    {lbl:TXT.kpi.rice.core,      val:nat24.BRRI_CORE28_29.toFixed(1)+"%",    series:NAT.rice.BRRI_CORE28_29,    colour:cR},
    {lbl:TXT.kpi.rice.new_lines, val:nat24.BRRI_NEW_POST2012.toFixed(1)+"%", series:NAT.rice.BRRI_NEW_POST2012, colour:cR},
    {lbl:TXT.kpi.rice.hybrid,    val:nat24.HYBRID.toFixed(1)+"%",            series:NAT.rice.HYBRID,            colour:cR}
  ].map(kpiBox).join("");

  const fams = ["BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL"];
  lineChart("riceFamilies", WAVES.map(w=>WAVE_LBL[w]),
    fams.map((k,i)=>({label:RICE_FAM_LBL[k], data:NAT.rice[k], borderColor:SERIES_RICE[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.riceFamilies.title},
              subtitle:{display:true,text:TXT.charts.riceFamilies.subtitle}}});
  lineChart("riceGrower", WAVES.map(w=>WAVE_LBL[w]),
    [{label:RICE_FAM_LBL.RICE_GROWER, data:NAT.rice.RICE_GROWER, borderColor:COL.leaf}],
    {plugins:{title:{display:true,text:TXT.charts.riceGrower.title},
              subtitle:{display:true,text:TXT.charts.riceGrower.subtitle},
              legend:{display:false}}});

  const sel = document.getElementById("riceDistFam");
  fams.forEach((k,i)=>{const o=document.createElement("option");o.value=k;o.innerHTML=RICE_FAM_LBL[k];if(i===0)o.selected=true;sel.appendChild(o);});
  function redrawDist(){
    const k = sel.value;
    const data = RICE.by_wave["2024"];
    const rows = Object.entries(data).filter(([n])=>n!=="__NATIONAL__")
                  .map(([name,r])=>({name,v:r[k]||0}))
                  .sort((a,b)=>b.v-a.v).slice(0,30);
    barChart("riceDistChart", rows.map(r=>r.name),
      [{label:RICE_FAM_LBL[k]+" (2024)",data:rows.map(r=>r.v),backgroundColor:COL.leaf,borderColor:COL.leaf}],
      {plugins:{title:{display:true,text:TXT.charts.top30_template.replace("{label}", RICE_FAM_LBL[k].toLowerCase())}}});
  }
  sel.onchange = redrawDist; redrawDist();

  // Top tables
  function topTbl(key,title){
    const data = RICE.by_wave["2024"];
    const rows = Object.entries(data).filter(([n])=>n!=="__NATIONAL__")
                  .map(([name,r])=>({name,v:r[key]||0,n:r.n_hh,div:(GEO.districts[name]||{}).division}))
                  .sort((a,b)=>b.v-a.v).slice(0,10);
    return `<div class="card"><h4>${title}</h4>
      <table class="tbl"><thead><tr><th>District</th><th>Division</th><th>n</th><th>%</th></tr></thead>
      <tbody>${rows.map(r=>`<tr><td>${r.name}</td><td>${r.div||""}</td><td>${r.n}</td><td>${r.v.toFixed(1)}</td></tr>`).join("")}
      </tbody></table></div>`;
  }
  document.getElementById("riceTopTables").innerHTML =
    topTbl("BRRI_CORE28_29", TXT.tables.rice_1)
  + topTbl("BRRI_NEW_POST2012", TXT.tables.rice_2);

  // Full district-level table (all 4 rounds, all variety families)
  const RICE_TBL_KEYS = ["RICE_GROWER","BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL"];
  renderFullTable(document.getElementById("riceFullTbl"), RICE, RICE_TBL_KEYS, RICE_FAM_LBL, "mixtape_rice_district");
};

/* ==============================  TAB 3 INIT (AQUA)  ============================== */
INITS["t-aqua"] = function(){
  const nat24 = AQUA.by_wave["2024"].__NATIONAL__;
  const cA = COL.teal;
  document.getElementById("kpiAqua").innerHTML = [
    {lbl:TXT.kpi.aqua.pond,        val:nat24.ANY_POND.toFixed(1)+"%",        series:NAT.aqua.ANY_POND,        colour:cA},
    {lbl:TXT.kpi.aqua.tilapia,     val:nat24.TILAPIA.toFixed(1)+"%",         series:NAT.aqua.TILAPIA,         colour:cA},
    {lbl:TXT.kpi.aqua.polyculture, val:nat24.POLY_CARP_2PLUS.toFixed(1)+"%", series:NAT.aqua.POLY_CARP_2PLUS, colour:cA},
    {lbl:TXT.kpi.aqua.mola,        val:nat24.MOLA.toFixed(1)+"%",            series:NAT.aqua.MOLA,            colour:cA}
  ].map(kpiBox).join("");

  lineChart("aquaTS", WAVES.map(w=>WAVE_LBL[w]),
    ["ANY_POND","CARP_ANY","POLY_CARP_2PLUS","TILAPIA","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"].map((k,i)=>({
      label:AQUA_IND_LBL[k], data:NAT.aqua[k], borderColor:SERIES_AQUA[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.aquaTS.title},
              subtitle:{display:true,text:TXT.charts.aquaTS.subtitle}}});

  lineChart("aquaPoly", WAVES.map(w=>WAVE_LBL[w]),
    [{label:AQUA_IND_LBL.POLY_CARP_2PLUS, data:NAT.aqua.POLY_CARP_2PLUS, borderColor:COL.teal},
     {label:AQUA_IND_LBL.MOLA,            data:NAT.aqua.MOLA,           borderColor:COL.teal2}],
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.aquaPoly.title},
              subtitle:{display:true,text:TXT.charts.aquaPoly.subtitle}}});

  const sel = document.getElementById("aquaDistInd");
  ["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"].forEach((k,i)=>{
    const o=document.createElement("option");o.value=k;o.innerHTML=AQUA_IND_LBL[k];if(i===0)o.selected=true;sel.appendChild(o);
  });
  function redrawAquaDist(){
    const k = sel.value;
    const data = AQUA.by_wave["2024"];
    const rows = Object.entries(data).filter(([n])=>n!=="__NATIONAL__")
                  .map(([name,r])=>({name,v:r[k]||0}))
                  .sort((a,b)=>b.v-a.v).slice(0,30);
    barChart("aquaDistChart", rows.map(r=>r.name),
      [{label:AQUA_IND_LBL[k]+" (2024)",data:rows.map(r=>r.v),backgroundColor:COL.teal,borderColor:COL.teal}],
      {plugins:{title:{display:true,text:TXT.charts.top30_template.replace("{label}", AQUA_IND_LBL[k].toLowerCase())}}});
  }
  sel.onchange = redrawAquaDist; redrawAquaDist();

  function topTbl(key,title){
    const rows = Object.entries(AQUA.by_wave["2024"]).filter(([n])=>n!=="__NATIONAL__")
                  .map(([name,r])=>({name,v:r[key]||0,n:r.n_hh,div:(GEO.districts[name]||{}).division}))
                  .sort((a,b)=>b.v-a.v).slice(0,10);
    return `<div class="card"><h4>${title}</h4>
      <table class="tbl"><thead><tr><th>District</th><th>Division</th><th>n</th><th>%</th></tr></thead>
      <tbody>${rows.map(r=>`<tr><td>${r.name}</td><td>${r.div||""}</td><td>${r.n}</td><td>${r.v.toFixed(1)}</td></tr>`).join("")}
      </tbody></table></div>`;
  }
  document.getElementById("aquaTopTables").innerHTML =
    topTbl("ANY_POND", TXT.tables.aqua_1)
  + topTbl("TILAPIA", TXT.tables.aqua_2);

  // Full district-level table. 2011/2015/2019 do not have SUPP_FEED/HORMONE/DISEASE_CTL,
  // but the table helper simply shows blanks for missing columns.
  const AQUA_TBL_KEYS = ["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA","SUPP_FEED","HORMONE","DISEASE_CTL"];
  renderFullTable(document.getElementById("aquaFullTbl"), AQUA, AQUA_TBL_KEYS, AQUA_IND_LBL, "mixtape_aqua_district");
};

/* ==============================  TAB 4 INIT (SPIA)  ============================== */
INITS["t-spia"] = function(){
  document.getElementById("kpiSpia").innerHTML = [
    {lbl:TXT.kpi.spia.samples,    val:DNA.n_samples.toLocaleString()},
    {lbl:TXT.kpi.spia.varieties,  val:DNA.n_varieties},
    {lbl:TXT.kpi.spia.clusters,   val:DNA.n_clusters},
    {lbl:TXT.kpi.spia.households, val:SUM.rounds["2024"].n_hh.toLocaleString()}
  ].map(x=>`<div class="box"><div class="lbl">${x.lbl}</div><div class="big">${x.val}</div></div>`).join("");

  const vEntries = Object.entries(DNA.by_variety).sort((a,b)=>b[1]-a[1]);
  const tot = vEntries.reduce((s,[,v])=>s+v,0);
  const boro = (DNA.by_variety["Bri Dhan BR-28 (Boro)"]||0) + (DNA.by_variety["Bri Dhan BR-29 (Boro)"]||0);
  document.getElementById("dnaBoroPct").innerText = (100*boro/tot).toFixed(1);

  barChart("dnaByVariety", vEntries.map(x=>x[0]),
    [{label:"DNA-verified samples",data:vEntries.map(x=>x[1]),backgroundColor:COL.leaf,borderColor:COL.leaf}],
    {plugins:{title:{display:true,text:TXT.charts.dnaByVariety.title},legend:{display:false}},
     scales:{x:{title:{display:true,text:"samples"}},y:{ticks:{font:{size:10.5}}}}});

  const cl = DNA.by_cluster.slice().sort((a,b)=>b.n_samples-a.n_samples);
  barChart("dnaByCluster", cl.map(r=>"Cluster "+r.cluster_id+" : "+r.top_variety),
    [{label:"Samples in cluster",data:cl.map(r=>r.n_samples),backgroundColor:COL.teal,borderColor:COL.teal}],
    {plugins:{title:{display:true,text:TXT.charts.dnaByCluster.title},legend:{display:false}},
     scales:{x:{title:{display:true,text:"samples"}}}});

  // Aqua practices 2024
  const aqNat24 = AQUA.by_wave["2024"].__NATIONAL__;
  barChart("spiaPractices",
    [AQUA_IND_LBL.SUPP_FEED,AQUA_IND_LBL.HORMONE,AQUA_IND_LBL.DISEASE_CTL],
    [{label:"2024 weighted HH %",data:[aqNat24.SUPP_FEED||0,aqNat24.HORMONE||0,aqNat24.DISEASE_CTL||0],
      backgroundColor:COL.teal,borderColor:COL.teal}],
    {plugins:{title:{display:true,text:TXT.charts.spiaPractices.title},legend:{display:false}}});

  // Equipment ownership 2024
  const mechNat24 = MECH.by_wave["2024"].__NATIONAL__ || {};
  const eq = [["POWER_TILLER","TRACTOR","POWER_THRESHER","PADDLE_THRESHER","TREADLE_PUMP",
               "ROWER_PUMP","AXIAL_FLOW_PUMP","LLP_IRRIG","ELEC_MOTOR_PUMP","DIESEL_MOTOR_PUMP",
               "SPRAYER","REAPER","SEEDER_DRILL","COMBINED_HARVEST","FISHING_NET"]
              .filter(k=>k in mechNat24)
              .map(k=>[MECH_IND_LBL[k],mechNat24[k]||0])
              .sort((a,b)=>b[1]-a[1])];
  barChart("spiaEquip", eq[0].map(x=>x[0]),
    [{label:"HH ownership %",data:eq[0].map(x=>x[1]),backgroundColor:COL.slate,borderColor:COL.slate}],
    {plugins:{title:{display:true,text:TXT.charts.spiaEquip.title},legend:{display:false}}});

  // ---- Pooled 2024 district-level full table (rice + aqua + mech) ----
  const POOLED_2024 = { by_wave: { "2024": {} } };
  const dists = new Set();
  [RICE, AQUA, MECH].forEach(src=>Object.keys(src.by_wave["2024"]||{}).forEach(d=>dists.add(d)));
  dists.forEach(d=>{
    const r = RICE.by_wave["2024"][d]  || {};
    const a = AQUA.by_wave["2024"][d]  || {};
    const m = MECH.by_wave["2024"][d]  || {};
    POOLED_2024.by_wave["2024"][d] = Object.assign({n_hh: r.n_hh||a.n_hh||m.n_hh, weight_sum: r.weight_sum||a.weight_sum||m.weight_sum}, r, a, m);
  });
  const SPIA_TBL_KEYS = [
    "RICE_GROWER","BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL",
    "ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA","SUPP_FEED","HORMONE","DISEASE_CTL",
    "POWER_TILLER","TRACTOR","POWER_THRESHER","SPRAYER","REAPER","COMBINED_HARVEST","LLP_IRRIG","AXIAL_FLOW_PUMP",
    "ELEC_MOTOR_PUMP","DIESEL_MOTOR_PUMP","USE_MOTOR_HARVEST","USE_MOTOR_THRESH"
  ];
  const SPIA_LBL = Object.assign({}, RICE_FAM_LBL, AQUA_IND_LBL, MECH_IND_LBL);
  renderFullTable(document.getElementById("spiaFullTbl"), POOLED_2024, SPIA_TBL_KEYS, SPIA_LBL, "mixtape_spia2024_district",
    {waves:["2024"], defaultWave:"2024", showWavePills:false});

  // ---- DNA raw tables ----
  const vTbl = document.getElementById("spiaDnaVariety");
  const vRows = Object.entries(DNA.by_variety).map(([v,n])=>({variety:v,n,share:100*n/DNA.n_samples}))
                  .sort((a,b)=>b.n-a.n);
  vTbl.innerHTML = `
    <div class="fulltbl-toolbar">
      <span class="meta">n = ${DNA.n_samples} DNA samples · ${DNA.n_varieties} varieties</span>
      <button class="dl">Download CSV</button>
    </div>
    <div class="fulltbl-scroll"><table class="full"><thead><tr>
      <th>Variety</th><th>Samples</th><th>% of sample</th>
    </tr></thead><tbody>${vRows.map(r=>`<tr><td>${r.variety}</td><td>${r.n}</td><td>${r.share.toFixed(2)}</td></tr>`).join("")}</tbody></table></div>`;
  vTbl.querySelector("button.dl").onclick = ()=>csvDownload("mixtape_dna_by_variety.csv", vRows, ["variety","n","share"], ["Variety","Samples","% of sample"]);

  const cTbl = document.getElementById("spiaDnaCluster");
  const cRows = DNA.by_cluster.slice().sort((a,b)=>b.n_samples-a.n_samples);
  cTbl.innerHTML = `
    <div class="fulltbl-toolbar">
      <span class="meta">${DNA.n_clusters} genetic clusters</span>
      <button class="dl">Download CSV</button>
    </div>
    <div class="fulltbl-scroll"><table class="full"><thead><tr>
      <th>Cluster</th><th>Samples</th><th>Distinct varieties</th><th>Top variety</th>
    </tr></thead><tbody>${cRows.map(r=>`<tr><td>${r.cluster_id}</td><td>${r.n_samples}</td><td>${r.n_varieties}</td><td>${r.top_variety}</td></tr>`).join("")}</tbody></table></div>`;
  cTbl.querySelector("button.dl").onclick = ()=>csvDownload("mixtape_dna_by_cluster.csv", cRows,
    ["cluster_id","n_samples","n_varieties","top_variety"], ["Cluster","Samples","Distinct varieties","Top variety"]);
};

/* ==============================  TAB 5 INIT (MECH)  ============================== */
INITS["t-mech"] = function(){
  const m24 = MECH.by_wave["2024"].__NATIONAL__ || {};
  const m19 = MECH.by_wave["2019"].__NATIONAL__ || {};
  const cM = COL.accent;
  // Mech equipment is only consistently tracked from 2018/19 onward; baseline label reflects that.
  const mechSeries = k => NAT.mech && NAT.mech[k] ? NAT.mech[k] : null;
  document.getElementById("kpiMech").innerHTML = [
    {lbl:TXT.kpi.mech.tiller,  val:(m24.POWER_TILLER||0).toFixed(1)+"%",     series:mechSeries("POWER_TILLER"),     colour:cM, baseLbl:"2018/19"},
    {lbl:TXT.kpi.mech.thresh,  val:(m24.USE_MOTOR_THRESH||0).toFixed(1)+"%", series:mechSeries("USE_MOTOR_THRESH"), colour:cM, baseLbl:"2018/19"},
    {lbl:TXT.kpi.mech.sprayer, val:(m24.SPRAYER||0).toFixed(1)+"%",          series:mechSeries("SPRAYER"),          colour:cM, baseLbl:"2018/19"},
    {lbl:TXT.kpi.mech.pump,    val:(m24.ELEC_MOTOR_PUMP||0).toFixed(1)+"%",  series:mechSeries("ELEC_MOTOR_PUMP"),  colour:cM, baseLbl:"2018/19"}
  ].map(kpiBox).join("");

  // Ownership comparison 2019 vs 2024
  const keys = ["TRACTOR","POWER_TILLER","POWER_THRESHER","LLP_IRRIG","AXIAL_FLOW_PUMP",
                "ELEC_MOTOR_PUMP","DIESEL_MOTOR_PUMP","SPRAYER","REAPER","SEEDER_DRILL","COMBINED_HARVEST"];
  const lbls = keys.map(k=>MECH_IND_LBL[k]);
  barChart("mechOwn", lbls,
    [{label:"2018/19",data:keys.map(k=>m19[k]||0),backgroundColor:COL.accent2,borderColor:COL.accent2},
     {label:"2024",   data:keys.map(k=>m24[k]||0),backgroundColor:COL.accent, borderColor:COL.accent}],
    {plugins:{title:{display:true,text:TXT.charts.mechOwn.title}}});

  // Use 2024
  const useKeys = ["USE_MOTOR_HARVEST","USE_MOTOR_THRESH","USE_TREADLE_THRESH"];
  barChart("mechUse", useKeys.map(k=>MECH_IND_LBL[k]),
    [{label:"2024 HH %",data:useKeys.map(k=>m24[k]||0),backgroundColor:COL.accent,borderColor:COL.accent}],
    {plugins:{title:{display:true,text:TXT.charts.mechUse.title},legend:{display:false}}});

  // District chart 2024
  const sel = document.getElementById("mechDistInd");
  const availableInds = Object.keys(MECH.by_wave["2024"]["Dhaka"]||{}).filter(k=>k in MECH_IND_LBL);
  availableInds.forEach((k,i)=>{const o=document.createElement("option");o.value=k;o.innerHTML=MECH_IND_LBL[k];if(k==="POWER_TILLER")o.selected=true;sel.appendChild(o);});
  function redrawMechDist(){
    const k = sel.value;
    const rows = Object.entries(MECH.by_wave["2024"]).filter(([n])=>n!=="__NATIONAL__")
                  .map(([name,r])=>({name,v:r[k]||0}))
                  .sort((a,b)=>b.v-a.v).slice(0,30);
    barChart("mechDistChart", rows.map(r=>r.name),
      [{label:MECH_IND_LBL[k]+" (2024)",data:rows.map(r=>r.v),backgroundColor:COL.accent,borderColor:COL.accent}],
      {plugins:{title:{display:true,text:TXT.charts.top30_template.replace("{label}", MECH_IND_LBL[k].toLowerCase())}}});
  }
  sel.onchange = redrawMechDist; redrawMechDist();

  // Full district level table: one column per equipment indicator, all rounds we have.
  const MECH_TBL_KEYS = ["TRACTOR","POWER_TILLER","POWER_THRESHER","PADDLE_THRESHER","TREADLE_PUMP","ROWER_PUMP",
                         "AXIAL_FLOW_PUMP","LLP_IRRIG","DIESEL_MOTOR_PUMP","ELEC_MOTOR_PUMP","SPRAYER","REAPER",
                         "SEEDER_DRILL","COMBINED_HARVEST","TRANSPLANTER","FISHING_NET",
                         "USE_MOTOR_HARVEST","USE_MOTOR_THRESH","USE_TREADLE_THRESH"];
  renderFullTable(document.getElementById("mechFullTbl"), MECH, MECH_TBL_KEYS, MECH_IND_LBL, "mixtape_mech_district");
};

/* ==============================  TAB 6 INIT (TECH INDEX)  ============================== */
INITS["t-tech"] = function(){
  // Category color mapping (for the colored chip on each card)
  const CAT_CLASS = {rice:"rice", wheat:"rice", maize:"rice", potato:"rice", sweetpotato:"rice",
                     lentil:"rice", groundnut:"rice", chickpea:"rice",
                     aqua:"aqua", nrm:"aqua", mech:"mech"};
  const CAT_LABEL = {}; TECH.categories.forEach(c => CAT_LABEL[c.id] = c.label);

  // Primary reference card
  const ref = TECH.primary_reference;
  document.getElementById("primaryRef").innerHTML = `
    <div class="ref-card">
      <div class="ref-eyebrow">${TXT.tech.primary_ref_eyebrow}</div>
      <div class="ref-title">${ref.title}</div>
      <div class="ref-meta">${ref.authors} (${ref.year}). <em>${ref.publisher}</em>. ${ref.license}.</div>
      <div class="ref-links">
        <a href="${ref.report_url}" target="_blank" rel="noopener">${TXT.tech.report_link_label}</a>
        <a href="${ref.github_url}" target="_blank" rel="noopener">${TXT.tech.github_link_label}</a>
      </div>
      <div class="ref-note">${ref.note}</div>
    </div>`;

  // Institutions grid
  const instHtml = TECH.institutions.map(i => `
    <div class="inst-card">
      <div class="inst-acro">${i.acronym}</div>
      <div class="inst-name">${i.name}</div>
      <div class="inst-role">${i.role}</div>
      <div class="inst-links">
        ${i.links.map(l => `<a href="${l.url}" target="_blank" rel="noopener">${l.title}</a>`).join("")}
      </div>
    </div>`).join("");
  document.getElementById("instGrid").innerHTML = instHtml;

  // Category pills
  const pills = document.getElementById("techCatPills");
  const cats = [{id:"all", label:"All"}].concat(TECH.categories);
  pills.innerHTML = cats.map((c,i) =>
    `<button data-cat="${c.id}" class="${i===0?"on":""}">${c.label}</button>`).join("");

  let activeCat = "all";
  let searchQ = "";

  function matchesSearch(t){
    if(!searchQ) return true;
    const q = searchQ.toLowerCase();
    return [t.code, t.name, t.description, t.developer, t.cgiar_origin, t.type, t.season, t.species]
      .filter(Boolean).join(" ").toLowerCase().includes(q);
  }
  function render(){
    const rows = TECH.technologies.filter(t =>
      (activeCat==="all" || t.category===activeCat) && matchesSearch(t));
    document.getElementById("techCount").textContent = rows.length + " technology" + (rows.length===1?"":"s");
    const html = rows.map(t => {
      const chipCat = CAT_CLASS[t.category] || "rice";
      const yearStr = t.year ? t.year : "";
      const meta = [t.season, t.species, t.developer].filter(Boolean).join(" · ");
      const cgiarBadge = t.cgiar_origin ? `<span class="cgiar-badge">CGIAR: ${t.cgiar_origin}</span>` : "";
      const srcs = (t.sources||[]).map(s =>
        `<a href="${s.url}" target="_blank" rel="noopener">${s.title}</a>`).join("");
      return `
        <article class="tech-card">
          <div class="tech-head">
            <span class="tech-chip chip-${chipCat}">${CAT_LABEL[t.category]||t.category}</span>
            <span class="tech-year">${yearStr}</span>
          </div>
          <h4 class="tech-name">${t.name}</h4>
          <div class="tech-meta">${meta}</div>
          ${cgiarBadge}
          <p class="tech-desc">${t.description}</p>
          <div class="tech-srcs">${srcs}</div>
        </article>`;
    }).join("");
    document.getElementById("techGrid").innerHTML = html || `<div class="empty">${TXT.tech.no_match}</div>`;
  }
  pills.addEventListener("click", e => {
    const btn = e.target.closest("button"); if(!btn) return;
    activeCat = btn.dataset.cat;
    pills.querySelectorAll("button").forEach(b => b.classList.toggle("on", b===btn));
    render();
  });
  document.getElementById("techSearch").addEventListener("input", e => {
    searchQ = e.target.value; render();
  });
  render();
};

// kick off first tab
lazyInit("t-map");
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------
# Compose HTML fragments from content.toml
# ---------------------------------------------------------------------
def _root_vars():
    t = THEME
    pairs = [
        ("--ink", t["ink"]), ("--text", t["text"]), ("--mute", t["mute"]),
        ("--line", t["line"]), ("--line2", t["line2"]), ("--bg", t["background"]),
        ("--panel", t["panel"]), ("--tint", t["tint"]),
        ("--rail-bg", t["rail_background"]),
        ("--positive", t["positive"]), ("--negative", t["negative"]),
        ("--rice", t["rice"]["main"]), ("--rice-dark", t["rice"]["dark"]), ("--rice-soft", t["rice"]["soft"]),
        ("--aqua", t["aqua"]["main"]), ("--aqua-dark", t["aqua"]["dark"]), ("--aqua-soft", t["aqua"]["soft"]),
        ("--mech", t["mech"]["main"]), ("--mech-dark", t["mech"]["dark"]), ("--mech-soft", t["mech"]["soft"]),
    ]
    return "\n".join(f"    {k}:{v};" for k, v in pairs)

def _nav_tabs():
    out = []
    for i, t in enumerate(C["tabs"]):
        on = ' class="on"' if i == 0 else ""
        out.append(f'    <button data-tab="{t["id"]}"{on}>'
                   f'<span class="num">{i+1:02d}</span><span>{t["label"]}</span></button>')
    return "\n".join(out)

def _rail_rows(rows):
    return "\n".join(f'    <div class="row"><span>{a}</span><span>{b}</span></div>'
                     for a, b in rows)

def _findings():
    out = []
    for f in C["findings"]:
        delta_cls = f' {f["delta_class"]}' if f["delta_class"] else ""
        out.append(
            f'    <a class="finding f-{f["category"]}" data-jump="{f["tab"]}" tabindex="0">\n'
            f'      <span class="arrow">{f["arrow"]} ›</span>\n'
            f'      <div class="eyebrow">{f["eyebrow"]}</div>\n'
            f'      <div class="big">{f["value"]}<span class="unit">{f["unit"]}</span></div>\n'
            f'      <div class="ctx">{f["context"]}</div>\n'
            f'      <div class="delta{delta_cls}">{f["delta"]}</div>\n'
            f'    </a>')
    return "\n".join(out)

def _denom_grid():
    return "\n".join(
        f'        <div class="cell"><div class="yr">{y}</div><div class="all">{a}</div><div class="agri">{g}</div></div>'
        for y, a, g in C["method"]["denominators"])

def _cat_pills():
    out = []
    for i, (cid, lbl) in enumerate(C["map"]["category_pills"]):
        on = " on" if i == 0 else ""
        out.append(f'      <button class="pill{on}" data-cat="{cid}">{lbl}</button>')
    return "\n".join(out)

P, R, M = C["page"], C["rail"], C["map"]
RC, AQ, SP, ME, TE = C["rice"], C["aqua"], C["spia"], C["mech"], C["tech"]
REF = SP["reference"]

REPL = {
    "__LOGO__": LOGO_B64,
    "__ROOT_VARS__": _root_vars(),
    # data
    "__GEO__": j(GEO), "__RICE__": j(RICE), "__AQUA__": j(AQUA), "__MECH__": j(MECH),
    "__DNA__": j(DNA), "__NAT__": j(NAT), "__SUM__": j(SUM), "__TECH__": j(TECH),
    "__TXT__": j(TXT_JS), "__THEME__": j(THEME),
    # page header
    "__PAGE_TITLE__": P["title"], "__PAGE_EYEBROW__": P["eyebrow"], "__PAGE_H1__": P["heading"],
    "__PAGE_META_LEFT__": P["meta_left"], "__PAGE_META_RIGHT__": P["meta_right"],
    "__BRIEF__": P["brief"],
    # side rail
    "__RAIL_ACRO__": R["brand_acronym"], "__RAIL_SUBTITLE__": R["brand_subtitle"],
    "__NAV_TABS__": _nav_tabs(),
    "__RAIL_PANEL_LBL__": R["panel_label"], "__RAIL_PANEL_ROWS__": _rail_rows(R["panel_rows"]),
    "__RAIL_AGRI_LBL__": R["agri_label"], "__RAIL_AGRI_ROWS__": _rail_rows(R["agri_rows"]),
    "__RAIL_NOTE__": R["note"],
    "__RAIL_CONTACT_NAME__": R["contact_name"], "__RAIL_CONTACT_EMAIL__": R["contact_email"],
    "__RAIL_CONTACT_AFFIL__": R["contact_affiliation"],
    "__RAIL_REPL_TEXT__": R["replication_text"], "__RAIL_REPL_URL__": R["replication_link_url"],
    "__RAIL_REPL_LABEL__": R["replication_link_label"],
    # map tab
    "__MAP_H2__": M["heading"], "__MAP_LEDE__": M["lede"],
    "__FINDINGS__": _findings(),
    "__METHOD_SUMMARY__": C["method"]["summary"], "__METHOD_BODY__": C["method"]["body"],
    "__DENOM_GRID__": _denom_grid(), "__METHOD_CAP__": C["method"]["caption"],
    "__MAP_SUB_MAP__": M["map_heading"], "__MAP_LEDE_MAP__": M["map_lede"],
    "__MAP_CAT_PILLS__": _cat_pills(),
    "__MAP_INFO_TITLE__": M["info_title"], "__MAP_INFO_HINT__": M["info_hover_hint"],
    "__MAP_TOP_LBL__": M["top_list_label"], "__MAP_BOT_LBL__": M["bottom_list_label"],
    "__MAP_SUB_TREND__": M["trend_heading"], "__MAP_LEDE_TREND__": M["trend_lede"],
    "__MAP_NOTE__": M["note"],
    # rice tab
    "__RICE_H2__": RC["heading"], "__RICE_LEDE__": RC["lede"],
    "__RICE_SUB_DIST__": RC["district_heading"], "__RICE_SUB_TOP__": RC["top_heading"],
    "__RICE_SUB_FULL__": RC["full_heading"], "__RICE_LEDE_FULL__": RC["full_lede"],
    "__RICE_NOTE__": RC["note"],
    # aqua tab
    "__AQUA_H2__": AQ["heading"], "__AQUA_LEDE__": AQ["lede"],
    "__AQUA_SUB_DIST__": AQ["district_heading"], "__AQUA_SUB_TOP__": AQ["top_heading"],
    "__AQUA_SUB_FULL__": AQ["full_heading"], "__AQUA_LEDE_FULL__": AQ["full_lede"],
    "__AQUA_NOTE__": AQ["note"],
    # spia tab
    "__SPIA_H2__": SP["heading"], "__SPIA_LEDE__": SP["lede"],
    "__SPIA_REF_EYEBROW__": REF["eyebrow"], "__SPIA_REF_TITLE__": REF["title"],
    "__SPIA_REF_CITATION__": REF["citation"],
    "__SPIA_REF_REPORT_URL__": REF["report_url"], "__SPIA_REF_REPORT_LABEL__": REF["report_label"],
    "__SPIA_REF_GITHUB_URL__": REF["github_url"], "__SPIA_REF_GITHUB_LABEL__": REF["github_label"],
    "__SPIA_REF_NOTE__": REF["note"],
    "__SPIA_SUB_DNA__": SP["dna_heading"], "__SPIA_LEDE_DNA__": SP["dna_lede"],
    "__SPIA_SUB_PRACT__": SP["practices_heading"], "__SPIA_LEDE_PRACT__": SP["practices_lede"],
    "__SPIA_SUB_EQUIP__": SP["equipment_heading"],
    "__SPIA_SUB_FULL__": SP["full_heading"], "__SPIA_LEDE_FULL__": SP["full_lede"],
    "__SPIA_SUB_DNAVAR__": SP["dna_variety_heading"], "__SPIA_LEDE_DNAVAR__": SP["dna_variety_lede"],
    "__SPIA_SUB_DNACLUST__": SP["dna_cluster_heading"], "__SPIA_LEDE_DNACLUST__": SP["dna_cluster_lede"],
    "__SPIA_NOTE__": SP["note"],
    # mech tab
    "__MECH_H2__": ME["heading"], "__MECH_LEDE__": ME["lede"],
    "__MECH_SUB_DIST__": ME["district_heading"],
    "__MECH_SUB_FULL__": ME["full_heading"], "__MECH_LEDE_FULL__": ME["full_lede"],
    "__MECH_NOTE__": ME["note"],
    # tech tab
    "__TECH_H2__": TE["heading"], "__TECH_LEDE__": TE["lede"],
    "__TECH_SUB_INST__": TE["institutions_heading"], "__TECH_SUB_BROWSE__": TE["browse_heading"],
    "__TECH_SEARCH_PH__": TE["search_placeholder"],
    # footer
    "__FOOT_NAME__": R["contact_name"], "__FOOT_EMAIL__": R["contact_email"],
    "__FOOT_AFFIL__": R["contact_affiliation"], "__FOOT_ATTRIB__": C["footer"]["attribution"],
}

html_out = HTML_TMPL
for key, val in REPL.items():
    html_out = html_out.replace(key, val)

out_path = os.path.join(ROOT, "index.html")
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write(html_out)
print(f"wrote {out_path}  ({os.path.getsize(out_path):,} bytes)")
