"""旅行计划持久化存储 - JSON 文件存储（按用户隔离）"""

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
IMAGE_DIR = DATA_DIR / "images"

MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 单张图片最大 2MB
PREP_CATEGORIES = ["证件", "衣物", "电子设备", "洗护", "药品", "其他"]
DEFAULT_PREP_CHECKLIST = [
    {"category": "证件", "name": "身份证/护照"},
    {"category": "证件", "name": "车票/机票信息"},
    {"category": "衣物", "name": "换洗衣物"},
    {"category": "电子设备", "name": "手机充电器"},
    {"category": "电子设备", "name": "充电宝"},
    {"category": "洗护", "name": "洗漱用品"},
]


def _get_user_file(username: str) -> Path:
    return DATA_DIR / f"trips_{username}.json"



def _load_all(username: str) -> List[dict]:
    f = _get_user_file(username)
    if not f.exists():
        return []
    with open(f, "r", encoding="utf-8") as fh:
        return json.load(fh)



def _save_all(username: str, trips: List[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_get_user_file(username), "w", encoding="utf-8") as fh:
        json.dump(trips, fh, ensure_ascii=False, indent=2)



def _short_id() -> str:
    return os.urandom(4).hex()



def _generate_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex()



def _safe_int(value: object, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return max(int(float(value)), 0)
    except Exception:
        return default



def _build_budget_from_tasks(tasks: list) -> dict:
    categories = {
        "attraction": {"label": "景点", "planned": 0, "actual": 0, "count": 0},
        "meal": {"label": "餐饮", "planned": 0, "actual": 0, "count": 0},
        "hotel": {"label": "酒店", "planned": 0, "actual": 0, "count": 0},
        "other": {"label": "其他", "planned": 0, "actual": 0, "count": 0},
    }
    normalized_tasks = []
    for task in tasks or []:
        task_type = str(task.get("type", "") or "").strip() or "other"
        bucket = task_type if task_type in categories else "other"
        planned = _safe_int(task.get("planned_cost", 0))
        actual = _safe_int(task.get("actual_cost", planned), planned)
        categories[bucket]["planned"] += planned
        categories[bucket]["actual"] += actual
        categories[bucket]["count"] += 1
        normalized_tasks.append({
            "type": bucket,
            "planned_cost": planned,
            "actual_cost": actual,
        })

    total_planned = sum(item["planned"] for item in categories.values())
    total_actual = sum(item["actual"] for item in categories.values())
    return {
        "total_planned": total_planned,
        "total_actual": total_actual,
        "difference": total_actual - total_planned,
        "is_over_budget": total_actual > total_planned,
        "by_type": categories,
        "legacy": {
            "total_attractions": categories["attraction"]["planned"],
            "total_hotels": categories["hotel"]["planned"],
            "total_meals": categories["meal"]["planned"],
            "total_transportation": categories["other"]["planned"],
            "total": total_planned,
        }
    }



def _normalize_task(task: dict) -> dict:
    task_type = str(task.get("type", "") or "").strip() or "other"
    planned = _safe_int(task.get("planned_cost", 0))
    actual = _safe_int(task.get("actual_cost", planned), planned)
    return {
        "id": str(task.get("id") or _short_id()),
        "type": task_type,
        "day": str(task.get("day", "") or "").strip(),
        "name": str(task.get("name", "") or "").strip() or "未命名项目",
        "done": bool(task.get("done")),
        "planned_cost": planned,
        "actual_cost": actual,
    }



def _normalize_prep_item(item: dict) -> dict:
    category = str(item.get("category", "其他") or "其他").strip() or "其他"
    if category not in PREP_CATEGORIES:
        category = "其他"
    return {
        "id": str(item.get("id") or _short_id()),
        "category": category,
        "name": str(item.get("name", "") or "").strip() or "未命名清单项",
        "done": bool(item.get("done")),
    }



def _default_prep_checklist() -> list:
    return [
        {
            "id": _short_id(),
            "category": item["category"],
            "name": item["name"],
            "done": False,
        }
        for item in DEFAULT_PREP_CHECKLIST
    ]



def _build_checklist_summary(items: list) -> dict:
    total = len(items or [])
    done = sum(1 for item in items or [] if item.get("done"))
    return {
        "total": total,
        "done": done,
        "progress": int(done / total * 100) if total > 0 else 0,
    }



def _normalize_trip_info(info: dict | None) -> dict:
    source = info if isinstance(info, dict) else {}
    return {
        "hotel": str(source.get("hotel", "") or "").strip(),
        "transport": str(source.get("transport", "") or "").strip(),
        "tickets": str(source.get("tickets", "") or "").strip(),
        "contact": str(source.get("contact", "") or "").strip(),
        "meetingPoint": str(source.get("meetingPoint", "") or "").strip(),
    }



def _ensure_trip_shape(trip: dict) -> dict:
    city = trip.get("city", "")
    start_date = trip.get("start_date", "")
    trip["data"] = _normalize_trip_data(trip.get("data", {}), city, start_date)
    trip["tasks"] = [_normalize_task(task) for task in trip.get("tasks", [])]
    prep_checklist = trip.get("prep_checklist")
    if not isinstance(prep_checklist, list):
        prep_checklist = _default_prep_checklist()
    else:
        prep_checklist = [_normalize_prep_item(item) for item in prep_checklist if isinstance(item, dict)]
    trip["prep_checklist"] = prep_checklist
    trip["trip_info"] = _normalize_trip_info(trip.get("trip_info"))
    budget_summary = _build_budget_from_tasks(trip["tasks"])
    trip["budget_summary"] = budget_summary
    trip["checklist_summary"] = _build_checklist_summary(prep_checklist)
    trip["data"]["budget"] = budget_summary["legacy"]
    return trip



def _normalize_trip_data(trip_data: dict, city: str, start_date: str) -> dict:
    normalized = dict(trip_data or {})
    normalized.setdefault("city", city)
    normalized.setdefault("start_date", start_date)
    days = normalized.get("days")
    if not isinstance(days, list) or not days:
        normalized["days"] = [{
            "day_index": 0,
            "date": start_date,
            "title": f"{city}轻旅行",
            "attractions": [],
            "meals": [],
            "hotel": {},
            "transportation": [],
            "tips": [],
        }]
    for index, day in enumerate(normalized.get("days", [])):
        day.setdefault("day_index", index)
        day.setdefault("date", start_date)
        day.setdefault("title", f"第{index + 1}天")
        day.setdefault("attractions", [])
        day.setdefault("meals", [])
        day.setdefault("hotel", {})
        day.setdefault("transportation", [])
        day.setdefault("tips", [])
    normalized.setdefault("overall_suggestions", "")
    normalized.setdefault("budget", {
        "total_attractions": 0,
        "total_hotels": 0,
        "total_meals": 0,
        "total_transportation": 0,
        "total": 0,
    })
    return normalized



def _build_tasks(trip_data: dict) -> list:
    """根据行程数据自动生成任务清单"""
    tasks = []
    for day in trip_data.get("days", []):
        prefix = f"第{day.get('day_index', 0) + 1}天"
        for a in day.get("attractions", []):
            tasks.append({
                "id": _short_id(),
                "type": "attraction",
                "day": prefix,
                "name": a.get("name", ""),
                "done": False,
                "planned_cost": _safe_int(a.get("ticket_price", 0)),
                "actual_cost": _safe_int(a.get("ticket_price", 0)),
            })
        for m in day.get("meals", []):
            tasks.append({
                "id": _short_id(),
                "type": "meal",
                "day": prefix,
                "name": f"{m.get('type', '')}: {m.get('name', '')}",
                "done": False,
                "planned_cost": _safe_int(m.get("estimated_cost", 0)),
                "actual_cost": _safe_int(m.get("estimated_cost", 0)),
            })
        h = day.get("hotel")
        if h and h.get("name"):
            tasks.append({
                "id": _short_id(),
                "type": "hotel",
                "day": prefix,
                "name": h.get("name", ""),
                "done": False,
                "planned_cost": _safe_int(h.get("estimated_cost", 0)),
                "actual_cost": _safe_int(h.get("estimated_cost", 0)),
            })
    return tasks



def _restore_task_progress(old_tasks: list, new_tasks: list) -> list:
    progress_map = {}
    for task in old_tasks or []:
        key = (task.get("type", ""), task.get("name", ""))
        progress_map[key] = {
            "done": bool(task.get("done")),
            "planned_cost": _safe_int(task.get("planned_cost", 0)),
            "actual_cost": _safe_int(task.get("actual_cost", task.get("planned_cost", 0))),
        }

    restored = []
    for task in new_tasks:
        key = (task.get("type", ""), task.get("name", ""))
        progress = progress_map.get(key)
        if progress:
            task["done"] = progress["done"]
            task["planned_cost"] = progress["planned_cost"]
            task["actual_cost"] = progress["actual_cost"]
        restored.append(_normalize_task(task))
    return restored



def _touch_trip(trip: dict) -> None:
    trip["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



def _build_day_attraction(name: str, city: str = "", note: str = "", lat: float | None = None, lng: float | None = None, image: str = "") -> dict:
    attraction = {
        "name": name,
        "ticket_price": 0,
        "suggested_duration": "半天",
        "description": note or f"从数据广场加入：{name}",
        "image": image,
        "travel_tips": ["来自数据广场，可后续补充更详细安排"],
    }
    if lat is not None and lng is not None:
        attraction["location"] = {
            "latitude": lat,
            "longitude": lng,
            "address": city,
        }
    return attraction



def save_trip(username: str, trip_data: dict, city: str, start_date: str) -> dict:
    trips = _load_all(username)
    normalized_data = _normalize_trip_data(trip_data, city, start_date)
    record = {
        "id": _generate_id(),
        "city": city,
        "start_date": start_date,
        "title": f"{start_date} {city}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": "",
        "notes": "",
        "images": [],
        "files": [],
        "tasks": _build_tasks(normalized_data),
        "prep_checklist": _default_prep_checklist(),
        "trip_info": _normalize_trip_info(None),
        "data": normalized_data,
    }
    _ensure_trip_shape(record)
    trips.insert(0, record)
    _save_all(username, trips)
    return record



def update_tasks(username: str, trip_id: str, tasks: list) -> Optional[dict]:
    """更新任务清单（完成状态与花费）"""
    trips = _load_all(username)
    for t in trips:
        if t["id"] == trip_id:
            t["tasks"] = [_normalize_task(item) for item in tasks if isinstance(item, dict)]
            _ensure_trip_shape(t)
            _touch_trip(t)
            _save_all(username, trips)
            return t
    return None



def update_trip(
    username: str,
    trip_id: str,
    notes: Optional[str] = "",
    images: List[str] = None,
    files: List[dict] = None,
    prep_checklist: List[dict] = None,
    trip_info: Optional[dict] = None,
) -> Optional[dict]:
    """更新行程的文字备注、附件、出发前清单与旅程信息"""
    trips = _load_all(username)
    for t in trips:
        if t["id"] == trip_id:
            if notes is not None:
                t["notes"] = notes
            if images is not None:
                valid = []
                for img in images:
                    if isinstance(img, str) and img.startswith("data:image"):
                        try:
                            header, b64 = img.split(",", 1)
                            if len(base64.b64decode(b64)) <= MAX_IMAGE_SIZE:
                                valid.append(img)
                        except Exception:
                            pass
                t["images"] = valid
            if files is not None:
                valid = []
                for f in files:
                    if isinstance(f, dict) and f.get("data", "").startswith("data:"):
                        try:
                            header, b64 = f["data"].split(",", 1)
                            if len(base64.b64decode(b64)) <= 15 * 1024 * 1024:
                                valid.append(f)
                        except Exception:
                            pass
                t["files"] = valid
            if prep_checklist is not None:
                t["prep_checklist"] = [
                    _normalize_prep_item(item)
                    for item in prep_checklist
                    if isinstance(item, dict)
                ]
            if trip_info is not None:
                t["trip_info"] = _normalize_trip_info(trip_info)
            _ensure_trip_shape(t)
            _touch_trip(t)
            _save_all(username, trips)
            return t
    return None



def list_trips(username: str) -> List[dict]:
    """列出行程，按城市分组后每组内按日期排序"""
    trips = _load_all(username)
    all_sorted = sorted(trips, key=lambda t: t.get("created_at", ""), reverse=True)
    result = []
    for raw_trip in all_sorted:
        t = _ensure_trip_shape(dict(raw_trip))
        tasks = t.get("tasks", [])
        done = sum(1 for tk in tasks if tk.get("done"))
        total = len(tasks)
        result.append({
            "id": t["id"],
            "city": t["city"],
            "start_date": t["start_date"],
            "title": t.get("title", f"{t['start_date']} {t['city']}"),
            "created_at": t["created_at"],
            "updated_at": t.get("updated_at", ""),
            "has_notes": bool(t.get("notes", "")),
            "has_images": bool(t.get("images", [])),
            "image_count": len(t.get("images", [])),
            "days": len(t.get("data", {}).get("days", [])),
            "task_done": done,
            "task_total": total,
            "progress": int(done / total * 100) if total > 0 else 0,
            "preview": t.get("data", {}).get("overall_suggestions", "")[:80],
            "budget_summary": t.get("budget_summary", {}),
            "checklist_summary": t.get("checklist_summary", {}),
        })
    return result



def get_trip(username: str, trip_id: str) -> Optional[dict]:
    for t in _load_all(username):
        if t["id"] == trip_id:
            return _ensure_trip_shape(t)
    return None



def add_attraction_to_trip(
    username: str,
    trip_id: str,
    attraction: dict,
    day_index: int = 0,
) -> Optional[dict]:
    trips = _load_all(username)
    for t in trips:
        if t["id"] != trip_id:
            continue

        trip_data = _normalize_trip_data(t.get("data", {}), t.get("city", ""), t.get("start_date", ""))
        days = trip_data.get("days", [])
        if not days:
            days.append({
                "day_index": 0,
                "date": t.get("start_date", ""),
                "title": "第1天",
                "attractions": [],
                "meals": [],
                "hotel": {},
                "transportation": [],
                "tips": [],
            })
        target_index = max(0, min(day_index, len(days) - 1))
        days[target_index].setdefault("attractions", [])
        existing_names = {str(item.get("name", "")).strip() for day in days for item in day.get("attractions", [])}
        attraction_name = str(attraction.get("name", "")).strip()
        if not attraction_name:
            return None
        if attraction_name in existing_names:
            return _ensure_trip_shape(t)

        days[target_index]["attractions"].append(attraction)
        t["data"] = trip_data
        t["tasks"] = _restore_task_progress(t.get("tasks", []), _build_tasks(trip_data))
        _ensure_trip_shape(t)
        _touch_trip(t)
        _save_all(username, trips)
        return t
    return None



def create_trip_with_attraction(username: str, city: str, start_date: str, attraction: dict) -> dict:
    trip_data = _normalize_trip_data({
        "city": city,
        "start_date": start_date,
        "days": [{
            "day_index": 0,
            "date": start_date,
            "title": f"{city}轻旅行",
            "attractions": [attraction],
            "meals": [],
            "hotel": {},
            "transportation": [],
            "tips": ["这是从数据广场快速创建的行程，可继续补充更多景点。"],
        }],
        "overall_suggestions": "先收藏感兴趣景点，再逐步补全完整行程。",
    }, city, start_date)
    return save_trip(username, trip_data, city, start_date)



def apply_replanned_route(username: str, trip_id: str, ordered_remaining_names: list[str], done_names: list[str]) -> Optional[dict]:
    trips = _load_all(username)
    done_set = {str(name or "").strip() for name in done_names if str(name or "").strip()}
    ordered_names = [str(name or "").strip() for name in ordered_remaining_names if str(name or "").strip()]

    for t in trips:
        if t["id"] != trip_id:
            continue

        trip_data = _normalize_trip_data(t.get("data", {}), t.get("city", ""), t.get("start_date", ""))
        days = trip_data.get("days", [])
        attraction_map = {}
        day_remaining_sizes = []

        for day in days:
            remaining_count = 0
            day.setdefault("attractions", [])
            for item in day.get("attractions", []):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                attraction_map[name] = item
                if name not in done_set:
                    remaining_count += 1
            day_remaining_sizes.append(remaining_count)

        ordered_objects = [attraction_map[name] for name in ordered_names if name in attraction_map and name not in done_set]
        used_names = {str(item.get("name", "")).strip() for item in ordered_objects}
        for name, item in attraction_map.items():
            if name in done_set or name in used_names:
                continue
            ordered_objects.append(item)

        cursor = 0
        for index, day in enumerate(days):
            completed = []
            for item in day.get("attractions", []):
                name = str(item.get("name", "")).strip()
                if name in done_set:
                    completed.append(item)
            size = day_remaining_sizes[index]
            replacement = ordered_objects[cursor:cursor + size]
            cursor += size
            day["attractions"] = completed + replacement

        t["data"] = trip_data
        restored_tasks = _restore_task_progress(t.get("tasks", []), _build_tasks(trip_data))
        for task in restored_tasks:
            if task.get("type") == "attraction":
                task["done"] = str(task.get("name", "")).strip() in done_set
        t["tasks"] = restored_tasks
        _ensure_trip_shape(t)
        _touch_trip(t)
        _save_all(username, trips)
        return t
    return None



def delete_trip(username: str, trip_id: str) -> bool:
    trips = _load_all(username)
    new_trips = [t for t in trips if t["id"] != trip_id]
    if len(new_trips) < len(trips):
        _save_all(username, new_trips)
        return True
    return False



def build_plaza_trip_attraction(payload: dict) -> dict:
    location = payload.get("location") or {}
    lat = location.get("lat")
    lng = location.get("lng")
    return _build_day_attraction(
        name=str(payload.get("name", "")).strip(),
        city=str(payload.get("city", "")).strip(),
        note=str(payload.get("intro", "")).strip(),
        lat=float(lat) if lat not in (None, "") else None,
        lng=float(lng) if lng not in (None, "") else None,
        image=str(payload.get("image", "")).strip(),
    )
