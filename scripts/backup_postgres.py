"""Create and verify a PostgreSQL 18 custom-format backup without exposing secrets.

Set BACKUP_DATABASE_URL in the process environment. The URL is never printed or
passed as a command-line argument to pg_dump; libpq receives only its components.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url


def backup(url: str, output: Path, bin_dir: Path) -> dict[str, object]:
    if output.exists():
        raise ValueError(f"Refusing to overwrite existing backup: {output}")
    if output.suffix.lower() not in {".backup", ".dump"}:
        raise ValueError("Use a .backup or .dump output file")
    # Render may provide the legacy postgres:// scheme.
    parsed = make_url(
        "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgres://")
        else url
    )
    if (
        parsed.get_backend_name() != "postgresql"
        or not parsed.host
        or not parsed.database
    ):
        raise ValueError("A PostgreSQL URL with host and database is required")
    dump = bin_dir / ("pg_dump.exe" if os.name == "nt" else "pg_dump")
    restore = bin_dir / ("pg_restore.exe" if os.name == "nt" else "pg_restore")
    version = subprocess.run(
        [str(dump), "--version"], capture_output=True, text=True, check=True
    )
    if not re.search(r"\b18(?:\.\d+)?\b", version.stdout):
        raise RuntimeError("PostgreSQL 18 client tools are required")
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    if parsed.password is not None:
        environment["PGPASSWORD"] = parsed.password
    try:
        subprocess.run(
            [
                str(dump),
                "-h",
                parsed.host,
                "-p",
                str(parsed.port or 5432),
                "-U",
                parsed.username or "postgres",
                "-d",
                parsed.database,
                "-Fc",
                "--no-owner",
                "--no-acl",
                "-f",
                str(output),
            ],
            env=environment,
            capture_output=True,
            check=True,
            timeout=900,
        )
        if output.stat().st_size == 0:
            raise RuntimeError("pg_dump produced an empty file")
        listing = subprocess.run(
            [str(restore), "--list", str(output)],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        if "TOC Entries:" not in listing.stdout:
            raise RuntimeError("pg_restore did not recognize the custom backup")
        with output.open("rb") as backup_file:
            checksum = hashlib.file_digest(backup_file, "sha256").hexdigest()
        manifest = {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "client_version": version.stdout.strip(),
            "format": "PostgreSQL custom",
            "size_bytes": output.stat().st_size,
            "sha256": checksum,
            "restore_list_verified": True,
            "database_name": parsed.database,
        }
        output.with_suffix(output.suffix + ".manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return manifest
    except Exception:
        if output.exists():
            output.unlink()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Verified PostgreSQL 18 backup")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--bin-dir", type=Path, default=Path(r"C:\Program Files\PostgreSQL\18\bin")
    )
    args = parser.parse_args()
    url = os.environ.get("BACKUP_DATABASE_URL")
    if not url:
        parser.error("Set BACKUP_DATABASE_URL securely in the process environment")
    result = backup(url, args.output, args.bin_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
