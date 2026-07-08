"""旅行规划API路由"""

import json
import math
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from fastapi import APIRouter, HTTPException, Header
from ...config import get_settings
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
    ParseRequest,
    ParseResponse,
    ExtractedFields,
    ErrorResponse
)
from ...agents.trip_planner_agent import get_trip_planner_agent
from ...services.llm_service import get_llm
from ...services.plaza_service import plaza_service
from .auth import get_current_user

router = APIRouter(prefix="/trip", tags=["旅行规划"])


def _get_username(authorization: str = Header("")) -> str:
    """从请求头获取当前用户名，未登录则报错"""
    return get_current_user(authorization)["username"]


def _safe_clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _safe_join(items: list[str], empty_text: str = "暂无") -> str:
    clean = [_safe_clean_text(item) for item in items if _safe_clean_text(item)]
    return "、".join(clean[:10]) if clean else empty_text


def _extract_trip_attractions(trip: dict) -> list[str]:
    names: list[str] = []
    for day in trip.get("data", {}).get("days", []):
        for attraction in day.get("attractions", []) or []:
            name = _safe_clean_text(attraction.get("name", ""))
            if name and name not in names:
                names.append(name)
    return names


def _fetch_amap_walk_context(city: str, current_location: dict | None, nearest_name: str) -> dict[str, str]:
    settings = get_settings()
    if not settings.amap_api_key or not current_location or not nearest_name:
        return {}

    lat = current_location.get("lat")
    lng = current_location.get("lng")
    if lat is None or lng is None:
        return {}

    try:
        endpoint = "https://restapi.amap.com/v3/geocode/regeo?" + urlencode({
            "key": settings.amap_api_key,
            "location": f"{lng},{lat}",
            "radius": 800,
            "extensions": "all",
            "roadlevel": 0,
        })
        with urlopen(endpoint, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        if payload.get("status") != "1":
            return {}

        regeocode = payload.get("regeocode", {}) or {}
        addr = _safe_clean_text(regeocode.get("formatted_address", ""))
        pois = regeocode.get("pois", []) or []
        top_pois = []
        for poi in pois[:3]:
            name = _safe_clean_text(poi.get("name", ""))
            distance = _safe_clean_text(poi.get("distance", ""))
            direction = _safe_clean_text(poi.get("direction", ""))
            if not name:
                continue
            desc = name
            extras = []
            if direction:
                extras.append(direction)
            if distance:
                extras.append(f"约{distance}米")
            if extras:
                desc += f"（{'，'.join(extras)}）"
            top_pois.append(desc)

        return {
            "formatted_address": addr,
            "nearby_pois": "；".join(top_pois),
            "city": city,
            "nearest_name": nearest_name,
        }
    except Exception as e:
        print(f"⚠️ 获取导览位置上下文失败: {e}")
        return {}


def _safe_float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _calc_distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _extract_trip_attraction_items(trip: dict) -> list[dict]:
    items: list[dict] = []
    for day in trip.get("data", {}).get("days", []):
        for attraction in day.get("attractions", []) or []:
            name = _safe_clean_text(attraction.get("name", ""))
            if not name:
                continue
            location = attraction.get("location") or {}
            items.append({
                "name": name,
                "lat": _safe_float(location.get("latitude")),
                "lng": _safe_float(location.get("longitude")),
                "description": _safe_clean_text(attraction.get("description", "")),
            })
    return items


def _build_replan_preview(data: dict, username: str) -> dict:
    trip_id = _safe_clean_text(data.get("tripId", ""))
    if not trip_id:
        return {"success": False, "message": "tripId不能为空"}

    from ...services.trip_store import get_trip

    trip = get_trip(username, trip_id)
    if trip is None:
        return {"success": False, "message": "当前行程不存在或已被删除"}

    mode = _safe_clean_text(data.get("mode", "nearby-first")) or "nearby-first"
    note = _safe_clean_text(data.get("note", ""))
    current_location = data.get("currentLocation") or {}
    user_lat = _safe_float(current_location.get("lat"))
    user_lng = _safe_float(current_location.get("lng"))
    done_names = {
        _safe_clean_text(item)
        for item in (data.get("doneAttractions") or [])
        if _safe_clean_text(item)
    }

    attraction_items = _extract_trip_attraction_items(trip)
    all_names = [item["name"] for item in attraction_items]
    if not done_names:
        done_names = {
            _safe_clean_text(task.get("name", ""))
            for task in trip.get("tasks", [])
            if task.get("done") and _safe_clean_text(task.get("name", ""))
        }

    remaining = [item for item in attraction_items if item["name"] not in done_names]
    if not remaining:
        return {
            "success": True,
            "data": {
                "tripId": trip_id,
                "mode": mode,
                "summary": "当前行程的景点已经全部完成，无需再调整后续路线。",
                "orderedRemainingNames": [],
                "doneNames": list(done_names),
                "reasons": [],
                "changed": False,
            }
        }

    def sort_key(item: dict):
        lat = item.get("lat")
        lng = item.get("lng")
        if user_lat is None or user_lng is None or lat is None or lng is None:
            return (1, item["name"])
        distance = _calc_distance_meters(user_lat, user_lng, lat, lng)
        return (0, distance, item["name"])

    ordered = list(remaining)
    if mode == "nearby-first":
        ordered.sort(key=sort_key)
        summary = "已优先把离你当前位置更近的景点排在前面，方便少走回头路。"
    elif mode == "light-first":
        ordered.sort(key=lambda item: (len(item.get("description", "")), sort_key(item)))
        summary = "已优先安排信息更轻量、节奏更轻松的景点，方便你放慢后半程节奏。"
    elif mode == "compact":
        ordered.sort(key=sort_key)
        ordered = ordered[:max(1, min(len(ordered), 3))]
        summary = "已帮你压缩后续安排，优先保留更值得马上去的少量景点。"
    else:
        ordered.sort(key=sort_key)
        summary = "已根据当前位置和剩余景点，给你整理了一版更顺路的后续安排。"

    ordered_names = [item["name"] for item in ordered]
    changed = ordered_names != [item["name"] for item in remaining][:len(ordered_names)]
    reasons = []
    if note:
        reasons.append(f"用户偏好：{note}")
    if user_lat is not None and user_lng is not None:
        reasons.append("已结合当前位置粗略排序")
    if mode == "compact" and len(ordered_names) < len(remaining):
        reasons.append(f"本次建议仅保留 {len(ordered_names)} 个后续重点景点")

    return {
        "success": True,
        "data": {
            "tripId": trip_id,
            "mode": mode,
            "summary": summary,
            "orderedRemainingNames": ordered_names,
            "doneNames": list(done_names),
            "reasons": reasons,
            "changed": changed,
            "remainingCount": len(remaining),
            "allRemainingNames": [item["name"] for item in remaining],
            "allTripAttractions": all_names,
        }
    }


def _fetch_amap_homepage_weather(data: dict) -> dict:
    settings = get_settings()
    if not settings.amap_api_key:
        return {"success": False, "message": "AMAP_API_KEY未配置"}

    city_text = _safe_clean_text(data.get("city", ""))
    lat = _safe_float(data.get("lat"))
    lng = _safe_float(data.get("lng"))

    display_city = ""
    weather_city = ""
    adcode = ""

    try:
        if lat is not None and lng is not None:
            endpoint = "https://restapi.amap.com/v3/geocode/regeo?" + urlencode({
                "key": settings.amap_api_key,
                "location": f"{lng},{lat}",
                "extensions": "base",
                "output": "json",
            })
            with urlopen(endpoint, timeout=8) as resp:
                payload = json.loads(resp.read().decode("utf-8"))

            if payload.get("status") != "1":
                info = _safe_clean_text(payload.get("info", "")) or "高德逆地理编码失败"
                return {"success": False, "message": info}

            regeocode = payload.get("regeocode", {}) or {}
            address_component = regeocode.get("addressComponent", {}) or {}
            city_value = address_component.get("city")
            if isinstance(city_value, list):
                city_value = city_value[0] if city_value else ""
            display_city = _safe_clean_text(city_value) or _safe_clean_text(address_component.get("district", "")) or _safe_clean_text(address_component.get("province", ""))
            weather_city = _safe_clean_text(city_value) or _safe_clean_text(address_component.get("province", "")) or display_city
            adcode = _safe_clean_text(address_component.get("adcode", ""))
        else:
            if not city_text:
                return {"success": False, "message": "城市或坐标不能为空"}
            endpoint = "https://restapi.amap.com/v3/geocode/geo?" + urlencode({
                "key": settings.amap_api_key,
                "address": city_text,
                "output": "json",
            })
            with urlopen(endpoint, timeout=8) as resp:
                payload = json.loads(resp.read().decode("utf-8"))

            if payload.get("status") != "1" or not payload.get("geocodes"):
                info = _safe_clean_text(payload.get("info", "")) or "高德地理编码失败"
                return {"success": False, "message": info}

            geo = (payload.get("geocodes") or [{}])[0] or {}
            display_city = _safe_clean_text(geo.get("city", "")) or _safe_clean_text(geo.get("district", "")) or _safe_clean_text(geo.get("province", "")) or city_text
            weather_city = _safe_clean_text(geo.get("city", "")) or _safe_clean_text(geo.get("province", "")) or display_city or city_text
            adcode = _safe_clean_text(geo.get("adcode", ""))

        if not adcode:
            return {"success": False, "message": "未获取到城市编码"}

        weather_endpoint = "https://restapi.amap.com/v3/weather/weatherInfo?" + urlencode({
            "key": settings.amap_api_key,
            "city": adcode,
            "extensions": "base",
            "output": "json",
        })
        with urlopen(weather_endpoint, timeout=8) as resp:
            weather_payload = json.loads(resp.read().decode("utf-8"))

        if weather_payload.get("status") != "1" or not weather_payload.get("lives"):
            info = _safe_clean_text(weather_payload.get("info", "")) or "高德天气查询失败"
            return {"success": False, "message": info}

        live = (weather_payload.get("lives") or [{}])[0] or {}
        live_city = _safe_clean_text(live.get("city", ""))
        return {
            "success": True,
            "data": {
                "city": display_city or live_city or city_text or "北京",
                "weatherCity": live_city or weather_city or display_city or city_text or "北京",
                "weather": _safe_clean_text(live.get("weather", "")) or "未知",
                "temperature": _safe_clean_text(live.get("temperature", "")),
                "humidity": _safe_clean_text(live.get("humidity", "")),
                "adcode": adcode,
            }
        }
    except Exception as e:
        print(f"⚠️ 获取首页天气失败: {e}")
        return {"success": False, "message": str(e) or "首页天气查询失败"}


    question = _safe_clean_text(data.get("question", ""))
    if not question:
        return {"success": False, "message": "问题不能为空"}

    trip_id = _safe_clean_text(data.get("tripId", ""))
    if not trip_id:
        return {"success": False, "message": "tripId不能为空"}

    from ...services.trip_store import get_trip

    trip = get_trip(username, trip_id)
    if trip is None:
        return {"success": False, "message": "当前行程不存在或已被删除"}

    city = _safe_clean_text(data.get("city", "") or trip.get("city", ""))
    current_location = data.get("currentLocation") or None
    nearest_attraction = data.get("nearestAttraction") or {}
    nearest_name = _safe_clean_text(nearest_attraction.get("name", ""))
    nearest_distance = nearest_attraction.get("distance")
    done_attractions = [
        _safe_clean_text(item)
        for item in (data.get("doneAttractions") or [])
        if _safe_clean_text(item)
    ]
    remaining_attractions = [
        _safe_clean_text(item)
        for item in (data.get("remainingAttractions") or [])
        if _safe_clean_text(item)
    ]
    current_intro = _safe_clean_text(data.get("currentAttractionIntro", ""))

    trip_attractions = _extract_trip_attractions(trip)
    if not done_attractions:
        done_attractions = [
            _safe_clean_text(task.get("name", ""))
            for task in trip.get("tasks", [])
            if task.get("done") and _safe_clean_text(task.get("name", ""))
        ]
    if not remaining_attractions:
        remaining_attractions = [name for name in trip_attractions if name not in done_attractions]

    detail_lines: list[str] = []
    if nearest_name:
        detail_resp = plaza_service.get_attraction_detail(nearest_name, city)
        if detail_resp.get("success"):
            detail = detail_resp.get("data", {}) or {}
            geo = detail.get("geo", {}) or {}
            current_intro = current_intro or _safe_clean_text(detail.get("intro", ""))
            if geo.get("address"):
                detail_lines.append(f"景点地址：{_safe_clean_text(geo.get('address'))}")
            if geo.get("type"):
                detail_lines.append(f"景点类型：{_safe_clean_text(geo.get('type'))}")
            if detail.get("weather"):
                detail_lines.append(f"景点天气：{_safe_clean_text(detail.get('weather'))}")
            if current_intro:
                detail_lines.append(f"景点介绍：{current_intro[:220]}")

    amap_context = _fetch_amap_walk_context(city, current_location, nearest_name)

    loc_line = "暂无精确定位"
    if current_location and current_location.get("lat") is not None and current_location.get("lng") is not None:
        loc_line = f"纬度{current_location.get('lat')}，经度{current_location.get('lng')}"

    distance_line = "未知"
    if nearest_distance is not None and nearest_distance != "":
        try:
            d = float(nearest_distance)
            distance_line = f"约{int(round(d))}米" if d < 1000 else f"约{d / 1000:.1f}公里"
        except Exception:
            distance_line = _safe_clean_text(str(nearest_distance)) or "未知"

    context_lines = [
        f"行程标题：{_safe_clean_text(trip.get('title', '')) or '未命名行程'}",
        f"旅行城市：{city or '未知'}",
        f"行程景点：{_safe_join(trip_attractions, '暂无景点数据')}",
        f"已完成景点：{_safe_join(done_attractions)}",
        f"待完成景点：{_safe_join(remaining_attractions)}",
        f"当前最近景点：{nearest_name or '暂未识别'}",
        f"距离最近景点：{distance_line}",
        f"当前位置：{loc_line}",
    ]
    if amap_context.get("formatted_address"):
        context_lines.append(f"地图定位地址：{amap_context['formatted_address']}")
    if amap_context.get("nearby_pois"):
        context_lines.append(f"附近地标：{amap_context['nearby_pois']}")
    context_lines.extend(detail_lines)

    prompt = f"""你是旅行导览数字人，正在陪游客走当前这条行程。请只基于已知导览上下文、高德定位补充信息和当前景点资料回答，不要编造票价、营业时间、精确路线时长等未提供的事实。

【当前导览上下文】
{chr(10).join(context_lines)}

【游客问题】
{question}

请输出一段适合直接语音播报的中文回答：
1. 优先回答游客此刻导览相关的问题；
2. 如果资料不足，要明确说“按我目前掌握的信息”；
3. 若无法精确定位，也要直接说明，但仍尽量结合行程给出帮助；
4. 口语化、自然、有陪伴感；
5. 控制在120字以内。
"""

    llm = get_llm()
    answer = _safe_clean_text(llm.invoke([
        {"role": "system", "content": "你是红美玲，当前身份是旅行导览数字助手，回答要像陪游客边走边讲解一样自然可靠。"},
        {"role": "user", "content": prompt}
    ]))

    if not answer:
        answer = "按我目前掌握的信息，我建议你先参考当前行程和地图位置，我们再继续导览。"

    return {
        "success": True,
        "data": {
            "answer": answer,
            "tripId": trip_id,
            "nearestAttraction": nearest_name,
        }
    }


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求,生成详细的旅行计划"
)
async def plan_trip(request: TripRequest):
    """
    生成旅行计划

    Args:
        request: 旅行请求参数

    Returns:
        旅行计划响应
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 收到旅行规划请求:")
        print(f"   城市: {request.city}")
        print(f"   日期: {request.start_date} - {request.end_date}")
        print(f"   天数: {request.travel_days}")
        print(f"{'='*60}\n")

        # 获取Agent实例
        print("🔄 获取多智能体系统实例...")
        agent = get_trip_planner_agent()

        # 生成旅行计划
        print("🚀 开始生成旅行计划...")
        trip_plan = agent.plan_trip(request)

        print("✅ 旅行计划生成成功,准备返回响应\n")

        return TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=trip_plan
        )

    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
        )


@router.post(
    "/parse",
    response_model=ParseResponse,
    summary="解析用户输入",
    description="使用 LLM 理解用户的自然语言输入，提取结构化旅行信息"
)
async def parse_input(request: ParseRequest):
    """
    解析用户自然语言输入

    Args:
        request: 用户消息和当前已提取字段

    Returns:
        提取结果 + AI 回复
    """
    try:
        llm = get_llm()

        current = request.current_fields
        system_prompt = """你是一个旅行规划助手的 NLU 模块。你的任务是从用户的自然语言中提取结构化旅行信息。

