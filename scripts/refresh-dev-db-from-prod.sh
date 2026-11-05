#!/usr/bin/env bash
# Copy PRODUCTION's database onto STAGING (lily-cafe-pos-dev) — one direction only.
#
#   lily-cafe-pos  (production, READ-ONLY)  ──►  lily-cafe-pos-dev  (staging, OVERWRITTEN)
#
# The apps are hardcoded, not parameters, so this can never run the other way.
# Production is only read from: a consistent snapshot is taken with SQLite's backup API
# (never a raw copy of the live file) into /tmp on the prod machine's root filesystem,
# downloaded, and deleted. Prod is never stopped, restarted or written to on its volume.
#
# Staging's /data/restaurant.db is REPLACED (the old one is kept once as
# /data/restaurant.db.pre-refresh) and the dev machine is restarted.
#
# Needs: flyctl (logged in), python3, curl. Usage: scripts/refresh-dev-db-from-prod.sh
set -euo pipefail

readonly PROD=lily-cafe-pos          # SOURCE — read only
readonly DEV=lily-cafe-pos-dev       # TARGET — the only app ever written to or restarted
readonly DB=/data/restaurant.db
readonly DEV_URL="https://$DEV.fly.dev/"
readonly PROD_URL="https://$PROD.fly.dev/"
readonly TABLES="orders inventory_items"

die() { echo "refresh-dev-db: $*" >&2; exit 1; }
say() { echo "==> $*"; }

# Belt and braces: the target must be the dev app, and never the source.
[ "$DEV" != "$PROD" ] && [ "${DEV%-dev}" != "$DEV" ] || die "target is not a -dev app — refusing"

command -v flyctl >/dev/null || die "flyctl not found"
command -v python3 >/dev/null || die "python3 not found"
command -v curl >/dev/null || die "curl not found"

# ---------------------------------------------------------------------------
# Helper run on the machines (python3 + stdlib sqlite3 are in the image). Shipped
# base64-encoded so no shell quoting is involved. Every op except `install` only
# reads; `install` refuses to run anywhere but the dev app.
# ---------------------------------------------------------------------------
read -r -d '' REMOTE_PY <<'PY' || true
import hashlib, os, sqlite3, sys

TMP_PREFIX = "/tmp/lily-refresh-"
op, args = sys.argv[1], sys.argv[2:]

def out(**kv):
    for k, v in kv.items():
        print(f"@@{k}={v}")

def ro(path):
    # mode=ro: this connection cannot write, even by accident.
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)

def counts(conn, tables):
    for t in tables:
        out(**{t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]})

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def tmp_only(path):
    if not path.startswith(TMP_PREFIX) or "/" in path[len(TMP_PREFIX):]:
        sys.exit(f"refusing path outside {TMP_PREFIX}*: {path}")

if op == "counts":                      # counts <db> <tables...>
    conn = ro(args[0]); counts(conn, args[1:]); conn.close()

elif op == "snapshot":                  # snapshot <live-db> <tmp-dst> <tables...>
    src_path, dst_path, tables = args[0], args[1], args[2:]
    tmp_only(dst_path)
    if os.path.exists(dst_path):
        sys.exit(f"{dst_path} already exists")
    src, dst = ro(src_path), sqlite3.connect(dst_path)
    src.backup(dst)                     # one step, one read transaction: consistent
    src.close()
    ok = dst.execute("PRAGMA integrity_check").fetchone()[0]
    dst.execute("PRAGMA journal_mode=DELETE")   # self-contained single file
    counts(dst, tables); dst.close()
    out(integrity=ok, sha256=sha(dst_path), bytes=os.path.getsize(dst_path))

elif op == "rm_tmp":                    # rm_tmp <tmp-path>
    tmp_only(args[0])
    if os.path.exists(args[0]):
        os.remove(args[0])
    out(gone=str(not os.path.exists(args[0])).lower())

elif op == "exists":                    # exists <path>
    out(exists=str(os.path.exists(args[0])).lower())

elif op == "install":                   # install <incoming> <db> <sha256>  (dev only)
    if os.environ.get("FLY_APP_NAME") != "lily-cafe-pos-dev":
        sys.exit(f"install refused on app {os.environ.get('FLY_APP_NAME')!r}")
    incoming, db, want = args
    got = sha(incoming)
    if got != want:
        sys.exit(f"uploaded file sha256 {got} != snapshot {want}")
    conn = ro(incoming)
    ok = conn.execute("PRAGMA integrity_check").fetchone()[0]; conn.close()
    if ok != "ok":
        sys.exit(f"uploaded file failed integrity_check: {ok}")
    if os.path.exists(db):
        os.replace(db, db + ".pre-refresh")
    # A stale WAL from the old database would be replayed onto the new one.
    for suffix in ("-wal", "-shm", "-journal"):
        if os.path.exists(db + suffix):
            os.remove(db + suffix)
    os.replace(incoming, db)            # same volume: atomic rename
    out(installed="true")

