#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$task_root"
task_target=${1:-src/Everything.agda}
mkdir -p "$task_root/_build"
task_build=$(cd -- "$task_root/_build" && pwd -P)
exec flock "$task_build/.study6.lock" agda +RTS -M3G -RTS \
  --no-libraries --safe --without-K --cubical-compatible -i src "$task_target"
