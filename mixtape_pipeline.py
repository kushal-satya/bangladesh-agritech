"""
MIXTAPE data pipeline
=====================
Reads RAW BIHS Stata microdata (.dta) for 4 waves + 2024 SPIA round,
computes household-level indicators for rice varieties, aquaculture
species/practices, and mechanization, then aggregates with sampling
weights to district level.

Outputs (all under ./output/):
  mixtape_geo.json          - simplified district polygons (from polbnda_bgd.shp)
  mixtape_rice.json         - district x wave rice variety prevalence
  mixtape_aqua.json         - district x wave aquaculture prevalence
  mixtape_mech.json         - district x wave mechanization prevalence
  mixtape_dna.json          - 2024 DNA fingerprinting variety counts
  mixtape_national.json     - national weighted time series per technology
  mixtape_summary.json      - metadata (n hh per wave, modules used)

ALL numbers below are computed from the Stata microdata.
NO synthetic numbers are introduced anywhere.
"""
from __future__ import annotations
import os, json, re, sys, warnings
from collections import defaultdict
import pyreadstat as prs
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import mapping
from shapely.ops import unary_union
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\kd475\RES\BGD_MIX\BIHS data, shape files and SPIA 2024 wave"
OUT  = r"C:\Users\kd475\RES\BGD_MIX\output"
os.makedirs(OUT, exist_ok=True)

def _json(o):
    if isinstance(o, (np.integer,)):   return int(o)
    if isinstance(o, (np.floating,)):  return (None if np.isnan(o) else float(o))
    if isinstance(o, np.ndarray):      return o.tolist()
    if isinstance(o, pd.Timestamp):    return o.isoformat()
    raise TypeError(f"Not JSON serialisable: {type(o).__name__}")

def dump(obj, name):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, default=_json, ensure_ascii=False)
    print(f"  wrote {p}  ({os.path.getsize(p):,} bytes)")

def read_dta(rel, **kw):
    full = os.path.join(ROOT, rel.replace("/", os.sep))
    try:
        df, meta = prs.read_dta(full, **kw)
        return df, meta
    except UnicodeDecodeError:
        df, meta = prs.read_dta(full, encoding="latin1", **kw)
        return df, meta

# ---------------------------------------------------------------------------
# RICE VARIETY CLASSIFICATION
# Based on the full H1 value labels (codes consistent 2011/2015/2019) and
# 2024 c2paddy_mainvariety (codes shift by +1 in some ranges). Group families:
#   BRRI_CORE28_29  : BR-28 / BR-29 (Boro mega-varieties)
#   BRRI_NEW_POST2012 : BR-70 and up  (BR-89, BR-92 etc. - post-2015 IRRI lines)
#   BRRI_STRESS     : BR-47 (flash-flood), BR-51/52/56 (submergence),
#                     BR-62/64 (Zn-biofortified HarvestPlus),
#                     BR-66 (drought), BR-67 (saline)
#   BRRI_OLDER_HYV  : all other BR / Bri Dhan BR up to BR-69
#   BINA            : Binadhan (codes 65-69 in 2011; 130-154 in 2024)
#   HYBRID          : Hybrid varieties (codes 70-73 in 2011, 155-162 in 2024)
#   LOCAL           : traditional/local varieties
# ---------------------------------------------------------------------------

def classify_variety_2011(code):
    """2011 H1 codebook: 1..53 map to BR1..BR54; 27=BR28, 28=BR29 etc."""
    if pd.isna(code): return None
    c = int(code)
    if c in (27, 28):            return "BRRI_CORE28_29"
    if c in (46,):               return "BRRI_STRESS"   # BR-47 submergence Aush
    if c in (50, 51):            return "BRRI_STRESS"   # BR-51 submergence Aman
    if c in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
             29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 47, 48, 49, 52, 53):
        return "BRRI_OLDER_HYV"
    if 65 <= c <= 69:            return "BINA"
    if 70 <= c <= 73:            return "HYBRID"
    if c == 54:                  return "LOCAL"         # "other"
    if 55 <= c <= 64 or c == 74: return "LOCAL"         # named local/private
    return None

def classify_variety_2015_2019(code):
    """2015+2019 H1: 1..53 = BR-1..BR-54, 56+ extended with Dhan 64-69 + stress."""
    if pd.isna(code): return None
    c = int(code)
    if c in (27, 28):            return "BRRI_CORE28_29"
    if c in (46,):               return "BRRI_STRESS"           # BR-47 Aus
    if c in (50, 51):            return "BRRI_STRESS"           # BR-51 Aman submergence
    if c in (61, 63):            return "BRRI_STRESS"           # BR-62, BR-64 Zinc (HarvestPlus)
    if c == 65:                  return "BRRI_STRESS"           # BR-66 drought
    if c == 66:                  return "BRRI_STRESS"           # BR-67 saline
    if c in (68, 67, 62):        return "BRRI_OLDER_HYV"        # BR-63, BR-68, BR-69
    if 1 <= c <= 68:             return "BRRI_OLDER_HYV"
    if 69 <= c <= 69:            return "BRRI_NEW_POST2012"     # NERICA (AfricaRice/IRRI)
    if 95 <= c <= 115:           return "BINA"                  # BINA + Iratom
    if 100 <= c <= 103:          return "HYBRID"
    if 92 <= c <= 94 or 116 <= c <= 128:  return "HYBRID"
    if c in (74, 75, 76, 77, 78, 79, 80, 81, 82, 85, 86, 87, 88, 89, 90, 91):
        return "LOCAL"
    if c in (888, 999):          return "LOCAL"
    return None

