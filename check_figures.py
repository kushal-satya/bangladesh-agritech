"""Print every national weighted share in data/, so any figure quoted in the
prose of content.toml can be checked against the underlying data.

The tables on the dashboard are generated from these same files at build time
and cannot drift. This script exists for the sentences that still name a number
by hand, such as the mechanisation lead paragraph.

    python check_figures.py
"""
import json, os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
WAVES = ["2011", "2015", "2019", "2024"]
LABELS = ["2011/12", "2015", "2018/19", "2024"]


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def national(src, wave):
    return src["by_wave"].get(wave, {}).get("__NATIONAL__", {})


def report(title, src, keys):
    print(f"\n{title}")
    print(f"  {'indicator':34}" + "".join(f"{l:>10}" for l in LABELS) + f"{'change':>10}")
    for k in keys:
        vals = [national(src, w).get(k) for w in WAVES]
        vals = [v if isinstance(v, (int, float)) else None for v in vals]
        cells = "".join(f"{(f'{v:.2f}' if v is not None else '-'):>10}" for v in vals)
        real = [v for v in vals if v is not None]
        chg = f"{real[-1] - real[0]:+.2f}" if len(real) >= 2 else "-"
        print(f"  {k:34}{cells}{chg:>10}")


def main():
    rice, aqua, mech = load("mixtape_rice.json"), load("mixtape_aqua.json"), load("mixtape_mech.json")
    dna, summary = load("mixtape_dna.json"), load("mixtape_summary.json")

    print("National weighted shares, percent of agricultural households")
    report("Rice", rice, ["RICE_GROWER", "BRRI_CORE28_29", "BRRI_OLDER_HYV", "BRRI_NEW_POST2012",
                          "BRRI_STRESS", "BINA", "HYBRID", "LOCAL"])
    report("Aquaculture", aqua, ["ANY_POND", "CARP_ANY", "POLY_CARP_2PLUS", "TILAPIA", "MOLA",
                                 "PRAWN_GALDA", "SHRIMP_BAGDA", "SUPP_FEED", "HORMONE", "DISEASE_CTL"])
    report("Mechanisation", mech, ["TRACTOR", "POWER_TILLER", "POWER_THRESHER", "SPRAYER",
                                   "ELEC_MOTOR_PUMP", "DIESEL_MOTOR_PUMP", "LLP_IRRIG",
                                   "AXIAL_FLOW_PUMP", "USE_MOTOR_THRESH", "USE_MOTOR_HARVEST"])

    print("\nSample sizes")
    for w, lbl in zip(WAVES, LABELS):
        r = summary["rounds"][w]
        print(f"  {lbl:10} panel {r['n_panel']:>6}   agricultural {r['n_hh']:>6}")

    print("\nDNA fingerprint subset (hybrid-excluded cluster file)")
    by_var = dna.get("by_variety", {})
    total = sum(by_var.values()) or 1
    boro = by_var.get("Bri Dhan BR-28 (Boro)", 0) + by_var.get("Bri Dhan BR-29 (Boro)", 0)
    print(f"  samples {dna['n_samples']}   varieties {dna['n_varieties']}   clusters {dna['n_clusters']}")
    print(f"  BR-28 plus BR-29: {boro} of {total} samples = {100 * boro / total:.1f}%")
    print("  most frequent entries:")
    for name, n in sorted(by_var.items(), key=lambda x: -x[1])[:6]:
        print(f"    {name:34}{n:>6}  ({100 * n / total:.1f}%)")

    print("\nReminder: the SPIA Bangladesh Study 2025 uses a different denominator for")
    print("each innovation class, so these figures are not directly comparable with the")
    print("published report. See the comparability note on the map overview tab.")


if __name__ == "__main__":
    main()
