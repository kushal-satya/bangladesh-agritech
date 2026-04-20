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

# embed logo as base64 so the HTML is truly single-file
with open(os.path.join(OUT, "MIXTAPE-logo-800x800.png"), "rb") as fh:
    LOGO_B64 = "data:image/png;base64," + base64.b64encode(fh.read()).decode()

def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

PROJECT_BRIEF = """Monitoring Impacts for Technology Adoption and Program Engagement in Bangladesh (MIXTAPE) \u2014 Years 2024\u2013present.
MIXTAPE is a country-level study of the dynamics of agricultural innovation in Bangladesh: the outreach of improved agricultural innovations, how adoption varies over time, and the impacts on individuals, households, markets, the agri-food system, and the environment. Focused on CGIAR-related innovations in rice and aquaculture, the project frames impact assessment as a dynamic household- and system-level analysis. The team is jointly led by Cornell and Bangladesh Agricultural University, combining agricultural economics, remote sensing, natural resource management (crop breeding and aquaculture), cropping-system ecology, behavioural sciences and gender in agriculture across five research institutions."""

HTML_TMPL = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Bangladesh MIXTAPE \u2014 Rice & Fish Technologies</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="icon" type="image/png" href="__LOGO__"/>
<style>
  :root{
    --slate:#2d3e43;
    --slate2:#3e535a;
    --leaf:#6e9b5c;
    --leaf2:#8fb37a;
    --teal:#3d8aa0;
    --teal2:#5aa8bc;
    --cream:#f6f1e4;
    --paper:#faf6ec;
    --ink:#1f2a2d;
    --mute:#6b7778;
    --line:#d8d2c2;
    --accent:#c47a4a;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--paper);color:var(--ink);
      font-family:Georgia,"Iowan Old Style","Palatino Linotype",Palatino,serif;
      line-height:1.55;-webkit-font-smoothing:antialiased;font-size:15px}
  .wrap{max-width:1240px;margin:0 auto;padding:28px 28px 80px}
  header.brand{display:flex;align-items:center;gap:22px;border-bottom:1px solid var(--line);
      padding-bottom:22px;margin-bottom:10px}
  header.brand img{width:104px;height:104px;border-radius:14px;background:var(--cream);padding:6px;flex-shrink:0}
  header.brand .titles{display:flex;flex-direction:column;gap:2px}
  header.brand .titles .kicker{color:var(--mute);font-size:12.5px;letter-spacing:.18em;text-transform:uppercase;
      font-family:"Helvetica Neue",Arial,sans-serif;font-weight:600}
  header.brand .titles h1{margin:0;font-size:56px;line-height:1;letter-spacing:-0.02em;color:var(--slate);
      font-weight:800;font-family:"Helvetica Neue",Arial,sans-serif}
  header.brand .titles h1 .amp{color:var(--teal);font-style:italic;font-weight:400;margin:0 4px}
  header.brand .titles .sub{color:var(--slate2);font-size:14px;font-style:italic;margin-top:6px;max-width:740px}
  .brief{background:var(--cream);border-left:3px solid var(--leaf);padding:14px 18px;margin:14px 0 22px;
      font-size:14px;color:#2b3638;border-radius:2px}
  .brief b{color:var(--slate)}
  nav.tabs{display:flex;gap:0;border-bottom:2px solid var(--slate);margin:10px 0 20px;flex-wrap:wrap}
  nav.tabs button{font-family:inherit;background:transparent;border:0;padding:10px 18px;font-size:14px;
      color:var(--mute);cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-2px;letter-spacing:.02em}
  nav.tabs button:hover{color:var(--slate)}
  nav.tabs button.on{color:var(--slate);border-bottom-color:var(--teal);font-weight:600}
  .tab{display:none}
  .tab.on{display:block}
  h2.section{font-size:22px;color:var(--slate);margin:30px 0 8px;letter-spacing:-0.01em;font-weight:700}
  h3.sub{font-size:16px;color:var(--slate2);margin:18px 0 6px;font-weight:600}
  p.lede{color:#384446;font-size:15px;margin:6px 0 14px;max-width:900px}
  p.note{font-size:12.5px;color:var(--mute);margin:4px 0 16px;font-style:italic}
  .row{display:grid;gap:18px}
  .row-2{grid-template-columns:1fr 1fr}
  .row-3{grid-template-columns:1fr 1fr 1fr}
  @media (max-width:920px){.row-2,.row-3{grid-template-columns:1fr}}
  .card{background:#fff;border:1px solid var(--line);border-radius:6px;padding:16px 18px}
  .card h4{margin:0 0 6px 0;font-size:14px;color:var(--slate);font-weight:700;letter-spacing:.04em;text-transform:uppercase}
  .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:10px 0 18px}
  @media (max-width:820px){.kpi{grid-template-columns:repeat(2,1fr)}}
  .kpi .box{background:#fff;border:1px solid var(--line);border-radius:6px;padding:12px 14px}
  .kpi .big{font-size:26px;color:var(--slate);font-weight:700;letter-spacing:-.02em;margin:2px 0 0}
  .kpi .lbl{font-size:11.5px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
  table.tbl{width:100%;border-collapse:collapse;font-size:13.5px;background:#fff;
      border:1px solid var(--line);border-radius:4px;overflow:hidden}
  table.tbl th,table.tbl td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:right}
  table.tbl th{background:var(--cream);color:var(--slate);text-align:right;font-weight:600;font-size:12px;
      text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid var(--slate)}
  table.tbl td:first-child,table.tbl th:first-child{text-align:left}
  table.tbl tr:last-child td{border-bottom:none}
  .map-wrap{position:relative;height:560px;border-radius:6px;overflow:hidden;border:1px solid var(--line);
      background:#fff}
  .leaflet-container{background:#f3ecd9;font-family:inherit}
  .chart-wrap{position:relative;height:340px;background:#fff;border:1px solid var(--line);border-radius:6px;padding:10px 14px}
  .chart-wrap.tall{height:420px}
  .controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin:6px 0 14px}
  .controls label{font-size:13px;color:var(--slate);font-weight:600}
  .controls select{font-family:inherit;font-size:14px;padding:7px 12px;
      border:1px solid var(--line);background:#fff;border-radius:4px;color:var(--slate);cursor:pointer;
      min-width:300px}
  .controls select:focus{outline:2px solid var(--teal);outline-offset:1px}
  .cat-pills, .year-pills{display:inline-flex;gap:0;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:#fff}
  .cat-pills button, .year-pills button{font-family:inherit;font-size:13px;padding:7px 14px;border:0;
      background:#fff;color:var(--slate);cursor:pointer;border-right:1px solid var(--line);font-weight:600;letter-spacing:.02em}
  .cat-pills button:last-child, .year-pills button:last-child{border-right:0}
  .cat-pills button.on, .year-pills button.on{background:var(--slate);color:#fff}
  .cat-pills button:hover:not(.on), .year-pills button:hover:not(.on){background:var(--cream)}
  .controls button.pill{font-family:inherit;font-size:13px;padding:5px 10px;
      border:1px solid var(--line);background:#fff;border-radius:3px;color:var(--slate);cursor:pointer}
  .controls button.pill.on{background:var(--slate);color:#fff;border-color:var(--slate)}
  .legend{display:flex;gap:8px;align-items:center;font-size:12px;color:var(--slate)}
  .legend .sw{width:14px;height:10px;display:inline-block;border-radius:2px;margin-right:4px}
  .footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--line);font-size:13px;color:var(--mute)}
  .footer .contact{color:var(--slate);font-size:14px;margin-bottom:6px}
  .footer .contact a{color:var(--teal);text-decoration:none;border-bottom:1px solid var(--teal2)}
  .footer .attrib{font-size:12.5px;color:var(--mute);max-width:820px;line-height:1.55}
  .src{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:11.5px;color:var(--mute)}
  .info{position:absolute;top:10px;left:10px;background:rgba(255,255,255,.96);padding:8px 10px;
      border-radius:4px;font-size:12px;color:var(--slate);max-width:260px;border:1px solid var(--line);z-index:500}
  .info h5{margin:0 0 4px;font-size:12.5px;color:var(--slate)}
  .info .val{font-size:14px;color:var(--slate);font-weight:700}
  .mini-legend{position:absolute;bottom:14px;left:10px;background:rgba(255,255,255,.96);padding:8px 10px;
      border-radius:4px;font-size:11.5px;color:var(--slate);border:1px solid var(--line);z-index:500;max-width:260px}
  .mini-legend .row-l{display:flex;gap:6px;align-items:center;margin:2px 0}
  .mini-legend .sw{width:18px;height:10px;display:inline-block}
  .tag{display:inline-block;background:var(--cream);color:var(--slate);padding:2px 8px;border-radius:10px;
      font-size:11px;margin-right:4px;letter-spacing:.04em;text-transform:uppercase}
  .tag.green{background:#e4efda;color:#445d37}
  .tag.teal{background:#dbebf0;color:#26535f}
  .tag.orange{background:#f1e0d1;color:#7a492a}
  details.tech{background:var(--cream);padding:10px 14px;border-radius:4px;margin:6px 0;font-size:13.5px}
  details.tech summary{cursor:pointer;color:var(--slate);font-weight:600}
  details.tech p{margin:6px 0 0;color:#2f3c3e}
  small.cap{color:var(--mute);font-size:11.5px}
</style>
</head>
<body>
<div class="wrap">

<header class="brand">
  <img src="__LOGO__" alt="MIXTAPE logo"/>
  <div class="titles">
    <div class="kicker">Bangladesh &middot; CGIAR rice &amp; fish technologies</div>
    <h1>MIXTAPE</h1>
    <div class="sub">Household-level evidence on rice-variety, aquaculture and mechanisation adoption across four BIHS panel rounds: 2011/12, 2015, 2018/19, 2024.</div>
  </div>
</header>

<div class="brief"><b>About the project.</b> __BRIEF__</div>

<nav class="tabs" id="tabs">
  <button data-tab="t-map" class="on">1 &middot; Map overview</button>
  <button data-tab="t-rice">2 &middot; Rice deep dive</button>
  <button data-tab="t-aqua">3 &middot; Aquaculture deep dive</button>
  <button data-tab="t-spia">4 &middot; 2024 SPIA round</button>
  <button data-tab="t-mech">5 &middot; Mechanisation &amp; practices</button>
</nav>

<!-- ============================== TAB 1 :: MAP ============================== -->
<section id="t-map" class="tab on">
  <h2 class="section">CGIAR technologies across Bangladesh, 2011&mdash;2024</h2>
  <p class="lede">The map below shows the weighted household-level prevalence of a chosen CGIAR-linked
  technology for any BIHS round. Prevalence is computed from raw Stata microdata for
  <b>6,503 (2011) &middot; 6,715 (2015) &middot; 6,011 (2019) &middot; 5,554 (2024)</b> households,
  aggregated with the round's sampling weights. Hover a district for the underlying number of sampled households.</p>
  <div class="controls">
    <div class="cat-pills" id="mapCatPills">
      <button class="pill on" data-cat="rice">Rice</button>
      <button class="pill" data-cat="aqua">Aquaculture</button>
      <button class="pill" data-cat="mech">Mechanisation</button>
    </div>
    <select id="mapIndicator" aria-label="Indicator"></select>
    <div class="year-pills" id="mapYearPills">
      <button class="pill" data-year="2011">2011/12</button>
      <button class="pill" data-year="2015">2015</button>
      <button class="pill" data-year="2019">2018/19</button>
      <button class="pill on" data-year="2024">2024</button>
    </div>
  </div>
  <div class="map-wrap">
    <div id="map" style="height:100%"></div>
    <div class="info" id="mapInfo"><h5>Hover a district</h5><div class="val">&mdash;</div></div>
    <div class="mini-legend" id="mapLegend"></div>
  </div>

  <h3 class="sub">National weighted prevalence over time</h3>
  <p class="lede">Each line is a weighted national mean across all sampled households of the round.</p>
  <div class="row row-2">
    <div class="chart-wrap"><canvas id="natRice"></canvas></div>
    <div class="chart-wrap"><canvas id="natAqua"></canvas></div>
  </div>

  <h3 class="sub">What the five indicator families capture</h3>
  <details class="tech" open><summary>Rice: BRRI core boro (BR-28 / BR-29), newer BRRI lines (BR-70+), stress-tolerant (submergence, Zn-biofortified, drought, saline)</summary>
    <p>BR-28 and BR-29 are the post-2000 mega-varieties of Boro rice developed by BRRI from IRRI lines. Newer BRRI Dhan 70+ include post-2012 releases such as BRRI Dhan 89 and 92 (high-yielding aromatic, Boro). Stress-tolerant varieties include BR-47 (submergence, Aus), BR-51 (submergence, Aman), BR-62 and BR-64 (HarvestPlus Zn-biofortified), BR-66 (drought) and BR-67 (saline).</p></details>
  <details class="tech"><summary>Aquaculture: any fish pond, GIFT/tilapia, 2+ carp polyculture, Mola small-fish co-culture, prawn (galda), shrimp (bagda)</summary>
    <p>WorldFish&nbsp;/ CGIAR-associated aquaculture technologies include GIFT (Genetically-Improved Farmed Tilapia), carp polyculture with 2+ carp species, and mola co-culture (small indigenous fish farmed alongside carp for micronutrient density). Prawn (galda) and shrimp (bagda) are traditional high-value species.</p></details>
  <details class="tech"><summary>Mechanisation: tractor, power tiller, power thresher, LLP / axial-flow / diesel / electric pump, sprayer, reaper, combined harvester, seeder drill</summary>
    <p>Identified from durable-asset rosters (Module&nbsp;D2 in 2018/19; a5_6 in 2024) and from actual use of motorised harvest &amp; thresh in 2024 (module&nbsp;d2). Values for 2011/2015 come only from harmonised asset flags (tractor); more granular equipment histories are not coded for those two rounds in the harmonised file.</p></details>
</section>

<!-- ============================== TAB 2 :: RICE ============================== -->
<section id="t-rice" class="tab">
  <h2 class="section">Rice-variety adoption, 2011&mdash;2024</h2>
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

  <h3 class="sub">Top districts &mdash; BRRI core (BR-28 / BR-29) and new BRRI lines (BR-70+), 2024</h3>
  <div id="riceTopTables" class="row row-2"></div>

  <p class="note">Source: BIHS 011_mod_h1_male.dta, 015_r2_mod_h1_male.dta, 021_bihs_r3_male_mod_h1.dta,
  SPIA_BIHS_2024_module_c2_4.dta + module_b6.dta. Weights: BIHS_FTF baseline sampling weights, BIHS FTF 2015 survey sampling weights,
  158_BIHS sampling weights_r3.dta, SPIA 2024 hhweight_24.</p>
</section>

<!-- ============================== TAB 3 :: AQUA ============================== -->
<section id="t-aqua" class="tab">
  <h2 class="section">Aquaculture adoption, 2011&mdash;2024</h2>
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

  <p class="note">Source: BIHS 026_mod_l1_male.dta, 037_r2_mod_l1_male.dta, 051_bihs_r3_male_mod_l1.dta,
  SPIA_BIHS_2024_module_e5.dta + module_e10.dta. Species codes from value labels in-file.</p>
</section>

<!-- ============================== TAB 4 :: 2024 SPIA ============================== -->
<section id="t-spia" class="tab">
  <h2 class="section">2024 SPIA round &mdash; new insights</h2>
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

  <p class="note">Source: SPIA_BIHS_2024_module_a1.dta, a5_6.dta, c2_4.dta, b6.dta, e5.dta, e10.dta, d2.dta,
  and ref_clusters_no_hybrids_with_HH_Ids.csv (DNA fingerprints).</p>
</section>

<!-- ============================== TAB 5 :: MECH ============================== -->
<section id="t-mech" class="tab">
  <h2 class="section">Mechanisation &amp; agricultural practices, 2018/19 and 2024</h2>
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

  <p class="note">Sources: 016_bihs_r3_male_mod_d2.dta (R3 asset roster, codes 12=tractor, 13=power tiller, 15=thresher,
  22=LLP pump, 25=electric motor pump, 26=diesel pump, 27=sprayer, 28=reaper, 36=axial-flow pump, 37=seeder drill,
  39=combined harvester); SPIA_BIHS_2024_module_a5_6.dta (binary ownership indicators); SPIA_BIHS_2024_module_d2.dta
  (actual motorised use). 2011 and 2015 ownership draws on the limited set of durable-asset flags in
  BIHS_household_2011_15.dta (asset_tractor only).</p>
</section>

<div class="footer">
<div class="contact">
  <b>Contact.</b> Kushal Kumar &middot; <a href="mailto:kd475@cornell.edu">kd475@cornell.edu</a>
</div>
<div class="attrib">
  Data: Bangladesh Integrated Household Survey (BIHS) rounds 1&ndash;3 and the 2024 SPIA round, International Food Policy Research Institute (IFPRI). Methods follow
  standard weighted-prevalence conventions using the round-specific household sampling weights.
</div>
</div>

</div><!-- /wrap -->

<script>
/* ==============================  DATA  ============================== */
const GEO  = __GEO__;
const RICE = __RICE__;
const AQUA = __AQUA__;
const MECH = __MECH__;
const DNA  = __DNA__;
const NAT  = __NAT__;
const SUM  = __SUM__;

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
const COL = {slate:"#2d3e43", slate2:"#3e535a", leaf:"#6e9b5c", leaf2:"#8fb37a",
             teal:"#3d8aa0", teal2:"#5aa8bc", cream:"#f6f1e4", ink:"#1f2a2d",
             mute:"#6b7778", accent:"#c47a4a"};
const SERIES_COL = [COL.slate, COL.teal, COL.leaf, COL.accent, COL.slate2, COL.teal2, COL.leaf2, "#8a5a8b", "#b4534f", "#4e7c6e"];

Chart.defaults.font.family = "Georgia, 'Iowan Old Style', Palatino, serif";
Chart.defaults.font.size   = 12;
Chart.defaults.color       = COL.ink;

/* ==============================  TABS  ============================== */
const chartRefs = {};
const tabInit   = {};
document.getElementById("tabs").addEventListener("click", e => {
  if(e.target.tagName !== "BUTTON") return;
  const id = e.target.dataset.tab;
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.toggle("on", b === e.target));
  document.querySelectorAll("section.tab").forEach(s => s.classList.toggle("on", s.id === id));
  lazyInit(id);
});
function lazyInit(id){ if(tabInit[id]) return; tabInit[id]=true; (INITS[id]||(()=>{}))(); }

/* ==============================  MAP  ============================== */
function ramp(v, stops){
  if(v==null || isNaN(v)) return "#e8e2d2";
  for(const [t,c] of stops) if(v<=t) return c;
  return stops[stops.length-1][1];
}
const MAP_RAMPS = {
  rice:{stops:[[0,"#f2efe0"],[2,"#e0ebd7"],[5,"#cddfc6"],[10,"#a8c99b"],[20,"#7cae6d"],[35,"#527d46"],[100,"#2e5027"]]},
  aqua:{stops:[[0,"#f2efe0"],[2,"#dbecee"],[5,"#b9d9dc"],[10,"#87bec5"],[20,"#4f9aa6"],[35,"#2a6a76"],[100,"#0f3f48"]]},
  mech:{stops:[[0,"#f2efe0"],[2,"#efe2d2"],[5,"#e5c8aa"],[10,"#d4a375"],[20,"#b37a48"],[35,"#8a552a"],[100,"#5a3614"]]}
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
      ["BRRI core — BR-28 / BR-29 (Boro mega-varieties)", "BRRI_CORE28_29"],
      ["New BRRI lines — BR-70 and above (post-2012)",    "BRRI_NEW_POST2012"],
      ["Stress-tolerant — submergence / Zn / saline / drought", "BRRI_STRESS"],
      ["Older BRRI HYV — BR-1 through BR-69",            "BRRI_OLDER_HYV"],
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
      ["Prawn — galda",                      "PRAWN_GALDA"],
      ["Shrimp — bagda",                     "SHRIMP_BAGDA"]
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
    if(e.target.tagName!=="BUTTON") return;
    mapCat = e.target.dataset.cat;
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
      return {color:"#fff",weight:0.8,opacity:1,fillOpacity:0.88,fillColor:ramp(v,stops)};
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
            <div class="val">${v==null?"&mdash;":v.toFixed(1)+"%"}</div>
            <small class="cap">${WAVE_LBL[year]} &middot; n=${n??"&mdash;"} households</small>`;
        },
        mouseout:()=>{ geoLayer.resetStyle(layer); document.getElementById("mapInfo").innerHTML='<h5>Hover a district</h5><div class="val">&mdash;</div>'; },
        click:()=>map.fitBounds(layer.getBounds(),{padding:[20,20]})
      });
    }
  }).addTo(map);
  // legend
  const lg = document.getElementById("mapLegend");
  const item = MAP_CATALOG[mapCat].items.find(x=>x[1]===ind);
  const title = item ? item[0] : "";
  let html = `<b>${MAP_CATALOG[mapCat].label}</b><br>${title}<br><small class="cap">% of households &middot; ${WAVE_LBL[year]}</small>`;
  stops.forEach((s,i)=>{
    const hi = s[0]; const lo = i===0?0:stops[i-1][0];
    html += `<div class="row-l"><span class="sw" style="background:${s[1]}"></span>${lo.toFixed(0)}&ndash;${hi===100?">35":hi.toFixed(0)}%</div>`;
  });
  lg.innerHTML = html;
}

/* ==============================  CHART HELPERS  ============================== */
function lineChart(canvas, labels, datasets, opts){
  if(chartRefs[canvas]) chartRefs[canvas].destroy();
  chartRefs[canvas] = new Chart(document.getElementById(canvas),{
    type:"line",
    data:{labels,datasets},
    options:Object.assign({
      responsive:true,maintainAspectRatio:false,
      plugins:{title:{display:true,color:COL.slate,font:{size:14,weight:"600"},padding:{bottom:10}},
               legend:{position:"bottom",labels:{boxWidth:12,font:{size:11.5}}}},
      scales:{y:{beginAtZero:true,title:{display:true,text:"% households (weighted)",font:{size:11}},grid:{color:"#eee4cd"}},
              x:{grid:{display:false}}}
    },opts||{})
  });
}
function barChart(canvas, labels, datasets, opts){
  if(chartRefs[canvas]) chartRefs[canvas].destroy();
  chartRefs[canvas] = new Chart(document.getElementById(canvas),{
    type:"bar",
    data:{labels,datasets},
    options:Object.assign({
      responsive:true,maintainAspectRatio:false,indexAxis:"y",
      plugins:{title:{display:true,color:COL.slate,font:{size:14,weight:"600"},padding:{bottom:10}},
               legend:{position:"bottom",labels:{boxWidth:12,font:{size:11.5}}}},
      scales:{x:{beginAtZero:true,title:{display:true,text:"% households",font:{size:11}},grid:{color:"#eee4cd"}},
              y:{grid:{display:false}}}
    },opts||{})
  });
}

/* ==============================  TAB 1 INIT  ============================== */
INITS = {};
INITS["t-map"] = function(){
  initMap();
  lineChart("natRice", WAVES.map(w=>WAVE_LBL[w]),
    ["BRRI_CORE28_29","BRRI_NEW_POST2012","BRRI_STRESS","HYBRID","LOCAL","BINA"].map((k,i)=>({
      label: RICE_FAM_LBL[k], data: NAT.rice[k],
      borderColor: SERIES_COL[i], backgroundColor: SERIES_COL[i], tension:.2, pointRadius:4
    })),
    {plugins:{title:{display:true,text:"Rice variety families (national, weighted)"}}});
  lineChart("natAqua", WAVES.map(w=>WAVE_LBL[w]),
    ["ANY_POND","TILAPIA","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"].map((k,i)=>({
      label: AQUA_IND_LBL[k], data: NAT.aqua[k],
      borderColor: SERIES_COL[i], backgroundColor: SERIES_COL[i], tension:.2, pointRadius:4
    })),
    {plugins:{title:{display:true,text:"Aquaculture indicators (national, weighted)"}}});
};

/* ==============================  TAB 2 INIT (RICE)  ============================== */
INITS["t-rice"] = function(){
  const nat24 = RICE.by_wave["2024"].__NATIONAL__;
  const kpi = document.getElementById("kpiRice");
  kpi.innerHTML = [
    {lbl:"Any rice grower, 2024", val:nat24.RICE_GROWER.toFixed(1)+"%"},
    {lbl:"BRRI core (BR-28/29), 2024", val:nat24.BRRI_CORE28_29.toFixed(1)+"%"},
    {lbl:"New BRRI lines, 2024", val:nat24.BRRI_NEW_POST2012.toFixed(1)+"%"},
    {lbl:"Hybrid rice, 2024", val:nat24.HYBRID.toFixed(1)+"%"}
  ].map(x=>`<div class="box"><div class="lbl">${x.lbl}</div><div class="big">${x.val}</div></div>`).join("");

  const fams = ["BRRI_CORE28_29","BRRI_OLDER_HYV","BRRI_NEW_POST2012","BRRI_STRESS","BINA","HYBRID","LOCAL"];
  lineChart("riceFamilies", WAVES.map(w=>WAVE_LBL[w]),
    fams.map((k,i)=>({label:RICE_FAM_LBL[k],data:NAT.rice[k],borderColor:SERIES_COL[i],backgroundColor:SERIES_COL[i],tension:.2,pointRadius:4})),
    {plugins:{title:{display:true,text:"Variety families, national weighted prevalence"}}});
  lineChart("riceGrower", WAVES.map(w=>WAVE_LBL[w]),
    [{label:"Any rice grower",data:NAT.rice.RICE_GROWER,borderColor:COL.leaf,backgroundColor:COL.leaf,tension:.2,pointRadius:4,fill:true}],
    {plugins:{title:{display:true,text:"Share of BIHS households who grew any rice"}}});

  const sel = document.getElementById("riceDistFam");
  fams.forEach((k,i)=>{const o=document.createElement("option");o.value=k;o.innerHTML=RICE_FAM_LBL[k];if(i===0)o.selected=true;sel.appendChild(o);});
  function redrawDist(){
    const k = sel.value;
    const data = RICE.by_wave["2024"];
    const rows = Object.entries(data).filter(([n])=>n!=="__NATIONAL__")
                  .map(([name,r])=>({name,v:r[k]||0}))
                  .sort((a,b)=>b.v-a.v).slice(0,30);
    barChart("riceDistChart", rows.map(r=>r.name),
      [{label:RICE_FAM_LBL[k]+" — 2024",data:rows.map(r=>r.v),backgroundColor:COL.leaf,borderColor:COL.leaf}],
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
    topTbl("BRRI_CORE28_29","Top 10 districts &mdash; BR-28 / BR-29 (2024)")
  + topTbl("BRRI_NEW_POST2012","Top 10 districts &mdash; new BRRI lines BR-70+ (2024)");
};

/* ==============================  TAB 3 INIT (AQUA)  ============================== */
INITS["t-aqua"] = function(){
  const nat24 = AQUA.by_wave["2024"].__NATIONAL__;
  document.getElementById("kpiAqua").innerHTML = [
    {lbl:"Any pond, 2024", val:nat24.ANY_POND.toFixed(1)+"%"},
    {lbl:"Tilapia (incl. GIFT), 2024", val:nat24.TILAPIA.toFixed(1)+"%"},
    {lbl:"Carp polyculture (2+), 2024", val:nat24.POLY_CARP_2PLUS.toFixed(1)+"%"},
    {lbl:"Mola co-culture, 2024", val:nat24.MOLA.toFixed(1)+"%"}
  ].map(x=>`<div class="box"><div class="lbl">${x.lbl}</div><div class="big">${x.val}</div></div>`).join("");

  lineChart("aquaTS", WAVES.map(w=>WAVE_LBL[w]),
    ["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"].map((k,i)=>({
      label:AQUA_IND_LBL[k],data:NAT.aqua[k],borderColor:SERIES_COL[i],backgroundColor:SERIES_COL[i],tension:.2,pointRadius:4
    })),
    {plugins:{title:{display:true,text:"Aquaculture indicators, national weighted prevalence"}}});

  lineChart("aquaPoly", WAVES.map(w=>WAVE_LBL[w]),
    [{label:"Carp polyculture (2+)",data:NAT.aqua.POLY_CARP_2PLUS,borderColor:COL.teal,backgroundColor:COL.teal,tension:.2,pointRadius:5,fill:true},
     {label:"Mola co-culture",data:NAT.aqua.MOLA,borderColor:COL.leaf,backgroundColor:COL.leaf,tension:.2,pointRadius:5,fill:false}],
    {plugins:{title:{display:true,text:"WorldFish-linked practices: carp polyculture &amp; Mola co-culture"}}});

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
      [{label:AQUA_IND_LBL[k]+" — 2024",data:rows.map(r=>r.v),backgroundColor:COL.teal,borderColor:COL.teal}],
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
  barChart("dnaByCluster", cl.map(r=>"Cluster "+r.cluster_id+"  \u2014  "+r.top_variety),
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
};

/* ==============================  TAB 5 INIT (MECH)  ============================== */
INITS["t-mech"] = function(){
  const m24 = MECH.by_wave["2024"].__NATIONAL__ || {};
  const m19 = MECH.by_wave["2019"].__NATIONAL__ || {};
  document.getElementById("kpiMech").innerHTML = [
    {lbl:"Power tiller, 2024", val:(m24.POWER_TILLER||0).toFixed(1)+"%"},
    {lbl:"Motorised thresh use, 2024", val:(m24.USE_MOTOR_THRESH||0).toFixed(1)+"%"},
    {lbl:"Sprayer, 2024", val:(m24.SPRAYER||0).toFixed(1)+"%"},
    {lbl:"Electric motor pump, 2024", val:(m24.ELEC_MOTOR_PUMP||0).toFixed(1)+"%"}
  ].map(x=>`<div class="box"><div class="lbl">${x.lbl}</div><div class="big">${x.val}</div></div>`).join("");

  // Ownership comparison 2019 vs 2024
  const keys = ["TRACTOR","POWER_TILLER","POWER_THRESHER","LLP_IRRIG","AXIAL_FLOW_PUMP",
                "ELEC_MOTOR_PUMP","DIESEL_MOTOR_PUMP","SPRAYER","REAPER","SEEDER_DRILL","COMBINED_HARVEST"];
  const lbls = keys.map(k=>MECH_IND_LBL[k]);
  barChart("mechOwn", lbls,
    [{label:"2018/19",data:keys.map(k=>m19[k]||0),backgroundColor:COL.slate2,borderColor:COL.slate2},
     {label:"2024",   data:keys.map(k=>m24[k]||0),backgroundColor:COL.teal,   borderColor:COL.teal}],
    {plugins:{title:{display:true,text:"Household equipment ownership — 2018/19 vs 2024"}}});

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
      [{label:MECH_IND_LBL[k]+" — 2024",data:rows.map(r=>r.v),backgroundColor:COL.accent,borderColor:COL.accent}],
      {plugins:{title:{display:true,text:"Top 30 districts for "+MECH_IND_LBL[k].toLowerCase()+" (2024)"}}});
  }
  sel.onchange = redrawMechDist; redrawMechDist();
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
