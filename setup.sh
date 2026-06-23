#!/usr/bin/env bash
# One-shot: git init -> commit -> create GitHub repo -> push. Run: bash setup.sh
set -euo pipefail

REPO="superpowerdevk/dopamine"   # change owner/name here if needed
VISIBILITY="--public"            # use "--private" to keep it private

# Always run from this script's own folder — never your home dir.
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ -f pyproject.toml ] && [ -d dopamine ] || { echo "ERROR: run from the dopamine-repo folder (pyproject.toml missing)."; exit 1; }

command -v git >/dev/null || { echo "git missing. Run: xcode-select --install"; exit 1; }

echo ">> preparing local repo"
[ -d .git ] || git init -q
git add .
git diff --cached --quiet 2>/dev/null || git commit -q -m "dopamine v1.0.0"
git branch -M main

if ! command -v gh >/dev/null; then
  echo ""
  echo "GitHub CLI not installed. Install it, then re-run this script:"
  echo "    brew install gh"
  echo "(no Homebrew? get gh at https://cli.github.com)"
  exit 1
fi

echo ">> checking GitHub login"
gh auth status >/dev/null 2>&1 || gh auth login

if git remote get-url origin >/dev/null 2>&1; then
  echo ">> remote exists, pushing"
  git push -u origin main
else
  echo ">> creating GitHub repo + pushing"
  gh repo create "$REPO" $VISIBILITY --source=. --remote=origin --push
fi

echo ""
echo "DONE -> https://github.com/$REPO"
echo "Install line for users:  pip install git+https://github.com/$REPO"
