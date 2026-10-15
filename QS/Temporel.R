##---- Preparation ----
setwd("M:/Knowledge/TF Innovation/Hackhathon 2026/QS")

library(readxl)
library(readr)
library(dplyr)
library(tidyr)
library(vars)

DDBValeur <- read_excel("M:/Knowledge/TF Innovation/Hackhathon 2026/Trade_Hackathon_2026/QS/ds-045409__custom_23235366_spreadsheet.xlsx", 
                        sheet = "Sheet 1", na = ":", skip = 8)


DDBQuanti <- read_excel("M:/Knowledge/TF Innovation/Hackhathon 2026/Trade_Hackathon_2026/QS/ds-045409__custom_23235366_spreadsheet.xlsx", 
                        sheet = "Sheet 2", na = ":", skip = 8)


DDBValeur[[3]] <- "V"


# 3. Fusionner les trois premières colonnes
indicator <- paste(DDBValeur[[1]], DDBValeur[[2]], DDBValeur[[3]], sep = "")

DatasetV <- data.frame(
  Indicator = indicator,
  DDBValeur[, -(1:3), drop = FALSE]
)

DDBmerged <- 


fullds[-1] <- lapply(fullds[-1], as.numeric)

fullds <- fullds %>%
  rename(indicator = ...1)

View(fullds)



### 1. IMPORTER LES DONNÉES ----

donnees_brutes <- fullds

# Nommer la première colonne
names(donnees_brutes)[1] <- "SERIES"


### 2. PASSER AU FORMAT MENSUEL ----


donnees <- donnees_brutes %>%
  pivot_longer(
    cols = -SERIES,
    names_to = "DATE",
    values_to = "VALEUR"
  ) %>%
  mutate(
    DATE = as.Date(paste0(DATE, "-01")),
    VALEUR = as.numeric(VALEUR)
  ) %>%
  pivot_wider(
    names_from = SERIES,
    values_from = VALEUR
  ) %>%
  arrange(DATE)

# Vérifier les données
print(head(donnees))


### 3. CALCULER LES PRIX UNITAIRES ----


donnees <- donnees %>%
  mutate(
    PIMP = LUIMPV / LUIMPQ,
    PEXP = LUEXPV / LUEXPQ
  )

# Retirer les observations manquantes ou non positives
donnees <- donnees %>%
  filter(
    LUIMPV > 0,
    LUEXPV > 0,
    LUIMPQ > 0,
    LUEXPQ > 0,
    PIMP > 0,
    PEXP > 0
  )


### 4. CALCULER LES VARIATIONS LOGARITHMIQUES MENSUELLES ----


donnees <- donnees %>%
  arrange(DATE) %>%
  mutate(
    dPIMP = c(NA, diff(log(PIMP))),
    dPEXP = c(NA, diff(log(PEXP))),
    dQIMP = c(NA, diff(log(LUIMPQ))),
    dQEXP = c(NA, diff(log(LUEXPQ)))
  ) %>%
  drop_na(dPIMP, dPEXP, dQIMP, dQEXP)


### 5. ESTIMER LES RELATIONS PRIX-QUANTITÉ ----


# Importations
modele_import <- lm(dQIMP ~ dPIMP, data = donnees)

cat("\n=== RELATION PRIX-QUANTITÉ : IMPORTATIONS ===\n")
print(summary(modele_import))

# Exportations
modele_export <- lm(dQEXP ~ dPEXP, data = donnees)

cat("\n=== RELATION PRIX-QUANTITÉ : EXPORTATIONS ===\n")
print(summary(modele_export))


### 6. ESTIMER UN VAR POUR ÉTUDIER LES EFFETS DYNAMIQUES ----


series_var <- donnees %>%
  dplyr::select(dPIMP, dPEXP, dQIMP, dQEXP)

if (nrow(series_var) < 30) {
  stop("Il faut davantage d'observations pour estimer ce VAR.")
}

