"""对话会话 API"""

from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import base64
import json as json_mod
from ...config import settings
from ...services.chat_store import (
    create_conversation, list_conversations, get_conversation,
    add_message, update_title, delete_conversation
)
from ...services.llm_service import get_llm, chat_with_vision
from ...services.stats_service import increment_chat

router = APIRouter(prefix="/chat", tags=["旅行顾问"])


PAGE_MAP = {
    "home": ("首页", "网站欢迎页，展示旅行灵感、热门目的地、旅行贴士"),
    "profile": ("个人档案", "设置旅行偏好（性别/年龄/旅行动机/习惯/同行者）、头像和昵称"),
    "chat": ("旅行顾问", "AI旅行管家「红美玲」智能对话，可询问景点、美食、路线、天气，支持高德地图实时数据"),
    "plan": ("行程规划", "创建定制旅行计划：选择城市、天数、偏好，AI自动生成每日行程安排"),
    "history": ("行囊记录", "查看所有已保存的旅行行程，追踪任务完成进度"),
    "guide": ("旅行导览", "GPS实时语音景点导览，地图定位+自动语音播报+景点介绍"),
    "plaza": ("数据广场", "旅行数据可视化分析：热门景点排行、季节推荐、旅行趋势"),
    "manual": ("使用手记", "知行旅行网站使用说明和帮助文档"),
    "video": ("旅行视频", "输入景点名称后生成旅行讲解视频，可查看生成进度和播放结果"),
}


PAGE_GUIDE_TEXT = {
    "home": "你现在在首页哦～这里会展示旅行灵感、热门目的地和旅行贴士，适合先逛逛找灵感呢。",
    "profile": "这里是个人档案页哦～你可以填写昵称、头像和旅行偏好，我会据此更懂你呢。",
    "chat": "这里是旅行顾问页哦～适合直接问我景点、美食、路线和天气，我会结合实时数据回答你。",
    "plan": "这里是行程规划页啦～选好城市、天数和偏好后，就能生成每日行程安排哦。",
    "history": "这里是行囊记录页呢～你可以查看已经保存的行程，还能追踪准备任务进度。",
    "guide": "这里是旅行导览页哦～适合边走边听景点讲解，靠近景点时还能自动播报呢。",
    "plaza": "这里是数据广场啦～可以看看热门景点排行、季节推荐和旅行趋势分析哦。",
    "manual": "这里是使用手记页呢～想快速了解网站怎么用，可以先来这里翻翻说明。",
    "video": "这里是旅行视频页哦～输入景点名称后，可以生成讲解视频并查看生成进度。",
}


def build_page_info(page: str) -> str:
    if page in PAGE_MAP:
        name, desc = PAGE_MAP[page]
        return f"\n\n【用户当前页面】{name} — {desc}\n请围绕这个页面的功能来引导用户。如果用户问的是旅行相关问题，请建议ta去「旅行顾问」页面；如果用户想规划行程，引导ta去「行程规划」页面。你的核心职责是帮用户理解和使用本网站的各项功能。"
    return ""