def classify_variety_2024(code):
    """2024 c2paddy_mainvariety codebook (shifted)."""
    if pd.isna(code) or code < 0: return None
    c = int(code)
    # 2024 codebook: c in 1..68 = Chandina BR-1 through BR-69.
    # c=27 is BR-28, c=28 is BR-29.
    if c in (27, 28):            return "BRRI_CORE28_29"
    if c in (46,):               return "BRRI_STRESS"           # BR-47
    if c in (50, 51):            return "BRRI_STRESS"           # BR-51
    if c in (61, 63):            return "BRRI_STRESS"           # BR-62, BR-64 Zinc
    if c == 65:                  return "BRRI_STRESS"           # BR-66 drought
    if c == 66:                  return "BRRI_STRESS"           # BR-67 saline
    if 1 <= c <= 68:             return "BRRI_OLDER_HYV"
    # 69..105 = Bri Dhan 70 to Bri Dhan 106 (post-2012 IRRI lines)
    if 69 <= c <= 105:           return "BRRI_NEW_POST2012"
    if 106 <= c <= 119:          return "LOCAL"
    if 120 <= c <= 129:          return "LOCAL"                  # Alok, Sonar bangla, etc.
    if 130 <= c <= 154:          return "BINA"
    if 155 <= c <= 162:          return "HYBRID"                 # BRI hybrids
    if 163 <= c <= 214:          return "HYBRID"                 # miscellaneous hybrids
    return None

# Fish species (carp polyculture = presence of 2+ carp species 1..8;
# GIFT/Tilapia = code 10; Prawn=18; Shrimp=19)
CARP_CODES = {1, 2, 3, 4, 5, 6, 7, 8, 9}
TILAPIA_CODE = 10
PRAWN_CODE   = 18
SHRIMP_CODE  = 19
ILISH_CODE   = 22
MOLA_CODE    = 21   # Mola (WorldFish biofortified small fish polyculture)

# ---------------------------------------------------------------------------
# 1) DISTRICT / DIVISION GEO
# ---------------------------------------------------------------------------
print("\n[1/7] Reading Bangladesh district polygons (polbnda_bgd.shp)")
shp = os.path.join(ROOT, "Bangladesh map shapefile", "data Earthwork Stanford", "polbnda_bgd.shp")
gdf = gpd.read_file(shp).to_crs("EPSG:4326")
gdf["division"] = gdf["nam"].astype(str).str.strip().str.title()
gdf["district"] = gdf["laa"].astype(str).str.strip().str.title()
# Normalize a few spelling variants so later joins work
DISTRICT_FIX = {
    "Cox'S Baza": "Cox's Bazar", "Cox'S Bazar": "Cox's Bazar",
    "Brahmanbari": "Brahmanbaria", "Brahamanbar": "Brahmanbaria",
    "Chittagong H": "Chittagong Hill Tracts",
    "Chittagong Hill": "Chittagong Hill Tracts",
    "Netrokona": "Netrakona", "Netrakona": "Netrakona",
    "Rangpur": "Rangpur", "Jamalpur": "Jamalpur",
    "Jhalakathi": "Jhalokati", "Jhalokati": "Jhalokati",
    "Chapai Nawa": "Chapainawabganj",
    "Chapainaw" : "Chapainawabganj",
    "Chapainawabg":"Chapainawabganj",
    "Sherpur ": "Sherpur",
}
gdf["district"] = gdf["district"].replace(DISTRICT_FIX).str.strip()
gdf["division"] = gdf["division"].replace({"Rajshahi": "Rajshahi"}).str.title()
# Simplify for smaller polygons (tolerance in degrees)
gdf["geom_simp"] = gdf.geometry.simplify(tolerance=0.01, preserve_topology=True)

# Build simplified GeoJSON features; aggregate by district (dissolve polygons
# belonging to same district in case shapefile has multiple parts).
district_geo = {}
for dist, sub in gdf.groupby("district"):
    geom = unary_union(sub["geom_simp"].values)
    # Round coords to 4dp for bandwidth
    def _round(obj):
        if isinstance(obj, list):
            if obj and all(isinstance(x, (int, float)) for x in obj):
                return [round(x, 4) for x in obj]
            return [_round(x) for x in obj]
        return obj
    gj = mapping(geom)
    gj["coordinates"] = _round(gj["coordinates"])
    division = sub["division"].iloc[0]
    district_geo[dist] = {
        "division": division,
        "geometry": gj,
        "centroid": [round(geom.centroid.x, 4), round(geom.centroid.y, 4)],
    }

# Aggregate division polygons
div_geo = {}
for div, sub in gdf.groupby("division"):
    geom = unary_union(sub["geom_simp"].values).simplify(0.03, preserve_topology=True)
    gj = mapping(geom)
    def _round(obj):
        if isinstance(obj, list):
            if obj and all(isinstance(x, (int, float)) for x in obj):
                return [round(x, 3) for x in obj]
            return [_round(x) for x in obj]
        return obj
    gj["coordinates"] = _round(gj["coordinates"])
    div_geo[div] = {"geometry": gj, "centroid": [round(geom.centroid.x, 3), round(geom.centroid.y, 3)]}

print(f"    {len(district_geo)} district polygons, {len(div_geo)} divisions")
print(f"    sample districts: {list(district_geo)[:10]}")

# ---------------------------------------------------------------------------
# 2) WAVE-SPECIFIC HH MASTER FRAMES (hhid -> district, weight, sample_type)
# ---------------------------------------------------------------------------
print("\n[2/7] Building HH master frames per wave")

def _title(s):
    if pd.isna(s): return None
    return str(s).strip().title()

