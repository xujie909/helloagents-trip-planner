"""视频生成 API 路由"""

import logging

from fastapi import APIRouter, Header, HTTPException
from ...models.schemas import VideoGenerateRequest, VideoHistoryResponse, VideoTaskStatus
from ...services.video_service import (
    delete_video_history,
    get_video_service,
    get_task,
    list_video_history,
    sync_task_from_history,
)

router = APIRouter(prefix="/video", tags=["视频生成"])
logger = logging.getLogger(__name__)


def _normalize_username(username: str) -> str:
    return (username or "guest").strip() or "guest"


def _clean_optional_text(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def _build_task_status(task) -> VideoTaskStatus:
    video_url = None
    if task.status == "done" and task.video_path:
        video_url = f"/api/video/download/{task.task_id}"

    return VideoTaskStatus(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        message=task.message,
        video_url=video_url,
        trip_id=_clean_optional_text(getattr(task, "trip_id", None)),
        trip_title=_clean_optional_text(getattr(task, "trip_title", None)),
        trip_city=_clean_optional_text(getattr(task, "trip_city", None)),
        source_attraction=_clean_optional_text(getattr(task, "source_attraction", None)),
    )


@router.post("/generate", response_model=VideoTaskStatus)
async def generate_video(
    request: VideoGenerateRequest,
    username: str = Header("", alias="X-Username"),
):
    """生成景区介绍视频"""
    if not request.scenic_name.strip():
        raise HTTPException(status_code=400, detail="景区名称不能为空")

    try:
        service = get_video_service()
        task_id = service.generate_video(
            request.scenic_name.strip(),
            _normalize_username(username),
            trip_id=_clean_optional_text(request.trip_id),
            trip_title=_clean_optional_text(request.trip_title),
            trip_city=_clean_optional_text(request.trip_city),
            source_attraction=_clean_optional_text(request.source_attraction),
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.exception("Video generation initialization failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Video generation request failed unexpectedly")
        raise HTTPException(status_code=500, detail="视频生成服务暂时不可用，请稍后重试") from exc

    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=500, detail="视频任务已创建，但状态同步失败")
    return _build_task_status(task)


@router.get("/status/{task_id}", response_model=VideoTaskStatus)
async def get_video_status(task_id: str, username: str = Header("", alias="X-Username")):
    """查询视频生成进度"""
    task = get_task(task_id) or sync_task_from_history(task_id, _normalize_username(username))

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return _build_task_status(task)


@router.get("/history", response_model=VideoHistoryResponse)
async def get_video_history(username: str = Header("", alias="X-Username")):
    """获取视频生成历史"""
    return VideoHistoryResponse(
        success=True,
        data=list_video_history(_normalize_username(username)),
    )


@router.delete("/history/{task_id}")
async def remove_video_history(task_id: str, username: str = Header("", alias="X-Username")):
    """删除单条视频历史记录"""
    ok = delete_video_history(_normalize_username(username), task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return {"success": True, "message": "已删除该视频记录"}


@router.get("/download/{task_id}")
async def download_video(task_id: str, username: str = Header("", alias="X-Username")):
    """下载生成的视频"""
    from fastapi.responses import FileResponse
    from pathlib import Path

    task = get_task(task_id) or sync_task_from_history(task_id, _normalize_username(username))

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "done" or not task.video_path:
        raise HTTPException(status_code=400, detail="视频尚未生成完成")

    video_path = Path(task.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{task.scenic_name}_{task_id}.mp4",
    )
