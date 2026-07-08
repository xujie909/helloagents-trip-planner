"""启动脚本"""

import sys
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    # Windows GBK编码兼容: 强制使用UTF-8输出
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    settings = get_settings()

    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

