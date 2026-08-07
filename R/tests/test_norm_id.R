# Unit tests for the household id normaliser.
#
#   Rscript R/tests/test_norm_id.R
#
# norm_id is the single point where 2024's character ids (which carry a
# decimal suffix for split households) are reconciled with the prior waves'
# numeric ids. A silent change here detaches every split household from its
# parent, so it gets its own tests.

this_dir <- local({
  args <- commandArgs(trailingOnly = FALSE)
  fa <- grep("^--file=", args, value = TRUE)
  if (length(fa)) dirname(dirname(normalizePath(sub("^--file=", "", fa[1]))))
  else file.path(getwd(), "R")
})
source(file.path(this_dir, "00_config.R"))

failures <- 0L
expect <- function(input, want, label) {
  got <- norm_id(input)
  ok <- identical(as.character(got), as.character(want))
  if (!ok) failures <<- failures + 1L
  cat(sprintf("  %-28s %-22s %s\n", label,
              paste(got, collapse = ","), if (ok) "ok" else
                paste0("FAIL, wanted ", paste(want, collapse = ","))))
}

cat("norm_id\n")
expect("117",        "117",        "plain integer string")
expect("118.2",      "118.2",      "split household suffix")
expect("118.25",     "118.25",     "two decimal places")
expect("1200",       "1200",       "trailing zeros in integer")
expect("1200.5",     "1200.5",     "trailing zeros plus decimal")
expect(117,          "117",        "numeric input")
expect(118.2,        "118.2",      "numeric with decimal")
expect(c("117", "118.2", "1200", "9.25"),
       c("117", "118.2", "1200", "9.25"),
       "mixed vector keeps each id")
expect(c("117", NA, ""), c("117", NA, NA), "missing values")

# The property that actually matters: a value read as text and the same value
# read as a double must normalise to the same key, or joins across waves fail.
cat("\nid_verbatim, the 2024 primary key\n")
expect_v <- function(input, want, label) {
  got <- id_verbatim(input)
  ok <- identical(as.character(got), as.character(want))
  if (!ok) failures <<- failures + 1L
  cat(sprintf("  %-28s %-22s %s\n", label, paste(got, collapse = ","),
              if (ok) "ok" else paste0("FAIL, wanted ", paste(want, collapse = ","))))
}
expect_v("2174.1.1", "2174.1.1", "twice-split household")
expect_v("118.2",    "118.2",    "once-split household")
expect_v("117",      "117",      "unsplit household")
expect_v(c("2174.1.1", "118.2", "117"), c("2174.1.1", "118.2", "117"),
         "vector keeps every id")

# The failure this guards against: a two-dot id is not a number, and pushing it
# through norm_id silently produces NA.
cat("\n  for contrast, norm_id on a two-dot id yields: ",
    format(norm_id("2174.1.1")), " (this is why the two functions differ)\n", sep = "")

cat("\ncross-type agreement\n")
pairs <- list(list("117", 117), list("118.2", 118.2), list("1200", 1200))
for (p in pairs) {
  a <- norm_id(p[[1]]); b <- norm_id(p[[2]])
  ok <- identical(a, b)
  if (!ok) failures <- failures + 1L
  cat(sprintf("  %-28s %-10s %-10s %s\n",
              paste0("text vs numeric ", p[[1]]), a, b,
              if (ok) "ok" else "FAIL"))
}

cat("\n")
if (failures > 0) {
  cat(failures, "test(s) failed\n")
  quit(status = 1)
}
cat("all tests passed\n")
