# HANDOFF — publish `dopamine` to GitHub

## Mission
Publish this folder as a public GitHub repo at `superpowerdevk/dopamine` so users can
install it with `pip install git+https://github.com/superpowerdevk/dopamine`.
It is a self-contained, pip-installable Python package (DB-backed, provably-fair
game engine for agents). Pure Python 3 stdlib, no dependencies, no network, no chain.

## What's in here
```
dopamine-repo/
├── setup.sh            # one-shot: git init -> commit -> create repo -> push
├── pyproject.toml      # package metadata + `dopamine` console entry point
├── README.md           # user-facing install + usage
├── LICENSE             # MIT
├── .gitignore
├── HANDOFF.md          # this file
└── dopamine/
    ├── __init__.py     # the engine (CLI in main())
    └── __main__.py     # enables `python -m dopamine`
```

## Prerequisites (install if missing)
- git  ->  xcode-select --install
- GitHub CLI  ->  brew install gh   (or https://cli.github.com)
- GitHub auth ->  gh auth login     (the script triggers this automatically if needed)

## Fastest path (one command, from inside this folder)
```
bash setup.sh
```
That inits git, commits, creates the GitHub repo, and pushes. Default is PUBLIC.
Edit the REPO or VISIBILITY variables at the top of setup.sh to change owner/name or
make it private.

## Manual path (if not using the script)
Run one line at a time. Do NOT run git init in the home directory.
```
cd <this-folder>
git init
git add .
git commit -m "dopamine v1.0.0"
git branch -M main
gh repo create superpowerdevk/dopamine --public --source=. --remote=origin --push
```

## Verify after push
```
python3 -m venv /tmp/verify && source /tmp/verify/bin/activate
pip install "git+https://github.com/superpowerdevk/dopamine"
dopamine register --agent test && dopamine leaderboard
deactivate
```
Expect JSON output and a `dopamine` command on PATH.

## Known pitfalls (already hit, avoid these)
- Never run `git init`/`git add .` from `~` — it tries to swallow the entire home
  folder. If it happened: `rm -rf ~/.git` (deletes only git metadata, not your files).
- Pasting multi-line blocks with `# comments` into zsh breaks (globbing). Run commands
  individually or use setup.sh, which has no inline-comment hazards.
- Branch must be `main` (not `master`) or the push mismatches.
- Create the GitHub repo EMPTY (no auto-README) if doing it via the web; the script
  handles this correctly via `gh`.

## Notes
- pip installs from git only re-pull when the ref changes. For updates, bump `version`
  in pyproject.toml and tag, or users run `pip install --force-reinstall git+...`.
- The runtime DB defaults to `dopamine.db` in the working directory; override with the
  `DOPAMINE_DB` env var to share one leaderboard across agents.
