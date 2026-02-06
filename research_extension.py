"""
科研表单扩展 UI (Research Extension)
=====================================
提供学术档案管理、表单生成、预算检查等功能
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from research_models import (
    load_research_profiles,
    save_research_profiles,
    create_research_profile,
    add_research_profile,
    update_research_profile,
    delete_research_profile,
    get_research_profile_by_id,
    add_education,
    remove_education,
    add_publication,
    remove_publication,
    add_grant,
    remove_grant,
    get_publications_summary,
    get_grants_summary,
    validate_budget,
    calculate_budget_summary,
    flatten_profile_for_template,
    get_all_profiles_for_selection,
    EDUCATION_TEMPLATE,
    PUBLICATION_TEMPLATE,
    GRANT_TEMPLATE,
    BUDGET_ALLOCATION_TEMPLATE
)

from form_generator import (
    generate_filled_forms,
    get_template_placeholders,
    get_available_field_mappings
)

from profile_validation import validate_research_profile

from smart_form_filler import detect_form_mode


# ==================== 主渲染函数 ====================

def render_research_mode():
    """渲染科研表单模式的主界面"""
    
    st.header("📚 科研表单填写系统")
    st.markdown("管理学术档案、生成表单、检查预算")
    st.markdown("---")
    
    # 三个主要 Tab
    tab1, tab2, tab3 = st.tabs(["📋 学术档案管理", "📝 表单生成", "💰 预算检查"])
    
    with tab1:
        render_profile_management()
    
    with tab2:
        render_form_generation()
    
    with tab3:
        render_budget_check()


# ==================== Tab 1: 学术档案管理 ====================

def render_profile_management():
    """渲染学术档案管理界面"""
    
    profiles = load_research_profiles()
    
    # 添加新档案
    st.subheader("➕ 添加新档案")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_name = st.text_input("姓名", placeholder="请输入姓名", key="new_profile_name")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("创建档案", type="primary", use_container_width=True):
            if new_name and new_name.strip():
                new_profile = create_research_profile(new_name.strip())
                if add_research_profile(new_profile):
                    st.success(f"✅ 已创建档案：{new_name}")
                    st.rerun()
            else:
                st.warning("请输入姓名")
    
    st.markdown("---")
    
    # 档案列表
    st.subheader(f"📁 已有档案 ({len(profiles)} 人)")
    
    if not profiles:
        st.info("暂无档案，请先添加")
        return
    
    # 选择要编辑的档案
    profile_options = {p["id"]: f"{p.get('姓名', '未知')} (ID: {p['id']})" for p in profiles}
    
    selected_id = st.selectbox(
        "选择档案进行编辑",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x],
        key="selected_research_profile"
    )
    
    if selected_id:
        profile = get_research_profile_by_id(selected_id)
        if profile:
            render_profile_editor(profile)


def render_profile_editor(profile: dict):
    """渲染档案编辑器"""
    
    st.markdown("---")
    
    # 基本信息
    with st.expander("👤 基本信息", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("姓名", value=profile.get("姓名", ""), key=f"edit_name_{profile['id']}")
        
        with col2:
            contact = profile.get("联系方式", {})
            if isinstance(contact, dict):
                email = st.text_input("邮箱", value=contact.get("邮箱", ""), key=f"edit_email_{profile['id']}")
                phone = st.text_input("电话", value=contact.get("电话", ""), key=f"edit_phone_{profile['id']}")
            else:
                email = st.text_input("邮箱", value="", key=f"edit_email_{profile['id']}")
                phone = st.text_input("电话", value="", key=f"edit_phone_{profile['id']}")
        
        if st.button("保存基本信息", key=f"save_basic_{profile['id']}"):
            profile["姓名"] = name
            profile["联系方式"] = {"邮箱": email, "电话": phone}
            if update_research_profile(profile["id"], profile):
                st.success("✅ 已保存")
                st.rerun()
    
    # 教育经历
    with st.expander("🎓 教育经历"):
        render_education_editor(profile)
    
    # 论文发表
    with st.expander("📄 论文发表"):
        render_publications_editor(profile)
    
    # 项目/基金
    with st.expander("💼 项目/基金"):
        render_grants_editor(profile)
    
    # 删除档案
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ 删除此档案", type="secondary", use_container_width=True):
            if delete_research_profile(profile["id"]):
                st.success("已删除")
                st.rerun()


def render_education_editor(profile: dict):
    """渲染教育经历编辑器"""
    
    education_list = profile.get("education_history", [])
    
    # 显示现有教育经历
    if education_list:
        for idx, edu in enumerate(education_list):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            with col1:
                st.text(f"🎓 {edu.get('degree', '')}")
            with col2:
                st.text(edu.get('institution', ''))
            with col3:
                st.text(edu.get('major', ''))
            with col4:
                st.text(f"{edu.get('start_date', '')} - {edu.get('end_date', '')}")
            with col5:
                if st.button("删除", key=f"del_edu_{profile['id']}_{edu.get('id', idx)}"):
                    remove_education(profile["id"], edu.get("id"))
                    st.rerun()
    
    st.markdown("**添加教育经历**")
    
    col1, col2 = st.columns(2)
    with col1:
        degree = st.selectbox("学位", ["博士", "硕士", "学士", "其他"], key=f"new_degree_{profile['id']}")
        institution = st.text_input("院校", key=f"new_institution_{profile['id']}")
    with col2:
        major = st.text_input("专业", key=f"new_major_{profile['id']}")
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.text_input("开始日期", placeholder="YYYY-MM", key=f"new_edu_start_{profile['id']}")
        with col_date2:
            end_date = st.text_input("结束日期", placeholder="YYYY-MM", key=f"new_edu_end_{profile['id']}")
    
    if st.button("添加教育经历", key=f"add_edu_{profile['id']}"):
        if institution:
            new_edu = {
                "degree": degree,
                "institution": institution,
                "major": major,
                "start_date": start_date,
                "end_date": end_date
            }
            if add_education(profile["id"], new_edu):
                st.success("✅ 已添加")
                st.rerun()


def render_publications_editor(profile: dict):
    """渲染论文编辑器"""
    
    publications = profile.get("publications", [])
    summary = get_publications_summary(profile)
    
    # 统计信息
    st.markdown(f"**统计**: 共 {summary['total']} 篇 | SCI: {summary['sci']} | EI: {summary['ei']} | 核心: {summary['core']}")
    
    # 显示现有论文
    if publications:
        for idx, pub in enumerate(publications):
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            with col1:
                st.text(f"📄 {pub.get('title', '')[:40]}...")
            with col2:
                st.text(pub.get('type', ''))
            with col3:
                st.text(str(pub.get('year', '')))
            with col4:
                if st.button("删除", key=f"del_pub_{profile['id']}_{pub.get('id', idx)}"):
                    remove_publication(profile["id"], pub.get("id"))
                    st.rerun()
    
    st.markdown("**添加论文**")
    
    title = st.text_input("论文标题", key=f"new_pub_title_{profile['id']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        journal = st.text_input("期刊/会议", key=f"new_pub_journal_{profile['id']}")
    with col2:
        pub_type = st.selectbox("类型", ["SCI", "EI", "核心", "其他"], key=f"new_pub_type_{profile['id']}")
    with col3:
        year = st.number_input("年份", min_value=1990, max_value=2030, value=2024, key=f"new_pub_year_{profile['id']}")
    
    col4, col5 = st.columns(2)
    with col4:
        authors = st.text_input("作者列表", key=f"new_pub_authors_{profile['id']}")
    with col5:
        doi = st.text_input("DOI", key=f"new_pub_doi_{profile['id']}")
    
    if st.button("添加论文", key=f"add_pub_{profile['id']}"):
        if title:
            new_pub = {
                "title": title,
                "journal": journal,
                "type": pub_type,
                "year": year,
                "authors": authors,
                "doi": doi
            }
            if add_publication(profile["id"], new_pub):
                st.success("✅ 已添加")
                st.rerun()


def render_grants_editor(profile: dict):
    """渲染项目/基金编辑器"""
    
    grants = profile.get("grants", [])
    summary = get_grants_summary(profile)
    
    # 统计信息
    st.markdown(f"**统计**: 共 {summary['total']} 项 | 负责人: {summary['as_pi']} | 参与者: {summary['as_member']} | 总经费: ¥{summary['total_budget']:,.0f}")
    
    # 显示现有项目
    if grants:
        for idx, grant in enumerate(grants):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.text(f"💼 {grant.get('project_name', '')[:30]}...")
            with col2:
                st.text(grant.get('role', ''))
            with col3:
                st.text(f"¥{grant.get('budget', 0):,.0f}")
            with col4:
                if st.button("删除", key=f"del_grant_{profile['id']}_{grant.get('id', idx)}"):
                    remove_grant(profile["id"], grant.get("id"))
                    st.rerun()
    
    st.markdown("**添加项目**")
    
    project_name = st.text_input("项目名称", key=f"new_grant_name_{profile['id']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        grant_id = st.text_input("基金号", key=f"new_grant_id_{profile['id']}")
    with col2:
        role = st.selectbox("角色", ["负责人", "参与者"], key=f"new_grant_role_{profile['id']}")
    with col3:
        budget = st.number_input("预算 (元)", min_value=0, value=100000, step=10000, key=f"new_grant_budget_{profile['id']}")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        funding_agency = st.text_input("资助机构", key=f"new_grant_agency_{profile['id']}")
    with col5:
        grant_start = st.text_input("开始日期", placeholder="YYYY-MM", key=f"new_grant_start_{profile['id']}")
    with col6:
        grant_end = st.text_input("结束日期", placeholder="YYYY-MM", key=f"new_grant_end_{profile['id']}")
    
    if st.button("添加项目", key=f"add_grant_{profile['id']}"):
        if project_name:
            new_grant = {
                "project_name": project_name,
                "grant_id": grant_id,
                "role": role,
                "budget": budget,
                "funding_agency": funding_agency,
                "start_date": grant_start,
                "end_date": grant_end
            }
            if add_grant(profile["id"], new_grant):
                st.success("✅ 已添加")
                st.rerun()


# ==================== Tab 2: 表单生成 ====================

def render_form_generation():
    """渲染表单生成界面"""
    
    profiles = load_research_profiles()
    
    if not profiles:
        st.warning("请先在「学术档案管理」中添加档案")
        return
    
    st.subheader("📄 上传模板")
    
    template_file = st.file_uploader(
        "上传 Excel 或 Word 模板",
        type=['xlsx', 'xls', 'docx'],
        help="模板中使用 {{字段名}} 作为占位符"
    )
    
    if template_file:
        # 分析模板占位符
        placeholders = get_template_placeholders(template_file, template_file.name)
        
        if placeholders:
            st.markdown("**检测到的占位符:**")
            st.code(", ".join(placeholders))
        
        template_file.seek(0)  # 重置文件指针
        
        # 自动检测表格模式
        st.markdown("---")
        st.subheader("📊 模板模式检测")
        
        # 确定文件类型
        file_type = "excel" if template_file.name.lower().endswith(('.xlsx', '.xls')) else "word"
        detected_mode, reason, confidence = detect_form_mode(template_file, file_type)
        template_file.seek(0)  # 重置文件指针
        
        # 显示检测结果
        mode_labels = {"batch": "一人一表", "aggregate": "一表多人"}
        confidence_pct = int(confidence * 100)
        
        st.markdown(f"**AI 判断结果：** {mode_labels[detected_mode]} (置信度: {confidence_pct}%)")
        st.caption(reason)
        
        # 保存检测结果到 session_state
        if 'research_detected_mode' not in st.session_state:
            st.session_state['research_detected_mode'] = detected_mode
    
    st.markdown("---")
    
    # 选择人员
    st.subheader("👥 选择人员")
    
    profile_options = get_all_profiles_for_selection()
    
    if not profile_options:
        st.warning("没有可用的档案")
        return
    
    # 创建选择表格
    selection_df = pd.DataFrame(profile_options)
    selection_df["选择"] = False
    
    edited_df = st.data_editor(
        selection_df,
        column_config={
            "选择": st.column_config.CheckboxColumn("选择", default=False),
            "id": st.column_config.TextColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("姓名", disabled=True),
            "degree": st.column_config.TextColumn("学位", disabled=True),
            "institution": st.column_config.TextColumn("院校", disabled=True),
            "publications": st.column_config.NumberColumn("论文数", disabled=True),
            "grants": st.column_config.NumberColumn("项目数", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key="profile_selection"
    )
    
    selected_ids = edited_df[edited_df["选择"] == True]["id"].tolist()
    
    st.markdown(f"**已选择 {len(selected_ids)} 人**")

    # ========== 信息完整性校验：不完整则禁止生成 ==========
    selected_profiles = [p for p in profiles if p.get("id") in selected_ids]
    incomplete = []
    for p in selected_profiles:
        try:
            res = validate_research_profile(p)
        except Exception:
            res = {"is_complete": False, "missing_required": ["档案结构异常"]}
        if not res.get("is_complete"):
            incomplete.append({
                "id": p.get("id", ""),
                "name": p.get("姓名", p.get("name", "未知")),
                "missing": res.get("missing_required", []),
            })

    all_complete = (len(selected_ids) > 0) and (len(incomplete) == 0)
    if selected_ids and incomplete:
        st.error("⚠️ 选中的档案信息不完整：无法生成表单。请先补全必填信息。")
        with st.expander("查看缺失项"):
            for x in incomplete:
                missing = "、".join(x.get("missing", []) or [])
                st.markdown(f"- **{x['name']}**：{missing if missing else '缺失必填项'}")
    
    st.markdown("---")
    
    # 生成策略（基于 AI 检测结果，但允许手动切换）
    st.subheader("⚙️ 生成策略")
    
    # 获取检测到的模式作为默认值
    default_mode = st.session_state.get('research_detected_mode', 'batch')
    default_index = 0 if default_mode == "batch" else 1
    
    strategy = st.radio(
        "选择生成方式",
        ["batch", "aggregate"],
        index=default_index,
        format_func=lambda x: "📂 批量生成 (每人一个文件)" if x == "batch" else "📑 聚合生成 (所有人填入一个文件)",
        horizontal=True,
        help="基于 AI 检测结果自动选择，如判断不准确可手动切换"
    )
    
    if template_file and strategy != st.session_state.get('research_detected_mode', 'batch'):
        st.info("已切换为手动选择模式")
    
    if strategy == "batch":
        st.info("💡 批量生成：将为每个选中的人生成一个独立文件，打包为 ZIP 下载")
    else:
        st.info("💡 聚合生成：将所有选中的人填入同一个文件的表格中（需要模板包含 {{TABLE:xxx}} 标记）")
    
    st.markdown("---")
    
    # 生成按钮
    if st.button(
        "🚀 生成表单",
        type="primary",
        use_container_width=True,
        disabled=not (template_file and selected_ids and all_complete)
    ):
        if not template_file:
            st.error("请上传模板文件")
        elif not selected_ids:
            st.error("请至少选择一人")
        elif not all_complete:
            st.error("选中的档案信息不完整，请先补全必填信息")
        else:
            with st.spinner("正在生成..."):
                content, filename, errors = generate_filled_forms(
                    template_file,
                    template_file.name,
                    selected_ids,
                    strategy
                )
            
            if errors:
                for err in errors:
                    st.warning(err)
            
            if content:
                st.success(f"✅ 生成成功！")
                
                # 确定 MIME 类型
                if filename.endswith('.zip'):
                    mime = "application/zip"
                elif filename.endswith('.xlsx'):
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif filename.endswith('.docx'):
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                else:
                    mime = "application/octet-stream"
                
                st.download_button(
                    label="📥 下载生成的文件",
                    data=content,
                    file_name=filename,
                    mime=mime,
                    use_container_width=True
                )
    
    # 占位符参考
    with st.expander("📖 可用占位符参考"):
        field_mappings = get_available_field_mappings()
        
        col1, col2 = st.columns(2)
        items = list(field_mappings.items())
        mid = len(items) // 2
        
        with col1:
            for placeholder, desc in items[:mid]:
                st.markdown(f"`{placeholder}` - {desc}")
        
        with col2:
            for placeholder, desc in items[mid:]:
                st.markdown(f"`{placeholder}` - {desc}")


# ==================== Tab 3: 预算检查 ====================

def render_budget_check():
    """渲染预算检查界面"""
    
    st.subheader("💰 预算分配检查工具")
    st.markdown("输入预算分配，自动检查是否符合常见限制")
    
    st.markdown("---")
    
    # 总预算
    total_budget = st.number_input(
        "项目总预算 (元)",
        min_value=0,
        value=500000,
        step=10000,
        key="budget_total"
    )
    
    st.markdown("---")
    
    # 预算分配
    st.subheader("📊 预算分配")
    
    col1, col2 = st.columns(2)
    
    with col1:
        labor_fee = st.number_input("人员费", min_value=0, value=200000, step=5000)
        equipment_fee = st.number_input("设备费", min_value=0, value=100000, step=5000)
        material_fee = st.number_input("材料费", min_value=0, value=50000, step=5000)
        travel_fee = st.number_input("差旅费", min_value=0, value=30000, step=5000)
    
    with col2:
        conference_fee = st.number_input("会议费", min_value=0, value=20000, step=5000)
        publication_fee = st.number_input("出版/文献费", min_value=0, value=15000, step=5000)
        indirect_cost = st.number_input("间接费用", min_value=0, value=50000, step=5000)
        other_fee = st.number_input("其他费用", min_value=0, value=35000, step=5000)
    
    # 构建预算分配字典
    budget_allocation = {
        "labor_fee": labor_fee,
        "equipment_fee": equipment_fee,
        "material_fee": material_fee,
        "travel_fee": travel_fee,
        "conference_fee": conference_fee,
        "publication_fee": publication_fee,
        "indirect_cost": indirect_cost,
        "other_fee": other_fee
    }
    
    st.markdown("---")
    
    # 约束条件
    st.subheader("⚙️ 约束条件")
    
    col3, col4 = st.columns(2)
    
    with col3:
        labor_max = st.slider("人员费最高占比", 0.0, 1.0, 0.5, 0.05)
        equipment_max = st.slider("设备费最高占比", 0.0, 1.0, 0.3, 0.05)
    
    with col4:
        travel_max = st.slider("差旅费最高占比", 0.0, 1.0, 0.1, 0.05)
        indirect_ratio = st.slider("间接费用建议比例", 0.0, 0.3, 0.1, 0.05)
    
    constraints = {
        "labor_fee_max_ratio": labor_max,
        "equipment_fee_max_ratio": equipment_max,
        "travel_fee_max_ratio": travel_max,
        "indirect_cost_ratio": indirect_ratio
    }
    
    st.markdown("---")
    
    # 检查结果
    if st.button("🔍 检查预算", type="primary", use_container_width=True):
        # 计算摘要
        summary = calculate_budget_summary(budget_allocation)
        allocated_total = summary["total"]
        
        st.subheader("📋 检查结果")
        
        # 总额对比
        col_sum1, col_sum2, col_sum3 = st.columns(3)
        with col_sum1:
            st.metric("项目总预算", f"¥{total_budget:,.0f}")
        with col_sum2:
            st.metric("已分配金额", f"¥{allocated_total:,.0f}")
        with col_sum3:
            diff = total_budget - allocated_total
            st.metric("差额", f"¥{diff:,.0f}", delta=f"{diff:+,.0f}")
        
        if allocated_total != total_budget:
            if allocated_total > total_budget:
                st.error(f"❌ 分配金额超出预算 ¥{allocated_total - total_budget:,.0f}")
            else:
                st.warning(f"⚠️ 尚有 ¥{total_budget - allocated_total:,.0f} 未分配")
        
        st.markdown("---")
        
        # 占比分析
        st.markdown("**占比分析:**")
        
        breakdown_data = []
        for key, info in summary["breakdown"].items():
            label_map = {
                "labor_fee": "人员费",
                "equipment_fee": "设备费",
                "material_fee": "材料费",
                "travel_fee": "差旅费",
                "conference_fee": "会议费",
                "publication_fee": "出版费",
                "indirect_cost": "间接费用",
                "other_fee": "其他费用"
            }
            breakdown_data.append({
                "项目": label_map.get(key, key),
                "金额": f"¥{info['amount']:,.0f}",
                "占比": f"{info['ratio']:.1%}"
            })
        
        st.table(pd.DataFrame(breakdown_data))
        
        # 验证警告
        warnings = validate_budget(budget_allocation, constraints)
        
        if warnings:
            st.markdown("**⚠️ 警告信息:**")
            for w in warnings:
                st.warning(w)
        else:
            st.success("✅ 预算分配符合所有约束条件")


# ==================== 侧边栏内容 ====================

def render_research_sidebar():
    """渲染科研模式的侧边栏内容"""
    
    st.markdown("---")
    st.subheader("📚 科研表单")
    
    # 快速统计
    profiles = load_research_profiles()
    st.metric("档案总数", len(profiles))
    
    total_pubs = sum(len(p.get("publications", [])) for p in profiles)
    total_grants = sum(len(p.get("grants", [])) for p in profiles)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("论文总数", total_pubs)
    with col2:
        st.metric("项目总数", total_grants)
    
    st.markdown("---")
    
    # 快速操作
    st.markdown("**快速操作**")
    
    if st.button("📥 导出所有档案", use_container_width=True):
        if profiles:
            json_str = json.dumps(profiles, ensure_ascii=False, indent=2)
            st.download_button(
                label="下载 JSON",
                data=json_str,
                file_name="research_profiles_export.json",
                mime="application/json",
                use_container_width=True
            )
    
    # 导入档案
    uploaded_import = st.file_uploader(
        "导入档案 (JSON)",
        type=['json'],
        key="import_research_profiles"
    )
    
    if uploaded_import:
        try:
            imported = json.load(uploaded_import)
            if isinstance(imported, list):
                if st.button("确认导入", type="primary"):
                    save_research_profiles(imported)
                    st.success(f"✅ 已导入 {len(imported)} 个档案")
                    st.rerun()
        except Exception as e:
            st.error(f"导入失败: {str(e)}")