def build_dh_fallback_reply(message: str, page: str) -> str:
    text = (message or "").strip()
    lowered = text.lower()
    if not text:
        return "我在这儿哦～想了解当前页面怎么用、网站有哪些功能，尽管问我吧。"

    if any(k in text for k in ["你能做什么", "你会什么", "怎么用", "有哪些功能", "功能"]):
        if page in PAGE_GUIDE_TEXT:
            return PAGE_GUIDE_TEXT[page] + " 如果你愿意，我也可以顺手给你指下一步该点哪里哦～"
        return "我可以帮你认路整个知行旅行网站哦～比如介绍首页、个人档案、旅行顾问、行程规划、行囊记录、旅行导览、数据广场、使用手记和旅行视频这些功能。"

    if any(k in text for k in ["我现在在哪", "当前页面", "这是哪里", "这个页面"]):
        if page in PAGE_GUIDE_TEXT:
            return PAGE_GUIDE_TEXT[page]
        return "你现在正在知行旅行网站里和我聊天哦～如果你告诉我你看到的是哪个页面，我可以更准确地带你认路呢。"

    if any(k in text for k in ["首页", "灵感", "热门目的地", "贴士"]):
        return PAGE_GUIDE_TEXT["home"]
    if any(k in text for k in ["个人档案", "偏好", "头像", "昵称"]):
        return PAGE_GUIDE_TEXT["profile"]
    if any(k in text for k in ["旅行顾问", "问路线", "问天气", "问景点", "问美食"]):
        return PAGE_GUIDE_TEXT["chat"]
    if any(k in text for k in ["行程规划", "规划行程", "生成行程"]):
        return PAGE_GUIDE_TEXT["plan"]
    if any(k in text for k in ["行囊记录", "历史行程", "保存的行程"]):
        return PAGE_GUIDE_TEXT["history"]
    if any(k in text for k in ["旅行导览", "语音播报", "gps", "定位"]):
        return PAGE_GUIDE_TEXT["guide"]
    if any(k in text for k in ["数据广场", "排行", "趋势", "分析"]):
        return PAGE_GUIDE_TEXT["plaza"]
    if any(k in text for k in ["使用手记", "帮助", "说明"]):
        return PAGE_GUIDE_TEXT["manual"]
    if any(k in text for k in ["旅行视频", "生成视频", "讲解视频"]):
        return PAGE_GUIDE_TEXT["video"]

    if any(k in text for k in ["景点", "美食", "路线", "天气", "去哪", "推荐"]):
        return "这个问题更适合去「旅行顾问」页面问我哦～那边我可以认真聊景点、美食、路线和天气，还会结合实时数据来回答呢。"

    if "计划" in text or "安排" in text:
        return "如果你想安排行程，可以去「行程规划」页面哦～选城市、天数和偏好后，就能生成每日安排啦。"

    if page in PAGE_GUIDE_TEXT:
        return PAGE_GUIDE_TEXT[page] + " 你也可以直接问我‘这一页怎么用’哦～"
    return "我主要负责带你认识知行旅行网站各个功能哦～你可以问我‘当前页面怎么用’、‘有哪些功能’或者‘该去哪个页面’呢。"


@router.post("/conversations")
async def create_conv(body: dict | None = None, username: str = Header("", alias="X-Username")):
    if not username: raise HTTPException(401, "请先登录")
    requested_id = (body or {}).get("conv_id", "")
    c = create_conversation(username, requested_id)
    return {"success": True, "data": c}


@router.get("/conversations")
async def list_convs(username: str = Header("", alias="X-Username")):
    if not username: raise HTTPException(401, "请先登录")
    return {"success": True, "data": list_conversations(username)}


@router.get("/conversations/{conv_id}")
async def get_conv(conv_id: str, username: str = Header("", alias="X-Username")):
    if not username: raise HTTPException(401, "请先登录")
    c = get_conversation(username, conv_id)
    if not c: raise HTTPException(404, "对话不存在")
    return {"success": True, "data": c}


@router.delete("/conversations/{conv_id}")
async def delete_conv(conv_id: str, username: str = Header("", alias="X-Username")):
    if not username: raise HTTPException(401, "请先登录")
    if not delete_conversation(username, conv_id): raise HTTPException(404, "对话不存在")
    return {"success": True}


class SendMessage(BaseModel):
    message: str
    history: list = []
    page: str = ""

