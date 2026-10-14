# Data Card

## Source

| | |
|---|---|
| Dataset | **ds-045409** – *EU trade since 1988 by HS2-4-6 and CN8* |
| Publisher | Eurostat (Comext), based on data from national statistical institutes including STATEC |
| Access | Eurostat Data Browser / Comext API (see `scripts/`) |
| Licence | Eurostat data are free to re-use with attribution: *© European Union, [year], source: Eurostat* |
| Last update used | _fill in the date shown in the Data Browser when you exported_ |
| Retrieved on | _fill in_ |

## What we extracted

| Table | Reporters | Partners | Products | Flows | Frequency | Period |
|---|---|---|---|---|---|---|
| `trade_hs2.parquet` | EU27 (or a subset) | WORLD + main partners | TOTAL + HS2 chapters | imports, exports | annual (+ monthly for LU) | 1999– |
| `trade_lu_cn8.parquet` | LU | WORLD (+ selected) | HS4 / HS6 / CN8 | imports, exports | annual | selected years |

Indicator: `VALUE_IN_EUROS`.

## Known limits

* Luxembourg is reported together with Belgium before 1999; all series start in 1999.
* Values are trade values in current euros, not deflated. Trends include price effects.
* Partner aggregates (WORLD, EU27…) are excluded from concentration indices; the exact list is in `src/trade_dna/config.py`.
* Monthly data are not seasonally adjusted by Eurostat; our seasonal adjustment (STL in R) is our own and is illustrative.
* No personal or confidential data are involved; everything is published aggregate statistics.

## Derived indicators

* **Finger-Kreinin similarity** (lens 1) – Finger & Kreinin (1979), *Economic Journal* 89.
* **Herfindahl-Hirschman index** of partner concentration (lens 2).
* **Top-k hierarchical pruning** (lens 3) – our own rule, documented in `src/trade_dna/indicators/hierarchy.py`.
* **STL decomposition** (lens 4) – Cleveland et al. (1990), via base R `stl()`.
