#!/usr/bin/env python3
"""Check Phase 1 runtime prerequisites without changing global configuration."""

from __future__ import annotations

import csv
import importlib
import platform
import shutil
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, ensure_project_directories, load_config
from src.utils import setup_logging


PACKAGE_IMPORTS = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "scikit-learn": "sklearn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "networkx": "networkx",
    "sqlalchemy": "sqlalchemy",
    "pyyaml": "yaml",
    "tqdm": "tqdm",
    "requests": "requests",
    "catboost": "catboost",
    "shap": "shap",
    "pyarrow": "pyarrow",
    "openpyxl": "openpyxl",
    "jupyter": "jupyter",
    "ipykernel": "ipykernel",
}


def main() -> int:
    config = load_config()
    ensure_project_directories(config)
    logger = setup_logging("setup", configured_path(config, "paths", "logs") / "setup_check.log")
    logger.info("Project root: %s", PROJECT_ROOT)
    logger.info("Python: %s", platform.python_version())
    logger.info("SQLite (Python module): %s", sqlite3.sqlite_version)

    missing_commands = []
    for command in ("python3", "git", "wget", "curl", "sqlite3", "unzip"):
        resolved = shutil.which(command)
        logger.info("Command %-8s %s", command, resolved or "MISSING (Python fallback may be used)")
        if not resolved:
            missing_commands.append(command)

    versions = [
        {"component": "python", "version": platform.python_version(), "status": "installed"},
        {"component": "sqlite", "version": sqlite3.sqlite_version, "status": "installed"},
    ]
    missing_packages = []
    for package, import_name in PACKAGE_IMPORTS.items():
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, "__version__", "installed")
            status = "installed"
        except Exception as exc:  # import can fail because a binary dependency is missing
            version = ""
            status = f"missing: {type(exc).__name__}"
            missing_packages.append(package)
        versions.append({"component": package, "version": version, "status": status})
        logger.info("Package %-14s %s", package, version or status)

    output = configured_path(config, "paths", "tables") / "environment_versions.csv"
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["component", "version", "status"])
        writer.writeheader()
        writer.writerows(versions)

    core = {"pandas", "numpy", "matplotlib", "seaborn", "pyyaml", "tqdm", "requests", "pyarrow"}
    missing_core = sorted(core.intersection(missing_packages))
    if missing_core:
        logger.error("Missing Phase 1 runtime packages: %s", ", ".join(missing_core))
        return 2
    if missing_packages:
        logger.warning("Packages preinstalled for later phases are missing: %s", ", ".join(missing_packages))
    if missing_commands:
        logger.warning("Missing optional system commands: %s", ", ".join(missing_commands))
    logger.info("Setup check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

