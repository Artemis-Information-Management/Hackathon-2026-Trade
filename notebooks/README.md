# Notebooks

Exploration lives here. To use the project code from a notebook:

```python
import sys; sys.path.insert(0, "../src")
from trade_dna.data import load_trade
from trade_dna.indicators import similarity_over_time, hhi_by_product, prune_hierarchy

df, status = load_trade()
```

Keep notebooks for exploration only: anything the app needs goes into `src/trade_dna/`
so that it is tested and reusable. Clear outputs before committing large notebooks.
