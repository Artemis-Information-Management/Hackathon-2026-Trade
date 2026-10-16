# Trade Hackathon 2026 · Luxembourg

**Interactive dashboard of Luxembourg's external trade in goods** — who Luxembourg trades with, what it buys and sells, how this changes over time, and which EU countries have a similar trade profile.

Built for the **STATEC Hackathon 2026** (14–16 October 2026, GovTech Lab Luxembourg), challenge *"Luxembourg's external trade data"*, by team **Dat'Artemis**.

One R Markdown file produces one self-contained HTML page. No server, no database: open the HTML in a browser and everything works offline (except the fonts and the map background).

🇫🇷 *Version française plus bas : [Lire en français](#trade-cockpit--luxembourg-fr)*

---

## Contents

1. [What the cockpit shows](#1-what-the-cockpit-shows)
2. [Quick start](#2-quick-start)
3. [Repository structure](#3-repository-structure)
4. [Data](#4-data)
5. [How the page works](#5-how-the-page-works)
6. [Methods, in plain words](#6-methods-in-plain-words)
7. [Reuse: another year, another country](#7-reuse-another-year-another-country)
8. [Known limits](#8-known-limits)
9. [Team](#9-team)
10. [Licence](#10-licence)

---

## 1. What the cockpit shows

The page has five views, selected in the left menu. Every view can be switched between **imports** and **exports**.

| View | What you see | Challenge question it answers |
|---|---|---|
| **Summary** | Key figures of the year, top 5 product families imported and exported (click a family to see what is inside it), trade balance over time and by product, "dependence" charts (big, concentrated and unbalanced flows), the four neighbours (BE, FR, NL, DE) and the history of their top 5 products | Main categories of goods · how they changed over time · trade with the neighbours |
| **Overview** | World map of partners (click a country to see its yearly evolution), top 20 partners, trade flows (origins → Luxembourg → destinations), trade balance by partner, partner × product heatmap | Main trading partners · how they evolved over time · partners of a given product |
| **Product** | For each product family: how many partners are needed to reach X % of the flow (slider), cumulative curve, value vs concentration | Partners of a given product · how concentrated the supply is |
| **Country** | One partner (or a region such as EU, Asia…): imports, exports, balance, yearly evolution, main goods bought and sold, product concentration, members of the region | Main goods traded with a given partner |
| **Trade twins** | Which EU countries buy (or sell) the same mix of products as Luxembourg: similarity map, score taken apart product by product, top 5 side by side, "pick a product" | Luxembourg compared with other countries |

The page covers **all years available** (1999 to the latest year in the data). The year shown in the Summary, Overview, Product and Country views is a parameter of the file; the Trade twins view has its own year slider.

---

## 2. Quick start

**You need:** R (≥ 4.2) and RStudio (RStudio brings *pandoc*, which R Markdown needs). The R packages are installed automatically the first time you knit (`tidyverse`, `plotly`, `crosstalk`, `htmltools`, `bslib`, `DT`, `jsonlite`, `readxl`, `knitr`, `rmarkdown`).

```text
1. Clone or download this repository (all files stay together in one folder).
2. Open Trade_Hackathon_2026.Rproj in RStudio: this makes the repository folder the working directory,
   so the data files are found by their name.
3. Open Dashboard_Hackathon_2026.Rmd and press  Knit.
```

Or from the R console, from the repository folder:

```r
rmarkdown::render("Dashboard_Hackathon_2026.Rmd")                                  # year 2025 (default)
rmarkdown::render("Dashboard_Hackathon_2026.Rmd", params = list(year = 2019),
                  output_file = "Dashboard_Hackathon_LU_2019.html")
```

The result is **one HTML file (about 22 MB)** next to the `.Rmd`. Open it in any modern browser (Chrome, Edge, Firefox). Knitting takes 1–2 minutes.

**No R installed?** Open `Dashboard_Hackathon_2026.html`: it is the knitted page, ready to use.

---

## 3. Repository structure

All files are at the root of the repository, next to each other, so that the `.Rmd` finds them by their name.

```text
Hackathon-2026-Trade/
├── README.md                           this file (EN + FR)
├── Trade_Hackathon_2026.Rproj          RStudio project: open it first
│
│   The page
├── Dashboard_Hackathon_2026.Rmd        ALL the code: data preparation, charts, page layout, interactivity (current version)
├── Dashboard_Hackathon_2026.html       the knitted page, ready to open
│
│   The data
├── final_df.rds                        Luxembourg × all partner countries, 1999–2025
├── eu27_df.rds                         the other 26 EU countries × World (Trade twins view)
├── code_agg.xlsx                       Eurostat list of partner aggregates = the "Regions"
├── 2025_4digits.json                   4-digit product detail for 2025 (Summary drill-down)
│
│   Scripts
├── Create_database_and_HTML_output.R   calls eu27_df.R and final_df.R to build the R Markdown and the databases.

```

`.Rproj.user`, `.RDataTmp` and `.Rhistory` are RStudio working files; they can be ignored.

Everything the page needs is in **one** `.Rmd` file, on purpose: copy the file, add the data, knit.

---

## 4. Data

All data come from **Eurostat Comext**, dataset **[ds-045409] EU trade since 1988 by HS2-4-6 and CN8**, indicator *VALUE_IN_EUROS*, annual frequency. Source: Eurostat, © European Union — free reuse allowed provided the source is acknowledged ([Eurostat copyright notice](https://ec.europa.eu/eurostat/en/help/copyright-notice)). Extraction date: 14 October 2026.

Products are **HS2 chapters** and **HS4 chapters**: the goods are grouped into 97 families following the international customs classification (Harmonized System, 2-digit level): 87 = vehicles, 84 = machinery, 30 = pharmaceuticals, 27 = mineral fuels, and so on. `TOTAL` = all products.

### 4.1 `final_df.rds` — required

| | |
|---|---|
| Content | reporter = **Luxembourg (LU)** · partner = **all** partner countries and the *World* aggregate · product = `TOTAL` + the 97 HS2 chapters · flow = 1 (import) and 2 (export) · annual, **1999 → 2025** |
| Size | 262 231 rows, 257 partner codes |
| Columns used by the page | `PRODUCT_CODE`, `PRODUCT_LABEL`, `FLOW_LABEL` (IMPORT / EXPORT), `PARTNER_CODE`, `PARTNER_LABEL`, `TIME` (year), `VALUE_IN_EUROS` |
| Other columns (ignored) | `FLOW_CODE`, `INDICATOR_CODE` |

It is built by `final_df.R` (run by `Create_database_and_HTML_output.R`). The `.Rmd` reads it with `readRDS()`; if a `final_df` table is already in memory (for instance right after running `final_df.R`), it uses that one instead.

### 4.2 `eu27_df.rds` — for the Trade twins view

| | |
|---|---|
| Content | reporter = **each of the other 26 EU countries** · partner = `WORLD` only · product = `TOTAL` + HS2 chapters · both flows · annual, 1999 → 2025 |
| Size | 136 775 rows |
| Columns | the same as `final_df.rds` plus `REPORTER_CODE` and `REPORTER_LABEL` |

Same Comext dataset, same selection, with the reporter changed. It is built by `eu27_df.R` (run by `Create_database_and_HTML_output.R`), which binds the tables of the 26 countries with the same column names. Without this file the page still knits; the Trade twins view shows a notice instead of the charts.

### 4.3 `code_agg.xlsx` — for the "Regions" of the Country view

Eurostat's list of **partner aggregates** (EU27, euro area, EFTA, Asia, Africa, OPEC…): one sheet with the columns `CODE`, `Label - English` and `Note (EN only)`, where the note lists the member countries of each aggregate (for example *"This aggregate covers following countries: BE, BG, CZ, …"*). It comes from the Comext metadata of the *PARTNER* dimension (the GEO list). The `.Rmd` reads the three columns by their first word (`code`, `label`, `note`) and turns each note into a list of country codes. Without this file the page still knits; the Country view offers countries only.

### 4.4 `2025_4digits.json` — a finer look at 2025, for the Summary drill-down

The cockpit works with **97 product families** (HS2). This file goes one level deeper: the same goods split into about **1 370 sub-families** (HS4, 4-digit codes). For example family 87 *Vehicles* becomes 8703 *Cars*, 8708 *Car parts*, 8711 *Motorcycles*, and so on.

It is the **raw answer of the Eurostat API**, saved as is, for one selection only: reporter = Luxembourg, partner = World, year = **2025**, imports and exports, value in euros.

The Summary view uses it for the **drill-down of the top 5**: click a family in the top 5 chart and the page shows the sub-families that make it up (those weighing at least 1 % of the family, 8 at most — parameter `hs4_n` — the rest folded into "Other"); a *Back* button returns to the top 5. Only the year of the file is covered: for another year, download the same selection for that year and set `hs4_path`. With `hs4_path = ""`, or if the file is missing, the page knits without the drill-down.

The format (called *JSON-stat*) is not meant to be read by eye: all the numbers sit in one long list, and a `dimension` block says what each position means. The `.Rmd` has its own reader (chunk `hs4-drill`). To turn the file into a normal table in R outside the page:

```r
js    <- jsonlite::fromJSON("2025_4digits.json", simplifyVector = FALSE)
ids   <- unlist(js$id)
codes <- lapply(ids, function(d) { i <- js$dimension[[d]]$category$index; names(i)[order(unlist(i))] })
names(codes) <- ids
grid  <- expand.grid(rev(codes), stringsAsFactors = FALSE)[, ids]
vals  <- rep(NA_real_, prod(unlist(js$size)))
vals[as.integer(names(js$value)) + 1] <- unlist(js$value)
grid$value <- vals
grid$product_label <- unlist(js$dimension$product$category$label)[grid$product]
df <- subset(grid, !is.na(value) & indicators == "VALUE_IN_EUROS",
             select = c(product, product_label, flow, time, value))
df$flow <- ifelse(df$flow == "1", "IMPORT", "EXPORT")
```

`df` then has one row per sub-family and flow (about 2 400 rows): `product` (4-digit code), `product_label`, `flow`, `time`, `value` in euros. In 2025 the largest lines are 8703 *Cars* (imports), 2710 *Petroleum oils* (imports), 8517 *Telephones and network equipment* (both flows) and 7216 *Steel sections* (exports).

### 4.5 What is dropped on purpose

* Partner codes that are not countries (stores and provisions, confidential trade, "not specified"…) are excluded from the charts. The sidebar lists them under *non-country codes excluded*.
* Chapter 99 (goods not classified elsewhere) is left out of the Summary top 5 and of the Trade twins (parameter `excluded_products`).
* The latest year is usually **incomplete** (data up to the last month published by Eurostat).

---

## 5. How the page works

The whole analysis runs **once, when you knit**. R computes every table for every product × flow (and, for the twins, every year) and stores them in the HTML as JSON. A small JavaScript, written at the end of the `.Rmd`, then **swaps the data of the plotly charts** when you use the menu, the product list, the year slider, click a country on the map or a family in the top 5. This is why the page is a plain file that works without R, Shiny or a server.

Libraries: [plotly](https://plotly.com/r/) for the charts, [crosstalk](https://rstudio.github.io/crosstalk/) for the link between the map and the "annual evolution" chart, [bslib](https://rstudio.github.io/bslib/) for the Bootstrap 5 theme, the [tidyverse](https://www.tidyverse.org/) for the data work.

Only two things are loaded from the internet when the page is opened: the *Poppins* font (Google Fonts) and the world map outlines (plotly CDN). Without internet the page still works, with the default font and without the map backgrounds. To knit a fully offline page, host the topojson files yourself and set `params$topojson_url`.

---

## 6. Methods, in plain words

* **Share of a partner** = value traded with that partner ÷ value traded with all partner countries, for one product and one flow. Shares add up to 100 %.
* **Partners needed** (Product view) = how many partners, taken from the largest, are needed to reach the chosen share of the flow (90 % by default). A small number means the product depends on few countries.
* **HHI** (Herfindahl–Hirschman index) = sum of the squared partner shares. 1 = a single partner; 0.25 = one partner at 50 %, or four equal partners. The higher, the more concentrated.
* **Dependence charts** (Summary view): each product family is placed by its weight in total trade (x), its partner concentration HHI (y) and its net dependence (bubble size: the share of the imports that is not covered by exports of the same products). A product is flagged on three criteria — weight ≥ 2 %, HHI ≥ 0.25, dependence ≥ 50 % — and classed *Critical* (3 flags), *High* (2), *Moderate* (1) or *Low* (0).
* **Drill-down of the top 5** (Summary view): inside a family, each sub-family is shown with its share of the family (the bars add up to 100 % of the family) and, on hover, its share of the total flow.
* **Trade twins — similarity score** (Finger–Kreinin index). For each product family, take its share in Luxembourg's trade and in the other country's trade, and keep the smaller of the two. Add these shared shares over all families: 0 = nothing in common, 100 = identical mix. A score of 77 means that 77 % of the other country's imports (or exports) follow the same product mix as Luxembourg's. Because the score is a sum, it can be taken apart product by product: that is what the butterfly chart and the heatmap show. *Finger, J.M. & Kreinin, M.E. (1979), "A measure of export similarity and its possible uses", Economic Journal 89.*

---

## 7. Reuse: another year, another country

Everything adjustable is in the `params` block at the top of the `.Rmd`:

| Parameter | Default | Meaning |
|---|---|---|
| `year` | 2025 | year of the Summary, Overview, Product and Country views |
| `reporter`, `reporter_code_twins` | Luxembourg, LU | name and code of the country studied |
| `data_path`, `data_eu`, `agg_path`, `hs4_path` | the four data files of section 4 | where the data are (file names, relative to the working directory) |
| `hs4_n` | 8 | sub-families shown in the drill-down of a family |
| `neighbours` | BE, FR, NL, DE | the "neighbouring countries" block of the Summary |
| `top_n`, `heat_n` | 20, 30 | partners shown in the bar charts and the heatmap |
| `threshold` | 0.9 | default concentration threshold (the slider changes it in the page) |
| `evo_default` | BE | partner selected when the Overview opens |
| `twins_rows`, `twins_countries` | 10, 12 | product families and countries shown in the Trade twins |
| `excluded_products` | 99 | chapters left out of the top 5 and the twins |
| `topojson_url` | "" | your own copy of the map files, for an offline page |

You can set them without editing the file:

```r
rmarkdown::render("Dashboard_Hackathon_2026.Rmd",
                  params = list(year = 2023, neighbours = c("BE", "FR", "DE")))
```

**Another country.** Run `final_df.R` with that reporter to get its `final_df.rds`, set `reporter`, `reporter_code_twins` and `neighbours`, and knit. The code never assumes Luxembourg except through these parameters. For the Trade twins, `eu27_df.rds` must contain the *other* countries: remove the new country from it and add Luxembourg if you want it among the twins.

**A newer year.** Re-run `final_df.R` and `eu27_df.R` (or `Create_database_and_HTML_output.R`, which runs both) to refresh the data files, set `year`, knit. For the drill-down, also download the 4-digit file of the new year and set `hs4_path`.

---

## 8. Known limits

* HS2 is the product level of all the views. The only finer detail is the drill-down of the Summary top 5 (4 digits, one year). The Comext dataset also has HS6 and CN8.
* Monthly data (seasonality) are not covered.
* Figures are declared by Luxembourg. The same flow declared by the partner country can differ a little (transport costs, timing, goods routed through a third country).

---

## 9. Our pluridisciplinary Team

**Dat'Artemis** — Artemis Information Management, Luxembourg

Quentin Barthel · Quentin Schmidt · Kevin Alati · Sandrine Herbeth · Mathieu Scheffer

For questions and suggestions: please open an issue on this repository.

---

## 10. Licence

* **Code**: [European Union Public Licence 1.2](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12) (SPDX: `EUPL-1.2`), see `LICENSE`.
* **Data**: Eurostat, © European Union, reuse allowed with acknowledgement of the source. The data files in this repository (`.rds`, `.xlsx`, `.json`) keep that licence; they are not covered by the EUPL.
* **Third-party libraries**: plotly.js (MIT), Bootstrap (MIT), DataTables (MIT), R packages under their own licences.

---
---

<a id="trade-cockpit--luxembourg-fr"></a>
# Trade Hackathon 2026 · Luxembourg (FR)

**Tableau de bord interactif du commerce extérieur de biens du Luxembourg** : avec qui le Luxembourg échange, ce qu'il achète et ce qu'il vend, comment cela évolue dans le temps, et quels pays de l'UE ont un profil commercial proche du sien.

Réalisé pour le **STATEC Hackathon 2026** (14–16 octobre 2026, GovTech Lab Luxembourg), défi *« Luxembourg's external trade data »*, par l'équipe **Dat'Artemis**.

Un seul fichier R Markdown produit une seule page HTML autonome. Pas de serveur, pas de base de données : on ouvre le HTML dans un navigateur et tout fonctionne, même hors ligne (sauf la police et le fond de carte).

---

## Sommaire

1. [Ce que montre le cockpit](#1-ce-que-montre-le-cockpit)
2. [Démarrage rapide](#2-démarrage-rapide)
3. [Structure du dépôt](#3-structure-du-dépôt)
4. [Données](#4-données)
5. [Comment la page fonctionne](#5-comment-la-page-fonctionne)
6. [Les méthodes, en mots simples](#6-les-méthodes-en-mots-simples)
7. [Réutiliser : une autre année, un autre pays](#7-réutiliser--une-autre-année-un-autre-pays)
8. [Limites connues](#8-limites-connues)
9. [Équipe](#9-équipe)
10. [Licence](#10-licence-1)

---

## 1. Ce que montre le cockpit

La page a cinq vues, choisies dans le menu de gauche. Chaque vue se consulte en **imports** ou en **exports**.

| Vue | Ce qu'on y voit | Question du défi à laquelle elle répond |
|---|---|---|
| **Summary** | Chiffres clés de l'année, top 5 des familles de produits importées et exportées (cliquer une famille montre ce qu'elle contient), balance commerciale dans le temps et par produit, graphiques de « dépendance » (flux importants, concentrés et déséquilibrés), les quatre voisins (BE, FR, NL, DE) et l'historique de leur top 5 | Principales catégories de biens · leur évolution · le commerce avec les voisins |
| **Overview** | Carte du monde des partenaires (cliquer un pays affiche son évolution annuelle), top 20 des partenaires, flux commerciaux (origines → Luxembourg → destinations), balance par partenaire, carte de chaleur partenaire × produit | Principaux partenaires · leur évolution · partenaires d'un produit donné |
| **Product** | Pour chaque famille de produits : combien de partenaires il faut pour atteindre X % du flux (curseur), courbe cumulée, valeur contre concentration | Partenaires d'un produit · concentration de l'approvisionnement |
| **Country** | Un partenaire (ou une région : UE, Asie…) : imports, exports, balance, évolution annuelle, principaux biens achetés et vendus, concentration par produit, membres de la région | Principaux biens échangés avec un partenaire donné |
| **Trade twins** | Quels pays de l'UE achètent (ou vendent) le même mélange de produits que le Luxembourg : carte de similarité, score décomposé produit par produit, top 5 côte à côte, « choisir un produit » | Le Luxembourg comparé aux autres pays |

La page couvre **toutes les années disponibles** (1999 jusqu'à la dernière année des données). L'année affichée dans Summary, Overview, Product et Country est un paramètre du fichier ; la vue Trade twins a son propre curseur d'année.

---

## 2. Démarrage rapide

**Il faut :** R (≥ 4.2) et RStudio (RStudio fournit *pandoc*, nécessaire à R Markdown). Les packages R s'installent tout seuls au premier knit (`tidyverse`, `plotly`, `crosstalk`, `htmltools`, `bslib`, `DT`, `jsonlite`, `readxl`, `knitr`, `rmarkdown`).

```text
1. Cloner ou télécharger ce dépôt (tous les fichiers restent ensemble dans un seul dossier).
2. Ouvrir Trade_Hackathon_2026.Rproj dans RStudio : le dossier du dépôt devient le répertoire de
   travail, et les fichiers de données sont trouvés par leur nom.
3. Ouvrir Dashboard_Hackathon_2026.Rmd et cliquer sur  Knit.
```

Ou depuis la console R, dans le dossier du dépôt :

```r
rmarkdown::render("Dashboard_Hackathon_2026.Rmd")                                  # année 2025 (par défaut)
rmarkdown::render("Dashboard_Hackathon_2026.Rmd", params = list(year = 2019),
                  output_file = "Dashboard_Hackathon_LU_2019.html")
```

Le résultat est **un fichier HTML (environ 22 Mo)** à côté du `.Rmd`. Il s'ouvre dans n'importe quel navigateur récent (Chrome, Edge, Firefox). Le knit prend 1 à 2 minutes.

**Pas de R installé ?** Ouvrir `Dashboard_Hackathon_2026.html` : c'est la page déjà produite, prête à l'emploi.

---

## 3. Structure du dépôt

Tous les fichiers sont à la racine du dépôt, les uns à côté des autres, pour que le `.Rmd` les trouve par leur nom.

```text
Hackathon-2026-Trade/
├── README.md                        ce fichier (EN + FR)
├── Trade_Hackathon_2026.Rproj       projet RStudio : à ouvrir en premier
│
│   La page
├── Dashboard_Hackathon_2026.Rmd         TOUT le code : préparation des données, graphiques, mise en page, interactivité (version actuelle)
├── Dashboard_Hackathon_2026.html        la page produite, prête à ouvrir
│
│   Les données
├── final_df.rds                     Luxembourg × tous les pays partenaires, 1999–2025
├── eu27_df.rds                      les 26 autres pays de l'UE × Monde (vue Trade twins)
├── code_agg.xlsx                    liste Eurostat des agrégats de partenaires = les « Regions »
├── 2025_4digits.json                détail produit à 4 chiffres pour 2025 (zoom de la vue Summary)
│
│   Scripts
├── Create_database_and_HTML_output.R                         appelle eu27_df.R et final_df.R pour construire les bases de données et le R Markdown.

```

`.Rproj.user`, `.RDataTmp` et `.Rhistory` sont des fichiers de travail de RStudio ; on peut les ignorer.

Tout ce dont la page a besoin tient dans **un seul** fichier `.Rmd`, volontairement : on copie le fichier, on ajoute les données, on knit.

---

## 4. Données

Toutes les données viennent d'**Eurostat Comext**, jeu de données **[ds-045409] EU trade since 1988 by HS2-4-6 and CN8**, indicateur *VALUE_IN_EUROS*, fréquence annuelle. Source : Eurostat, © Union européenne — réutilisation libre à condition de citer la source ([avis de droit d'auteur Eurostat](https://ec.europa.eu/eurostat/en/help/copyright-notice)). Date d'extraction : 14 octobre 2026.

Les produits sont des **chapitres HS2** et **chapitres HS4** : les marchandises sont regroupées en 97 familles selon la nomenclature douanière internationale (Système harmonisé, niveau à 2 chiffres) : 87 = véhicules, 84 = machines, 30 = produits pharmaceutiques, 27 = combustibles minéraux, etc. `TOTAL` = tous les produits.

### 4.1 `final_df.rds` — obligatoire

| | |
|---|---|
| Contenu | déclarant (reporter) = **Luxembourg (LU)** · partenaire = **tous** les pays partenaires et l'agrégat *World* · produit = `TOTAL` + les 97 chapitres HS2 · flux = 1 (import) et 2 (export) · annuel, **1999 → 2025** |
| Taille | 262 231 lignes, 257 codes partenaires |
| Colonnes utilisées par la page | `PRODUCT_CODE`, `PRODUCT_LABEL`, `FLOW_LABEL` (IMPORT / EXPORT), `PARTNER_CODE`, `PARTNER_LABEL`, `TIME` (année), `VALUE_IN_EUROS` |
| Autres colonnes (ignorées) | `FLOW_CODE`, `INDICATOR_CODE` |

Il est construit par `final_df.R` (lancé par `Create_database_and_HTML_output.R`). Le `.Rmd` le lit avec `readRDS()` ; si une table `final_df` est déjà en mémoire (par exemple juste après avoir lancé `final_df.R`), il utilise celle-là.

### 4.2 `eu27_df.rds` — pour la vue Trade twins

| | |
|---|---|
| Contenu | déclarant = **chacun des 26 autres pays de l'UE** · partenaire = `WORLD` seulement · produit = `TOTAL` + chapitres HS2 · les deux flux · annuel, 1999 → 2025 |
| Taille | 136 775 lignes |
| Colonnes | les mêmes que `final_df.rds` plus `REPORTER_CODE` et `REPORTER_LABEL` |

Même jeu Comext, même sélection, en changeant le déclarant. Il est construit par `eu27_df.R` (lancé par `Create_database_and_HTML_output.R`), qui empile les tables des 26 pays avec les mêmes noms de colonnes. Sans ce fichier la page se génère quand même ; la vue Trade twins affiche un message à la place des graphiques.

### 4.3 `code_agg.xlsx` — pour les « Regions » de la vue Country

La liste Eurostat des **agrégats de partenaires** (UE27, zone euro, AELE, Asie, Afrique, OPEP…) : une feuille avec les colonnes `CODE`, `Label - English` et `Note (EN only)`, où la note donne les pays membres de chaque agrégat (par exemple *« This aggregate covers following countries: BE, BG, CZ, … »*). Elle vient des métadonnées Comext de la dimension *PARTNER* (la liste GEO). Le `.Rmd` reconnaît les trois colonnes par leur premier mot (`code`, `label`, `note`) et transforme chaque note en liste de codes pays. Sans ce fichier la page se génère quand même ; la vue Country ne propose que des pays.

### 4.4 `2025_4digits.json` — un regard plus fin sur 2025, pour le zoom de la vue Summary

Le cockpit travaille avec **97 familles de produits** (HS2). Ce fichier descend d'un niveau : les mêmes marchandises découpées en environ **1 370 sous-familles** (HS4, codes à 4 chiffres). Par exemple, la famille 87 *Véhicules* devient 8703 *Voitures*, 8708 *Pièces de voitures*, 8711 *Motos*, etc.

C'est la **réponse brute de l'API Eurostat**, enregistrée telle quelle, pour une seule sélection : déclarant = Luxembourg, partenaire = Monde, année = **2025**, imports et exports, valeur en euros.

La vue Summary s'en sert pour le **zoom du top 5** : on clique une famille dans le graphique du top 5 et la page montre les sous-familles qui la composent (celles qui pèsent au moins 1 % de la famille, 8 au plus — paramètre `hs4_n` — le reste regroupé dans « Other ») ; un bouton *Back* ramène au top 5. Seule l'année du fichier est couverte : pour une autre année, télécharger la même sélection pour cette année et renseigner `hs4_path`. Avec `hs4_path = ""`, ou si le fichier manque, la page se génère sans le zoom.

Le format (appelé *JSON-stat*) n'est pas fait pour être lu à l'œil : tous les chiffres sont dans une seule longue liste, et un bloc `dimension` dit à quoi correspond chaque position. Le `.Rmd` a son propre lecteur (bloc `hs4-drill`). Pour en faire un tableau normal dans R, en dehors de la page :

```r
js    <- jsonlite::fromJSON("2025_4digits.json", simplifyVector = FALSE)
ids   <- unlist(js$id)
codes <- lapply(ids, function(d) { i <- js$dimension[[d]]$category$index; names(i)[order(unlist(i))] })
names(codes) <- ids
grid  <- expand.grid(rev(codes), stringsAsFactors = FALSE)[, ids]
vals  <- rep(NA_real_, prod(unlist(js$size)))
vals[as.integer(names(js$value)) + 1] <- unlist(js$value)
grid$value <- vals
grid$product_label <- unlist(js$dimension$product$category$label)[grid$product]
df <- subset(grid, !is.na(value) & indicators == "VALUE_IN_EUROS",
             select = c(product, product_label, flow, time, value))
df$flow <- ifelse(df$flow == "1", "IMPORT", "EXPORT")
```

`df` contient alors une ligne par sous-famille et par flux (environ 2 400 lignes) : `product` (code à 4 chiffres), `product_label`, `flow`, `time`, `value` en euros. En 2025, les plus grosses lignes sont 8703 *Voitures* (imports), 2710 *Huiles de pétrole* (imports), 8517 *Téléphones et équipements réseau* (les deux flux) et 7216 *Profilés en acier* (exports).

### 4.5 Ce qui est écarté volontairement

* Les codes partenaires qui ne sont pas des pays (avitaillement, commerce confidentiel, « non précisé »…) sont exclus des graphiques. Le menu latéral les liste sous *non-country codes excluded*.
* Le chapitre 99 (marchandises non classées ailleurs) est laissé hors du top 5 de la vue Summary et des Trade twins (paramètre `excluded_products`).
* La dernière année est généralement **incomplète** (données jusqu'au dernier mois publié par Eurostat).

---

## 5. Comment la page fonctionne

Toute l'analyse tourne **une seule fois, au moment du knit**. R calcule chaque table pour chaque produit × flux (et, pour les twins, chaque année) et les range dans le HTML au format JSON. Un petit JavaScript, écrit à la fin du `.Rmd`, **échange ensuite les données des graphiques plotly** quand on utilise le menu, la liste des produits, le curseur d'année, quand on clique un pays sur la carte ou une famille dans le top 5. C'est pour cela que la page est un simple fichier qui fonctionne sans R, sans Shiny et sans serveur.

Bibliothèques : [plotly](https://plotly.com/r/) pour les graphiques, [crosstalk](https://rstudio.github.io/crosstalk/) pour le lien entre la carte et le graphique « évolution annuelle », [bslib](https://rstudio.github.io/bslib/) pour le thème Bootstrap 5, le [tidyverse](https://www.tidyverse.org/) pour le travail sur les données.

Seules deux choses sont chargées depuis internet à l'ouverture de la page : la police *Poppins* (Google Fonts) et les contours de la carte du monde (CDN plotly). Sans internet la page fonctionne quand même, avec la police par défaut et sans fond de carte. Pour une page entièrement hors ligne, hébergez vous-même les fichiers topojson et renseignez `params$topojson_url`.

---

## 6. Les méthodes, en mots simples

* **Part d'un partenaire** = valeur échangée avec ce partenaire ÷ valeur échangée avec tous les pays partenaires, pour un produit et un flux. Les parts font 100 % au total.
* **Partenaires nécessaires** (vue Product) = combien de partenaires, en partant du plus gros, il faut pour atteindre la part du flux choisie (90 % par défaut). Un petit nombre veut dire que le produit dépend de peu de pays.
* **HHI** (indice de Herfindahl-Hirschman) = somme des carrés des parts des partenaires. 1 = un seul partenaire ; 0,25 = un partenaire à 50 %, ou quatre partenaires égaux. Plus il est élevé, plus le flux est concentré.
* **Graphiques de dépendance** (vue Summary) : chaque famille de produits est placée selon son poids dans le commerce total (x), la concentration de ses partenaires HHI (y) et sa dépendance nette (taille de la bulle : la part des imports qui n'est pas couverte par des exports des mêmes produits). Un produit reçoit un drapeau par critère atteint — poids ≥ 2 %, HHI ≥ 0,25, dépendance ≥ 50 % — et est classé *Critical* (3 drapeaux), *High* (2), *Moderate* (1) ou *Low* (0).
* **Zoom du top 5** (vue Summary) : à l'intérieur d'une famille, chaque sous-famille est montrée avec sa part de la famille (les barres font 100 % de la famille) et, au survol, sa part du flux total.
* **Trade twins — score de similarité** (indice de Finger-Kreinin). Pour chaque famille de produits, on prend sa part dans le commerce du Luxembourg et dans celui de l'autre pays, et on garde la plus petite des deux. On additionne ces parts communes sur toutes les familles : 0 = rien en commun, 100 = mélange identique. Un score de 77 veut dire que 77 % des imports (ou des exports) de l'autre pays suivent le même mélange de produits que ceux du Luxembourg. Comme le score est une somme, on peut le décomposer produit par produit : c'est ce que montrent le graphique en papillon et la carte de chaleur. *Finger, J.M. & Kreinin, M.E. (1979), « A measure of export similarity and its possible uses », Economic Journal 89.*

---

## 7. Réutiliser : une autre année, un autre pays

Tout ce qui se règle est dans le bloc `params` en tête du `.Rmd` :

| Paramètre | Défaut | Sens |
|---|---|---|
| `year` | 2025 | année des vues Summary, Overview, Product et Country |
| `reporter`, `reporter_code_twins` | Luxembourg, LU | nom et code du pays étudié |
| `data_path`, `data_eu`, `agg_path`, `hs4_path` | les quatre fichiers de données de la section 4 | où sont les données (noms de fichiers, relatifs au répertoire de travail) |
| `hs4_n` | 8 | sous-familles montrées dans le zoom d'une famille |
| `neighbours` | BE, FR, NL, DE | le bloc « pays voisins » de la vue Summary |
| `top_n`, `heat_n` | 20, 30 | partenaires affichés dans les barres et la carte de chaleur |
| `threshold` | 0.9 | seuil de concentration par défaut (le curseur le change dans la page) |
| `evo_default` | BE | partenaire sélectionné à l'ouverture de la vue Overview |
| `twins_rows`, `twins_countries` | 10, 12 | familles de produits et pays affichés dans les Trade twins |
| `excluded_products` | 99 | chapitres écartés du top 5 et des twins |
| `topojson_url` | "" | votre propre copie des fichiers de carte, pour une page hors ligne |

On peut les changer sans modifier le fichier :

```r
rmarkdown::render("Dashboard_Hackathon_2026.Rmd",
                  params = list(year = 2023, neighbours = c("BE", "FR", "DE")))
```

**Un autre pays.** Lancer `final_df.R` avec ce déclarant pour obtenir son `final_df.rds`, renseigner `reporter`, `reporter_code_twins` et `neighbours`, et knitter. Le code ne suppose jamais le Luxembourg autrement que par ces paramètres. Pour les Trade twins, `eu27_df.rds` doit contenir les *autres* pays : retirez-en le nouveau pays et ajoutez le Luxembourg si vous le voulez parmi les twins.

**Une année plus récente.** Relancer `final_df.R` et `eu27_df.R` (ou `Create_database_and_HTML_output.R`, qui lance les deux) pour rafraîchir les fichiers de données, régler `year`, knitter. Pour le zoom, télécharger aussi le fichier à 4 chiffres de la nouvelle année et renseigner `hs4_path`.

---

## 8. Limites connues

* HS2 est le niveau de produit de toutes les vues. Le seul détail plus fin est le zoom du top 5 de la vue Summary (4 chiffres, une année). Le jeu Comext contient aussi HS6 et CN8.
* Les données mensuelles (saisonnalité) ne sont pas traitées.
* Les chiffres sont ceux déclarés par le Luxembourg. Le même flux déclaré par le pays partenaire peut différer un peu (coûts de transport, calendrier, marchandises passant par un pays tiers).

---

## 9. Notre équipe pluridisciplinaire

**Dat'Artemis** — Artemis Information Management, Luxembourg

Quentin Barthel · Quentin Schmidt · Kevin Alati · Sandrine Herbeth · Mathieu Scheffer

Pour toute question ou suggestion : ouvrir une *issue* sur ce dépôt.

---

## 10. Licence

* **Code** : [Licence publique de l'Union européenne 1.2](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12) (SPDX : `EUPL-1.2`), voir `LICENSE`.
* **Données** : Eurostat, © Union européenne, réutilisation autorisée avec mention de la source. Les fichiers de données de ce dépôt (`.rds`, `.xlsx`, `.json`) gardent cette licence ; ils ne sont pas couverts par l'EUPL.
* **Bibliothèques tierces** : plotly.js (MIT), Bootstrap (MIT), DataTables (MIT), packages R sous leurs propres licences.
