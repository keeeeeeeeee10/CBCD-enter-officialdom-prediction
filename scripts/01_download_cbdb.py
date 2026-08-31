#!/usr/bin/env python3
"""Fetch the current official CBDB SQLite release, verify it, and make a working copy."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import requests
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, ensure_project_directories, load_config, project_path
from src.utils import atomic_write_text, human_bytes, setup_logging, sha256_file


def fetch_latest_metadata(config: dict, logger) -> tuple[dict, str]:
    """Prefer live official GitHub metadata and fall back to the cloned official repository."""
    url = config["database"]["latest_metadata_url"]
    retries = int(config["download"]["retries"])
    timeout = int(config["download"]["timeout_seconds"])
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            metadata = response.json()
            return metadata, url
        except Exception as exc:
            last_error = exc
            logger.warning("Metadata request %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(attempt)

    local = project_path(config, config["database"]["official_repo"]) / "latest.json"
    if local.exists():
        logger.warning("Using latest.json from the cloned official repository after network failure: %s", last_error)
        return json.loads(local.read_text(encoding="utf-8")), str(local.relative_to(PROJECT_ROOT))
    raise RuntimeError(f"Could not retrieve official latest.json: {last_error}")


def validate_metadata(metadata: dict) -> None:
    required = {"sqlite_filename", "sha256", "huggingface_url"}
    missing = required.difference(metadata)
    if missing:
        raise ValueError(f"latest.json is missing fields: {sorted(missing)}")
    filename = metadata["sqlite_filename"]
    if Path(filename).name != filename or not filename.endswith((".sqlite", ".sqlite3", ".db")):
        raise ValueError(f"Unsafe or unexpected SQLite filename: {filename}")
    digest = metadata["sha256"].lower()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("latest.json contains an invalid SHA256 value")


def mirror_url(official_url: str, mirror_base: str) -> str:
    parsed = urlparse(official_url)
    if parsed.netloc != "huggingface.co":
        return official_url
    return mirror_base.rstrip("/") + parsed.path


def stream_download(url: str, destination: Path, config: dict, logger) -> None:
    """Download to a partial file with HTTP Range resumption when supported."""
    partial = destination.with_suffix(destination.suffix + ".part")
    existing = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    timeout = int(config["download"]["timeout_seconds"])
    chunk_size = int(config["download"]["chunk_size_bytes"])
    with requests.get(url, headers=headers, stream=True, timeout=(15, timeout), allow_redirects=True) as response:
        response.raise_for_status()
        resumed = existing > 0 and response.status_code == 206
        if existing and not resumed:
            logger.warning("Server ignored Range; restarting partial download")
            existing = 0
        mode = "ab" if resumed else "wb"
        content_length = int(response.headers.get("content-length", 0))
        total = existing + content_length if content_length else None
        logger.info("Downloading %s (%s)", url, human_bytes(total) if total else "size unknown")
        with partial.open(mode) as handle, tqdm(
            total=total,
            initial=existing,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=destination.name,
        ) as progress:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    handle.write(chunk)
                    progress.update(len(chunk))
            handle.flush()
            os.fsync(handle.fileno())
    os.replace(partial, destination)


def download_with_fallback(metadata: dict, archive: Path, config: dict, logger) -> str:
    official = metadata["huggingface_url"]
    mirror = mirror_url(official, config["download"]["huggingface_mirror_base"])
    urls = [official] + ([mirror] if mirror != official else [])
    last_error: Exception | None = None
    for source in urls:
        try:
            stream_download(source, archive, config, logger)
            return source
        except Exception as exc:
            last_error = exc
            logger.warning("Download source failed (%s): %s", source, exc)
    raise RuntimeError(f"All official/mirror download sources failed: {last_error}")


def extract_expected_sqlite(archive: Path, expected_name: str, destination_dir: Path, logger) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        bad_member = bundle.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP CRC validation failed at member: {bad_member}")
        candidates = [
            member for member in bundle.infolist()
            if not member.is_dir() and PurePosixPath(member.filename).name == expected_name
        ]
        if len(candidates) != 1:
            names = [member.filename for member in bundle.infolist()]
            raise RuntimeError(f"Expected exactly one {expected_name} in ZIP; members={names[:20]}")
        member = candidates[0]
        temporary = destination_dir / f".{expected_name}.extracting"
        logger.info("Extracting %s (%s uncompressed)", member.filename, human_bytes(member.file_size))
        with bundle.open(member) as source, temporary.open("wb") as target:
            shutil.copyfileobj(source, target, length=8 * 1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        final = destination_dir / expected_name
        os.replace(temporary, final)
        return final


def update_stable_link(link: Path, target: Path, logger) -> None:
    if link.is_symlink() or link.exists():
        if link.resolve() == target.resolve():
            return
        link.unlink()
    try:
        link.symlink_to(target.name)
        logger.info("Stable database symlink: %s -> %s", link.name, target.name)
    except OSError as exc:
        logger.warning("Symlink unsupported (%s); copying stable read-only database path", exc)
        shutil.copy2(target, link)
        link.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def prepare_working_copy(raw_database: Path, expected_sha: str, config: dict, logger) -> Path:
    working = configured_path(config, "database", "working_db")
    marker = configured_path(config, "database", "working_source_marker")
    marker_value = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""
    if working.exists() and marker_value == expected_sha:
        logger.info("Working database already corresponds to this source release: %s", working)
        return working
    if working.exists():
        logger.warning("Replacing working database because its source release changed")
        working.unlink()
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(working) + suffix)
        if sidecar.exists():
            sidecar.unlink()
    logger.info("Copying verified raw database to writable working database")
    shutil.copy2(raw_database, working)
    working.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    atomic_write_text(marker, expected_sha + "\n")
    return working


def main() -> int:
    config = load_config()
    ensure_project_directories(config)
    logger = setup_logging("download", configured_path(config, "paths", "logs") / "download_cbdb.log")
    metadata, metadata_source = fetch_latest_metadata(config, logger)
    validate_metadata(metadata)
    raw_dir = configured_path(config, "paths", "raw")
    database_dir = project_path(config, "database")
    metadata_path = raw_dir / "latest.json"
    atomic_write_text(metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")

    filename = metadata["sqlite_filename"]
    expected_sha = metadata["sha256"].lower()
    raw_database = database_dir / filename
    archive = raw_dir / (Path(filename).stem + ".zip")
    logger.info("Release date: %s", metadata.get("generated_at_utc", "not supplied"))
    logger.info("SQLite filename: %s", filename)
    logger.info("Expected SQLite SHA256: %s", expected_sha)
    logger.info("Metadata source: %s", metadata_source)
    logger.info("Download source: %s", metadata["huggingface_url"])

    source_used = "existing verified database"
    valid_existing = False
    if raw_database.exists():
        observed = sha256_file(raw_database)
        if observed == expected_sha:
            valid_existing = True
            logger.info("SHA256 PASS; SKIP DOWNLOAD: %s", raw_database)
        else:
            logger.warning("Existing database SHA256 mismatch (%s); removing corrupt file", observed)
            raw_database.chmod(stat.S_IRUSR | stat.S_IWUSR)
            raw_database.unlink()

    if not valid_existing:
        if not archive.exists():
            source_used = download_with_fallback(metadata, archive, config, logger)
        else:
            source_used = "existing ZIP archive"
            logger.info("Using existing ZIP archive: %s (%s)", archive, human_bytes(archive.stat().st_size))
        try:
            raw_database = extract_expected_sqlite(archive, filename, database_dir, logger)
        except (zipfile.BadZipFile, RuntimeError) as exc:
            logger.warning("Existing/downloaded ZIP is invalid; downloading a fresh copy: %s", exc)
            archive.unlink(missing_ok=True)
            source_used = download_with_fallback(metadata, archive, config, logger)
            raw_database = extract_expected_sqlite(archive, filename, database_dir, logger)

        observed = sha256_file(raw_database)
        if observed != expected_sha:
            raw_database.unlink(missing_ok=True)
            raise RuntimeError(
                f"SQLite SHA256 FAIL: expected {expected_sha}, observed {observed}. "
                "The extracted database was removed and will not be used."
            )
        logger.info("SQLite SHA256 PASS: %s", observed)

    raw_database.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    raw_mode = stat.S_IMODE(raw_database.stat().st_mode)
    if raw_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        logger.warning(
            "Filesystem did not honor chmod 0444 (observed mode %s). The pipeline will still open the raw DB "
            "only with SQLite mode=ro and will revalidate its SHA256 before and after processing.",
            oct(raw_mode),
        )
    stable_link = configured_path(config, "database", "raw_db")
    update_stable_link(stable_link, raw_database, logger)
    working = prepare_working_copy(raw_database, expected_sha, config, logger)

    manifest = {
        "metadata_source": metadata_source,
        "download_source_used": source_used,
        "generated_at_utc": metadata.get("generated_at_utc"),
        "sqlite_filename": filename,
        "sqlite_sha256": expected_sha,
        "sqlite_sha256_status": "PASS",
        "sqlite_size_bytes": raw_database.stat().st_size,
        "sqlite_observed_mode": oct(raw_mode),
        "archive_filename": archive.name if archive.exists() else None,
        "archive_sha256": sha256_file(archive) if archive.exists() else None,
        "working_database": str(working.relative_to(PROJECT_ROOT)),
    }
    atomic_write_text(raw_dir / "download_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    logger.info("Raw database is read-only: %s (%s)", raw_database, human_bytes(raw_database.stat().st_size))
    logger.info("Working database: %s", working)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
