"""Replicate the SPIA Bangladesh Study 2025 reach figures in Python.

This is a direct port of the relevant parts of the study's Stata code
(`Code/Analysis/analysis.do` in the replication package). It reproduces the
report's own denominators rather than imposing a single frame of our own,
which is what makes the dashboard a replication instead of a parallel
calculation.

The important structural facts carried over from the Stata:

*   The agricultural frame is "grew a crop OR operated a pond". In 2024 that
    is `agri_control_household = (b1repeat_count > 0) | (b1fishing_count > 0)`
    built in `data_structure.do`; in earlier rounds it is
    `(h1_sl != 99) | fishing_hh` built in `analysis.do`.
*   The 2011/12 and 2015 rounds **drop the Feed the Future booster sample**
    (`Sample_type == 1` and `hh_type == 1` respectively). Keeping it inflates
    the panel from roughly 5,500 to roughly 6,700 households per round.
*   Every mean is weighted with that round's household sampling weight, and
    the weight merge is an inner join, matching Stata's `keep(3)`.

Run it directly to print a verification table against the published figures:

    python spia_replication.py
"""
import os
import numpy as np
import pandas as pd
import pyreadstat

# The replication package. Override with the SPIA_REPO environment variable.
REPO = os.environ.get(
    "SPIA_REPO",
    r"C:/Users/kd475/RES/BGD_MIX/hilsa_feasibility/external/SPIA-Bangladesh-Study-2025",
)
FINAL = os.path.join(REPO, "Data", "Final")
PRIOR = os.path.join(REPO, "Data", "Prior Waves")
DNA = os.path.join(REPO, "Data", "DNA fingerprinting")
R18 = os.path.join(PRIOR, "Third Round (2018-2019)")
R15 = os.path.join(PRIOR, "Second Round (2015-2016)")
R12 = os.path.join(PRIOR, "First Round (2011-2012)")

ROUNDS = ["2011", "2015", "2019", "2024"]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def dta(path, cols=None):
    """Read a Stata file, tolerating a requested column that is absent."""
    if cols is not None:
        _, meta = pyreadstat.read_dta(path, metadataonly=True)
        cols = [c for c in cols if c in meta.column_names]
    df, _ = pyreadstat.read_dta(path, usecols=cols)
    return df


def wmean(df, col, wcol):
    d = df[[col, wcol]].dropna()
    if d.empty or d[wcol].sum() <= 0:
        return np.nan
    return float(np.average(d[col], weights=d[wcol]))


def wshare(df, col, wcol):
    """Weighted mean expressed as a percentage."""
    v = wmean(df, col, wcol)
    return np.nan if np.isnan(v) else 100.0 * v


# --------------------------------------------------------------------------
# The agricultural frame, one round at a time.
# Each returns a household-level frame: hhid, weight, agri_hh, pond.
# --------------------------------------------------------------------------
def frame_2024():
    b15 = dta(os.path.join(FINAL, "SPIA_BIHS_2024_module_b1_5.dta"),
              ["a1hhid_combined", "agri_control_household"])
    base = b15.groupby("a1hhid_combined", as_index=False).first()

    e5 = dta(os.path.join(FINAL, "SPIA_BIHS_2024_module_e5.dta"),
             ["a1hhid_combined", "b1plot_fishing"])
    pond = (e5.groupby("a1hhid_combined", as_index=False)["b1plot_fishing"]
              .max().rename(columns={"b1plot_fishing": "pond"}))

    a1 = dta(os.path.join(FINAL, "SPIA_BIHS_2024_module_a1.dta"),
             ["a1hhid_combined", "hhweight_24"])

    df = (base.merge(pond, on="a1hhid_combined", how="outer")
               .merge(a1, on="a1hhid_combined", how="left")
               .rename(columns={"a1hhid_combined": "hhid", "hhweight_24": "weight",
                                "agri_control_household": "agri_hh"}))
    df.loc[df["pond"].isna() & (df["agri_hh"] == 1), "pond"] = 0
    return df[df["agri_hh"] == 1].reset_index(drop=True)


def frame_2019():
    h1 = dta(os.path.join(R18, "021_bihs_r3_male_mod_h1.dta"), ["a01", "h1_sl"])
    h1["agri_control"] = np.where(h1["h1_sl"] == 99, 0, 1)
    agri = h1.groupby("a01", as_index=False)["agri_control"].max()

    l1 = dta(os.path.join(R18, "051_bihs_r3_male_mod_l1.dta"), ["a01", "sl_l1", "pondid_l1"])
    l1 = l1[~((l1["sl_l1"] == 0) | (l1["pondid_l1"] == 999))]
    l1["pond"] = 1
    pond = l1.groupby("a01", as_index=False)["pond"].max()

    df = agri.merge(pond, on="a01", how="outer")
    df["agri_hh"] = ((df["pond"] == 1) | (df["agri_control"] == 1)).astype(int)

    w = dta(os.path.join(R18, "158_BIHS sampling weights_r3.dta"), ["a01", "hhweight"])
    df = df.merge(w, on="a01", how="inner")           # Stata keep(3)
    df = df[df["agri_hh"] == 1].copy()
    df["pond"] = df["pond"].fillna(0)
    return df.rename(columns={"a01": "hhid", "hhweight": "weight"}).reset_index(drop=True)


