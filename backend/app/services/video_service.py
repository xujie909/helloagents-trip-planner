"""视频生成服务 - 编排 LLM 脚本、TTS 音频、Unsplash 图片、Remotion 渲染"""

import os
import json
import shutil
import subprocess
import threading
import uuid
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import asdict, dataclass

from mutagen.mp3 import MP3
from ..config import get_settings

settings = get_settings()

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VIDEO_DATA_DIR = PROJECT_ROOT / "backend" / "app" / "data"
VIDEO_GENERATOR_DIR = settings.get_video_generator_dir()
OUTPUT_DIR = settings.get_video_output_dir()
PUBLIC_AUDIO_DIR = settings.get_video_audio_dir()
PUBLIC_IMAGES_DIR = settings.get_video_image_dir()
RENDER_PUBLIC_DIR = VIDEO_GENERATOR_DIR / "public"
RENDER_AUDIO_DIR = RENDER_PUBLIC_DIR / "audio"
RENDER_IMAGES_DIR = RENDER_PUBLIC_DIR / "images"
PLACEHOLDER_IMAGE_NAME = "placeholder.svg"

# Edge TTS 二进制完整路径（子进程需要绝对路径）
EDGE_TTS_BIN = settings.get_edge_tts_bin()

# 跨平台子进程编码：Windows 中文环境下默认 GBK，但工具输出通常是 UTF-8
_SUBPROCESS_ENCODING = "utf-8"


def _build_subprocess_env() -> dict:
    """构建跨平台子进程环境变量，修复 Git Bash / MSYS 导致的 PATH 编码问题"""
    env = dict(os.environ)
    # 确保 Node.js 路径在 PATH 中（跨平台）
    if os.name == "nt":
        node_dirs = []
        for prog in [os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]:
            nodejs_dir = os.path.join(prog, "nodejs")
            if os.path.isdir(nodejs_dir):
                node_dirs.append(nodejs_dir)
        if node_dirs:
            existing_path = env.get("PATH", "")
            for nd in node_dirs:
                if nd not in existing_path:
                    existing_path = nd + os.pathsep + existing_path
            env["PATH"] = existing_path
    # 设置 UTF-8 编码，避免 GBK 解码错误
    env["PYTHONIOENCODING"] = "utf-8"
    return env

# 表情 key 列表（与 EXPRESSION_MAP 一致）
EXPRESSION_KEYS = [
    "default", "happy_confident", "happy2", "happy3", "happy5",
    "excited", "happy6", "thinking", "surprised", "confused",
    "upset", "confident",
]

# 红美铃的 System Prompt 用于生成景区介绍脚本（完整深度版）
SCRIPT_SYSTEM_PROMPT = """你是一个名叫\"红美铃\"（Hong Meiling）的AI数字人导游。你来自東方Project，是红魔馆的门卫。

你的性格特点：
- 活泼开朗、随性自在，工作时偶尔会偷懒打瞌睡，但对朋友热情真诚
- 对自己的中国血统感到自豪，对中国各地的风景名胜了如指掌
- 说话风格自然亲切，像邻家大姐一样热情
- 偶尔冒冒失失但很可爱，但介绍景点时非常专业认真

你的说话方式：
- 使用\"呀\"\"呢\"\"哦\"\"嘛\"\"~\"等语气词让介绍更生动
- 可以用\"咱们\"、\"大家\"拉近与观众的距离
- 遇到壮丽景色会由衷感叹，遇到历史典故会认真讲解
- 偶尔会插入一些可爱的感叹，比如\"哇~\"\"哎呀！\"

你的任务：为指定的景区写一篇完整、详细的介绍脚本。要求18-25句话，用红美铃的口吻生动讲述。

脚本必须按以下章节结构组织，每个章节2-5句话：

【开场欢迎】(2-3句) - 自信地自我介绍，引出景区，概括它的地位和特色
【地理概况】(2-3句) - 景区位置、面积、地貌、气候特点等
【历史渊源】(3-5句) - 景区的来龙去脉、建造背景、重要历史事件、名人典故
【核心亮点】(5-8句) - 逐个讲解景区内最值得看的景点、标志性建筑、独特景观，每处用1-2句
【文化价值】(2-3句) - 文化内涵、艺术价值、在历史上的地位和意义
【旅行贴士】(2-3句) - 最佳旅行季节、游览路线建议、注意事项等
【深情告别】(2-3句) - 总结推荐，表达对景区的情感，热情告别

每个句子的文案要求：
- 每句15-40个字，内容丰富有料，不要空洞的套话
- 包含具体的数据、典故、细节描述（如建造年代、高度、特色元素等）
- 用红美铃的语气自然地串联，保持亲切感和专业感的平衡
- 历史部分要有\"讲故事\"的感觉；亮点部分要有\"带你看\"的画面感

你必须严格按照以下JSON格式回复，不要包含任何其他内容：
[
  {"text": "第1句解说词", "expression": "表情代号"},
  {"text": "第2句解说词", "expression": "表情代号"},
  ...
]

可用的表情代号（根据每句话的内容和情绪选择最合适的）：
- "confident" — 自信满满（开场、总结推荐时）
- "excited" — 兴奋激动（看到壮丽景色、高潮亮点时）
- "happy3" — 愉快（介绍有趣事物、轻松的内容时）
- "happy_confident" — 开心又自信（骄傲地介绍独特之处时）
- "thinking" — 思考中（讲历史典故、文化内涵时）
- "surprised" — 惊讶（感叹奇观、令人震撼的事实）
- "default" — 正常微笑（日常叙述、过渡语句）
- "confused" — 疑惑（提到神秘传说、未解之谜）
- "happy5" — 温暖开心（贴心建议、告别时）

只回复JSON数组，不要有其他文字。"""


