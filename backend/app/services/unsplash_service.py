"""Unsplash图片服务 — 带缓存、限流保护和中→英景点翻译"""

import hashlib
import requests
import time
import re
from typing import List, Optional, Dict
from ..config import get_settings


# ===== 常见中国景点中→英翻译表 =====
# Unsplash对纯中文查询效果很差, 必须翻译成英文
_ATTRACTION_EN_MAP: Dict[str, str] = {
    # 北京
    "故宫": "Forbidden City",
    "天安门": "Tiananmen Square",
    "天坛": "Temple of Heaven",
    "颐和园": "Summer Palace",
    "圆明园": "Old Summer Palace",
    "八达岭长城": "Great Wall Badaling",
    "长城": "Great Wall of China",
    "鸟巢": "Bird Nest Stadium",
    "水立方": "Water Cube",
    "北海公园": "Beihai Park",
    "景山公园": "Jingshan Park",
    "雍和宫": "Yonghe Temple Lama Temple",
    "恭王府": "Prince Gong Mansion",
    "南锣鼓巷": "Nanluoguxiang Hutong",
    "798艺术区": "798 Art District",
    "三里屯": "Sanlitun Beijing",
    "王府井": "Wangfujing Street",
    "什刹海": "Shichahai Lake",
    "国家博物馆": "National Museum of China",
    "首都博物馆": "Capital Museum",
    "北京动物园": "Beijing Zoo",
    "香山": "Fragrant Hills Beijing",
    "清华大学": "Tsinghua University",
    "北京大学": "Peking University",
    # 上海
    "外滩": "The Bund Shanghai",
    "东方明珠": "Oriental Pearl Tower",
    "豫园": "Yuyuan Garden Shanghai",
    "城隍庙": "City God Temple Shanghai",
    "南京路": "Nanjing Road Shanghai",
    "迪士尼": "Shanghai Disneyland",
    "上海博物馆": "Shanghai Museum",
    "陆家嘴": "Lujiazui Pudong Shanghai",
    "田子坊": "Tianzifang Shanghai",
    # 杭州
    "西湖": "West Lake Hangzhou",
    "灵隐寺": "Lingyin Temple Hangzhou",
    "雷峰塔": "Leifeng Pagoda",
    # 西安
    "兵马俑": "Terracotta Warriors",
    "大雁塔": "Giant Wild Goose Pagoda",
    "城墙": "Xi'an City Wall",
    "钟楼": "Xi'an Bell Tower",
    # 成都
    "宽窄巷子": "Kuanzhai Alley Chengdu",
    "锦里": "Jinli Ancient Street",
    "大熊猫基地": "Chengdu Panda Base",
    "武侯祠": "Wuhou Shrine",
    "都江堰": "Dujiangyan",
    # 广州
    "广州塔": "Canton Tower",
    "白云山": "Baiyun Mountain Guangzhou",
    "陈家祠": "Chen Clan Academy",
    # 深圳
    "世界之窗": "Window of the World Shenzhen",
    "欢乐谷": "Happy Valley Shenzhen",
    # 南京
    "中山陵": "Sun Yat-sen Mausoleum",
    "夫子庙": "Confucius Temple Nanjing",
    # 重庆
    "洪崖洞": "Hongyadong Chongqing",
    "磁器口": "Ciqikou Chongqing",
    # 武汉
    "黄鹤楼": "Yellow Crane Tower",
    # 苏州
    "拙政园": "Humble Administrator Garden",
    "虎丘": "Tiger Hill Suzhou",
    # 桂林
    "漓江": "Li River Guilin",
    "阳朔": "Yangshuo Guilin",
}


