# =============================================================================
# GEO.xlsx : éclatement des agrégats géographiques en pays individuels
# Résultat : data.frame "geo_detail" en mémoire
#            (1 ligne = CODE x pays listé dans "Note (EN only)")
# =============================================================================

# ---- 0. Packages -------------------------------------------------------------
pkgs <- c("readxl", "dplyr", "tidyr", "stringr")
manquants <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(manquants) > 0) install.packages(manquants)
invisible(lapply(pkgs, library, character.only = TRUE))

# ---- 1. Lecture ----------------------------------------------------------------
fichier_geo <- "M:/Knowledge/TF Innovation/Hackhathon 2026/GEO/GEO.xlsx"

geo_raw <- read_excel(fichier_geo, col_types = "text")

# Repérage des colonnes par leur nom (insensible aux espaces / majuscules)
trouver_col <- function(df, motif) {
  nom <- names(df)[str_detect(str_squish(tolower(names(df))), motif)][1]
  if (is.na(nom)) stop("Colonne introuvable : ", motif)
  nom
}
col_code  <- trouver_col(geo_raw, "^code$")
col_label <- trouver_col(geo_raw, "^label - english")
col_note  <- trouver_col(geo_raw, "^note")

geo <- geo_raw |>
  transmute(CODE          = str_trim(.data[[col_code]]),
            LABEL_ENGLISH = str_trim(.data[[col_label]]),
            NOTE          = .data[[col_note]]) |>
  filter(!is.na(CODE), CODE != "")

# ---- 2. Extraction des codes pays de la note ---------------------------------
# Ex. "This aggregate covers following countries: BE, BG, CZ, ..., SE"
#     "This aggregate covers the New Member States in 2013: BG, CZ, ..."
# -> on prend le texte après le premier ":" puis on découpe sur les virgules
#    et on ne garde que les éléments qui ressemblent à un code (ex. "BE", "UK").
geo_detail <- geo |>
  mutate(LISTE = if_else(str_detect(NOTE, ":"),
                         str_remove(NOTE, "^[^:]*:"),
                         NA_character_)) |>
  separate_longer_delim(LISTE, delim = ",") |>
  mutate(COUNTRY_CODE = str_remove_all(str_trim(LISTE), "[\\s\\.;]+$"),
         COUNTRY_CODE = if_else(str_detect(COUNTRY_CODE, "^[A-Z]{2}$"),
                                COUNTRY_CODE, NA_character_)) |>
  # 1 ligne par pays ; les CODE sans liste gardent 1 ligne avec COUNTRY_CODE = NA
  group_by(CODE) |>
  filter(!is.na(COUNTRY_CODE) | all(is.na(COUNTRY_CODE))) |>
  ungroup() |>
  distinct(CODE, LABEL_ENGLISH, COUNTRY_CODE) |>
  as.data.frame()

# Pour ne garder que les CODE qui ont effectivement une liste de pays :
# geo_detail <- geo_detail[!is.na(geo_detail$COUNTRY_CODE), ]

# ---- 3. Contrôles ------------------------------------------------------------
cat("CODE lus                     :", n_distinct(geo$CODE), "\n")
cat("CODE avec une liste de pays  :",
    n_distinct(geo_detail$CODE[!is.na(geo_detail$COUNTRY_CODE)]), "\n")
cat("Lignes dans geo_detail       :", nrow(geo_detail), "\n")

# Nombre de pays par agrégat (pratique pour vérifier ex. EU27_2020 = 27)
print(geo_detail |>
        filter(!is.na(COUNTRY_CODE)) |>
        count(CODE, LABEL_ENGLISH, name = "NB_PAYS"))

# Notes contenant un ":" mais dont aucun code n'a pu être extrait (à vérifier)
a_verifier <- geo |>
  filter(str_detect(NOTE, ":"),
         !CODE %in% geo_detail$CODE[!is.na(geo_detail$COUNTRY_CODE)])
if (nrow(a_verifier) > 0) {
  warning("Notes non interprétées, à vérifier :")
  print(a_verifier)
}