@dataclass
class SceneData:
    """单个场景数据"""
    text: str
    expression: str
    audio_file: str
    duration_frames: int
    image_file: str


@dataclass
class VideoTask:
    """视频生成任务"""
    task_id: str
    status: str  # "processing" | "done" | "error"
    progress: int  # 0-100
    message: str
    video_path: Optional[str] = None
    scenic_name: str = ""
    username: str = ""
    created_at: str = ""
    updated_at: str = ""
    trip_id: str = ""
    trip_title: str = ""
    trip_city: str = ""
    source_attraction: str = ""


# 内存中的任务存储（简单实现）
_tasks: dict[str, VideoTask] = {}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _history_file(username: str) -> Path:
    safe_username = (username or "guest").strip() or "guest"
    VIDEO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return VIDEO_DATA_DIR / f"video_history_{safe_username}.json"


def _task_to_history_item(task: VideoTask) -> dict:
    video_url = f"/api/video/download/{task.task_id}" if task.status == "done" and task.video_path else None
    file_exists = bool(task.video_path and Path(task.video_path).exists())
    return {
        "task_id": task.task_id,
        "scenic_name": task.scenic_name,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "video_url": video_url,
        "video_path": task.video_path,
        "file_exists": file_exists,
        "trip_id": str(task.trip_id or "").strip(),
        "trip_title": str(task.trip_title or "").strip(),
        "trip_city": str(task.trip_city or "").strip(),
        "source_attraction": str(task.source_attraction or "").strip(),
    }


def _load_history(username: str) -> list[dict]:
    path = _history_file(username)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_history(username: str, items: list[dict]) -> None:
    path = _history_file(username)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _upsert_history(task: VideoTask) -> None:
    username = (task.username or "guest").strip() or "guest"
    items = _load_history(username)
    payload = _task_to_history_item(task)
    updated = False
    for index, item in enumerate(items):
        if item.get("task_id") == task.task_id:
            items[index] = payload
            updated = True
            break
    if not updated:
        items.insert(0, payload)
    _save_history(username, items)


def list_video_history(username: str) -> list[dict]:
    items = _load_history(username)
    normalized = []
    for item in items:
        task_id = str(item.get("task_id", "") or "").strip()
        video_path = str(item.get("video_path", "") or "").strip()
        file_exists = bool(video_path and Path(video_path).exists())
        normalized.append({
            "task_id": task_id,
            "scenic_name": str(item.get("scenic_name", "") or "").strip(),
            "status": str(item.get("status", "processing") or "processing").strip() or "processing",
            "progress": int(item.get("progress", 0) or 0),
            "message": str(item.get("message", "") or "").strip(),
            "created_at": str(item.get("created_at", "") or "").strip(),
            "updated_at": str(item.get("updated_at", "") or "").strip(),
            "video_url": f"/api/video/download/{task_id}" if file_exists and task_id else None,
            "video_path": video_path,
            "file_exists": file_exists,
            "trip_id": str(item.get("trip_id", "") or "").strip(),
            "trip_title": str(item.get("trip_title", "") or "").strip(),
            "trip_city": str(item.get("trip_city", "") or "").strip(),
            "source_attraction": str(item.get("source_attraction", "") or "").strip(),
        })
    normalized.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return normalized


def delete_video_history(username: str, task_id: str) -> bool:
    items = _load_history(username)
    next_items = [item for item in items if str(item.get("task_id", "")).strip() != task_id]
    if len(next_items) == len(items):
        return False
    _save_history(username, next_items)
    return True


def sync_task_from_history(task_id: str, username: str) -> Optional[VideoTask]:
    for item in list_video_history(username):
        if item.get("task_id") != task_id:
            continue
        task = VideoTask(
            task_id=item.get("task_id", ""),
            status=item.get("status", "processing"),
            progress=int(item.get("progress", 0) or 0),
            message=item.get("message", ""),
            video_path=item.get("video_path") or None,
            scenic_name=item.get("scenic_name", ""),
            username=(username or "guest").strip() or "guest",
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
            trip_id=str(item.get("trip_id", "") or "").strip(),
            trip_title=str(item.get("trip_title", "") or "").strip(),
            trip_city=str(item.get("trip_city", "") or "").strip(),
            source_attraction=str(item.get("source_attraction", "") or "").strip(),
        )
        _tasks[task_id] = task
        return task
    return None


