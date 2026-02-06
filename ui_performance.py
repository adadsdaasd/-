"""
绩效面板 UI (Performance Panel)
================================
独立 UI 组件，嵌入到 ui_data_management 的人员详情中。
不直接操作文件——通过 store_org 的 API 读写。
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Optional

from performance_models import (
    ensure_performance,
    compute_current_score,
    get_summary,
    get_contributions,
    filter_events,
    build_contribution_event,
    build_manual_adjust_event,
    EVENT_TYPE_CONTRIBUTION,
    EVENT_TYPE_MANUAL_ADJUST,
    EVENT_TYPE_IMPORT,
)
from store_org import (
    get_person_performance,
    set_person_base_score,
    add_performance_event,
    update_performance_event,
    delete_performance_event,
    get_people_in_group,
    get_person_by_id,
    load_groups,
)


# ==================== 指标卡片 ====================


def _render_score_metrics(person_id: str, group_id: Optional[str] = None):
    """渲染绩效概览指标"""
    perf = get_person_performance(person_id)
    summary = get_summary(perf, group_id=group_id)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("当前绩效", f"{summary['current_score']:.1f}")
    with c2:
        st.metric("基准分", f"{summary['base_score']:.1f}")
    with c3:
        st.metric("贡献累计", f"+{summary['contribution_total']:.1f}")

    c4, c5 = st.columns(2)
    with c4:
        st.caption(f"贡献 {summary['contribution_count']} 条 | 总事件 {summary['event_count']} 条")
    with c5:
        st.caption(f"最后更新：{summary['last_updated']}")


# ==================== 贡献管理 ====================


def _render_contribution_section(person_id: str, group_id: Optional[str] = None, context: str = "default"):
    """渲染贡献列表 + 添加贡献表单"""
    perf = get_person_performance(person_id)
    contributions = get_contributions(perf, group_id=group_id)

    st.markdown("##### 主要贡献")

    if contributions:
        for i, c in enumerate(contributions):
            with st.expander(f"📌 {c.get('title', '未命名')}  |  +{c.get('delta', 0):.1f} 分  |  {c.get('at', '')}", expanded=False):
                st.text(f"备注：{c.get('note', '无')}")
                col_del, col_edit = st.columns(2)
                with col_del:
                    if st.button("🗑 删除", key=f"del_contrib_{person_id}_{c['id']}_{context}"):
                        delete_performance_event(person_id, c["id"])
                        st.rerun()
                with col_edit:
                    new_note = st.text_input("修改备注", value=c.get("note", ""), key=f"edit_note_{person_id}_{c['id']}_{context}")
                    if new_note != c.get("note", ""):
                        if st.button("💾 保存", key=f"save_note_{person_id}_{c['id']}_{context}"):
                            update_performance_event(person_id, c["id"], {"note": new_note})
                            st.rerun()
    else:
        st.caption("暂无贡献记录")

    # 添加新贡献
    st.markdown("---")
    st.markdown("###### 添加新贡献")
    with st.form(key=f"add_contrib_form_{person_id}_{context}"):
        title = st.text_input("贡献名称", placeholder="例：完成XX项目")
        delta = st.number_input("绩效分值", value=0.0, step=0.5, min_value=-100.0, max_value=1000.0)
        note = st.text_area("备注说明", placeholder="可选填写", height=68)
        submitted = st.form_submit_button("➕ 添加贡献", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("请输入贡献名称")
        else:
            event = build_contribution_event(
                title=title.strip(),
                delta=delta,
                note=note.strip(),
                group_id=group_id,
            )
            add_performance_event(person_id, event)
            st.success(f"✅ 已添加贡献：{title.strip()}（+{delta}）")
            st.rerun()


# ==================== 手动调整 ====================


def _render_adjust_section(person_id: str, group_id: Optional[str] = None, context: str = "default"):
    """渲染手动绩效调整"""
    st.markdown("##### 手动调整")

    with st.form(key=f"manual_adjust_form_{person_id}_{context}"):
        adj_title = st.text_input("调整说明", placeholder="例：季度奖励 / 迟到扣分")
        adj_delta = st.number_input("分值（正加负减）", value=0.0, step=0.5, min_value=-1000.0, max_value=1000.0)
        adj_note = st.text_area("备注", placeholder="可选", height=68)
        adj_submitted = st.form_submit_button("📝 提交调整", use_container_width=True)

    if adj_submitted:
        if not adj_title.strip():
            st.warning("请输入调整说明")
        elif adj_delta == 0:
            st.warning("分值不能为 0")
        else:
            event = build_manual_adjust_event(
                delta=adj_delta,
                title=adj_title.strip(),
                note=adj_note.strip(),
                group_id=group_id,
            )
            add_performance_event(person_id, event)
            st.success(f"✅ 已调整：{adj_title.strip()}（{'+' if adj_delta > 0 else ''}{adj_delta}）")
            st.rerun()


# ==================== 基准分设置 ====================


def _render_base_score_editor(person_id: str, context: str = "default"):
    """编辑基准绩效分"""
    perf = get_person_performance(person_id)
    current_base = perf.get("base_score", 0.0)

    st.markdown("##### 基准分设置")
    new_base = st.number_input(
        "基准绩效分",
        value=float(current_base),
        step=1.0,
        key=f"base_score_input_{person_id}_{context}",
    )
    if st.button("💾 更新基准分", key=f"update_base_{person_id}_{context}"):
        if new_base != current_base:
            set_person_base_score(person_id, new_base)
            st.success(f"✅ 基准分已更新为 {new_base}")
            st.rerun()
        else:
            st.info("基准分未改变")


# ==================== 事件历史 ====================


def _render_event_history(person_id: str, group_id: Optional[str] = None, context: str = "default"):
    """渲染全部事件历史表"""
    perf = get_person_performance(person_id)
    events = filter_events(perf, group_id=group_id)

    st.markdown("##### 事件记录")

    if not events:
        st.caption("暂无事件记录")
        return

    type_labels = {
        EVENT_TYPE_IMPORT: "📥 导入",
        EVENT_TYPE_CONTRIBUTION: "📌 贡献",
        EVENT_TYPE_MANUAL_ADJUST: "📝 调整",
    }

    rows = []
    for e in reversed(events):  # 最新在前
        rows.append({
            "类型": type_labels.get(e.get("type", ""), e.get("type", "")),
            "标题": e.get("title", ""),
            "分值": f"+{e['delta']}" if e.get("delta", 0) >= 0 else str(e.get("delta", 0)),
            "日期": e.get("at", ""),
            "备注": e.get("note", ""),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ==================== 团队排行榜 ====================


def render_group_leaderboard(group_id: str):
    """渲染团队绩效排行榜"""
    items = get_people_in_group(group_id)
    if not items:
        st.info("该团队暂无成员")
        return

    rows = []
    for item in items:
        p = item["person"]
        perf = p.get("performance", {})
        ensure_performance(p)
        summary = get_summary(perf, group_id=group_id)
        rows.append({
            "姓名": p.get("name", "未知"),
            "当前绩效": summary["current_score"],
            "基准分": summary["base_score"],
            "贡献累计": summary["contribution_total"],
            "贡献数": summary["contribution_count"],
        })

    df = pd.DataFrame(rows).sort_values("当前绩效", ascending=False).reset_index(drop=True)

    st.markdown("#### 📊 团队绩效排行")

    # 柱状图
    if len(df) > 0:
        chart_data = df[["姓名", "当前绩效"]].set_index("姓名")
        st.bar_chart(chart_data)

    st.dataframe(df, use_container_width=True, hide_index=True)

    # 导出
    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 导出团队绩效 CSV",
        csv_data,
        file_name="team_performance.csv",
        mime="text/csv",
        key=f"export_team_perf_{group_id}",
    )


# ==================== 主入口面板 ====================


def render_performance_panel(person_id: str, group_id: Optional[str] = None, context: str = "default"):
    """
    完整的绩效面板，嵌入人员详情页面。

    Args:
        person_id: 人员 ID
        group_id: 可选组 ID（过滤事件）
        context: UI 上下文（防止 key 冲突）
    """
    person = get_person_by_id(person_id)
    if not person:
        st.warning("未找到该人员")
        return

    st.markdown(f"### 📈 绩效管理 — {person.get('name', '未知')}")

    # 1. 概览指标
    _render_score_metrics(person_id, group_id)

    st.markdown("---")

    # 2. 标签页分区
    tab_contrib, tab_adjust, tab_base, tab_history = st.tabs([
        "📌 主要贡献", "📝 手动调整", "⚙️ 基准分", "📋 事件记录"
    ])

    with tab_contrib:
        _render_contribution_section(person_id, group_id, context=f"{context}_contrib")

    with tab_adjust:
        _render_adjust_section(person_id, group_id, context=f"{context}_adjust")

    with tab_base:
        _render_base_score_editor(person_id, context=f"{context}_base")

    with tab_history:
        _render_event_history(person_id, group_id, context=f"{context}_history")
