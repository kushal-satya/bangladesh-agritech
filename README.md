# Bangladesh MIXTAPE: Rice and Fish Technologies

**Live dashboard:** https://kushal-satya.github.io/bangladesh-agritech/

Household level evidence on CGIAR rice variety, aquaculture and mechanisation adoption across four Bangladesh Integrated Household Survey (BIHS) panel rounds: **2011/12, 2015, 2018/19, 2024**.

MIXTAPE (*Monitoring Impacts for Technology Adoption and Program Engagement*) is a country level study of the dynamics of agricultural innovation in Bangladesh. It asks what the outreach of improved agricultural innovations is, how their adoption varies over time, and what the impacts are on individuals, households, markets, the agri-food system and the environment. The project is jointly led by Cornell University and Bangladesh Agricultural University, with a multidisciplinary team covering agricultural economics, remote sensing, natural resource management (crop breeding and aquaculture), cropping system ecology, behavioural sciences and gender in agriculture.

## What the dashboard shows

Six tabs:

1. **Map overview.** Choropleth of 64 districts. Category buttons (Rice, Aquaculture, Mechanisation) switch the indicator list, and round buttons switch the survey year.
2. **Rice.** National and district weighted prevalence for seven variety families: BRRI core (BR-28/29), older BRRI HYV, new BRRI lines (BR-70 and above), stress tolerant (submergence, zinc biofortified, saline, drought), BINA lines, hybrid, and traditional or local landraces.
3. **Aquaculture.** Any cultivated pond, tilapia (including GIFT), carp polyculture, mola co-culture, prawn (galda), shrimp (bagda).
4. **2024 SPIA round.** DNA fingerprint variety identification on 370 paddy samples, the equipment ownership roster, and aquaculture intensification practices.
5. **Mechanisation.** Ownership comparison between 2018/19 and 2024, plus actual motorised use in 2024.
6. **Technology index.** Every tracked variety, strain, practice and machine, with descriptions and source links.

All numbers are computed from the raw BIHS Stata microdata, weighted with the round specific household sampling weights. No imputed or synthetic values appear on the page. Every figure in a table is read from `data/` when `build_dashboard.py` runs, so the published numbers cannot drift away from the underlying data.

## How these figures relate to the SPIA Bangladesh Study 2025

This dashboard is an **independent recomputation** from the BIHS microdata, not a reproduction of the report's published tables. It applies a single denominator, agricultural households, to every indicator so that technologies can be compared with one another and across the four rounds.

The SPIA report instead picks a denominator suited to each innovation: Boro rice-growing households for rice varieties, fish-cultivating households for individual species, and agricultural households excluding aquaculture-only households for machinery. Rice is where that matters most. The report works with roughly 1,733 Boro rice-growing households in 2024 against the 2,924 agricultural households used here, so rice shares on this dashboard are correspondingly lower than the matching figures in the report.

Sample counts also differ. This dashboard reports the BIHS panel as delivered in the microdata, which includes the Feed the Future booster, while the report uses the nationally representative core of roughly 5,500 households per round. The two agree exactly for 2024, at 5,554.

The DNA tab uses the hybrid-excluded cluster file from the replication package, covering 370 samples in 10 clusters. That is a subset of the full fingerprinting exercise described in the report.

**Cite the SPIA report, not this dashboard, for official reach estimates.**

Run `python check_figures.py` to print every national weighted share held in `data/`. That is the quickest way to check any figure still quoted by hand in the prose.

## Repository layout

```
index.html                     Self-contained dashboard (open in any browser)
content.toml                   All dashboard text and colors, in one editable file
build_dashboard.py             Combines content.toml and data/ into index.html
check_figures.py               Prints every national share in data/, for checking prose
mixtape_pipeline.py            Reads raw BIHS .dta microdata, emits the data/ JSON files
data/
  mixtape_geo.json             64 simplified district polygons
  mixtape_rice.json            District by wave rice variety prevalence
  mixtape_aqua.json            District by wave aquaculture prevalence
  mixtape_mech.json            District by wave mechanisation prevalence
  mixtape_dna.json             2024 DNA fingerprint summary
  mixtape_national.json        National weighted time series
  mixtape_summary.json         Per-round sample sizes and source modules
  mixtape_technologies.json    Technology index entries, institutions, references
  MIXTAPE-logo-800x800.png     Project logo
```

## Editing text or colors

Every heading, paragraph, chart title, indicator label and colour on the dashboard lives in `content.toml`. The `[theme]` section holds a single accent colour, taken from the CGIAR SPIA house teal, plus a neutral grey scale, one chart series palette and one map ramp. Changing `accent` there restyles the whole page. To change anything:

```bash
# 1. Edit content.toml in any text editor
# 2. Rebuild the page
python build_dashboard.py
# 3. Commit and push index.html together with content.toml
```

The build needs Python 3.11 or newer (it uses the standard library `tomllib`) and has no other dependencies.

## Rebuilding the data from microdata

```bash
python -m pip install pyreadstat pandas numpy geopandas shapely

# Point ROOT in mixtape_pipeline.py at your local copy of the BIHS microdata,
# then run:
python mixtape_pipeline.py
python build_dashboard.py
```

Raw BIHS `.dta` files are not redistributed here. They are available on request from the IFPRI Dataverse (https://dataverse.harvard.edu/dataverse/IFPRI) subject to the standard data use agreement.

## Data sources

| Round | Modules used | Sampling weights |
|-------|--------------|-------------------|
| 2011/12 | `001_mod_a_male`, `011_mod_h1_male`, `026_mod_l1_male` | `BIHS_FTF baseline sampling weights.dta` |
| 2015 | `001_r2_mod_a_male`, `015_r2_mod_h1_male`, `037_r2_mod_l1_male` | `BIHS FTF 2015 survey sampling weights.dta` |
| 2018/19 | `009_bihs_r3_male_mod_a`, `016_bihs_r3_male_mod_d2`, `021_bihs_r3_male_mod_h1`, `051_bihs_r3_male_mod_l1` | `158_BIHS sampling weights_r3.dta` |
| 2024 (SPIA) | `SPIA_BIHS_2024_module_{a1, a5_6, c2_4, b6, d2, e5, e10}` plus DNA fingerprint cluster file | `hhweight_24` in module a1 |

District polygons: `polbnda_bgd.shp` (Bangladesh administrative boundaries, Earthworks, Stanford). District names for 2018/19 are cross-walked from the 2015 `District_Name` via the integer part of `a01`, because the 2018/19 `district` variable ships as a numeric code without value labels.

## Contact

Kushal Kumar, kd475@cornell.edu, Cornell University
