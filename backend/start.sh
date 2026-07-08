#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PORT_VALUE="${PORT:-8000}"
HOST_VALUE="${HOST:-0.0.0.0}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "❌ 未找到 $PYTHON_BIN"
  echo "请先执行：cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ -d "$BACKEND_DIR/.venv" ]]; then
  echo "⚠️ 检测到 backend/.venv，但当前项目统一使用 backend/venv"
fi

if ss -ltn | grep -q ":$PORT_VALUE "; then
  echo "❌ 端口 $PORT_VALUE 已被占用，请先释放，或改用其他端口。"
  echo "例如：PORT=8001 ./backend/start.sh"
  exit 1
fi

cd "$BACKEND_DIR"
exec env HOST="$HOST_VALUE" PORT="$PORT_VALUE" "$PYTHON_BIN" run.py
