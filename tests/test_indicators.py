"""Unit tests for the three indicators. Run with: pytest"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trade_dna.data import sample  # noqa: E402
from trade_dna.data.schema import validate  # noqa: E402
from trade_dna.indicators import finger_kreinin, hhi_by_product, product_shares, prune_hierarchy, similarity_over_time  # noqa: E402


def _frame(rows):
    return validate(pd.DataFrame(rows, columns=["reporter", "partner", "product", "flow", "freq", "period", "value"]))


def test_finger_kreinin_identical_is_one_and_disjoint_is_zero():
    df = _frame(
        [
            ("LU", "WORLD", "72", "2", "A", "2024", 50),
            ("LU", "WORLD", "84", "2", "A", "2024", 50),
            ("AA", "WORLD", "72", "2", "A", "2024", 5),   # same mix, different size
            ("AA", "WORLD", "84", "2", "A", "2024", 5),
            ("BB", "WORLD", "30", "2", "A", "2024", 100),  # nothing in common
            ("CC", "WORLD", "72", "2", "A", "2024", 100),  # half in common
        ]
    )
    fk = finger_kreinin(product_shares(df, "2", "2024"))
    assert fk["LU"] == pytest.approx(1.0)
    assert fk["AA"] == pytest.approx(1.0)
    assert fk["BB"] == pytest.approx(0.0)
    assert fk["CC"] == pytest.approx(0.5)


def test_similarity_over_time_shape():
    df = sample.make_sample_trade(reporters=["LU", "BE", "DE"], years=(2020, 2022))
    sim = similarity_over_time(df, "2")
    assert set(sim.columns) == {"period", "reporter", "fk"}
    assert sim["period"].nunique() == 3
    assert ((sim["fk"] >= 0) & (sim["fk"] <= 1)).all()


def test_hhi_single_partner_is_one_and_aggregates_excluded():
    df = _frame(
        [
            ("LU", "DE", "72", "1", "A", "2024", 100),
            ("LU", "WORLD", "72", "1", "A", "2024", 100),  # must be ignored
            ("LU", "DE", "84", "1", "A", "2024", 50),
            ("LU", "FR", "84", "1", "A", "2024", 50),
        ]
    )
    h = hhi_by_product(df, "2024", "1", "LU").set_index("product")
    assert h.loc["72", "hhi"] == pytest.approx(1.0)
    assert h.loc["72", "top_partner"] == "DE"
    assert h.loc["84", "hhi"] == pytest.approx(0.5)
    assert h.loc["84", "n_partners"] == 2


def test_prune_keeps_totals_and_folds_tail():
    df = pd.DataFrame(
        {
            "product": ["72081000", "72082000", "72083000", "72084000", "84011000", "84012000"],
            "value": [100.0, 50.0, 10.0, 5.0, 80.0, 1.0],
        }
    )
    nodes = prune_hierarchy(df, top_k=2, min_share=0.0)
    root = nodes[nodes["level"] == 0]["value"].iloc[0]
    assert root == pytest.approx(246.0)
    # every parent's children (named + other) sum to the parent
    for _, parent in nodes[nodes["level"] < 8].iterrows():
        kids = nodes[nodes["parent"] == parent["id"]]
        if len(kids):
            assert kids["value"].sum() == pytest.approx(parent["value"])
    # 7208 has four HS6 children, top_k=2 -> the two smallest fold into one "Other (2)"
    other = nodes[(nodes["parent"] == "7208") & nodes["is_other"]]
    assert len(other) == 1
    assert other["label"].iloc[0] == "Other (2)"
    assert other["value"].iloc[0] == pytest.approx(15.0)
    # 8401 has two children, both kept, so no "Other" there
    assert not nodes[(nodes["parent"] == "8401") & nodes["is_other"]].shape[0]
