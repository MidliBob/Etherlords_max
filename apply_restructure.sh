#!/usr/bin/env bash
# Применение перестройки репозитория Etherlords_max из Git Bash.
# Класть этот скрипт И restructure.patch в корень локального клона, затем: bash apply_restructure.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [ ! -f restructure.patch ]; then echo "ERROR: restructure.patch not found next to script"; exit 1; fi
echo "== check ==";  git apply --check restructure.patch
echo "== apply ==";  git apply restructure.patch
git add -A
git commit -q -m "Restructure into mod project: drop game binaries, add docs/tools/patches

- removed dumped game root (exe/dll/ini/res) - no game redistribution
- added docs/ (research log, protocols), tools/ (scan+patch scripts), patches/
- new README.md describing native hi-res project status and legal note"
echo "== done =="; git log --oneline -1; git status --short | head
