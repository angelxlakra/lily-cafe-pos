#!/usr/bin/env bash
# Deploy the backend to Fly — and prove it shipped.
#
#   scripts/deploy-backend.sh prod [--dry-run]   origin/main        -> lily-cafe-pos
#   scripts/deploy-backend.sh dev  [--dry-run]   origin/pre-release -> lily-cafe-pos-dev
#
# `flyctl deploy` builds from the working directory, not from git, so a tree that
# is behind its branch deploys a stale image and every signal still says success.
# This refuses unless HEAD is exactly the target's branch on origin, then checks
# that the live app reports the commit it was given. See docs/INVENTORY_PLAN.md.
#
# The target is required. Production restarts the machine the cafe is using, so it
# should only ever happen because someone typed "prod" — never by leaving a word
# off a dev deploy.
set -euo pipefail

ATTEMPTS=30 INTERVAL=5                 # ~2.5 minutes to converge

die()  { echo "deploy-backend: $*" >&2; exit 1; }
warn() { echo "deploy-backend: warning: $*" >&2; }
usage() {
  cat >&2 <<'EOF'
usage: scripts/deploy-backend.sh <prod|dev> [--dry-run]

  prod   deploy origin/main        to lily-cafe-pos      (production)
  dev    deploy origin/pre-release to lily-cafe-pos-dev  (staging)

  --dry-run   run every guard and print what would be deployed; never calls flyctl
EOF
  exit 2
}

TARGET= DRY_RUN=
for arg in "$@"; do
  case "$arg" in
    prod|dev)  [ -z "$TARGET" ] || { echo "deploy-backend: one target only" >&2; usage; }
               TARGET=$arg ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage ;;
    *)         echo "deploy-backend: unknown argument '$arg'" >&2; usage ;;
  esac
done
[ -n "$TARGET" ] || { echo "deploy-backend: no target given" >&2; usage; }

# Every value below is chosen here, never read from fly.toml: the committed
# fly.toml names the dev app, so its app name must not decide where code goes.
case "$TARGET" in
  prod) BRANCH=main        APP=lily-cafe-pos ;;
  dev)  BRANCH=pre-release APP=lily-cafe-pos-dev ;;
esac
URL="https://$APP.fly.dev/"

# The commit GET / reports, or nothing if the app does not answer.
live_commit() {
  curl -fsS --max-time 10 "$URL" 2>/dev/null |
    grep -o '"commit": *"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' || true
}

cd "$(git rev-parse --show-toplevel)"
[ -n "$DRY_RUN" ] || command -v flyctl >/dev/null || die "flyctl not found"
command -v curl >/dev/null || die "curl not found"

# Explicit refspec so origin/$BRANCH is updated even where fetch config is narrow.
git fetch -q origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH" ||
  die "could not fetch origin/$BRANCH — refusing"

# Modified tracked files are code that is not HEAD but would ship with it.
dirty=$(git status --porcelain --untracked-files=no)
[ -z "$dirty" ] || die "tracked files are modified — refusing:
$dirty"

# Untracked files outside backend/ never reach the image (.dockerignore keeps only
# backend/), so they are not worth blocking on. Ones under backend/ may ship.
stray=$(git ls-files --others --exclude-standard -- backend/)
[ -z "$stray" ] || warn "untracked files under backend/ may be copied into the image:
$(sed 's/^/  /' <<<"$stray")"

SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git rev-parse "origin/$BRANCH")
[ "$SHA" = "$REMOTE_SHA" ] || die "HEAD is not origin/$BRANCH — refusing to deploy to $APP.
$(printf '  %-19s %s (%s)\n' HEAD "$SHA" "$(git rev-parse --abbrev-ref HEAD)")
$(printf '  %-19s %s' "origin/$BRANCH" "$REMOTE_SHA")
Run: git checkout $BRANCH && git pull --ff-only"

if [ -n "$DRY_RUN" ]; then
  live=$(live_commit)
  cat <<EOF
Dry run — all guards passed. Nothing deployed.
  target   $TARGET
  branch   origin/$BRANCH
  app      $APP
  sha      $SHA
  url      $URL
  live now ${live:-unknown (no response)}
  would run: flyctl deploy -a $APP --build-arg GIT_SHA=$SHA
EOF
  exit 0
fi

echo "Deploying $SHA (origin/$BRANCH) to $APP"
flyctl deploy -a "$APP" --build-arg GIT_SHA="$SHA"

for ((i = 1; i <= ATTEMPTS; i++)); do
  live=$(live_commit)
  if [ "$live" = "$SHA" ]; then
    echo "Verified: $URL is serving $SHA"
    exit 0
  fi
  echo "Waiting for $SHA (live: ${live:-no response}) [$i/$ATTEMPTS]"
  sleep "$INTERVAL"
done

die "DEPLOY NOT VERIFIED — $URL reports '${live:-nothing}', expected $SHA.
The release may have succeeded but $APP is not running this commit."
