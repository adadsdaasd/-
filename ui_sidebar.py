"""
UI: Sidebar
===========
侧边栏负责：模式选择、API Key、导入区、清除按钮。
"""

from __future__ import annotations

import streamlit as st

from ui_import import render_import_section, render_clear_memory_buttons


def render_sidebar() -> str:
    """渲染侧边栏，返回 api_key"""
    with st.sidebar:
        st.header("🧠 Digital Twin")
        st.markdown("---")

        # 用户模式选择
        st.subheader("📌 用户模式")
        mode_options = ["👤 个人版", "👥 多人版"]
        mode_index = 0 if st.session_state.get("mode", "single") == "single" else 1
        mode = st.radio(
            "选择版本",
            mode_options,
            index=mode_index,
            help="个人版：只保存一个人的信息\n多人版：可保存和管理多人信息",
        )
        st.session_state["mode"] = "single" if "个人" in mode else "multi"

        st.markdown("---")

        # API Key
        st.subheader("🔑 API 配置")
        
        # 优先从环境变量或 Streamlit secrets 读取
        import os
        default_api_key = ""
        
        # 1. 尝试从 Streamlit secrets 读取（Streamlit Cloud）
        try:
            if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets:
                default_api_key = st.secrets["DEEPSEEK_API_KEY"]
        except Exception:
            pass
        
        # 2. 尝试从环境变量读取
        if not default_api_key:
            default_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        # 3. 从 session_state 读取（用户之前输入的）
        if not default_api_key:
            default_api_key = st.session_state.get("api_key", "")
        
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            value=default_api_key,
            placeholder="sk-...",
            help="输入你的 DeepSeek API Key，用于 AI 分析功能。也可以设置环境变量 DEEPSEEK_API_KEY",
        )
        
        # 保存到 session_state
        if api_key:
            st.session_state["api_key"] = api_key
        
        if api_key:
            st.success("✅ API Key 已配置")
        else:
            st.warning("⚠️ 请输入 API Key 以启用 AI 分析")
            st.markdown("[获取 API Key →](https://platform.deepseek.com/)")
            st.caption("💡 提示：可以在 Streamlit Cloud 的 Settings → Secrets 中配置，避免每次输入")

        st.markdown("---")

        # 导入
        render_import_section(api_key)

        # 清除
        render_clear_memory_buttons()

        return api_key

