#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 scripts/offline_self_test.py
