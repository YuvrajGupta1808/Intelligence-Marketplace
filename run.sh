#!/usr/bin/env bash
# Start the deep-finance-research app. Unbrowse starts automatically unless --no-unbrowse.
# Usage:
#   ./run.sh                        # backend + Unbrowse (default)
#   ./run.sh --streamlit             # backend + Unbrowse + Streamlit
#   ./run.sh --no-unbrowse           # backend only (Unbrowse must be running elsewhere)
#   ./run.sh --no-unbrowse --streamlit
#   ./run.sh --ui                   # backend + Unbrowse + frontend (requires deep-agents-ui)

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

UNBROWSE_PID=""
UI_PID=""
STREAMLIT_PID=""
UI_DIR="${DEEP_AGENTS_UI_PATH:-$ROOT/../deep-agents-ui}"

cleanup() {
  if [ -n "$UNBROWSE_PID" ] && kill -0 "$UNBROWSE_PID" 2>/dev/null; then
    echo "Stopping Unbrowse (PID $UNBROWSE_PID)..."
    kill "$UNBROWSE_PID" 2>/dev/null || true
  fi
  if [ -n "$UI_PID" ] && kill -0 "$UI_PID" 2>/dev/null; then
    echo "Stopping UI (PID $UI_PID)..."
    kill "$UI_PID" 2>/dev/null || true
  fi
  if [ -n "$STREAMLIT_PID" ] && kill -0 "$STREAMLIT_PID" 2>/dev/null; then
    echo "Stopping Streamlit (PID $STREAMLIT_PID)..."
    kill "$STREAMLIT_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# Start Unbrowse by default unless --no-unbrowse is passed
START_UNBROWSE=true
for arg in "$@"; do
  if [ "$arg" = "--no-unbrowse" ]; then
    START_UNBROWSE=false
    echo "Note: Unbrowse disabled. Start it elsewhere (e.g. unbrowse setup) for SEC/EDGAR data."
    break
  fi
done

if [ "$START_UNBROWSE" = true ]; then
  if command -v unbrowse >/dev/null 2>&1; then
    echo "Starting Unbrowse server in background..."
    unbrowse setup &
    UNBROWSE_PID=$!
    sleep 3
    if kill -0 "$UNBROWSE_PID" 2>/dev/null; then
      echo "Unbrowse running (PID $UNBROWSE_PID). Waiting for health endpoint..."
    fi
    UNBROWSE_URL="${UNBROWSE_URL:-http://localhost:6969}"
    for i in $(seq 1 30); do
      if curl -sf "${UNBROWSE_URL}/health" >/dev/null 2>&1; then
        echo "Unbrowse ready at $UNBROWSE_URL"
        break
      fi
      if [ $i -eq 30 ]; then
        echo "Warning: Unbrowse health check did not succeed after 30s. Backend will run but Unbrowse tools may fail."
      fi
      sleep 1
    done
  else
    echo "Warning: 'unbrowse' not found. Install with: npm install -g unbrowse. Backend will run but Unbrowse tools will return errors."
  fi
fi

# Optional: start Streamlit app in background
for arg in "$@"; do
  if [ "$arg" = "--streamlit" ]; then
    if [ -f "$ROOT/app.py" ]; then
      echo "Starting Streamlit app (app.py) in background..."
      if command -v uv >/dev/null 2>&1; then
        (cd "$ROOT" && uv run streamlit run app.py --server.headless true) &
      else
        (cd "$ROOT" && streamlit run app.py --server.headless true) &
      fi
      STREAMLIT_PID=$!
      sleep 3
      if kill -0 "$STREAMLIT_PID" 2>/dev/null; then
        echo "Streamlit running (PID $STREAMLIT_PID). Open http://localhost:8501"
      fi
    else
      echo "Warning: app.py not found in $ROOT"
    fi
    break
  fi
done

# Optional: start Node frontend in background
for arg in "$@"; do
  if [ "$arg" = "--ui" ]; then
    if [ -d "$UI_DIR" ] && [ -f "$UI_DIR/package.json" ]; then
      echo "Starting frontend at $UI_DIR..."
      (cd "$UI_DIR" && yarn dev) &
      UI_PID=$!
      sleep 2
      echo "UI running (PID $UI_PID). Open http://localhost:3000"
    else
      echo "Warning: UI dir not found at $UI_DIR. Set DEEP_AGENTS_UI_PATH or clone deep-agents-ui to ../deep-agents-ui"
    fi
    break
  fi
done

# Backend (foreground so logs are visible and script stays in charge)
echo "Starting LangGraph backend..."
if command -v uv >/dev/null 2>&1; then
  exec uv run --group dev langgraph dev
else
  exec langgraph dev
fi
