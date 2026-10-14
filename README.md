# 🧬 Trade DNA

**Luxembourg's external trade profile: who it resembles, what it depends on, and how that changed.**

STATEC Hackathon 2026 · 14–16 October · GovTech Lab, Luxembourg
Data: Eurostat Comext [ds-045409](https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table) – *EU trade since 1988 by HS2-4-6 and CN8*

> Most trade dashboards answer *who* and *what*. Trade DNA asks three different questions and answers each with one established indicator, a map and a timeline.

| Lens | Question | Indicator |
|---|---|---|
| **1 · Trade twins** | Which European countries have a trade profile like Luxembourg's, and is that changing? | Finger-Kreinin similarity index |
| **2 · Dependency points** | For which products does Luxembourg rely on a single partner? | Herfindahl-Hirschman concentration |
| **3 · Smart zoom** | How to show HS2 → CN8 detail while only naming the significant flows? | Top-*k* pruning of the product tree |
| **4 · Seasonality** | Which flows are seasonal, and what is left once seasonality is removed? | STL decomposition, computed in **R** |

<!-- Add a screenshot or GIF of the app here before submission -->

## Quick start

```bash
git clone https://github.com/<you>/trade-dna.git
cd trade-dna
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens on a **synthetic sample** so the interface works immediately. Real numbers appear once the data files exist (next section).

Full environment with R included (conda/mamba): `mamba env create -f environment.yml`.

## Data

Two ways to get Eurostat data into `data/processed/`:

**A. Export from the Data Browser (most reliable)**
1. Open the dataset, *Customise your dataset*: reporters (EU27 or a subset), partners (`World` + main partners), products (TOTAL + HS2 chapters), both flows, annual, 1999 onwards.
2. Download as CSV into `data/raw/`. Repeat for a Luxembourg-only extract at HS4/HS6/CN8 if you want lens 3 on real data.
3. `python scripts/prepare_data.py`

**B. Comext API**
```bash
python scripts/fetch_data.py                                   # EU27 × WORLD × HS2, annual
python scripts/fetch_data.py --reporters LU --partners WORLD DE FR BE NL US CN UK   # bilateral, for lens 2
```

Output files (read by the app):

| File | Content |
|---|---|
| `data/processed/trade_hs2.parquet` | all reporters, HS2 + TOTAL, annual (and monthly if fetched) |
| `data/processed/trade_lu_cn8.parquet` | Luxembourg only, HS4/HS6/CN8 |
| `data/processed/r/*.csv` | outputs of the R scripts (committed so the app runs without R) |

Everything is normalised to one tidy schema (`reporter, partner, product, flow, freq, period, value`), documented in `src/trade_dna/data/schema.py`. Sources and limits are in [DATA_CARD.md](DATA_CARD.md).

Luxembourg is reported separately from Belgium only since **1999**, so all series start there.

## Python + R

The analysis is split between the two languages. Python owns the app, the data pipeline and lenses 1–3; R owns the time-series work (lens 4 and anything the team adds).

They talk through CSV files: Python writes a CSV in the tidy schema, calls `Rscript r/<script>.R --input in.csv --output out.csv`, reads the result. The contract is in [r/README.md](r/README.md); the bridge is `src/trade_dna/r_bridge.py`. If R is not installed where the app runs, the last committed output under `data/processed/r/` is used instead.

To add an R-backed page: copy `pages/4_Seasonality_R.py`, change the script name and the output columns.

## Project layout

```
app.py                      Streamlit home page
pages/                      one file per lens (Streamlit multipage)
src/trade_dna/
  config.py                 paths, country codes, HS2 labels, constants
  data/                     schema, loaders, Eurostat access, synthetic sample
  indicators/               similarity.py (FK), concentration.py (HHI), hierarchy.py (pruning)
  viz/                      plotly charts with one shared theme
  r_bridge.py               run R scripts, exchange CSV
  ui.py                     shared Streamlit widgets
r/                          R scripts + contract (r/README.md)
scripts/                    fetch_data.py, prepare_data.py
tests/                      pytest unit tests for the indicators
data/raw/                   Eurostat exports (git-ignored)
data/processed/             tidy parquet + R outputs (committed)
notebooks/                  exploration
```

## Reproducibility checklist

- [x] Open licence with SPDX identifier (`LICENSE`, EUPL-1.2)
- [x] `requirements.txt` and `environment.yml`
- [x] Data card with source, licence and limits
- [x] Unit tests: `pytest`
- [ ] Real data committed under `data/processed/`
- [ ] R outputs regenerated on real data and committed
- [ ] Screenshot in this README
- [ ] Pitch deck in `docs/`

## Team

_Names, roles, GitHub handles._

## Licence

Code: [EUPL-1.2](LICENSE). Data: © European Union, Eurostat, reused under Eurostat's re-use policy.
