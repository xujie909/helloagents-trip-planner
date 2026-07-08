#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
DEFAULT_PORT="${PORT:-8000}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "❌ 未找到可用的后端解释器：$PYTHON_BIN"
  echo "请先在 backend 目录创建并安装 venv："
  echo "  cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

echo "✅ 后端解释器：$PYTHON_BIN"
"$PYTHON_BIN" -V

if [[ -d "$BACKEND_DIR/.venv" ]]; then
  echo "⚠️ 检测到额外的 backend/.venv"
  echo "   当前项目统一使用 backend/venv，避免误用 .venv 导致依赖缺失。"
fi

if [[ -x "$PIP_BIN" ]]; then
  echo
  echo "📦 关键依赖检查"
  "$PIP_BIN" show fastapi uvicorn pydantic pydantic-settings >/dev/null
  echo "   fastapi / uvicorn / pydantic / pydantic-settings：已安装"
fi

echo
if ss -ltn | grep -q ":$DEFAULT_PORT "; then
  echo "⚠️ 端口 $DEFAULT_PORT 已被占用"
  echo "   可执行：PORT=8001 ./backend/start.sh"
else
  echo "✅ 端口 $DEFAULT_PORT 当前可用"
fi

echo
cat <<EOF
后端环境检查完成。
- 推荐启动命令：./backend/start.sh
- 如需改端口：PORT=8001 ./backend/start.sh
EOF
