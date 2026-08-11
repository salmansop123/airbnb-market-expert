#!/usr/bin/env bash
# Debug helper: diagnose alembic ModuleNotFoundError
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API="$ROOT/apps/api"
DEBUG_LOG="/home/salman-mazhar/Drive/My project/airbnb-market-expert/.cursor/debug-dd6526.log"

# #region agent log
_dbg() {
  local hid="$1" msg="$2" data="$3"
  printf '%s\n' "{\"sessionId\":\"dd6526\",\"runId\":\"pre-fix\",\"hypothesisId\":\"${hid}\",\"location\":\"scripts/debug_alembic.sh\",\"message\":\"${msg}\",\"data\":${data},\"timestamp\":$(date +%s%3N)}" >> "$DEBUG_LOG"
}
# #endregion

WHICH="$(command -v alembic || true)"
WHICH_A="$(type -a alembic 2>&1 | tr '\n' '|' || true)"
_dbg "A" "which alembic resolves to" "{\"which\":\"${WHICH}\",\"typeA\":\"${WHICH_A}\"}"

VENV_ALEMBIC="$API/.venv/bin/alembic"
VENV_PY="$API/.venv/bin/python"
_dbg "B" "venv alembic binary exists" "{\"path\":\"$VENV_ALEMBIC\",\"exists\":$([ -x "$VENV_ALEMBIC" ] && echo true || echo false)}"

if [[ -x "$VENV_PY" ]]; then
  VENV_IMPORT="$($VENV_PY -c "import alembic,alembic.config; print(alembic.__file__+'|'+alembic.__version__)" 2>&1 || true)"
  _dbg "C" "venv python import alembic.config" "{\"result\":\"$(echo "$VENV_IMPORT" | sed 's/\"/\\\\\"/g')\"}"
else
  _dbg "C" "venv python missing" "{\"exists\":false}"
fi

SYS_IMPORT="$(/usr/bin/python3 -c "import alembic; print(getattr(alembic,'__file__',None)); import alembic.config" 2>&1 || true)"
_dbg "D" "system python import alembic.config" "{\"result\":\"$(echo "$SYS_IMPORT" | sed 's/\"/\\\\\"/g')\"}"

# Check if local alembic/ package dir shadows
SHADOW=""
[[ -f "$API/alembic/__init__.py" ]] && SHADOW="has_init" || SHADOW="no_init_only_env"
_dbg "E" "local apps/api/alembic directory" "{\"shadowCheck\":\"$SHADOW\",\"listing\":\"$(ls "$API/alembic" 2>/dev/null | tr '\n' ',')\"}"

echo "Diagnostic complete. Wrote logs to debug-dd6526.log"
echo "System alembic: $WHICH"
echo "Prefer: $VENV_ALEMBIC"
