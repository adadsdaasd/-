"""
UI: 数据管理（个人版 / 多人版）
============================
将数据管理相关 UI 从 app.py 拆分出来，降低入口文件复杂度。
"""

from __future__ import annotations

import streamlit as st

from profile_validation import validate_general_profile
from store_single import load_profile_single
from self_config import (
    get_self_person_id,
    load_self_profile_from_orgstore,
    migrate_single_to_orgstore,
    bind_self_by_phone,
    search_self_by_name,
    set_self_person_id,
)
from store_org import (
    get_organization,
    load_groups,
    load_people,
    get_group_by_id,
    get_person_by_id,
    delete_person,
    get_people_in_group,
    add_person_to_group,
    remove_person_from_group,
    update_membership_fields,
    create_group,
    rename_group,
    delete_group,
)
from ui_common import render_empty_state, render_export_buttons
from ui_profile import (
    display_profile_from_text,
    display_profile_from_file,
    render_profile_completeness_panel,
)
from ui_performance import render_performance_panel, render_group_leaderboard


def render_data_management():
    """数据管理入口：根据模式渲染个人版/多人版"""
    if st.session_state.get("mode", "single") == "single":
        render_single_mode()
    else:
        render_multi_mode()


def _build_effective_profile_for_validation(person: dict) -> dict:
    """将 OrgStore 的 person 结构拼成更适合校验的 profile dict（不修改原对象）"""
    profile = person.get("profile", {})
    effective = profile.copy() if isinstance(profile, dict) else {}

    # 姓名兜底
    if not effective.get("姓名") or str(effective.get("姓名")).strip() in ("", "未提及", "未知"):
        if person.get("name"):
            effective["姓名"] = person.get("name")

    # 联系方式兜底（同时写入嵌套与扁平键，方便兼容）
    phone = person.get("phone", "") or ""
    email = person.get("email", "") or ""

    contact = effective.get("联系方式")
    if not isinstance(contact, dict):
        contact = {}

    if phone and (not contact.get("电话") or str(contact.get("电话")).strip() in ("", "未提及", "未知")):
        contact["电话"] = phone
    if email and (not contact.get("邮箱") or str(contact.get("邮箱")).strip() in ("", "未提及", "未知")):
        contact["邮箱"] = email

    if contact:
        effective["联系方式"] = contact

    if phone and not effective.get("电话"):
        effective["电话"] = phone
    if email and not effective.get("邮箱"):
        effective["邮箱"] = email

    return effective


# ==================== 主界面：个人版 ====================


