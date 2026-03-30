#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
PID_FILE="$RUN_DIR/pids.env"

BACKEND_DIR="$ROOT_DIR/backend"
STREAMLIT_DIR="$ROOT_DIR/streamlit"
FRONTEND_DIR="$ROOT_DIR/frontend"
START_VUE="${START_VUE:-false}"
PYTHON3="$(command -v python3)"

mkdir -p "$LOG_DIR"
: >"$PID_FILE"

# ── 工具函数 ──

is_port_listening() { lsof -ti "tcp:$1" -sTCP:LISTEN >/dev/null 2>&1; }

kill_port() {
  local pids
  pids="$(lsof -ti "tcp:$1" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "$pids" ]] && echo "$pids" | xargs kill >/dev/null 2>&1 || true
}

wait_for_port() {
  local port="$1" name="$2" pid="$3" timeout="${4:-90}" elapsed=0
  while ! is_port_listening "$port"; do
    if [[ -n "$pid" ]] && ! kill -0 "$pid" >/dev/null 2>&1; then
      echo "[FAIL] $name 进程已退出，未能监听 $port"
      echo "       日志: $LOG_DIR/$(echo "$name" | tr '[:upper:]' '[:lower:]').log"
      return 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
    if [[ "$elapsed" -ge "$timeout" ]]; then
      echo "[FAIL] $name 在 ${timeout}s 内未就绪 ($port)"
      return 1
    fi
  done
  return 0
}

record_pid() { echo "$1=$2" >>"$PID_FILE"; }

# ── 清理旧进程 ──

echo "== 一键启动 =="
echo "项目根目录: $ROOT_DIR"
echo

for port in 9999 8501 8888; do
  kill_port "$port"
done
sleep 1

# ── 环境检查 ──

if is_port_listening 3306; then
  echo "[OK] MySQL (3306)"
else
  echo "[WARN] MySQL 未在 3306 监听，数据库连接可能失败"
fi

# ── 启动 FastAPI ──

echo "[START] FastAPI (9999) ..."
(
  cd "$BACKEND_DIR"
  nohup "$PYTHON3" main.py >"$LOG_DIR/fastapi.log" 2>&1 &
  echo $! >"$RUN_DIR/fastapi.pid"
)
FASTAPI_PID="$(cat "$RUN_DIR/fastapi.pid")"
record_pid "FASTAPI_PID" "$FASTAPI_PID"

if wait_for_port 9999 "FastAPI" "$FASTAPI_PID" 120; then
  echo "[OK] FastAPI (9999)"
fi

# ── 启动 Streamlit（可选）──

if "$PYTHON3" -m streamlit version >/dev/null 2>&1; then
  echo "[START] Streamlit (8501) ..."
  (
    cd "$STREAMLIT_DIR"
    nohup "$PYTHON3" -m streamlit run main.py \
      --server.port 8501 --server.headless true \
      --server.enableCORS false --server.enableXsrfProtection false \
      >"$LOG_DIR/streamlit.log" 2>&1 &
    echo $! >"$RUN_DIR/streamlit.pid"
  )
  STREAMLIT_PID="$(cat "$RUN_DIR/streamlit.pid")"
  record_pid "STREAMLIT_PID" "$STREAMLIT_PID"

  if wait_for_port 8501 "Streamlit" "$STREAMLIT_PID" 120; then
    echo "[OK] Streamlit (8501)"
  fi
else
  echo "[SKIP] Streamlit 未安装"
fi

# ── 启动 Vue 开发服务器（可选）──

if [[ "$START_VUE" == "true" ]]; then
  if [[ -f "$FRONTEND_DIR/node_modules/vite/bin/vite.js" ]]; then
    echo "[START] Vue dev (8888) ..."
    (
      cd "$FRONTEND_DIR"
      nohup node node_modules/vite/bin/vite.js --force >"$LOG_DIR/vue.log" 2>&1 &
      echo $! >"$RUN_DIR/vue.pid"
    )
    VUE_PID="$(cat "$RUN_DIR/vue.pid")"
    record_pid "VUE_PID" "$VUE_PID"

    if wait_for_port 8888 "Vue" "$VUE_PID" 120; then
      echo "[OK] Vue dev (8888)"
    fi
  else
    echo "[SKIP] Vue 依赖未安装，跳过"
  fi
fi

# ── 完成 ──

echo
echo "== 启动完成 =="
echo "前端:      http://localhost:9999/#/login"
echo "FastAPI:   http://localhost:9999"
echo "Streamlit: http://localhost:8501"
echo
echo "日志: $LOG_DIR/"
echo "停止: ./stop-all.sh"
