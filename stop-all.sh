#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
PID_FILE="$RUN_DIR/pids.env"

echo "== 一键停止 =="

# ── 按 PID 文件停止 ──

if [[ -f "$PID_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$PID_FILE"

  for pair in "FASTAPI_PID:FastAPI" "STREAMLIT_PID:Streamlit" "VUE_PID:Vue"; do
    key="${pair%%:*}"
    name="${pair##*:}"
    pid="${!key:-}"
    if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      echo "[STOP] $name (pid $pid)"
    fi
  done
fi

# ── 兜底：按端口清理 ──

for port in 9999 8501 8888; do
  pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs kill >/dev/null 2>&1 || true
    echo "[STOP] 清理端口 $port"
  fi
done

# ── 清空 PID 文件 ──

: >"$RUN_DIR/pids.env" 2>/dev/null || true

echo "[DONE] 所有服务已停止"
