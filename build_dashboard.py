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
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,system-ui,sans-serif;
      line-height:1.45;-webkit-font-smoothing:antialiased;font-size:13.5px}
  a{color:var(--accent)}

  /* Layout: fixed side rail, main measure-limited column */
  .layout{display:grid;grid-template-columns:196px minmax(0,1fr);
      max-width:1500px;margin:0 auto;min-height:100vh}
  @media (max-width:980px){.layout{grid-template-columns:1fr}}

  /* ---------------- Side rail ---------------- */
  aside.rail{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;
      padding:22px 22px 22px 0;border-right:1px solid var(--line);background:var(--bg)}
  aside.rail::-webkit-scrollbar{width:5px}
  aside.rail::-webkit-scrollbar-thumb{background:var(--line2)}
  @media (max-width:980px){
    aside.rail{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);
        padding:14px 16px 0}
  }
  .brand{display:flex;align-items:baseline;gap:8px;margin-bottom:18px}
  .brand img{width:26px;height:26px;flex-shrink:0;object-fit:contain;align-self:center;
      mix-blend-mode:multiply}
  .brand .name{min-width:0}
  .brand .acro{font-size:15px;font-weight:700;color:var(--ink);letter-spacing:.01em;line-height:1.1}
  .brand .full{font-size:12px;color:var(--mute);line-height:1.3;margin-top:2px}

  /* Nav: plain text list, active marked by weight and a rule. No fills, no numbers. */
  nav.tabs{display:flex;flex-direction:column;margin:0 0 18px}
  nav.tabs button{font-family:inherit;background:none;border:0;border-left:2px solid transparent;
      padding:3px 0 3px 10px;margin-left:-12px;font-size:13px;color:var(--text);cursor:pointer;
      font-weight:400;text-align:left;line-height:1.35}
  nav.tabs button:hover{color:var(--ink)}
  nav.tabs button.on{color:var(--ink);font-weight:600;border-left-color:var(--accent)}
  @media (max-width:980px){
    nav.tabs{flex-direction:row;overflow-x:auto;gap:18px;margin:10px 0 0;
        scrollbar-width:none;border-bottom:1px solid var(--line)}
    nav.tabs::-webkit-scrollbar{display:none}
    nav.tabs button{border-left:0;border-bottom:2px solid transparent;margin:0;padding:8px 0;
        white-space:nowrap;flex-shrink:0}
    nav.tabs button.on{border-bottom-color:var(--accent)}
  }

  /* Rail figures: a small plain table, not a stat panel */
  .rail-meta{font-size:11.5px;color:var(--mute);padding-top:13px;border-top:1px solid var(--line)}
  .rail-meta .lbl{color:var(--ink);font-weight:600;margin-bottom:5px;font-size:12px}
  .rail-meta table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;
      margin-bottom:10px}
  .rail-meta td{padding:0;font-size:11.5px}
  .rail-meta td:last-child{text-align:right;color:var(--ink)}
  .rail-meta .foot{line-height:1.45;padding-top:2px}
  .rail-foot{margin-top:16px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;
      color:var(--mute);line-height:1.5}
  .rail-foot a{color:var(--accent)}
  @media (max-width:980px){.rail-meta,.rail-foot{display:none}}

  /* ---------------- Main column ---------------- */
  main.wrap{padding:22px 24px 70px 32px;max-width:1140px;width:100%;min-width:0}
  @media (max-width:980px){main.wrap{padding:16px 14px 48px}}

  header.title{padding-bottom:10px;margin-bottom:14px;border-bottom:2px solid var(--ink)}
  header.title h1{margin:0;font-size:21px;line-height:1.18;letter-spacing:-.015em;color:var(--ink);
      font-weight:700;max-width:34em}
  header.title .meta{margin-top:5px;font-size:12px;color:var(--mute);line-height:1.4}
  header.title .meta b{font-weight:600;color:var(--text)}
  @media (max-width:680px){header.title h1{font-size:18px}}

  .brief{margin:0 0 16px;font-size:13.5px;color:var(--text);max-width:46em;line-height:1.55}
  @media (max-width:680px){
    .brief{font-size:14px;max-height:6em;overflow:hidden;position:relative;cursor:pointer}
    .brief::after{content:"Show more";position:absolute;bottom:0;right:0;
        background:linear-gradient(to right,transparent 0,var(--bg) 40%);padding-left:30px;
        color:var(--accent);font-size:13px}
    .brief.open{max-height:none;cursor:default}
    .brief.open::after{display:none}
  }

  .tab{display:none}
  .tab.on{display:block}

  /* Headings: sentence case, plain weight contrast, no kickers */
  h2.section{font-size:17px;color:var(--ink);margin:24px 0 5px;letter-spacing:-.01em;
      font-weight:700;line-height:1.25;max-width:40em}
  h2.section:first-of-type{margin-top:0}
  h3.sub{font-size:13.5px;color:var(--ink);margin:22px 0 4px;font-weight:700}
  p.lede{color:var(--text);font-size:13.5px;margin:4px 0 12px;max-width:46em;line-height:1.55}
  p.note{font-size:12px;color:var(--mute);margin:8px 0 16px;max-width:56em;line-height:1.5;
      padding-top:7px;border-top:1px solid var(--line)}
  @media (max-width:680px){
    h2.section{font-size:16px}
    p.lede{font-size:13px}
  }

  .row{display:grid;gap:20px}
  .row-2{grid-template-columns:1fr 1fr}
  @media (max-width:920px){.row-2{grid-template-columns:1fr}}

  /* ---------------- Data tables (the primary display device) ---------------- */
  /* Report style: no vertical rules, no fills, rule under the header, rule under
     the last row. Numbers right-aligned and tabular. */
  table.data{width:100%;border-collapse:collapse;font-size:12.5px;
      font-variant-numeric:tabular-nums;margin:2px 0 4px}
  table.data caption{caption-side:top;text-align:left;font-size:12.5px;color:var(--ink);
      font-weight:700;padding-bottom:5px}
  table.data th,table.data td{padding:3px 10px;text-align:right;white-space:nowrap}
  table.data th:first-child,table.data td:first-child{text-align:left;padding-left:0;
      font-variant-numeric:normal;white-space:normal}
  table.data th:last-child,table.data td:last-child{padding-right:0}
  table.data thead th{font-weight:600;color:var(--mute);font-size:11.5px;
      border-bottom:1px solid var(--ink);padding-bottom:4px}
  table.data tbody td{border-bottom:1px solid var(--line)}
  table.data tbody tr:last-child td{border-bottom:1px solid var(--line2)}
  table.data td.chg{color:var(--mute)}
  table.data td.num{color:var(--ink)}
  table.data tr.lead td{font-weight:600;color:var(--ink)}
  table.data .unit{color:var(--mute);font-weight:400}
  table.data td.dim{color:var(--mute)}

  /* Compact figure line used above the map: label over value, no boxes */
  .statline{display:flex;flex-wrap:wrap;gap:0 40px;margin:10px 0 12px;padding:8px 0;
      border-top:1px solid var(--ink);border-bottom:1px solid var(--line)}
  .statline .item{min-width:0}
  .statline .k{font-size:12.5px;color:var(--mute);margin-bottom:1px}
  .statline .v{font-size:15px;color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums;
      letter-spacing:-.01em}
  .statline .v small{font-size:12.5px;color:var(--mute);font-weight:400;letter-spacing:0}

  /* ---------------- Map ---------------- */
  .map-wrap{position:relative;height:560px;overflow:hidden;background:#fff;
      border:1px solid var(--line)}
  @media (max-width:980px){.map-wrap{height:400px}}
  .map-pair{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:22px;margin-top:6px}
  @media (max-width:980px){.map-pair{grid-template-columns:1fr}}
  .map-side .blk{margin-bottom:18px}
  .map-side .blk .lbl{font-size:12.5px;color:var(--ink);font-weight:700;margin-bottom:5px;
      padding-bottom:4px;border-bottom:1px solid var(--ink)}
  .map-side .blk ol{margin:0;padding:0;list-style:none;font-size:13px}
  .map-side .blk li{display:flex;justify-content:space-between;gap:8px;padding:3px 0;
      border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
  .map-side .blk li span:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .map-side .blk li span:last-child{color:var(--ink);flex-shrink:0}
  .map-side .blk .empty{color:var(--mute);font-size:12.5px}

  .ind-gloss{font-size:13px;color:var(--text);margin:0 0 10px;max-width:56em;line-height:1.5;
      padding-left:11px;border-left:2px solid var(--line2)}
  .ind-gloss em{color:var(--mute);font-style:normal;font-size:12.5px;display:block;margin-top:4px}

  .leaflet-container{background:#fff;font-family:inherit}
  .leaflet-top.leaflet-left{display:none}
  .leaflet-top.leaflet-right{top:10px;right:10px}
  .leaflet-bar{border:1px solid var(--line2) !important;border-radius:0 !important;
      box-shadow:none !important}
  .leaflet-bar a,.leaflet-bar a:hover{background:#fff;color:var(--ink);border-radius:0 !important}
  .leaflet-bar a:hover{background:var(--tint)}

  .info{position:absolute;top:10px;left:10px;background:#fff;padding:9px 12px;font-size:12.5px;
      color:var(--ink);max-width:230px;z-index:500;border:1px solid var(--line2)}
  .info h5{margin:0 0 3px;font-size:12.5px;color:var(--ink);font-weight:700}
  .info .val{font-size:19px;color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums;
      display:block;margin:1px 0;letter-spacing:-.01em}
  .info .cap{font-size:11.5px;color:var(--mute);display:block;line-height:1.4}
  .mini-legend{position:absolute;bottom:12px;left:10px;background:#fff;padding:9px 11px;
      font-size:12px;color:var(--text);z-index:500;max-width:215px;border:1px solid var(--line2);
      line-height:1.45}
  .mini-legend b{display:block;color:var(--ink);font-size:12px;margin-bottom:3px;font-weight:700}
  .mini-legend .sub{display:block;color:var(--mute);font-size:11.5px;margin-bottom:5px}
  .mini-legend .row-l{display:flex;gap:7px;align-items:center;margin:1px 0;
      font-variant-numeric:tabular-nums}
  .mini-legend .sw{width:18px;height:9px;display:inline-block}
  @media (max-width:680px){.info,.mini-legend{max-width:165px;font-size:11.5px}}

  /* ---------------- Charts ---------------- */
  .chart-wrap{position:relative;height:290px;padding:0}
  .chart-wrap.tall{height:420px}
  @media (max-width:680px){.chart-wrap{height:270px}.chart-wrap.tall{height:340px}}

  /* ---------------- Controls: plain, square, unfilled ---------------- */
  .controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin:12px 0 14px}
  .controls label{font-size:13px;color:var(--mute)}
  .controls select,.tech-search,input.search{font-family:inherit;font-size:13.5px;
      padding:5px 26px 5px 8px;border:1px solid var(--line2);background:#fff;color:var(--ink);
      cursor:pointer;min-width:250px;max-width:100%;appearance:none;border-radius:0;
      background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'><path d='M3 4.5l3 3 3-3' stroke='%232b2b2b' stroke-width='1.3' fill='none' stroke-linecap='round'/></svg>");
      background-repeat:no-repeat;background-position:right 8px center;background-size:11px}
  .tech-search,input.search{cursor:text;background-image:none;padding-right:8px;min-width:210px}
  .controls select:focus,.tech-search:focus,input.search:focus{outline:1px solid var(--accent);
      outline-offset:0}
  @media (max-width:680px){.controls select{min-width:0;width:100%}}

  /* Segmented switches: text buttons separated by rules, active is underlined */
  .cat-pills,.year-pills,.wave-pills{display:inline-flex;gap:0}
  .cat-pills button,.year-pills button,.wave-pills button{font-family:inherit;font-size:13.5px;
      padding:4px 11px;border:0;border-bottom:2px solid transparent;background:none;
      color:var(--mute);cursor:pointer;border-radius:0}
  .cat-pills button:first-child,.year-pills button:first-child,.wave-pills button:first-child{
      padding-left:0}
  .cat-pills button:hover,.year-pills button:hover,.wave-pills button:hover{color:var(--ink)}
  .cat-pills button.on,.year-pills button.on,.wave-pills button.on{color:var(--ink);
      font-weight:600;border-bottom-color:var(--accent)}

  /* ---------------- Scrollable full tables ---------------- */
  .fulltbl-wrap{margin:6px 0 4px}
  .fulltbl-toolbar{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:0 0 9px}
  .fulltbl-toolbar .dl{font-family:inherit;font-size:13px;padding:4px 10px;background:none;
      color:var(--accent);border:1px solid var(--line2);border-radius:0;cursor:pointer}
  .fulltbl-toolbar .dl:hover{border-color:var(--accent)}
  .fulltbl-toolbar .meta{color:var(--mute);font-size:12.5px;margin-left:auto;
      font-variant-numeric:tabular-nums}
  .fulltbl-scroll{max-height:460px;overflow:auto;border:1px solid var(--line)}
  table.full{width:100%;border-collapse:collapse;font-size:12px;background:#fff;
      font-variant-numeric:tabular-nums}
  table.full thead th{position:sticky;top:0;background:#fff;color:var(--ink);padding:7px 10px;
      text-align:right;font-weight:600;font-size:12px;white-space:nowrap;cursor:pointer;
      user-select:none;border-bottom:1px solid var(--ink);font-variant-numeric:normal}
  table.full thead th:first-child,table.full thead th:nth-child(2){text-align:left}
  table.full thead th .arr{color:var(--line2);margin-left:3px;font-size:9px}
  table.full thead th.sort-asc .arr,table.full thead th.sort-desc .arr{color:var(--accent)}
  table.full tbody td{padding:3px 9px;border-bottom:1px solid var(--line);text-align:right;
      white-space:nowrap}
  table.full tbody td:first-child,table.full tbody td:nth-child(2){text-align:left;color:var(--ink);
      font-variant-numeric:normal}
  table.full tbody tr:hover{background:var(--tint)}
  table.full tbody tr.natrow td{font-weight:600;color:var(--ink);
      border-bottom:1px solid var(--ink)}

  /* ---------------- Expandable notes ---------------- */
  details.method,details.tech{border-top:1px solid var(--line);border-bottom:1px solid var(--line);
      padding:9px 0;margin:0 0 18px;font-size:13.5px;color:var(--text)}
  details.method summary,details.tech summary{cursor:pointer;color:var(--ink);font-size:13.5px;
      font-weight:600;list-style:none;line-height:1.4}
  details.method summary::-webkit-details-marker,
  details.tech summary::-webkit-details-marker{display:none}
  details.method summary::before,details.tech summary::before{content:"+";display:inline-block;
      margin-right:8px;color:var(--accent);width:9px;font-weight:600}
  details.method[open] summary::before,details.tech[open] summary::before{content:"\2212"}
  details.method .body{margin-top:9px;line-height:1.55;max-width:56em}
  details.method .body b{color:var(--ink)}
  small.cap{color:var(--mute);font-size:12.5px;line-height:1.5;display:block;margin-top:9px}

  /* ---------------- Technology index ---------------- */
  .ref-card{border-left:2px solid var(--accent);padding:2px 0 2px 14px;margin:10px 0 24px;
      max-width:44em}
  .ref-title{font-size:15px;color:var(--ink);font-weight:700;line-height:1.35;margin-bottom:3px}
  .ref-meta{font-size:13px;color:var(--text);line-height:1.5;margin-bottom:6px}
  .ref-links{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:7px}
  .ref-links a{font-size:13px;color:var(--accent)}
  .ref-note{font-size:12.5px;color:var(--mute);line-height:1.5}
  .ref-eyebrow{display:none}

  .inst-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px 24px;margin:8px 0 24px;
      padding-top:12px;border-top:1px solid var(--line)}
  @media (max-width:1100px){.inst-grid{grid-template-columns:repeat(3,1fr)}}
  @media (max-width:980px){.inst-grid{grid-template-columns:repeat(2,1fr)}}
  @media (max-width:680px){.inst-grid{grid-template-columns:1fr}}
  .inst-card{min-width:0}
  .inst-acro{display:none}
  .inst-name{font-size:13.5px;color:var(--ink);font-weight:700;margin-bottom:4px;line-height:1.3}
  .inst-role{font-size:12.5px;color:var(--text);line-height:1.5;margin-bottom:6px}
  .inst-links{display:flex;flex-direction:column;gap:2px}
  .inst-links a{font-size:12.5px;color:var(--accent);line-height:1.4}

  .tech-count{font-size:12.5px;color:var(--mute);font-variant-numeric:tabular-nums;margin-left:auto}
  .tech-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px 26px;margin-top:12px;
      padding-top:14px;border-top:1px solid var(--line)}
  @media (max-width:1100px){.tech-grid{grid-template-columns:repeat(2,1fr)}}
  @media (max-width:820px){.tech-grid{grid-template-columns:1fr}}
  .tech-card{min-width:0;padding-bottom:18px;border-bottom:1px solid var(--line)}
  .tech-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;
      margin-bottom:3px;font-size:12.5px;color:var(--mute)}
  .tech-chip{font-weight:400}
  .tech-year{font-variant-numeric:tabular-nums}
  .tech-name{margin:0 0 3px;font-size:14.5px;color:var(--ink);font-weight:700;line-height:1.3}
  .tech-meta{font-size:12.5px;color:var(--mute);line-height:1.45;margin-bottom:6px}
  .cgiar-badge{display:inline;font-size:12.5px;color:var(--mute)}
  .tech-desc{font-size:13.5px;color:var(--text);line-height:1.55;margin:0 0 8px}
  .tech-srcs{display:flex;flex-direction:column;gap:2px}
  .tech-srcs a{font-size:12.5px;color:var(--accent);line-height:1.4}
  .empty{padding:20px 0;color:var(--mute);font-size:13.5px}

  /* ---------------- Footer ---------------- */
  .footer{margin-top:56px;padding-top:16px;border-top:1px solid var(--ink);font-size:12.5px;
      color:var(--mute);max-width:46em}
  .footer .contact{color:var(--ink);font-size:13.5px;margin-bottom:6px}
  .footer .attrib{line-height:1.55}
  .src{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:11.5px;
      color:var(--mute)}
