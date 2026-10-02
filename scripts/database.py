"""Portable database operations using the repository .env or --env-file."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("command", choices=["status", "migrate", "ingest-historical"])
    args = parser.parse_args()
    try:
        from dotenv import dotenv_values
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
    except ImportError:
        print(
            'Instala el backend: python -m pip install -e "./backend[dev]"',
            file=sys.stderr,
        )
        return 1
    env = os.environ.copy()
    if args.env_file.is_file():
        for key, value in dotenv_values(args.env_file).items():
            if value is not None:
                env.setdefault(key, value)
    raw_url = env.get("DATABASE_URL", "")
    try:
        url = make_url(raw_url)
        if url.get_backend_name() != "postgresql" or not url.database or not url.host:
            raise ValueError
        if (
            not url.password
            or "CHANGE_ME" in url.password
            or url.password.startswith("change_me")
        ):
            raise ValueError
    except Exception:
        print(
            "Configura DATABASE_URL para PostgreSQL con una contraseña local real.",
            file=sys.stderr,
        )
        return 1

    def redact(message: str) -> str:
        return message.replace(raw_url, "[DATABASE_URL]").replace(
            url.password, "[password]"
        )

    try:
        if args.command == "status":
            engine = create_engine(url, connect_args={"connect_timeout": 5})
            try:
                with engine.connect() as connection:
                    row = connection.execute(
                        text(
                            "SELECT current_database(), current_user, "
                            "version(), PostGIS_Version()"
                        )
                    ).one()
                    revisions = (
                        connection.execute(
                            text("SELECT version_num FROM alembic_version")
                        )
                        .scalars()
                        .all()
                    )
                    tables = (
                        connection.execute(
                            text(
                                "SELECT tablename FROM pg_tables "
                                "WHERE schemaname='public' ORDER BY tablename"
                            )
                        )
                        .scalars()
                        .all()
                    )
                    print(
                        json.dumps(
                            {
                                "database": row[0],
                                "user": row[1],
                                "postgresql": row[2],
                                "postgis": row[3],
                                "revisions": revisions,
                                "public_tables": tables,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
            finally:
                engine.dispose()
        else:
            if args.command == "migrate":
                command = [sys.executable, "-m", "alembic", "upgrade", "head"]
                cwd = ROOT / "backend"
            else:
                env["DEMO_REPOSITORY"] = "sqlalchemy"
                env.setdefault("DATA_ROOT", str(ROOT / "data"))
                command = [
                    sys.executable,
                    "-m",
                    "application.cli",
                    "datasets",
                    "ingest",
                    "huancayo-historical",
                ]
                cwd = ROOT
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.stdout:
                print(redact(result.stdout), end="")
            if result.stderr:
                print(redact(result.stderr), end="", file=sys.stderr)
            return result.returncode
    except Exception as error:
        print(redact(str(error)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