# -- 2011 --
df_a11, _ = read_dta("BIHS 2011-2012/001_mod_a_male.dta")
df_w11, _ = read_dta("BIHS 2011-2012/BIHS_FTF baseline sampling weights.dta")
# Key: a_id (household). Check columns
print("    2011 A_male cols:", [c for c in df_a11.columns if c.lower() in ("a_id","hhid","hh_id","district_name","upazila_name","div_name","div","dcode","district")])
# HHID variable in 2011: must locate – scan
hhid_col_11 = "a01" if "a01" in df_a11.columns else df_a11.columns[0]
print(f"    2011 hhid col guessed: {hhid_col_11}")

df_a11["district"] = df_a11["District_Name"].map(_title)
df_a11["division"] = df_a11["div_name"].map(_title) if "div_name" in df_a11.columns else None
hh11 = df_a11[[hhid_col_11, "district", "division"]].rename(columns={hhid_col_11: "hhid"}).dropna(subset=["district"])
# Weights on same file: 6503 rows match A. merge by position? weights file has dvcode but no hhid shown. Try columns of weights:
print("    2011 weights cols:", df_w11.columns.tolist())
w_hhid_col = next((c for c in df_w11.columns if re.match(r"(a_id|hhid|hh_id|id01)$", c, re.I)), None)
if w_hhid_col:
    hh11 = hh11.merge(df_w11[[w_hhid_col, "hhweight", "popweight", "sample_type"]].rename(columns={w_hhid_col: "hhid"}), on="hhid", how="left")
else:
    # If same length 6503 align by position
    if len(df_a11) == len(df_w11):
        hh11["hhweight"] = df_w11["hhweight"].values
        hh11["popweight"] = df_w11["popweight"].values
        hh11["sample_type"] = df_w11["sample_type"].values
hh11["wave"] = "2011"
hh11 = hh11.drop_duplicates("hhid")
print(f"    2011 HH master: {len(hh11)} rows")

# -- 2015 --
df_a15, _ = read_dta("BIHS 2015-2016/001_r2_mod_a_male.dta")
df_w15, _ = read_dta("BIHS 2015-2016/BIHS FTF 2015 survey sampling weights.dta")
hhid_col_15 = "a01" if "a01" in df_a15.columns else df_a15.columns[0]
print(f"    2015 hhid col guessed: {hhid_col_15}")
df_a15["district"] = df_a15["District_Name"].map(_title) if "District_Name" in df_a15.columns else None
df_a15["division"] = df_a15["div_name"].map(_title) if "div_name" in df_a15.columns else None
hh15 = df_a15[[hhid_col_15, "district", "division"]].rename(columns={hhid_col_15: "hhid"}).dropna(subset=["district"])
w_hhid_15 = "a01" if "a01" in df_w15.columns else None
if w_hhid_15:
    hh15 = hh15.merge(df_w15[[w_hhid_15, "hhweight", "popweight"]].rename(columns={w_hhid_15: "hhid"}), on="hhid", how="left")
else:
    if len(df_a15) == len(df_w15):
        hh15["hhweight"] = df_w15["hhweight"].values
        hh15["popweight"] = df_w15["popweight"].values
hh15["sample_type"] = None
hh15["wave"] = "2015"
hh15 = hh15.drop_duplicates("hhid")
print(f"    2015 HH master: {len(hh15)} rows")

# -- 2019 --
# 2019 uses `hhid2` (string) as the primary HH id across modules, and `a01` (float w/
# optional decimal split) for panel lineage.  District is stored as a NUMERIC code
# without value labels; division is stored as a STRING (`div_name`) and usable.
# Strategy:
#   - Use base-integer of a01 to cross-walk to 2015 `District_Name` (100% overlap: all
#     5,503 integer a01s in 2019 are present in 2015, inheriting labelled district).
#   - Merge weights on float `a01` (weights file has matching a01 for all 5,605 HHs).
#   - Carry hhid2 as the master `hhid` key since all 2019 modules key on hhid2.
df_a19, _ = read_dta("BIHS 2018-2019/BIHSRound3/Male/009_bihs_r3_male_mod_a.dta")
df_w19, _ = read_dta("BIHS 2018-2019/158_BIHS sampling weights_r3.dta")
# Build 2015 a01-int -> district name map (once)
_a15_map = df_a15.copy()
_a15_map["a01_int"] = np.floor(pd.to_numeric(_a15_map["a01"], errors="coerce")).astype("Int64")
_a15_map["district_name_15"] = _a15_map["District_Name"].map(_title)
_a15_lookup = (_a15_map.dropna(subset=["a01_int","district_name_15"])
                       .drop_duplicates("a01_int")
                       .set_index("a01_int")["district_name_15"])

df_a19["a01_int"] = np.floor(pd.to_numeric(df_a19["a01"], errors="coerce")).astype("Int64")
df_a19["district"] = df_a19["a01_int"].map(_a15_lookup)
df_a19["division"] = df_a19["div_name"].map(_title) if "div_name" in df_a19.columns else None
hh19 = (df_a19[["hhid2", "a01", "district", "division"]]
        .rename(columns={"hhid2": "hhid"})
        .dropna(subset=["district"]))
# Weights file keys on float a01
hh19 = hh19.merge(df_w19[["a01","hhweight","popweight"]], on="a01", how="left")
hh19["sample_type"] = None
hh19["wave"] = "2019"
hh19 = hh19.drop_duplicates("hhid")
print(f"    2019 HH master: {len(hh19)} rows, districts non-null: {hh19['district'].notna().sum()}, weight non-null: {hh19['hhweight'].notna().sum()}")

