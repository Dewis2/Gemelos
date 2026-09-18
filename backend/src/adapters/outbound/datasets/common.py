from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def detect_encoding(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            raw.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detect_delimiter(path: Path, encoding: str) -> str:
    sample = path.read_text(encoding=encoding, errors="replace")[:8192]
    return csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter


def read_rows(path: Path) -> Iterator[dict[str, str]]:
    encoding = detect_encoding(path)
    delimiter = detect_delimiter(path, encoding)
    with path.open(encoding=encoding, newline="") as source:
        reader = csv.DictReader(source, delimiter=delimiter)
        for row in reader:
            yield {
                str(key).strip(): (value or "").strip()
                for key, value in row.items()
                if key and not str(key).startswith("Unnamed")
            }


def parse_integer(value: str) -> int:
    normalized = re.sub(r"[\s,.]", "", value.strip())
    if not normalized or not normalized.lstrip("-").isdigit():
        raise ValueError(f"Not an integer: {value!r}")
    return int(normalized)


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text.strip()).casefold()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_profile(path: Path) -> dict[str, Any]:
    encoding = detect_encoding(path)
    delimiter = detect_delimiter(path, encoding)
    rows = list(read_rows(path))
    columns = list(rows[0]) if rows else []
    nulls = {column: sum(not row.get(column, "") for row in rows) for column in columns}
    return {
        "path": str(path),
        "encoding": encoding,
        "delimiter": delimiter,
        "row_count": len(rows),
        "columns": columns,
        "nulls": nulls,
        "checksum_sha256": sha256(path),
    }
