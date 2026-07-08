"""配置管理模块"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# 加载环境变量
# 首先尝试加载 backend 目录下的 .env
load_dotenv(BASE_DIR / ".env")

# 然后尝试加载当前工作目录的 .env
load_dotenv(override=False)

# 再尝试加载 HelloAgents 的 .env(如果存在)
helloagents_env = ROOT_DIR / "HelloAgents" / ".env"
if helloagents_env.exists():
    load_dotenv(helloagents_env, override=False)  # 不覆盖已有的环境变量


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    app_name: str = "HelloAgents智能旅行助手"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置 - 使用字符串,在代码中分割 (开发环境覆盖常见Vite端口)
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5176,http://127.0.0.1:3000"

    # 高德地图API配置
    amap_api_key: str = ""

    # 景区洞察数据文件（可选）
    scenic_insights_excel_path: str = ""

    # Unsplash API配置
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # 视频生成运行时配置
    video_generator_dir: str = "video-generator"
    video_media_root: str = ""
    video_output_subdir: str = "output"
    video_audio_subdir: str = "audio"
    video_image_subdir: str = "images"
    video_output_keep_count: int = 5
    video_temp_keep_days: int = 2
    edge_tts_bin: str = ""
    remotion_concurrency: int = 4
    puppeteer_executable_path: str = ""

    # 主文本 LLM 配置
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model_id: str = "gpt-4"

    # 兼容旧配置命名
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # Qwen-VL 多模态大模型配置
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model_id: str = "qwen-vl-plus"

    # 日志配置
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量

    def get_cors_origins_list(self) -> List[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]

    def get_scenic_insights_excel_path(self) -> Path | None:
        """获取景区洞察 Excel 文件路径（可选）"""
        if not self.scenic_insights_excel_path:
            return None

        path = Path(self.scenic_insights_excel_path).expanduser()
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path

    def get_video_generator_dir(self) -> Path:
        """获取视频生成子项目目录"""
        path = Path(self.video_generator_dir).expanduser()
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path

    def get_video_media_root(self) -> Path:
        """获取视频媒体根目录"""
        if self.video_media_root:
            path = Path(self.video_media_root).expanduser()
            if not path.is_absolute():
                path = ROOT_DIR / path
            return path
        return self.get_video_generator_dir()

    def get_video_output_dir(self) -> Path:
        """获取视频输出目录"""
        return self.get_video_media_root() / self.video_output_subdir

    def get_video_audio_dir(self) -> Path:
        """获取视频音频目录"""
        return self.get_video_media_root() / self.video_audio_subdir

    def get_video_image_dir(self) -> Path:
        """获取视频图片目录"""
        return self.get_video_media_root() / self.video_image_subdir

    def get_edge_tts_bin(self) -> str:
        """获取 Edge TTS 可执行文件路径"""
        if self.edge_tts_bin:
            return self.edge_tts_bin
        local_bin = ROOT_DIR / "backend" / "venv" / "bin" / "edge-tts"
        if local_bin.exists():
            return str(local_bin)
        return "edge-tts"

    def get_puppeteer_executable_path(self) -> str:
        """获取 Puppeteer 浏览器路径"""
        return self.puppeteer_executable_path or os.environ.get("PUPPETEER_EXECUTABLE_PATH", "")

    def get_primary_llm_api_key(self) -> str:
        """获取主文本模型 API Key（兼容旧字段）"""
        return self.llm_api_key or self.openai_api_key

    def get_primary_llm_base_url(self) -> str:
        """获取主文本模型 Base URL（兼容旧字段）"""
        return self.llm_base_url or self.openai_base_url

    def get_primary_llm_model(self) -> str:
        """获取主文本模型 ID（兼容旧字段）"""
        return self.llm_model_id or self.openai_model


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


# 验证必要的配置
def validate_config():
    """验证配置是否完整"""
    errors = []
    warnings = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY未配置")

    if not settings.get_primary_llm_api_key():
        warnings.append("LLM_API_KEY或OPENAI_API_KEY未配置,LLM功能可能无法使用")

    scenic_excel_path = settings.get_scenic_insights_excel_path()
    if scenic_excel_path and not scenic_excel_path.exists():
        warnings.append(f"SCENIC_INSIGHTS_EXCEL_PATH文件不存在: {scenic_excel_path}")

    video_generator_dir = settings.get_video_generator_dir()
    if not video_generator_dir.exists():
        warnings.append(f"VIDEO_GENERATOR_DIR目录不存在: {video_generator_dir}")

    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n⚠️  配置警告:")
        for w in warnings:
            print(f"  - {w}")

    return True


# 打印配置信息(用于调试)
def print_config():
    """打印当前配置(隐藏敏感信息)"""
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"服务器: {settings.host}:{settings.port}")
    print(f"高德地图API Key: {'已配置' if settings.amap_api_key else '未配置'}")
    print(f"景区洞察Excel: {settings.get_scenic_insights_excel_path() or '未配置'}")
    print(f"视频生成目录: {settings.get_video_generator_dir()}")
    print(f"视频媒体根目录: {settings.get_video_media_root()}")
    print(f"LLM API Key: {'已配置' if settings.get_primary_llm_api_key() else '未配置'}")
    print(f"LLM Base URL: {settings.get_primary_llm_base_url()}")
    print(f"LLM Model: {settings.get_primary_llm_model()}")
    print(f"日志级别: {settings.log_level}")
