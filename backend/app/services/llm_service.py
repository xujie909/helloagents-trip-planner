"""LLM服务模块"""

import base64
import httpx
from hello_agents import HelloAgentsLLM
from ..config import get_settings

# 全局LLM实例
_llm_instance = None
_qwen_llm_instance = None


def get_llm() -> HelloAgentsLLM:
    """
    获取LLM实例(单例模式) — DeepSeek, 文本任务

    Returns:
        HelloAgentsLLM实例
    """
    global _llm_instance

    if _llm_instance is None:
        settings = get_settings()
        # 显式传入主模型配置，避免业务层继续依赖零散环境变量
        _llm_instance = HelloAgentsLLM(
            model=settings.get_primary_llm_model(),
            api_key=settings.get_primary_llm_api_key(),
            base_url=settings.get_primary_llm_base_url(),
        )

        print(f"[LLM] Service initialized: provider={_llm_instance.provider} model={_llm_instance.model}")

    return _llm_instance


def get_qwen_llm() -> HelloAgentsLLM:
    """
    获取Qwen-VL多模态LLM实例(单例模式)
    用于图片理解和视觉问答任务

    Returns:
        HelloAgentsLLM实例 (配置为Qwen-VL)
    """
    global _qwen_llm_instance

    if _qwen_llm_instance is None:
        settings = get_settings()

        _qwen_llm_instance = HelloAgentsLLM(
            model=settings.qwen_model_id,
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
            provider="qwen",
        )

        print(f"[LLM] Qwen-VL service initialized: model={settings.qwen_model_id}")

    return _qwen_llm_instance


def chat_with_vision(image_base64: str, prompt: str, system_prompt: str = "") -> str:
    """
    使用Qwen-VL进行图片+文本多模态问答

    Args:
        image_base64: 图片的base64编码 (不含data:image前缀)
        prompt: 用户问题
        system_prompt: 系统提示词（可选）

    Returns:
        Qwen-VL的文本回答
    """
    settings = get_settings()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # 构建多模态消息：包含图片和文本
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            },
            {
                "type": "text",
                "text": prompt
            }
        ]
    })

    # 直接调用Qwen API (OpenAI兼容接口)
    headers = {
        "Authorization": f"Bearer {settings.qwen_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.qwen_model_id,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.7
    }

    try:
        resp = httpx.post(
            f"{settings.qwen_base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60.0
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"Qwen-VL API error: {resp.status_code} - {resp.text[:200]}")
            # 回退到文本LLM
            text_llm = get_llm()
            return text_llm.invoke([
                {"role": "user", "content": f"[用户上传了一张图片，但多模态模型暂时不可用。请基于文本描述回答]\n\n用户问题：{prompt}"}
            ]).strip()
    except Exception as e:
        print(f"Qwen-VL调用异常: {e}")
        # 回退到文本LLM
        text_llm = get_llm()
        return text_llm.invoke([
            {"role": "user", "content": f"[用户上传了一张图片，但多模态模型暂时不可用。请基于文本描述回答]\n\n用户问题：{prompt}"}
        ]).strip()


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance, _qwen_llm_instance
    _llm_instance = None
    _qwen_llm_instance = None

