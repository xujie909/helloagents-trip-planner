"""数据广场服务"""

import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import requests

from ..config import settings
from .llm_service import get_llm
from .unsplash_service import get_unsplash_service

DATA_DIR = Path(__file__).parent.parent / "data"
ATTRACTION_CACHE_DIR = DATA_DIR / "attraction_cache"
KNOWLEDGE_BASE_FILE = DATA_DIR / "knowledge_base.json"
PLAZA_FILE = DATA_DIR / "plaza_data.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
CITY_PROVINCE_MAP_FILE = DATA_DIR / "city_province_map.json"
INSIGHTS_CACHE_FILE = DATA_DIR / "insights_cache.json"


class PlazaService:
    """数据广场相关服务"""

    def __init__(self):
        self._http = requests.Session()

    def load_plaza(self) -> dict:
        with open(PLAZA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_profiles(self) -> dict:
        if not PROFILES_FILE.exists():
            return {}
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_profiles(self, profiles: dict) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)

    def get_provinces(self) -> list:
        plaza = self.load_plaza()
        return [
            {"name": province, "count": info["count"], "cityCount": len(info["cities"])}
            for province, info in sorted(plaza.items(), key=lambda item: -item[1]["count"])
        ]

    def get_province_detail(self, province: str) -> dict | None:
        plaza = self.load_plaza()
        return plaza.get(province)

    def search_attractions(self, query: str = "") -> list:
        plaza = self.load_plaza()
        results = []
        lowered_query = query.lower()
        for province, info in plaza.items():
            for city in info.get("cities", []):
                for attraction in city.get("attractions", []):
                    if lowered_query in attraction["name"].lower():
                        results.append({
                            "name": attraction["name"],
                            "count": attraction["count"],
                            "city": city["name"],
                            "province": province,
                        })
        return sorted(results, key=lambda item: -item["count"])[:20]

    def recommend_for_user(self, username: str) -> str:
        cache_file = DATA_DIR / f"recommend_cache_{username}.json"
        if cache_file.exists() and datetime.now().timestamp() - os.path.getmtime(cache_file) < 300:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)["r"]

        llm = get_llm()
        profiles = self.load_profiles()
        profile = profiles.get(username, {})
        plaza = self.load_plaza()
        hot = sorted(plaza.items(), key=lambda item: -item[1]["count"])[:5]
        hot_str = "、".join(f"{province}({info['count']}人次)" for province, info in hot)

        prompt = f"""你是一个旅行推荐专家。根据以下信息给用户推荐旅行目的地：

用户档案：性别={profile.get('gender', '未知')}，年龄={profile.get('age', '未知')}，
旅行动机={profile.get('motivation', '未知')}，旅行习惯={profile.get('habits', '未知')}，
同行者={profile.get('companion', '未知')}，偏好={profile.get('preference', '未知')}

平台热门目的地：{hot_str}

请给出1-2个具体推荐（含推荐理由），80字以内，像朋友聊天一样。"""
        messages = [
            {"role": "system", "content": "你是旅行推荐专家。回复简洁自然。"},
            {"role": "user", "content": prompt},
        ]
        reply = llm.invoke(messages).strip()
        if len(reply) > 150:
            reply = reply[:150]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"r": reply}, f)
        return reply

    def save_profile(self, username: str, data: dict) -> None:
        profiles = self.load_profiles()
        current = profiles.get(username, {}) if isinstance(profiles.get(username, {}), dict) else {}
        profiles[username] = {
            **current,
            "gender": data.get("gender", ""),
            "age": data.get("age", ""),
            "motivation": data.get("motivation", ""),
            "habits": data.get("habits", ""),
            "companion": data.get("companion", ""),
            "preference": data.get("preference", ""),
            "filled": True,
        }
        self.save_profiles(profiles)

    def get_profile(self, username: str) -> dict:
        profiles = self.load_profiles()
        return profiles.get(username, {})

    def _build_attraction_state_key(self, name: str, city: str = "") -> str:
        return f"{str(name or '').strip().lower()}|{str(city or '').strip().lower()}"

    def _normalize_attraction_state(self, item: dict | None, name: str = "", city: str = "") -> dict:
        state = dict(item or {})
        normalized_name = str(state.get("name") or name or "").strip()
        normalized_city = str(state.get("city") or city or "").strip()
        return {
            "name": normalized_name,
            "city": normalized_city,
            "favorite": bool(state.get("favorite")),
            "want_to_go": bool(state.get("want_to_go")),
            "visited": bool(state.get("visited")),
            "checked_in": bool(state.get("checked_in")),
            "updated_at": state.get("updated_at", ""),
        }

    def get_attraction_state(self, username: str, name: str, city: str = "") -> dict:
        if not username:
            return self._normalize_attraction_state(None, name, city)
        profiles = self.load_profiles()
        user_profile = profiles.get(username, {}) if isinstance(profiles.get(username, {}), dict) else {}
        states = user_profile.get("attraction_states", {}) if isinstance(user_profile.get("attraction_states", {}), dict) else {}
        key = self._build_attraction_state_key(name, city)
        return self._normalize_attraction_state(states.get(key), name, city)

    def update_attraction_state(self, username: str, name: str, city: str, payload: dict) -> dict:
        if not username:
            raise ValueError("用户名不能为空")
        clean_name = str(name or "").strip()
        clean_city = str(city or "").strip()
        if not clean_name:
            raise ValueError("景区名称不能为空")

        profiles = self.load_profiles()
        user_profile = profiles.get(username, {}) if isinstance(profiles.get(username, {}), dict) else {}
        states = user_profile.get("attraction_states", {}) if isinstance(user_profile.get("attraction_states", {}), dict) else {}
        key = self._build_attraction_state_key(clean_name, clean_city)
        current = self._normalize_attraction_state(states.get(key), clean_name, clean_city)

        for field in ["favorite", "want_to_go", "visited", "checked_in"]:
            if field in payload:
                current[field] = bool(payload.get(field))

        if current["checked_in"]:
            current["visited"] = True
        if current["visited"] is False:
            current["checked_in"] = False

        current["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        states[key] = current
        user_profile["attraction_states"] = states
        profiles[username] = user_profile
        self.save_profiles(profiles)
        return current

    def list_attraction_states(self, username: str) -> list[dict]:
        if not username:
            return []
        profiles = self.load_profiles()
        user_profile = profiles.get(username, {}) if isinstance(profiles.get(username, {}), dict) else {}
        states = user_profile.get("attraction_states", {}) if isinstance(user_profile.get("attraction_states", {}), dict) else {}
        items = [self._normalize_attraction_state(value) for value in states.values()]
        items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return items

    def get_insights(self) -> dict:
        """基于数据的季节性+人群分析推荐（缓存10分钟）"""
        if INSIGHTS_CACHE_FILE.exists():
            mtime = os.path.getmtime(INSIGHTS_CACHE_FILE)
            if datetime.now().timestamp() - mtime < 600:
                with open(INSIGHTS_CACHE_FILE, "r", encoding="utf-8") as f:
                    return {"success": True, "data": json.load(f)}

        excel_path = settings.get_scenic_insights_excel_path()
        if not excel_path:
            return {
                "success": False,
                "message": "未配置景区洞察数据文件，请在后端环境变量中设置 SCENIC_INSIGHTS_EXCEL_PATH",
            }
        if not excel_path.exists():
            return {
                "success": False,
                "message": f"景区洞察数据文件不存在: {excel_path}",
            }

        import openpyxl

        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        try:
            ws = wb["景点景区旅游数据行为分析数据"]
            rows = list(ws.iter_rows(values_only=True))
        finally:
            wb.close()

        data = rows[1:]
        month = datetime.now().month
        season = self._month_to_season(month)
        next_season = {
            "春天": "夏天",
            "夏天": "秋天",
            "秋天": "冬天",
            "冬天": "春天",
        }[season]

        season_attr = defaultdict(Counter)
        for row in data:
            if not row[4] or not row[7]:
                continue
            try:
                row_month = int(str(row[7])[5:7])
                row_season = self._month_to_season(row_month)
                season_attr[row_season][str(row[4])] += 1
            except Exception:
                pass

        gender_type = defaultdict(Counter)
        for row in data:
            if not row[3] or not row[6]:
                continue
            gender_type[str(row[3])][str(row[6])] += 1

        age_groups = {"青年(19-30)": [], "中年(31-45)": [], "熟龄(46+)": []}
        for row in data:
            if not row[2] or not row[4]:
                continue
            try:
                age = int(row[2])
                group = "青年(19-30)" if age <= 30 else ("中年(31-45)" if age <= 45 else "熟龄(46+)")
                age_groups[group].append(str(row[4]))
            except Exception:
                pass

        result = {
            "season": season,
            "month": month,
            "current_season_top": [
                {"name": name, "count": count}
                for name, count in season_attr.get(season, Counter()).most_common(5)
            ],
            "next_season": next_season,
            "next_season_top": [
                {"name": name, "count": count}
                for name, count in season_attr.get(next_season, Counter()).most_common(3)
            ],
            "female_top_types": [
                {"type": scenic_type, "count": count}
                for scenic_type, count in gender_type.get("女", Counter()).most_common(3)
            ],
            "male_top_types": [
                {"type": scenic_type, "count": count}
                for scenic_type, count in gender_type.get("男", Counter()).most_common(3)
            ],
            "age_top": {
                group: [{"name": name, "count": count} for name, count in Counter(items).most_common(3)]
                for group, items in age_groups.items()
                if items
            },
        }

        with open(INSIGHTS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return {"success": True, "data": result}

    def get_attraction_detail(self, name: str, city: str = "") -> dict:
        """获取景点详细介绍（RAG知识库优先 → 缓存 → 高德+LLM）"""
        cache_file = self._get_attraction_cache_file(name, city)
        cached_result = self._load_cached_attraction_detail(cache_file)
        if cached_result:
            return cached_result

        kb_match = self._find_knowledge_base_match(name)
        if self._is_high_quality_kb_match(kb_match):
            result = self._build_kb_attraction_detail(name, city, kb_match)
            enriched_result = self._enrich_attraction_media(result, city)
            return self._store_attraction_detail(cache_file, enriched_result, "知识库")

        result = self._build_amap_attraction_detail(name, city)
        enriched_result = self._enrich_attraction_media(result, city)
        return self._store_attraction_detail(cache_file, enriched_result, "高德+LLM")

    def ask_attraction_question(self, name: str, city: str, question: str) -> dict:
        """基于当前景区详情做上下文问答，供数字人讲解使用"""
        clean_question = (question or "").strip()
        if not clean_question:
            return {"success": False, "message": "问题不能为空"}

        detail_resp = self.get_attraction_detail(name, city)
        if not detail_resp.get("success"):
            return {"success": False, "message": detail_resp.get("message", "景区详情获取失败")}

        detail = detail_resp.get("data", {})
        context_lines = [
            f"景区：{detail.get('name') or name}",
            f"城市：{city or '未知'}",
            f"来源：{detail.get('source') or detail_resp.get('source') or '未知'}",
        ]
        if detail.get("geo"):
            geo = detail["geo"]
            context_lines.extend([
                f"地址：{geo.get('address', '')}",
                f"类型：{geo.get('type', '')}",
                f"电话：{geo.get('tel', '')}",
                f"坐标：{geo.get('location', '')}",
            ])
        if detail.get("weather"):
            context_lines.append(f"天气：{detail.get('weather')}")
        if detail.get("intro"):
            context_lines.append(f"介绍：{detail.get('intro')}")

        llm = get_llm()
        prompt = f"""你是景区数字人讲解员，请只基于已知景区资料回答游客问题，不要编造门票、开放时间等未给出的事实。

【景区资料】
{chr(10).join(context_lines)}

【游客问题】
{clean_question}

请输出一段适合直接语音播报的中文回答：
1. 优先回答问题本身；
2. 若资料里没有明确答案，要明确说“目前掌握的信息里没有明确提到”，再给出稳妥建议；
3. 控制在120字以内，口语化、自然。
"""
        messages = [
            {"role": "system", "content": "你是景区数字人讲解员，回答简洁、真实、可播报。"},
            {"role": "user", "content": prompt},
        ]

        try:
            answer = llm.invoke(messages).strip()
            if not answer:
                raise ValueError("empty answer")
            return {
                "success": True,
                "data": {
                    "name": detail.get("name", name),
                    "city": city,
                    "question": clean_question,
                    "answer": answer,
                },
            }
        except Exception:
            fallback = f"抱歉，我暂时没法继续讲解{name}。你可以稍后再试，或者先看看下方的图文介绍。"
            return {
                "success": True,
                "data": {
                    "name": detail.get("name", name),
                    "city": city,
                    "question": clean_question,
                    "answer": fallback,
                },
            }

    def sync_to_plaza(self, data: dict) -> str:
        """用户完成行程后，将数据同步到广场（自动映射城市到省份）"""
        plaza = self.load_plaza()
        city = data.get("city", "")
        attractions = data.get("attractions", [])
        province = self._resolve_province(data, city)

        if province not in plaza:
            plaza[province] = {"count": 0, "cities": []}

        city_found = False
        for city_info in plaza[province]["cities"]:
            if city_info["name"] != city:
                continue
            city_info["count"] += 1
            city_found = True
            for attraction_name in attractions:
                for attraction in city_info["attractions"]:
                    if attraction["name"] == attraction_name:
                        attraction["count"] += 1
                        break
                else:
                    city_info["attractions"].append({"name": attraction_name, "count": 1, "city": city})
            break

        if not city_found:
            plaza[province]["cities"].append({
                "name": city,
                "count": 1,
                "attractions": [{"name": attraction, "count": 1, "city": city} for attraction in attractions],
            })

        plaza[province]["count"] += 1
        with open(PLAZA_FILE, "w", encoding="utf-8") as f:
            json.dump(plaza, f, ensure_ascii=False, indent=2)
        return province

    def _resolve_province(self, data: dict, city: str) -> str:
        province = data.get("province", "")
        if province and province != city:
            return province

        city_map = {}
        if CITY_PROVINCE_MAP_FILE.exists():
            with open(CITY_PROVINCE_MAP_FILE, "r", encoding="utf-8") as f:
                city_map = json.load(f)
        return city_map.get(city, city)

    def _get_attraction_cache_file(self, name: str, city: str) -> Path:
        ATTRACTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.md5(f"{name}_{city}".encode()).hexdigest()
        return ATTRACTION_CACHE_DIR / f"{cache_key}.json"

    def _load_cached_attraction_detail(self, cache_file: Path) -> dict | None:
        if not cache_file.exists():
            return None
        if time.time() - os.path.getmtime(cache_file) >= 7 * 86400:
            return None
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)

        normalized = dict(cached)
        normalized.setdefault("image", "")
        normalized.setdefault("city", "")

        if not normalized.get("image"):
            normalized = self._enrich_attraction_media(normalized, normalized.get("city", ""))
            if normalized != cached:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(normalized, f, ensure_ascii=False)

        return {"success": True, "data": normalized, "source": "缓存"}

    def _store_attraction_detail(self, cache_file: Path, result: dict, source: str) -> dict:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return {"success": True, "data": result, "source": source}

    def _enrich_attraction_media(self, result: dict, city: str) -> dict:
        enriched = dict(result)
        enriched.setdefault("image", "")
        enriched.setdefault("city", city)

        if enriched["image"]:
            return enriched

        if not settings.unsplash_access_key:
            return enriched

        try:
            image_url = get_unsplash_service().get_photo_url_multi_strategy(
                enriched.get("name", ""),
                city=city,
                category=enriched.get("geo", {}).get("type", "") if isinstance(enriched.get("geo"), dict) else "",
            )
            enriched["image"] = image_url or ""
        except Exception:
            enriched["image"] = ""
        return enriched

    def _is_high_quality_kb_match(self, kb_match: dict | None) -> bool:
        return bool(kb_match and kb_match.get("detail") and len(kb_match.get("detail", "")) > 100)

    def _find_knowledge_base_match(self, name: str) -> dict | None:
        if not KNOWLEDGE_BASE_FILE.exists():
            return None
        with open(KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as f:
            kb_data = json.load(f)

        for item in kb_data:
            item_name = item.get("name", "")
            if item_name == name or name in item_name:
                return item
            if name in item.get("detail", "")[:100]:
                return item
        return None

    def _build_kb_attraction_detail(self, name: str, city: str, kb_match: dict) -> dict:
        kb_text = self._format_kb_text(kb_match)
        weather_text = self._get_weather_text(city or name)

        llm = get_llm()
        prompt = f"""请基于以下知识库数据为景点「{name}」编写详细介绍。知识库数据已经过人工审核，确保真实准确。

【知识库数据 - 来源：知行旅行知识库】
{kb_text}

【当前天气】{weather_text}

按模板输出（Markdown，800字以上）：
## {name}
### 📍 基本概况
### 🏛️ 建筑/景观特色
### 📖 文化内涵
### 🎯 游玩亮点
### 🍜 周边推荐
### 🌤️ 出行提示

文末注明：📌 信息来源：知行旅行知识库"""
        messages = [
            {"role": "system", "content": "你基于知识库数据撰写景点介绍。只使用给定的数据，不编造。"},
            {"role": "user", "content": prompt},
        ]
        intro = llm.invoke(messages).strip()
        return {"name": name, "city": city, "intro": intro, "weather": weather_text, "source": "知识库", "image": ""}

    def _format_kb_text(self, kb_match: dict) -> str:
        return f"""名称：{kb_match.get('name', '')}
省份：{kb_match.get('province', '')}  城市：{kb_match.get('city', '')}
类别：{kb_match.get('category', '')}  标签：{', '.join(kb_match.get('tags', []))}
简介：{kb_match.get('intro', '')}
详细信息：{kb_match.get('detail', '')}"""

    def _build_amap_attraction_detail(self, name: str, city: str) -> dict:
        poi = self._search_primary_poi(name, city)
        geo_data = self._build_geo_data(name, poi)
        detail_data = self._build_amap_detail_text(poi)
        weather_text = self._get_weather_text(city or name)

        llm = get_llm()
        prompt = f"""请为景点「{name}」写旅行介绍。基于高德地图真实数据。

【高德地图数据】{detail_data}

按模板输出（Markdown，800字以上）：
## {name}
### 📍 基本概况
### 🏛️ 建筑/景观特色
### 📖 文化内涵
### 🎯 游玩亮点
### 🍜 周边推荐
### 🌤️ 出行提示
- {weather_text or '暂无实时天气'}

文末注明：📌 信息来源：DeepSeek模型 + 高德地图"""
        messages = [
            {"role": "system", "content": "你基于高德地图真实数据撰写。不编造。"},
            {"role": "user", "content": prompt},
        ]
        intro = llm.invoke(messages).strip()
        return {"name": name, "city": city, "intro": intro, "geo": geo_data, "weather": weather_text, "source": "高德+LLM", "image": ""}

    def _search_primary_poi(self, name: str, city: str) -> dict | None:
        search_json = self._safe_get_json(
            "https://restapi.amap.com/v3/place/text",
            {
                "key": settings.amap_api_key,
                "keywords": name,
                "city": city or name,
                "citylimit": "true",
                "output": "json",
                "offset": 1,
            },
            timeout=5,
        )
        if search_json.get("status") == "1" and search_json.get("pois"):
            return search_json["pois"][0]
        return None

    def _build_geo_data(self, name: str, poi: dict | None) -> dict | None:
        if not poi:
            return None
        return {
            "name": poi.get("name", name),
            "address": poi.get("address", ""),
            "location": poi.get("location", ""),
            "type": poi.get("type", ""),
            "tel": poi.get("tel", ""),
        }

    def _build_amap_detail_text(self, poi: dict | None) -> str:
        if not poi:
            return ""

        detail_lines = [
            f"地址：{poi.get('address', '')}",
            f"类型：{poi.get('type', '')}",
        ]
        deep_info = self._fetch_poi_deep_info(poi)
        if deep_info:
            detail_lines.append(f"深度信息：{deep_info}")
        return "\n".join(detail_lines) + "\n"

    def _fetch_poi_deep_info(self, poi: dict) -> str:
        if not poi.get("id"):
            return ""
        detail_json = self._safe_get_json(
            "https://restapi.amap.com/v3/place/detail",
            {"key": settings.amap_api_key, "id": poi["id"], "output": "json"},
            timeout=5,
        )
        if detail_json.get("status") == "1" and detail_json.get("pois"):
            detail_poi = detail_json["pois"][0]
            return detail_poi.get("deep_info", "")
        return ""

    def _get_weather_text(self, city: str) -> str:
        weather_json = self._safe_get_json(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            {
                "key": settings.amap_api_key,
                "city": city,
                "extensions": "base",
                "output": "json",
            },
            timeout=3,
        )
        if weather_json.get("status") == "1" and weather_json.get("lives"):
            live = weather_json["lives"][0]
            return f"天气：{live.get('weather')}，温度{live.get('temperature')}°C"
        return ""

    def _safe_get_json(self, url: str, params: dict, timeout: int) -> dict:
        try:
            response = self._http.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception:
            pass
        return {}

    def _month_to_season(self, month: int) -> str:
        if month in [3, 4, 5]:
            return "春天"
        if month in [6, 7, 8]:
            return "夏天"
        if month in [9, 10, 11]:
            return "秋天"
        return "冬天"


plaza_service = PlazaService()
