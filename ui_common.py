"""
UI Common Components
===================
放置通用 UI 组件：空状态提示、导出按钮等。
"""

from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd
import streamlit as st


def render_export_buttons(saved_data: Dict[str, Any]):
    """渲染导出按钮（JSON/CSV）"""
    st.markdown("---")
    st.subheader("📤 导出数据")
    col1, col2 = st.columns(2)

    with col1:
        json_str = json.dumps(saved_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 下载 JSON",
            data=json_str,
            file_name="digital_twin_profile.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        profile = saved_data.get("profile", {})
        try:
            if isinstance(profile, list):
                df = pd.DataFrame(profile)
            elif isinstance(profile, dict):
                flat_profile = {}
                for key, value in profile.items():
                    if isinstance(value, (list, dict)):
                        flat_profile[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        flat_profile[key] = value
                df = pd.DataFrame([flat_profile])
            else:
                df = pd.DataFrame([{"profile": str(profile)}])

            csv_data = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 下载 CSV",
                data=csv_data,
                file_name="digital_twin_profile.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception:
            st.button("📥 下载 CSV", disabled=True, use_container_width=True)


def render_empty_state():
    """渲染空状态提示"""
    st.markdown(
        """
    ### 🚀 快速开始

    **方式一：文件上传**
    1. 准备一个包含个人信息的 Excel 或 CSV 文件
    2. 在左侧选择「文件上传」标签
    3. 上传文件并点击「保存」

    **方式二：AI 文本分析** ⭐ 推荐
    1. 在左侧输入 DeepSeek API Key
    2. 选择「文本输入」标签
    3. 粘贴一段自我介绍
    4. 点击「AI 分析并保存」

    AI 会自动提取并分析：
    - 基本信息（姓名、联系方式、教育背景）
    - 能力画像（技能特长、性格特点、个人优势）
    - **🆕 发展建议（可发展方向、可发展优点）**
    """
    )