# -- 2024 --
df_a24, meta_a24 = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_a1.dta")
# Use districtname if populated, else map a1district via value labels
if "districtname" in df_a24.columns:
    df_a24["district"] = df_a24["districtname"].map(_title)
else:
    vl_d24 = meta_a24.variable_value_labels.get("a1district", {})
    df_a24["district"] = df_a24["a1district"].map(lambda c: _title(vl_d24.get(int(c)) if pd.notna(c) else None))
if "divisionname" in df_a24.columns:
    df_a24["division"] = df_a24["divisionname"].map(_title)
else:
    vl_div = meta_a24.variable_value_labels.get("a1division", {})
    df_a24["division"] = df_a24["a1division"].map(lambda c: _title(vl_div.get(int(c)) if pd.notna(c) else None))
wcol = "hhweight_24" if "hhweight_24" in df_a24.columns else (
       "hhweight_18" if "hhweight_18" in df_a24.columns else None)
hh24 = df_a24[["a1hhid_combined", "district", "division", wcol]].rename(
    columns={"a1hhid_combined":"hhid", wcol:"hhweight"}
).dropna(subset=["district"])
hh24["popweight"] = hh24["hhweight"]
hh24["sample_type"] = None
hh24["wave"] = "2024"
hh24 = hh24.drop_duplicates("hhid")
print(f"    2024 HH master: {len(hh24)} rows")

# Fill missing weights with 1 (so counts still make sense - but we note it)
for H in (hh11, hh15, hh19, hh24):
    H["hhweight"] = pd.to_numeric(H["hhweight"], errors="coerce").fillna(1.0)
    H["popweight"] = pd.to_numeric(H["popweight"], errors="coerce").fillna(H["hhweight"])

HH_MASTERS = {"2011": hh11, "2015": hh15, "2019": hh19, "2024": hh24}

# ---------------------------------------------------------------------------
# 3) RICE - collect per-HH dummy for each variety family
# ---------------------------------------------------------------------------
print("\n[3/7] Rice variety prevalence per HH per wave")

def hh_rice_families(wave, h1_df, variety_col, classify_fn, hhid_field):
    """Return DataFrame with one row per HH having indicator columns for each family."""
    h1_df = h1_df[[hhid_field, variety_col]].dropna()
    h1_df["fam"] = h1_df[variety_col].map(classify_fn)
    h1_df = h1_df.dropna(subset=["fam"])
    # Pivot: HH x family presence
    piv = (h1_df
           .assign(v=1)
           .pivot_table(index=hhid_field, columns="fam", values="v", aggfunc="max", fill_value=0)
           .reset_index()
           .rename(columns={hhid_field: "hhid"}))
    # Also "any rice grower" indicator for denominator questions
    piv["RICE_GROWER"] = 1
    return piv

# 2011 H1
df11_h1, _ = read_dta("BIHS 2011-2012/011_mod_h1_male.dta")
print(f"    2011 H1 rows: {len(df11_h1)}")
hhid_h1_11 = "a01" if "a01" in df11_h1.columns else df11_h1.columns[0]
print(f"    2011 H1 hhid: {hhid_h1_11}")
rice11 = hh_rice_families("2011", df11_h1, "h1_01", classify_variety_2011, hhid_h1_11)

# 2015 H1
df15_h1, _ = read_dta("BIHS 2015-2016/015_r2_mod_h1_male.dta")
print(f"    2015 H1 rows: {len(df15_h1)}")
hhid_h1_15 = "a01" if "a01" in df15_h1.columns else df15_h1.columns[0]
print(f"    2015 H1 hhid: {hhid_h1_15}")
rice15 = hh_rice_families("2015", df15_h1, "h1_01", classify_variety_2015_2019, hhid_h1_15)

# 2019 H1
df19_h1, _ = read_dta("BIHS 2018-2019/BIHSRound3/Male/021_bihs_r3_male_mod_h1.dta")
print(f"    2019 H1 rows: {len(df19_h1)}")
rice19 = hh_rice_families("2019", df19_h1, "h1_01", classify_variety_2015_2019, "hhid2")

# 2024 c2paddy_mainvariety AND b6seedbed_paddy1..4
df24_c2, _ = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_c2_4.dta")
df24_b6, _ = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_b6.dta")
print(f"    2024 c2 rows: {len(df24_c2)}; b6 rows: {len(df24_b6)}")
rows = []
for _, r in df24_c2.iterrows():
    for col in ("c2paddy_mainvariety", "c2paddy_intercropvariety"):
        v = r.get(col)
        if pd.notna(v) and int(v) > 0:
            rows.append((r["a1hhid_combined"], int(v)))
for _, r in df24_b6.iterrows():
    for col in ("b6seedbed_paddy1", "b6seedbed_paddy2", "b6seedbed_paddy3", "b6seedbed_paddy4"):
        v = r.get(col)
        if pd.notna(v) and int(v) > 0:
            rows.append((r["a1hhid_combined"], int(v)))
df24_rice = pd.DataFrame(rows, columns=["a1hhid_combined", "variety_code"])
rice24 = hh_rice_families("2024", df24_rice, "variety_code", classify_variety_2024, "a1hhid_combined")
print(f"    2024 rice HH w/any classified variety: {len(rice24)}")

RICE_FAMS = ["BRRI_CORE28_29", "BRRI_OLDER_HYV", "BRRI_NEW_POST2012",
             "BRRI_STRESS", "BINA", "HYBRID", "LOCAL"]
RICE_FRAMES = {"2011": rice11, "2015": rice15, "2019": rice19, "2024": rice24}

