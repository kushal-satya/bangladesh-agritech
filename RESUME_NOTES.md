# SPIA replication: state of play

Updated 7 August 2026.

## Done and verified

`spia_replication.py` ports the reach computations from the study's
`Code/Analysis/analysis.do`. Run it to print the verification table:

```bash
python spia_replication.py
```

| Quantity | Computed | Published | |
|---|---|---|---|
| Aquaculture participation 2011/12 | 29.79 | 29.79 | match |
| Aquaculture participation 2024 | 23.06 | 23.06 | match |
| Agricultural frame 2024 | 2,972 | 2,972 | match |
| 2-wheel power tiller use 2024 | 71.9 | 72.0 | match |

Agricultural frame sizes come out at 3,082 / 3,053 / 3,220 / 2,972.

Three things the port settled:

1. **The booster sample.** 2011/12 and 2015 drop the Feed the Future booster
   (`Sample_type == 1`, `hh_type == 1`). Keeping it inflates the panel from
   roughly 5,500 to roughly 6,700 per round. That was the whole sample-size
   discrepancy against the report.
2. **Machinery is use, not ownership.** The report reads
   `d1cgiartech_usage` from module `d1_machinery`. Power tiller *use* is 72%
   while *ownership* in the a5_6 asset roster is under 3%, because the market
   runs on rental and custom hire. Note Figure 33 is the mechanisation figure;
   Figure 32 is mobile-app usage. Any mapping taken from reading the PDF
   should be re-checked against the code.
3. **The DNA tab was reading the wrong file** (now fixed, see below).

## Done: DNA tab rebuilt on the correct source

Was reading `ref_clusters_no_hybrids_with_HH_Ids.csv`, a 370-row reference
cluster panel whose columns are mislabelled — the column headed `HH Id`
actually carries the variety name, and there is no household id in it at all.

Now reads `bangladesh_rice_assignment_results.xlsx`: 2,202 field samples,
1,199 assigned to a named variety, 26 distinct varieties. BD-29 is 43.4% of
assigned samples, BD-89 13.3%, BD-28 11.0%, so BR-28 and BR-29 together are
54.4% — which is what the report means by the two mega-varieties continuing to
dominate. The old tab said 19.2%, describing a reference panel rather than
farmer adoption. The cluster chart, which had no basis in the correct file, is
replaced by the assignment-status breakdown; 45% of field samples came back
unassigned, which is worth knowing.

## Not done

**The main tables still run on the old frame.** `data/mixtape_rice.json`,
`mixtape_aqua.json` and `mixtape_mech.json` still come from
`mixtape_pipeline.py`, which uses its own agricultural-household definition
and keeps the booster. So the dashboard shows aquaculture at 23.4 where the
verified replication gives 23.06, and mechanisation still shows ownership
rather than use.

Next step is to regenerate those three files from `spia_replication.py`'s
frames. The frame functions (`frame_2011`, `frame_2015`, `frame_2019`,
`frame_2024`) already return household-level tables with weights and are the
right foundation; they need district joined on, plus the per-indicator flags.

**Rice variety families are not ported.** The report classifies rice by CGIAR
origin and release year (Table 15, "CGIAR varieties year 2000 onwards"),
computed over Boro rice-growing households. The dashboard uses its own seven
variety families over all agricultural households. These are genuinely
different analytical objects, so this needs a decision rather than a
mechanical port: either adopt the report's taxonomy, or keep the dashboard's
families but compute them on the corrected frame.

Until the main tables are regenerated, the comparability note on the map
overview tab should stay.
