# -----------------------------------------------------------------------------
# Check the ported figures against the values printed in the SPIA report.
#
# A run that prints anything other than "match" means the port has drifted from
# the published analysis and should not be used until the cause is understood.
# -----------------------------------------------------------------------------

PUBLISHED <- list(
  pond      = c("2011" = 29.79, "2024" = 23.06),   # Figure 10 endpoints
  frame_n   = c("2024" = 2972),                    # agricultural households, 2024
  tiller_2w = 72.0                                 # Figure 33, 2-wheel power tiller use
)

verdict <- function(got, want, tol = 0.05) {
  if (is.na(got)) return("no value")
  if (abs(got - want) < tol) "match" else "MISMATCH"
}

# `[[` on a named vector raises an error when the name is absent, so look up
# published values through a helper that returns NA for rounds the report does
# not print a number for.
published <- function(vec, key) {
  if (!is.null(vec) && key %in% names(vec)) unname(vec[[key]]) else NA_real_
}

verify_all <- function() {
  frames <- build_frames()
  ok <- TRUE

  banner("Aquaculture participation, share of agricultural households (Figure 10)")
  aq <- aquaculture_participation(frames)
  cat(sprintf("%-8s %10s %11s %8s   %s\n", "round", "computed", "published", "n", "status"))
  for (i in seq_len(nrow(aq))) {
    r <- aq$round[i]
    want <- published(PUBLISHED$pond, r)
    if (is.na(want)) {
      cat(sprintf("%-8s %10.2f %11s %8d   %s\n", r, aq$pct[i], "-", aq$n[i],
                  "no published value"))
    } else {
      st <- verdict(aq$pct[i], want)
      if (st != "match") ok <- FALSE
      cat(sprintf("%-8s %10.2f %11.2f %8d   %s\n", r, aq$pct[i], want, aq$n[i], st))
    }
  }

  banner("Agricultural frame sizes")
  for (r in names(frames)) {
    n <- nrow(frames[[r]])
    want <- published(PUBLISHED$frame_n, r)
    if (is.na(want)) {
      cat(sprintf("  %-6s %6d\n", r, n))
    } else {
      st <- if (n == want) "match" else "MISMATCH"
      if (st != "match") ok <- FALSE
      cat(sprintf("  %-6s %6d   published %d   %s\n", r, n, as.integer(want), st))
    }
  }

  banner("Machinery use in 2024, share of agricultural households (Figure 33)")
  mu <- machinery_use_2024()
  cat(sprintf("%-32s %10s %11s %8s\n", "technology", "computed", "published", "n"))
  for (i in seq_len(nrow(mu))) {
    want <- if (mu$tech[i] == "2-wheeled power tiller") PUBLISHED$tiller_2w else NA_real_
    wtxt <- if (is.na(want)) "-" else sprintf("%.1f", want)
    cat(sprintf("%-32s %10.1f %11s %8d\n", mu$tech[i], mu$pct[i], wtxt, mu$n[i]))
    if (!is.na(want) && verdict(mu$pct[i], want, tol = 0.2) != "match") ok <- FALSE
  }
  cat("\nThe report substitutes 12.6 for the axial flow pump in 2024, preferring\n")
  cat("the smaller plot-level estimate from module B5.\n")

  banner("DNA fingerprinting, field sample assignments")
  d <- dna_assignments()
  cat("  field samples          ", d$n_field_rows, "\n")
  cat("  assigned to a variety  ", d$n_assigned, "\n")
  cat("  distinct varieties     ", d$n_varieties, "\n")
  top <- head(d$by_variety, 5)
  br <- sum(d$by_variety[c("BD-28", "BD-29")], na.rm = TRUE)
  cat("  most frequent:         ",
      paste(sprintf("%s %d", names(top), as.integer(top)), collapse = ", "), "\n")
  cat(sprintf("  BD-28 plus BD-29:       %.1f%% of assigned samples\n",
              100 * br / d$n_assigned))

  banner(if (ok) "All checked figures match the published report."
         else "SOME FIGURES DO NOT MATCH. Do not use these outputs.")
  invisible(ok)
}
