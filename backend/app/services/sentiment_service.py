"""游客情感分析服务 — 基于 LLM 的情感分类 + 关注点提取 + 报告生成"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from ..services.llm_service import get_llm

DATA_DIR = Path(__file__).parent.parent / "data"
REPORT_FILE = DATA_DIR / "sentiment_reports.json"


def _load_all_chat_messages() -> list[dict]:
    """加载所有用户的聊天消息"""
    all_msgs = []
    if not DATA_DIR.exists():
        return all_msgs

    for f in DATA_DIR.glob("conversations_*.json"):
        try:
            username = f.stem.replace("conversations_", "")
            conversations = json.load(open(f, encoding="utf-8"))
            for conv in conversations:
                conv_id = conv.get("id", "")
                for msg in conv.get("messages", []):
                    if msg.get("role") == "user" and msg.get("content"):
                        all_msgs.append({
                            "username": username,
                            "conv_id": conv_id,
                            "content": msg["content"],
                            "time": msg.get("time", ""),
                            "date": msg.get("time", "")[:10] if msg.get("time") else ""
                        })
        except Exception:
            pass

    return all_msgs


def _extract_topics_with_llm(messages: list[str]) -> dict:
    """使用 LLM 提取关注点话题"""
    if not messages:
        return {"topics": [], "suggestions": ""}

    llm = get_llm()

    # 合并消息（最多取 50 条，每条截取 100 字）
    sample = [m[:100] for m in messages[:50]]
    combined = "\n".join(f"- {s}" for s in sample)

    prompt = f"""你是一位旅游行业数据分析师。请分析以下游客的聊天消息，提取：

1. **关注点 TOP8**：游客最常问到的主题（如景点特色、交通、住宿、美食、票价、排队时间、历史文化等），按频率从高到低排列
2. **情感倾向**：正面/中性/负面的大致比例
3. **服务改进建议**：基于游客反馈，给出 3-5 条具体的服务优化建议

请返回 JSON 格式（只返回 JSON，不要其他内容）：
{{{{
  "topics": [{{"name":"主题名","count":数字,"sentiment":"正面/中性/负面"}}, ...],
  "sentiment": {{"positive": 数字,"neutral": 数字,"negative": 数字}},
  "suggestions": ["建议1", "建议2", ...]
}}}}

聊天消息样本：
{combined[:3000]}"""

    try:
        msgs = [{"role": "system", "content": "你是一位旅游行业数据分析师。只返回 JSON。"},
                {"role": "user", "content": prompt}]
        reply = llm.invoke(msgs).strip()

        # 提取 JSON
        if "```json" in reply:
            reply = reply.split("```json")[1].split("```")[0]
        elif "```" in reply:
            reply = reply.split("```")[1].split("```")[0]

        return json.loads(reply)
    except Exception as e:
        print(f"LLM 情感分析失败: {e}")
        return {
            "topics": [],
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
            "suggestions": ["数据不足，无法生成建议"]
        }


def analyze_sentiment(days: int = 30) -> dict:
    """
    运行情感分析，生成报告

    Args:
        days: 分析最近 N 天的数据

    Returns:
        分析报告 dict
    """
    all_msgs = _load_all_chat_messages()
    if not all_msgs:
        return {"error": "没有聊天数据可供分析"}

    # 筛选最近 N 天
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [m for m in all_msgs if m.get("date", "") >= cutoff]
    if not recent:
        return {"error": f"最近 {days} 天没有聊天数据"}

    # 基础统计
    unique_users = len(set(m["username"] for m in recent))
    total_messages = len(recent)
    daily_counts = {}
    for m in recent:
        d = m.get("date", "")
        daily_counts[d] = daily_counts.get(d, 0) + 1

    # 关键词情感快速分析
    positive_words = ['好', '棒', '赞', '喜欢', '推荐', '不错', '太美', '很棒', '满意', '开心', '谢谢', '感谢', '太好了', '非常', '完美']
    negative_words = ['差', '不好', '失望', '太贵', '坑', '烂', '后悔', '不要', '差评', '糟糕', '无聊']

    pos_count = sum(1 for m in recent for w in positive_words if w in m["content"])
    neg_count = sum(1 for m in recent for w in negative_words if w in m["content"])
    neutral_count = total_messages - pos_count - neg_count

    # LLM 深度分析（对最近消息采样）
    sample_messages = [m["content"] for m in recent[-50:]]
    llm_analysis = _extract_topics_with_llm(sample_messages)

    # 按天统计情感趋势
    trend = []
    for d in sorted(daily_counts.keys())[-14:]:  # 最近 14 天
        day_msgs = [m for m in recent if m.get("date") == d]
        day_pos = sum(1 for m in day_msgs for w in positive_words if w in m["content"])
        day_neg = sum(1 for m in day_msgs for w in negative_words if w in m["content"])
        day_neu = len(day_msgs) - day_pos - day_neg
        trend.append({
            "date": d,
            "total": len(day_msgs),
            "positive": day_pos,
            "neutral": max(day_neu, 0),
            "negative": day_neg
        })

    # 生成报告
    report = {
        "id": os.urandom(4).hex(),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period": f"最近 {days} 天",
        "summary": {
            "total_messages": total_messages,
            "unique_users": unique_users,
            "analyzed_days": len(daily_counts)
        },
        "sentiment_overview": {
            "positive": pos_count,
            "neutral": max(neutral_count, 0),
            "negative": neg_count,
            "positive_rate": round(pos_count / max(total_messages, 1) * 100, 1)
        },
        "topics": llm_analysis.get("topics", []),
        "llm_sentiment": llm_analysis.get("sentiment", {}),
        "suggestions": llm_analysis.get("suggestions", []),
        "daily_trend": trend
    }

    # 保存报告
    _save_report(report)

    return report


def get_latest_report() -> Optional[dict]:
    """获取最近一次分析报告"""
    reports = _load_reports()
    if reports:
        return reports[-1]  # 最新
    return None


def get_all_reports() -> list:
    """获取所有历史报告"""
    return _load_reports()


def _load_reports() -> list:
    """加载历史报告"""
    if not REPORT_FILE.exists():
        return []
    with open(REPORT_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_report(report: dict):
    """保存报告"""
    os.makedirs(DATA_DIR, exist_ok=True)
    reports = _load_reports()
    reports.append(report)
    # 最多保留 20 份
    if len(reports) > 20:
        reports = reports[-20:]
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
