#!/bin/bash
# 知行旅行 · Docker 一键启动脚本
# 前提：已安装 Docker Engine / Docker Desktop，并确保 docker compose 可用
# 如需本地开发模式，请使用 ./start-local.sh

set -e

echo "🚀 知行旅行 · 正在启动..."
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到 Docker，请先安装 Docker Engine 或 Docker Desktop"
    echo "   Linux 可安装 Docker Engine；Mac/Windows 可安装 Docker Desktop"
    echo "   参考：https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ 当前环境不可用 docker compose"
    echo "   请先安装或启用 Docker Compose 插件后再执行。"
    echo "   参考：https://docs.docker.com/compose/install/"
    exit 1
fi

# 检查 .env 文件
if [ ! -f "backend/.env" ]; then
    echo "❌ 缺少 backend/.env 配置文件"
    echo "   请先复制 backend/.env.example 为 backend/.env，再填写你自己的真实配置。"
    echo ""
    echo "   cp backend/.env.example backend/.env"
    echo ""
    echo "   注意：仓库不会提供可直接使用的本地密钥，必须由使用者自行配置。"
    echo "   至少需要配置："
    echo "   AMAP_API_KEY=你的高德地图 Web 服务 Key"
    echo "   LLM_API_KEY=你的主文本模型 Key"
    echo "   LLM_BASE_URL=你的主模型兼容地址"
    echo "   LLM_MODEL_ID=你的主模型 ID"
    echo "   QWEN_API_KEY=你的 Qwen Key（可选，视觉问答需要）"
    echo "   SCENIC_INSIGHTS_EXCEL_PATH=你的景区洞察 Excel 路径（可选）"
    echo "   UNSPLASH_ACCESS_KEY=你的 Unsplash Key（可选）"
    exit 1
fi

require_env() {
    local key="$1"
    local value
    value=$(grep -E "^${key}=" backend/.env | tail -n 1 | cut -d'=' -f2- | tr -d '\r' | sed 's/^ *//;s/ *$//')

    if [ -z "$value" ]; then
        echo "❌ backend/.env 缺少必填配置：$key"
        echo "   请填写你自己的真实配置后再执行 ./start.sh"
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

require_env "AMAP_API_KEY"
require_env "LLM_API_KEY"
require_env "LLM_BASE_URL"
require_env "LLM_MODEL_ID"

echo "📦 正在构建镜像（首次约 8-15 分钟，视频渲染依赖会一起构建）..."
docker compose up -d --build

echo ""
echo "✅ 启动完成！"
echo ""
echo "   🌐 打开浏览器访问：http://localhost"
echo "   📋 API文档：http://localhost:8000/docs"
echo "   🎬 视频媒体会保存在 Compose 的 video_media 卷中"
echo ""
echo "   管理员账号：admin / admin123"
echo ""
echo "   停止服务：docker compose down"
echo "   查看日志：docker compose logs -f"
echo "   查看视频服务日志：docker compose logs -f backend video-generator"
echo "   彻底清理（含媒体文件）：docker compose down -v"
echo ""
echo "📌 体积控制建议："
echo "   - 不要把 backend/venv、frontend/node_modules、video-generator/node_modules 打包上传"
echo "   - 不要把 frontend/dist、video-generator/output、video-generator/public/audio、video-generator/public/images 一起打包上传"
echo "   - 视频成品与中间素材现在会写入 Docker volume，而不是代码目录"
