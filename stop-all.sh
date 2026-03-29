#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
PID_FILE="$RUN_DIR/pids.env"

kill_if_running() {
  local pid="$1"
  local name="$2"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1; then
    kill "${pid}" >/dev/null 2>&1 || true
    echo "[STOP] ${name} (pid ${pid})"
  else
    echo "[SKIP] ${name} not running by pid."
  fi
}

if [[ -f "$PID_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$PID_FILE"
else
  echo "[INFO] PID file not found: $PID_FILE"
fi

kill_if_running "${VUE_PID:-}" "Vue"
kill_if_running "${STREAMLIT_PID:-}" "Streamlit"
kill_if_running "${FASTAPI_PID:-}" "FastAPI"
kill_if_running "${FLASK_PID:-}" "Flask"
kill_if_running "${SPRING_PID:-}" "Spring Boot"

# Also clear common ports in case service was started manually.
for port in 8888 8501 9999; do
  pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs kill >/dev/null 2>&1 || true
    echo "[STOP] Cleared listener(s) on port ${port}"
  fi
done

echo "[DONE] All services stopped."
