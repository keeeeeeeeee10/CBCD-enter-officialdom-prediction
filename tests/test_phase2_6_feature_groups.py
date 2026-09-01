from pathlib import Path

import pandas as pd

from src.phase26 import feature_group_lookup, model_features


ROOT = Path(__file__).resolve().parents[1]


def test_address_type_and_locked_group_policy():
    _, _, h_features = model_features("H_STRUCT")
    _, _, d5_features = model_features("D5_MAIN")
    _, _, d6_features = model_features("D6_UPPER")
    assert "addr_type_name" not in h_features
    assert feature_group_lookup(d5_features)["addr_type_name"] == "address_record_semantics"
    assert "family_full_record_capital" not in set(feature_group_lookup(d5_features).values())
    assert "family_full_record_capital" in set(feature_group_lookup(d6_features).values())
    assert not {"raw_index_year", "index_year", "family_group_id", "target_entry_v1", "target_posting"} & set(h_features + d5_features + d6_features)


def test_feature_coverage_separates_missingness_and_prevalence():
    frame = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_feature_coverage.csv")
    block = frame.loc[frame["population"].eq("Global") & frame["feature"].isin(["has_geography", "father_identified"])]
    assert len(block) == 2
    assert block["non_missing_rate"].eq(1).all()
    assert block["positive_flag_rate"].between(0, 1, inclusive="neither").all()