字段说明：
- city: 目的地城市（如北京、上海、杭州）
- start_date: 出发日期，格式 YYYY-MM-DD（如 2026-06-15）
- end_date: 结束日期，格式 YYYY-MM-DD
- travel_days: 旅行天数，整数
- transportation: 交通方式，取值为 公共交通 / 自驾 / 步行 / 混合
- accommodation: 住宿偏好，取值为 经济型酒店 / 舒适型酒店 / 豪华酒店 / 民宿
- preferences: 旅行偏好标签列表，可选值：历史文化 / 自然风光 / 美食 / 购物 / 艺术 / 休闲
- free_text_input: 无法归类的额外要求文本
- extra_asked: 用户是否表示已经没有其他要求了（true/false）

请严格按照以下 JSON 格式返回，不要包含任何其他内容：
{
  "extracted": {
    "city": null,
    "start_date": null,
    "end_date": null,
    "travel_days": null,
    "transportation": null,
    "accommodation": null,
    "preferences": null,
    "free_text_input": null,
    "extra_asked": false
  },
  "is_complete": false,
  "bot_reply": "你的回复"
}

规则：
1. 只提取用户明确提到的信息，未提及的字段设为 null
2. 如果用户表达了"没有/没了/可以/好的/行"等确认无补充的意图，extra_asked 设为 true
3. 如果所有必填字段（city, start_date, travel_days, transportation, accommodation）都已提供或已存在于 current_fields，is_complete 设为 true
4. 今天日期是 2026 年 6 月，如果用户说"下周""周末"等，请计算具体日期
5. **重要**：如果用户回答含糊、答非所问、或者无法提取到任何与当前缺失字段相关的有效信息，bot_reply 必须明确指出用户回答无效，并给出具体的回答模板。例如：「抱歉，没有从你的回复中识别到有效信息。请明确告诉我你的出发日期、交通方式和住宿偏好，例如：6月20号出发，公共交通，舒适型酒店。」
6. bot_reply 应简洁专业，每次只问当前最缺的 1-3 项信息，不要一次问太多"""

        user_prompt = f"""当前已提取的字段：
{current.model_dump_json(indent=2)}

