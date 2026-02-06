"""
UI State initialization
=======================
集中初始化 Streamlit session_state，避免各模块分散设置导致状态不一致。
"""

from __future__ import annotations

import streamlit as st


def init_session_state():
    defaults = {
        # 用户模式：single / multi
        "mode": "single",

        # 多人版：当前选中的小组/人员
        "selected_group_id": None,
        "selected_person_id": None,

        # 详情页上下文：org / group
        "view_context": "org",
        "view_group_id": None,

        # 人员库：管理分组弹层
        "managing_person_groups": None,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