# Sélection automatique du nombre de retards
choix_retards <- VARselect(
  series_var,
  lag.max = min(6, floor(nrow(series_var) / 5)),
  type = "const"
)

print(choix_retards$selection)

p <- as.integer(choix_retards$selection["AIC(n)"])

modele_var <- VAR(
  series_var,
  p = p,
  type = "const"
)

cat("\n=== RÉSULTATS DU VAR ===\n")
print(summary(modele_var))

cat("\n=== RACINES DU VAR ===\n")
print(roots(modele_var))


### 7. RÉPONSES À UN CHOC DE PRIX ----


# Choc sur le prix des importations
irf_import <- irf(
  modele_var,
  impulse = "dPIMP",
  response = c("dQIMP", "dQEXP"),
  n.ahead = 12,
  cumulative = TRUE,
  boot = TRUE,
  runs = 500,
  ci = 0.95,
  plot = FALSE
)

# Choc sur le prix des exportations
irf_export <- irf(
  modele_var,
  impulse = "dPEXP",
  response = c("dQIMP", "dQEXP"),
  n.ahead = 12,
  cumulative = TRUE,
  boot = TRUE,
  runs = 500,
  ci = 0.95,
  plot = FALSE
)


### 8. EXPORTER LES RÉSULTATS ----


write_csv(donnees, "donnees_analysees.csv")

# Exporter les résultats des régressions
capture.output(
  summary(modele_import),
  file = "regression_importations.txt"
)

capture.output(
  summary(modele_export),
  file = "regression_exportations.txt"
)

# Exporter les réponses impulsionnelles
extraire_irf <- function(objet, choc) {
  do.call(rbind, lapply(names(objet$irf), function(nom) {
    data.frame(
      choc = choc,
      reponse = nom,
      mois = 0:(nrow(objet$irf[[nom]]) - 1),
      estimation = as.numeric(objet$irf[[nom]][, 1]),
      borne_inf = as.numeric(objet$Lower[[nom]][, 1]),
      borne_sup = as.numeric(objet$Upper[[nom]][, 1])
    )
  }))
}

resultats_irf <- bind_rows(
  extraire_irf(irf_import, "Choc_prix_import"),
  extraire_irf(irf_export, "Choc_prix_export")
)

write_csv(resultats_irf, "M:/Knowledge/TF Innovation/Hackhathon 2026/Trade_Hackathon_2026/QS/reponses_impulsionnelles.csv")

cat("\nAnalyse terminée. Les fichiers de résultats ont été créés.\n")


# Représentation graphique ----


### 1. ÉVOLUTION DES PRIX UNITAIRES ----


plot(
  donnees$DATE, donnees$PIMP,
  type = "l",
  xlab = "Mois",
  ylab = "Prix unitaire",
  main = "Prix unitaire des importations"
)

plot(
  donnees$DATE, donnees$PEXP,
  type = "l",
  xlab = "Mois",
  ylab = "Prix unitaire",
  main = "Prix unitaire des exportations"
)


### 2. ÉVOLUTION DES QUANTITÉS ----


plot(
  donnees$DATE, donnees$LUIMPQ,
  type = "l",
  xlab = "Mois",
  ylab = "Quantité",
  main = "Quantités importées"
)

plot(
  donnees$DATE, donnees$LUEXPQ,
  type = "l",
  xlab = "Mois",
  ylab = "Quantité",
  main = "Quantités exportées"
)


### 3. RELATION ENTRE PRIX ET QUANTITÉS ----


plot(
  donnees$dPIMP, donnees$dQIMP,
  xlab = "Variation logarithmique du prix importé",
  ylab = "Variation logarithmique de la quantité importée",
  main = "Prix et quantités importées",
  pch = 16
)
abline(modele_import, lwd = 2)

plot(
  donnees$dPEXP, donnees$dQEXP,
  xlab = "Variation logarithmique du prix exporté",
  ylab = "Variation logarithmique de la quantité exportée",
