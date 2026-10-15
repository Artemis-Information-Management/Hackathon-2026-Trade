# Installer le package si nécessaire
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  install.packages("jsonlite")
}
library(jsonlite)

if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
  setwd(dirname(rstudioapi::getSourceEditorContext()$path))
}

donnees <- fromJSON("data_LU_BE.json")

# Aperçu des données
str(donnees)
head(donnees)