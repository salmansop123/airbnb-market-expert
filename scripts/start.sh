#!/usr/bin/env bash
# Start StayPrice AI frontend + backend in one terminal.
# Usage (from repo root):  ./scripts/start.sh
# Stop with Ctrl+C

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT/apps/api"
WEB_DIR="$ROOT/apps/web"
LOG_DIR="$ROOT/scripts/.logs"
PID_FILE="$LOG_DIR/start.pids"

mkdir -p "$LOG_DIR"

# Load .env if present (safe KEY=VALUE parser — do not bash-source; spaces break source)
if [[ -f "$ROOT/.env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    # skip blanks and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # only KEY=VALUE lines
    [[ "$line" == *"="* ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    # strip optional surrounding quotes
    if [[ "$val" =~ ^\".*\"$ ]]; then
      val="${val:1:-1}"
    elif [[ "$val" =~ ^\'.*\'$ ]]; then
      val="${val:1:-1}"
    fi
    # export even if value contains spaces
    export "$key=$val"
  done < "$ROOT/.env"
fi

export PYTHONPATH="${API_DIR}${PYTHONPATH:+:$PYTHONPATH}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://stayprice:stayprice@localhost:5436/stayprice}"
export DATABASE_URL_SYNC="${DATABASE_URL_SYNC:-postgresql://stayprice:stayprice@localhost:5436/stayprice}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6382/0}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6382/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6382/1}"
export SECRET_KEY="${SECRET_KEY:-dev-secret-change-me}"
export APP_ENV="${APP_ENV:-development}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

cleanup() {
  echo ""
  echo "Stopping StayPrice AI…"
  if [[ -f "$PID_FILE" ]]; then
    while read -r pid; do
      if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
      fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
  fi
  # Fallback: kill anything we started on these ports
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${API_PORT}/tcp" 2>/dev/null || true
    fuser -k "${WEB_PORT}/tcp" 2>/dev/null || true
  fi
  echo "Stopped."
  exit 0
}

trap cleanup INT TERM

# Resolve Python / uvicorn
if [[ -x "$API_DIR/.venv/bin/uvicorn" ]]; then
  UVICORN="$API_DIR/.venv/bin/uvicorn"
elif command -v uvicorn >/dev/null 2>&1; then
  UVICORN="uvicorn"
else
  echo "Error: uvicorn not found. Create the API venv first:"
  echo "  cd apps/api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Resolve npm / next
if [[ ! -d "$WEB_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies…"
  (cd "$WEB_DIR" && npm install)
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is not installed."
  exit 1
fi

: > "$PID_FILE"

echo "========================================"
echo "  StayPrice AI — starting services"
echo "========================================"
echo "  Backend:  http://localhost:${API_PORT}"
echo "  Frontend: http://localhost:${WEB_PORT}"
echo "  API docs: http://localhost:${API_PORT}/v1/docs"
echo "  Logs:     $LOG_DIR/"
echo "  Press Ctrl+C to stop both."
echo "========================================"
echo ""

# Backend
(
  cd "$API_DIR"
  "$UVICORN" app.main:app --host 0.0.0.0 --port "$API_PORT" --reload
) >"$LOG_DIR/backend.log" 2>&1 &
API_PID=$!
echo "$API_PID" >> "$PID_FILE"
echo "[ok] Backend started (pid $API_PID) → logging to scripts/.logs/backend.log"

# Frontend
(
  cd "$WEB_DIR"
  npm run dev -- --port "$WEB_PORT"
) >"$LOG_DIR/frontend.log" 2>&1 &
WEB_PID=$!
echo "$WEB_PID" >> "$PID_FILE"
echo "[ok] Frontend started (pid $WEB_PID) → logging to scripts/.logs/frontend.log"
echo ""

# Stream both logs to this terminal
tail -n +1 -F "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" &
TAIL_PID=$!
echo "$TAIL_PID" >> "$PID_FILE"

# Wait until either process exits
wait "$API_PID" "$WEB_PID" 2>/dev/null || true
cleanup