用户最新消息：
"{request.message}"

请解析并返回 JSON。"""

        # 调用 LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = llm.invoke(messages)

        # 提取 JSON
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        elif "{" in response:
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                json_str = m.group(0)

        data = json.loads(json_str)

        return ParseResponse(
            success=True,
            extracted=ExtractedFields(**data.get("extracted", {})),
            bot_reply=data.get("bot_reply"),
            is_complete=data.get("is_complete", False)
        )

    except Exception as e:
        print(f"❌ 解析用户输入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 降级：返回空提取结果
        return ParseResponse(
            success=True,
            extracted=ExtractedFields(),
            bot_reply="抱歉，我没有完全理解你的意思。请告诉我你的旅行目的地、出发日期和偏好，例如「北京，6月20号出发，3天，公共交通，舒适型酒店，喜欢历史文化」。",
            is_complete=False
        )


@router.post("/save")
async def save_trip(data: dict, authorization: str = Header("")):
    """保存旅行计划到本地存储"""
    try:
        from ...services.trip_store import save_trip
        username = _get_username(authorization)
        trip_data = data.get("trip_plan", {})
        city = trip_data.get("city", data.get("city", "未知"))
        start_date = trip_data.get("start_date", data.get("start_date", ""))
        record = save_trip(username, trip_data, city, start_date)
        return {"success": True, "message": "保存成功", "id": record["id"]}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/history")
async def list_history(authorization: str = Header("")):
    """获取当前用户已保存行程的历史列表"""
    try:
        from ...services.trip_store import list_trips
        username = _get_username(authorization)
        trips = list_trips(username)
        return {"success": True, "data": trips}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.get("/history/{trip_id}")
async def get_history_detail(trip_id: str, authorization: str = Header("")):
    """获取单条已保存行程的完整数据"""
    try:
        from ...services.trip_store import get_trip
        username = _get_username(authorization)
        trip = get_trip(username, trip_id)
        if trip is None:
            raise HTTPException(status_code=404, detail="行程不存在")
        return {"success": True, "data": trip}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取行程详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@router.put("/history/{trip_id}/tasks")
async def update_trip_tasks(trip_id: str, data: dict, authorization: str = Header("")):
    """更新任务清单（勾选/取消、修改花费）"""
    try:
        from ...services.trip_store import update_tasks
        username = _get_username(authorization)
        result = update_tasks(username, trip_id, data.get("tasks", []))
        if result is None: raise HTTPException(404, "行程不存在")
        return {"success": True, "message": "已更新", "data": result}
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(500, f"更新失败: {str(e)}")


@router.put("/history/{trip_id}")
async def update_trip_detail(
    trip_id: str,
    data: dict,
    authorization: str = Header("")
):
    """更新行程的文字备注、附件、出发前清单与旅程信息"""
    try:
        from ...services.trip_store import update_trip
        username = _get_username(authorization)
        result = update_trip(
            username,
            trip_id,
            data.get("notes"),
            data.get("images"),
            data.get("files"),
            data.get("prep_checklist"),
            data.get("trip_info"),
        )
        if result is None:
            raise HTTPException(status_code=404, detail="行程不存在")
        return {"success": True, "message": "更新成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/history/{trip_id}")
async def delete_history(trip_id: str, authorization: str = Header("")):
    """删除一条已保存的行程"""
    try:
        from ...services.trip_store import delete_trip
        username = _get_username(authorization)
        ok = delete_trip(username, trip_id)
        if not ok:
            raise HTTPException(status_code=404, detail="行程不存在")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/add-attraction")
async def add_attraction_to_trip(data: dict, authorization: str = Header("")):
    """将数据广场景点加入已有行程"""
    try:
        from ...services.trip_store import add_attraction_to_trip, build_plaza_trip_attraction

        username = _get_username(authorization)
        trip_id = _safe_clean_text(data.get("tripId", ""))
        if not trip_id:
            return {"success": False, "message": "tripId不能为空"}

        payload = data.get("attraction") or data
        attraction = build_plaza_trip_attraction(payload)
        day_index = int(data.get("dayIndex", 0) or 0)
        result = add_attraction_to_trip(username, trip_id, attraction, day_index)
        if result is None:
            return {"success": False, "message": "加入行程失败，请检查景点信息或目标行程是否存在"}
        return {"success": True, "message": "已加入行程", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 加入行程失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/create-with-attraction")
async def create_trip_with_attraction(data: dict, authorization: str = Header("")):
    """从数据广场快速创建包含单个景点的最小行程"""
    try:
        from ...services.trip_store import create_trip_with_attraction, build_plaza_trip_attraction

        username = _get_username(authorization)
        payload = data.get("attraction") or data
        city = _safe_clean_text(data.get("city", "") or payload.get("city", "")) or "未知城市"
        start_date = _safe_clean_text(data.get("startDate", ""))
        if not start_date:
            return {"success": False, "message": "startDate不能为空"}
        attraction = build_plaza_trip_attraction(payload)
        if not _safe_clean_text(attraction.get("name", "")):
            return {"success": False, "message": "景区名称不能为空"}
        result = create_trip_with_attraction(username, city, start_date, attraction)
        return {"success": True, "message": "已创建行程", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建最小行程失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/replan/preview")
async def preview_replanned_route(data: dict, authorization: str = Header("")):
    """根据当前位置和剩余景点生成重规划建议预览"""
    try:
        username = _get_username(authorization)
        return _build_replan_preview(data, username)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 生成重规划建议失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/replan/apply")
async def apply_replanned_route(data: dict, authorization: str = Header("")):
    """应用用户确认后的重规划结果"""
    try:
        from ...services.trip_store import apply_replanned_route

        username = _get_username(authorization)
        trip_id = _safe_clean_text(data.get("tripId", ""))
        ordered_remaining_names = [
            _safe_clean_text(item)
            for item in (data.get("orderedRemainingNames") or [])
            if _safe_clean_text(item)
        ]
        done_names = [
            _safe_clean_text(item)
            for item in (data.get("doneNames") or [])
            if _safe_clean_text(item)
        ]
        if not trip_id:
            return {"success": False, "message": "tripId不能为空"}
        result = apply_replanned_route(username, trip_id, ordered_remaining_names, done_names)
        if result is None:
            return {"success": False, "message": "应用失败，当前行程不存在"}
        return {"success": True, "message": "已应用新的后续路线", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 应用重规划失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/guide/ask")
async def ask_guide_question(data: dict, authorization: str = Header("")):
    """旅行导览数字人问答"""
    try:
        username = _get_username(authorization)
        return _build_guide_answer(data, username)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 导览问答失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/homepage-weather")
async def get_homepage_weather(data: dict):
    """首页天气与定位信息"""
    return _fetch_amap_homepage_weather(data)


@router.post("/suggest")
async def get_suggestion(data: dict):
    """生活建议 / 旅行顾问对话"""
    try:
        llm = get_llm()
        if data.get("_chat"):
            # 旅行顾问模式
            user_msg = data.get("_message", "")
            username = data.get("_username", "")
            if username:
                try:
                    from ...services.stats_service import increment_chat
                    increment_chat(username)
                except: pass

            # 构建带上下文的 messages
            history = data.get("_history", [])
            chat_messages = [
                {"role": "system", "content": "你是红美玲，来自东方Project红魔馆的门番，回中国老家探亲时担任知行旅行的导游管家。你开朗活泼，对中国山水美食了如指掌，喜欢用「～」「呢」「哦」结尾。回答旅行相关问题：目的地推荐、行程建议、景点介绍、美食推荐、交通住宿、穿搭提醒等。回答亲切有趣，200字以内。"},
            ]
            # 加入历史上下文（最近10轮）
            for h in history[-10:]:
                chat_messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            chat_messages.append({"role": "user", "content": user_msg})

            reply = llm.invoke(chat_messages).strip()
            if len(reply) > 300:
                reply = reply[:300]
            return {"success": True, "suggestion": reply}

        # 生活建议模式（缓存1小时）
        import hashlib, os as _os, time as _time
        from pathlib import Path as _Path
        _DATA_DIR = _Path(__file__).parent.parent.parent / "data"
        city = data.get("city", "未知城市")
        weather = data.get("weather", "晴")
        temp = data.get("temp", "20")
        time_str = data.get("time", "")
        cache_key = hashlib.md5(f"suggest_{city}_{weather}_{temp}".encode()).hexdigest()
        cache_file = _DATA_DIR / f"suggest_{cache_key}.json"
        if cache_file.exists():
            if _time.time() - _os.path.getmtime(cache_file) < 3600:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.loads(f.read())
                    return {"success": True, "suggestion": cached['s']}

        prompt = f"用户位于{city}，当前天气{weather}，温度{temp}°C，时间{time_str}。请给出一条简短实用的生活建议（15字以内，不要加引号，像朋友提醒一样自然）。"
        messages = [
            {"role": "system", "content": "你是红美玲，知行旅行的管家。像朋友一样给出简短实用的生活建议，俏皮亲切。只推荐中国国内相关内容。"},
            {"role": "user", "content": prompt}
        ]
        suggestion = llm.invoke(messages).strip().strip('"').strip('"').strip()
        if len(suggestion) > 20:
            suggestion = suggestion[:20]
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'s': suggestion}))
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        print(f"❌ 生成建议失败: {e}")
        return {"success": True, "suggestion": "祝你今天开心～" if not data.get("_chat") else "抱歉，请换个问题试试～"}


@router.get("/stats")
async def get_stats(authorization: str = Header("")):
    """获取用户平台使用统计"""
    try:
        from ...services.stats_service import get_user_stats
        username = _get_username(authorization)
        stats = get_user_stats(username)
        return {"success": True, "data": stats}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取统计失败: {e}")
        return {"success": True, "data": {"chat_count": 0, "trip_count": 0, "note_count": 0, "city_count": 0, "total_users": 1, "better_than": 0}}


@router.get(
    "/health",
    summary="健康检查",
    description="检查旅行规划服务是否正常"
)
async def health_check():
    """健康检查"""
    try:
        # 检查Agent是否可用
        agent = get_trip_planner_agent()

        # 汇总各Agent的工具数量
        tools_info = {
            "attraction_agent": len(agent.attraction_agent.list_tools()),
            "weather_agent": len(agent.weather_agent.list_tools()),
            "hotel_agent": len(agent.hotel_agent.list_tools()),
        }

        return {
            "status": "healthy",
            "service": "trip-planner",
            "agents": {
                "attraction_agent": agent.attraction_agent.name,
                "weather_agent": agent.weather_agent.name,
                "hotel_agent": agent.hotel_agent.name,
                "planner_agent": agent.planner_agent.name,
            },
            "tools_count": sum(tools_info.values()),
            "tools_detail": tools_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )

