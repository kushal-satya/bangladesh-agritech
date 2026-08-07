# -----------------------------------------------------------------------------
# Paths, packages and shared helpers.
#
# Edit SPIA_REPO below (or set the environment variable of the same name) to
# point at your copy of the SPIA Bangladesh Study 2025 replication package.
# Nothing else in this project needs changing.
# -----------------------------------------------------------------------------

SPIA_REPO <- Sys.getenv(
  "SPIA_REPO",
  unset = "C:/Users/kd475/RES/BGD_MIX/hilsa_feasibility/external/SPIA-Bangladesh-Study-2025"
)

if (!dir.exists(SPIA_REPO)) {
  stop("SPIA_REPO does not exist: ", SPIA_REPO,
       "\nEdit R/00_config.R or set the SPIA_REPO environment variable.")
}

PATHS <- list(
  final = file.path(SPIA_REPO, "Data", "Final"),
  prior = file.path(SPIA_REPO, "Data", "Prior Waves"),
  dna   = file.path(SPIA_REPO, "Data", "DNA fingerprinting")
)
PATHS$r18 <- file.path(PATHS$prior, "Third Round (2018-2019)")
PATHS$r15 <- file.path(PATHS$prior, "Second Round (2015-2016)")
PATHS$r12 <- file.path(PATHS$prior, "First Round (2011-2012)")

# Where this project writes its output.
OUT_DIR <- file.path(dirname(normalizePath(file.path(getwd(), "R"), mustWork = FALSE)), "R", "output")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

REQUIRED_PACKAGES <- c("haven", "dplyr", "tidyr", "readxl", "jsonlite", "tibble")

check_packages <- function() {
  missing <- REQUIRED_PACKAGES[!vapply(REQUIRED_PACKAGES, requireNamespace,
                                       logical(1), quietly = TRUE)]
  if (length(missing)) {
    stop("Missing packages: ", paste(missing, collapse = ", "),
         "\nInstall with: install.packages(c(",
         paste0('"', missing, '"', collapse = ", "), "))")
  }
  invisible(TRUE)
}

suppressPackageStartupMessages({
  library(haven)
  library(dplyr)
  library(tidyr)
  library(tibble)
})

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# Read a Stata file and strip value labels, which otherwise turn numeric
# comparisons into factor comparisons and silently fail.
read_stata <- function(path, cols = NULL) {
  if (!file.exists(path)) stop("File not found: ", path)
  df <- haven::read_dta(path, col_select = all_of(cols))
  df <- haven::zap_labels(df)
  df <- haven::zap_label(df)
  as_tibble(df)
}

# -----------------------------------------------------------------------------
# Household identifiers. There are two kinds and they must not be confused.
#
# id_verbatim()  the 2024 primary key, a1hhid_combined. These are hierarchical
#                composite strings, not numbers: a household that split twice
#                is recorded as "2174.1.1", with two dots. Passing one through
#                as.numeric() yields NA, and 77 of the 5,554 households in 2024
#                collapse into a single unusable key. Keep them verbatim.
#
# norm_id()      the cross-wave link keys (a01combined_18, a01combined_15,
#                a01_12) and the prior-wave rosters (a01). These are genuine
#                numbers, and the prior rosters really do contain fractional
#                ids such as 3.1 and 10.1 for households that split in that
#                round, so a numeric round trip is both safe and necessary:
#                one side arrives as character, the other as double, and they
#                only compare after being put in a common form. Verified
#                collision free on all three link columns.
# -----------------------------------------------------------------------------

id_verbatim <- function(x) {
  out <- trimws(as.character(x))
  out[out %in% c("", "NA", ".")] <- NA_character_
  out
}

norm_id <- function(x) {
  if (is.character(x)) {
    x <- trimws(x)
    x[x %in% c("", "NA", ".")] <- NA_character_
  }
  num <- suppressWarnings(as.numeric(x))

  # Use formatC rather than format(). format() picks one width for the whole
  # vector, so a single id with two decimals turns "118.2" into "118.20" and
  # the key silently stops matching. formatC formats each element to a fixed
  # number of decimals, after which trailing zeros and any bare trailing dot
  # are stripped. The dot itself halts the zero-stripping regex, so a whole
  # number such as 1200 survives intact.
  out <- formatC(num, format = "f", digits = 6)
  out <- sub("0+$", "", out)
  out <- sub("\\.$", "", out)
  out[is.na(num)] <- NA_character_
  trimws(out)
}

# Weighted mean expressed as a percentage, ignoring missing values.
weighted_pct <- function(x, w) {
  keep <- !is.na(x) & !is.na(w)
  if (!any(keep) || sum(w[keep]) <= 0) return(NA_real_)
  100 * sum(x[keep] * w[keep]) / sum(w[keep])
}

# Stata's `merge ..., keep(3)` is an inner join. Naming it makes the intent
# obvious at the call sites below.
inner <- function(x, y, by) dplyr::inner_join(x, y, by = by)

banner <- function(txt) {
  cat("\n", strrep("-", 74), "\n", txt, "\n", strrep("-", 74), "\n", sep = "")
}
