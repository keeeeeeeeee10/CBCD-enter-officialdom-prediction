#!/usr/bin/env python3
"""Run non-experimental integrity and hygiene checks for the public release."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PDFS = {
    "paper/final/cbdb_kdd_style_author_final.pdf":
        "6d010ffb2592b3e3309efb69ffcb480f841c80c90e55c918b0acc03f85adcaa2",
    "paper/final/cbdb_kdd_style_anonymous_final.pdf":
        "988b050c0045541209d2eb01ea0d28739ecdf6c56d6073faac2c02f71bd2f624",
}
REQUIRED = {
    "README.md",
    "README_ZH.md",
    "LICENSE",
    "CITATION.cff",
    "requirements.txt",
    "environment.yml",
    "paper/final/main_body_final.tex",
    "paper/final/references_final.bib",
    "docs/phase3_1_1/final_claim_evidence_map.md",
    "outputs/phase3_1_1/methods/local_target_prior_spec.json",
}
PROHIBITED_SUFFIXES = {
    ".sqlite",
    ".sqlite3",
    ".db",
    ".cbm",
    ".joblib",
    ".pkl",
    ".pickle",
    ".pt",
    ".pth",
    ".parquet",
    ".feather",
    ".arrow",
    ".zip",
}
PROHIBITED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "checkpoints",
    "predictions",
}
MAX_PUBLIC_FILE_BYTES = 50 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def public_files() -> list[Path]:
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if tracked.returncode == 0 and tracked.stdout:
        return sorted(
            ROOT / item.decode("utf-8")
            for item in tracked.stdout.split(b"\0")
            if item and (ROOT / item.decode("utf-8")).is_file()
        )

    ignored_parts = {".git", "__pycache__", ".pytest_cache", ".venv"}
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not (set(path.relative_to(ROOT).parts) & ignored_parts)
    )


def main() -> None:
    errors: list[str] = []
    for relative in sorted(REQUIRED):
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for relative, expected in EXPECTED_PDFS.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing frozen PDF: {relative}")
        elif sha256(path) != expected:
            errors.append(f"frozen PDF hash mismatch: {relative}")

    files = public_files()
    for path in files:
        relative = path.relative_to(ROOT)
        lower_parts = {part.lower() for part in relative.parts}
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            errors.append(f"prohibited artifact type: {relative}")
        if lower_parts & PROHIBITED_PARTS:
            errors.append(f"prohibited artifact path: {relative}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            errors.append(f"file exceeds 50 MiB: {relative}")

    if errors:
        raise SystemExit("PUBLIC RELEASE CHECK FAILED\n" + "\n".join(errors))

    largest = max(files, key=lambda path: path.stat().st_size)
    print(
        "PUBLIC RELEASE CHECK PASS\n"
        f"files_checked={len(files)}\n"
        f"largest_file={largest.relative_to(ROOT)}\n"
        f"largest_bytes={largest.stat().st_size}\n"
        "frozen_pdf_hashes=PASS\n"
        "prohibited_artifacts=ABSENT\n"
        "files_over_50_mib=ABSENT"
    )


if __name__ == "__main__":
    main()
