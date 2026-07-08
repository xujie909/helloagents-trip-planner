"""对话会话存储 - JSON 文件，按用户隔离"""

import json, os
from pathlib import Path
from datetime import datetime
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"


def _file(username: str) -> Path:
    return DATA_DIR / f"conversations_{username}.json"


def _load(username: str) -> list:
    f = _file(username)
    return json.load(open(f, encoding="utf-8")) if f.exists() else []


def _save(username: str, data: list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(_file(username), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def create_conversation(username: str, conv_id: str = "") -> dict:
    convs = _load(username)
    cid = conv_id if conv_id else datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex()
    # 如果指定了 conv_id 且已存在，直接返回已有的
    for existing in convs:
        if existing["id"] == cid:
            return existing
    c = {
        "id": cid,
        "title": "新对话",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    convs.insert(0, c)
    _save(username, convs)
    return c


def list_conversations(username: str) -> list:
    convs = _load(username)
    # 过滤数字人对话（dh_前缀），与旅行顾问分开存储
    convs = [c for c in convs if not c["id"].startswith("dh_")]
    return [{"id": c["id"], "title": c["title"], "created_at": c["created_at"], "updated_at": c["updated_at"], "msg_count": len(c.get("messages", []))} for c in convs]


def get_conversation(username: str, conv_id: str) -> Optional[dict]:
    for c in _load(username):
        if c["id"] == conv_id:
            return c
    return None


def add_message(username: str, conv_id: str, role: str, content: str) -> Optional[dict]:
    convs = _load(username)
    for c in convs:
        if c["id"] == conv_id:
            c["messages"].append({"role": role, "content": content, "time": datetime.now().strftime("%H:%M")})
            c["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 自动生成标题：用第一条用户消息截取
            if c["title"] == "新对话" and role == "user":
                c["title"] = content[:20] + ("..." if len(content) > 20 else "")
            _save(username, convs)
            return c
    return None


def update_title(username: str, conv_id: str, title: str) -> bool:
    convs = _load(username)
    for c in convs:
        if c["id"] == conv_id:
            c["title"] = title[:30]
            _save(username, convs)
            return True
    return False


def delete_conversation(username: str, conv_id: str) -> bool:
    convs = _load(username)
    new = [c for c in convs if c["id"] != conv_id]
    if len(new) < len(convs):
        _save(username, new)
        return True
    return False