</style>
</head>
<body>
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
    <table>__RAIL_PANEL_ROWS__</table>
    <div class="lbl">__RAIL_AGRI_LBL__</div>
    <table>__RAIL_AGRI_ROWS__</table>
    <div class="foot">__RAIL_NOTE__</div>
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
  <h1>__PAGE_H1__</h1>
  <div class="meta">__PAGE_META_LEFT__. __PAGE_META_RIGHT__</div>
</header>

<div class="brief">__BRIEF__</div>

<!-- ============================== TAB 1 :: MAP ============================== -->
<section id="t-map" class="tab on">
  <h2 class="section">__MAP_H2__</h2>
  <p class="lede">__MAP_LEDE__</p>

  __SUMMARY_TABLE__
  <p class="note">__SUMMARY_NOTE__</p>

  <details class="method">
    <summary>__METHOD_SUMMARY__</summary>
    <div class="body">
      __METHOD_BODY__
      __DENOM_GRID__
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

  <div class="statline" id="statMap"></div>

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

  __RICE_KEYFIG__

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

  __AQUA_KEYFIG__

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

  __SPIA_KEYFIG__

  <h3 class="sub">__SPIA_SUB_DNA__</h3>
  <p class="lede">__SPIA_LEDE_DNA__</p>
  <div class="row row-2">
    <div class="chart-wrap tall"><canvas id="dnaByVariety"></canvas></div>
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

  __MECH_KEYFIG__

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

