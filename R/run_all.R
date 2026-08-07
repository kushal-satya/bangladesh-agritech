# -----------------------------------------------------------------------------
# Run the whole analysis.
#
#   Rscript R/run_all.R
#
# from the repository root, or from anywhere with:
#
#   Rscript --vanilla /path/to/deploy_repo/R/run_all.R
#
# Writes the household frames, the crosswalk and a machine-readable summary to
# R/output/, and prints a verification table against the published SPIA
# figures. Every number it reports is computed from the replication package;
# nothing is hard coded except the published values being checked against.
# -----------------------------------------------------------------------------

# Resolve this script's own directory so the project runs from any working
# directory. commandArgs covers Rscript; sys.frames covers source().
this_dir <- local({
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg)) return(dirname(normalizePath(sub("^--file=", "", file_arg[1]))))
  if (!is.null(sys.frames()[[1]]$ofile)) return(dirname(normalizePath(sys.frames()[[1]]$ofile)))
  file.path(getwd(), "R")
})

source(file.path(this_dir, "00_config.R"), chdir = FALSE)
check_packages()
source(file.path(this_dir, "01_crosswalk.R"))
source(file.path(this_dir, "02_frames.R"))
source(file.path(this_dir, "03_indicators.R"))
source(file.path(this_dir, "04_verify.R"))

OUT_DIR <- file.path(this_dir, "output")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

cat("SPIA Bangladesh 2025, BIHS panel analysis\n")
cat("Replication package: ", SPIA_REPO, "\n", sep = "")

# 1. The crosswalk across the four rounds.
cw <- report_crosswalk()
write.csv(cw, file.path(OUT_DIR, "crosswalk.csv"), row.names = FALSE, na = "")

# 2. The agricultural frames.
frames <- build_frames()
for (r in names(frames)) {
  write.csv(frames[[r]], file.path(OUT_DIR, paste0("frame_", r, ".csv")),
            row.names = FALSE, na = "")
}

# 3. Verification against the report.
ok <- verify_all()

# 4. A machine-readable summary for anything downstream.
summary_obj <- list(
  spia_repo = SPIA_REPO,
  generated_by = "deploy_repo/R/run_all.R",
  all_checks_passed = ok,
  frame_sizes = vapply(frames, nrow, integer(1)),
  aquaculture_participation = as.list(setNames(
    round(aquaculture_participation(frames)$pct, 4), names(frames))),
  machinery_use_2024 = local({
    m <- machinery_use_2024(); as.list(setNames(round(m$pct, 4), m$tech))
  })
)
jsonlite::write_json(summary_obj, file.path(OUT_DIR, "summary.json"),
                     auto_unbox = TRUE, pretty = TRUE)

banner("Output written")
cat("  ", file.path(OUT_DIR, "crosswalk.csv"), "\n")
cat("  ", file.path(OUT_DIR, "frame_<round>.csv"), "\n")
cat("  ", file.path(OUT_DIR, "summary.json"), "\n")

if (!ok) quit(status = 1)