def render_single_mode():
    """渲染个人版界面（从 OrgStore 读取"我自己"）"""
    st.header("📋 我的数字分身信息")

    # 尝试从 OrgStore 加载"我自己"
    saved_data = load_self_profile_from_orgstore()

    # 如果 OrgStore 中没有绑定，尝试迁移 user_profile.json
    if saved_data is None:
        single_data = load_profile_single()
        if single_data:
            st.info("检测到旧版个人数据，正在迁移到新架构...")
            success, msg = migrate_single_to_orgstore()
            if success:
                st.success(f"✅ {msg}")
                saved_data = load_self_profile_from_orgstore()
            else:
                st.warning(f"⚠️ 迁移失败：{msg}")
                # 显示手动绑定入口
                _render_manual_bind_section()

    if saved_data is not None:
        # 元信息展示
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            source_map = {
                "text_analysis": "AI 文本分析",
                "file_upload": "文件上传",
                "pdf_resume": "PDF 简历",
            }
            source_label = source_map.get(saved_data.get("source"), saved_data.get("source", "未知"))
            st.metric("数据来源", source_label)
        with col2:
            st.metric("更新时间", saved_data.get("updated_at", saved_data.get("created_at", "未知"))[:10])
        with col3:
            st.metric("存储状态", "✅ 已同步到 OrgStore")
        with col4:
            memberships = saved_data.get("memberships", [])
            st.metric("所属小组", f"{len(memberships)} 个")

        st.markdown("---")

        # 显示所属小组信息（个人版也能看到自己在多人版中的所有组）
        if memberships:
            with st.expander(f"📁 我所属的小组（{len(memberships)} 个）", expanded=False):
                for ms in memberships:
                    group = get_group_by_id(ms.get("group_id"))
                    group_name = group.get("name") if group else "未知小组"
                    fields = ms.get("fields", {})
                    fields_str = ", ".join([f"{k}: {v}" for k, v in fields.items() if k != "source"][:3])
                    st.markdown(f"- **{group_name}** {f'({fields_str})' if fields_str else ''}")

        profile = saved_data.get("profile", {})

        # 必填信息完整性检查
        render_profile_completeness_panel(profile, schema="general", title="✅ 个人信息完整性（必填项）")
        st.markdown("---")

        if saved_data.get("source") == "text_analysis":
            display_profile_from_text(profile)
        else:
            display_profile_from_file(profile)

        with st.expander("🔍 查看原始 JSON 数据"):
            st.json(saved_data)

        render_export_buttons(saved_data)

        # 绩效面板（个人版）
        person_id = saved_data.get("person_id") or saved_data.get("id")
        if person_id:
            st.markdown("---")
            render_performance_panel(person_id, group_id=None, context="single_mode")

        # 解绑/重新绑定入口
        st.markdown("---")
        with st.expander("⚙️ 身份绑定设置"):
            st.caption(f"当前绑定的 person_id: `{saved_data.get('person_id')}`")
            st.caption("个人版数据现已与多人版同步：你在任何小组中的信息都会自动关联到这里。")
            if st.button("🔄 重新绑定（按姓名搜索）", key="rebind_self"):
                st.session_state["show_rebind_search"] = True
            
            if st.session_state.get("show_rebind_search"):
                _render_manual_bind_section(context="rebind")

    else:
        render_empty_state()
        _render_manual_bind_section(context="empty")


def _render_manual_bind_section(context: str = "default"):
    """渲染手动绑定"我自己"的界面"""
    st.markdown("---")
    st.subheader("🔗 绑定「我是谁」")
    st.caption("如果你已经在多人版中有数据，可以输入姓名搜索并绑定为「我自己」。")

    search_name = st.text_input("输入姓名搜索", key=f"bind_search_name_{context}", placeholder="例如：张三")
    
    if search_name:
        candidates = search_self_by_name(search_name)
        if candidates:
            st.markdown(f"**找到 {len(candidates)} 个候选人：**")
            for c in candidates:
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.markdown(f"👤 **{c['name']}** | 📱 {c['phone'] or '无'} | 📧 {c['email'] or '无'}")
                with col_btn:
                    if st.button("绑定", key=f"bind_{c['person_id']}_{context}", use_container_width=True):
                        set_self_person_id(c["person_id"])
                        st.success(f"✅ 已绑定为「{c['name']}」")
                        st.session_state["show_rebind_search"] = False
                        st.rerun()
        else:
            st.info("未找到匹配的人员，请先在「多人版」中导入你的信息。")


# ==================== 主界面：多人版 ====================


def render_multi_mode():
    """渲染多人版界面 - 双视角：组织视角（人员库）+ 小组视角（小组管理）"""
    org = get_organization()
    groups = load_groups()
    people = load_people()

    st.subheader(f"🏢 {org.get('name', '大团队')}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总人数", f"{len(people)} 人")
    with col2:
        st.metric("小组数", f"{len(groups)} 个")
    with col3:
        people_with_groups = sum(1 for p in people if p.get("memberships"))
        st.metric("已分组", f"{people_with_groups} 人")

    st.markdown("---")

    org_tab, group_tab = st.tabs(["👥 人员库（组织视角）", "📁 小组管理（小组视角）"])

    with org_tab:
        _render_org_view(people, groups)

    with group_tab:
        _render_group_view(groups, people)


