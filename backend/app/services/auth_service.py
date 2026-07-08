"""用户认证服务 - JSON 文件存储"""

import json, hashlib, os, random
from pathlib import Path
from typing import Optional
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
USER_FILE = DATA_DIR / "users.json"

# 中国风名字生成：诗意前缀 + 山河意象 + 后缀
NAME_PREFIX = [
    "清风","明月","行云","流水","远山","归雁","孤舟","闲鹤",
    "踏雪","寻梅","听雨","观澜","倚松","枕石","拂柳","逐日",
    "云游","四海","天涯","客行","行知","问道","乘兴","随意",
    "临风","沐光","拾光","逐梦","觅静","寄情","随心","自在",
    "晨曦","暮云","晴岚","烟雨","霜华","露凝","星垂","月涌",
]
NAME_SUFFIX = [
    "行者","旅人","居士","散人","闲人","墨客","归人","游侠",
    "过客","远客","故人","隐士","逸士","野老","山客","江客",
]


def _load_users() -> dict:
    return json.load(open(USER_FILE, encoding="utf-8")) if USER_FILE.exists() else {}


def _save_users(users: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(users, open(USER_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _hash_password(password: str, salt: str = "") -> tuple[str, str]:
    if not salt:
        salt = os.urandom(16).hex()
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return h, salt


def _generate_unique_name() -> str:
    """生成唯一的中国风行者名，保证全局不重复"""
    users = _load_users()
    existing_names = {u.get("name", "") for u in users.values()}
    # 计算还有多少可用组合
    total_combos = len(NAME_PREFIX) * len(NAME_SUFFIX)
    used_combos = [n for n in existing_names if any(n.startswith(p) for p in NAME_PREFIX)]
    if len(used_combos) < total_combos * 0.8:
        # 随机尝试，最多200次
        for _ in range(200):
            name = random.choice(NAME_PREFIX) + random.choice(NAME_SUFFIX)
            if name not in existing_names:
                existing_names.add(name)  # 内存中也记录，防止并发重复
                return name
    # 组合基本用完，前缀+随机数字
    for _ in range(500):
        name = random.choice(NAME_PREFIX) + str(random.randint(1, 999))
        if name not in existing_names:
            existing_names.add(name)
            return name
    # 极端兜底
    import uuid
    return "行者" + uuid.uuid4().hex[:6]


def register_user(username: str, password: str) -> dict:
    """注册，自动生成唯一中文昵称"""
    users = _load_users()
    if len(username) < 2:
        return {"error": "用户名至少2位"}
    if len(password) < 4:
        return {"error": "密码至少4位"}
    # 检查用户名是否已存在
    if username in users:
        return None
    # 也检查是否有同名email
    for u in users.values():
        if u.get("email") == username or u.get("username") == username:
            return None

    name = _generate_unique_name()
    pw_hash, salt = _hash_password(password)
    user = {
        "username": username,
        "name": name,
        "password_hash": pw_hash,
        "salt": salt,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "login_count": 0,
        "last_login": ""
    }
    users[username] = user
    _save_users(users)
    return {"username": username, "name": name, "created_at": user["created_at"]}


def login_user(username: str, password: str) -> Optional[str]:
    """验证登录，成功返回 token"""
    users = _load_users()
    user = users.get(username)
    if not user:
        # 尝试email匹配
        for u in users.values():
            if u.get("email") == username:
                user = u
                break
    if not user:
        return None
    if user.get("disabled"):
        return "__disabled__"

    pw_hash, _ = _hash_password(password, user["salt"])
    if pw_hash != user["password_hash"]:
        return None

    token = os.urandom(32).hex()
    user["token"] = token
    user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user["login_count"] = user.get("login_count", 0) + 1
    _save_users(users)
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    users = _load_users()
    for u in users.values():
        if u.get("token") == token:
            return {
                "username": u.get("username", ""),
                "name": u.get("name", u.get("username", "")),
                "created_at": u.get("created_at", ""),
                "last_login": u.get("last_login", ""),
                "login_count": u.get("login_count", 0)
            }
    return None


def update_user_name(username: str, name: str) -> bool:
    """修改用户显示名"""
    users = _load_users()
    if username in users:
        users[username]["name"] = name[:20]
        _save_users(users)
        return True
    return False


def logout_user(token: str) -> None:
    users = _load_users()
    for u in users.values():
        if u.get("token") == token:
            u.pop("token", None)
            _save_users(users)
            return
