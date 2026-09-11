#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python -m pytest backend/tests ml/tests

