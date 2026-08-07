# BIHS panel analysis in R

A replicable port of the household-panel construction and reach computations
behind the MIXTAPE dashboard, following the Stata in the SPIA Bangladesh Study
2025 replication package.

It exists to answer two questions without anyone having to open Stata:

1. **How do the four BIHS rounds join into a panel?** That is `01_crosswalk.R`,
   and it is the part most likely to go quietly wrong.
2. **Do the ported figures still match the published report?** That is
   `04_verify.R`, which fails loudly if they stop matching.

## Running it

Requires R 4.1 or newer and the packages `haven`, `dplyr`, `tidyr`, `readxl`,
`jsonlite` and `tibble`.

```bash
Rscript R/run_all.R
```

Point it at your copy of the replication package by editing `SPIA_REPO` at the
top of `R/00_config.R`, or by setting the environment variable:

```bash
SPIA_REPO=/path/to/SPIA-Bangladesh-Study-2025 Rscript R/run_all.R
```

Unit tests for the identifier handling:

```bash
Rscript R/tests/test_norm_id.R
```

## What a clean run reports

```
round          roster     linked     distinct    matched
2018/19          6011       5554         5244       5244
2015             6715       5554         4987       4987
2011/12          6503       5554         4840       4840

round      computed   published        n   status
2011          29.79       29.79     3082   match
2024          23.06       23.06     2972   match

2-wheeled power tiller     71.9        72.0     2739
```

Every linked identifier resolves to a household that exists in the target
round, so nothing is being silently dropped in the merge.

## Files

| File | What it does |
|---|---|
| `00_config.R` | Paths, packages, and the two identifier helpers |
| `01_crosswalk.R` | Joins the four rounds into a panel and reports attrition |
| `02_frames.R` | The agricultural household frame, one function per round |
| `03_indicators.R` | Aquaculture participation, machinery use, DNA assignments |
| `04_verify.R` | Checks the computed figures against the published report |
| `run_all.R` | Runs everything and writes `R/output/` |
| `tests/test_norm_id.R` | Unit tests for identifier normalisation |

Outputs land in `R/output/`: `crosswalk.csv`, `frame_<round>.csv` and
`summary.json`.

## Three things worth knowing about this data

**Household identifiers come in two incompatible kinds.** The 2024 key
`a1hhid_combined` is a hierarchical composite string: a household that split
twice is `"2174.1.1"`, with two dots. It is not a number, and coercing it to
one turns 77 of the 5,554 households into `NA` and collapses them onto a single
key. The cross-wave link columns (`a01combined_18`, `a01combined_15`,
`a01_12`) *are* numbers and have to make a numeric round trip, because the
prior-wave rosters store the same identifier as a double. So `id_verbatim()`
handles the 2024 key and `norm_id()` handles the links, and the two must not be
swapped. `build_crosswalk()` asserts the 2024 key stays unique and complete.

**The prior rosters contain fractional identifiers.** 2018/19 has 935 and 2015
has 396 households whose `a01` looks like `3.1` or `10.1`, because they had
already split in that round. Rounding `a01` to an integer loses them.

**2011/12 and 2015 drop the Feed the Future booster sample.** The Stata filters
on `Sample_type == 1` and `hh_type == 1`. Keeping the booster inflates those
rounds from roughly 5,500 households to roughly 6,700, which is why a naive
recomputation reports larger samples than the report does.

## Relationship to the rest of the repository

`spia_replication.py` in the repository root does the same computations in
Python and produces the same numbers; the two are independent implementations
of the same Stata and agreeing is a useful check. The dashboard itself
(`build_dashboard.py`) still reads `data/mixtape_*.json`, which for rice,
aquaculture and mechanisation is older output on a different frame. See
`../RESUME_NOTES.md` for what regenerating those involves.
