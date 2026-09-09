#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo '请先创建 .venv 并安装 backend/requirements.txt（参见 README）。' >&2
  exit 1
fi
check_dir=$(mktemp -d "${TMPDIR:-/tmp}/zaigong-check.XXXXXX")
trap 'rm -rf "$check_dir"' EXIT
# Production data is never used by this test run.
export ANALYSIS_DB_PATH="$check_dir/analysis.db"
.venv/bin/python -m pytest -c backend/pytest.ini backend/tests/ -q --ignore=backend/tests/test_api.py
npm --prefix frontend test -- --reporter=dot
npm --prefix frontend run build
