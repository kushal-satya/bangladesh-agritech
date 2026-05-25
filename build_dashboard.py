"""Build the MIXTAPE dashboard HTML by inlining all mixtape_*.json outputs.

Produces output/mixtape_dashboard.html which is fully self-contained (except for
the MIXTAPE-logo-800x800.png which must sit next to it) and deploys on GitHub
Pages as-is.
"""
import json, os, html, base64

OUT = r"C:/Users/kd475/RES/BGD_MIX/output"

def load(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as fh:
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
with open(os.path.join(OUT, "MIXTAPE-logo-800x800.png"), "rb") as fh:
    LOGO_B64 = "data:image/png;base64," + base64.b64encode(fh.read()).decode()

def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

PROJECT_BRIEF = """MIXTAPE tracks how publicly-bred rice varieties, aquaculture practices, and farm machinery have spread across Bangladesh's farming households between 2011 and 2024, using four rounds of the nationally-representative BIHS panel. Each map and chart shows the share of farmers using a particular technology — by district and over time. Cornell University and Bangladesh Agricultural University run the study; CGIAR's Standing Panel on Impact Assessment (SPIA) funds it through 2027."""

HTML_TMPL = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>MIXTAPE: Bangladesh CGIAR rice and aquaculture technologies</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="icon" type="image/png" href="__LOGO__"/>
<style>
  :root{
    /* Editorial minimal. Neutral surfaces. Two category accents: rice green, aquaculture blue. */
    --ink:#1a1f1c;
    --text:#2b332e;
    --mute:#6c7570;
    --line:#e3e6e1;
    --line2:#cfd4cd;
    --bg:#fafaf7;
    --panel:#ffffff;
    --tint:#f3f5f0;
    --rice:#2d6a4f;
    --rice-dark:#1c4a36;
    --rice-soft:#e5ede7;
    --aqua:#1f5e8a;
    --aqua-dark:#163f5d;
    --aqua-soft:#dfe9f1;
    --mech:#7a6147;
    --mech-dark:#52402b;
    --mech-soft:#ece4d6;
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
      padding:30px 22px 24px;border-right:1px solid var(--line);background:#fbfbf8}
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
        background:linear-gradient(to right,transparent,#fbfbf8)}
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
  .kpi .box .chip.up{color:#2f6b3a}
  .kpi .box .chip.dn{color:#9c3a2a}
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
  .leaflet-container{background:#fafaf7;font-family:inherit}
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
      font-weight:600;margin-bottom:8px;color:var(--mute)}
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
  .finding .delta.up{color:#2f6b3a}
  .finding .delta.dn{color:#9c3a2a}
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
      <div class="acro">MIXTAPE</div>
      <div class="full">Bangladesh country study</div>
    </div>
  </div>
  <nav class="tabs" id="tabs">
    <button data-tab="t-map" class="on"><span class="num">01</span><span>Map overview</span></button>
    <button data-tab="t-rice"><span class="num">02</span><span>Rice</span></button>
    <button data-tab="t-aqua"><span class="num">03</span><span>Aquaculture</span></button>
    <button data-tab="t-spia"><span class="num">04</span><span>2024 SPIA round</span></button>
    <button data-tab="t-mech"><span class="num">05</span><span>Mechanisation</span></button>
    <button data-tab="t-tech"><span class="num">06</span><span>Technology index</span></button>
  </nav>
  <div class="rail-meta">
    <div class="lbl">BIHS panel (all rural HH surveyed)</div>
    <div class="row"><span>2011/12</span><span>6,503</span></div>
    <div class="row"><span>2015</span><span>6,715</span></div>
    <div class="row"><span>2018/19</span><span>6,011</span></div>
    <div class="row"><span>2024 SPIA</span><span>5,554</span></div>
    <div class="lbl" style="margin-top:12px">Agricultural HH (analysis frame)</div>
    <div class="row"><span>2011/12</span><span>3,755</span></div>
    <div class="row"><span>2015</span><span>3,723</span></div>
    <div class="row"><span>2018/19</span><span>3,220</span></div>
    <div class="row"><span>2024 SPIA</span><span>2,924</span></div>
    <div class="row" style="margin-top:6px;border-top:1px dashed var(--line);padding-top:6px;font-size:10.5px;line-height:1.45">
      <span style="color:var(--mute);font-weight:500">All percentages on this dashboard are weighted shares of the agricultural sub-frame — farmers who cultivated land or operated a pond. The full BIHS panel covers all rural HH.</span>
    </div>
  </div>
  <div class="rail-foot">
    Kushal Kumar<br><a href="mailto:kd475@cornell.edu">kd475@cornell.edu</a><br>
    Cornell University<br>
    <br>
    Replicates <a href="https://github.com/CGIAR-SPIA/SPIA-Bangladesh-Study-2025" target="_blank" rel="noopener">SPIA Bangladesh Study 2025</a>
  </div>
</aside>

<main class="wrap">

<header class="title">
  <div class="eyebrow">CGIAR Standing Panel on Impact Assessment, country study</div>
  <h1>Monitoring Impacts for Technology Adoption and Program Engagement in Bangladesh</h1>
  <div class="meta">
    <span>Household level evidence on CGIAR linked rice and aquaculture innovations</span>
    <span>Four BIHS rounds: <b>2011/12, 2015, 2018/19, 2024</b></span>
  </div>
</header>

<div class="brief"><b>About.</b> __BRIEF__</div>

<!-- ============================== TAB 1 :: MAP ============================== -->
<section id="t-map" class="tab on">
  <h2 class="section">What's changed in the four-round BIHS panel, 2011/12 to 2024</h2>
  <p class="lede">Three big shifts in CGIAR-linked technology adoption: which Boro rice lines farmers plant, how many of them keep fish ponds, and how mechanised paddy production has become. Numbers are weighted shares of <b>agricultural households</b> in each round (n = 2,924 in 2024); the underlying BIHS panel surveys <b>all rural households</b> (n = 5,554 in 2024) regardless of whether they farm. Click any card to open its full tab.</p>

  <div class="findings">
    <a class="finding f-rice" data-jump="t-rice" tabindex="0">
      <span class="arrow">Rice ›</span>
      <div class="eyebrow">Rice · BR-28 / BR-29 (Boro mega-varieties)</div>
      <div class="big">27.8<span class="unit">%</span></div>
      <div class="ctx">of farmers planted BR-28 or BR-29 in 2024. Hybrid rice climbed from <b>0.5%</b> (2011/12) to <b>19.5%</b>, and post-2012 BRRI lines (BR-70+) reached <b>10.6%</b> from near zero. Traditional landraces fell from <b>57.9%</b> to <b>17.5%</b>.</div>
      <div class="delta dn">▼ 20.4 pp vs 2011/12 (48.2%)</div>
    </a>
    <a class="finding f-aqua" data-jump="t-aqua" tabindex="0">
      <span class="arrow">Aquaculture ›</span>
      <div class="eyebrow">Aquaculture · Any cultivated pond</div>
      <div class="big">23.5<span class="unit">%</span></div>
      <div class="ctx">of farmers operate at least one cultivated pond in 2024. Tilapia (incl. GIFT) holds at <b>13.4%</b>; carp polyculture eases from <b>22.6%</b> to <b>13.7%</b>; small-fish (mola) co-culture roughly tripled from <b>0.5%</b> to <b>1.3%</b>.</div>
      <div class="delta dn">▼ 6.4 pp vs 2011/12 (29.9%)</div>
    </a>
    <a class="finding f-mech" data-jump="t-mech" tabindex="0">
      <span class="arrow">Mechanisation ›</span>
      <div class="eyebrow">Mechanisation · Motorised threshing (2024)</div>
      <div class="big">65.4<span class="unit">%</span></div>
      <div class="ctx">of paddy growers thresh with a motor in 2024. Sprayer use jumped from <b>0.9%</b> (2019) to <b>29.2%</b>, and electric motor-pump irrigation rose from <b>9.2%</b> to <b>14.1%</b>. Power-tiller use is still <b>~82%</b> in the 2024 module.</div>
      <div class="delta">First measured in the 2024 SPIA round</div>
    </a>
  </div>

  <details class="method">
    <summary>How to read these numbers — denominators, weights, sources</summary>
    <div class="body">
      The BIHS panel <b>surveys all rural households</b> in the Feed-the-Future zone, regardless of whether they farm; analysis here follows the SPIA Bangladesh Study 2025 and restricts to the <b>agricultural sub-frame</b> (households that cultivated land or operated a pond in the recall period). Roughly half of the panel sits in that sub-frame each round. Both denominators are shown so users can pick the one that matches their question.
      <div class="denom-grid">
        <div class="cell"><div class="yr">2011/12</div><div class="all">6,503 panel HH</div><div class="agri">3,755 agri-HH</div></div>
        <div class="cell"><div class="yr">2015</div><div class="all">6,715 panel HH</div><div class="agri">3,723 agri-HH</div></div>
        <div class="cell"><div class="yr">2018/19</div><div class="all">6,011 panel HH</div><div class="agri">3,220 agri-HH</div></div>
        <div class="cell"><div class="yr">2024 SPIA</div><div class="all">5,554 panel HH</div><div class="agri">2,924 agri-HH</div></div>
      </div>
      <small class="cap">Weights: BIHS_FTF baseline 2011/12, BIHS FTF 2015 sampling weights, 158_BIHS r3 weights, SPIA 2024 hhweight_24. Source: <a href="https://github.com/CGIAR-SPIA/SPIA-Bangladesh-Study-2025" target="_blank" rel="noopener">SPIA Bangladesh Study 2025 replication code</a>; full project context in tab 04 (2024 SPIA round) and tab 06 (Technology index).</small>
    </div>
  </details>

  <h3 class="sub">District map: pick a category, an indicator, and a round</h3>
  <p class="lede">Each of Bangladesh's 64 districts is shaded by the share of agricultural households using the selected indicator. <b>Darker means a higher share.</b> Hover any district for its weighted rate; the four headline boxes, the top-5 / bottom-5 list to the right of the map, and the national trend lines at the bottom all update with the indicator you pick.</p>

  <div class="controls">
    <div class="cat-pills" id="mapCatPills">
      <button class="pill on" data-cat="rice">Rice variety</button>
      <button class="pill" data-cat="aqua">Aquaculture</button>
      <button class="pill" data-cat="mech">Machinery / pumps</button>
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
      <div class="info" id="mapInfo"><h5>Bangladesh, weighted mean</h5><div class="val">–</div><small class="cap">Hover any district for its share</small></div>
      <div class="mini-legend" id="mapLegend"></div>
    </div>
    <div class="map-side">
      <div class="blk"><div class="lbl">Highest adoption (top 5 districts)</div><ol id="mapTopList"></ol></div>
      <div class="blk"><div class="lbl">Lowest adoption (bottom 5 districts)</div><ol id="mapBotList"></ol></div>
    </div>
  </div>

  <h3 class="sub">How the national rate has moved, 2011 to 2024</h3>
  <p class="lede">Each line is the weighted national share of agricultural households for one variety family or aquaculture practice across the four BIHS rounds.</p>
  <div class="row row-2">
    <div class="chart-wrap"><canvas id="natRice"></canvas></div>
    <div class="chart-wrap"><canvas id="natAqua"></canvas></div>
  </div>

  <p class="note">Denominator = agricultural households (cultivated land or operated a pond in the recall period), weighted with each round's BIHS sampling weights. Analytic-frame sizes: 3,755 / 3,723 / 3,220 / 2,924 households across the four rounds; the underlying BIHS panel ran 5,503 to 6,715 households per round. Frame definitions follow the SPIA Bangladesh Study 2025 (full citation on the 2024 SPIA round tab). Mechanisation indicators for 2011 and 2015 are limited to a single harmonised tractor flag; richer equipment rosters only exist for 2018/19 (Module D2) and 2024 (a5_6, d2).</p>
</section>

<!-- ============================== TAB 2 :: RICE ============================== -->
<section id="t-rice" class="tab">
  <h2 class="section">Rice variety adoption, 2011 to 2024</h2>
  <p class="lede">Rice varieties are coded round-by-round from module H1 (2011, 2015, 2019) and from 2024's paddy modules
  c2_4 (main paddy) and b6 (seedbed). Each household's set of grown varieties is classified into one of seven CGIAR-relevant
  families; we then compute the weighted share of households growing a family.</p>

  <div class="kpi" id="kpiRice"></div>

  <div class="row row-2">
    <div class="chart-wrap"><canvas id="riceFamilies"></canvas></div>
    <div class="chart-wrap"><canvas id="riceGrower"></canvas></div>
  </div>

  <h3 class="sub">District-level prevalence, by variety family (2024)</h3>
  <div class="controls">
    <label>Family</label>
    <select id="riceDistFam"></select>
  </div>
  <div class="chart-wrap tall"><canvas id="riceDistChart"></canvas></div>

  <h3 class="sub">Top districts: BRRI core (BR-28 / BR-29) and new BRRI lines (BR-70+), 2024</h3>
  <div id="riceTopTables" class="row row-2"></div>

  <h3 class="sub">Full district level table: every variety family, all 64 districts, all rounds</h3>
  <p class="lede">Pick a round below. Every cell is a weighted share (%) of households in that district who grew a variety
  in the family; <span class="src">n (households)</span> is the unweighted sample size; <span class="src">Σ weight</span> is
  the sum of household sampling weights (the denominator used to compute each percentage). Use the search box to filter,
  click any header to sort, and the CSV button to export the full table for that round.</p>
  <div class="fulltbl-wrap" id="riceFullTbl"></div>

  <p class="note">Source: BIHS 011_mod_h1_male.dta, 015_r2_mod_h1_male.dta, 021_bihs_r3_male_mod_h1.dta,
  SPIA_BIHS_2024_module_c2_4.dta + module_b6.dta. Weights: BIHS_FTF baseline sampling weights, BIHS FTF 2015 survey sampling weights,
  158_BIHS sampling weights_r3.dta, SPIA 2024 hhweight_24.</p>
</section>

<!-- ============================== TAB 3 :: AQUA ============================== -->
<section id="t-aqua" class="tab">
  <h2 class="section">Aquaculture adoption, 2011 to 2024</h2>
  <p class="lede">Pond-level rosters (module L1 in earlier rounds; e5/e10 in 2024) are filtered to ponds with positive
  cultivated area. For every household with at least one cultivated pond we record the fish species present, then
  compute weighted prevalence across the full HH sample.</p>

  <div class="kpi" id="kpiAqua"></div>

  <div class="row row-2">
    <div class="chart-wrap"><canvas id="aquaTS"></canvas></div>
    <div class="chart-wrap"><canvas id="aquaPoly"></canvas></div>
  </div>

  <h3 class="sub">District-level pond prevalence (2024)</h3>
  <div class="controls">
    <label>Indicator</label>
    <select id="aquaDistInd"></select>
  </div>
  <div class="chart-wrap tall"><canvas id="aquaDistChart"></canvas></div>

  <h3 class="sub">Top pond-intensive and tilapia-intensive districts, 2024</h3>
  <div id="aquaTopTables" class="row row-2"></div>

  <h3 class="sub">Full district level table: every aquaculture indicator, all 64 districts, all rounds</h3>
  <p class="lede">Weighted share (%) of households in each district showing the indicator (filtered to ponds with positive
  cultivated area). The 2024 round additionally records intensification practices (supplementary feed, hormone, disease
  control). Sort on any column, filter by district, or export a CSV for the round on display.</p>
  <div class="fulltbl-wrap" id="aquaFullTbl"></div>

  <p class="note">Source: BIHS 026_mod_l1_male.dta, 037_r2_mod_l1_male.dta, 051_bihs_r3_male_mod_l1.dta,
  SPIA_BIHS_2024_module_e5.dta + module_e10.dta. Species codes from value labels in-file.</p>
</section>

<!-- ============================== TAB 4 :: 2024 SPIA ============================== -->
<section id="t-spia" class="tab">
  <h2 class="section">2024 SPIA round: new insights</h2>

  <div class="ref-card">
    <div class="ref-eyebrow">Source for this tab</div>
    <div class="ref-title">SPIA Bangladesh Study 2025: Updating the Green Revolution</div>
    <div class="ref-meta">Singla, S., Ul Islam, T., Hassan, F., Monteiro, I., Stevenson, J., Emerick, K. (2025). Standing Panel on Impact Assessment (SPIA), Rome. CC BY-NC-SA 4.0.</div>
    <div class="ref-links">
      <a href="https://iaes.cgiar.org/sites/default/files/pdf/SPIA_Bangladesh_Study_2025.pdf" target="_blank" rel="noopener">Read the SPIA 2025 report (PDF)</a>
      <a href="https://github.com/CGIAR-SPIA/SPIA-Bangladesh-Study-2025" target="_blank" rel="noopener">SPIA replication repository on GitHub</a>
    </div>
    <div class="ref-note">The 2024 SPIA round of BIHS, the DNA-fingerprint sample, the equipment roster and the aquaculture-intensification module on this tab are taken from SPIA's published 2025 study. This dashboard presents and verifies a subset of that evidence in a navigable form.</div>
  </div>

  <p class="lede">The 2024 SPIA round adds three pieces of evidence on top of the traditional recall-based BIHS instrument:
  (i) DNA fingerprinting of a random sample of 370 paddy plots, allowing direct rather than self-reported variety identification;
  (ii) a detailed agricultural-equipment ownership roster;
  (iii) explicit aquaculture-intensification practices (supplementary feed, hormones, disease control).</p>

  <div class="kpi" id="kpiSpia"></div>

  <h3 class="sub">DNA-fingerprint varieties (370 paddy samples, 10 genetic clusters)</h3>
  <p class="lede">These are the verified varieties, <em>not</em> self-reported: each sample was genotyped and matched to a
  reference library (rice-hybrids excluded). BR-28 and BR-29 together account for <span id="dnaBoroPct"></span>% of the
  DNA-typed sample, confirming that the two IRRI-derived BRRI mega-varieties still dominate the Boro season 40+ years after release.</p>
  <div class="row row-2">
    <div class="chart-wrap"><canvas id="dnaByVariety"></canvas></div>
    <div class="chart-wrap"><canvas id="dnaByCluster"></canvas></div>
  </div>

  <h3 class="sub">Aquaculture-intensification practices (household-weighted, 2024)</h3>
  <p class="lede">Measured at the household level in the 2024 e10 module.</p>
  <div class="chart-wrap"><canvas id="spiaPractices"></canvas></div>

  <h3 class="sub">Equipment-ownership roster (Module a5_6)</h3>
  <div class="chart-wrap"><canvas id="spiaEquip"></canvas></div>

  <h3 class="sub">Full 2024 district level table: every rice, aquaculture and mechanisation indicator</h3>
  <p class="lede">All indicators measured in the 2024 SPIA round, pooled into a single wide table at the district level.
  Rows sort and filter, and the CSV download exports every column.</p>
  <div class="fulltbl-wrap" id="spiaFullTbl"></div>

  <div class="row row-2" style="margin-top:16px">
    <div>
      <h3 class="sub">DNA-fingerprint variety counts (n = 370 samples)</h3>
      <p class="lede">Raw count of samples matched to each reference variety, descending.</p>
      <div class="fulltbl-wrap" id="spiaDnaVariety"></div>
    </div>
    <div>
      <h3 class="sub">Genetic clusters (10 clusters)</h3>
      <p class="lede">Each sample was assigned to a cluster by its genotype. Here: sample counts per cluster, number of
      distinct varieties observed in the cluster, and the cluster's most frequent variety.</p>
      <div class="fulltbl-wrap" id="spiaDnaCluster"></div>
    </div>
  </div>

  <p class="note">Source: SPIA_BIHS_2024_module_a1.dta, a5_6.dta, c2_4.dta, b6.dta, e5.dta, e10.dta, d2.dta,
  and ref_clusters_no_hybrids_with_HH_Ids.csv (DNA fingerprints).</p>
</section>

<!-- ============================== TAB 5 :: MECH ============================== -->
<section id="t-mech" class="tab">
  <h2 class="section">Mechanisation and agricultural practices, 2018/19 and 2024</h2>
  <p class="lede">This panel compares household-level ownership of farm equipment between 2018/19 (BIHS R3 module D2) and
  2024 (SPIA module a5_6). The 2024 round additionally records the <em>actual use</em> of motorised harvest and
  thresh from the paddy operations module.</p>

  <div class="kpi" id="kpiMech"></div>

  <div class="row row-2">
    <div class="chart-wrap"><canvas id="mechOwn"></canvas></div>
    <div class="chart-wrap"><canvas id="mechUse"></canvas></div>
  </div>

  <h3 class="sub">District-level mechanisation (2024)</h3>
  <div class="controls">
    <label>Indicator</label>
    <select id="mechDistInd"></select>
  </div>
  <div class="chart-wrap tall"><canvas id="mechDistChart"></canvas></div>

  <h3 class="sub">Full district level table: every piece of equipment, all rounds with data</h3>
  <p class="lede">Weighted share (%) of households owning each piece of equipment (and, for 2024, actually
  <em>using</em> motorised harvest / thresh). The 2011 and 2015 rounds only carry a tractor flag in the harmonised
  file, so those columns are filled only where microdata exist.</p>
  <div class="fulltbl-wrap" id="mechFullTbl"></div>

  <p class="note">Sources: 016_bihs_r3_male_mod_d2.dta (R3 asset roster, codes 12=tractor, 13=power tiller, 15=thresher,
  22=LLP pump, 25=electric motor pump, 26=diesel pump, 27=sprayer, 28=reaper, 36=axial-flow pump, 37=seeder drill,
  39=combined harvester); SPIA_BIHS_2024_module_a5_6.dta (binary ownership indicators); SPIA_BIHS_2024_module_d2.dta
  (actual motorised use). 2011 and 2015 ownership draws on the limited set of durable-asset flags in
  BIHS_household_2011_15.dta (asset_tractor only).</p>
</section>

<!-- ============================== TAB 6 :: TECH INDEX ============================== -->
<section id="t-tech" class="tab">
  <h2 class="section">Technology index, CGIAR linked innovations in Bangladesh</h2>
  <p class="lede">Every variety, strain, practice, or piece of equipment tracked by the MIXTAPE dashboard, with a short description and links to authoritative sources. Curated from BRRI, BINA, BARI, IRRI, WorldFish, CIMMYT, ICARDA, ICRISAT, CIP, HarvestPlus, the CGIAR Standing Panel on Impact Assessment (SPIA), and peer reviewed literature. The canonical synthesis is the SPIA Bangladesh Study 2025: Updating the Green Revolution, with replication code on GitHub.</p>

  <div class="primary-ref" id="primaryRef"></div>

  <h3 class="sub">Institutions and programmes</h3>
  <div class="inst-grid" id="instGrid"></div>

  <h3 class="sub">Browse technologies</h3>
  <div class="controls tech-controls">
    <div class="cat-pills" id="techCatPills"></div>
    <input type="search" class="search tech-search" placeholder="Search variety, strain, or trait..." id="techSearch"/>
    <span class="tech-count" id="techCount"></span>
  </div>
  <div class="tech-grid" id="techGrid"></div>
</section>

<div class="footer">
<div class="contact">
  Kushal Kumar &middot; <a href="mailto:kd475@cornell.edu">kd475@cornell.edu</a> &middot; Cornell University
</div>
<div class="attrib">
  Underlying microdata: Bangladesh Integrated Household Survey (BIHS) rounds 1 (2011/12), 2 (2015), 3 (2018/19) via the
  <a href="https://dataverse.harvard.edu/dataverse/IFPRI" target="_blank" rel="noopener">IFPRI dataverse</a>;
  the 2024 round is from the SPIA Bangladesh Study 2025 (see the 2024 SPIA round tab and the Technology Index tab for the full citation).
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

const WAVES = ["2011","2015","2019","2024"];
const WAVE_LBL = {"2011":"2011/12","2015":"2015","2019":"2018/19","2024":"2024"};

const RICE_FAM_LBL = {
  BRRI_CORE28_29:   "BRRI core (BR-28 / BR-29)",
  BRRI_OLDER_HYV:   "BRRI older HYV (BR-1…BR-69)",
  BRRI_NEW_POST2012:"New BRRI lines (BR-70+)",
  BRRI_STRESS:      "Stress-tolerant (subm / Zn / saline / drought)",
  BINA:             "BINA lines (Binadhan)",
  HYBRID:           "Hybrid rice",
  LOCAL:            "Traditional / local landraces",
  RICE_GROWER:      "Any rice grower"
};
const AQUA_IND_LBL = {
  ANY_POND:        "Any cultivated pond",
  TILAPIA:         "Tilapia (incl. GIFT)",
  CARP_ANY:        "Any carp",
  POLY_CARP_2PLUS: "Carp polyculture (2+ species)",
  MOLA:            "Mola co-culture",
  PRAWN_GALDA:     "Prawn (galda)",
  SHRIMP_BAGDA:    "Shrimp (bagda)",
  SUPP_FEED:       "Supplementary fish feed",
  HORMONE:         "Hormone use (aquaculture)",
  DISEASE_CTL:     "Disease control (aquaculture)"
};
const MECH_IND_LBL = {
  TRACTOR:           "Tractor",
  POWER_TILLER:      "Power tiller",
  POWER_THRESHER:    "Power thresher",
  TREADLE_PUMP:      "Treadle pump",
  ROWER_PUMP:        "Rower pump",
  AXIAL_FLOW_PUMP:   "Axial-flow (Jumbo) pump",
  LLP_IRRIG:         "Low-lift irrigation pump",
  DIESEL_MOTOR_PUMP: "Diesel motor pump",
  ELEC_MOTOR_PUMP:   "Electric motor pump",
  SPRAYER:           "Sprayer (motorised)",
  REAPER:            "Reaper",
  SEEDER_DRILL:      "Seeder / drill",
  COMBINED_HARVEST:  "Combined harvester",
  TRANSPLANTER:      "Rice transplanter",
  FISHING_NET:       "Fishing net",
  PADDLE_THRESHER:   "Paddle thresher",
  USE_MOTOR_HARVEST: "Motorised harvest (actual use)",
  USE_MOTOR_THRESH:  "Motorised thresh (actual use)",
  USE_TREADLE_THRESH:"Treadle thresh (actual use)"
};

/* ==============================  COLORS  ============================== */
/* Semantic palette. Rice tab uses leaf greens, aqua uses blues, mech uses earth tones. */
const COL = {slate:"#1a1f1c", slate2:"#4a5550",
             leaf:"#2d6a4f", leaf2:"#6c9971",
             teal:"#1f5e8a", teal2:"#6996ad",
             accent:"#7a6147", accent2:"#bdaa7f",
             cream:"#f3f5f0", ink:"#1a1f1c", mute:"#6c7570"};
/* Monochrome series palettes per tab. Dark to light shades within one hue family
   keep multi-line charts coherent (no rainbow). */
const SERIES_RICE = ["#1c4a36","#2d6a4f","#467a52","#6c9971","#94b696","#b9cbb0","#dde6dd","#0f3624","#5d8a4d","#3f5e2c"];
const SERIES_AQUA = ["#0e3a5c","#163f5d","#1f5e8a","#3f7896","#6996ad","#94b3c4","#bccfd9","#5198c7","#1c4a36","#52402b"];
const SERIES_MECH = ["#332617","#52402b","#7a6147","#9c885c","#bdaa7f","#d6c8a8","#ece4d6","#a3866c","#5e5340","#8a7253"];
const SERIES_COL = SERIES_RICE; /* default (kept for any code that still references it) */

Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
Chart.defaults.font.size   = 11.5;
Chart.defaults.color       = COL.slate2;
Chart.defaults.borderColor = "#e3e6e1";
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
  if(v==null || isNaN(v)) return "#ebede8";
  for(const [t,c] of stops) if(v<=t) return c;
  return stops[stops.length-1][1];
}
/* Three sequential ramps. Rice green, aquaculture blue, mechanisation warm earth.
   Lightest step always contrasts with the page bg (#fafaf7). */
const MAP_RAMPS = {
  rice:{stops:[[0,"#dde6dd"],[2,"#bcd0bd"],[5,"#94b696"],[10,"#6c9971"],[20,"#467a52"],[35,"#285e3d"],[100,"#143f27"]]},
  aqua:{stops:[[0,"#dee6ec"],[2,"#bccfd9"],[5,"#94b3c4"],[10,"#6996ad"],[20,"#3f7896"],[35,"#1f5e8a"],[100,"#0e3a5c"]]},
  mech:{stops:[[0,"#ece4d6"],[2,"#d6c8a8"],[5,"#bdaa7f"],[10,"#9c885c"],[20,"#7a6147"],[35,"#54402b"],[100,"#332617"]]}
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
const MAP_CATALOG = {
  rice: {
    label: "Rice variety adoption",
    items: [
      ["BRRI core: BR-28 / BR-29 (Boro mega-varieties)", "BRRI_CORE28_29"],
      ["New BRRI lines: BR-70 and above (post-2012)",    "BRRI_NEW_POST2012"],
      ["Stress tolerant: submergence, Zn, saline, drought", "BRRI_STRESS"],
      ["Older BRRI HYV: BR-1 through BR-69",            "BRRI_OLDER_HYV"],
      ["Hybrid rice",                                     "HYBRID"],
      ["BINA lines (Binadhan)",                           "BINA"],
      ["Traditional / local landrace",                    "LOCAL"],
      ["Any rice grower",                                 "RICE_GROWER"]
    ]
  },
  aqua: {
    label: "Aquaculture",
    items: [
      ["Any cultivated pond",                "ANY_POND"],
      ["Tilapia (incl. GIFT)",               "TILAPIA"],
      ["Carp polyculture (2+ species)",      "POLY_CARP_2PLUS"],
      ["Any carp",                           "CARP_ANY"],
      ["Mola co-culture (small indigenous)", "MOLA"],
      ["Prawn (galda)",                      "PRAWN_GALDA"],
      ["Shrimp (bagda)",                     "SHRIMP_BAGDA"]
    ]
  },
  mech: {
    label: "Mechanisation",
    items: [
      ["Power tiller",            "POWER_TILLER"],
      ["Tractor",                 "TRACTOR"],
      ["Power thresher",          "POWER_THRESHER"],
      ["Sprayer (motorised)",     "SPRAYER"],
      ["Reaper",                  "REAPER"],
      ["Combined harvester",      "COMBINED_HARVEST"],
      ["Seeder / drill",          "SEEDER_DRILL"],
      ["LLP irrigation pump",     "LLP_IRRIG"],
      ["Axial-flow (Jumbo) pump", "AXIAL_FLOW_PUMP"],
      ["Electric motor pump",     "ELEC_MOTOR_PUMP"],
      ["Diesel motor pump",       "DIESEL_MOTOR_PUMP"]
    ]
  }
};
const DEFAULT_MAP_IND = {rice:"BRRI_CORE28_29", aqua:"ANY_POND", mech:"POWER_TILLER"};

/* Plain-English gloss per indicator. Keep each <100 words; the first sentence is the "what",
   the second is the "why a fresh viewer should care". The map's gloss strip shows exactly this. */
const IND_GLOSS = {
  BRRI_CORE28_29:    "<b>BR-28 and BR-29</b> are the two IRRI-derived Boro-season rice varieties released by BRRI in the 1990s. They are still the workhorse of Bangladesh's dry-season rice — what farmers grow when irrigation is available.",
  BRRI_NEW_POST2012: "<b>BR-70 and above</b> are the post-2012 BRRI lines (e.g. BR-89 and BR-92, high-yielding aromatic Boro). They show how fast newer public varieties are replacing BR-28/29.",
  BRRI_STRESS:       "<b>Stress-tolerant BRRI varieties</b> are bred to survive flooding (BR-47 / BR-51), drought (BR-66), salinity (BR-67), or to add zinc to the grain (BR-62 / BR-64). They matter in coastal and flood-prone districts.",
  BRRI_OLDER_HYV:    "<b>Older BRRI HYVs (BR-1 to BR-69)</b> are pre-2000 public varieties, many still widely grown in Aman/Aus. A rising share for this family suggests older lines are persisting; a falling share suggests they are being displaced.",
  HYBRID:            "<b>Hybrid rice</b> is F1 seed, mostly imported or produced by private firms. Farmers must buy fresh seed every season, so adoption tracks input markets, not just agronomy.",
  BINA:              "<b>BINA varieties (Binadhan)</b> come from the Bangladesh Institute of Nuclear Agriculture. Best known for flood-tolerant Binadhan-11 in haor and flash-flood districts.",
  LOCAL:             "<b>Local landraces</b> are traditional, often single-season varieties grown from saved seed. They flag where modern varieties have not yet displaced informal seed systems.",
  RICE_GROWER:       "<b>Any rice grower</b> — the share of agricultural households who grew any rice at all in the round. A baseline to compare every other variety family against.",
  ANY_POND:          "<b>Any cultivated fish pond</b> — the entry point for every aquaculture indicator. Without a cultivated pond, none of the species-level shares can be non-zero.",
  TILAPIA:           "<b>Tilapia (including GIFT)</b>. GIFT — Genetically Improved Farmed Tilapia — is WorldFish/CGIAR's flagship aquaculture innovation; it dominates Bangladesh's commercial fish ponds.",
  POLY_CARP_2PLUS:   "<b>Carp polyculture (2+ species)</b> is the CGIAR-promoted intensification path: stocking multiple carp species in the same pond raises pond productivity over single-species culture.",
  CARP_ANY:          "<b>Any carp</b> — at least one carp species in a cultivated pond, regardless of stocking pattern.",
  MOLA:              "<b>Mola co-culture</b>: small indigenous fish co-stocked with carp for household nutrition (mola is exceptionally rich in vitamin A, iron and zinc). A WorldFish nutrition-sensitive innovation.",
  PRAWN_GALDA:       "<b>Galda — freshwater prawn</b>. A high-value export species, concentrated in the southwest.",
  SHRIMP_BAGDA:      "<b>Bagda — brackish-water shrimp</b>. Concentrated in the coastal southwest belt where saline water permits cultivation.",
  POWER_TILLER:      "<b>Power tiller</b> — a two-wheel tractor. The dominant machine for land preparation on Bangladesh's small farms.",
  TRACTOR:           "<b>Four-wheel tractor</b>. Far less common than the power tiller on smallholder farms.",
  POWER_THRESHER:    "<b>Power thresher</b> — motor-driven post-harvest threshing. A separating step before machines like the combined harvester were widely available.",
  SPRAYER:           "<b>Motorised sprayer</b>. The fastest-growing piece of farm machinery in the 2024 round; used for pesticides, herbicides and fertilizer foliar sprays.",
  REAPER:            "<b>Reaper</b> — a motorised crop-cutting machine. Adoption is still concentrated in a few districts.",
  COMBINED_HARVEST:  "<b>Combined harvester</b> — cuts, threshes and cleans grain in one pass. Still rare; expensive and built for larger plots than most Bangladeshi farms.",
  SEEDER_DRILL:      "<b>Seeder / drill</b> — a row-planting attachment for power tillers, used to reduce labour at sowing.",
  LLP_IRRIG:         "<b>LLP (Low-Lift Pump)</b> — surface-water lift for irrigation, especially during Aman and Boro. The traditional irrigation backbone.",
  AXIAL_FLOW_PUMP:   "<b>Axial-flow ('Jumbo') pump</b> — high-volume, low-head pump for flood-prone surface irrigation.",
  ELEC_MOTOR_PUMP:   "<b>Electric motor pump</b>. Adoption tracks rural electrification — growing fast in Boro rice belts.",
  DIESEL_MOTOR_PUMP: "<b>Diesel motor pump</b> — an older but still widespread irrigation source where the grid hasn't reached.",
  USE_MOTOR_HARVEST: "<b>Motorised harvest, used in 2024</b> — share of households who actually used a motorised harvester this round, not just owned one.",
  USE_MOTOR_THRESH:  "<b>Motorised threshing, used in 2024</b> — share of households who actually used a power thresher this round. The single most common piece of mechanised agriculture in Bangladesh."
};

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
  box.innerHTML = `<h5>Bangladesh, weighted mean</h5>
    <div class="val">${valTxt}</div>
    <small class="cap">${lbl} &middot; ${WAVE_LBL[year]} &middot; n=${natN??"–"} agri-HH</small>
    <small class="cap" style="display:block;margin-top:4px;color:var(--mute);font-size:10.5px">Hover any district for its share</small>`;
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
            <small class="cap">${WAVE_LBL[year]} &middot; n=${n??"–"} agri-HH</small>`;
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
  let html = `<b>${MAP_CATALOG[mapCat].label}</b><br>${title}<br><small class="cap">% of households &middot; ${WAVE_LBL[year]}</small>`;
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
      `<em>Map shows: weighted share of agricultural households in each district where this indicator is true, ${WAVE_LBL[year]}. Darker = higher share.</em>`;
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
      {lbl:`National share, ${WAVE_LBL[year]}`, val:fmtPct(natNow)},
      {lbl:`Change at the national level`,       val:deltaTxt},
      {lbl:`Highest district`,                   val: top ? distFmt(top) : "n/a"},
      {lbl:`Lowest district`,                    val: bot ? distFmt(bot) : "n/a"}
    ].map(o => `<div class="box"><div class="lbl">${o.lbl}</div><div class="big">${o.val}</div></div>`).join("");
  }

  /* --- Top 5 and bottom 5 district lists beside the map --- */
  const topEl = document.getElementById("mapTopList");
  const botEl = document.getElementById("mapBotList");
  if(topEl && botEl){
    if(rows.length === 0){
      topEl.innerHTML = '<li class="empty">No district data this round</li>';
      botEl.innerHTML = '<li class="empty">No district data this round</li>';
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
      <input type="search" class="search" placeholder="Filter districts…"/>
      <button class="dl">Download CSV</button>
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
      y: { beginAtZero: true, grid: { color: "#eef0eb", drawTicks: false }, ticks: { callback: v => v + "%" }, title: { display: false } },
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
      scales:{x:{beginAtZero:true,grid:{color:"#eef0eb",drawTicks:false},ticks:{callback:v=>v+"%"},title:{display:false}},
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
     plugins:{title:{display:true,text:"BRRI core mega-varieties still dominate, hybrid rice surges from a near-zero base"},
              subtitle:{display:true,text:"Share of agricultural households growing each variety family"}}});
  const aquaKeys = ["ANY_POND","POLY_CARP_2PLUS","TILAPIA","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"];
  lineChart("natAqua", WAVES.map(w=>WAVE_LBL[w]),
    aquaKeys.map((k,i)=>({label:AQUA_IND_LBL[k], data:NAT.aqua[k], borderColor:SERIES_AQUA[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:"Pond aquaculture contracts: from ~30% to ~23% of agricultural HH"},
              subtitle:{display:true,text:"Share of agricultural households cultivating fish in any water body"}}});
};

/* ==============================  TAB 2 INIT (RICE)  ============================== */
INITS["t-rice"] = function(){
  const nat24 = RICE.by_wave["2024"].__NATIONAL__;
  const kpi = document.getElementById("kpiRice");
  const cR = COL.leaf;
  kpi.innerHTML = [
    {lbl:"Any rice grower, 2024",       val:nat24.RICE_GROWER.toFixed(1)+"%",       series:NAT.rice.RICE_GROWER,       colour:cR},
    {lbl:"BRRI core (BR-28/29), 2024",  val:nat24.BRRI_CORE28_29.toFixed(1)+"%",    series:NAT.rice.BRRI_CORE28_29,    colour:cR},
    {lbl:"New BRRI lines, 2024",        val:nat24.BRRI_NEW_POST2012.toFixed(1)+"%", series:NAT.rice.BRRI_NEW_POST2012, colour:cR},
    {lbl:"Hybrid rice, 2024",           val:nat24.HYBRID.toFixed(1)+"%",            series:NAT.rice.HYBRID,            colour:cR}
  ].map(kpiBox).join("");

  const fams = ["BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL"];
  lineChart("riceFamilies", WAVES.map(w=>WAVE_LBL[w]),
    fams.map((k,i)=>({label:RICE_FAM_LBL[k], data:NAT.rice[k], borderColor:SERIES_RICE[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:"BR-28 and BR-29 hold; hybrid rice and BR-70+ lines surge from near zero"},
              subtitle:{display:true,text:"Share of agricultural households growing each variety family, 2011 to 2024"}}});
  lineChart("riceGrower", WAVES.map(w=>WAVE_LBL[w]),
    [{label:"Any rice grower", data:NAT.rice.RICE_GROWER, borderColor:COL.leaf}],
    {plugins:{title:{display:true,text:"Rice cultivation participation eases from 84% to 70% of agricultural HH"},
              subtitle:{display:true,text:"Share of agricultural households who grew any rice, 2011 to 2024"},
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
      {plugins:{title:{display:true,text:"Top 30 districts for "+RICE_FAM_LBL[k].toLowerCase()+" (2024)"}}});
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
    topTbl("BRRI_CORE28_29","Top 10 districts: BR-28 / BR-29 (2024)")
  + topTbl("BRRI_NEW_POST2012","Top 10 districts: new BRRI lines BR-70+ (2024)");

  // Full district-level table (all 4 rounds, all variety families)
  const RICE_TBL_KEYS = ["RICE_GROWER","BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL"];
  renderFullTable(document.getElementById("riceFullTbl"), RICE, RICE_TBL_KEYS, RICE_FAM_LBL, "mixtape_rice_district");
};

/* ==============================  TAB 3 INIT (AQUA)  ============================== */
INITS["t-aqua"] = function(){
  const nat24 = AQUA.by_wave["2024"].__NATIONAL__;
  const cA = COL.teal;
  document.getElementById("kpiAqua").innerHTML = [
    {lbl:"Any pond, 2024",                val:nat24.ANY_POND.toFixed(1)+"%",        series:NAT.aqua.ANY_POND,        colour:cA},
    {lbl:"Tilapia (incl. GIFT), 2024",    val:nat24.TILAPIA.toFixed(1)+"%",         series:NAT.aqua.TILAPIA,         colour:cA},
    {lbl:"Carp polyculture (2+), 2024",   val:nat24.POLY_CARP_2PLUS.toFixed(1)+"%", series:NAT.aqua.POLY_CARP_2PLUS, colour:cA},
    {lbl:"Mola co-culture, 2024",         val:nat24.MOLA.toFixed(1)+"%",            series:NAT.aqua.MOLA,            colour:cA}
  ].map(kpiBox).join("");

  lineChart("aquaTS", WAVES.map(w=>WAVE_LBL[w]),
    ["ANY_POND","CARP_ANY","POLY_CARP_2PLUS","TILAPIA","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"].map((k,i)=>({
      label:AQUA_IND_LBL[k], data:NAT.aqua[k], borderColor:SERIES_AQUA[i]})),
    {heroIdx:0,
     plugins:{title:{display:true,text:"Pond aquaculture and carp polyculture retreat after 2018/19"},
              subtitle:{display:true,text:"Share of agricultural households practising each, 2011 to 2024"}}});

  lineChart("aquaPoly", WAVES.map(w=>WAVE_LBL[w]),
    [{label:"Carp polyculture (2+ species)", data:NAT.aqua.POLY_CARP_2PLUS, borderColor:COL.teal},
     {label:"Mola co-culture",                data:NAT.aqua.MOLA,           borderColor:COL.teal2}],
    {heroIdx:0,
     plugins:{title:{display:true,text:"Carp polyculture fell from 23% to 14% of agricultural HH; Mola co-culture stayed below 2%"},
              subtitle:{display:true,text:"Two WorldFish-linked aquaculture practices, 2011 to 2024"}}});

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
      {plugins:{title:{display:true,text:"Top 30 districts for "+AQUA_IND_LBL[k].toLowerCase()+" (2024)"}}});
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
    topTbl("ANY_POND","Top 10 pond-intensive districts (2024)")
  + topTbl("TILAPIA","Top 10 tilapia districts (2024)");

  // Full district-level table. 2011/2015/2019 do not have SUPP_FEED/HORMONE/DISEASE_CTL,
  // but the table helper simply shows blanks for missing columns.
  const AQUA_TBL_KEYS = ["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA","SUPP_FEED","HORMONE","DISEASE_CTL"];
  renderFullTable(document.getElementById("aquaFullTbl"), AQUA, AQUA_TBL_KEYS, AQUA_IND_LBL, "mixtape_aqua_district");
};

/* ==============================  TAB 4 INIT (SPIA)  ============================== */
INITS["t-spia"] = function(){
  document.getElementById("kpiSpia").innerHTML = [
    {lbl:"DNA samples genotyped", val:DNA.n_samples.toLocaleString()},
    {lbl:"Unique rice varieties identified", val:DNA.n_varieties},
    {lbl:"Genetic clusters", val:DNA.n_clusters},
    {lbl:"SPIA 2024 households", val:SUM.rounds["2024"].n_hh.toLocaleString()}
  ].map(x=>`<div class="box"><div class="lbl">${x.lbl}</div><div class="big">${x.val}</div></div>`).join("");

  const vEntries = Object.entries(DNA.by_variety).sort((a,b)=>b[1]-a[1]);
  const tot = vEntries.reduce((s,[,v])=>s+v,0);
  const boro = (DNA.by_variety["Bri Dhan BR-28 (Boro)"]||0) + (DNA.by_variety["Bri Dhan BR-29 (Boro)"]||0);
  document.getElementById("dnaBoroPct").innerText = (100*boro/tot).toFixed(1);

  barChart("dnaByVariety", vEntries.map(x=>x[0]),
    [{label:"DNA-verified samples",data:vEntries.map(x=>x[1]),backgroundColor:COL.leaf,borderColor:COL.leaf}],
    {plugins:{title:{display:true,text:"Rice varieties identified by DNA fingerprint (n=370)"},legend:{display:false}},
     scales:{x:{title:{display:true,text:"samples"}},y:{ticks:{font:{size:10.5}}}}});

  const cl = DNA.by_cluster.slice().sort((a,b)=>b.n_samples-a.n_samples);
  barChart("dnaByCluster", cl.map(r=>"Cluster "+r.cluster_id+" : "+r.top_variety),
    [{label:"Samples in cluster",data:cl.map(r=>r.n_samples),backgroundColor:COL.teal,borderColor:COL.teal}],
    {plugins:{title:{display:true,text:"Genetic clusters and their dominant variety"},legend:{display:false}},
     scales:{x:{title:{display:true,text:"samples"}}}});

  // Aqua practices 2024
  const aqNat24 = AQUA.by_wave["2024"].__NATIONAL__;
  barChart("spiaPractices",
    [AQUA_IND_LBL.SUPP_FEED,AQUA_IND_LBL.HORMONE,AQUA_IND_LBL.DISEASE_CTL],
    [{label:"2024 weighted HH %",data:[aqNat24.SUPP_FEED||0,aqNat24.HORMONE||0,aqNat24.DISEASE_CTL||0],
      backgroundColor:COL.teal,borderColor:COL.teal}],
    {plugins:{title:{display:true,text:"Aquaculture intensification practices (2024, e10 module)"},legend:{display:false}}});

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
    {plugins:{title:{display:true,text:"Equipment ownership (2024, SPIA module a5_6)"},legend:{display:false}}});

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
    {lbl:"Power tiller, 2024",         val:(m24.POWER_TILLER||0).toFixed(1)+"%",     series:mechSeries("POWER_TILLER"),     colour:cM, baseLbl:"2018/19"},
    {lbl:"Motorised thresh use, 2024", val:(m24.USE_MOTOR_THRESH||0).toFixed(1)+"%", series:mechSeries("USE_MOTOR_THRESH"), colour:cM, baseLbl:"2018/19"},
    {lbl:"Sprayer, 2024",              val:(m24.SPRAYER||0).toFixed(1)+"%",          series:mechSeries("SPRAYER"),          colour:cM, baseLbl:"2018/19"},
    {lbl:"Electric motor pump, 2024",  val:(m24.ELEC_MOTOR_PUMP||0).toFixed(1)+"%",  series:mechSeries("ELEC_MOTOR_PUMP"),  colour:cM, baseLbl:"2018/19"}
  ].map(kpiBox).join("");

  // Ownership comparison 2019 vs 2024
  const keys = ["TRACTOR","POWER_TILLER","POWER_THRESHER","LLP_IRRIG","AXIAL_FLOW_PUMP",
                "ELEC_MOTOR_PUMP","DIESEL_MOTOR_PUMP","SPRAYER","REAPER","SEEDER_DRILL","COMBINED_HARVEST"];
  const lbls = keys.map(k=>MECH_IND_LBL[k]);
  barChart("mechOwn", lbls,
    [{label:"2018/19",data:keys.map(k=>m19[k]||0),backgroundColor:COL.accent2,borderColor:COL.accent2},
     {label:"2024",   data:keys.map(k=>m24[k]||0),backgroundColor:COL.accent, borderColor:COL.accent}],
    {plugins:{title:{display:true,text:"Household equipment ownership: 2018/19 vs 2024"}}});

  // Use 2024
  const useKeys = ["USE_MOTOR_HARVEST","USE_MOTOR_THRESH","USE_TREADLE_THRESH"];
  barChart("mechUse", useKeys.map(k=>MECH_IND_LBL[k]),
    [{label:"2024 HH %",data:useKeys.map(k=>m24[k]||0),backgroundColor:COL.accent,borderColor:COL.accent}],
    {plugins:{title:{display:true,text:"Paddy-operation practice (2024 actual use)"},legend:{display:false}}});

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
      {plugins:{title:{display:true,text:"Top 30 districts for "+MECH_IND_LBL[k].toLowerCase()+" (2024)"}}});
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
      <div class="ref-eyebrow">Primary reference</div>
      <div class="ref-title">${ref.title}</div>
      <div class="ref-meta">${ref.authors} (${ref.year}). <em>${ref.publisher}</em>. ${ref.license}.</div>
      <div class="ref-links">
        <a href="${ref.report_url}" target="_blank" rel="noopener">Read the SPIA 2025 report (PDF)</a>
        <a href="${ref.github_url}" target="_blank" rel="noopener">SPIA replication repository on GitHub</a>
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
    document.getElementById("techGrid").innerHTML = html || `<div class="empty">No technologies match your filter.</div>`;
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

html_out = (HTML_TMPL
    .replace("__LOGO__", LOGO_B64)
    .replace("__BRIEF__", html.escape(PROJECT_BRIEF))
    .replace("__GEO__",  j(GEO))
    .replace("__RICE__", j(RICE))
    .replace("__AQUA__", j(AQUA))
    .replace("__MECH__", j(MECH))
    .replace("__DNA__",  j(DNA))
    .replace("__NAT__",  j(NAT))
    .replace("__SUM__",  j(SUM))
    .replace("__TECH__", j(TECH))
)
# The HTML template is a raw string (r"""..."""), so any \uXXXX escape we wrote
# inside it reached the output verbatim.  Normalise the few Unicode escapes we used.
import re as _re
def _un(m): return chr(int(m.group(1), 16))
html_out = _re.sub(r"\\u([0-9a-fA-F]{4})", _un, html_out)

out_path = os.path.join(OUT, "mixtape_dashboard.html")
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write(html_out)
print(f"wrote {out_path}  ({os.path.getsize(out_path):,} bytes)")
