library(tidyverse)
library(rmarkdown)

# Create final_df.rds data source which will contain LU annual data for 1998-2025 years for all partners and all products
source("final_df.R", encoding = "UTF-8")

# Create eu27_df.rds data source which will contain for LU reporting country the data for EU 27 partners countries
# since 1999, for all 2-digits products
source("eu27_df.R", encoding = "UTF-8")

# Call rmarkdown - output HTML format
rmarkdown::render("Dashboard_Hackathon_2026.Rmd", envir = globalenv())