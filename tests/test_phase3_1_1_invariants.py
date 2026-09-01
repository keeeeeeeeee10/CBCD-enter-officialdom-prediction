from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path) -> Counter[str]:
    result = []
    for line in path.read_text().splitlines():
        line = line.strip().replace("\\allowbreak ", "")
        if " & " in line and line.endswith(r"\\") and not line.startswith("Population &"):
            result.append(re.sub(r"\s+", " ", line))
    return Counter(result)


def test_all_frozen_baseline_hashes_are_unchanged():
    manifest = ROOT / "outputs/phase3_1_1/manifests/baseline_sha256.tsv"
    records = list(csv.DictReader(manifest.open(), delimiter="\t"))
    assert len(records) == 97
    assert all((ROOT / row["relative_path"]).is_file() for row in records)
    assert all(sha256(ROOT / row["relative_path"]) == row["sha256"] for row in records)


def test_global_d5_headline_metrics_are_frozen():
    metrics = pd.read_csv(ROOT / "outputs/phase3_1/tables/final_metric_recomputation.csv")
    subset = metrics[(metrics.population == "Global") & (metrics.model_id == "D5_MAIN")].set_index("quantity")
    expected = {"roc_auc": 0.936956, "pr_auc": 0.882535, "log_loss": 0.315106, "brier_score": 0.097356, "calibrated_ece": 0.003438}
    for key, value in expected.items():
        assert round(float(subset.loc[key, "reported"]), 6) == value


def test_appendix_tables_preserve_phase31_rows_and_values():
    for name in ["tableA2_full_metrics.tex", "tableA3_full_ablation.tex", "tableA4_full_robustness.tex"]:
        assert rows(ROOT / "paper/revised/tables" / name) == rows(ROOT / "paper/final/tables" / name)


def test_physical_geography_intervals_remain_unavailable():
    table = (ROOT / "paper/final/tables/tableA3_full_ablation.tex").read_text()
    physical = [line for line in table.splitlines() if "Physical geography" in line]
    assert len(physical) == 3
    assert all(line.count("--") == 2 for line in physical)


def test_final_audit_status_is_pass():
    result = json.loads((ROOT / "outputs/phase3_1_1/tables/phase3_1_1_audit_status.json").read_text())
    assert result["status"] == "PASS"
    assert not result["blocking_issues"]
