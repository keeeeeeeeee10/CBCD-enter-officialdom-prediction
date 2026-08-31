"""Project configuration loading with paths anchored at the repository root."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and retain its project root."""
    config_path = Path(path).resolve() if path else DEFAULT_CONFIG
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    config["_project_root"] = PROJECT_ROOT
    config["_config_path"] = config_path
    return config


def project_path(config: dict[str, Any], value: str | Path) -> Path:
    """Resolve a configured path relative to the repository root."""
    value = Path(value)
    return value if value.is_absolute() else Path(config["_project_root"]) / value


def configured_path(config: dict[str, Any], section: str, key: str) -> Path:
    return project_path(config, config[section][key])


def ensure_project_directories(config: dict[str, Any]) -> None:
    """Create all generated-data directories declared in the config."""
    for value in config["paths"].values():
        project_path(config, value).mkdir(parents=True, exist_ok=True)
    project_path(config, "database").mkdir(parents=True, exist_ok=True)
    project_path(config, "notebooks").mkdir(parents=True, exist_ok=True)