# ---------------------------------------------------------------------------
# 4) AQUACULTURE - pond, tilapia, carp polyculture, prawn/shrimp
# ---------------------------------------------------------------------------
print("\n[4/7] Aquaculture prevalence per HH per wave")

def aqua_indicators_from_l1(df, hhid_field):
    """Given module L1 (pond-level rows), return one row per HH with indicators.

    CRITICAL: L1 rosters in BIHS include placeholder rows for HHs with no pond
    (indicated by `l1_sl == 99` "without cultivation" and `l1_01` = NaN/0 area).
    Only rows with an actual pond area > 0 represent real aquaculture.
    """
    fish_cols = [c for c in df.columns if re.match(r"l1_02(_\d+)?$", c)]
    keep = [hhid_field] + fish_cols + [c for c in ("l1_01","l1_sl") if c in df.columns]
    df = df[keep].copy()
    area = pd.to_numeric(df.get("l1_01", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    sl   = pd.to_numeric(df.get("l1_sl", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    mask = (area > 0) & (sl != 99)
    df = df.loc[mask].copy()
    df["ANY_POND"] = 1
    df["TILAPIA"] = df[fish_cols].isin([TILAPIA_CODE]).any(axis=1).astype(int)
    df["CARP_ANY"] = df[fish_cols].isin(CARP_CODES).any(axis=1).astype(int)
    df["POLY_CARP_2PLUS"] = (df[fish_cols].isin(CARP_CODES).sum(axis=1) >= 2).astype(int)
    df["MOLA"] = df[fish_cols].isin([MOLA_CODE]).any(axis=1).astype(int)
    df["PRAWN_GALDA"] = df[fish_cols].isin([PRAWN_CODE]).any(axis=1).astype(int)
    df["SHRIMP_BAGDA"] = df[fish_cols].isin([SHRIMP_CODE]).any(axis=1).astype(int)
    # HH level max (any pond having species)
    g = (df.groupby(hhid_field)[["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS",
                                 "MOLA","PRAWN_GALDA","SHRIMP_BAGDA"]].max()
           .reset_index().rename(columns={hhid_field:"hhid"}))
    return g

# 2011
df11_l1, _ = read_dta("BIHS 2011-2012/026_mod_l1_male.dta")
hhid_l1_11 = "a01" if "a01" in df11_l1.columns else df11_l1.columns[0]
aqua11 = aqua_indicators_from_l1(df11_l1, hhid_l1_11)
print(f"    2011 L1: {len(df11_l1)} rows -> {len(aqua11)} HH with pond; tilapia {aqua11['TILAPIA'].sum()}")

# 2015
df15_l1, _ = read_dta("BIHS 2015-2016/037_r2_mod_l1_male.dta")
hhid_l1_15 = "a01" if "a01" in df15_l1.columns else df15_l1.columns[0]
aqua15 = aqua_indicators_from_l1(df15_l1, hhid_l1_15)
print(f"    2015 L1: {len(df15_l1)} rows -> {len(aqua15)} HH with pond; tilapia {aqua15['TILAPIA'].sum()}")

# 2019
df19_l1, _ = read_dta("BIHS 2018-2019/BIHSRound3/Male/051_bihs_r3_male_mod_l1.dta")
aqua19 = aqua_indicators_from_l1(df19_l1, "hhid2")
print(f"    2019 L1: {len(df19_l1)} rows -> {len(aqua19)} HH with pond; tilapia {aqua19['TILAPIA'].sum()}")

# 2024 (module E5 has pond info and e5fish_species1..8)
df24_e5, _ = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_e5.dta")
fish_cols_24 = [c for c in df24_e5.columns if re.match(r"e5fish_species\d+$", c)]
df24_e5 = df24_e5[["a1hhid_combined"] + fish_cols_24 + [c for c in ("e5tilapia_clean","e5carp_small_fish") if c in df24_e5.columns]].copy()
df24_e5["ANY_POND"] = 1
df24_e5["TILAPIA"] = df24_e5[fish_cols_24].isin([TILAPIA_CODE]).any(axis=1).astype(int)
df24_e5["CARP_ANY"] = df24_e5[fish_cols_24].isin(CARP_CODES).any(axis=1).astype(int)
df24_e5["POLY_CARP_2PLUS"] = (df24_e5[fish_cols_24].isin(CARP_CODES).sum(axis=1) >= 2).astype(int)
df24_e5["MOLA"] = df24_e5[fish_cols_24].isin([MOLA_CODE]).any(axis=1).astype(int)
df24_e5["PRAWN_GALDA"] = df24_e5[fish_cols_24].isin([PRAWN_CODE]).any(axis=1).astype(int)
df24_e5["SHRIMP_BAGDA"] = df24_e5[fish_cols_24].isin([SHRIMP_CODE]).any(axis=1).astype(int)
aqua24 = (df24_e5.groupby("a1hhid_combined")[["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS",
                                              "MOLA","PRAWN_GALDA","SHRIMP_BAGDA"]].max()
                 .reset_index().rename(columns={"a1hhid_combined":"hhid"}))
# Also enrich with e10 aquaculture practices (supp_feed, hormone, disease control)
df24_e10, _ = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_e10.dta")
agg_e10 = (df24_e10.assign(
    SUPP_FEED = (df24_e10["e10supp_feed"]==1).astype(int) if "e10supp_feed" in df24_e10.columns else 0,
    HORMONE   = (df24_e10["e10use_hormone"]==1).astype(int) if "e10use_hormone" in df24_e10.columns else 0,
    DISEASE_CTL = (df24_e10["e10disease_control"]==1).astype(int) if "e10disease_control" in df24_e10.columns else 0,
)[["a1hhid_combined","SUPP_FEED","HORMONE","DISEASE_CTL"]]
  .groupby("a1hhid_combined").max().reset_index().rename(columns={"a1hhid_combined":"hhid"}))
aqua24 = aqua24.merge(agg_e10, on="hhid", how="left").fillna(0)
print(f"    2024 E5 pond HH: {len(aqua24)}; tilapia {int(aqua24['TILAPIA'].sum())}; supp_feed {int(aqua24['SUPP_FEED'].sum())}")

AQUA_FRAMES = {"2011": aqua11, "2015": aqua15, "2019": aqua19, "2024": aqua24}
AQUA_INDS = ["ANY_POND","TILAPIA","CARP_ANY","POLY_CARP_2PLUS","MOLA","PRAWN_GALDA","SHRIMP_BAGDA"]

# ---------------------------------------------------------------------------
# 5) MECHANIZATION (tractor, power tiller, thresher, reaper, combined harvester,
#    LLP pump, sprayer, motorized thresher use)
# ---------------------------------------------------------------------------
print("\n[5/7] Mechanization ownership per HH per wave")

def _flag(series, val=1):
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int).eq(val).astype(int)

# --- 2024: module a5_6 has named binary ownership a5_agri_equipment_{1..23}
df24_a56, _ = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_a5_6.dta")
def own(col):
    return _flag(df24_a56[col]) if col in df24_a56.columns else 0
mech24 = pd.DataFrame({
    "hhid":             df24_a56["a1hhid_combined"],
    "TRACTOR":          own("a5_agri_equipment_1"),
    "POWER_TILLER":     own("a5_agri_equipment_2"),
    "POWER_THRESHER":   own("a5_agri_equipment_4"),
    "PADDLE_THRESHER":  own("a5_agri_equipment_5"),
    "TREADLE_PUMP":     own("a5_agri_equipment_7"),
    "ROWER_PUMP":       own("a5_agri_equipment_8"),
    "AXIAL_FLOW_PUMP":  own("a5_agri_equipment_9"),
    "LLP_IRRIG":        own("a5_agri_equipment_10"),
    "ELEC_MOTOR_PUMP":  own("a5_agri_equipment_13"),
    "DIESEL_MOTOR_PUMP":own("a5_agri_equipment_14"),
    "SPRAYER":          own("a5_agri_equipment_15"),
    "REAPER":           own("a5_agri_equipment_16"),
    "SEEDER_DRILL":     own("a5_agri_equipment_17"),
    "COMBINED_HARVEST": own("a5_agri_equipment_19"),
    "FISHING_NET":      own("a5_agri_equipment_22"),
}).groupby("hhid").max().reset_index()

# Module d2: motorized harvest & thresh USE (not ownership but actual use)
df24_d2, _ = read_dta("SPIA 2024 round/Data/Final/SPIA_BIHS_2024_module_d2.dta")
use24 = df24_d2.assign(
    USE_MOTOR_HARVEST = _flag(df24_d2.get("d2paddy_harvest_2", pd.Series(0, index=df24_d2.index))),
    USE_MOTOR_THRESH  = _flag(df24_d2.get("d2paddy_thresh_5", pd.Series(0, index=df24_d2.index))),
    USE_TREADLE_THRESH= _flag(df24_d2.get("d2paddy_thresh_4", pd.Series(0, index=df24_d2.index))),
).groupby("a1hhid_combined")[["USE_MOTOR_HARVEST","USE_MOTOR_THRESH","USE_TREADLE_THRESH"]].max().reset_index().rename(columns={"a1hhid_combined":"hhid"})
mech24 = mech24.merge(use24, on="hhid", how="left").fillna(0)

# --- Prior waves: use harmonized HH file asset_* flags for tractor/tiller/thresher/pump
df_harm, _ = read_dta("BIHS Harmonized Dataset/BIHS_household_2011_15.dta")
# HHID and year
hh_id_harm = "a01" if "a01" in df_harm.columns else next((c for c in df_harm.columns if re.match(r"^(hhid|hh_id)$", c, re.I)), None)
year_col = next((c for c in df_harm.columns if c.lower() in ("year","survey_year","wave")), None)
print(f"    harmonized cols include hhid: {hh_id_harm}  year: {year_col}")
asset_cols = [c for c in df_harm.columns if c.lower().startswith("asset_")]
print(f"    harmonized asset_* columns: {asset_cols}")

# If year column exists, split 2011 vs 2015
def mech_prior_from_harm(year_value):
    if year_col:
        sub = df_harm[pd.to_numeric(df_harm[year_col], errors="coerce") == year_value].copy()
    else:
        sub = df_harm.copy()
    m = pd.DataFrame({"hhid": sub[hh_id_harm] if hh_id_harm else range(len(sub))})
    for a in asset_cols:
        m[a.upper()] = _flag(sub[a])
    # Map harmonised flags to our standard names (rename knowns)
    rename = {}
    for a in asset_cols:
        au = a.upper()
        if "TRACTOR" in au:   rename[au] = "TRACTOR"
        elif "POWER_TILL" in au or "TILLER" in au: rename[au] = "POWER_TILLER"
        elif "THRESHER" in au:rename[au] = "POWER_THRESHER"
        elif "PUMP" in au and "DIESEL" in au: rename[au] = "DIESEL_MOTOR_PUMP"
        elif "PUMP" in au and "ELECTRIC" in au: rename[au] = "ELEC_MOTOR_PUMP"
        elif "PUMP" in au and ("SHALLOW" in au or "LLP" in au or "MOTOR" in au): rename[au] = "LLP_IRRIG"
        elif "PUMP" in au and "TREADLE" in au: rename[au] = "TREADLE_PUMP"
        elif "SPRAYER" in au: rename[au] = "SPRAYER"
        elif "REAPER" in au:  rename[au] = "REAPER"
        elif "SEEDER" in au or "DRILL" in au: rename[au] = "SEEDER_DRILL"
        elif "HARVEST" in au: rename[au] = "COMBINED_HARVEST"
    m = m.rename(columns=rename)
    return m

mech11 = mech_prior_from_harm(2011) if year_col else None
mech15 = mech_prior_from_harm(2015) if year_col else None

# For 2019 we have module D2 (durable-asset roster) with `d2_02` = asset code
# (labelled 1..40: tractor=12, power tiller=13, thresher=15, LLP pump=22,
# electric motor pump=25, diesel motor pump=26, sprayer=27, reaper=28, jumbo
# (axial-flow) pump=36, seeder drill=37, combined harvester=39, rice transplanter=40).
# A household is flagged as owning an asset if it has AT LEAST ONE row with the
# matching `d2_02` code AND a positive quantity `d2_03` (stock at survey).
df19_d2, _ = read_dta("BIHS 2018-2019/BIHSRound3/Male/016_bihs_r3_male_mod_d2.dta")
_code_map_19 = {
    "TRACTOR":         12,
    "POWER_TILLER":    13,
    "POWER_THRESHER":  15,
    "LLP_IRRIG":       22,
    "ELEC_MOTOR_PUMP": 25,
    "DIESEL_MOTOR_PUMP":26,
    "SPRAYER":         27,
    "REAPER":          28,
    "AXIAL_FLOW_PUMP": 36,
    "SEEDER_DRILL":    37,
    "COMBINED_HARVEST":39,
    "TRANSPLANTER":    40,
    "TREADLE_PUMP":    20,
    "ROWER_PUMP":      21,
}
_qty_col = "d2_03" if "d2_03" in df19_d2.columns else None
if _qty_col:
    _has = df19_d2[(pd.to_numeric(df19_d2[_qty_col], errors="coerce") > 0)]
else:
    _has = df19_d2
mech19 = df19_d2[["a01"]].drop_duplicates().copy()
for name, code in _code_map_19.items():
    by = _has[_has["d2_02"] == code].groupby("a01").size().rename(name)
    mech19 = mech19.merge(by, on="a01", how="left")
mech19 = mech19.fillna(0)
for c in mech19.columns:
    if c == "a01": continue
    mech19[c] = (mech19[c] > 0).astype(int)
# hhid key for 2019 is `hhid2`; cross-walk via df_a19 (A module)
_a19_idmap = df_a19[["a01","hhid2"]].dropna().drop_duplicates("a01")
mech19 = mech19.merge(_a19_idmap, on="a01", how="left").rename(columns={"hhid2":"hhid"})
mech19 = mech19.drop(columns=["a01"]).dropna(subset=["hhid"])
print(f"    2019 mech HH rows: {len(mech19)}  tractor {int(mech19['TRACTOR'].sum())}  tiller {int(mech19['POWER_TILLER'].sum())}  sprayer {int(mech19['SPRAYER'].sum())}")

MECH_FRAMES = {"2011": mech11, "2015": mech15, "2019": mech19, "2024": mech24}

MECH_INDS = ["TRACTOR","POWER_TILLER","POWER_THRESHER","REAPER","COMBINED_HARVEST",
             "LLP_IRRIG","DIESEL_MOTOR_PUMP","ELEC_MOTOR_PUMP","SPRAYER",
             "USE_MOTOR_HARVEST","USE_MOTOR_THRESH"]

# ---------------------------------------------------------------------------
# 6) AGGREGATE TO DISTRICT x WAVE (weighted prevalence)
# ---------------------------------------------------------------------------
print("\n[6/7] Aggregating to district x wave")

def weighted_prev(master_hh, ind_frame, ind_cols):
    """Return dict[district] -> {ind: weighted prevalence in %}."""
    if ind_frame is None or len(ind_frame) == 0:
        return {}
    merged = master_hh.merge(ind_frame, on="hhid", how="left")
    for c in ind_cols:
        if c not in merged.columns:
            merged[c] = 0
        merged[c] = pd.to_numeric(merged[c], errors="coerce").fillna(0)
    out = {}
    for dist, sub in merged.groupby("district"):
        w = sub["hhweight"].values
        wsum = w.sum()
        if wsum <= 0: continue
        rec = {"n_hh": int(len(sub)), "weight_sum": float(wsum)}
        for c in ind_cols:
            rec[c] = round(100.0 * float((sub[c].values * w).sum() / wsum), 2)
        out[dist] = rec
    # National
    nat = {"n_hh": int(len(merged)), "weight_sum": float(merged["hhweight"].sum())}
    for c in ind_cols:
        nat[c] = round(100.0 * float((merged[c].values * merged["hhweight"].values).sum() /
                                     max(merged["hhweight"].sum(), 1)), 2)
    out["__NATIONAL__"] = nat
    return out

# RICE district-wave
rice_dist = {}
for wave, master in HH_MASTERS.items():
    rf = RICE_FRAMES[wave]
    rice_dist[wave] = weighted_prev(master, rf, RICE_FAMS + ["RICE_GROWER"])
    print(f"    rice {wave}: {len(rice_dist[wave])-1} districts")

# AQUA
aqua_dist = {}
for wave, master in HH_MASTERS.items():
    af = AQUA_FRAMES[wave]
    aqua_dist[wave] = weighted_prev(master, af, AQUA_INDS +
        (["SUPP_FEED","HORMONE","DISEASE_CTL"] if wave == "2024" else []))
    print(f"    aqua {wave}: {len(aqua_dist[wave])-1} districts")

# MECH
mech_dist = {}
for wave, master in HH_MASTERS.items():
    mf = MECH_FRAMES.get(wave)
    if mf is None:
        mech_dist[wave] = {}
        continue
    existing = [c for c in (MECH_INDS) if c in mf.columns]
    mech_dist[wave] = weighted_prev(master, mf, existing)
    print(f"    mech {wave}: {len(mech_dist[wave])-1} districts  ({len(existing)} indicators)")

# ---------------------------------------------------------------------------
# 7) DNA fingerprint summary (370 real samples, 2024)
# ---------------------------------------------------------------------------
print("\n[7/7] DNA fingerprint 2024 summary")
dna_csv = r"C:\Users\kd475\RES\BGD_MIX\BIHS data, shape files and SPIA 2024 wave\SPIA 2024 round\Data\DNA fingerprinting\ref_clusters_no_hybrids_with_HH_Ids.csv"
dna = pd.read_csv(dna_csv)
# The file column 'HH Id' actually holds the variety name (not an HH id) - rename for clarity
dna = dna.rename(columns={"HH Id": "Variety_name"})
by_variety = dna["Variety_name"].value_counts().to_dict()
by_cluster = dna.groupby("Group").agg(
    n_samples=("Barcode Id","count"),
    n_varieties=("Variety_name","nunique"),
    top_variety=("Variety_name", lambda s: s.value_counts().idxmax()),
).reset_index().rename(columns={"Group":"cluster_id"})
by_cluster = by_cluster.to_dict("records")
print(f"    DNA samples: {len(dna)}  varieties: {dna['Variety_name'].nunique()}  clusters: {dna['Group'].nunique()}")

# ---------------------------------------------------------------------------
# DUMP OUTPUTS
# ---------------------------------------------------------------------------
print("\n### Writing outputs")
dump({
    "districts": district_geo,
    "divisions": div_geo,
    "source":    "polbnda_bgd.shp (Earthwork Stanford)",
}, "mixtape_geo.json")

dump({
    "source_files": {
        "2011": "011_mod_h1_male.dta",
        "2015": "015_r2_mod_h1_male.dta",
        "2019": "021_bihs_r3_male_mod_h1.dta",
        "2024": "SPIA_BIHS_2024_module_c2_4.dta + module_b6.dta",
    },
    "variety_families": RICE_FAMS,
    "by_wave": rice_dist,
}, "mixtape_rice.json")

dump({
    "source_files": {
        "2011": "026_mod_l1_male.dta",
        "2015": "037_r2_mod_l1_male.dta",
        "2019": "051_bihs_r3_male_mod_l1.dta",
        "2024": "SPIA_BIHS_2024_module_e5.dta + module_e10.dta",
    },
    "indicators": AQUA_INDS + ["SUPP_FEED","HORMONE","DISEASE_CTL"],
    "by_wave": aqua_dist,
}, "mixtape_aqua.json")

dump({
    "source_files": {
        "2011": "BIHS_household_2011_15.dta (asset_*)",
        "2015": "BIHS_household_2011_15.dta (asset_*)",
        "2019": "unavailable - harmonised file ends 2015",
        "2024": "SPIA_BIHS_2024_module_a5_6.dta + module_d2.dta",
    },
    "indicators": MECH_INDS,
    "by_wave": mech_dist,
}, "mixtape_mech.json")

dump({
    "source": "ref_clusters_no_hybrids_with_HH_Ids.csv (n=370 samples)",
    "n_samples": int(len(dna)),
    "n_varieties": int(dna["Variety_name"].nunique()),
    "n_clusters": int(dna["Group"].nunique()),
    "by_variety": by_variety,
    "by_cluster": by_cluster,
}, "mixtape_dna.json")

# Build national time series per technology for easy chart use
national_ts = {"years": ["2011","2015","2019","2024"], "rice": {}, "aqua": {}, "mech": {}}
for fam in RICE_FAMS + ["RICE_GROWER"]:
    national_ts["rice"][fam] = [
        rice_dist[w].get("__NATIONAL__", {}).get(fam, None) for w in ["2011","2015","2019","2024"]
    ]
for ind in AQUA_INDS:
    national_ts["aqua"][ind] = [
        aqua_dist[w].get("__NATIONAL__", {}).get(ind, None) for w in ["2011","2015","2019","2024"]
    ]
for ind in MECH_INDS:
    national_ts["mech"][ind] = [
        (mech_dist[w].get("__NATIONAL__", {}) or {}).get(ind, None) for w in ["2011","2015","2019","2024"]
    ]
dump(national_ts, "mixtape_national.json")

dump({
    "rounds": {
        "2011": {"n_hh": int(len(hh11)), "module_a": "001_mod_a_male.dta"},
        "2015": {"n_hh": int(len(hh15)), "module_a": "001_r2_mod_a_male.dta"},
        "2019": {"n_hh": int(len(hh19)), "module_a": "009_bihs_r3_male_mod_a.dta"},
        "2024": {"n_hh": int(len(hh24)), "module_a": "SPIA_BIHS_2024_module_a1.dta"},
    },
    "shapefile": "polbnda_bgd.shp",
}, "mixtape_summary.json")

print("\nDone.")
print("\nNational prevalence sanity check (%):")
for cat in ("rice","aqua","mech"):
    print(f"\n  {cat.upper()}:")
    for k, v in national_ts[cat].items():
        print(f"    {k:22s}  {v}")
