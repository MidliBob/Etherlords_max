#!/usr/bin/env bash
# Применение update_002_new_data.patch к текущему состоянию репозитория (после "reload").
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
[ -f update_002_new_data.patch ] || { echo "ERROR: update_002_new_data.patch not found"; exit 1; }
git apply --check update_002_new_data.patch
git apply update_002_new_data.patch
git add -A
git commit -q -m "Update model: three coordinate consumers (draw/hover/click), acceptance criteria

- docs/06: three-consumer model + click requires hover&baked agreement + acceptance criterion
- docs/08: acceptance criteria for v2 (draw == hover zones == click)
- README: status reflects refined model
- tools/hook_skeleton: acceptance note"
echo "== done =="; git log --oneline -1