def _render_org_view(people: list, groups: list):
    """组织视角：显示全局人员库"""
    if not people:
        st.info("📭 暂无人员数据，请在左侧「导入信息」中添加")
        render_empty_state()
        return

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_term = st.text_input("🔍 搜索人员", placeholder="输入姓名、电话或邮箱")
    with col_filter:
        filter_group_options = {"all": "全部人员"} | {g["id"]: g["name"] for g in groups}
        filter_group = st.selectbox(
            "按小组筛选",
            options=list(filter_group_options.keys()),
            format_func=lambda x: filter_group_options[x],
        )

    filtered_people = people
    if search_term:
        search_lower = search_term.lower()
        filtered_people = [
            p
            for p in filtered_people
            if search_lower in p.get("name", "").lower()
            or search_lower in p.get("phone", "")
            or search_lower in p.get("email", "")
        ]

    if filter_group != "all":
        filtered_people = [
            p
            for p in filtered_people
            if any(m.get("group_id") == filter_group for m in p.get("memberships", []))
        ]

    st.caption(f"显示 {len(filtered_people)} / {len(people)} 人")

    for person in filtered_people:
        person_id = person.get("id")
        person_name = person.get("name", "未知")
        person_phone = person.get("phone", "")
        person_email = person.get("email", "")
        memberships = person.get("memberships", [])

        group_names = []
        for ms in memberships:
            group = get_group_by_id(ms.get("group_id"))
            if group:
                group_names.append(group.get("name"))
        groups_str = ", ".join(group_names) if group_names else "未分组"

        with st.container():
            is_selected = st.session_state.get("selected_person_id") == person_id
            border_color = "#4CAF50" if is_selected else "#e0e0e0"
            st.markdown(
                f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 12px; margin: 8px 0;">
                    <div>
                        <h4 style="margin: 0; color: #333;">👤 {person_name}</h4>
                        <p style="font-size: 13px; color: #666; margin: 4px 0;">
                            📱 {person_phone or '无'} | 📧 {person_email or '无'}
                        </p>
                        <p style="font-size: 12px; color: #888; margin: 2px 0;">
                            📁 所属小组：{groups_str}
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("👁️ 查看详情", key=f"view_person_{person_id}", use_container_width=True):
                    st.session_state["selected_person_id"] = person_id
                    st.session_state["view_context"] = "org"
                    st.rerun()
            with btn_col2:
                if st.button("📁 管理分组", key=f"manage_groups_{person_id}", use_container_width=True):
                    st.session_state["managing_person_groups"] = person_id
                    st.rerun()
            with btn_col3:
                if st.button("🗑️ 删除", key=f"delete_person_{person_id}", use_container_width=True):
                    if delete_person(person_id):
                        if st.session_state.get("selected_person_id") == person_id:
                            st.session_state["selected_person_id"] = None
                        st.success(f"已删除「{person_name}」")
                        st.rerun()

            if st.session_state.get("managing_person_groups") == person_id:
                with st.expander("📁 管理小组归属", expanded=True):
                    current_group_ids = [m.get("group_id") for m in memberships]
                    for group in groups:
                        is_member = group.get("id") in current_group_ids
                        col_g, col_action = st.columns([3, 1])
                        with col_g:
                            st.markdown(f"{'✅' if is_member else '⬜'} {group.get('name')}")
                        with col_action:
                            if is_member:
                                if st.button(
                                    "移出",
                                    key=f"remove_from_{group['id']}_{person_id}",
                                    use_container_width=True,
                                ):
                                    remove_person_from_group(person_id, group["id"])
                                    st.rerun()
                            else:
                                if st.button(
                                    "加入",
                                    key=f"add_to_{group['id']}_{person_id}",
                                    use_container_width=True,
                                ):
                                    add_person_to_group(person_id, group["id"])
                                    st.rerun()

                    if st.button("完成", key=f"done_managing_{person_id}", use_container_width=True):
                        st.session_state["managing_person_groups"] = None
                        st.rerun()

    st.markdown("---")

    selected_person_id = st.session_state.get("selected_person_id")
    view_context = st.session_state.get("view_context", "org")
    if selected_person_id and view_context == "org":
        person = get_person_by_id(selected_person_id)
        if person:
            _render_person_detail_org_view(person)


def _render_person_detail_org_view(person: dict):
    """人员详情（组织视角：显示所有小组信息）"""
    st.subheader(f"📄 {person.get('name', '未知')} 的详细信息")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sources = person.get("sources", [])
        source_type = sources[0].get("type", "unknown") if sources else "unknown"
        source_map = {"text_analysis": "AI分析", "file_upload": "文件上传", "pdf_resume": "PDF简历"}
        st.metric("数据来源", source_map.get(source_type, source_type))
    with col2:
        st.metric("电话", person.get("phone") or "无")
    with col3:
        st.metric("邮箱", person.get("email") or "无")
    with col4:
        st.metric("创建时间", (person.get("created_at", "") or "")[:10])

    st.markdown("---")

    effective_profile = _build_effective_profile_for_validation(person)
    render_profile_completeness_panel(effective_profile, schema="general", title="✅ 个人信息完整性（必填项）")
    st.markdown("---")

    memberships = person.get("memberships", [])
    if memberships:
        st.markdown("#### 📁 所属小组及组内信息")
        for ms in memberships:
            group = get_group_by_id(ms.get("group_id"))
            group_name = group.get("name") if group else "未知小组"
            with st.expander(f"📁 {group_name}", expanded=True):
                fields = ms.get("fields", {})
                if fields:
                    for key, value in fields.items():
                        if key != "source":
                            st.markdown(f"**{key}:** {value}")
                else:
                    st.caption("暂无组内信息")
                st.caption(f"加入时间: {ms.get('joined_at', '未知')}")
    else:
        st.info("此人尚未分配到任何小组")

    st.markdown("---")

    profile = person.get("profile", {})
    if isinstance(profile, dict) and profile:
        st.markdown("#### 📋 基础档案")
        if "可发展方向" in profile or "联系方式" in profile:
            display_profile_from_text(profile)
        else:
            display_profile_from_file(profile)

    # 绩效面板（组织视角 — 显示全局绩效）
    st.markdown("---")
    render_performance_panel(person.get("id"), group_id=None, context=f"org_{person.get('id')}")

    with st.expander("🔍 查看原始 JSON 数据"):
        st.json(person)


def _render_group_view(groups: list, people: list):
    """小组视角：显示小组列表和组内成员"""
    with st.expander("➕ 创建新小组"):
        col_name, col_desc = st.columns([2, 1])
        with col_name:
            new_group_name = st.text_input("小组名称", key="new_group_name", placeholder="例如：项目A组")
        with col_desc:
            new_group_desc = st.text_input("描述（可选）", key="new_group_desc", placeholder="小组描述")

        if st.button("创建小组", key="create_group_btn", use_container_width=True):
            if new_group_name.strip():
                group_id = create_group(new_group_name.strip(), new_group_desc.strip())
                st.session_state["selected_group_id"] = group_id
                st.success(f"✅ 小组「{new_group_name}」创建成功！")
                st.rerun()
            else:
                st.warning("请输入小组名称")

    if not groups:
        st.info("📭 暂无小组，请先创建小组")
        return

    st.markdown("---")
    st.markdown("#### 📁 小组列表")

    selected_group_id = st.session_state.get("selected_group_id")

    for group in groups:
        group_id = group.get("id")
        group_name = group.get("name", "未命名小组")
        group_desc = group.get("description", "")

        group_members = get_people_in_group(group_id)
        member_count = len(group_members)

        is_selected = selected_group_id == group_id
        border_color = "#4CAF50" if is_selected else "#e0e0e0"
        bg_color = "#f0fff0" if is_selected else "#fff"

        with st.container():
            st.markdown(
                f"""
            <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 12px; margin: 8px 0; background-color: {bg_color};">
                <h4 style="margin: 0; color: #333;">📁 {group_name}</h4>
                <p style="font-size: 13px; color: #666; margin: 4px 0;">
                    👥 {member_count} 人 {f'| {group_desc}' if group_desc else ''}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
            with btn_col1:
                if st.button("📂 展开", key=f"expand_group_{group_id}", use_container_width=True):
                    st.session_state["selected_group_id"] = group_id
                    st.session_state["selected_person_id"] = None
                    st.session_state["view_context"] = "group"
                    st.rerun()
            with btn_col2:
                if st.button("✏️ 重命名", key=f"rename_group_{group_id}", use_container_width=True):
                    st.session_state["renaming_group_id"] = group_id
                    st.rerun()
            with btn_col3:
                if st.button("➕ 添加成员", key=f"add_member_group_{group_id}", use_container_width=True):
                    st.session_state["selected_group_id"] = group_id
                    st.info("👈 请在左侧「导入信息」中添加成员，或使用「人员库」的「管理分组」功能")
            with btn_col4:
                if st.button("🗑️ 删除", key=f"delete_group_{group_id}", use_container_width=True):
                    if delete_group(group_id):
                        if st.session_state.get("selected_group_id") == group_id:
                            st.session_state["selected_group_id"] = None
                        st.success(f"小组「{group_name}」已删除")
                        st.rerun()

            if st.session_state.get("renaming_group_id") == group_id:
                with st.form(key=f"rename_group_form_{group_id}"):
                    new_name = st.text_input("新小组名称", value=group_name)
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("保存", use_container_width=True):
                            if new_name.strip() and new_name.strip() != group_name:
                                if rename_group(group_id, new_name.strip()):
                                    st.success(f"小组已重命名为「{new_name.strip()}」")
                                    st.session_state["renaming_group_id"] = None
                                    st.rerun()
                            else:
                                st.session_state["renaming_group_id"] = None
                                st.rerun()
                    with col_cancel:
                        if st.form_submit_button("取消", use_container_width=True):
                            st.session_state["renaming_group_id"] = None
                            st.rerun()

            if is_selected:
                st.markdown("##### 组内成员")
                if group_members:
                    for item in group_members:
                        person = item["person"]
                        membership = item["membership"]
                        person_id = person.get("id")
                        person_name = person.get("name", "未知")

                        ms_fields = membership.get("fields", {})
                        fields_str = ", ".join([f"{k}: {v}" for k, v in ms_fields.items() if k != "source"][:3])

                        col_member, col_actions = st.columns([3, 1])
                        with col_member:
                            st.markdown(f"👤 **{person_name}** {f'({fields_str})' if fields_str else ''}")
                        with col_actions:
                            btn_view, btn_remove = st.columns(2)
                            with btn_view:
                                if st.button("查看", key=f"view_in_group_{group_id}_{person_id}", use_container_width=True):
                                    st.session_state["selected_person_id"] = person_id
                                    st.session_state["view_context"] = "group"
                                    st.session_state["view_group_id"] = group_id
                                    st.rerun()
                            with btn_remove:
                                if st.button("移出", key=f"remove_in_group_{group_id}_{person_id}", use_container_width=True):
                                    remove_person_from_group(person_id, group_id)
                                    st.rerun()
                else:
                    st.info("📭 该小组暂无成员")

                # 团队绩效排行榜
                if group_members:
                    st.markdown("---")
                    render_group_leaderboard(group_id)

                st.markdown("---")

    selected_person_id = st.session_state.get("selected_person_id")
    view_context = st.session_state.get("view_context")
    view_group_id = st.session_state.get("view_group_id")

    if selected_person_id and view_context == "group" and view_group_id:
        person = get_person_by_id(selected_person_id)
        group = get_group_by_id(view_group_id)
        if person and group:
            _render_person_detail_group_view(person, group)


def _render_person_detail_group_view(person: dict, group: dict):
    """人员详情（小组视角：只显示当前小组 membership）"""
    group_id = group.get("id")
    group_name = group.get("name", "未知小组")

    st.subheader(f"📄 {person.get('name', '未知')} 在「{group_name}」的信息")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("电话", person.get("phone") or "无")
    with col2:
        st.metric("邮箱", person.get("email") or "无")
    with col3:
        st.metric("人员 ID", person.get("id", ""))

    st.markdown("---")

    effective_profile = _build_effective_profile_for_validation(person)
    completeness = validate_general_profile(effective_profile)
    if completeness.get("is_complete"):
        st.success("✅ 个人必填信息完整：可以进行后续表格输出/生成。")
    else:
        missing = completeness.get("missing_required", [])
        st.error("⚠️ 个人必填信息不完整：无法完成后续表格输出/生成。"
                 + (f" 缺少：{'、'.join(missing)}" if missing else ""))
        with st.expander("查看必填项详情"):
            render_profile_completeness_panel(effective_profile, schema="general", title="必填项明细")

    st.markdown("---")

    st.markdown(f"#### 📁 在「{group_name}」的组内信息")
    current_membership = None
    for ms in person.get("memberships", []):
        if ms.get("group_id") == group_id:
            current_membership = ms
            break

    if current_membership:
        fields = current_membership.get("fields", {})
        if fields:
            with st.form(key=f"edit_membership_{person['id']}_{group_id}"):
                st.markdown("**编辑组内信息：**")
                updated_fields = {}
                for key, value in fields.items():
                    if key != "source":
                        updated_fields[key] = st.text_input(key, value=str(value), key=f"field_{key}_{person['id']}")

                st.markdown("**添加新字段：**")
                col_new_key, col_new_val = st.columns(2)
                with col_new_key:
                    new_field_key = st.text_input("字段名", key=f"new_key_{person['id']}", placeholder="例如：角色")
                with col_new_val:
                    new_field_val = st.text_input("字段值", key=f"new_val_{person['id']}", placeholder="例如：组长")

                if st.form_submit_button("保存更改", use_container_width=True):
                    if new_field_key and new_field_val:
                        updated_fields[new_field_key] = new_field_val
                    update_membership_fields(person["id"], group_id, updated_fields)
                    st.success("✅ 组内信息已更新")
                    st.rerun()
        else:
            st.info("暂无组内信息，可在下方添加")
            with st.form(key=f"add_field_{person['id']}_{group_id}"):
                col_key, col_val = st.columns(2)
                with col_key:
                    new_key = st.text_input("字段名", placeholder="例如：职位")
                with col_val:
                    new_val = st.text_input("字段值", placeholder="例如：工程师")

                if st.form_submit_button("添加", use_container_width=True):
                    if new_key and new_val:
                        update_membership_fields(person["id"], group_id, {new_key: new_val})
                        st.success("✅ 已添加组内信息")
                        st.rerun()

        st.caption(f"加入时间: {current_membership.get('joined_at', '未知')}")

    st.markdown("---")

    with st.expander("📋 查看基础档案", expanded=False):
        profile = person.get("profile", {})
        if isinstance(profile, dict) and profile:
            if "可发展方向" in profile or "联系方式" in profile:
                display_profile_from_text(profile)
            else:
                display_profile_from_file(profile)
        else:
            st.info("暂无基础档案")

    # 绩效面板（小组视角 — 按 group 过滤事件）
    st.markdown("---")
    render_performance_panel(person.get("id"), group_id=group_id, context=f"grp_{group_id}_{person.get('id')}")

    with st.expander("🔍 查看原始 JSON 数据"):
        st.json(person)

