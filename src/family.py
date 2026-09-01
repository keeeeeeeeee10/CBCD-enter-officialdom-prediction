"""Phase 2 family feature helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def smoothed_ratio(
    positive_count: pd.Series,
    eligible_count: pd.Series,
    prior: float,
    alpha: float = 20.0,
) -> pd.Series:
    numerator = pd.to_numeric(positive_count, errors="coerce").fillna(0.0)
    denominator = pd.to_numeric(eligible_count, errors="coerce").fillna(0.0)
    values = (numerator + alpha * float(prior)) / (denominator + alpha)
    return values.replace([np.inf, -np.inf], np.nan).astype(float)


def training_family_prior(positive_count: pd.Series, eligible_count: pd.Series) -> float:
    positives = float(pd.to_numeric(positive_count, errors="coerce").fillna(0.0).sum())
    eligible = float(pd.to_numeric(eligible_count, errors="coerce").fillna(0.0).sum())
    return positives / eligible if eligible > 0 else 0.0


INDUCTIVE_FEATURES = [
    "ind_father_outcome",
    "ind_paternal_grandfather_outcome",
    "ind_maternal_grandfather_outcome",
    "ind_n_observed_older_kin",
    "ind_n_positive_older_kin",
    "ind_positive_ratio",
    "ind_any_positive",
]


def build_inductive_family_features(
    focal_ids: pd.Series,
    relation_edges: pd.DataFrame,
    training_ids: set[int],
    relative_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Build family outcomes using only relatives belonging to locked training IDs.

    `relative_outcomes` must have `person_id` and `relative_outcome`. A relative
    outside `training_ids` is unknown, never a negative. Self edges are rejected.
    """

    focal = pd.DataFrame({"person_id": pd.Series(focal_ids, dtype="int64").to_numpy()})
    if focal["person_id"].duplicated().any():
        raise ValueError("focal_ids must be unique")
    required = {"person_id", "kin_id", "generation_class", "specific_relation"}
    if not required.issubset(relation_edges.columns):
        raise ValueError(f"Missing inductive relation columns: {sorted(required - set(relation_edges.columns))}")
    if relation_edges["person_id"].eq(relation_edges["kin_id"]).any():
        raise ValueError("Inductive family edges cannot contain self edges")
    if set(relative_outcomes.columns) != {"person_id", "relative_outcome"}:
        raise ValueError("relative_outcomes must contain exactly person_id and relative_outcome")
    if relative_outcomes["person_id"].duplicated().any():
        raise ValueError("relative_outcomes person_id must be unique")

    edges = relation_edges.loc[
        relation_edges["person_id"].isin(set(focal["person_id"]))
        & relation_edges["kin_id"].isin(training_ids)
    ].drop_duplicates(["person_id", "kin_id"]).copy()
    observed = edges.merge(
        relative_outcomes.rename(columns={"person_id": "kin_id"}),
        on="kin_id",
        how="left",
        validate="many_to_one",
    )
    observed = observed.loc[observed["relative_outcome"].notna()].copy()
    output = focal.copy()
    direct = {
        "father": "ind_father_outcome",
        "paternal_grandfather": "ind_paternal_grandfather_outcome",
        "maternal_grandfather": "ind_maternal_grandfather_outcome",
    }
    for relation, column in direct.items():
        mapping = observed.loc[observed["specific_relation"].eq(relation)].groupby("person_id")["relative_outcome"].max()
        output[column] = output["person_id"].map(mapping).astype(float)

    older = observed.loc[observed["generation_class"].isin(["ancestor", "parent_generation"])]
    aggregate = older.groupby("person_id").agg(
        ind_n_observed_older_kin=("kin_id", "nunique"),
        ind_n_positive_older_kin=("relative_outcome", "sum"),
    )
    aggregate["ind_positive_ratio"] = aggregate["ind_n_positive_older_kin"] / aggregate["ind_n_observed_older_kin"]
    aggregate["ind_any_positive"] = aggregate["ind_n_positive_older_kin"].gt(0).astype(float)
    for column in [
        "ind_n_observed_older_kin",
        "ind_n_positive_older_kin",
        "ind_positive_ratio",
        "ind_any_positive",
    ]:
        output[column] = output["person_id"].map(aggregate[column]).astype(float)
    return output[["person_id", *INDUCTIVE_FEATURES]]
