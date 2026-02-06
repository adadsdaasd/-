"""
AI Services (DeepSeek)
=====================
集中管理与 LLM 交互的逻辑与常量，避免在各模块中重复定义。

原则：
- 不依赖 Streamlit（不直接 st.error/st.warning）
- 将错误信息以返回值形式交给 UI 层展示
"""

from __future__ import annotations

import json
import re
from typing import Optional, Tuple

from openai import OpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


SYSTEM_PROMPT_PROFILE = """你是一个人物画像分析专家和职业发展顾问。请从用户提供的自我介绍中提取关键信息，并给出发展建议。

要求：
1. 仔细分析文本，提取所有可用信息
2. 如果某项信息文本中没有提到，填写"未提及"
3. 必须返回有效的 JSON 格式，不要添加任何其他文字
4. 技能特长、性格特点等列表类字段，请提取多个关键词
5. 【重要】根据分析结果，给出有洞察力的"可发展方向"和"可发展优点"建议

返回格式（严格按此 JSON 结构）：
{
  "姓名": "提取的姓名",
  "联系方式": {
    "电话": "提取的电话",
    "邮箱": "提取的邮箱"
  },
  "教育背景": "提取的教育信息",
  "工作经历": ["经历1", "经历2"],
  "技能特长": ["技能1", "技能2", "技能3"],
  "性格特点": ["特点1", "特点2"],
  "个人优势": "总结的个人优势",
  "未来规划": "提取的未来规划或目标",
  "其他亮点": "其他值得注意的信息",
  "可发展方向": {
    "短期建议": "基于当前能力，1-2年内可以发展的方向",
    "中期建议": "3-5年的职业发展路径建议",
    "长期愿景": "基于潜力的长远发展方向"
  },
  "可发展优点": {
    "核心优势": "最值得深耕的1-2个核心优点",
    "潜力优点": "目前体现不明显但值得培养的优点",
    "发展建议": "如何将优点转化为竞争力的具体建议"
  }
}"""


def create_ai_client(api_key: str) -> OpenAI:
    """创建 DeepSeek(OpenAI SDK 兼容) 客户端"""
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def _strip_markdown_code_fence(text: str) -> str:
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
    return content.strip()


def analyze_text_with_ai(
    text: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 2500,
) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
    """
    分析自我介绍文本，提取结构化人物画像。

    Returns:
        (profile, raw_content, error)
        - profile: dict | None
        - raw_content: str | None（AI 原始返回，用于调试展示）
        - error: str | None（失败时错误信息）
    """
    client = create_ai_client(api_key)
    user_prompt = f"请分析以下自我介绍，提取人物画像信息并给出发展建议：\n\n{text}"

    content = None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PROFILE},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = (response.choices[0].message.content or "").strip()
        cleaned = _strip_markdown_code_fence(content)
        profile = json.loads(cleaned)
        return profile, content, None

    except json.JSONDecodeError as e:
        return None, content, f"AI 返回的格式无法解析: {str(e)}"
    except Exception as e:
        return None, content, f"AI 分析失败: {str(e)}"

