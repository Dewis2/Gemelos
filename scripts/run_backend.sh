#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python -m uvicorn main:app --app-dir backend/src --reload

