"""管理员 API"""

import json, os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from ...services.auth_service import get_user_by_token

router = APIRouter(prefix="/admin", tags=["管理员"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ADMIN_USERNAME = "admin"

def _check_admin(username: str = Header("", alias="X-Username"), authorization: str = Header("")):
    """验证管理员身份"""
    if username != ADMIN_USERNAME:
        if authorization.startswith("Bearer "):
            user = get_user_by_token(authorization[7:])
            if user and user.get("username") == ADMIN_USERNAME:
                return
        raise HTTPException(403, "仅管理员可访问")

# ---- 用户管理 ----
@router.get("/users")
async def list_users(username: str = Header("", alias="X-Username")):
    """获取所有用户列表及统计"""
    _check_admin(username)
    users_file = DATA_DIR / "users.json"
    if not users_file.exists(): return {"success": True, "data": []}
    users = json.load(open(users_file, encoding="utf-8"))
    result = []
    for uname, u in users.items():
        trips_file = DATA_DIR / f"trips_{uname}.json"
        trip_count = len(json.load(open(trips_file, encoding="utf-8"))) if trips_file.exists() else 0
        chats_file = DATA_DIR / f"conversations_{uname}.json"
        chat_count = len(json.load(open(chats_file, encoding="utf-8"))) if chats_file.exists() else 0
        result.append({
            "username": uname, "created_at": u.get("created_at", ""),
            "last_login": u.get("last_login", ""), "login_count": u.get("login_count", 0),
            "trip_count": trip_count, "chat_count": chat_count,
            "disabled": u.get("disabled", False)
        })
    return {"success": True, "data": result, "total": len(result)}

@router.put("/users/{uname}/toggle")
async def toggle_user(uname: str, username: str = Header("", alias="X-Username")):
    """禁用/启用用户"""
    _check_admin(username)
    if uname == ADMIN_USERNAME: raise HTTPException(400, "不能操作管理员账号")
    users_file = DATA_DIR / "users.json"
    users = json.load(open(users_file, encoding="utf-8"))
    if uname not in users: raise HTTPException(404, "用户不存在")
    users[uname]["disabled"] = not users[uname].get("disabled", False)
    json.dump(users, open(users_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"success": True, "disabled": users[uname]["disabled"]}

@router.delete("/users/{uname}")
async def delete_user(uname: str, username: str = Header("", alias="X-Username")):
    """删除用户及所有数据"""
    _check_admin(username)
    if uname == ADMIN_USERNAME: raise HTTPException(400, "不能删除管理员账号")
    users_file = DATA_DIR / "users.json"
    users = json.load(open(users_file, encoding="utf-8"))
    if uname not in users: raise HTTPException(404, "用户不存在")
    del users[uname]
    json.dump(users, open(users_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # 清理用户数据文件
    for f in DATA_DIR.glob(f"{uname}*"):
        try: os.remove(f)
        except: pass
    return {"success": True}

# ---- 数据广场管理 ----
@router.get("/plaza")
async def get_plaza_data(username: str = Header("", alias="X-Username")):
    """获取广场数据（管理员可编辑）"""
    _check_admin(username)
    f = DATA_DIR / "plaza_data.json"
    if not f.exists(): return {"success": True, "data": {}}
    return {"success": True, "data": json.load(open(f, encoding="utf-8"))}

@router.post("/plaza/update")
async def update_plaza(data: dict, username: str = Header("", alias="X-Username")):
    """更新广场数据（同步清除缓存，实时生效）"""
    _check_admin(username)
    json.dump(data.get("data", {}), open(DATA_DIR / "plaza_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # 清除景点缓存，确保用户查询使用最新数据
    import shutil
    cache_dir = DATA_DIR / "attraction_cache"
    if cache_dir.exists(): shutil.rmtree(cache_dir); cache_dir.mkdir()
    return {"success": True, "message": "已更新，缓存已刷新"}

# ---- 知识库(RAG) ----
@router.get("/knowledge")
async def list_knowledge(username: str = Header("", alias="X-Username")):
    """获取知识库列表"""
    _check_admin(username)
    f = DATA_DIR / "knowledge_base.json"
    if not f.exists(): return {"success": True, "data": []}
    return {"success": True, "data": json.load(open(f, encoding="utf-8"))}

@router.post("/knowledge/import")
async def import_knowledge(data: dict, username: str = Header("", alias="X-Username")):
    """导入景点知识（AI自动分类）"""
    _check_admin(username)
    items = data.get("items", [])
    if not items: raise HTTPException(400, "至少需要一条数据")

    # AI分类
    from ...services.llm_service import get_llm
    llm = get_llm()
    classified = []
    for item in items:
        try:
            prompt = f"""请为以下景点信息分类，返回JSON格式（只返回JSON，不要其他内容）：
{{"name":"景点名","province":"省份","city":"城市","category":"类别(如:古镇水乡/风景名胜/主题乐园/博物馆/自然公园/现代地标/历史文化/动植物园)","tags":["标签1","标签2"],"intro":"50字简介","detail":"{item.get('detail','')[:300]}"}}

景点信息：名称={item.get('name','')}，内容={item.get('detail','')[:200]}"""
            msgs = [{"role":"system","content":"你是旅游数据分类专家。只返回JSON。"},{"role":"user","content":prompt}]
            reply = llm.invoke(msgs).strip()
            if "```json" in reply: reply = reply.split("```json")[1].split("```")[0]
            elif "```" in reply: reply = reply.split("```")[1].split("```")[0]
            result = json.loads(reply)
            result["id"] = os.urandom(4).hex()
            classified.append(result)
        except: classified.append({"id":os.urandom(4).hex(),"name":item.get("name",""),"province":"未知","city":"未知","category":"其他","tags":[],"intro":"","detail":item.get("detail","")[:300]})

    # 保存到知识库
    kb_file = DATA_DIR / "knowledge_base.json"
    existing = json.load(open(kb_file, encoding="utf-8")) if kb_file.exists() else []
    existing.extend(classified)
    json.dump(existing, open(kb_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 清除景点介绍缓存，让用户查询时立即使用新知识库
    import shutil
    cache_dir = DATA_DIR / "attraction_cache"
    if cache_dir.exists(): shutil.rmtree(cache_dir); cache_dir.mkdir()

    # 同时更新广场数据
    try:
        plaza = json.load(open(DATA_DIR / "plaza_data.json", encoding="utf-8")) if (DATA_DIR/"plaza_data.json").exists() else {}
        for c in classified:
            prov = c.get("province", "其他")
            city = c.get("city", prov)
            if prov not in plaza: plaza[prov] = {"count":0,"cities":[]}
            found = False
            for ci in plaza[prov]["cities"]:
                if ci["name"] == city:
                    ci["count"] += 1
                    if not any(a["name"]==c["name"] for a in ci["attractions"]):
                        ci["attractions"].append({"name":c["name"],"count":1,"city":city})
                    found = True; break
            if not found:
                plaza[prov]["cities"].append({"name":city,"count":1,"attractions":[{"name":c["name"],"count":1,"city":city}]})
            plaza[prov]["count"] += 1
        json.dump(plaza, open(DATA_DIR/"plaza_data.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass

    return {"success": True, "count": len(classified)}

@router.delete("/knowledge/{kid}")
async def delete_knowledge(kid: str, username: str = Header("", alias="X-Username")):
    """删除知识库条目"""
    _check_admin(username)
    f = DATA_DIR / "knowledge_base.json"
    if not f.exists(): return {"success": True}
    items = json.load(open(f, encoding="utf-8"))
    items = [i for i in items if i.get("id") != kid]
    json.dump(items, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"success": True}

# ---- 文件上传知识库 ----
@router.post("/knowledge/upload")
async def upload_knowledge_file(file: UploadFile = File(...), username: str = Header("", alias="X-Username")):
    """上传PDF/DOCX/TXT/图片，AI解析并分类"""
    _check_admin(username)
    try:
        # 读取文件内容
        content = await file.read()
        fname = file.filename or "unknown"
        text = ""

        if fname.endswith('.txt'):
            text = content.decode('utf-8', errors='ignore')
        elif fname.endswith('.pdf'):
            try:
                import PyPDF2, io
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = '\n'.join(p.extract_text() or '' for p in reader.pages)
            except: text = f"[PDF文件: {fname}]"
        elif fname.endswith('.docx'):
            try:
                import zipfile, xml.etree.ElementTree as ET, io
                z = zipfile.ZipFile(io.BytesIO(content))
                xml_c = z.read('word/document.xml')
                root = ET.fromstring(xml_c)
                text = '\n'.join(''.join(t.text or '' for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')) for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
            except: text = f"[DOCX文件: {fname}]"
        elif fname.endswith(('.jpg','.jpeg','.png')):
            # 图片用OCR或直接记录
            text = f"[图片文件: {fname}]"

        if not text.strip(): return {"success": False, "message": "无法提取文本内容"}

        # AI解析分类（分段处理长文本）
        from ...services.llm_service import get_llm
        llm = get_llm()
        items = []
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for chunk in chunks[:5]:  # 最多5段
            prompt = f"""从以下文本中提取景点信息，返回JSON数组。每个景点格式：{{"name":"景点名","province":"省份","city":"城市","category":"类别(古镇水乡/风景名胜/主题乐园/博物馆/自然公园/现代地标/历史文化/动植物园)","tags":["标签"],"intro":"50字简介","detail":"详细描述"}}。只返回JSON数组。

文本内容：{chunk[:1200]}"""
            msgs = [{"role":"system","content":"你是旅游数据提取专家。只返回JSON数组。"},{"role":"user","content":prompt}]
            reply = llm.invoke(msgs).strip()
            try:
                if "```json" in reply: reply = reply.split("```json")[1].split("```")[0]
                elif "```" in reply: reply = reply.split("```")[1].split("```")[0]
                extracted = json.loads(reply)
                if isinstance(extracted, list): items.extend(extracted)
            except: pass

        if not items: return {"success": False, "message": "未识别到景点信息"}

        # 保存
        kb_file = DATA_DIR / "knowledge_base.json"
        existing = json.load(open(kb_file, encoding="utf-8")) if kb_file.exists() else []
        for item in items:
            item["id"] = os.urandom(4).hex()
            item["source"] = fname
        existing.extend(items)
        json.dump(existing, open(kb_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        # 同步广场
        try:
            plaza = json.load(open(DATA_DIR/"plaza_data.json", encoding="utf-8")) if (DATA_DIR/"plaza_data.json").exists() else {}
            for c in items:
                prov = c.get("province","其他"); city = c.get("city",prov)
                if prov not in plaza: plaza[prov] = {"count":0,"cities":[]}
                found = False
                for ci in plaza[prov]["cities"]:
                    if ci["name"]==city: ci["count"]+=1; ci["attractions"].append({"name":c["name"],"count":1,"city":city}); found=True; break
                if not found: plaza[prov]["cities"].append({"name":city,"count":1,"attractions":[{"name":c["name"],"count":1,"city":city}]})
                plaza[prov]["count"]+=1
            json.dump(plaza, open(DATA_DIR/"plaza_data.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
        except: pass

        return {"success": True, "count": len(items)}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ---- 平台统计 ----
# ---- FAQ 常见问答管理 ----
from ...services import faq_service

@router.get("/faq")
async def list_faq(category: str = "", username: str = Header("", alias="X-Username")):
    """获取 FAQ 列表"""
    _check_admin(username)
    return {"success": True, "data": faq_service.get_all_faqs(category),
            "categories": faq_service.get_faq_categories()}

@router.post("/faq")
async def create_faq(data: dict, username: str = Header("", alias="X-Username")):
    """创建 FAQ"""
    _check_admin(username)
    item = faq_service.create_faq(
        question=data.get("question", ""),
        answer=data.get("answer", ""),
        category=data.get("category", "通用"),
        tags=data.get("tags", [])
    )
    return {"success": True, "data": item}

@router.put("/faq/{faq_id}")
async def update_faq(faq_id: str, data: dict, username: str = Header("", alias="X-Username")):
    """更新 FAQ"""
    _check_admin(username)
    item = faq_service.update_faq(faq_id, **data)
    if not item: raise HTTPException(404, "FAQ不存在")
    return {"success": True, "data": item}

@router.delete("/faq/{faq_id}")
async def delete_faq(faq_id: str, username: str = Header("", alias="X-Username")):
    """删除 FAQ"""
    _check_admin(username)
    if not faq_service.delete_faq(faq_id): raise HTTPException(404, "FAQ不存在")
    return {"success": True}


# ---- 数据大屏 ----
@router.get("/dashboard")
async def dashboard_data(username: str = Header("", alias="X-Username")):
    """数据大屏实时运营指标"""
    _check_admin(username)
    from datetime import datetime, timedelta

    users = json.load(open(DATA_DIR/"users.json", encoding="utf-8")) if (DATA_DIR/"users.json").exists() else {}
    plaza = json.load(open(DATA_DIR/"plaza_data.json", encoding="utf-8")) if (DATA_DIR/"plaza_data.json").exists() else {}
    kb = json.load(open(DATA_DIR/"knowledge_base.json", encoding="utf-8")) if (DATA_DIR/"knowledge_base.json").exists() else []
    faqs = json.load(open(DATA_DIR/"faq_data.json", encoding="utf-8")) if (DATA_DIR/"faq_data.json").exists() else []

    # 基础统计
    trip_total = 0; chat_total = 0
    today = datetime.now().strftime("%Y-%m-%d")
    today_trips = 0; today_chats = 0

    for uname in users:
        tf = DATA_DIR / f"trips_{uname}.json"
        if tf.exists():
            udata = json.load(open(tf, encoding="utf-8"))
            trip_total += len(udata)
            today_trips += sum(1 for t in udata if t.get("created_at","").startswith(today))
        cf = DATA_DIR / f"conversations_{uname}.json"
        if cf.exists():
            cdata = json.load(open(cf, encoding="utf-8"))
            chat_total += len(cdata)
            for c in cdata:
                today_chats += sum(1 for m in c.get("messages",[]) if m.get("time","").startswith(today))

    # 本周统计
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_trips = 0; week_chats = 0
    for uname in users:
        tf = DATA_DIR / f"trips_{uname}.json"
        if tf.exists():
            for t in json.load(open(tf, encoding="utf-8")):
                ct = t.get("created_at","")
                if ct >= week_start.strftime("%Y-%m-%d"): week_trips += 1
        cf = DATA_DIR / f"conversations_{uname}.json"
        if cf.exists():
            for c in json.load(open(cf, encoding="utf-8")):
                for m in c.get("messages",[]):
                    if m.get("time","") >= week_start.strftime("%Y-%m-%d"): week_chats += 1

    # 热门景点 TOP10
    hot_attractions = sorted(
        [(pname,pinfo.get("count",0)) for pname, pinfo in plaza.items() if isinstance(pinfo,dict)],
        key=lambda x: x[1], reverse=True
    )[:10]

    # 热门问答（基于FAQ匹配和聊天关键词）
    hot_questions = []
    for u in users:
        cf = DATA_DIR / f"conversations_{uname}.json"
        if cf.exists():
            for c in json.load(open(cf, encoding="utf-8")):
                for m in c.get("messages",[]):
                    if m.get("role") == "user" and len(m.get("content","")) > 4:
                        hot_questions.append(m["content"][:60])

    # 取最近20条用户问题作为"热门问答"
    hot_questions = hot_questions[-20:]

    # 满意度趋势（基于聊天内容简单估算，真实场景需情感分析）
    # 这里用正面词占比估算
    positive_words = ['好','棒','赞','喜欢','推荐','不错','太美','很棒','满意','开心','谢谢','感谢']
    negative_words = ['差','不好','失望','太贵','坑','烂','后悔','不要']
    total_sentiment = 0; pos_count = 0; neg_count = 0
    for u in users:
        cf = DATA_DIR / f"conversations_{uname}.json"
        if cf.exists():
            for c in json.load(open(cf, encoding="utf-8")):
                for m in c.get("messages",[]):
                    if m.get("role") == "user":
                        txt = m.get("content","")
                        p = sum(1 for w in positive_words if w in txt)
                        n = sum(1 for w in negative_words if w in txt)
                        if p > n: pos_count += 1
                        elif n > p: neg_count += 1
                        total_sentiment += 1

    satisfaction_rate = round(pos_count / max(total_sentiment, 1) * 100, 1)

    # 活跃用户
    active_users = sum(1 for u in users.values() if u.get("login_count",0) > 0)

    return {"success": True, "data": {
        "user_count": len(users),
        "active_users": active_users,
        "trip_total": trip_total,
        "chat_total": chat_total,
        "today_trips": today_trips,
        "today_chats": today_chats,
        "week_trips": week_trips,
        "week_chats": week_chats,
        "knowledge_count": len(kb),
        "faq_count": len(faqs),
        "plaza_records": sum(v.get("count",0) for v in plaza.values() if isinstance(v,dict)),
        "hot_attractions": hot_attractions,
        "hot_questions": hot_questions,
        "satisfaction_rate": satisfaction_rate,
        "pos_count": pos_count,
        "neg_count": neg_count,
        "sentiment_data": [
            {"label": "好评", "value": pos_count, "color": "#52c41a"},
            {"label": "一般", "value": max(total_sentiment - pos_count - neg_count, 0), "color": "#faad14"},
            {"label": "差评", "value": neg_count, "color": "#ff4d4f"}
        ]
    }}


# ---- 情感分析 & 感受度报告 ----
from ...services import sentiment_service

@router.post("/sentiment/analyze")
async def trigger_sentiment_analysis(data: dict = None, username: str = Header("", alias="X-Username")):
    """触发情感分析，生成感受度报告"""
    _check_admin(username)
    days = (data or {}).get("days", 30)
    try:
        report = sentiment_service.analyze_sentiment(days)
        if "error" in report:
            return {"success": False, "message": report["error"]}
        return {"success": True, "data": report}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/sentiment/report")
async def get_sentiment_report(latest: bool = True, username: str = Header("", alias="X-Username")):
    """获取感受度报告"""
    _check_admin(username)
    if latest:
        report = sentiment_service.get_latest_report()
        if not report:
            return {"success": False, "message": "暂无报告，请先触发分析"}
        return {"success": True, "data": report}
    reports = sentiment_service.get_all_reports()
    return {"success": True, "data": reports, "count": len(reports)}


@router.get("/stats")
async def platform_stats(username: str = Header("", alias="X-Username")):
    """获取平台总览统计"""
    _check_admin(username)
    users = json.load(open(DATA_DIR/"users.json", encoding="utf-8")) if (DATA_DIR/"users.json").exists() else {}
    plaza = json.load(open(DATA_DIR/"plaza_data.json", encoding="utf-8")) if (DATA_DIR/"plaza_data.json").exists() else {}
    kb = json.load(open(DATA_DIR/"knowledge_base.json", encoding="utf-8")) if (DATA_DIR/"knowledge_base.json").exists() else []

    trip_total = 0
    for uname in users:
        f = DATA_DIR / f"trips_{uname}.json"
        if f.exists(): trip_total += len(json.load(open(f, encoding="utf-8")))

    return {"success": True, "data": {
        "user_count": len(users),
        "trip_count": trip_total,
        "plaza_records": sum(v.get("count",0) for v in plaza.values()),
        "knowledge_count": len(kb),
        "province_count": len([p for p in plaza if p not in ("其他",) and plaza[p].get("count",0)>0])
    }}