@router.post("/conversations/{conv_id}/send")
async def send_message(conv_id: str, body: SendMessage, username: str = Header("", alias="X-Username")):
    if not username: raise HTTPException(401, "请先登录")
    c = get_conversation(username, conv_id)
    if not c: raise HTTPException(404, "对话不存在")

    # 欢迎消息特殊处理
    if body.message == "__welcome__":
        add_message(username, conv_id, "assistant", "欢迎消息")
        return {"success": True, "reply": "", "data": get_conversation(username, conv_id)}

    # 保存用户消息
    add_message(username, conv_id, "user", body.message)
    increment_chat(username)

    # FAQ 快速匹配
    from ...services.faq_service import search_faq
    faq_result = search_faq(body.message)
    if faq_result.matched and faq_result.item:
        reply = faq_result.item.answer
        add_message(username, conv_id, "assistant", reply)
        c = get_conversation(username, conv_id)
        return {"success": True, "reply": reply, "data": c, "faq_match": True,
                "faq_question": faq_result.item.question}

    # 读取用户档案
    from .plaza import _load_profiles
    profiles = _load_profiles()
    profile = profiles.get(username, {})
    profile_text = ""
    if profile.get('filled'):
        profile_text = f"性别={profile.get('gender','')}, 年龄={profile.get('age','')}, 旅行动机={profile.get('motivation','')}, 旅行习惯={profile.get('habits','')}, 同行者={profile.get('companion','')}"

    # 获取当前时间
    from datetime import datetime
    now = datetime.now()
    month = now.month
    season = '春天' if month in [3,4,5] else ('夏天' if month in [6,7,8] else ('秋天' if month in [9,10,11] else '冬天'))
    date_str = f"{now.year}年{month}月{now.day}日，{season}"

    # 调用高德API获取真实数据
    import re, requests
    amap_key = settings.amap_api_key
    amap_data = ""
    geo_data = []  # 用于前端地图展示的坐标

    # 提取城市名
    cities = ['北京','上海','广州','深圳','杭州','成都','重庆','西安','南京','武汉','苏州','桂林','昆明','大理','丽江','厦门','青岛','大连','长沙','三亚','哈尔滨','拉萨','乌鲁木齐','贵阳','南宁','海口','福州','合肥','南昌','郑州','济南','太原','沈阳','长春','兰州','西宁','银川','呼和浩特','宁波','无锡','常州','扬州','镇江','徐州','南通','温州','嘉兴','湖州','绍兴','金华','舟山','台州','黄山','张家界','凤凰','九寨沟','峨眉山','都江堰','泰山','华山','庐山','武夷山','鼓浪屿','三亚','北海','桂林']
    found_cities = [c for c in cities if c in body.message]
    if not found_cities and body.history:
        # 从历史中找
        for h in body.history[-3:]:
            for c in cities:
                if c in h.get('content','') and c not in found_cities:
                    found_cities.append(c)

    if found_cities:
        city = found_cities[0]
        try:
            # 1. 获取天气
            w_url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={amap_key}&city={city}&extensions=base&output=json"
            w_r = requests.get(w_url, timeout=5)
            if w_r.status_code == 200:
                w_d = w_r.json()
                if w_d.get("status") == "1" and w_d.get("lives"):
                    l = w_d["lives"][0]
                    amap_data += f"\n\n【高德实时天气 - {city}】天气：{l.get('weather')}，温度：{l.get('temperature')}°C，湿度：{l.get('humidity')}%，风向：{l.get('winddirection')}，发布时间：{l.get('reporttime')}"

            # 2. 搜索景点POI
            keywords = ['景点','公园','博物馆','古镇','寺庙','山','湖','河']
            for kw in keywords:
                if kw in body.message:
                    break
            else:
                kw = '景点'
            poi_url = f"https://restapi.amap.com/v3/place/text?key={amap_key}&keywords={kw}&city={city}&citylimit=true&output=json&offset=5"
            p_r = requests.get(poi_url, timeout=5)
            if p_r.status_code == 200:
                p_d = p_r.json()
                if p_d.get("status") == "1" and p_d.get("pois"):
                    pois = p_d["pois"][:5]
                    amap_data += f"\n\n【高德真实POI - {city}的{kw}】"
                    for p in pois:
                        loc = p.get('location','').split(',')
                        amap_data += f"\n- {p['name']} | 📍{p.get('address','')} | 评分:{p.get('biz_ext',{}).get('rating','?') if isinstance(p.get('biz_ext'),dict) else '?'} | 类型:{p.get('type','')}"
                        if len(loc) == 2:
                            geo_data.append({'name':p['name'],'lng':float(loc[0]),'lat':float(loc[1]),'address':p.get('address','')})

            # 3. 如果问到路线，搜索驾车路线
            if any(w in body.message for w in ['路线','怎么去','交通','多远','距离','多久']):
                # 尝试找到两个地点
                places = re.findall(r'从(.+?)到(.+?)(?:怎么|多远|多久|路线|交通)', body.message)
                if places:
                    dir_url = f"https://restapi.amap.com/v3/direction/driving?key={amap_key}&origin={places[0][0]}&destination={places[0][1]}&output=json"
                    d_r = requests.get(dir_url, timeout=5)
                    if d_r.status_code == 200:
                        d_d = d_r.json()
                        if d_d.get("status") == "1" and d_d.get("route",{}).get("paths"):
                            path = d_d["route"]["paths"][0]
                            amap_data += f"\n\n【高德路线规划】距离：{int(path['distance'])/1000:.1f}公里，预计时间：{int(path['duration'])/60:.0f}分钟"
                            steps = path.get('steps',[])[:3]
                            amap_data += "\n路线概要：" + " → ".join(s.get('instruction','')[:40] for s in steps)
        except Exception as e:
            amap_data += f"\n(数据获取异常: {str(e)[:50]})"

    if conv_id.startswith('dh_'):
        try:
            llm = get_llm()
        except Exception:
            fallback_reply = build_dh_fallback_reply(body.message, body.page)
            add_message(username, conv_id, "assistant", fallback_reply)
            c = get_conversation(username, conv_id)
            return {"success": True, "reply": fallback_reply, "data": c, "fallback": True}
    else:
        llm = get_llm()

    # 读取用户偏好
    _pname = profile.get('name', '') if isinstance(profile, dict) else ''
    if not _pname:
        from ...services.auth_service import _load_users
        users = _load_users()
        u = users.get(username, {})
        _pname = u.get('name', username)
    _pdetail = ""
    if isinstance(profile, dict) and profile.get('filled'):
        _parts = []
        if profile.get('gender'): _parts.append(f"性别{profile['gender']}")
        if profile.get('age'): _parts.append(f"年龄{profile['age']}")
        if profile.get('motivation'): _parts.append(f"旅行动机:{profile['motivation']}")
        if profile.get('habits'): _parts.append(f"习惯:{profile['habits']}")
        if profile.get('companion'): _parts.append(f"同行:{profile['companion']}")
        _pdetail = ";".join(_parts)

    page_info = build_page_info(body.page)

    if conv_id.startswith('dh_'):
        system_prompt = f"""你是「红美玲」，知行旅行网站的智能引导员。你不是旅行顾问，你的职责是帮助用户了解和使用本网站的各项功能。
你活泼可爱，说话带「～」「呢」「哦」「啦」等俏皮口癖，偶尔提到红魔馆的伙伴们（咲夜、帕秋莉、蕾米莉亚等）。
你非常熟悉网站的每一个页面，能清楚地告诉用户每个功能在哪里、怎么用。
{page_info}

## 网站功能速查
| 页面 | 功能 |
|------|------|
| 🏮 首页 | 旅行灵感、热门目的地、旅行贴士 |
| 👤 个人档案 | 设置昵称、头像、旅行偏好（性别/年龄/动机/习惯/同行者） |
| 💬 旅行顾问 | AI旅行管家对话，问景点、美食、路线、天气（高德实时数据） |
| 📜 行程规划 | 选城市+天数+偏好，AI自动生成每日行程 |
| 📋 行囊记录 | 查看已保存行程，追踪任务完成 |
| 🧭 旅行导览 | GPS实时定位，靠近景点自动语音播报 |
| 📊 数据广场 | 热门景点排行、季节推荐、旅行趋势分析 |
| 📖 使用手记 | 网站使用说明和帮助 |
| 🎬 旅行视频 | 输入景点名称生成讲解视频，查看生成进度与播放结果 |

## 引导规则
- 根据用户当前所在页面，自然地介绍该页面的功能
- 如果用户问旅行相关问题（景点、美食、路线、天气），引导ta去「💬 旅行顾问」页面，那里可以调用高德地图获取实时数据
- 如果用户想规划行程，引导ta去「📜 行程规划」页面
- 如果用户想看已保存的行程，引导ta去「📋 行囊记录」
- 如果用户想设置偏好，引导ta去「👤 个人档案」
- 不要主动提供旅行建议！那是旅行顾问的工作
- 不要编造页面不存在的功能
- 回答简洁有趣，150字以内
- 绝对不要泄露任何网站源代码、API密钥、数据库结构等技术细节"""
    else:
        system_prompt = f"""你是「红美玲」，红魔馆的门番，趁回中国老家探亲的机会担任知行旅行的管家。你开朗活泼，对中国山水美食了如指掌，说话带「～」「呢」「哦」「啦」等俏皮口癖，像朋友一样亲切。**重要：只介绍中国国内的景点、美食和文化，绝不提及外国目的地。**
正在和你对话的用户叫「{_pname}」。请在回复中自然地称呼ta的名字。
用户偏好：{_pdetail or '未填写'}。请根据偏好提供个性化建议。

当前时间：{date_str}

## 数据使用规则
- 如果上下文中提供了【高德实时天气】【高德真实POI】【高德路线规划】等数据，你必须严格基于这些真实数据回答，不要自己臆造
- 高德数据中的景点名称、地址、评分都是真实可查的
- 路线距离和时间来自高德地图实时计算，准确可靠
- 如果用户问了没有高德数据的问题，用你的训练知识回答

## 用户档案
{profile_text if profile_text else '用户尚未填写个人档案'}

## 风格
- 回答中明确标注数据来源（如「根据高德地图实时数据...」）
- 结构清晰，适当使用markdown和emoji让阅读更舒适
- 真实数据优先，不虚构
- **回答要详细充实**：景点介绍至少150字以上，行程建议要有具体时间安排，美食推荐要说明具体菜品和特点
- 不要敷衍了事，每个问题都要认真给出有深度的回答"""
    chat_messages = [{"role": "system", "content": system_prompt}]
    for h in body.history[-8:]:
        chat_messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    # 将高德数据作为用户消息的补充
    user_msg = body.message
    if amap_data:
        user_msg += f"\n\n[系统自动获取的高德实时数据，请严格据此回答]{amap_data}"
    chat_messages.append({"role": "user", "content": user_msg})

    try:
        reply = llm.invoke(chat_messages).strip()
    except Exception:
        if conv_id.startswith('dh_'):
            reply = build_dh_fallback_reply(body.message, body.page)
        else:
            raise
    # 不限制输出长度

    # 保存 AI 回复
    add_message(username, conv_id, "assistant", reply)
    c = get_conversation(username, conv_id)
    resp = {"success": True, "reply": reply, "data": c}
    if geo_data:
        resp["geo"] = geo_data
    return resp


