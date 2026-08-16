#!/usr/bin/env bash
# Launch a match in YOUR terminal, logs in front of you. The bash/zsh twin of
# play.fish, for machines without fish.
#
#   scripts/play.sh uoh-sqak https://their-tunnel.example/mcp [--role police] [peer args]
#
# Loads the negotiated contract for that opponent from config/opponents/<name>.env,
# so the terms, dialect, scent model, doctrine and email mode are whatever was
# agreed with THEM - never edited into the committed constitution.
#
# Two things this does that play.fish cannot:
#   * it finds a working runner instead of assuming `uv run` (see §runner), so an
#     editable install that macOS has quietly broken is reported, not tripped over;
#   * it refuses the one mistake that cannot be undone - mailing the lecturer a
#     warm-up - by asking the real config loader what would actually be sent.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo"

opponent="${1:-}"
url="${2:-}"
if [ -z "$opponent" ] || [ -z "$url" ]; then
    echo "usage: scripts/play.sh <opponent-name> <their-/mcp-url> [peer args...]" >&2
    echo "       e.g. scripts/play.sh uoh-sqak https://xxxx.trycloudflare.com/mcp" >&2
    exit 2
fi
shift 2
rest=("$@")

envfile="config/opponents/$opponent.env"
if [ ! -f "$envfile" ]; then
    echo "no contract file: $envfile" >&2
    echo "available contracts:" >&2
    for f in config/opponents/*.env; do
        [ -e "$f" ] || continue
        b="$(basename "$f" .env)"
        [ "$b" = "TEMPLATE" ] && continue
        echo "  $b" >&2
    done
    echo "start a new one from config/opponents/TEMPLATE.env" >&2
    exit 2
fi

# The contract files are plain KEY=value and document this exact form themselves.
set -a
# shellcheck disable=SC1090
. "$envfile"
set +a
export P2P_OPPONENT_URL="$url"

# Default role is police unless the caller passes --role; keep it visible either way.
role="police"
for i in "${!rest[@]}"; do
    if [ "${rest[$i]}" = "--role" ]; then role="${rest[$((i + 1))]:-police}"; fi
done
has_role=false
for a in ${rest[@]+"${rest[@]}"}; do [ "$a" = "--role" ] && has_role=true; done
$has_role || rest=(--role "$role" ${rest[@]+"${rest[@]}"})

config_dir="config/$role"
for i in "${!rest[@]}"; do
    if [ "${rest[$i]}" = "--config-dir" ]; then config_dir="${rest[$((i + 1))]:-$config_dir}"; fi
done

counted=false
for a in ${rest[@]+"${rest[@]}"}; do [ "$a" = "--counted" ] && counted=true; done

# Headless unless the caller explicitly asks for the window. cli.py runs the
# series on a worker thread and only mails the report *after* LiveView.run()
# returns (cli.py:52-58), so an open GUI holds the finished report hostage
# indefinitely - a counted result can sit unsent behind a window nobody knew to
# close. `--gui` opts back in and is consumed here rather than forwarded.
want_gui=false
filtered=()
for a in ${rest[@]+"${rest[@]}"}; do
    if [ "$a" = "--gui" ]; then want_gui=true; else filtered+=("$a"); fi
done
rest=(${filtered[@]+"${filtered[@]}"})
if [ "$want_gui" = false ]; then
    has_nogui=false
    for a in ${rest[@]+"${rest[@]}"}; do [ "$a" = "--no-gui" ] && has_nogui=true; done
    $has_nogui || rest+=(--no-gui)
fi

# --- runner -----------------------------------------------------------------
# On an iCloud-synced checkout, macOS keeps re-setting UF_HIDDEN on the venv's
# .pth files, and CPython 3.13 silently skips hidden .pth - which kills the
# editable install and every `uv run`. Clear the flag if we can, then put src on
# PYTHONPATH regardless, so the launch does not depend on winning that race.
py=".venv/bin/python"
[ -x "$py" ] || { echo "no .venv - run: uv sync --all-extras" >&2; exit 2; }

if ! "$py" -c "import p2p_pursuit" >/dev/null 2>&1; then
    chflags nohidden .venv/lib/python*/site-packages/*.pth 2>/dev/null || true
fi
export PYTHONPATH="$repo/src${PYTHONPATH:+:$PYTHONPATH}"
if ! "$py" -c "import p2p_pursuit" >/dev/null 2>&1; then
    echo "cannot import p2p_pursuit even with PYTHONPATH=$repo/src" >&2
    echo "try: uv sync --all-extras" >&2
    exit 2
fi
runner=(".venv/bin/p2p-pursuit")

# --- email guard ------------------------------------------------------------
# Ask the real loader what would be sent, rather than second-guessing the TOML
# defaults and the env overlay separately - they resolve in one place, so the
# guard should read that one place.
eff="$("$py" - "$config_dir" <<'PY'
import sys
from pathlib import Path
from p2p_pursuit.shared.config import load_role
_, peer = load_role(Path(sys.argv[1]))
print(peer.email_mode)
print(peer.email_recipient)
PY
)"
email_mode="$(printf '%s\n' "$eff" | sed -n 1p)"
email_to="$(printf '%s\n' "$eff" | sed -n 2p)"
lecturer="rmisegal+uoh26finalgame@gmail.com"

if [ "$counted" = false ] && [ "$email_mode" = "send" ] && [ "$email_to" = "$lecturer" ]; then
    echo "REFUSING: this is an uncounted run, but it would MAIL THE LECTURER" >&2
    echo "  recipient: $email_to" >&2
    echo "  a warm-up report cannot be unsent, and one counted game per opponent" >&2
    echo "  is sealed forever once filed (book 9.2.1)." >&2
    echo "  fix: add  P2P_EMAIL_MODE=draft  to $envfile" >&2
    exit 3
fi

echo "=== contract: $opponent ==="
echo "  opponent   $P2P_OPPONENT_URL"
echo "  dialect    ${P2P_DIALECT:-<config>}   alternate=${P2P_ALTERNATE_ROLES:-<config>}  rehandshake=${P2P_HANDSHAKE_PER_SUB_GAME:-<config>}"
echo "  scent      ${P2P_SCENT_MODEL:-<config>}   doctrine=${P2P_DOCTRINE:-<config>}"
echo "  enclosure  ${P2P_CLAIM_ENCLOSURE:-<config>}"
echo "  email      $email_mode -> $email_to"
echo "  args       ${rest[*]}"
echo

if [ "$counted" = true ]; then
    echo "This is a COUNTED match: one per opponent, sealed once filed."
    echo "The report goes to: $email_to"
    printf 'Type "counted" to proceed: '
    read -r confirm
    [ "$confirm" = "counted" ] || { echo "aborted" >&2; exit 3; }
    echo
fi

# The sealed artifacts under results/ are the evidence that counts, but the
# terminal narrative is what explains a match afterwards - so keep both.
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p logs
transcript="logs/$opponent-$stamp.log"
echo "  transcript $transcript"
echo

"${runner[@]}" peer ${rest[@]+"${rest[@]}"} 2>&1 | tee "$transcript"

# --- did the report actually leave? -----------------------------------------
# A played series and a delivered report are two different things, and the gap
# between them is silent: the result files land on disk either way. So say so
# out loud, and name the exact command that finishes the job.
echo
if grep -q "\[email\].*'delivered': True" "$transcript" \
   && ! grep -q "\[email\].*dry-run" "$transcript"; then
    echo "email: DELIVERED - $(grep -o "\[email\].*" "$transcript" | tail -1)"
elif grep -q "\[email\].*dry-run" "$transcript"; then
    echo "email: NOT SENT - the dry-run transport stood in for Gmail." >&2
    echo "  'delivered: True' above is the dry run reporting itself, not a mail server." >&2
elif grep -q "\[email\]" "$transcript"; then
    echo "email: NOT DELIVERED - $(grep -o "\[email\].*" "$transcript" | tail -1)" >&2
else
    latest="$(ls -td results/*/ 2>/dev/null | head -1)"
    echo "email: NEVER ATTEMPTED - the run ended before cli.py's report step." >&2
    if [ -n "$latest" ]; then
        res="$(ls "$latest"result_*.json 2>/dev/null | head -1)"
        [ -n "$res" ] && {
            echo "  the match itself is filed under $latest" >&2
            echo "  send it with:" >&2
            echo "    scripts/send_report.py $res --to <address>" >&2
        }
    fi
fi