/* ==============================  COLOURS  ============================== */
/* One accent from content.toml; everything else is neutral grey. The accent is
   reserved for the series a chart is asking the reader to follow. */
const COL = {ink:THEME.ink, mute:THEME.mute, chartText:THEME.chart_text,
             accent:THEME.accent, accentDark:THEME.accent_dark,
             grey:"#3c3c3c", grey2:"#9a9a9a"};
const SERIES = THEME.series;
/* Kept as aliases so chart call sites stay readable. */
const SERIES_RICE = SERIES, SERIES_AQUA = SERIES, SERIES_MECH = SERIES;

Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
Chart.defaults.font.size   = 11.5;
Chart.defaults.color       = COL.chartText;
Chart.defaults.borderColor = THEME.line;
Chart.defaults.plugins.legend.labels.boxWidth = 10;
Chart.defaults.plugins.legend.labels.boxHeight = 2;
Chart.defaults.plugins.legend.labels.padding = 8;
Chart.defaults.plugins.legend.labels.font = {size: 11};
Chart.defaults.plugins.legend.align = "start";
Chart.defaults.plugins.title.align = "start";
Chart.defaults.plugins.title.color = COL.ink;
Chart.defaults.plugins.title.font = {size: 13, weight: "700"};
Chart.defaults.plugins.title.padding = {bottom: 4};
Chart.defaults.plugins.subtitle.align = "start";
Chart.defaults.plugins.subtitle.color = COL.mute;
Chart.defaults.plugins.subtitle.font = {size: 11.5, weight: "400"};
Chart.defaults.plugins.subtitle.padding = {bottom: 10};

