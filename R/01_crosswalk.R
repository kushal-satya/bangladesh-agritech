# -----------------------------------------------------------------------------
# The cross-wave household crosswalk.
#
# This is the piece that makes the four BIHS rounds a panel rather than four
# unrelated cross-sections, and it is where merges quietly go wrong, so it is
# kept separate and reported on.
#
# The linkage lives in the 2024 roster, `SPIA_BIHS_2024_module_a1.dta`, which
# carries a column pointing back at each earlier round:
#
#   a1hhid_combined   the 2024 household, 5,554 of them
#   a01combined_18    its parent household in 2018/19
#   a01combined_15    its parent household in 2015
#   a01_12            its parent household in 2011/12
#
# Three traps, all of them found the hard way:
#
#   1. The two id kinds are not interchangeable. a1hhid_combined is a
#      hierarchical composite string and a household that split twice reads
#      "2174.1.1", with two dots. Coercing that to a number gives NA, and 77 of
#      the 5,554 households collapse into one key. The link columns, by
#      contrast, are genuine numbers and must go through a numeric round trip
#      because the prior rosters store them as doubles. See 00_config.R.
#   2. The prior rosters themselves contain fractional ids such as 3.1 and
#      10.1, for households that had already split in that round. Treating a01
#      as an integer loses them.
#   3. The map back to earlier rounds is many-to-one. 5,554 households in 2024
#      descend from 5,244 households in 2018/19, because 563 of them are
#      recorded splits. Any join from 2024 onto a prior wave is therefore m:1,
#      and any join in the other direction fans out.
# -----------------------------------------------------------------------------

build_crosswalk <- function() {
  a1 <- read_stata(
    file.path(PATHS$final, "SPIA_BIHS_2024_module_a1.dta"),
    cols = c("a1hhid_combined", "a01combined_18", "a01combined_15", "a01_12",
             "a01split_hh_18", "a01split_hh_15",
             "hhweight_24", "divisionname", "districtname", "upazilaname")
  )

  cw <- tibble(
    hh24        = id_verbatim(a1$a1hhid_combined),
    hh18        = norm_id(a1$a01combined_18),
    hh15        = norm_id(a1$a01combined_15),
    hh12        = norm_id(a1$a01_12),
    split_18    = as.integer(a1$a01split_hh_18 == 1),
    split_15    = as.integer(a1$a01split_hh_15 == 1),
    weight_24   = as.numeric(a1$hhweight_24),
    division    = as.character(a1$divisionname),
    district    = as.character(a1$districtname),
    upazila     = as.character(a1$upazilaname)
  )

  # The 2024 key must survive normalisation intact. If this ever fires, the id
  # handling has regressed and every downstream join is suspect.
  if (anyDuplicated(cw$hh24) || any(is.na(cw$hh24))) {
    stop("hh24 is not a unique, complete key after normalisation: ",
         nrow(cw), " rows but ", dplyr::n_distinct(cw$hh24), " distinct ids, ",
         sum(is.na(cw$hh24)), " missing.")
  }
  cw
}

# The household roster of each prior wave, used to measure how much of each
# earlier round is still represented in 2024.
prior_wave_rosters <- function() {
  list(
    "2018" = read_stata(file.path(PATHS$r18, "009_bihs_r3_male_mod_a.dta"), "a01"),
    "2015" = read_stata(file.path(PATHS$r15, "001_r2_mod_a_male.dta"), "a01"),
    "2011" = read_stata(file.path(PATHS$r12, "001_mod_a_male.dta"), "a01")
  )
}

# A plain-language account of what the crosswalk actually links, printed so
# that attrition is visible rather than assumed.
report_crosswalk <- function(cw = build_crosswalk()) {
  rosters <- prior_wave_rosters()

  banner("Cross-wave household crosswalk")
  cat("2024 households:                       ", nrow(cw), "\n")
  cat("  recorded as a split from 2018/19:    ", sum(cw$split_18 == 1, na.rm = TRUE), "\n")
  cat("  recorded as a split from 2015:       ", sum(cw$split_15 == 1, na.rm = TRUE), "\n\n")

  spec <- list(
    list(round = "2018/19", col = "hh18", roster = rosters[["2018"]]$a01),
    list(round = "2015",    col = "hh15", roster = rosters[["2015"]]$a01),
    list(round = "2011/12", col = "hh12", roster = rosters[["2011"]]$a01)
  )

  cat(sprintf("%-10s %10s %10s %12s %10s\n",
              "round", "roster", "linked", "distinct", "matched"))
  for (s in spec) {
    ids      <- cw[[s$col]]
    roster   <- norm_id(s$roster)
    linked   <- sum(!is.na(ids))
    distinct <- dplyr::n_distinct(ids[!is.na(ids)])
    matched  <- sum(unique(ids[!is.na(ids)]) %in% roster)
    cat(sprintf("%-10s %10d %10d %12d %10d\n",
                s$round, length(roster), linked, distinct, matched))
  }
  cat("\n  roster    households enumerated in that round\n")
  cat("  linked    2024 households carrying an id for that round\n")
  cat("  distinct  distinct parent households they point at\n")
  cat("  matched   of those parents, how many exist in the round's roster\n")

  invisible(cw)
}

# Attach the crosswalk to a prior-wave table. Direction matters: this is a
# many-to-one join from 2024 onto the earlier round, so the earlier round's
# values are repeated across split households, which is what you want when
# carrying a baseline characteristic forward.
attach_prior <- function(cw, prior_df, prior_id_col, round = c("2018", "2015", "2011")) {
  round <- match.arg(round)
  key <- c("2018" = "hh18", "2015" = "hh15", "2011" = "hh12")[[round]]
  prior_df <- prior_df %>% mutate(.join_id = norm_id(.data[[prior_id_col]]))
  cw %>%
    mutate(.join_id = .data[[key]]) %>%
    left_join(prior_df, by = ".join_id") %>%
    select(-.join_id)
}
