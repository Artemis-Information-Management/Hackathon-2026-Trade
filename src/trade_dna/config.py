"""Project-wide constants: paths, country codes, dataset codes.

Keep everything that might need tweaking during the hackathon here,
so nobody has to hunt through the code to change a year or a country.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
R_DIR = ROOT / "r"

# The single tidy file everything in the app reads from.
# Columns: reporter, partner, product, flow, freq, period, value
TRADE_FILE = DATA_PROCESSED / "trade_hs2.parquet"
# Optional: Luxembourg only, down to CN8, used by the "smart zoom" page.
TRADE_LU_DETAIL_FILE = DATA_PROCESSED / "trade_lu_cn8.parquet"

# --------------------------------------------------------------------------- #
# Dataset
# --------------------------------------------------------------------------- #
EUROSTAT_DATASET = "ds-045409"  # EU trade since 1988 by HS2-4-6 and CN8
FOCUS = "LU"

# Luxembourg is reported separately from Belgium only since 1999
# (before that the Eurostat series is "Belgium incl. Luxembourg").
START_YEAR = 1999

FLOW_IMPORT = "1"
FLOW_EXPORT = "2"
FLOW_LABELS = {FLOW_IMPORT: "Imports", FLOW_EXPORT: "Exports"}

# Partner codes that are aggregates, not countries. They must be excluded
# when computing concentration indices (otherwise "World" dominates).
# Check the exact codes in the Eurostat Data Browser and adjust if needed.
AGGREGATE_PARTNERS = {
    "WORLD",
    "EU27_2020",
    "EU28",
    "EU27",
    "EXT_EU27_2020",
    "INT_EU27_2020",
    "EA20",
    "QU",
    "QV",
    "QW",
}

# --------------------------------------------------------------------------- #
# Countries
# --------------------------------------------------------------------------- #
# Eurostat uses ISO2 with two quirks: EL = Greece, UK = United Kingdom.
EU27 = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
]

# Comparison set for a quick demo (small open economies + neighbours).
# Use EU27 for the full picture once the data pipeline works.
COMPARISON_DEFAULT = ["LU", "BE", "NL", "DE", "FR", "IE", "MT", "AT", "DK", "EE"]

ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "HR": "HRV", "CY": "CYP", "CZ": "CZE",
    "DK": "DNK", "EE": "EST", "FI": "FIN", "FR": "FRA", "DE": "DEU", "EL": "GRC",
    "HU": "HUN", "IE": "IRL", "IT": "ITA", "LV": "LVA", "LT": "LTU", "LU": "LUX",
    "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU", "SK": "SVK",
    "SI": "SVN", "ES": "ESP", "SE": "SWE", "UK": "GBR", "CH": "CHE", "NO": "NOR",
    "US": "USA", "CN": "CHN", "JP": "JPN", "TR": "TUR",
}

COUNTRY_NAMES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark", "EE": "Estonia",
    "FI": "Finland", "FR": "France", "DE": "Germany", "EL": "Greece",
    "HU": "Hungary", "IE": "Ireland", "IT": "Italy", "LV": "Latvia",
    "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "NL": "Netherlands",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia",
    "SI": "Slovenia", "ES": "Spain", "SE": "Sweden", "UK": "United Kingdom",
    "CH": "Switzerland", "NO": "Norway", "US": "United States", "CN": "China",
    "JP": "Japan", "TR": "Türkiye",
}

# Short labels for HS2 chapters most relevant to Luxembourg.
# Extend as needed; unknown codes fall back to the code itself.
HS2_LABELS = {
    "27": "Mineral fuels",
    "30": "Pharmaceuticals",
    "39": "Plastics",
    "40": "Rubber",
    "72": "Iron & steel",
    "73": "Articles of iron/steel",
    "76": "Aluminium",
    "84": "Machinery",
    "85": "Electrical equipment",
    "87": "Vehicles",
    "88": "Aircraft",
    "90": "Optical / medical instruments",
    "94": "Furniture",
    "22": "Beverages",
    "48": "Paper",
    "70": "Glass",
}


def country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code, code)


def hs2_label(code: str) -> str:
    return f"{code} - {HS2_LABELS[code]}" if code in HS2_LABELS else code
