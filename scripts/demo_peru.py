from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from application.cli import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if arguments == ["prepare"]:
        arguments = ["demo-peru", "prepare"]
    raise SystemExit(main(arguments))
