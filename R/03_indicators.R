# -----------------------------------------------------------------------------
# Indicators computed on the frames from 02_frames.R.
# -----------------------------------------------------------------------------

# Aquaculture participation, SPIA Figure 10: the weighted share of agricultural
# households operating at least one pond.
aquaculture_participation <- function(frames = build_frames()) {
  tibble(
    round = names(frames),
    pct   = vapply(frames, function(f) weighted_pct(f$pond, f$weight), numeric(1)),
    n     = vapply(frames, nrow, integer(1))
  )
}

# Machinery use, SPIA Figure 33.
#
# The report measures USE from the CGIAR technology module d1_machinery, not
# ownership from the a5_6 asset roster. The gap is large and meaningful: two
# wheel power tiller use runs near 72 percent in 2024 while ownership of one
# runs under 3 percent, because the market is served by rental and custom hire
# rather than by households buying machines.
#
# The 2024 base is restricted to households that can be matched back to the
# 2018 round (Stata: merge on a01combined_18, keep if _merge == 3).
TECH_RENAME <- c(
  "Power Tiller Operated Seeder - 2 wheeler"          = "2-wheeled power tiller",
  "Power Tiller Operated Seeder - 4 wheeler"          = "4-wheeled power tiller",
  "Two wheeled mechanical Reaper for Rice/Wheat/Jute" = "Reaper",
  "Combine Harvester/Thresher"                        = "Combine harvester or thresher",
  "Axial Flow Pump"                                   = "Axial flow pump"
)

machinery_use_2024 <- function() {
  h18 <- read_stata(file.path(PATHS$r18, "021_bihs_r3_male_mod_h1.dta"),
                    c("a01", "hh_type")) %>%
    distinct() %>%
    mutate(a01 = norm_id(a01)) %>%
    distinct(a01, .keep_all = TRUE)

  b15 <- read_stata(file.path(PATHS$final, "SPIA_BIHS_2024_module_b1_5.dta"),
                    c("a1hhid_combined", "agri_control_household"))
  a1 <- read_stata(file.path(PATHS$final, "SPIA_BIHS_2024_module_a1.dta"),
                   c("a1hhid_combined", "districtname", "a01combined_18", "hhweight_24"))

  base <- b15 %>%
    inner(a1, "a1hhid_combined") %>%
    distinct(a1hhid_combined, .keep_all = TRUE) %>%
    mutate(a01 = norm_id(a01combined_18)) %>%
    inner(h18, "a01")                                    # Stata keep if _merge == 3

  mach <- read_stata(file.path(PATHS$final, "SPIA_BIHS_2024_module_d1_machinery.dta"),
                     c("a1hhid_combined", "d1cgiartech_name", "d1cgiartech_usage"))

  mach %>%
    inner(base, "a1hhid_combined") %>%                   # Stata drop if _merge == 2
    mutate(tech = dplyr::recode(as.character(d1cgiartech_name), !!!TECH_RENAME)) %>%
    filter(!startsWith(tech, "Alternate Wetting")) %>%
    mutate(use = ifelse(is.na(d1cgiartech_usage), 0, d1cgiartech_usage)) %>%
    group_by(tech) %>%
    summarise(pct = weighted_pct(use, hhweight_24),
              n = dplyr::n_distinct(a1hhid_combined), .groups = "drop") %>%
    arrange(desc(pct))
}

# DNA fingerprinting.
#
# Read bangladesh_rice_assignment_results.xlsx, the field sample assignments.
# Do not use ref_clusters_no_hybrids_with_HH_Ids.csv: that file holds a 370 row
# reference cluster panel and its columns are mislabelled, with the column
# headed "HH Id" actually carrying the variety name and no household id present
# anywhere in the file.
dna_assignments <- function() {
  path <- file.path(PATHS$dna, "bangladesh_rice_assignment_results.xlsx")
  # Read every column as text. The Top_IBS and Top_Purity columns hold numbers
  # on assigned rows and the string "Not assigned" elsewhere, so letting readxl
  # infer a type produces a warning per offending cell (about 2,000 of them)
  # and coerces those cells to NA. Nothing here needs them as numbers.
  df <- readxl::read_excel(path, col_types = "text")
  field <- df %>% filter(tolower(as.character(Sample_attribute)) == "field")
  status <- ifelse(is.na(field$Status), "Not run", trimws(as.character(field$Status)))
  assigned <- field[tolower(status) == "assigned", ]

  list(
    n_field_rows      = nrow(field),
    n_field_samples   = dplyr::n_distinct(field$SPIA_sample_ID),
    n_assigned        = nrow(assigned),
    n_varieties       = dplyr::n_distinct(assigned$Variety),
    by_variety        = sort(table(assigned$Variety), decreasing = TRUE),
    by_status         = sort(table(status), decreasing = TRUE)
  )
}
