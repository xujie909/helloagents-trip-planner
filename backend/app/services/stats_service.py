"""用户统计服务"""

import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"


def get_user_stats(username: str) -> dict:
    """获取用户统计数据"""
    # 行程记录数
    trip_file = DATA_DIR / f"trips_{username}.json"
    trip_count = 0
    note_count = 0
    city_set = set()
    if trip_file.exists():
        with open(trip_file, "r", encoding="utf-8") as f:
            trips = json.load(f)
        trip_count = len(trips)
        for t in trips:
            if t.get("notes"):
                note_count += 1
            city_set.add(t.get("city", ""))

    # 对话次数
    chat_file = DATA_DIR / f"chats_{username}.json"
    chat_count = 0
    if chat_file.exists():
        with open(chat_file, "r", encoding="utf-8") as f:
            chats = json.load(f)
        chat_count = len(chats)

    # 全平台用户数
    all_users = _get_all_users()
    total_users = max(len(all_users), 1)

    # 计算超过百分比
    other_trip_counts = []
    for u in all_users:
        if u != username:
            tf = DATA_DIR / f"trips_{u}.json"
            if tf.exists():
                with open(tf, "r", encoding="utf-8") as f:
                    other_trip_counts.append(len(json.load(f)))
            else:
                other_trip_counts.append(0)

    better_than = 0
    if other_trip_counts:
        better_than = sum(1 for c in other_trip_counts if c < trip_count)
        better_than = int(better_than / len(other_trip_counts) * 100)

    return {
        "chat_count": chat_count,
        "trip_count": trip_count,
        "note_count": note_count,
        "city_count": len(city_set),
        "total_users": total_users,
        "better_than": better_than
    }


def increment_chat(username: str) -> None:
    """记录一次对话"""
    chat_file = DATA_DIR / f"chats_{username}.json"
    chats = []
    if chat_file.exists():
        with open(chat_file, "r", encoding="utf-8") as f:
            chats = json.load(f)
    chats.append({"time": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(chat_file, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False)


def _get_all_users() -> list:
    """获取所有用户列表"""
    user_file = DATA_DIR / "users.json"
    if not user_file.exists():
        return []
    with open(user_file, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())
