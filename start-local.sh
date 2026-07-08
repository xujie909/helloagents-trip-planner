#!/usr/bin/env bash
# 知行旅行 · 本地开发启动脚本
# 默认启动后端 + 前端；传入 --with-video 可额外启动 Remotion 开发服务

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ENV_FILE="$ROOT_DIR/backend/.env"
BACKEND_VENV_PYTHON="$ROOT_DIR/backend/venv/bin/python"
FRONTEND_NODE_MODULES="$ROOT_DIR/frontend/node_modules"
VIDEO_NODE_MODULES="$ROOT_DIR/video-generator/node_modules"
BACKEND_PORT="${PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
WITH_VIDEO=0

for arg in "$@"; do
  case "$arg" in
    --with-video)
      WITH_VIDEO=1
      ;;
    *)
      echo "❌ 不支持的参数：$arg"
      echo "   可用参数：--with-video"
      exit 1
      ;;
  esac
done

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${VIDEO_PID:-}" ]] && kill -0 "$VIDEO_PID" 2>/dev/null; then
    kill "$VIDEO_PID" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

require_env() {
  local key="$1"
  local value
  value=$(grep -E "^${key}=" "$BACKEND_ENV_FILE" | tail -n 1 | cut -d'=' -f2- | tr -d '\r' | sed 's/^ *//;s/ *$//')

  if [[ -z "$value" ]]; then
    echo "❌ backend/.env 缺少必填配置：$key"
    echo "   请填写你自己的真实配置后再执行 ./start-local.sh"
    exit 1
  fi

  case "$value" in
    请填写你的*|your-*|your_*|changeme|CHANGE_ME|TODO|todo)
      echo "❌ backend/.env 中的 $key 仍是示例占位值"
      echo "   仓库不会附带可直接使用的本地密钥，请改成你自己的真实配置。"
      exit 1
      ;;
  esac
}

echo "🚀 知行旅行 · 正在启动本地开发环境..."
echo ""

if [[ ! -f "$BACKEND_ENV_FILE" ]]; then
  echo "❌ 缺少 backend/.env 配置文件"
  echo "   请先复制 backend/.env.example 为 backend/.env，再填写你自己的真实配置。"
  echo ""
  echo "   cp backend/.env.example backend/.env"
  echo ""
  echo "   注意：仓库不会提供可直接使用的本地密钥，必须由使用者自行配置。"
  exit 1
fi

require_env "AMAP_API_KEY"
require_env "LLM_API_KEY"
require_env "LLM_BASE_URL"
require_env "LLM_MODEL_ID"

if [[ ! -x "$BACKEND_VENV_PYTHON" ]]; then
  echo "❌ 未检测到 backend/venv/bin/python"
  echo "   请先执行：cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -d "$FRONTEND_NODE_MODULES" ]]; then
  echo "❌ 未检测到 frontend/node_modules"
  echo "   请先执行：cd frontend && npm install"
  exit 1
fi

if [[ "$WITH_VIDEO" == "1" && ! -d "$VIDEO_NODE_MODULES" ]]; then
  echo "❌ 你启用了 --with-video，但未检测到 video-generator/node_modules"
  echo "   请先执行：cd video-generator && npm install"
  exit 1
fi

if ss -ltn | grep -q ":$BACKEND_PORT "; then
  echo "❌ 后端端口 $BACKEND_PORT 已被占用"
  echo "   请先释放该端口，或执行：PORT=8001 ./start-local.sh"
  exit 1
fi

if ss -ltn | grep -q ":$FRONTEND_PORT "; then
  echo "❌ 前端端口 $FRONTEND_PORT 已被占用"
  echo "   请先释放该端口，或执行：FRONTEND_PORT=5174 ./start-local.sh"
  exit 1
fi

echo "✅ 后端配置检查通过"
echo "✅ backend/venv 已就绪"
echo "✅ frontend/node_modules 已就绪"
echo "✅ 后端端口 $BACKEND_PORT 可用"
echo "✅ 前端端口 $FRONTEND_PORT 可用"
if [[ "$WITH_VIDEO" == "1" ]]; then
  echo "✅ video-generator/node_modules 已就绪"
else
  echo "ℹ️ 视频子项目默认不启动；如需调试 Remotion，请使用 ./start-local.sh --with-video"
fi

echo ""
echo "📦 正在启动后端..."
(
  cd "$ROOT_DIR"
  ./backend/start.sh
) &
BACKEND_PID=$!

echo "🌐 正在启动前端..."
(
  cd "$ROOT_DIR/frontend"
  FRONTEND_PORT="$FRONTEND_PORT" npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort
) &
FRONTEND_PID=$!

if [[ "$WITH_VIDEO" == "1" ]]; then
  echo "🎬 正在启动视频模板开发服务..."
  (
    cd "$ROOT_DIR/video-generator"
    npm run dev
  ) &
  VIDEO_PID=$!
fi

echo ""
echo "✅ 本地开发服务已开始启动"
echo ""
echo "   前端开发地址： http://localhost:$FRONTEND_PORT"
echo "   后端 API 地址： http://localhost:$BACKEND_PORT"
echo "   后端文档地址： http://localhost:$BACKEND_PORT/docs"
if [[ "$WITH_VIDEO" == "1" ]]; then
  echo "   Remotion Studio：按终端输出提示访问"
fi
echo ""
echo "   按 Ctrl+C 可停止本次脚本拉起的全部本地服务"
echo ""

wait
