# Paused mid-task — resume notes

Paused 6 August 2026. Two threads were in flight.

---

## Thread 1: density pass (done, built, NOT committed)

`build_dashboard.py` and `index.html` are modified in the working tree. The
change is a pure CSS density pass, no content or data changes:

- body 15px to 13.5px, line-height 1.5 to 1.45
- h1 25px to 21px, h2 20px to 17px, h3 15px to 13.5px
- layout max-width 1360 to 1500, main column 940 to 1140
- tighter table rows, rail, statline, section margins
- technology and institution grids go to 3 and 4 columns

Rebuilt and verified at 1270px viewport. The whole summary table plus the
method toggle now sit above the fold, where before only three elements did.

To ship it:

```bash
python build_dashboard.py && git add -A && git commit && git push
```

The live site currently serves commit `4de8667`, which is the previous
(looser) layout. Nothing is broken either way.

---

## Thread 2: replicate the SPIA Stata analysis (not started)

The goal, in the user's words, is to rewrite their Stata in Python so the
dashboard genuinely replicates the report rather than caveating the
differences.

Replication repo is local at:

```
C:\Users\kd475\RES\BGD_MIX\hilsa_feasibility\external\SPIA-Bangladesh-Study-2025
```

It has the real data, not LFS pointers. `Code/Analysis/analysis.do` is 18,915
lines and labels every output by the figure or table it produces
(`figure_10`, `table_15`), so grep for those rather than reading it whole.

### What still has to be settled

**Denominators.** The dashboard uses agricultural households for everything.
The report picks a population per innovation: Boro rice-growing households for
rice varieties, fish-cultivating households for species, agricultural
households excluding aquaculture-only for machinery, Boro irrigators for
pumps. Table 26 in the report carries the explicit "Population of interest"
column. Porting means reproducing those per-indicator denominators.

**Sample sizes.** Dashboard reports the BIHS panel as delivered, including the
Feed the Future booster (6,503 / 6,715 / 6,011 / 5,554). The report uses the
nationally representative core of roughly 5,500 per round. Only 2024 agrees.

### Confirmed finding: the DNA tab uses the wrong file

This one is worth fixing regardless of how far the port goes.

`mixtape_pipeline.py` reads
`Data/DNA fingerprinting/ref_clusters_no_hybrids_with_HH_Ids.csv`. That file
is a 370-row reference-cluster panel, and its columns are mislabelled: the
column headed `HH Id` actually holds the variety name (17 distinct values
including an `Others` bucket), and there is no household identifier in it at
all despite the filename.

The real field results are in
`Data/DNA fingerprinting/bangladesh_rice_assignment_results.xlsx`:

| | |
|---|---|
| rows | 2,202, all `Sample_attribute = field` |
| unique samples | 2,186 |
| `Status = Assigned` | 1,199 rows, 1,192 unique samples |
| distinct varieties assigned | 26 |
| BD-29 | 520 of 1,199 assigned, 43.4% |
| BD-89 | 160, 13.3% |
| BD-28 | 132, 11.0% |

So BR-28 and BR-29 together are about 54% of assigned field samples, which
matches the report's "BRRI Dhan 28 and 29 continue to dominate" narrative.
The current dashboard instead shows 19.2%, because it is describing the
composition of a reference panel rather than adoption among farmers.

Note the report quotes BRRI Dhan 28 at 6.45% and BRRI Dhan 29 at 23.01% of
1,665 DNA-fingerprinted Boro households. Neither the 370-row file nor a raw
count of assigned samples reproduces that directly, so the household-level
weighting and the Boro restriction in `analysis.do` still need to be worked
out before the tab can be rebuilt correctly.

### Suggested order on resume

1. Ship or discard the density pass so the tree is clean.
2. Grep `analysis.do` for `figure_10`, `figure_17`, `figure_18`, `figure_32`,
   `table_15`, `table_22`, `table_23`, `table_26` and write down the exact
   denominator, weight variable and collapse rule for each.
3. Port those to Python next to `mixtape_pipeline.py`, emitting the same JSON
   shape so `build_dashboard.py` needs no change.
4. Rebuild the DNA tab from `bangladesh_rice_assignment_results.xlsx`.
5. Check each ported figure against the published number before publishing,
   and drop the comparability caveat only for the indicators that then match.