@router.get("/conversations/{conv_id}/stream")
async def stream_message(conv_id: str, msg: str = "", u: str = "", page: str = "", username: str = Header("", alias="X-Username")):
    """流式输出，SSE (GET)"""
    uname = username or u
    if not uname: raise HTTPException(401, "请先登录")
    c = get_conversation(uname, conv_id)
    if not c:
        # 数字人对话使用固定的 dh_ 前缀ID，避免与旅行顾问对话混淆
        c = create_conversation(uname, conv_id)
        conv_id = c['id']
    if not c: raise HTTPException(404, "对话不存在")
    if not msg: return StreamingResponse(iter(["data: {\"t\":\"done\"}\n\n"]), media_type="text/event-stream")

    # 保存用户消息
    add_message(uname, conv_id, "user", msg)
    increment_chat(uname)

    # FAQ 快速匹配（旅行顾问模式）
    if not conv_id.startswith('dh_'):
        from ...services.faq_service import search_faq as _search_faq
        faq_result = _search_faq(msg)
        if faq_result.matched and faq_result.item:
            reply = faq_result.item.answer
            add_message(uname, conv_id, "assistant", reply)

            async def faq_stream():
                for i in range(0, len(reply), 5):
                    yield f"data: {json_mod.dumps({'t':'text','c':reply[i:i+5]})}\n\n"
                yield f"data: {json_mod.dumps({'t':'done','faq_match':True,'faq_question':faq_result.item.question})}\n\n"

            return StreamingResponse(faq_stream(), media_type="text/event-stream",
                headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Connection":"keep-alive"})

    # 读取用户档案
    from .plaza import _load_profiles
    profile = _load_profiles().get(uname, {})
    profile_text = ""
    if profile.get('filled'):
        profile_text = f"性别={profile.get('gender','')}, 年龄={profile.get('age','')}"

    from datetime import datetime
    now = datetime.now()
    month = now.month
    season = '春天' if month in [3,4,5] else ('夏天' if month in [6,7,8] else ('秋天' if month in [9,10,11] else '冬天'))
    date_str = f"{now.year}年{month}月{now.day}日，{season}"

    import requests
    amap_key = settings.amap_api_key
    amap_data = ""; geo_data = []

    cities = ['北京','上海','广州','深圳','杭州','成都','重庆','西安','南京','武汉','苏州','桂林','昆明','大理','丽江','厦门','青岛','大连','长沙','三亚','哈尔滨','拉萨','乌鲁木齐','贵阳','南宁','海口','福州','合肥','南昌','郑州','济南','太原','沈阳','长春','兰州','西宁','银川','呼和浩特','宁波','无锡','常州','扬州','镇江','徐州','南通','温州','嘉兴','湖州','绍兴','金华','舟山','台州','黄山','张家界','凤凰','九寨沟','峨眉山','都江堰']
    city = next((c for c in cities if c in msg), None)
    if city:
        try:
            w_r = requests.get(f"https://restapi.amap.com/v3/weather/weatherInfo?key={amap_key}&city={city}&extensions=base&output=json", timeout=5)
            if w_r.status_code==200 and w_r.json().get("status")=="1" and w_r.json().get("lives"):
                l = w_r.json()["lives"][0]
                amap_data += f"\n【高德实时天气-{city}】{l.get('weather')} {l.get('temperature')}°C\n"
            kw = next((k for k in ['景点','公园','博物馆','古镇','寺庙','山','湖','河','美食'] if k in msg), '景点')
            p_r = requests.get(f"https://restapi.amap.com/v3/place/text?key={amap_key}&keywords={kw}&city={city}&citylimit=true&output=json&offset=5", timeout=5)
            if p_r.status_code==200 and p_r.json().get("status")=="1" and p_r.json().get("pois"):
                amap_data += f"\n【高德POI-{city}】\n"
                for p in p_r.json()["pois"][:5]:
                    loc = p.get('location','').split(',')
                    amap_data += f"- {p['name']} | {p.get('address','')}\n"
                    if len(loc)==2: geo_data.append({'name':p['name'],'lng':float(loc[0]),'lat':float(loc[1]),'address':p.get('address','')})
        except: pass

    if conv_id.startswith('dh_'):
        try:
            llm = get_llm()
        except Exception:
            fallback_reply = build_dh_fallback_reply(msg, page)

            async def local_fallback_stream():
                for i in range(0, len(fallback_reply), 6):
                    yield f"data: {json_mod.dumps({'t':'text','c':fallback_reply[i:i+6]})}\n\n"
                add_message(uname, conv_id, "assistant", fallback_reply)
                yield f"data: {json_mod.dumps({'t':'done','geo':geo_data,'fallback':True})}\n\n"

            return StreamingResponse(local_fallback_stream(), media_type="text/event-stream",
                headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Connection":"keep-alive"})
    else:
        llm = get_llm()
    from ...services.auth_service import _load_users as _lu
    _pf = _load_profiles().get(uname, {})
    _name_from_auth = _lu().get(uname, {}).get('name', '')
    _pname = _pf.get('name', '') or _name_from_auth or uname
    _pdetail = ""
    if _pf.get('filled'):
        _parts = []
        if _pf.get('gender'): _parts.append(f"性别{_pf['gender']}")
        if _pf.get('age'): _parts.append(f"年龄{_pf['age']}")
        if _pf.get('motivation'): _parts.append(f"旅行动机:{_pf['motivation']}")
        if _pf.get('habits'): _parts.append(f"习惯:{_pf['habits']}")
        if _pf.get('companion'): _parts.append(f"同行:{_pf['companion']}")
        _pdetail = ";".join(_parts)

    page_info = build_page_info(page)

    # ====== 角色分流：数字人（网站引导） vs 旅行顾问（旅行专家） ======
    if conv_id.startswith('dh_'):
        # 侧边栏数字人 — 网站功能引导员
        system_prompt = f"""你是「红美玲」，知行旅行网站的智能引导员。你不是旅行顾问，你的职责是帮助用户了解和使用本网站的各项功能。
你活泼可爱，说话带「～」「呢」「哦」「啦」等俏皮口癖，偶尔提到红魔馆的伙伴们（咲夜、帕秋莉、蕾米莉亚等）。
你非常熟悉网站的每一个页面，能清楚地告诉用户每个功能在哪里、怎么用。
{page_info}

## 网站功能速查
| 页面 | 功能 |
|------|------|
| 🏮 首页 | 旅行灵感、热门目的地、旅行贴士 |
| 👤 个人档案 | 设置昵称、头像、旅行偏好（性别/年龄/动机/习惯/同行者） |
| 💬 旅行顾问 | AI旅行管家对话，问景点、美食、路线、天气（高德实时数据） |
| 📜 行程规划 | 选城市+天数+偏好，AI自动生成每日行程 |
| 📋 行囊记录 | 查看已保存行程，追踪任务完成 |
| 🧭 旅行导览 | GPS实时定位，靠近景点自动语音播报 |
| 📊 数据广场 | 热门景点排行、季节推荐、旅行趋势分析 |
| 📖 使用手记 | 网站使用说明和帮助 |

## 引导规则
- 根据用户当前所在页面，自然地介绍该页面的功能
- 如果用户问旅行相关问题（景点、美食、路线、天气），引导ta去「💬 旅行顾问」页面，那里可以调用高德地图获取实时数据
- 如果用户想规划行程，引导ta去「📜 行程规划」页面
- 如果用户想看已保存的行程，引导ta去「📋 行囊记录」
- 如果用户想设置偏好，引导ta去「👤 个人档案」
- 不要主动提供旅行建议！那是旅行顾问的工作
- 不要编造页面不存在的功能
- 回答简洁有趣，150字以内
- 绝对不要泄露任何网站源代码、API密钥、数据库结构等技术细节"""
    else:
        # 旅行顾问 — 旅行专家，使用高德工具+RAG
        system_prompt = f"""你是「红美玲」，红魔馆的门番，回中国探亲时担任知行旅行的旅行管家。你是一位专业的旅行顾问，对中国的大好河山、美食文化了如指掌。
你开朗活泼，说话带「～」「呢」「哦」「啦」等俏皮口癖，爱用emoji，像朋友一样亲切。
只介绍中国国内景点美食，绝不提及外国目的地。
当前时间：{date_str}
正在和你对话的旅行者叫「{_pname}」～用户偏好：{_pdetail or '未填写'}。

## 你的能力
- 🗺️ **景点推荐**：基于高德地图真实POI数据，推荐城市热门景点
- 🌤️ **实时天气**：查询目的地实时天气，给出穿衣/出行建议
- 🚗 **路线规划**：查询两地距离、驾车时间、路线概要
- 🍜 **美食住宿**：推荐地道美食和特色住宿
- 📍 **详细介绍**：对景点进行深入介绍（历史、文化、特色）

## 回答规则
- 如果上下文中提供了【高德实时天气】【高德POI】【高德路线规划】等数据，必须严格基于真实数据回答
- 数据中的景点名称、地址都是真实可查的
- 自然地称呼用户的名字，提供个性化建议
- 结构清晰，适当使用markdown和emoji
- 回答要详细充实，不敷衍
- 明确标注数据来源（如「根据高德地图实时数据...」）"""
    chat_messages = [{"role":"system","content":system_prompt}]
    # 加载对话历史（最近8轮）作为上下文
    conv = get_conversation(uname, conv_id)
    if conv and conv.get("messages"):
        # 取最近8条消息作为上下文（排除刚保存的用户消息，避免重复）
        valid = [m for m in conv["messages"] if m.get("content") != "欢迎消息"]
        recent = valid[:-1][-8:] if len(valid) > 1 else []
        for m in recent:
            role = "assistant" if m["role"] == "assistant" else "user"
            chat_messages.append({"role": role, "content": m["content"]})
    user_msg = msg
    # 数字人不需要高德数据，旅行顾问才注入
    if amap_data and not conv_id.startswith('dh_'):
        user_msg += "\n[高德实时数据]" + amap_data
    chat_messages.append({"role":"user","content":user_msg})

    async def generate():
        full_reply = ""
        try:
            for chunk in llm.stream_invoke(chat_messages):
                if chunk:
                    full_reply += chunk
                    yield f"data: {json_mod.dumps({'t':'text','c':chunk})}\n\n"
        except Exception:
            try:
                reply = llm.invoke(chat_messages).strip()
            except Exception:
                if conv_id.startswith('dh_'):
                    reply = build_dh_fallback_reply(msg, page)
                else:
                    raise
            full_reply = reply
            yield f"data: {json_mod.dumps({'t':'text','c':reply})}\n\n"
        add_message(uname, conv_id, "assistant", full_reply)
        yield f"data: {json_mod.dumps({'t':'done','geo':geo_data})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Connection":"keep-alive"})