def frame_2015():
    h1 = dta(os.path.join(R15, "015_r2_mod_h1_male.dta"), ["a01", "h1_sl"])
    h1["agri_control"] = np.where(h1["h1_sl"] == 99, 0, 1)
    agri = h1.groupby("a01", as_index=False)["agri_control"].max()

    l1 = dta(os.path.join(R15, "037_r2_mod_l1_male.dta"), ["a01", "l1_sl", "pondid"])
    l1 = l1[~((l1["l1_sl"] == 99) | (l1["pondid"] == 999))]
    l1["pond"] = 1
    pond = l1.groupby("a01", as_index=False)["pond"].max()

    df = agri.merge(pond, on="a01", how="outer")
    df["agri_hh"] = ((df["pond"] == 1) | (df["agri_control"] == 1)).astype(int)

    w = dta(os.path.join(R15, "BIHS FTF 2015 survey sampling weights.dta"),
            ["a01", "hhweight", "hh_type"])
    df = df.merge(w, on="a01", how="inner")           # Stata keep(3)
    df = df[df["hh_type"] != 1]                       # drop the FTF booster
    df = df[df["agri_hh"] == 1].copy()
    df["pond"] = df["pond"].fillna(0)
    return df.rename(columns={"a01": "hhid", "hhweight": "weight"}).reset_index(drop=True)


def frame_2011():
    h1 = dta(os.path.join(R12, "011_mod_h1_male.dta"), ["a01"])
    agri = h1.groupby("a01", as_index=False).size()[["a01"]]
    agri["agri_control"] = 1                          # Stata: g agri_control = 1

    l1 = dta(os.path.join(R12, "026_mod_l1_male.dta"), ["a01", "pondid"])
    l1 = l1[l1["pondid"] != 999]
    l1["pond"] = 1
    pond = l1.groupby("a01", as_index=False)["pond"].max()

    df = agri.merge(pond, on="a01", how="outer")
    df["agri_hh"] = ((df["pond"] == 1) | (df["agri_control"] == 1)).astype(int)

    a = dta(os.path.join(R12, "001_mod_a_male.dta"), ["a01", "Sample_type"])
    df = df.merge(a, on="a01", how="left")
    df = df[df["Sample_type"] != 1]                   # drop the FTF booster

    w = dta(os.path.join(R12, "BIHS_FTF baseline sampling weights.dta"), ["a01", "hhweight"])
    df = df.merge(w, on="a01", how="inner")           # Stata keep(3)
    df = df[df["agri_hh"] == 1].copy()
    df["pond"] = df["pond"].fillna(0)
    return df.rename(columns={"a01": "hhid", "hhweight": "weight"}).reset_index(drop=True)


FRAMES = {"2011": frame_2011, "2015": frame_2015, "2019": frame_2019, "2024": frame_2024}


def build_frames():
    return {r: FRAMES[r]() for r in ROUNDS}


# --------------------------------------------------------------------------
# Mechanisation, SPIA Figure 33.
#
# The report measures machinery USE from the CGIAR-technology module
# `d1_machinery`, not ownership from the a5_6 asset roster. That distinction
# matters enormously: 2-wheel power tiller use runs near 72 percent in 2024
# while ownership of one runs under 3 percent, because the market is served by
# rental and custom hire.
#
# The 2024 base is the set of households that can be matched back to the 2018
# round (Stata: merge on a01combined_18, keep if _merge == 3).
# --------------------------------------------------------------------------
TECH_RENAME = {
    "Power Tiller Operated Seeder - 2 wheeler": "2-wheeled power tiller",
    "Power Tiller Operated Seeder - 4 wheeler": "4-wheeled power tiller",
    "Two wheeled mechanical Reaper for Rice/Wheat/Jute": "Reaper",
    "Combine Harvester/Thresher": "Combine harvester or thresher",
    "Axial Flow Pump": "Axial flow pump",
}


def _str_id(s):
    """Mimic Stata `tostring` on a numeric id: integers lose the decimal."""
    s = pd.to_numeric(s, errors="coerce")
    return s.map(lambda v: "" if pd.isna(v)
                 else (str(int(v)) if float(v).is_integer() else str(v)))


