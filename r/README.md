# R side of Trade DNA

The Streamlit app (Python) calls R scripts through `src/trade_dna/r_bridge.py`.
Nothing is shared in memory: Python writes a CSV, R writes a CSV back.

## The contract

Every script in this folder must accept:

```
Rscript r/<script>.R --input <in.csv> --output <out.csv> [extra args...]
```

* `--input` is a CSV in the tidy schema used everywhere in the project:

  | column   | type   | example      |
  |----------|--------|--------------|
  | reporter | string | `LU`         |
  | partner  | string | `WORLD`, `DE`|
  | product  | string | `72`, `7208` |
  | flow     | string | `1` imports, `2` exports |
  | freq     | string | `A` or `M`   |
  | period   | string | `2024` or `2024-03` |
  | value    | number | euros        |

  Read `product` and `flow` as character (leading zeros matter):
  `read.csv(input, colClasses = c(product = "character", flow = "character"))`.

* `--output` is where the script writes its result CSV. Create the folder if
  needed. The columns are up to the script, but document them at the top of
  the file and in the table below, because the Python page that displays them
  needs to know.

* Exit code 0 on success. Print diagnostics to stdout; errors go to stderr.

* Base R only if possible. If you need packages, list them in
  `r/DEPENDENCIES` (one per line) and add them to `environment.yml`
  (`r-forecast`, `r-seasonal`, ...) so the environment stays reproducible.

## Scripts

| script           | what it does                                   | output columns |
|------------------|------------------------------------------------|----------------|
| `seasonality.R`  | STL decomposition of monthly series (base R)   | `series_id, period, value, trend, seasonal, remainder` |

Add yours here.

## Running by hand

```bash
Rscript r/seasonality.R --input data/processed/r/_input_seasonality.csv --output data/processed/r/seasonality.csv
```

## Committing outputs

Outputs under `data/processed/r/` are committed on purpose: if R is not
installed on the machine running the app (the jury's, for instance), the
Python side falls back to the committed CSV. Re-run the script and commit
whenever you change it.
