#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
PID_FILE="$RUN_DIR/pids.env"

FLASK_DIR="$ROOT_DIR/yolo_img_detection_web/yolo_img_detection_flask"
FASTAPI_DIR="$ROOT_DIR/yolo_img_detection_web/yolo_img_detection_fastapi"
VUE_DIR="$ROOT_DIR/yolo_img_detection_web/yolo_img_detection_vue"

mkdir -p "$LOG_DIR"
touch "$PID_FILE"

is_port_listening() {
  local port="$1"
  lsof -ti "tcp:${port}" -sTCP:LISTEN >/dev/null 2>&1
}

port_pid() {
  local port="$1"
  lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null | head -n 1
}

wait_for_port() {
  local port="$1"
  local name="$2"
  local timeout="${3:-90}"
  local elapsed=0
  while ! is_port_listening "$port"; do
    sleep 1
    elapsed=$((elapsed + 1))
    if [[ "$elapsed" -ge "$timeout" ]]; then
      echo "[ERROR] ${name} did not become ready on port ${port} within ${timeout}s."
      echo "Check logs: $LOG_DIR"
      exit 1
    fi
  done
}

wait_for_port_with_pid() {
  local port="$1"
  local name="$2"
  local pid="$3"
  local log_file="$4"
  local timeout="${5:-90}"
  local elapsed=0
  while ! is_port_listening "$port"; do
    if [[ -n "$pid" ]] && ! kill -0 "$pid" >/dev/null 2>&1; then
      echo "[ERROR] ${name} process exited before listening on ${port}."
      echo "Log: $log_file"
      exit 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
    if [[ "$elapsed" -ge "$timeout" ]]; then
      echo "[ERROR] ${name} did not become ready on port ${port} within ${timeout}s."
      echo "Check logs: $LOG_DIR"
      exit 1
    fi
  done
}

record_pid() {
  local key="$1"
  local pid="$2"
  if grep -q "^${key}=" "$PID_FILE"; then
    sed -i.bak "s/^${key}=.*/${key}=${pid}/" "$PID_FILE"
    rm -f "$PID_FILE.bak"
  else
    echo "${key}=${pid}" >>"$PID_FILE"
  fi
}

check_fastapi_deps() {
  python3 - <<'PY'
import importlib.util

mods = ["fastapi", "uvicorn", "socketio", "pymysql", "cv2", "ultralytics"]
missing = []
for mod in mods:
    if importlib.util.find_spec(mod) is None:
        missing.append(mod)
if missing:
    print("MISSING:" + ",".join(missing))
    raise SystemExit(1)
print("OK")
PY
}

has_streamlit() {
  python3 - <<'PY'
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("streamlit") else 1)
PY
}

echo "== One-click startup =="
echo "Project root: $ROOT_DIR"
echo

if is_port_listening 3306; then
  echo "[OK] MySQL is listening on 3306."
else
  echo "[WARN] MySQL is not listening on 3306. FastAPI may fail DB connection."
fi

if is_port_listening 9999; then
  echo "[SKIP] FastAPI already running on 9999 (pid $(port_pid 9999))."
else
  if ! check_fastapi_deps >/tmp/fastapi_dep_check.txt 2>&1; then
    echo "[ERROR] FastAPI dependencies are missing."
    echo "Install first: python3 -m pip install -r yolo_img_detection_web/yolo_img_detection_fastapi/requirements.txt"
    echo "Details: $(cat /tmp/fastapi_dep_check.txt)"
    exit 1
  fi
  echo "[START] FastAPI (9999)"
  (
    cd "$FASTAPI_DIR"
    nohup python3 main.py >"$LOG_DIR/fastapi.log" 2>&1 &
    echo $! >"$RUN_DIR/fastapi.pid"
  )
  record_pid "FASTAPI_PID" "$(cat "$RUN_DIR/fastapi.pid")"
  wait_for_port_with_pid 9999 "FastAPI" "$(cat "$RUN_DIR/fastapi.pid")" "$LOG_DIR/fastapi.log" 120
fi
if is_port_listening 9999; then
  wait_for_port 9999 "FastAPI" 120
fi

if is_port_listening 8501; then
  echo "[SKIP] Streamlit already running on 8501 (pid $(port_pid 8501))."
else
  if has_streamlit; then
    echo "[START] Streamlit QA (8501)"
    (
      cd "$FLASK_DIR"
      nohup python3 -m streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false >"$LOG_DIR/streamlit.log" 2>&1 &
      echo $! >"$RUN_DIR/streamlit.pid"
    )
    record_pid "STREAMLIT_PID" "$(cat "$RUN_DIR/streamlit.pid")"
    wait_for_port_with_pid 8501 "Streamlit" "$(cat "$RUN_DIR/streamlit.pid")" "$LOG_DIR/streamlit.log" 120
  else
    echo "[WARN] Streamlit not installed, skip QA service (8501)."
  fi
fi

if is_port_listening 8888; then
  echo "[SKIP] Vue already running on 8888 (pid $(port_pid 8888))."
else
  echo "[START] Vue (8888)"
  (
    cd "$VUE_DIR"
    nohup node node_modules/vite/bin/vite.js --force >"$LOG_DIR/vue.log" 2>&1 &
    echo $! >"$RUN_DIR/vue.pid"
  )
  record_pid "VUE_PID" "$(cat "$RUN_DIR/vue.pid")"
  wait_for_port_with_pid 8888 "Vue" "$(cat "$RUN_DIR/vue.pid")" "$LOG_DIR/vue.log" 120
fi
if is_port_listening 8888; then
  wait_for_port 8888 "Vue" 120
fi

echo
echo "== Started =="
echo "Frontend:  http://localhost:8888"
echo "FastAPI:   http://localhost:9999"
echo "Streamlit: http://localhost:8501"
echo
echo "Logs:"
echo "  $LOG_DIR/fastapi.log"
echo "  $LOG_DIR/streamlit.log"
echo "  $LOG_DIR/vue.log"
echo
echo "Stop all: ./stop-all.sh"