else:
    sys.exit(f"unknown op {op}")
PY
REMOTE_B64=$(printf '%s' "$REMOTE_PY" | base64 | tr -d '\n')

# The one machine of an app that is started and has /data mounted.
data_machine() {
  flyctl machine list -a "$1" --json | python3 -c '
import json, sys
ms = [m for m in json.load(sys.stdin)
      if m.get("state") == "started"
      and any(x.get("path") == "/data" for x in (m.get("config") or {}).get("mounts") or [])]
if len(ms) != 1:
    sys.exit(f"expected exactly one started machine with /data, found {len(ms)}")
print(ms[0]["id"])'
}

# Fingerprint used to prove prod was not restarted/updated: id|state|instance|updated_at.
machine_fingerprint() {
  flyctl machine list -a "$1" --json | python3 -c '
import json, sys
m = [m for m in json.load(sys.stdin) if m["id"] == sys.argv[1]][0]
print("|".join(str(m.get(k)) for k in ("id", "state", "instance_id", "updated_at")))' "$2"
}

# remote <app> <machine> <op> <args...> — runs the helper, prints its @@k=v lines as k=v.
remote() {
  local app=$1 machine=$2; shift 2
  local out
  out=$(flyctl ssh console -q -a "$app" --machine "$machine" \
        -C "python3 -c \"import base64;exec(base64.b64decode('$REMOTE_B64'))\" $*" 2>&1) \
    || { echo "$out" >&2; return 1; }
  printf '%s\n' "$out" | tr -d '\r' | sed -n 's/^@@//p'
}
field() { sed -n "s/^$1=//p" <<<"$2"; }

live_commit() {
  curl -fsS --max-time 15 "$1" 2>/dev/null |
    grep -o '"commit": *"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' || true
}

# ---------------------------------------------------------------------------
cat <<EOF

  This OVERWRITES the STAGING database:
      $DEV:$DB   <==  snapshot of  $PROD:$DB
  Staging's current data is replaced (kept once as $DB.pre-refresh) and
  the $DEV machine is restarted. Production is only read.

EOF
[ -r /dev/tty ] || die "needs an interactive terminal to confirm"
printf 'Type the TARGET app name (%s) to continue: ' "$DEV" > /dev/tty
read -r answer < /dev/tty
[ "$answer" = "$DEV" ] || die "not confirmed — nothing done"

PROD_M=$(data_machine "$PROD") || die "could not pick the prod machine"
DEV_M=$(data_machine "$DEV") || die "could not pick the dev machine"
say "prod machine $PROD_M, dev machine $DEV_M"

STAMP=$(date +%Y%m%d-%H%M%S)-$$
PROD_TMP="/tmp/lily-refresh-$STAMP.db"
DEV_INCOMING="$DB.incoming-$STAMP"
LOCAL_DIR=$(mktemp -d "${TMPDIR:-/tmp}/lily-refresh.XXXXXX")   # outside the repo
LOCAL_DB="$LOCAL_DIR/snapshot.db"
PROD_TMP_MADE=0

cleanup() {
  rm -rf "$LOCAL_DIR"
  if [ "$PROD_TMP_MADE" = 1 ]; then
    remote "$PROD" "$PROD_M" rm_tmp "$PROD_TMP" >/dev/null 2>&1 ||
      echo "WARNING: could not delete $PROD_TMP on $PROD — remove it by hand" >&2
  fi
}
trap cleanup EXIT

# --- 1. Production: record state, snapshot (read only) --------------------------------
PROD_FP_BEFORE=$(machine_fingerprint "$PROD" "$PROD_M")
PROD_COMMIT=$(live_commit "$PROD_URL")
[ -n "$PROD_COMMIT" ] || die "$PROD_URL is not answering — not touching anything"
PROD_BEFORE=$(remote "$PROD" "$PROD_M" counts "$DB" $TABLES) || die "could not read prod counts"
DEV_BEFORE=$(remote "$DEV" "$DEV_M" counts "$DB" $TABLES) || DEV_BEFORE="(unreadable)"

say "snapshotting $PROD:$DB -> $PROD_TMP (backup API)"
PROD_TMP_MADE=1
SNAP=$(remote "$PROD" "$PROD_M" snapshot "$DB" "$PROD_TMP" $TABLES) || die "snapshot failed"
SHA=$(field sha256 "$SNAP")
[ "$(field integrity "$SNAP")" = ok ] || die "snapshot failed integrity_check: $SNAP"
say "snapshot ok: $(field bytes "$SNAP") bytes, sha256 $SHA"