def mech_usage_2024():
    h18 = dta(os.path.join(R18, "021_bihs_r3_male_mod_h1.dta"), ["a01", "hh_type"])
    h18 = h18.drop_duplicates()
    h18["a01"] = _str_id(h18["a01"])
    h18 = h18.drop_duplicates(subset=["a01"])

    b15 = dta(os.path.join(FINAL, "SPIA_BIHS_2024_module_b1_5.dta"),
              ["a1hhid_combined", "agri_control_household"])
    a1 = dta(os.path.join(FINAL, "SPIA_BIHS_2024_module_a1.dta"),
             ["a1hhid_combined", "districtname", "a01combined_18", "hhweight_24"])
    base = (b15.merge(a1, on="a1hhid_combined", how="inner")
                .drop_duplicates(subset=["a1hhid_combined"]))
    base["a01"] = _str_id(base["a01combined_18"])
    base = base.merge(h18, on="a01", how="inner")          # Stata keep if _merge == 3

    mach = dta(os.path.join(FINAL, "SPIA_BIHS_2024_module_d1_machinery.dta"),
               ["a1hhid_combined", "d1cgiartech_name", "d1cgiartech_usage"])
    d = mach.merge(base, on="a1hhid_combined", how="inner")  # Stata drop if _merge == 2
    d["tech"] = d["d1cgiartech_name"].replace(TECH_RENAME)
    d = d[~d["tech"].str.startswith("Alternate Wetting")]
    d["use"] = d["d1cgiartech_usage"].fillna(0)

    out = {}
    for tech, g in d.groupby("tech"):
        out[tech] = {"pct": wshare(g, "use", "hhweight_24"),
                     "n": int(g["a1hhid_combined"].nunique())}
    return out


# --------------------------------------------------------------------------
# DNA fingerprinting.
#
# Use `bangladesh_rice_assignment_results.xlsx`, which holds the field sample
# assignments. Do NOT use `ref_clusters_no_hybrids_with_HH_Ids.csv`: that file
# is a 370-row reference cluster panel whose columns are mislabelled (the
# column headed "HH Id" actually carries the variety name and there is no
# household identifier in it at all).
# --------------------------------------------------------------------------
def dna_assignments():
    df = pd.read_excel(os.path.join(DNA, "bangladesh_rice_assignment_results.xlsx"))
    field = df[df["Sample_attribute"].astype(str).str.lower() == "field"]
    assigned = field[field["Status"].astype(str).str.lower() == "assigned"]
    counts = assigned["Variety"].value_counts()
    return {
        "n_field_rows": int(len(field)),
        "n_field_samples": int(field["SPIA_sample_ID"].nunique()),
        "n_assigned_rows": int(len(assigned)),
        "n_assigned_samples": int(assigned["SPIA_sample_ID"].nunique()),
        "n_varieties": int(assigned["Variety"].nunique()),
        "by_variety": {k: int(v) for k, v in counts.items()},
    }


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
# Values published in SPIA Bangladesh Study 2025. Figure 10 gives the two
# endpoints explicitly; the middle rounds are read off the same chart.
PUBLISHED_POND = {"2011": 29.79, "2015": None, "2019": None, "2024": 23.06}
PUBLISHED_N = {"2024": 2972}


def verify():
    frames = build_frames()
    print("Aquaculture participation, share of agricultural households")
    print("(SPIA Figure 10)\n")
    print(f"  {'round':8}{'computed':>10}{'published':>11}{'n':>8}{'':>4}status")
    ok = True
    for r in ROUNDS:
        f = frames[r]
        got = wshare(f, "pond", "weight")
        pub = PUBLISHED_POND[r]
        if pub is None:
            status = "no published value to compare"
        elif abs(got - pub) < 0.05:
            status = "match"
        else:
            status = "MISMATCH"
            ok = False
        pubtxt = f"{pub:.2f}" if pub is not None else "-"
        print(f"  {r:8}{got:10.2f}{pubtxt:>11}{len(f):8d}    {status}")

    print("\nAgricultural frame sizes")
    for r in ROUNDS:
        n = len(frames[r])
        pub = PUBLISHED_N.get(r)
        extra = ""
        if pub is not None:
            extra = "   match" if n == pub else f"   published {pub}  MISMATCH"
        print(f"  {r}: {n}{extra}")

    print("\n\nMachinery use in 2024, share of agricultural households")
    print("(SPIA Figure 33; this is USE, not ownership)\n")
    pub_mech = {"2-wheeled power tiller": 72.0, "4-wheeled power tiller": 33.0}
    mech = mech_usage_2024()
    print(f"  {'technology':32}{'computed':>10}{'published':>11}{'n':>8}")
    for tech, rec in sorted(mech.items(), key=lambda kv: -kv[1]["pct"]):
        p = pub_mech.get(tech)
        ptxt = f"{p:.1f}" if p is not None else "-"
        print(f"  {tech:32}{rec['pct']:10.1f}{ptxt:>11}{rec['n']:8d}")
    print("  note: the report substitutes 12.6 for the axial flow pump in 2024,")
    print("  taking the smaller plot-level estimate from module B5 instead.")

    print("\n\nDNA fingerprinting, field sample assignments")
    d = dna_assignments()
    print(f"  field rows {d['n_field_rows']}, unique samples {d['n_field_samples']}")
    print(f"  assigned rows {d['n_assigned_rows']}, unique samples {d['n_assigned_samples']}")
    print(f"  distinct varieties assigned: {d['n_varieties']}")
    tot = d["n_assigned_rows"]
    print("  most frequent assignments:")
    for name, n in list(d["by_variety"].items())[:8]:
        print(f"    {name:16}{n:6d}   {100 * n / tot:5.1f}%")
    return ok


if __name__ == "__main__":
    verify()
