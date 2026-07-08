#!/usr/bin/env python3
"""Plaza 接口轻量回归检查脚本"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.getenv("PLAZA_BASE_URL", "http://127.0.0.1:8000")
USERNAME = os.getenv("PLAZA_TEST_USERNAME", "plaza-regression")
TIMEOUT = 10

PROFILE_PAYLOAD = {
    "gender": "女",
    "age": "29",
    "motivation": "放松",
    "habits": "周末短途",
    "companion": "朋友",
    "preference": "自然风景",
}


def request_json(method: str, path: str, data: dict | None = None, headers: dict | None = None) -> dict:
    payload = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if data is not None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=payload,
        headers=request_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {path} 返回 HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AssertionError(f"无法连接后端 {BASE_URL}: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{method} {path} 未返回合法 JSON: {body}") from exc


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    profile_headers = {"X-Username": USERNAME}

    provinces = request_json("GET", "/api/plaza/provinces")
    assert_true(provinces.get("success") is True, "provinces.success 应为 true")
    assert_true(isinstance(provinces.get("data"), list), "provinces.data 应为列表")
    assert_true(len(provinces["data"]) > 0, "provinces.data 不应为空")
    assert_true("name" in provinces["data"][0], "provinces 首项应包含 name")
    print("✅ /api/plaza/provinces")

    attractions = request_json(
        "GET",
        "/api/plaza/attractions?q=" + urllib.parse.quote("西湖"),
    )
    assert_true(attractions.get("success") is True, "attractions.success 应为 true")
    assert_true(isinstance(attractions.get("data"), list), "attractions.data 应为列表")
    assert_true(any("西湖" in item.get("name", "") for item in attractions["data"]), "attractions 应能搜索到西湖相关景点")
    print("✅ /api/plaza/attractions?q=西湖")

    attraction_detail = request_json(
        "GET",
        "/api/plaza/attraction/" + urllib.parse.quote("西湖") + "?city=" + urllib.parse.quote("杭州"),
    )
    assert_true(attraction_detail.get("success") is True, "attraction detail.success 应为 true")
    detail_data = attraction_detail.get("data") or {}
    assert_true(detail_data.get("name") == "西湖", f"attraction detail.name 应为西湖，实际为 {detail_data.get('name')}")
    assert_true(bool(detail_data.get("intro")), "attraction detail.intro 不应为空")
    assert_true("image" in detail_data, "attraction detail 应包含 image 字段")
    assert_true(isinstance(detail_data.get("image"), str), "attraction detail.image 应为字符串")
    print("✅ /api/plaza/attraction/西湖?city=杭州")

    save_profile = request_json("POST", "/api/plaza/profile", PROFILE_PAYLOAD, profile_headers)
    assert_true(save_profile.get("success") is True, "profile 保存应成功")
    print("✅ POST /api/plaza/profile")

    profile = request_json("GET", "/api/plaza/profile", headers=profile_headers)
    assert_true(profile.get("success") is True, "profile 获取应成功")
    data = profile.get("data") or {}
    for key, expected in PROFILE_PAYLOAD.items():
        assert_true(data.get(key) == expected, f"profile.{key} 应为 {expected}，实际为 {data.get(key)}")
    assert_true(data.get("filled") is True, "profile.filled 应为 true")
    print("✅ GET /api/plaza/profile")

    insights = request_json("GET", "/api/plaza/insights")
    assert_true("success" in insights, "insights 返回应包含 success 字段")
    if insights.get("success") is True:
        assert_true(isinstance(insights.get("data"), dict), "insights.data 应为对象")
    else:
        message = insights.get("message", "")
        assert_true("SCENIC_INSIGHTS_EXCEL_PATH" in message or "景区洞察数据文件" in message, "未配置洞察文件时应返回可解释提示")
    print("✅ /api/plaza/insights")

    print("\n🎉 Plaza 回归检查通过")
    print(f"基准地址: {BASE_URL}")
    print(f"测试用户: {USERNAME}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"❌ Plaza 回归检查失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