# --- 2. Download, then remove the snapshot from prod ----------------------------------
flyctl ssh sftp get -a "$PROD" --machine "$PROD_M" "$PROD_TMP" "$LOCAL_DB" >/dev/null
LOCAL_SHA=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$LOCAL_DB")
[ "$LOCAL_SHA" = "$SHA" ] || die "download corrupted: $LOCAL_SHA != $SHA"
[ "$(field gone "$(remote "$PROD" "$PROD_M" rm_tmp "$PROD_TMP")")" = true ] ||
  die "snapshot still present on prod at $PROD_TMP"
PROD_TMP_MADE=0
say "downloaded and verified; prod temp snapshot deleted"

# --- 3. Upload to a temp path on dev ----------------------------------------------------
# `flyctl ssh sftp put` exists from flyctl ~v0.3.2xx; older versions only have the
# interactive `sftp shell`, whose put exits 0 even on failure. Either way the sha256 is
# checked on dev before anything is replaced.
if flyctl ssh sftp put --help >/dev/null 2>&1; then
  flyctl ssh sftp put -a "$DEV" --machine "$DEV_M" -m 0644 "$LOCAL_DB" "$DEV_INCOMING"
else
  printf 'put %s %s\n' "$LOCAL_DB" "$DEV_INCOMING" |
    flyctl ssh sftp shell -a "$DEV" --machine "$DEV_M"
fi
[ "$(field exists "$(remote "$DEV" "$DEV_M" exists "$DEV_INCOMING")")" = true ] ||
  die "upload did not arrive at $DEV:$DEV_INCOMING"
rm -rf "$LOCAL_DIR"                      # customer data: not needed locally any more

# --- 4. Swap into place on dev and restart dev ------------------------------------------
say "installing on $DEV (sha256 checked on the machine)"
[ "$(field installed "$(remote "$DEV" "$DEV_M" install "$DEV_INCOMING" "$DB" "$SHA")")" = true ] ||
  die "install on $DEV failed"
say "restarting $DEV"
flyctl machine restart -a "$DEV" "$DEV_M"

for ((i = 1; i <= 30; i++)); do
  DEV_COMMIT=$(live_commit "$DEV_URL")
  [ -n "$DEV_COMMIT" ] && break
  sleep 5
done
[ -n "${DEV_COMMIT:-}" ] || die "$DEV_URL did not come back after restart"

# --- 5. Verify ---------------------------------------------------------------------------
DEV_AFTER=$(remote "$DEV" "$DEV_M" counts "$DB" $TABLES) || die "could not read dev counts"
PROD_AFTER=$(remote "$PROD" "$PROD_M" counts "$DB" $TABLES) || die "could not read prod counts"
PROD_FP_AFTER=$(machine_fingerprint "$PROD" "$PROD_M")
PROD_COMMIT_AFTER=$(live_commit "$PROD_URL")
PROD_TMP_LEFT=$(field exists "$(remote "$PROD" "$PROD_M" exists "$PROD_TMP")")

echo
printf '%-16s %12s %12s %12s %12s %12s\n' table "prod before" snapshot "prod after" "dev before" "dev after"
fail=0
for t in $TABLES; do
  pb=$(field "$t" "$PROD_BEFORE"); s=$(field "$t" "$SNAP"); pa=$(field "$t" "$PROD_AFTER")
  db=$(field "$t" "$DEV_BEFORE"); da=$(field "$t" "$DEV_AFTER")
  printf '%-16s %12s %12s %12s %12s %12s\n' "$t" "$pb" "$s" "$pa" "${db:--}" "$da"
  [ "$da" = "$s" ] || { echo "  ✗ dev $t ($da) != snapshot ($s)"; fail=1; }
  [ "$pa" -ge "$pb" ] || { echo "  ✗ prod $t went DOWN ($pb -> $pa)"; fail=1; }
  [ "$pa" = "$pb" ] || echo "  (prod $t grew $pb -> $pa during the run — live trading)"
done
echo
[ "$PROD_FP_BEFORE" = "$PROD_FP_AFTER" ] &&
  echo "prod machine unchanged (not restarted/updated): $PROD_FP_AFTER" ||
  { echo "✗ prod machine changed: $PROD_FP_BEFORE -> $PROD_FP_AFTER"; fail=1; }
[ -n "$PROD_COMMIT_AFTER" ] && echo "prod serving, commit $PROD_COMMIT_AFTER" ||
  { echo "✗ prod not answering at $PROD_URL"; fail=1; }
[ "$PROD_TMP_LEFT" = false ] && echo "prod temp snapshot $PROD_TMP: gone" ||
  { echo "✗ prod temp snapshot still at $PROD_TMP"; fail=1; }
echo "dev serving, commit $DEV_COMMIT (prod is $PROD_COMMIT_AFTER)"

[ "$fail" = 0 ] || die "VERIFICATION FAILED — see above"
echo "Done: $DEV now has production's data as of this run."
