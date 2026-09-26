#!/usr/bin/env bash
# Deploy the backend to production Fly — and prove it shipped.
#
# `flyctl deploy` builds from the working directory, not from git, so a tree that
# is behind origin/main deploys a stale image and every signal still says success.
# This refuses unless the tree is exactly origin/main, then checks that the live
# app reports the commit it was given. See docs/INVENTORY_PLAN.md.
set -euo pipefail

APP=lily-cafe-pos                      # the local fly.toml may name the dev app
URL="https://$APP.fly.dev/"
ATTEMPTS=30 INTERVAL=5                 # ~2.5 minutes to converge

die() { echo "deploy-backend: $*" >&2; exit 1; }

cd "$(git rev-parse --show-toplevel)"
command -v flyctl >/dev/null || die "flyctl not found"

git fetch -q origin main
[ -z "$(git status --porcelain)" ] || die "working tree is dirty — refusing"
SHA=$(git rev-parse HEAD)
[ "$SHA" = "$(git rev-parse origin/main)" ] || die "HEAD is not origin/main — refusing"

echo "Deploying $SHA to $APP"
flyctl deploy -a "$APP" --build-arg GIT_SHA="$SHA"

for ((i = 1; i <= ATTEMPTS; i++)); do
  live=$(curl -fsS --max-time 10 "$URL" 2>/dev/null |
    grep -o '"commit": *"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' || true)
  if [ "$live" = "$SHA" ]; then
    echo "Verified: $URL is serving $SHA"
    exit 0
  fi
  echo "Waiting for $SHA (live: ${live:-no response}) [$i/$ATTEMPTS]"
  sleep "$INTERVAL"
done

die "DEPLOY NOT VERIFIED — $URL reports '${live:-nothing}', expected $SHA.
The release may have succeeded but production is not running this commit."
