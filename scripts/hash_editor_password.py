"""Create a staging editor password hash and signing secret without saving plaintext."""

import getpass
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from infrastructure.auth import password_hash


def main() -> None:
    first = getpass.getpass("Contraseña nueva del editor: ")
    second = getpass.getpass("Repita la contraseña: ")
    if first != second or len(first) < 16:
        raise SystemExit(
            "Las contraseñas deben coincidir y tener al menos 16 caracteres."
        )
    print("AUTH_PASSWORD_HASH=" + password_hash(first))
    print("AUTH_SECRET=" + secrets.token_urlsafe(48))
    print(
        "Guarde la contraseña en su gestor de contraseñas; este script no la conserva."
    )


if __name__ == "__main__":
    main()
