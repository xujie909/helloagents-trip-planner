"""数据广场 + 用户档案 API"""

from typing import Any

from fastapi import APIRouter, HTTPException, Header

from ...services.plaza_service import plaza_service

router = APIRouter(prefix="/plaza", tags=["数据广场"])


def _load_profiles() -> dict:
    """兼容旧调用：供 chat 路由读取用户档案。"""
    return plaza_service.load_profiles()


@router.get("/provinces")
async def get_provinces():
    """获取所有省份统计"""
    return {"success": True, "data": plaza_service.get_provinces()}


@router.get("/provinces/{province}")
async def get_province_detail(province: str):
    """获取某省份下城市/景区统计"""
    info = plaza_service.get_province_detail(province)
    if not info:
        raise HTTPException(404, "省份不存在")
    return {"success": True, "data": info}


@router.get("/attractions")
async def search_attractions(q: str = ""):
    """搜索景点"""
    return {"success": True, "data": plaza_service.search_attractions(q)}


@router.post("/recommend")
async def plaza_recommend(data: dict, username: str = Header("", alias="X-Username")):
    """AI 根据用户档案+数据广场分析推荐（5分钟缓存）"""
    try:
        return {"success": True, "recommendation": plaza_service.recommend_for_user(username)}
    except Exception:
        return {"success": True, "recommendation": "推荐你去杭州西湖，春季游人如织，风景如画～"}


# ---- 用户档案 ----
@router.get("/profile")
async def get_profile(username: str = Header("", alias="X-Username")):
    return {"success": True, "data": plaza_service.get_profile(username)}


@router.post("/profile")
async def save_profile(data: dict, username: str = Header("", alias="X-Username")):
    plaza_service.save_profile(username, data)
    return {"success": True, "message": "档案已保存"}


@router.get("/attraction/state")
async def get_attraction_state(name: str, city: str = "", username: str = Header("", alias="X-Username")):
    return {"success": True, "data": plaza_service.get_attraction_state(username, name, city)}


@router.post("/attraction/state")
async def update_attraction_state(data: dict, username: str = Header("", alias="X-Username")):
    try:
        name = str(data.get("name", "")).strip()
        city = str(data.get("city", "")).strip()
        if not name:
            return {"success": False, "message": "景区名称不能为空"}
        result = plaza_service.update_attraction_state(username, name, city, data)
        return {"success": True, "data": result, "message": "景点状态已更新"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/attraction/states")
async def list_attraction_states(username: str = Header("", alias="X-Username")):
    return {"success": True, "data": plaza_service.list_attraction_states(username)}


# ---- 用户完成行程后同步到广场 ----
@router.get("/insights")
async def get_insights():
    """基于数据的季节性+人群分析推荐（缓存到JSON，10分钟刷新）"""
    try:
        return plaza_service.get_insights()
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/attraction/ask")
async def ask_attraction_question(data: dict[str, Any]):
    """景区数字人问答接口"""
    try:
        name = str(data.get("name", "")).strip()
        city = str(data.get("city", "")).strip()
        question = str(data.get("question", "")).strip()
        if not name:
            return {"success": False, "message": "景区名称不能为空"}
        return plaza_service.ask_attraction_question(name, city, question)
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/attraction/{name}")
async def get_attraction_detail(name: str, city: str = ""):
    """获取景点详细介绍（RAG知识库优先 → 缓存 → 高德+LLM）"""
    try:
        return plaza_service.get_attraction_detail(name, city)
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/sync")
async def sync_to_plaza(data: dict, username: str = Header("", alias="X-Username")):
    """用户完成行程后，将数据同步到广场（自动映射城市到省份）"""
    try:
        province = plaza_service.sync_to_plaza(data)
        return {"success": True, "message": f"已同步到 {province}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