def get_task(task_id: str) -> Optional[VideoTask]:
    """获取任务状态"""
    return _tasks.get(task_id)


class VideoService:
    """视频生成服务"""

    def __init__(self):
        self.video_generator_dir = VIDEO_GENERATOR_DIR
        self.output_dir = OUTPUT_DIR
        self.audio_root = PUBLIC_AUDIO_DIR
        self.image_root = PUBLIC_IMAGES_DIR
        self.render_audio_root = RENDER_AUDIO_DIR
        self.render_image_root = RENDER_IMAGES_DIR
        self.remotion_concurrency = max(1, int(settings.remotion_concurrency or 4))
        self.puppeteer_executable_path = settings.get_puppeteer_executable_path()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-gen")

        if not self.video_generator_dir.exists():
            raise RuntimeError(f"视频生成目录不存在: {self.video_generator_dir}")
        if not (self.video_generator_dir / "package.json").exists():
            raise RuntimeError(f"视频生成目录缺少 package.json: {self.video_generator_dir}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_root.mkdir(parents=True, exist_ok=True)
        self.image_root.mkdir(parents=True, exist_ok=True)
        self.render_audio_root.mkdir(parents=True, exist_ok=True)
        self.render_image_root.mkdir(parents=True, exist_ok=True)
        VIDEO_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_placeholder_image()

    def _ensure_placeholder_image(self):
        """确保存在可用的占位图，避免本地渲染时因外部图库缺图而失败"""
        svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1920\" height=\"1080\" viewBox=\"0 0 1920 1080\">
  <defs>
    <linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">
      <stop offset=\"0%\" stop-color=\"#1b2433\"/>
      <stop offset=\"100%\" stop-color=\"#5c3a21\"/>
    </linearGradient>
  </defs>
  <rect width=\"1920\" height=\"1080\" fill=\"url(#bg)\"/>
  <circle cx=\"320\" cy=\"220\" r=\"120\" fill=\"rgba(255,255,255,0.08)\"/>
  <circle cx=\"1620\" cy=\"860\" r=\"180\" fill=\"rgba(255,215,0,0.08)\"/>
  <text x=\"960\" y=\"470\" text-anchor=\"middle\" fill=\"#f7e7ce\" font-size=\"72\" font-family=\"'Noto Sans SC','Microsoft YaHei',sans-serif\">知行旅行</text>
  <text x=\"960\" y=\"570\" text-anchor=\"middle\" fill=\"rgba(247,231,206,0.88)\" font-size=\"42\" font-family=\"'Noto Sans SC','Microsoft YaHei',sans-serif\">外部图库素材暂不可用，当前使用占位图继续渲染</text>
</svg>
"""

        for target_dir in (self.image_root, self.render_image_root):
            placeholder = target_dir / PLACEHOLDER_IMAGE_NAME
            if not placeholder.exists():
                placeholder.write_text(svg_content, encoding="utf-8")

    def _task_audio_dir(self, task_id: str) -> Path:
        return self.audio_root / task_id

    def _task_image_dir(self, task_id: str) -> Path:
        return self.image_root / task_id

    def _render_task_audio_dir(self, task_id: str) -> Path:
        return self.render_audio_root / task_id

    def _render_task_image_dir(self, task_id: str) -> Path:
        return self.render_image_root / task_id

    def _prepare_task_dirs(self, task_id: str):
        self._task_audio_dir(task_id).mkdir(parents=True, exist_ok=True)
        self._task_image_dir(task_id).mkdir(parents=True, exist_ok=True)

    def _sync_task_assets_to_render_public(self, task_id: str):
        """将可配置媒体目录中的素材同步到 Remotion 的 public 目录"""
        src_audio_dir = self._task_audio_dir(task_id)
        src_image_dir = self._task_image_dir(task_id)
        dst_audio_dir = self._render_task_audio_dir(task_id)
        dst_image_dir = self._render_task_image_dir(task_id)

        if dst_audio_dir.exists():
            shutil.rmtree(dst_audio_dir)
        if dst_image_dir.exists():
            shutil.rmtree(dst_image_dir)

        dst_audio_dir.parent.mkdir(parents=True, exist_ok=True)
        dst_image_dir.parent.mkdir(parents=True, exist_ok=True)

        if src_audio_dir.exists():
            shutil.copytree(src_audio_dir, dst_audio_dir)
        else:
            dst_audio_dir.mkdir(parents=True, exist_ok=True)

        if src_image_dir.exists() and any(src_image_dir.iterdir()):
            shutil.copytree(src_image_dir, dst_image_dir)
        else:
            dst_image_dir.mkdir(parents=True, exist_ok=True)

        render_placeholder = self.render_image_root / PLACEHOLDER_IMAGE_NAME
        media_placeholder = self.image_root / PLACEHOLDER_IMAGE_NAME
        if media_placeholder.exists() and not render_placeholder.exists():
            shutil.copy2(media_placeholder, render_placeholder)

    def _cleanup_render_staging(self, task_id: str):
        """清理 Remotion public 下的任务级临时素材"""
        for path in (self._render_task_audio_dir(task_id), self._render_task_image_dir(task_id)):
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

    def _cleanup_storage(self, current_task_id: str = ""):
        """清理过期媒体，控制部署后的长期占用"""
        keep_count = max(1, int(settings.video_output_keep_count or 5))
        keep_days = max(0, int(settings.video_temp_keep_days or 2))
        cutoff = datetime.now() - timedelta(days=keep_days)

        output_files = sorted(
            self.output_dir.glob("*.mp4"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for old_file in output_files[keep_count:]:
            try:
                old_file.unlink(missing_ok=True)
                print(f"[VideoService] Removed old video: {old_file.name}")
            except Exception as e:
                print(f"[VideoService] Failed to remove old video {old_file}: {e}")

        for extra_file in self.output_dir.glob("*-props.json"):
            try:
                if datetime.fromtimestamp(extra_file.stat().st_mtime) < cutoff:
                    extra_file.unlink(missing_ok=True)
            except Exception:
                pass

        self._cleanup_old_task_dirs(self.audio_root, cutoff, current_task_id)
        self._cleanup_old_task_dirs(self.image_root, cutoff, current_task_id)
        self._cleanup_old_task_dirs(self.render_audio_root, cutoff, current_task_id)
        self._cleanup_old_task_dirs(self.render_image_root, cutoff, current_task_id)

    def _cleanup_old_task_dirs(self, root: Path, cutoff: datetime, current_task_id: str = ""):
        if not root.exists():
            return

        for child in root.iterdir():
            if not child.is_dir():
                continue
            if child.name == current_task_id:
                continue
            try:
                modified_at = datetime.fromtimestamp(child.stat().st_mtime)
                if modified_at < cutoff:
                    shutil.rmtree(child, ignore_errors=True)
                    print(f"[VideoService] Removed old task dir: {child}")
            except Exception as e:
                print(f"[VideoService] Failed to cleanup {child}: {e}")

    def generate_video(
        self,
        scenic_name: str,
        username: str = "",
        trip_id: Optional[str] = None,
        trip_title: Optional[str] = None,
        trip_city: Optional[str] = None,
        source_attraction: Optional[str] = None,
    ) -> str:
        """
        生成景区介绍视频（异步后台执行）
        立即返回 task_id，前端轮询状态
        """
        self._cleanup_storage()

        task_id = f"vid_{uuid.uuid4().hex[:12]}"
        now = _now_iso()
        task = VideoTask(
            task_id=task_id,
            status="processing",
            progress=0,
            message="正在准备...",
            scenic_name=scenic_name,
            username=(username or "guest").strip() or "guest",
            created_at=now,
            updated_at=now,
            trip_id=str(trip_id or "").strip(),
            trip_title=str(trip_title or "").strip(),
            trip_city=str(trip_city or "").strip(),
            source_attraction=str(source_attraction or "").strip(),
        )
        _tasks[task_id] = task
        _upsert_history(task)

        # 后台线程执行生成，避免阻塞 HTTP 响应
        def _run():
            try:
                self._prepare_task_dirs(task_id)
                self._do_generate(task_id, scenic_name, username)
            except Exception as e:
                task.status = "error"
                task.message = f"生成失败: {str(e)}"
                task.progress = 0
                task.updated_at = _now_iso()
                _upsert_history(task)
                self._cleanup_render_staging(task_id)
                print(f"[VideoService] Task {task_id} failed: {e}")
            finally:
                self._cleanup_storage(current_task_id=task_id)

        self._executor.submit(_run)
        return task_id

    def _do_generate(self, task_id: str, scenic_name: str, username: str):
        """实际执行视频生成"""
        task = _tasks[task_id]

        # Step 1: 生成脚本 (0-20%)
        task.message = "正在用 LLM 生成介绍脚本..."
        task.progress = 5
        task.updated_at = _now_iso()
        _upsert_history(task)
        script = self._generate_script(scenic_name)
        task.progress = 20
        task.message = f"脚本已生成，共 {len(script)} 句话"
        task.updated_at = _now_iso()
        _upsert_history(task)

        # Step 2: 生成 TTS 音频 (20-50%)
        task.message = "正在合成语音..."
        task.progress = 25
        task.updated_at = _now_iso()
        _upsert_history(task)
        audio_files = self._generate_audio(script, task_id)
        task.progress = 50
        task.message = f"语音合成完成，共 {len(audio_files)} 段"
        task.updated_at = _now_iso()
        _upsert_history(task)

        # Step 3: 测量音频时长 (50-55%)
        task.message = "正在分析音频时长..."
        task.updated_at = _now_iso()
        _upsert_history(task)
        durations = self._measure_audio_durations(task_id, audio_files)
        task.progress = 55
        task.updated_at = _now_iso()
        _upsert_history(task)

        # Step 4: 获取景区图片 (55-70%)
        task.message = "正在获取景区图片..."
        task.progress = 60
        task.updated_at = _now_iso()
        _upsert_history(task)
        image_files = self._fetch_images(scenic_name, task_id, len(script))
        task.progress = 70
        task.message = f"已获取 {len(image_files)} 张图片"
        task.updated_at = _now_iso()
        _upsert_history(task)

        # Step 5: 确定城市
        city = self._guess_city(scenic_name)

        # Step 6: 构建 props (70-75%)
        task.message = "正在构建视频项目..."
        task.updated_at = _now_iso()
        _upsert_history(task)
        props = self._build_props(task_id, scenic_name, city, script, durations, image_files)
        task.progress = 75
        task.updated_at = _now_iso()
        _upsert_history(task)

        # Step 7: Remotion 渲染 (75-95%)
        task.message = "正在渲染视频（详细脚本，可能需要 3-8 分钟）..."
        task.progress = 80
        task.updated_at = _now_iso()
        _upsert_history(task)
        video_path = self._render_video(task_id, props)
        task.progress = 95
        task.message = "视频渲染完成！"
        task.updated_at = _now_iso()
        _upsert_history(task)

        # Step 8: 完成
        task.status = "done"
        task.progress = 100
        task.message = "视频已生成！"
        task.video_path = video_path
        task.updated_at = _now_iso()
        _upsert_history(task)

    def _generate_script(self, scenic_name: str) -> list[dict]:
        """使用 LLM 生成景区介绍脚本"""
        from ..services.llm_service import get_llm

        llm = get_llm()
        user_prompt = f'请为景区「{scenic_name}」写一篇介绍脚本。记住：只回复JSON数组！'

        messages = [
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        response = llm.invoke(messages)
        raw_text = response.strip()

        # Parse JSON from response
        script = self._extract_json_array(raw_text)

        if not script or len(script) < 8:
            # Fallback: generate a detailed script
            print(f"[VideoService] LLM script parsing failed ({len(script) if script else 0} items), using fallback. Raw: {raw_text[:200]}")
            script = self._fallback_script(scenic_name)

        # Validate expressions
        for item in script:
            if item.get("expression") not in EXPRESSION_KEYS:
                item["expression"] = "default"

        return script

    def _extract_json_array(self, text: str) -> list | None:
        """从 LLM 回复中提取 JSON 数组"""
        import re

        # Try direct parse
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in code blocks
        match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON array
        bracket_start = text.find('[')
        if bracket_start != -1:
            depth = 0
            for i in range(bracket_start, len(text)):
                if text[i] == '[':
                    depth += 1
                elif text[i] == ']':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[bracket_start:i + 1])
                        except json.JSONDecodeError:
                            break

        return None

    def _fallback_script(self, scenic_name: str) -> list[dict]:
        """生成详细的 fallback 脚本（当 LLM 解析失败时使用）"""
        return [
            # 开场欢迎
            {"text": f"嗨～大家好呀！我是红美铃，你们的专属导游！今天可真是太开心了，要带大家去一个超级棒的地方——{scenic_name}！", "expression": "confident"},
            {"text": f"{scenic_name}可是咱们中国响当当的旅游名片，无论是历史文化还是自然风光，都让人流连忘返呢～", "expression": "excited"},
            # 地理概况
            {"text": f"说到{scenic_name}的位置呀，它坐落在风景如画的地方，交通便利，每年都吸引着成千上万的游客前来打卡～", "expression": "happy3"},
            {"text": "这里的四季各有各的美，春天繁花似锦，夏天绿树成荫，秋天层林尽染，冬天更是别有一番韵味呢！", "expression": "happy_confident"},
            # 历史渊源
            {"text": f"哎呀，说到{scenic_name}的历史，那可是大有来头哦！它历经了数百年的风雨沧桑，见证了无数历史变迁。", "expression": "thinking"},
            {"text": "很多文人墨客都曾在这里留下过墨宝，每一个角落都藏着说不完的故事呢～是不是光是想想就觉得特别有意思？", "expression": "surprised"},
            {"text": "这些古老的建筑和遗迹，就像是一本打开的历史书，静静地向我们诉说着过去的辉煌岁月。", "expression": "thinking"},
            # 核心亮点
            {"text": f"好啦好啦，咱们来细说{scenic_name}里面最值得逛的地方吧！首先映入眼帘的就是那气势恢宏的主体建筑，光是站在它面前，就能感受到扑面而来的震撼！", "expression": "excited"},
            {"text": "你看那精致的雕刻和巧妙的设计，古人的智慧和匠心真是让人佩服得五体投地呀～每一处细节都包含着深厚的文化底蕴。", "expression": "happy_confident"},
            {"text": "还有那一片园林景观，小桥流水、亭台楼阁，走在其中仿佛穿越了时空，回到了几百年前的皇家园林呢～", "expression": "happy3"},
            {"text": "哇～从这里远眺，整个景区的美景尽收眼底！一定要拿出相机多拍几张，因为每个角度都美得像一幅画！", "expression": "excited"},
            {"text": "对了对了，还有一个地方可千万别错过！那里的景色被誉为「天下第一」，亲眼看到的时候，你一定会和我一样发出惊叹的～", "expression": "surprised"},
            {"text": "走在青石板路上，抚摸着斑驳的墙壁，你仿佛能听到历史的回音在耳边轻轻响起，那种感觉，真是太奇妙了！", "expression": "thinking"},
            # 文化价值
            {"text": "从文化的角度来看呢，这里不仅仅是风景美，更重要的是它承载的精神和文化价值。它是我们中华文明的重要象征之一哦～", "expression": "happy_confident"},
            {"text": "许多重要的历史事件都发生在这里，它对后世的影响一直延续到今天。来这儿旅游，可不只是看风景，更是一次深度的文化之旅！", "expression": "thinking"},
            # 旅行贴士
            {"text": "给大家几个小贴士哈～最佳游览时间是春秋两季，天气不冷不热刚刚好。建议安排一整天的时间慢慢逛，别着急，这样才能品出味道来～", "expression": "happy5"},
            {"text": "记得穿一双舒服的鞋子哦！因为里面真的很大很大，要走不少路呢。带上水和防晒用品也很有必要呀～", "expression": "default"},
            {"text": "对了，最好提前在网上预约门票，特别是节假日，现场排队的人可是人山人海呢！早上早点出发，避开人流高峰，体验会好很多～", "expression": "thinking"},
            # 深情告别
            {"text": f"哎呀，时间过得真快呀～{scenic_name}的美，真的不是几句介绍就能说完的呢！每一处景致都值得你亲自来感受、来体验。", "expression": "happy3"},
            {"text": "红美铃在这里真诚地邀请大家，有时间一定要亲自来走一走、看一看！我保证，这将是一次让你终生难忘的旅行～", "expression": "confident"},
            {"text": "好啦，今天的云游览就到这里啦～我是红美铃，咱们下次旅行再见哦！拜拜～", "expression": "happy_confident"},
        ]

    def _generate_audio(self, script: list[dict], task_id: str) -> list[str]:
        """使用 Edge TTS 生成音频，命名为 seg-00.mp3, seg-01.mp3, ...

        失败时生成静音占位 MP3，确保 Remotion 渲染不崩溃。
        段间加 0.3s 延迟防止 Edge TTS 限流。
        """
        import time

        audio_files = []
        task_audio_dir = self._task_audio_dir(task_id)
        task_audio_dir.mkdir(parents=True, exist_ok=True)

        for i, item in enumerate(script):
            text = item["text"]
            filename = f"seg-{i:02d}.mp3"
            filepath = task_audio_dir / filename

            # Skip if already exists and valid
            if filepath.exists() and filepath.stat().st_size > 100:
                audio_files.append(filename)
                continue

            success = False
            for voice in [
                "zh-CN-YunyangNeural",   # 首选：专业播音
                "zh-CN-XiaoxiaoNeural",  # 备选1：温暖自然
                "zh-CN-YunxiNeural",     # 备选2：阳光青年
            ]:
                try:
                    result = subprocess.run(
                        [
                            EDGE_TTS_BIN,
                            "--voice", voice,
                            "--text", text,
                            "--write-media", str(filepath),
                        ],
                        capture_output=True,
                        encoding=_SUBPROCESS_ENCODING,
                        timeout=60,
                        env=_build_subprocess_env(),
                    )
                    if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 100:
                        audio_files.append(filename)
                        print(f"[VideoService] TTS seg-{i:02d}: OK ({len(text)} chars, voice={voice})")
                        success = True
                        break
                    else:
                        stderr = result.stderr.decode()[:100] if result.stderr else ""
                        print(f"[VideoService] TTS seg-{i:02d} voice={voice} failed: {stderr}")
                except Exception as e:
                    print(f"[VideoService] TTS seg-{i:02d} voice={voice} error: {e}")

            if not success:
                # Generate silent MP3 as fallback (minimal valid MP3, ~2 sec)
                print(f"[VideoService] TTS seg-{i:02d}: ALL voices failed, creating silent fallback")
                self._create_silent_mp3(str(filepath), duration_sec=len(text) * 0.25)
                audio_files.append(filename)

            # Small delay between requests to avoid rate limiting
            time.sleep(0.3)

        return audio_files

    def _create_silent_mp3(self, filepath: str, duration_sec: float = 3.0):
        """创建一段静音 MP3 占位文件"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Use edge-tts with a short placeholder text
        try:
            subprocess.run(
                [EDGE_TTS_BIN, "--voice", "zh-CN-XiaoxiaoNeural",
                 "--text", "。", "--write-media", filepath],
                capture_output=True, timeout=20, check=True,
                encoding=_SUBPROCESS_ENCODING,
                env=_build_subprocess_env(),
            )
            return
        except Exception:
            pass

        # If edge-tts completely unavailable, create minimal valid MP3 from base64
        # This is a ~0.5s silent MP3 frame (smallest valid MP3)
        MINI_MP3_B64 = (
            "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAWGluZwAAAA8AAAACAAADcAD//////////////////////////////////////////////////////////////////8"
            "//8AAAAJTEFNRTMuMTAwAZYAAAAAAAAAABSAJAAGQgAAgAAAANcY7HgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//tQZAAAAEF2M8IAAgAxAAx4AAQAEBAQEBAAAAAGAAAAAQIBAQGQQAAAAAAA"
        )
        import base64
        try:
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(MINI_MP3_B64))
        except Exception:
            # Ultimate fallback: touch empty file (Remotion will show warning but continue)
            with open(filepath, "wb") as f:
                f.write(b"")

    def _measure_audio_durations(self, task_id: str, audio_files: list[str]) -> list[int]:
        """使用 mutagen 测量音频时长，转换为帧数 (30fps)"""
        durations = []
        task_audio_dir = self._task_audio_dir(task_id)
        for filename in audio_files:
            filepath = task_audio_dir / filename
            try:
                audio = MP3(str(filepath))
                duration_seconds = audio.info.length
                frames = max(90, round(duration_seconds * 30 + 10))  # +10 frames padding, min 3s
                durations.append(frames)
                print(f"[VideoService] Audio {filename}: {duration_seconds:.1f}s → {frames} frames")
            except Exception as e:
                print(f"[VideoService] Duration measurement failed for {filename}: {e}")
                durations.append(150)  # Default 5 seconds
        return durations

    def _fetch_images(self, scenic_name: str, task_id: str, count: int) -> list[str]:
        """从 Unsplash 获取景区图片"""
        from ..services.unsplash_service import get_unsplash_service

        unsplash = get_unsplash_service()
        city = self._guess_city(scenic_name)
        task_image_dir = self._task_image_dir(task_id)
        task_image_dir.mkdir(parents=True, exist_ok=True)

        image_files = []
        # 每个景区只要2-3张高质量图片，精而不多
        suffixes = ["", "scenery", "architecture"]

        for i in range(min(count, len(suffixes))):
            suffix = suffixes[i] if i > 0 else ""
            search_name = f"{scenic_name} {suffix}".strip() if suffix else scenic_name

            try:
                url = unsplash.get_photo_url_multi_strategy(
                    name=search_name,
                    city=city,
                    category="",
                )
                if url:
                    filename = f"img-{i:02d}.jpg"
                    filepath = task_image_dir / filename
                    self._download_image(url, str(filepath))
                    image_files.append(filename)
                    print(f"[VideoService] Image fetched: {task_id}/{filename}")
            except Exception as e:
                print(f"[VideoService] Image fetch failed for {search_name}: {e}")

        # If no images fetched, create placeholder
        if not image_files:
            placeholder = task_image_dir / "img-00.jpg"
            if not placeholder.exists():
                # Download a default image
                try:
                    default_url = unsplash.get_photo_url_multi_strategy(
                        name="travel China",
                        city="",
                        category="",
                    )
                    if default_url:
                        self._download_image(default_url, str(placeholder))
                        image_files.append("img-00.jpg")
                except Exception:
                    pass

        if not image_files:
            image_files.append(PLACEHOLDER_IMAGE_NAME)

        return image_files

    def _download_image(self, url: str, filepath: str):
        """下载图片到本地"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "HelloAgents/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())

    def _guess_city(self, scenic_name: str) -> str:
        """根据景区名猜测城市"""
        # 简单的景区-城市映射
        scenic_city_map = {
            "故宫": "北京", "天安门": "北京", "长城": "北京", "颐和园": "北京",
            "天坛": "北京", "鸟巢": "北京", "北海公园": "北京", "圆明园": "北京",
            "外滩": "上海", "东方明珠": "上海", "豫园": "上海", "迪士尼": "上海",
            "西湖": "杭州", "灵隐寺": "杭州", "雷峰塔": "杭州",
            "兵马俑": "西安", "大雁塔": "西安", "华清池": "西安", "钟楼": "西安",
            "武侯祠": "成都", "锦里": "成都", "宽窄巷子": "成都", "大熊猫": "成都",
            "中山陵": "南京", "夫子庙": "南京", "秦淮河": "南京",
            "洪崖洞": "重庆", "解放碑": "重庆", "磁器口": "重庆",
            "黄鹤楼": "武汉", "东湖": "武汉",
            "鼓浪屿": "厦门", "曾厝垵": "厦门",
            "布达拉宫": "拉萨",
            "丽江古城": "丽江", "玉龙雪山": "丽江",
            "漓江": "桂林", "象鼻山": "桂林",
            "张家界": "张家界",
            "黄山": "黄山",
            "泰山": "泰安",
            "九寨沟": "阿坝",
            "峨眉山": "峨眉山",
            "三亚": "三亚",
            "拙政园": "苏州", "苏州园林": "苏州", "虎丘": "苏州",
        }
        return scenic_city_map.get(scenic_name, scenic_name)

    def _build_props(
        self,
        task_id: str,
        scenic_name: str,
        city: str,
        script: list[dict],
        durations: list[int],
        image_files: list[str],
    ) -> dict:
        """构建 Remotion props"""
        scenes = []
        for i, item in enumerate(script):
            img_idx = i % len(image_files) if image_files else 0
            image_name = image_files[img_idx] if image_files else ""
            if image_name and image_name != PLACEHOLDER_IMAGE_NAME:
                image_path = f"{task_id}/{image_name}"
            else:
                image_path = PLACEHOLDER_IMAGE_NAME

            scenes.append({
                "text": item["text"],
                "expression": item.get("expression", "default"),
                "audioFile": f"{task_id}/seg-{i:02d}.mp3",
                "durationInFrames": durations[i] if i < len(durations) else 150,
                "imageFile": image_path,
            })

        total_frames = sum(s["durationInFrames"] for s in scenes) + 90  # 3s outro

        return {
            "scenicName": scenic_name,
            "city": city,
            "scenes": scenes,
            "totalFrames": total_frames,
        }

    def _find_node(self) -> str:
        """查找 node 可执行文件路径"""
        import shutil as _shutil
        if os.name == "nt":
            for candidate in [
                os.path.expandvars(r"%ProgramFiles%\nodejs\node.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\nodejs\node.exe"),
            ]:
                if Path(candidate).exists():
                    return candidate
        which = _shutil.which("node") or _shutil.which("node.exe")
        return which or "node"

    def _find_remotion_cli(self) -> str:
        """查找 remotion CLI 入口 JS 文件"""
        cli_js = self.video_generator_dir / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
        if cli_js.exists():
            return str(cli_js)
        # fallback: dist/index.js
        dist_js = self.video_generator_dir / "node_modules" / "@remotion" / "cli" / "dist" / "index.js"
        if dist_js.exists():
            return str(dist_js)
        raise RuntimeError(f"找不到 Remotion CLI 入口文件，请确认 video-generator 已安装依赖")

    def _render_video(self, task_id: str, props: dict) -> str:
        """调用 Remotion 渲染视频"""
        output_filename = f"{task_id}.mp4"
        output_path = self.output_dir / output_filename
        props_json = json.dumps(props, ensure_ascii=False)

        self._sync_task_assets_to_render_public(task_id)

        node_bin = self._find_node()
        remotion_cli = self._find_remotion_cli()
        cmd = [
            node_bin,
            remotion_cli,
            "render",
            "ScenicVideo",
            str(output_path),
            f"--props={props_json}",
            "--codec", "h264",
            "--crf", "26",
            "--width", "1280",
            "--height", "720",
            "--concurrency", str(self.remotion_concurrency),
        ]

        print(f"[VideoService] Rendering: node={node_bin} cli={remotion_cli} cwd={self.video_generator_dir}")

        env = _build_subprocess_env()
        if self.puppeteer_executable_path:
            env["PUPPETEER_EXECUTABLE_PATH"] = self.puppeteer_executable_path

        # 将 stdout 重定向到日志文件，避免管道缓冲区填满导致死锁
        render_log_path = self.output_dir / f"{task_id}_render.log"
        try:
            with open(str(render_log_path), "w", encoding="utf-8") as log_file:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.video_generator_dir),
                    stdout=log_file,
                    stderr=subprocess.PIPE,
                    encoding=_SUBPROCESS_ENCODING,
                    timeout=1800,  # 30 minute timeout for full video render
                    env=env,
                )

            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                # 同时读取日志末尾用于诊断
                log_tail = ""
                try:
                    with open(str(render_log_path), "r", encoding="utf-8") as lf:
                        lines = lf.readlines()
                        log_tail = "".join(lines[-10:]) if lines else ""
                except Exception:
                    pass
                runtime_hint = ""
                combined_output = f"{stderr}\n{log_tail}".lower()
                if "not found" in combined_output or "winerror 2" in combined_output:
                    runtime_hint = f"请先安装 Node.js 并确认 remotion 依赖已安装。node={node_bin} remotion={remotion_cli}"
                elif "puppeteer" in combined_output or "chrome" in combined_output or "browser" in combined_output:
                    runtime_hint = "请检查 Puppeteer/Chrome 运行环境是否已安装并可访问。"
                elif "module not found" in combined_output or "cannot find module" in combined_output:
                    runtime_hint = "请先在 video-generator 目录安装前端渲染依赖。"
                detail = stderr[-500:] if stderr else log_tail[-500:]
                hint = f" {runtime_hint}" if runtime_hint else ""
                raise RuntimeError(f"Remotion 渲染失败（rc={result.returncode}）。{detail or '未返回可用日志。'}{hint}")

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise RuntimeError("Remotion 渲染已结束，但没有产出有效 mp4 文件，请检查渲染依赖和输出目录权限")

            print(f"[VideoService] Render complete: {output_path} ({output_path.stat().st_size} bytes)")
            return str(output_path)

        except subprocess.TimeoutExpired:
            raise RuntimeError("视频渲染超时（超过 15 分钟），请稍后重试或检查渲染环境性能")
        finally:
            self._cleanup_render_staging(task_id)


# 全局单例
_video_service: Optional[VideoService] = None


def get_video_service() -> VideoService:
    """获取 VideoService 单例"""
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service