/* ==============================  TABS  ============================== */
const chartRefs = {};
const tabInit   = {};
document.getElementById("tabs").addEventListener("click", e => {
  const btn = e.target.closest("button"); if(!btn) return;
  const id = btn.dataset.tab;
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.toggle("on", b === btn));
  document.querySelectorAll("section.tab").forEach(s => s.classList.toggle("on", s.id === id));
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
const MAP_STOPS = THEME.map_ramp;
function stopsFor(ind){ return MAP_STOPS; }
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
          layer.setStyle({weight:2,color:COL.ink});
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
    deltaTxt = `${d >= 0 ? "+" : "−"}${Math.abs(d).toFixed(1)} pp <small>since ${firstWaveLbl}</small>`;
  }
  const top = rows[0], bot = rows[rows.length-1];
  const kpiEl = document.getElementById("statMap");
  if(kpiEl){
    const fmtPct = v => (v==null||isNaN(v)) ? "n/a" : v.toFixed(1)+"%";
    const distFmt = r => `${r.name} <small>${fmtPct(r.v)}</small>`;
    kpiEl.innerHTML = [
      {lbl:TXT.map.kpi_national.replace("{year}", WAVE_LBL[year]), val:fmtPct(natNow)},
      {lbl:TXT.map.kpi_change,  val:deltaTxt},
      {lbl:TXT.map.kpi_highest, val: top ? distFmt(top) : "n/a"},
      {lbl:TXT.map.kpi_lowest,  val: bot ? distFmt(bot) : "n/a"}
    ].map(o => `<div class="item"><div class="k">${o.lbl}</div><div class="v">${o.val}</div></div>`).join("");
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
      title: { display: !!(opts.plugins && opts.plugins.title), align: "start", color: COL.ink, font: { size: 13, weight: "700" }, padding: { bottom: 4 } },
      subtitle: { display: !!(opts.plugins && opts.plugins.subtitle), align: "start", color: COL.mute, font: { size: 11.5, style: "normal" }, padding: { bottom: 10 } },
      legend: { position: "top", align: "start", labels: { boxWidth: 10, boxHeight: 2, padding: 6, font: { size: 11 } } },
      tooltip: { mode: "index", intersect: false }
    },
    scales: {
      y: { beginAtZero: true, border: { display: false }, grid: { color: THEME.chart_grid, drawTicks: false, borderDash: [4,4] }, ticks: { callback: v => v + "%" }, title: { display: false } },
      x: { grid: { display: false }, border: { color: THEME.line2 } }
    }
  }, opts);
  chartRefs[canvas] = new Chart(document.getElementById(canvas), { type: "line", data: { labels, datasets }, options: merged });
}
function barChart(canvas, labels, datasets, opts){
  if(chartRefs[canvas]) chartRefs[canvas].destroy();
  datasets = datasets.map(d => Object.assign({maxBarThickness:18, borderWidth:0}, d));
  chartRefs[canvas] = new Chart(document.getElementById(canvas),{
    type:"bar",
    data:{labels,datasets},
    options:Object.assign({
      responsive:true,maintainAspectRatio:false,indexAxis:"y",
      plugins:{legend:{labels:{boxHeight:8,boxWidth:8}}},
      plugins:{title:{display:true,align:"start",color:COL.ink,font:{size:13,weight:"700"},padding:{bottom:8}},
               legend:{display:false}},
      scales:{x:{beginAtZero:true,border:{display:false},grid:{color:THEME.chart_grid,drawTicks:false,borderDash:[4,4]},ticks:{callback:v=>v+"%"},title:{display:false}},
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
  const fams = ["BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL"];
  lineChart("riceFamilies", WAVES.map(w=>WAVE_LBL[w]),
    fams.map((k,i)=>({label:RICE_FAM_LBL[k], data:NAT.rice[k], borderColor:SERIES_RICE[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.riceFamilies.title},
              subtitle:{display:true,text:TXT.charts.riceFamilies.subtitle}}});
  lineChart("riceGrower", WAVES.map(w=>WAVE_LBL[w]),
    [{label:RICE_FAM_LBL.RICE_GROWER, data:NAT.rice.RICE_GROWER, borderColor:COL.accent}],
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
      [{label:RICE_FAM_LBL[k]+" (2024)",data:rows.map(r=>r.v),backgroundColor:COL.accent,borderColor:COL.accent}],
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
  lineChart("aquaTS", WAVES.map(w=>WAVE_LBL[w]),
    ["ANY_POND","CARP_ANY","POLY_CARP_2PLUS","TILAPIA","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"].map((k,i)=>({
      label:AQUA_IND_LBL[k], data:NAT.aqua[k], borderColor:SERIES_AQUA[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:TXT.charts.aquaTS.title},
              subtitle:{display:true,text:TXT.charts.aquaTS.subtitle}}});

  lineChart("aquaPoly", WAVES.map(w=>WAVE_LBL[w]),
    [{label:AQUA_IND_LBL.POLY_CARP_2PLUS, data:NAT.aqua.POLY_CARP_2PLUS, borderColor:COL.accent},
     {label:AQUA_IND_LBL.MOLA,            data:NAT.aqua.MOLA,           borderColor:COL.grey2}],
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
      [{label:AQUA_IND_LBL[k]+" (2024)",data:rows.map(r=>r.v),backgroundColor:COL.accent,borderColor:COL.accent}],
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
  const vEntries = Object.entries(DNA.by_variety).sort((a,b)=>b[1]-a[1]);
  const tot = DNA.n_assigned;
  const boro = (DNA.by_variety["BD-28"]||0) + (DNA.by_variety["BD-29"]||0);
  document.getElementById("dnaBoroPct").innerText = (100*boro/tot).toFixed(1);

  barChart("dnaByVariety", vEntries.map(x=>x[0]),
    [{label:"Assigned samples",data:vEntries.map(x=>x[1]),backgroundColor:COL.accent,borderColor:COL.accent}],
    {plugins:{title:{display:true,text:TXT.charts.dnaByVariety.title},legend:{display:false}},
     scales:{x:{title:{display:true,text:"samples"}},
             y:{ticks:{autoSkip:false,font:{size:9.5}}}}});

  const stOrder = ["Assigned","Unassigned","Not run"];
  const st = stOrder.filter(k => DNA.by_status[k] != null);
  barChart("dnaByCluster", st,
    [{label:"Field samples",data:st.map(k=>DNA.by_status[k]),backgroundColor:COL.accent,borderColor:COL.accent}],
    {plugins:{title:{display:true,text:TXT.charts.dnaByCluster.title},legend:{display:false}},
     scales:{x:{title:{display:true,text:"samples"}}}});

  // Aqua practices 2024
  const aqNat24 = AQUA.by_wave["2024"].__NATIONAL__;
  barChart("spiaPractices",
    [AQUA_IND_LBL.SUPP_FEED,AQUA_IND_LBL.HORMONE,AQUA_IND_LBL.DISEASE_CTL],
    [{label:"2024 weighted HH %",data:[aqNat24.SUPP_FEED||0,aqNat24.HORMONE||0,aqNat24.DISEASE_CTL||0],
      backgroundColor:COL.accent,borderColor:COL.accent}],
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
    [{label:"HH ownership %",data:eq[0].map(x=>x[1]),backgroundColor:COL.accent,borderColor:COL.accent}],
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
  const vRows = Object.entries(DNA.by_variety).map(([v,n])=>({variety:v,n,share:100*n/DNA.n_assigned}))
                  .sort((a,b)=>b.n-a.n);
  vTbl.innerHTML = `
    <div class="fulltbl-toolbar">
      <span class="meta">${DNA.n_assigned} assigned samples · ${DNA.n_varieties} varieties</span>
      <button class="dl">Download CSV</button>
    </div>
    <div class="fulltbl-scroll"><table class="full"><thead><tr>
      <th>Variety</th><th>Samples</th><th>% of assigned</th>
    </tr></thead><tbody>${vRows.map(r=>`<tr><td>${r.variety}</td><td>${r.n}</td><td>${r.share.toFixed(2)}</td></tr>`).join("")}</tbody></table></div>`;
  vTbl.querySelector("button.dl").onclick = ()=>csvDownload("mixtape_dna_by_variety.csv", vRows, ["variety","n","share"], ["Variety","Samples","% of sample"]);

  const cTbl = document.getElementById("spiaDnaCluster");
  const sRows = Object.entries(DNA.by_status).map(([status,n])=>
      ({status, n, share:100*n/DNA.n_field_rows})).sort((a,b)=>b.n-a.n);
  cTbl.innerHTML = `
    <div class="fulltbl-toolbar">
      <span class="meta">${DNA.n_field_rows} field samples</span>
      <button class="dl">Download CSV</button>
    </div>
    <div class="fulltbl-scroll"><table class="full"><thead><tr>
      <th>Assignment status</th><th>Samples</th><th>% of field samples</th>
    </tr></thead><tbody>${sRows.map(r=>`<tr><td>${r.status}</td><td>${r.n}</td><td>${r.share.toFixed(2)}</td></tr>`).join("")}</tbody></table></div>`;
  cTbl.querySelector("button.dl").onclick = ()=>csvDownload("mixtape_dna_assignment_status.csv", sRows,
    ["status","n","share"], ["Assignment status","Samples","% of field samples"]);
};

/* ==============================  TAB 5 INIT (MECH)  ============================== */
INITS["t-mech"] = function(){
  const m24 = MECH.by_wave["2024"].__NATIONAL__ || {};
  const m19 = MECH.by_wave["2019"].__NATIONAL__ || {};
  // Ownership comparison 2019 vs 2024
  const keys = ["TRACTOR","POWER_TILLER","POWER_THRESHER","LLP_IRRIG","AXIAL_FLOW_PUMP",
                "ELEC_MOTOR_PUMP","DIESEL_MOTOR_PUMP","SPRAYER","REAPER","SEEDER_DRILL","COMBINED_HARVEST"];
  const lbls = keys.map(k=>MECH_IND_LBL[k]);
  barChart("mechOwn", lbls,
    [{label:"2018/19",data:keys.map(k=>m19[k]||0),backgroundColor:COL.grey2,borderColor:COL.grey2},
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
        ("--accent", t["accent"]), ("--accent-dark", t["accent_dark"]),
        ("--ink", t["ink"]), ("--text", t["text"]), ("--mute", t["mute"]),
        ("--line", t["line"]), ("--line2", t["line2"]), ("--bg", t["background"]),
        ("--tint", t["tint"]),
        ("--positive", t["positive"]), ("--negative", t["negative"]),
    ]
    return "\n".join(f"    {k}:{v};" for k, v in pairs)

def _nav_tabs():
    out = []
    for i, t in enumerate(C["tabs"]):
        on = ' class="on"' if i == 0 else ""
        out.append(f'    <button data-tab="{t["id"]}"{on}>{t["label"]}</button>')
    return "\n".join(out)

# ---------------------------------------------------------------------
# Indicator tables. Every number is read from data/ at build time, so the
# published figures cannot drift away from the underlying JSON.
# ---------------------------------------------------------------------
WAVES = ["2011", "2015", "2019", "2024"]
WAVE_LABELS = ["2011/12", "2015", "2018/19", "2024"]
SOURCES = {"rice": RICE, "aqua": AQUA, "mech": MECH}

def _series(source, key):
    src = SOURCES[source]
    out = []
    for w in WAVES:
        v = src["by_wave"].get(w, {}).get("__NATIONAL__", {}).get(key)
        out.append(v if isinstance(v, (int, float)) else None)
    return out

def _series_table(rows_def, caption):
    head = "".join(f"<th>{lbl}</th>" for lbl in WAVE_LABELS)
    body = []
    for label, source, key in rows_def:
        vals = _series(source, key)
        cells = "".join(
            f'<td class="num">{v:.1f}</td>' if v is not None else '<td class="dim">&ndash;</td>'
            for v in vals)
        real = [v for v in vals if v is not None]
        if len(real) >= 2 and real[0] != real[-1]:
            d = real[-1] - real[0]
            chg = f'{"+" if d >= 0 else "−"}{abs(d):.1f}'
        else:
            chg = "&ndash;"
        body.append(f'<tr><td>{label}</td>{cells}<td class="chg">{chg}</td></tr>')
    return (f'<table class="data"><caption>{caption}</caption>'
            f'<thead><tr><th>Indicator</th>{head}<th>Change</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')

def _summary_table():
    S = C["summary"]
    return _series_table(S["rows"], S["caption"])

def _keyfig(tab):
    return _series_table(C["keyfig"][tab]["rows"], C["keyfig"]["caption"])

def _spia_counts():
    """Counts describing the 2024 round, read straight from the data files."""
    K = C["kpi"]["spia"]
    rows = [
        (K["samples"],    f'{DNA["n_field_rows"]:,}'),
        (K["clusters"],   f'{DNA["n_assigned"]:,}'),
        (K["varieties"],  f'{DNA["n_varieties"]:,}'),
        (K["households"], f'{SUM["rounds"]["2024"]["n_hh"]:,}'),
    ]
    body = "".join(f'<tr><td>{k}</td><td class="num">{v}</td></tr>' for k, v in rows)
    return (f'<table class="data" style="max-width:26em">'
            f'<tbody>{body}</tbody></table>')

def _rail_rows(rows):
    return "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows)

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
    "__PAGE_TITLE__": P["title"], "__PAGE_H1__": P["heading"],
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
    "__SUMMARY_TABLE__": _summary_table(), "__SUMMARY_NOTE__": C["summary"]["note"],
    "__RICE_KEYFIG__": _keyfig("rice"), "__AQUA_KEYFIG__": _keyfig("aqua"),
    "__MECH_KEYFIG__": _keyfig("mech"), "__SPIA_KEYFIG__": _spia_counts(),
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
