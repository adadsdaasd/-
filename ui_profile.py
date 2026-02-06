"""
UI Components: Profile Views
============================
将人物画像的展示逻辑从 app.py 中拆出，便于复用与维护。
"""

from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd
import streamlit as st

from profile_validation import validate_general_profile, validate_research_profile


def display_profile_from_text(profile: dict):
    """显示 AI 分析的人物画像（增强版，包含发展建议）"""

    # 基本信息卡片
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 基本信息")
        st.markdown(f"**姓名：** {profile.get('姓名', '未提及')}")
        contact = profile.get("联系方式", {})
        if isinstance(contact, dict):
            st.markdown(f"**电话：** {contact.get('电话', '未提及')}")
            st.markdown(f"**邮箱：** {contact.get('邮箱', '未提及')}")
        else:
            st.markdown(f"**联系方式：** {contact}")
        st.markdown(f"**教育背景：** {profile.get('教育背景', '未提及')}")

    with col2:
        st.subheader("🎯 个人优势")
        st.info(profile.get("个人优势", "未提及"))

        st.subheader("🚀 未来规划")
        st.info(profile.get("未来规划", "未提及"))

    st.markdown("---")

    # 技能和特点
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("💡 技能特长")
        skills = profile.get("技能特长", [])
        if isinstance(skills, list) and skills:
            for skill in skills:
                st.markdown(f"- {skill}")
        else:
            st.markdown("未提及")

    with col4:
        st.subheader("✨ 性格特点")
        traits = profile.get("性格特点", [])
        if isinstance(traits, list) and traits:
            for trait in traits:
                st.markdown(f"- {trait}")
        else:
            st.markdown("未提及")

    st.markdown("---")

    # 工作经历
    st.subheader("💼 工作经历")
    experience = profile.get("工作经历", [])
    if isinstance(experience, list) and experience:
        for exp in experience:
            st.markdown(f"- {exp}")
    else:
        st.markdown("未提及")

    # 其他亮点
    other = profile.get("其他亮点", "")
    if other and other != "未提及":
        st.subheader("🌟 其他亮点")
        st.success(other)

    st.markdown("---")

    # 可发展方向
    st.subheader("🧭 可发展方向（AI 建议）")
    dev_direction = profile.get("可发展方向", {})

    if isinstance(dev_direction, dict) and dev_direction:
        col_d1, col_d2, col_d3 = st.columns(3)

        with col_d1:
            st.markdown("**📅 短期建议（1-2年）**")
            st.info(dev_direction.get("短期建议", "暂无建议"))

        with col_d2:
            st.markdown("**📆 中期建议（3-5年）**")
            st.info(dev_direction.get("中期建议", "暂无建议"))

        with col_d3:
            st.markdown("**🔭 长期愿景**")
            st.info(dev_direction.get("长期愿景", "暂无建议"))
    else:
        st.markdown("暂无发展方向建议")

    st.markdown("---")

    # 可发展优点
    st.subheader("💎 可发展优点（AI 建议）")
    dev_strengths = profile.get("可发展优点", {})

    if isinstance(dev_strengths, dict) and dev_strengths:
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.markdown("**🏆 核心优势**")
            st.success(dev_strengths.get("核心优势", "暂无"))

            st.markdown("**🌱 潜力优点**")
            st.warning(dev_strengths.get("潜力优点", "暂无"))

        with col_s2:
            st.markdown("**📝 发展建议**")
            st.info(dev_strengths.get("发展建议", "暂无建议"))
    else:
        st.markdown("暂无发展优点建议")


def display_profile_from_file(profile_data: Any):
    """显示文件上传的数据"""
    if isinstance(profile_data, list):
        df = pd.DataFrame(profile_data)
        st.dataframe(df, use_container_width=True, height=400)
    elif isinstance(profile_data, dict):
        try:
            df = pd.DataFrame([profile_data])
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.json(profile_data)
    else:
        st.json(profile_data)


def render_profile_completeness_panel(
    profile_data: Any,
    schema: str = "general",
    title: str = "✅ 信息完整性检查",
) -> Dict[str, Any]:
    """
    渲染“必填信息完整性”面板。
    - schema = general: 用于个人版/多人版成员
    - schema = research: 用于科研档案
    """
    if schema == "research":
        result = validate_research_profile(profile_data)
    else:
        result = validate_general_profile(profile_data)

    st.markdown(f"#### {title}")

    if result.get("is_complete"):
        st.success("信息完整：可以进行后续表格输出/生成。")
    else:
        st.error("信息不完整：将无法完成后续表格输出/生成。请先补全必填信息。")

    issues = result.get("issues", [])
    if issues:
        for msg in issues:
            st.warning(msg)

    required_items = result.get("items_required", [])
    for it in required_items:
        ok = it.get("ok", False)
        label = it.get("label", "")
        value = it.get("value", "")
        if ok:
            st.markdown(f"✅ **{label}**：{value if value else '已填写'}")
        else:
            st.markdown(f"❌ **{label}**：未填写")

    recommended_items = result.get("items_recommended", [])
    if recommended_items:
        missing_reco = [it.get("label") for it in recommended_items if not it.get("ok")]
        if missing_reco:
            st.info("推荐补充：" + "、".join(missing_reco))

    return result

