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

# Two-letter codes that are NOT countries: Eurostat's special groupings
# (stores & provisions, unknown destination, confidential...). Note that
# "QA" is Qatar, a real country, so we list the special codes explicitly.
SPECIAL_PARTNERS = {"QP", "QQ", "QR", "QS", "QU", "QV", "QW", "QX", "QY", "QZ"}


def is_country_partner(codes):
    """Vectorised test on a pandas Series of partner codes: True for real countries.

    A partner counts as a country if its code has 2 letters (ISO2) and is not
    one of the special groupings. Aggregates (WORLD, EU27_2020, AFRICA...)
    have longer codes, so they are excluded without having to list them all.
    """
    return codes.str.len().eq(2) & ~codes.isin(SPECIAL_PARTNERS | AGGREGATE_PARTNERS)


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

# Short plain-English labels for the HS2 chapters (HS 2022 nomenclature).
# Unknown codes fall back to the code itself.
HS2_LABELS = {
    "01": "Live animals", "02": "Meat", "03": "Fish & seafood", "04": "Dairy, eggs, honey",
    "05": "Other animal products", "06": "Live plants & flowers", "07": "Vegetables",
    "08": "Fruit & nuts", "09": "Coffee, tea, spices", "10": "Cereals", "11": "Milling products",
    "12": "Oil seeds", "13": "Gums & resins", "14": "Other vegetable products",
    "15": "Fats & oils", "16": "Meat & fish preparations", "17": "Sugars", "18": "Cocoa & chocolate",
    "19": "Cereal & bakery preparations", "20": "Fruit & vegetable preparations",
    "21": "Misc. food preparations", "22": "Beverages", "23": "Animal feed & food residues",
    "24": "Tobacco", "25": "Salt, stone, cement", "26": "Ores & slag", "27": "Mineral fuels",
    "28": "Inorganic chemicals", "29": "Organic chemicals", "30": "Pharmaceuticals",
    "31": "Fertilisers", "32": "Dyes, paints, inks", "33": "Cosmetics & perfumes",
    "34": "Soap & waxes", "35": "Glues & proteins", "36": "Explosives & matches",
    "37": "Photographic goods", "38": "Misc. chemical products", "39": "Plastics", "40": "Rubber",
    "41": "Raw hides & leather", "42": "Leather articles", "43": "Furskins", "44": "Wood",
    "45": "Cork", "46": "Basketware", "47": "Wood pulp", "48": "Paper", "49": "Printed matter",
    "50": "Silk", "51": "Wool", "52": "Cotton", "53": "Other vegetable fibres",
    "54": "Man-made filaments", "55": "Man-made staple fibres", "56": "Wadding & felt",
    "57": "Carpets", "58": "Special woven fabrics", "59": "Coated textiles", "60": "Knitted fabrics",
    "61": "Knitted clothing", "62": "Woven clothing", "63": "Other textile articles",
    "64": "Footwear", "65": "Headgear", "66": "Umbrellas", "67": "Feathers & artificial flowers",
    "68": "Stone & plaster articles", "69": "Ceramics", "70": "Glass",
    "71": "Pearls, gems, precious metals", "72": "Iron & steel", "73": "Articles of iron/steel",
    "74": "Copper", "75": "Nickel", "76": "Aluminium", "78": "Lead", "79": "Zinc", "80": "Tin",
    "81": "Other base metals", "82": "Tools & cutlery", "83": "Misc. metal articles",
    "84": "Machinery", "85": "Electrical equipment", "86": "Railway equipment", "87": "Vehicles",
    "88": "Aircraft", "89": "Ships", "90": "Optical / medical instruments", "91": "Clocks & watches",
    "92": "Musical instruments", "93": "Arms & ammunition", "94": "Furniture", "95": "Toys & games",
    "96": "Misc. manufactured articles", "97": "Works of art", "98": "Special classifications",
    "99": "Special classifications",
}


def country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code, code)


def hs2_label(code: str) -> str:
    return f"{code} - {HS2_LABELS[code]}" if code in HS2_LABELS else code


def hs2_name(code: str) -> str:
    """Plain name of a chapter: "Machinery". Falls back to the code itself."""
    return HS2_LABELS.get(code, code)
