# -----------------------------------------------------------------------------
# The agricultural household frame, one function per round.
#
# Ported from Code/Analysis/analysis.do in the SPIA replication package. The
# frame is "grew a crop OR operated a pond":
#
#   2024   agri_control_household = (b1repeat_count > 0) | (b1fishing_count > 0)
#          built in data_structure.do and shipped in module b1_5
#   prior  agri_control = (h1_sl != 99), then OR'd with the pond flag from
#          the l1 module, built inline in analysis.do
#
# Two details that change the answer materially:
#
#   * 2011/12 and 2015 drop the Feed the Future booster sample (Sample_type
#     and hh_type equal to 1). Keeping it inflates each of those rounds from
#     roughly 5,500 to roughly 6,700 households.
#   * The weight merge is Stata's keep(3), an inner join. Households without a
#     sampling weight leave the frame entirely.
#
# Each function returns one row per household: hhid, weight, agri_hh, pond.
# -----------------------------------------------------------------------------

frame_2024 <- function() {
  base <- read_stata(file.path(PATHS$final, "SPIA_BIHS_2024_module_b1_5.dta"),
                     c("a1hhid_combined", "agri_control_household")) %>%
    group_by(a1hhid_combined) %>% slice(1) %>% ungroup()

  pond <- read_stata(file.path(PATHS$final, "SPIA_BIHS_2024_module_e5.dta"),
                     c("a1hhid_combined", "b1plot_fishing")) %>%
    group_by(a1hhid_combined) %>%
    summarise(pond = max(b1plot_fishing, na.rm = TRUE), .groups = "drop") %>%
    mutate(pond = ifelse(is.finite(pond), pond, NA_real_))

  wts <- read_stata(file.path(PATHS$final, "SPIA_BIHS_2024_module_a1.dta"),
                    c("a1hhid_combined", "hhweight_24"))

  base %>%
    full_join(pond, by = "a1hhid_combined") %>%
    left_join(wts, by = "a1hhid_combined") %>%
    mutate(pond = ifelse(is.na(pond) & agri_control_household == 1, 0, pond)) %>%
    filter(agri_control_household == 1) %>%
    transmute(hhid = id_verbatim(a1hhid_combined),
              weight = as.numeric(hhweight_24),
              agri_hh = 1L,
              pond = as.numeric(pond))
}

frame_2019 <- function() {
  agri <- read_stata(file.path(PATHS$r18, "021_bihs_r3_male_mod_h1.dta"),
                     c("a01", "h1_sl")) %>%
    mutate(agri_control = ifelse(h1_sl == 99, 0, 1)) %>%
    group_by(a01) %>%
    summarise(agri_control = max(agri_control, na.rm = TRUE), .groups = "drop")

  pond <- read_stata(file.path(PATHS$r18, "051_bihs_r3_male_mod_l1.dta"),
                     c("a01", "sl_l1", "pondid_l1")) %>%
    filter(!(sl_l1 == 0 | pondid_l1 == 999)) %>%
    group_by(a01) %>% summarise(pond = 1, .groups = "drop")

  wts <- read_stata(file.path(PATHS$r18, "158_BIHS sampling weights_r3.dta"),
                    c("a01", "hhweight"))

  agri %>%
    full_join(pond, by = "a01") %>%
    mutate(agri_hh = as.integer(pond %in% 1 | agri_control %in% 1)) %>%
    inner(wts, "a01") %>%                                  # Stata keep(3)
    filter(agri_hh == 1) %>%
    mutate(pond = ifelse(is.na(pond), 0, pond)) %>%
    transmute(hhid = norm_id(a01), weight = as.numeric(hhweight),
              agri_hh, pond = as.numeric(pond))
}

frame_2015 <- function() {
  agri <- read_stata(file.path(PATHS$r15, "015_r2_mod_h1_male.dta"),
                     c("a01", "h1_sl")) %>%
    mutate(agri_control = ifelse(h1_sl == 99, 0, 1)) %>%
    group_by(a01) %>%
    summarise(agri_control = max(agri_control, na.rm = TRUE), .groups = "drop")

  pond <- read_stata(file.path(PATHS$r15, "037_r2_mod_l1_male.dta"),
                     c("a01", "l1_sl", "pondid")) %>%
    filter(!(l1_sl == 99 | pondid == 999)) %>%
    group_by(a01) %>% summarise(pond = 1, .groups = "drop")

  wts <- read_stata(file.path(PATHS$r15, "BIHS FTF 2015 survey sampling weights.dta"),
                    c("a01", "hhweight", "hh_type"))

  agri %>%
    full_join(pond, by = "a01") %>%
    mutate(agri_hh = as.integer(pond %in% 1 | agri_control %in% 1)) %>%
    inner(wts, "a01") %>%
    filter(hh_type != 1) %>%                               # drop the FTF booster
    filter(agri_hh == 1) %>%
    mutate(pond = ifelse(is.na(pond), 0, pond)) %>%
    transmute(hhid = norm_id(a01), weight = as.numeric(hhweight),
              agri_hh, pond = as.numeric(pond))
}

frame_2011 <- function() {
  # Stata sets agri_control = 1 for every household appearing in the h1 module.
  agri <- read_stata(file.path(PATHS$r12, "011_mod_h1_male.dta"), "a01") %>%
    distinct(a01) %>% mutate(agri_control = 1)

  pond <- read_stata(file.path(PATHS$r12, "026_mod_l1_male.dta"), c("a01", "pondid")) %>%
    filter(pondid != 999) %>%
    group_by(a01) %>% summarise(pond = 1, .groups = "drop")

  sample_type <- read_stata(file.path(PATHS$r12, "001_mod_a_male.dta"),
                            c("a01", "Sample_type"))
  wts <- read_stata(file.path(PATHS$r12, "BIHS_FTF baseline sampling weights.dta"),
                    c("a01", "hhweight"))

  agri %>%
    full_join(pond, by = "a01") %>%
    mutate(agri_hh = as.integer(pond %in% 1 | agri_control %in% 1)) %>%
    left_join(sample_type, by = "a01") %>%
    filter(is.na(Sample_type) | Sample_type != 1) %>%      # drop the FTF booster
    inner(wts, "a01") %>%
    filter(agri_hh == 1) %>%
    mutate(pond = ifelse(is.na(pond), 0, pond)) %>%
    transmute(hhid = norm_id(a01), weight = as.numeric(hhweight),
              agri_hh, pond = as.numeric(pond))
}

build_frames <- function() {
  list("2011" = frame_2011(), "2015" = frame_2015(),
       "2019" = frame_2019(), "2024" = frame_2024())
}
