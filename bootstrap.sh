#!/usr/bin/env bash
# Fresh-session bootstrap (Arena sandbox). From an EMPTY workspace:
#   1. save the GitHub token:  mkdir -p ~/.cache/secrets && printf %s "$TOKEN" > ~/.cache/secrets/gh_token
#   2. git clone https://github.com/zainkhan122/History.git ~/History   (use the token if the repo is private)
#   3. source ~/History/bootstrap.sh
# Restores the toolchain into ~/.cache (not persisted, not counted against the workspace budget),
# wires git auth to the token file, pulls nothing heavy until an episode needs it, then prints the resume pack.
R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod 700 "$HOME/.cache/secrets" 2>/dev/null || true
if [ -s "$HOME/.cache/secrets/gh_token" ]; then
  git -C "$R" config credential.helper '!f() { echo username=x-access-token; echo "password=$(cat $HOME/.cache/secrets/gh_token)"; }; f'
  git -C "$R" config user.name  >/dev/null || git -C "$R" config user.name "zainkhan122"
  git -C "$R" config user.email >/dev/null || git -C "$R" config user.email "zainkhan122@users.noreply.github.com"
  git -C "$R" pull -q --ff-only origin main && echo "repo up to date @ $(git -C "$R" rev-parse --short HEAD)"
else
  echo "!! no token at ~/.cache/secrets/gh_token — read-only mode (ask the owner for the token)"
fi
# shellcheck disable=SC1091
source "$R/reelkit/setup.sh"
python3 "$R/tools/state.py" show
echo; echo "Next: read $R/RESUME.md (full context) — then continue with the first item under 'next'."