class UnsplashService:
    """Unsplash图片服务类 (每小时50次免费请求, 必须精打细算)"""

    def __init__(self):
        """初始化服务"""
        settings = get_settings()
        self.access_key = settings.unsplash_access_key
        self.base_url = "https://api.unsplash.com"
        # 查询缓存: key=query字符串, value=(时间戳, 结果列表)
        self._cache: Dict[str, tuple[float, List[dict]]] = {}
        self._cache_ttl = 3600  # 缓存1小时 (和API限流窗口一致)
        self._rate_limit_hits = 0

    def _is_rate_limited(self) -> bool:
        """检查是否很可能已被限流"""
        return self._rate_limit_hits >= 2

    def search_photos(self, query: str, per_page: int = 5) -> List[dict]:
        """
        搜索图片 (带缓存)

        Args:
            query: 搜索关键词
            per_page: 每页数量

        Returns:
            图片列表
        """
        if self._is_rate_limited():
            print(f"  ⚡ 已触发限流, 使用空结果")
            return []

        # 检查缓存
        cache_key = f"{query}|{per_page}"
        if cache_key in self._cache:
            ts, results = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                print(f"  [cache]缓存命中: '{query}' ({len(results)}张)")
                return results

        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key
            }

            response = requests.get(url, params=params, timeout=10)

            # 检测限流
            if response.status_code == 403:
                self._rate_limit_hits += 1
                print(f"  [rate-limit] Unsplash 403 第{self._rate_limit_hits}次, 切换到缓存/兜底模式")
                return []
            if response.status_code == 429:
                self._rate_limit_hits = 999  # 标记为完全限流
                print(f"  [rate-limit] Unsplash 429")
                return []

            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            # 提取图片URL
            photos = []
            for photo in results:
                photos.append({
                    "id": photo.get("id"),
                    "url": photo.get("urls", {}).get("regular"),
                    "thumb": photo.get("urls", {}).get("thumb"),
                    "description": photo.get("description") or photo.get("alt_description"),
                    "photographer": photo.get("user", {}).get("name")
                })

            # 写入缓存
            self._cache[cache_key] = (time.time(), photos)
            return photos

        except Exception as e:
            print(f"[ERROR] Unsplash: {str(e)}")
            return []

    def get_photo_url(self, query: str, pick_index: int = 0) -> Optional[str]:
        """
        从缓存/API获取单张图片URL

        Args:
            query: 搜索关键词
            pick_index: 取第几张结果

        Returns:
            图片URL
        """
        per_page = max(pick_index + 1, 5)  # 一次取5张, 最大化利用率
        photos = self.search_photos(query, per_page=per_page)
        if not photos:
            return None
        idx = min(pick_index, len(photos) - 1)
        return photos[idx].get("url")

    def _translate_attraction(self, name: str) -> str:
        """将中文景点名翻译为英文 (未收录的景点用拼音/原文)"""
        # 精确匹配
        if name in _ATTRACTION_EN_MAP:
            return _ATTRACTION_EN_MAP[name]
        # 模糊匹配: 去掉"公园", "景区"等通用后缀再试
        for suffix in ["公园", "景区", "风景区", "名胜区", "博物馆", "寺", "庙", "塔", "山", "湖", "河", "园", "林", "宫", "殿", "楼", "阁"]:
            if name.endswith(suffix) and len(name) > len(suffix):
                base = name[:-len(suffix)]
                if base in _ATTRACTION_EN_MAP:
                    return _ATTRACTION_EN_MAP[base]
        return name  # 未收录, 保持原文

    def get_photo_url_multi_strategy(self, name: str, city: str = "", category: str = "") -> Optional[str]:
        """
        精简多策略搜索 (每次景点最多3次API调用)
        自动中→英翻译, 因为Unsplash对纯中文查询效果极差

        策略:
          1. "{英文名} {city} China" per_page=5   (翻译后精准搜索)
          2. "{city} landmark China" per_page=5    (同城景点兜底)
          3. "{city} travel China" per_page=5      (城市兜底, 保证同城)

        Args:
            name: 景点名称
            city: 城市名
            category: 景点类别

        Returns:
            图片URL
        """
        # 翻译景点名
        en_name = self._translate_attraction(name.strip())
        combined_results: List[dict] = []
        self._rate_limit_hits = 0

        # ===== 调用1: 英文精准搜索 =====
        if city:
            query1 = f"{en_name} {city} China"
            print(f"  [search] Strategy 1: '{query1}'")
            results = self.search_photos(query1, per_page=5)
            if results:
                combined_results.extend(results)
                print(f"  [OK] Strategy 1: {len(results)}张")
            else:
                print(f"  [miss] Strategy 1")

        # ===== 调用2: 同城景点兜底 =====
        if not combined_results and city:
            query2 = f"{city} landmark China"
            print(f"  [search] Strategy 2: '{query2}'")
            results = self.search_photos(query2, per_page=5)
            if results:
                combined_results.extend(results)
                print(f"  [OK] Strategy 2: {len(results)}张")
            else:
                print(f"  [miss] Strategy 2")

        # ===== 调用3: 城市兜底 (最后手段, 保证同城) =====
        if not combined_results:
            query3 = f"{city or en_name} travel China"
            print(f"  [search] Strategy 3(fallback): '{query3}'")
            results = self.search_photos(query3, per_page=5)
            if results:
                combined_results.extend(results)
                print(f"  [OK] Strategy 3(fallback): {len(results)}张")
            else:
                print(f"  [miss] Strategy 3")

        # 从合并结果中选一张 (用原中文名hash确保不同景点选不同图)
        if not combined_results:
            print(f"  [FAIL] All strategies failed: {name}")
            return None

        stable_key = f"{name.strip()}|{city.strip()}|{category.strip()}"
        stable_hash = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
        pick = int(stable_hash[:12], 16) % len(combined_results)
        chosen = combined_results[pick]
        print(f"  [select]第{pick+1}/{len(combined_results)}张: {chosen['description'] or chosen['id']}")
        return chosen.get("url")

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        print("[Unsplash] Cache cleared")


# 全局服务实例
_unsplash_service = None


def get_unsplash_service() -> UnsplashService:
    """获取Unsplash服务实例(单例模式)"""
    global _unsplash_service

    if _unsplash_service is None:
        _unsplash_service = UnsplashService()

    return _unsplash_service
