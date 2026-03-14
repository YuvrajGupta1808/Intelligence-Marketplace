#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${TMPDIR:-/tmp}/proof-of-browse-logs"
mkdir -p "$LOG_DIR"

PIDS=()
MODE="${1:-demo}"

if [[ "$MODE" != "demo" && "$MODE" != "real" ]]; then
  echo "Usage: ./run.sh [demo|real]" >&2
  exit 1
fi

cleanup() {
  local code=$?
  trap - EXIT INT TERM
  if ((${#PIDS[@]} > 0)); then
    echo
    echo "Stopping app processes..."
    kill "${PIDS[@]}" >/dev/null 2>&1 || true
    wait "${PIDS[@]}" >/dev/null 2>&1 || true
  fi
  exit "$code"
}

trap cleanup EXIT INT TERM

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_http() {
  local method="$1"
  local url="$2"
  local name="$3"
  local attempts="${4:-60}"
  local i
  for ((i = 1; i <= attempts; i += 1)); do
    if curl -fsS -X "$method" "$url" >/dev/null 2>&1; then
      echo "$name is ready at $url"
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $name at $url" >&2
  return 1
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local name="$3"
  local attempts="${4:-60}"
  local i
  for ((i = 1; i <= attempts; i += 1)); do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "$name is ready on $host:$port"
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $name on $host:$port" >&2
  return 1
}

ensure_python_env() {
  local dir="$1"
  if [[ ! -x "$dir/.venv/bin/python" ]]; then
    echo "Creating Python virtualenv in $dir/.venv"
    python3 -m venv "$dir/.venv"
  fi
  if [[ ! -x "$dir/.venv/bin/uvicorn" ]]; then
    echo "Installing Python dependencies in $dir"
    (
      cd "$dir"
      source .venv/bin/activate
      pip install -e .[dev]
    )
    return
  fi
  if [[ "$dir" == "$ROOT_DIR/apps/planner-api" ]] && ! "$dir/.venv/bin/python" -c "import temporalio" >/dev/null 2>&1; then
    echo "Installing updated planner dependencies in $dir"
    (
      cd "$dir"
      source .venv/bin/activate
      pip install -e .[dev]
    )
  fi
}

ensure_node_env() {
  local dir="$1"
  if [[ ! -d "$dir/node_modules" ]]; then
    echo "Installing Node dependencies in $dir"
    (
      cd "$dir"
      npm install
    )
  fi
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required env var for $MODE mode: $name" >&2
    exit 1
  fi
}

start_service() {
  local name="$1"
  local workdir="$2"
  local logfile="$3"
  shift 3
  (
    cd "$workdir"
    "$@"
  ) >"$logfile" 2>&1 &
  local pid=$!
  PIDS+=("$pid")
  echo "Started $name (pid $pid). Log: $logfile"
}

require_cmd docker
require_cmd curl
require_cmd nc
require_cmd python3
require_cmd npm

echo "Preparing local environments..."
ensure_python_env "$ROOT_DIR/apps/planner-api"
ensure_python_env "$ROOT_DIR/apps/browser-worker"
ensure_python_env "$ROOT_DIR/apps/verifier-api"
ensure_node_env "$ROOT_DIR/apps/sponsor-runtime"
ensure_node_env "$ROOT_DIR/apps/web"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

export APP_MODE="$MODE"

if [[ "$MODE" == "real" ]]; then
  require_env OPENAI_API_KEY
  require_env X402_SOLANA_PRIVATE_KEY
  require_env X402_PAY_TO
  require_env ALKAHEST_RPC_URL
  require_env ALKAHEST_BUYER_PRIVATE_KEY
  require_env ALKAHEST_WORKER_PRIVATE_KEY
  require_env ALKAHEST_ORACLE_PRIVATE_KEY
  export PLANNER_PROVIDER="openai"
  export PAYMENT_MODE="real"
  export SETTLEMENT_MODE="alkahest"
else
  export PLANNER_PROVIDER="${PLANNER_PROVIDER:-auto}"
  export PAYMENT_MODE="${PAYMENT_MODE:-mock}"
  export SETTLEMENT_MODE="${SETTLEMENT_MODE:-app}"
fi

echo "Starting Docker infrastructure..."
(
  cd "$ROOT_DIR"
  docker compose -f infra/docker-compose.yml up -d
)

wait_for_port 127.0.0.1 5432 "Postgres"
wait_for_port 127.0.0.1 6379 "Redis"
wait_for_port 127.0.0.1 7233 "Temporal"
wait_for_http GET http://127.0.0.1:8088 "Temporal UI"

echo "Applying planner migrations..."
(
  cd "$ROOT_DIR/apps/planner-api"
  if [[ "$MODE" == "real" ]]; then
    .venv/bin/python scripts/migrate.py
  else
    POSTGRES_URL=sqlite:///./proof-of-browse.db .venv/bin/python scripts/migrate.py
  fi
)

echo "Starting app services..."
start_service \
  "planner-api" \
  "$ROOT_DIR/apps/planner-api" \
  "$LOG_DIR/planner-api.log" \
  bash -lc "export APP_MODE=\"$APP_MODE\" PLANNER_PROVIDER=\"$PLANNER_PROVIDER\" PAYMENT_MODE=\"$PAYMENT_MODE\" SETTLEMENT_MODE=\"$SETTLEMENT_MODE\"; if [[ \"$MODE\" == \"demo\" ]]; then export POSTGRES_URL=\"sqlite:///./proof-of-browse.db\"; fi; .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001"

start_service \
  "temporal-worker" \
  "$ROOT_DIR/apps/planner-api" \
  "$LOG_DIR/temporal-worker.log" \
  bash -lc "export APP_MODE=\"$APP_MODE\" PLANNER_PROVIDER=\"$PLANNER_PROVIDER\" PAYMENT_MODE=\"$PAYMENT_MODE\" SETTLEMENT_MODE=\"$SETTLEMENT_MODE\"; if [[ \"$MODE\" == \"demo\" ]]; then export POSTGRES_URL=\"sqlite:///./proof-of-browse.db\"; fi; .venv/bin/python -m app.temporal.worker"

start_service \
  "browser-worker" \
  "$ROOT_DIR/apps/browser-worker" \
  "$LOG_DIR/browser-worker.log" \
  bash -lc "export APP_MODE=\"$APP_MODE\" PAYMENT_MODE=\"$PAYMENT_MODE\"; source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8002"

start_service \
  "verifier-api" \
  "$ROOT_DIR/apps/verifier-api" \
  "$LOG_DIR/verifier-api.log" \
  bash -lc "source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8003"

start_service \
  "sponsor-runtime" \
  "$ROOT_DIR/apps/sponsor-runtime" \
  "$LOG_DIR/sponsor-runtime.log" \
  env APP_MODE="$APP_MODE" PAYMENT_MODE="$PAYMENT_MODE" SETTLEMENT_MODE="$SETTLEMENT_MODE" npm run dev

start_service \
  "web" \
  "$ROOT_DIR/apps/web" \
  "$LOG_DIR/web.log" \
  npm run dev -- --hostname 127.0.0.1 --port 3000

wait_for_http POST http://127.0.0.1:8001/health "Planner API"
wait_for_http GET http://127.0.0.1:8002/health "Browser worker"
wait_for_http GET http://127.0.0.1:8003/health "Verifier API"
wait_for_http GET http://127.0.0.1:8010/health "Sponsor runtime"
wait_for_http GET http://127.0.0.1:3000 "Web app"

cat <<EOF

Proof-of-Browse is running.
Mode:           $MODE

Web app:        http://127.0.0.1:3000
Planner API:    http://127.0.0.1:8001
Browser worker: http://127.0.0.1:8002
Verifier API:   http://127.0.0.1:8003
Sponsor runtime:http://127.0.0.1:8010
Temporal UI:    http://127.0.0.1:8088

Logs:
  $LOG_DIR/planner-api.log
  $LOG_DIR/temporal-worker.log
  $LOG_DIR/browser-worker.log
  $LOG_DIR/verifier-api.log
  $LOG_DIR/sponsor-runtime.log
  $LOG_DIR/web.log

Press Ctrl+C to stop the app processes. Docker services remain running.
EOF

wait
