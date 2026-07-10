#!/usr/bin/env python3
"""
知行旅行 · 跨平台本地开发启动脚本 (Windows / Linux / macOS)

用法:
    python start-local.py                  # 启动后端 + 前端
    python start-local.py --with-video     # 启动后端 + 前端 + Remotion
    python start-local.py --check-only     # 仅检查配置，不启动服务

前置条件:
    1. 复制并填写后端配置：  cp backend/.env.example backend/.env
    2. 复制并填写前端配置：  cp frontend/.env.example frontend/.env
    3. 安装后端依赖：        cd backend && python -m venv venv && venv/Scripts/pip install -r requirements.txt
    4. 安装前端依赖：        cd frontend && npm install
    5. (可选) 安装视频依赖：  cd video-generator && npm install

API Key 申请:
    - DeepSeek API Key:   https://platform.deepseek.com
    - 高德地图 Key:        https://console.amap.com/dev/key/app
      (需要「Web服务」和「Web端(JS API)」两种类型)
    - Unsplash Key:       https://unsplash.com/developers (可选)
    - Qwen-VL Key:        https://dashscope.console.aliyun.com (可选)
"""

import os
import re
import sys
import time
import shutil
import signal
import socket
import platform
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VIDEO_DIR = ROOT_DIR / "video-generator"

BACKEND_ENV = BACKEND_DIR / ".env"
BACKEND_ENV_EXAMPLE = BACKEND_DIR / ".env.example"
FRONTEND_ENV = FRONTEND_DIR / ".env"
FRONTEND_ENV_EXAMPLE = FRONTEND_DIR / ".env.example"