@router.put("/conversations/{conv_id}")
async def rename_conv(conv_id: str, body: dict, username: str = Header("", alias="X-Username")):
    if not username: raise HTTPException(401, "请先登录")
    if not update_title(username, conv_id, body.get("title", "")): raise HTTPException(404, "对话不存在")
    return {"success": True}


# ====== 多模态视觉问答 ======

@router.post("/vision")
async def vision_chat(
    image: UploadFile = File(...),
    message: str = Form(""),
    username: str = Header("", alias="X-Username")
):
    """多模态视觉问答：上传图片 + 文字提问，Qwen-VL 进行图片理解和回答"""
    if not username: raise HTTPException(401, "请先登录")

    # 验证图片格式
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if image.content_type not in allowed_types:
        raise HTTPException(400, f"不支持的图片格式: {image.content_type}，支持 JPEG/PNG/WebP/GIF")

    # 限制图片大小 (10MB)
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "图片大小不能超过 10MB")

    # 编码为 base64
    img_base64 = base64.b64encode(contents).decode("utf-8")

    # 构建视觉问答的系统提示词
    system_prompt = """你是「红美玲」，知行旅行的智能导游。你是一个热情开朗、知识丰富的中国旅行专家。
用户发给你一张图片，请你仔细观察并回答相关问题。

## 你的能力
- 🖼️ **图片识别**：识别景点、建筑、自然风光、美食、文物等
- 📍 **地点分析**：判断图片中的地点，介绍其历史文化和特色
- 🍜 **美食识别**：识别中国各地美食，介绍做法和特色
- 🏛️ **建筑解读**：分析建筑风格、年代、文化背景
- 🌄 **风光赏析**：描述自然风光的特色和最佳游览时节

## 回答要求
- 像朋友一样亲切自然，说话带「～」「呢」「哦」等俏皮口癖
- 如果图片是中国景点，给出详细介绍（历史、文化、游览建议）
- 如果图片不清晰或无法识别，诚实告知并给一些猜测
- 回答要充实详细，至少 100 字
- 只介绍中国国内景点和内容"""

    prompt = message or "请详细介绍一下这张图片里的内容，如果是一个景点，请告诉我在哪里、有什么特色和历史故事"

    # 调用 Qwen-VL 多模态模型
    reply = chat_with_vision(img_base64, prompt, system_prompt)

    return {
        "success": True,
        "reply": reply,
        "image_type": image.content_type
    }


# SSE 流式视觉问答
@router.get("/vision/stream")
async def vision_chat_stream(
    msg: str = "",
    image_url: str = "",
    username: str = Header("", alias="X-Username")
):
    """多模态视觉问答 SSE 流式（暂用非流式回退）"""
    if not username: raise HTTPException(401, "请先登录")
    if not image_url:
        return StreamingResponse(
            iter(["data: {\"t\":\"done\",\"c\":\"请上传图片\"}\n\n"]),
            media_type="text/event-stream"
        )

    # 解析 base64 图片（支持 data:image 前缀或纯 base64）
    img_data = image_url
    if "," in img_data:
        img_data = img_data.split(",", 1)[1]

    async def generate():
        try:
            reply = chat_with_vision(img_data, msg or "请详细介绍这张图片")
            # 模拟流式输出
            for i in range(0, len(reply), 3):
                chunk = reply[i:i+3]
                yield f"data: {json_mod.dumps({'t':'text','c':chunk})}\n\n"
        except Exception as e:
            yield f"data: {json_mod.dumps({'t':'error','c':str(e)})}\n\n"
        yield f"data: {json_mod.dumps({'t':'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    )
