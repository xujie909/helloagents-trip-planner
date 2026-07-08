"""FAQ 常见问答服务 — TF-IDF 向量化 + 余弦相似度匹配"""

import json
import os
import re
from pathlib import Path
from typing import Optional
from ..models.schemas import FAQItem, FAQMatchResult

DATA_DIR = Path(__file__).parent.parent / "data"
FAQ_FILE = DATA_DIR / "faq_data.json"


def _load_faqs() -> list:
    """加载 FAQ 数据"""
    if not FAQ_FILE.exists():
        return []
    with open(FAQ_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_faqs(items: list):
    """保存 FAQ 数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _tokenize(text: str) -> list[str]:
    """简单中文分词 (基于字级 bigram)"""
    # 清理标点
    text = re.sub(r'[^一-鿿\w]', '', text)
    # 字级 unigram + bigram
    tokens = list(text)
    for i in range(len(text) - 1):
        tokens.append(text[i:i + 2])
    return tokens


def _tf_idf_similarity(query: str, document: str, corpus: list[str]) -> float:
    """
    计算 query 和 document 的 TF-IDF 余弦相似度
    corpus 用于计算 IDF
    """
    # 构建词汇表
    all_docs = [document] + corpus
    tokenized = [_tokenize(d) for d in all_docs]
    query_tokens = _tokenize(query)

    # 计算 IDF
    N = len(all_docs)
    vocab = {}
    for tokens in tokenized:
        for t in set(tokens):
            vocab[t] = vocab.get(t, 0) + 1

    # TF for query
    q_tf = {}
    for t in query_tokens:
        q_tf[t] = q_tf.get(t, 0) + 1

    # TF for document
    d_tf = {}
    for t in tokenized[0]:
        d_tf[t] = d_tf.get(t, 0) + 1

    # 计算 TF-IDF 向量点积
    dot_product = 0.0
    q_norm = 0.0
    d_norm = 0.0

    all_terms = set(q_tf.keys()) | set(d_tf.keys())
    for term in all_terms:
        idf = 1.0 / (1.0 + vocab.get(term, 1))
        q_val = q_tf.get(term, 0) * idf
        d_val = d_tf.get(term, 0) * idf
        dot_product += q_val * d_val
        q_norm += q_val ** 2
        d_norm += d_val ** 2

    if q_norm == 0 or d_norm == 0:
        return 0.0
    return dot_product / ((q_norm ** 0.5) * (d_norm ** 0.5))


def search_faq(query: str, threshold: float = 0.75) -> FAQMatchResult:
    """
    搜索 FAQ 库，返回最佳匹配

    Args:
        query: 用户问题
        threshold: 匹配阈值 (0-1)，高于此值视为匹配成功

    Returns:
        FAQMatchResult
    """
    faqs = _load_faqs()
    if not faqs:
        return FAQMatchResult(matched=False, score=0.0)

    # 合并 question + tags 作为文档内容
    documents = [f"{f['question']} {' '.join(f.get('tags', []))} {f.get('category', '')}" for f in faqs]

    best_score = 0.0
    best_item = None

    for i, faq in enumerate(faqs):
        score = _tf_idf_similarity(query, documents[i], documents)
        if score > best_score:
            best_score = score
            best_item = FAQItem(**faq)

    if best_score >= threshold and best_item:
        return FAQMatchResult(matched=True, item=best_item, score=best_score)

    return FAQMatchResult(matched=False, score=best_score)


def get_all_faqs(category: str = "") -> list:
    """获取所有 FAQ"""
    faqs = _load_faqs()
    if category:
        faqs = [f for f in faqs if f.get("category") == category]
    return sorted(faqs, key=lambda x: x.get("created_at", ""), reverse=True)


def create_faq(question: str, answer: str, category: str = "通用", tags: list = None) -> dict:
    """创建 FAQ"""
    import os as _os
    from datetime import datetime

    faqs = _load_faqs()
    item = {
        "id": _os.urandom(4).hex(),
        "question": question,
        "answer": answer,
        "category": category,
        "tags": tags or [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    faqs.append(item)
    _save_faqs(faqs)
    return item


def update_faq(faq_id: str, question: str = None, answer: str = None,
               category: str = None, tags: list = None) -> Optional[dict]:
    """更新 FAQ"""
    faqs = _load_faqs()
    for f in faqs:
        if f["id"] == faq_id:
            if question is not None:
                f["question"] = question
            if answer is not None:
                f["answer"] = answer
            if category is not None:
                f["category"] = category
            if tags is not None:
                f["tags"] = tags
            _save_faqs(faqs)
            return f
    return None


def delete_faq(faq_id: str) -> bool:
    """删除 FAQ"""
    faqs = _load_faqs()
    new_faqs = [f for f in faqs if f["id"] != faq_id]
    if len(new_faqs) == len(faqs):
        return False
    _save_faqs(new_faqs)
    return True


def get_faq_categories() -> list:
    """获取所有 FAQ 分类"""
    faqs = _load_faqs()
    return sorted(set(f.get("category", "通用") for f in faqs))
