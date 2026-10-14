"""Unit tests for the three indicators. Run with: pytest"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trade_dna.data import sample  # noqa: E402
from trade_dna.data.schema import validate  # noqa: E402
from trade_dna.indicators import (  # noqa: E402
    collapse_overlap,
    common_matrix,
    finger_kreinin,
    hhi_by_product,
    overlap_summary,
    product_overlap,
    product_shares,
    prune_hierarchy,
    similarity_over_time,
)


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


def test_prune_ignores_coarser_levels_to_avoid_double_counting():
    # Eurostat stores HS2, HS4 and CN8 rows side by side; only CN8 must be summed.
    df = pd.DataFrame(
        {
            "product": ["TOTAL", "72", "7208", "72081000", "72082000"],
            "value": [150.0, 150.0, 150.0, 100.0, 50.0],
        }
    )
    nodes = prune_hierarchy(df, top_k=5, min_share=0.0)
    assert nodes.loc[nodes["level"] == 0, "value"].iloc[0] == pytest.approx(150.0)
    assert nodes.loc[nodes["id"] == "72", "value"].iloc[0] == pytest.approx(150.0)


def test_total_line_is_not_counted_as_a_product_in_similarity():
    # The real extractions contain a TOTAL row next to the HS2 chapters.
    df = _frame(
        [
            ("LU", "WORLD", "TOTAL", "2", "A", "2024", 100),
            ("LU", "WORLD", "72", "2", "A", "2024", 50),
            ("LU", "WORLD", "84", "2", "A", "2024", 50),
            ("AA", "WORLD", "TOTAL", "2", "A", "2024", 100),
            ("AA", "WORLD", "72", "2", "A", "2024", 50),
            ("AA", "WORLD", "30", "2", "A", "2024", 50),
        ]
    )
    fk = finger_kreinin(product_shares(df, "2", "2024"))
    assert fk["AA"] == pytest.approx(0.5)  # would be 0.75 if TOTAL were counted


def test_hhi_ignores_total_line_and_aggregate_partners():
    df = _frame(
        [
            ("LU", "DE", "72", "1", "A", "2024", 60),
            ("LU", "FR", "72", "1", "A", "2024", 40),
            ("LU", "EU27_2020", "72", "1", "A", "2024", 100),  # aggregate
            ("LU", "AFRICA", "72", "1", "A", "2024", 5),       # aggregate
            ("LU", "QU", "72", "1", "A", "2024", 5),           # special grouping
            ("LU", "DE", "TOTAL", "1", "A", "2024", 60),       # not a chapter
        ]
    )
    h = hhi_by_product(df, "2024", "1", "LU")
    assert list(h["product"]) == ["72"]
    assert h["hhi"].iloc[0] == pytest.approx(0.6**2 + 0.4**2)


# ---- product dimension -------------------------------------------------------
def _shares_example():
    df = _frame(
        [
            ("LU", "WORLD", "TOTAL", "2", "A", "2024", 100),
            ("LU", "WORLD", "72", "2", "A", "2024", 50),
            ("LU", "WORLD", "84", "2", "A", "2024", 30),
            ("LU", "WORLD", "30", "2", "A", "2024", 20),
            ("AA", "WORLD", "72", "2", "A", "2024", 10),
            ("AA", "WORLD", "84", "2", "A", "2024", 60),
            ("AA", "WORLD", "27", "2", "A", "2024", 30),
            ("BB", "WORLD", "72", "2", "A", "2024", 50),
            ("BB", "WORLD", "84", "2", "A", "2024", 30),
            ("BB", "WORLD", "30", "2", "A", "2024", 20),
        ]
    )
    return product_shares(df, "2", "2024")


def test_product_overlap_adds_up_to_the_finger_kreinin_score():
    shares = _shares_example()
    fk = finger_kreinin(shares)
    for other in ("AA", "BB"):
        ov = product_overlap(shares, other)
        assert ov["common"].sum() == pytest.approx(fk[other])
        assert (ov["common"] <= ov[["focus", "other"]].min(axis=1) + 1e-12).all()
    ov = product_overlap(shares, "AA").loc[["72", "84", "30", "27"]]
    assert ov.loc["72", "common"] == pytest.approx(0.1)   # LU 50 %, AA 10 %
    assert ov.loc["84", "common"] == pytest.approx(0.3)   # LU 30 %, AA 60 %
    assert ov.loc["30", "common"] == pytest.approx(0.0)   # AA does not export it
    assert ov.loc["27", "common"] == pytest.approx(0.0)   # LU does not export it


def test_collapse_overlap_keeps_every_total():
    sample_df = sample.make_sample_trade(reporters=["LU", "BE", "DE"], years=(2024, 2024))
    shares = product_shares(sample_df, "2", "2024")
    ov = product_overlap(shares, "DE")
    small = collapse_overlap(ov, n=5)
    assert len(small) == 6
    assert small.index[-1] == f"Other chapters ({len(ov) - 5})"
    for col in ("focus", "other", "common"):
        assert small[col].sum() == pytest.approx(ov[col].sum())
    # nothing to fold -> the table is returned as it is
    assert len(collapse_overlap(ov, n=50)) == len(ov)


def test_common_matrix_columns_add_up_to_each_score():
    shares = _shares_example()
    fk = finger_kreinin(shares)
    m = common_matrix(shares, ["AA", "BB", "LU"], n=2)   # LU itself is ignored
    assert list(m.columns) == ["AA", "BB"]
    assert m.index[-1].startswith("Other")
    assert m["AA"].sum() == pytest.approx(fk["AA"])
    assert m["BB"].sum() == pytest.approx(fk["BB"])


def test_overlap_summary_names_main_overlap_and_biggest_gap():
    ov = product_overlap(_shares_example(), "AA")
    info = overlap_summary(ov, k=2)
    assert [code for code, _ in info["top_common"]] == ["84", "72"]
    code, lu_share, other_share = info["gap"]
    assert code in {"72", "84", "30", "27"}
    # LU 50 % vs AA 10 % in chapter 72 is the widest gap (0.40)
    assert (code, lu_share, other_share) == ("72", pytest.approx(0.5), pytest.approx(0.1))


def test_line_charts_use_a_numeric_year_axis_so_event_lines_sit_on_the_data():
    from trade_dna.viz import similarity_lines

    df = sample.make_sample_trade(reporters=["LU", "BE"], years=(2005, 2024))
    fig = similarity_lines(similarity_over_time(df, "2"), ["BE"])
    xs = list(fig.data[0].x)
    assert xs[0] == 2005 and xs[-1] == 2024            # integers, not '2005'
    assert {s.x0 for s in fig.layout.shapes} == {2008, 2016, 2020, 2022}
