#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$task_root"
task_target=${1:-src/Everything.agda}
exec flock /tmp/othello-agda-local-check.lock agda +RTS -M3G -RTS \
  --no-libraries --safe --without-K --cubical-compatible -i src "$task_target"