IS_WINDOWS = os.name == "nt"
PYTHON_EXE = "python.exe" if IS_WINDOWS else "python"
BACKEND_PORT = int(os.environ.get("PORT", "8000"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5173"))

# ── Subprocess management ──────────────────────────────────────────
_processes: list[subprocess.Popen] = []


def _on_exit(*_):
    for p in _processes:
        try:
            p.terminate()
        except Exception:
            pass
    # On Windows, give processes a moment then force kill
    if IS_WINDOWS:
        time.sleep(0.5)
        for p in _processes:
            try:
                p.kill()
            except Exception:
                pass


signal.signal(signal.SIGINT, _on_exit)
signal.signal(signal.SIGTERM, _on_exit)


def find_venv_python() -> str:
    """Locate the Python executable inside backend/venv."""
    if IS_WINDOWS:
        candidates = [
            BACKEND_DIR / "venv" / "Scripts" / "python.exe",
        ]
    else:
        candidates = [
            BACKEND_DIR / "venv" / "bin" / "python",
            BACKEND_DIR / "venv" / "bin" / "python3",
        ]
    for c in candidates:
        if c.exists():
            return str(c)
    # Fallback: system python
    which = shutil.which("python") or shutil.which("python3") or "python"
    return which


def find_node() -> str:
    """Locate node executable."""
    if IS_WINDOWS:
        for prog in [os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]:
            node_exe = os.path.join(prog, "nodejs", "node.exe")
            if Path(node_exe).exists():
                return node_exe
    which = shutil.which("node") or shutil.which("node.exe") or "node"
    return which


def find_npx() -> str:
    """Locate npx executable."""
    if IS_WINDOWS:
        for prog in [os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]:
            npx_cmd = os.path.join(prog, "nodejs", "npx.cmd")
            if Path(npx_cmd).exists():
                return npx_cmd
    which = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
    return which


def read_env_value(env_file: Path, key: str) -> str:
    """Read a value from a .env file."""
    if not env_file.exists():
        return ""
    text = env_file.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return ""


def is_placeholder(value: str) -> bool:
    """Check if a config value is still a placeholder."""
    if not value:
        return True
    placeholders = ["请填写", "your-", "your_", "changeme", "CHANGE_ME", "TODO", "todo"]
    for p in placeholders:
        if p in value:
            return True
    return False


def check_port(port: int) -> bool:
    """Check if a port is available."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(("localhost", port))
        s.close()
        return False  # In use
    except Exception:
        return True  # Free


# ── Check ──────────────────────────────────────────────────────────
def check_config() -> bool:
    """Validate all required configuration. Returns True if OK."""
    ok = True
    errors: list[str] = []
    warnings: list[str] = []

    print("=" * 60)
    print("  知行旅行 · 配置检查")
    print("=" * 60)
    print()

    # Backend .env
    if not BACKEND_ENV.exists():
        errors.append(f"缺少 {BACKEND_ENV.relative_to(ROOT_DIR)}")
        errors.append(f"  请运行: cp {BACKEND_ENV_EXAMPLE.relative_to(ROOT_DIR)} {BACKEND_ENV.relative_to(ROOT_DIR)}")
    else:
        required_backend = ["AMAP_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL_ID"]
        for key in required_backend:
            val = read_env_value(BACKEND_ENV, key)
            if not val:
                errors.append(f"backend/.env 缺少必填项: {key}")
            elif is_placeholder(val):
                errors.append(f"backend/.env 中的 {key} 仍是示例占位值，请填写真实 Key")

    if not errors:
        print("[OK] backend/.env 配置完整")

    # Frontend .env
    if not FRONTEND_ENV.exists():
        errors.append(f"缺少 {FRONTEND_ENV.relative_to(ROOT_DIR)}")
        errors.append(f"  请运行: cp {FRONTEND_ENV_EXAMPLE.relative_to(ROOT_DIR)} {FRONTEND_ENV.relative_to(ROOT_DIR)}")
    else:
        js_key = read_env_value(FRONTEND_ENV, "VITE_AMAP_WEB_JS_KEY")
        if not js_key or is_placeholder(js_key):
            errors.append("frontend/.env 中的 VITE_AMAP_WEB_JS_KEY 仍是占位值")
            errors.append("  高德地图 JS Key 用于旅行导览 GPS 定位和地图交互，必须填写")
            errors.append("  申请地址: https://console.amap.com/dev/key/app")

        web_key = read_env_value(FRONTEND_ENV, "VITE_AMAP_WEB_KEY")
        if not web_key or is_placeholder(web_key):
            warnings.append("VITE_AMAP_WEB_KEY 未配置，首页静态地图将无法显示")

    if not errors:
        print("[OK] frontend/.env 配置完整")

    # Python venv
    venv_python = find_venv_python()
    if "venv" not in venv_python:
        warnings.append(f"未检测到 backend/venv，将使用系统 Python: {venv_python}")
        warnings.append("  建议运行: cd backend && python -m venv venv && venv/Scripts/pip install -r requirements.txt")
    else:
        print("[OK] backend/venv 已就绪")

    # Node modules
    if not (FRONTEND_DIR / "node_modules").exists():
        errors.append("未检测到 frontend/node_modules")
        errors.append("  请运行: cd frontend && npm install")
    else:
        print("[OK] frontend/node_modules 已就绪")

    print()

    if warnings:
        for w in warnings:
            print(f"[WARN] {w}")
        print()

    if errors:
        print("=" * 60)
        print("  CONFIG ERRORS - 请先修复以下问题:")
        print("=" * 60)
        for e in errors:
            print(f"  - {e}")
        print()
        return False

    print("[OK] 所有配置检查通过！")
    print()
    return True


# ── Start ──────────────────────────────────────────────────────────
def start_services(with_video: bool = False):
    """Start backend, frontend, and optionally video dev server."""
    venv_python = find_venv_python()
    node_bin = find_node()
    npx_bin = find_npx()

    # Check ports
    if not check_port(BACKEND_PORT):
        print(f"[ERROR] 后端端口 {BACKEND_PORT} 已被占用，请先释放")
        sys.exit(1)
    if not check_port(FRONTEND_PORT):
        print(f"[ERROR] 前端端口 {FRONTEND_PORT} 已被占用，请先释放")
        sys.exit(1)

    print("=" * 60)
    print("  启动本地开发服务...")
    print("=" * 60)
    print()

    # Backend
    print(f"[START] 后端 (port {BACKEND_PORT})...")
    backend_proc = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app.api.main:app",
         "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    _processes.append(backend_proc)

    # Frontend
    print(f"[START] 前端 (port {FRONTEND_PORT})...")
    frontend_proc = subprocess.Popen(
        [npx_bin, "vite", "--port", str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    _processes.append(frontend_proc)

    # Video (optional)
    if with_video:
        if not (VIDEO_DIR / "node_modules").exists():
            print("[WARN] video-generator/node_modules 未安装，跳过 Remotion")
        else:
            print("[START] Remotion Studio (port 3000)...")
            video_proc = subprocess.Popen(
                [npx_bin, "remotion", "studio"],
                cwd=str(VIDEO_DIR),
            )
            _processes.append(video_proc)

    # Wait for servers to be ready
    print()
    print("  等待服务就绪...")
    time.sleep(3)

    # Print summary
    print()
    print("=" * 60)
    print("  ALL SERVICES STARTED")
    print("=" * 60)
    print(f"  前端开发地址:  http://localhost:{FRONTEND_PORT}")
    print(f"  后端 API 地址:  http://localhost:{BACKEND_PORT}")
    print(f"  后端 API 文档:  http://localhost:{BACKEND_PORT}/docs")
    if with_video:
        print(f"  Remotion Studio: http://localhost:3000")
    print()
    print("  按 Ctrl+C 停止所有服务")
    print()

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  正在停止所有服务...")
        _on_exit()
        print("  已停止。再见！")


# ── Main ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Windows GBK 编码兼容
    if IS_WINDOWS:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    with_video = "--with-video" in sys.argv
    check_only = "--check-only" in sys.argv

    if not check_config():
        sys.exit(1)

    if check_only:
        print("  配置检查完成。带上你的 API Key，开启知行之旅吧！")
        print()
        sys.exit(0)

    start_services(with_video=with_video)
