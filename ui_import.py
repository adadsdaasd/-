"""
UI: 侧边栏导入与清除
====================
把“文件上传 / 文本分析 / PDF 简历导入 / 清除记忆”等逻辑集中在侧边栏模块中。
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from ai_services import analyze_text_with_ai
from pdf_resume_import import extract_pdf_text, clean_resume_text
from store_single import (
    save_profile_single,
    single_profile_exists,
    delete_profile_single,
)
from self_config import (
    save_self_profile,
    clear_self_person_id,
)
from store_org import (
    load_groups,
    create_group,
    get_people_in_group,
    upsert_person,
    add_profile_multi,
    org_store_exists,
    delete_org_store_file,
)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """读取上传的文件，支持 CSV 和 Excel 格式"""
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, encoding="gbk")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="latin-1")
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"不支持的文件格式: {filename}")

    return df


def render_group_selector():
    """多人版：目标小组选择器（会写入 st.session_state['selected_group_id']）"""
    groups = load_groups()

    if not groups:
        st.info("📭 暂无小组，请先创建")
        with st.expander("➕ 快速创建小组", expanded=True):
            quick_group_name = st.text_input("小组名称", key="quick_group_name", placeholder="例如：研发组、项目A组")
            if st.button("创建", key="quick_create_group", use_container_width=True):
                if quick_group_name.strip():
                    group_id = create_group(quick_group_name.strip())
                    st.session_state["selected_group_id"] = group_id
                    st.success(f"✅ 小组「{quick_group_name}」已创建！")
                    st.rerun()
                else:
                    st.warning("请输入小组名称")
        return

    # 计算每组成员数
    group_member_counts = {g["id"]: len(get_people_in_group(g["id"])) for g in groups}
    group_options = {g["id"]: f"📁 {g['name']} ({group_member_counts.get(g['id'], 0)}人)" for g in groups}

    current_group_id = st.session_state.get("selected_group_id")
    if current_group_id not in group_options:
        current_group_id = groups[0]["id"]
        st.session_state["selected_group_id"] = current_group_id

    selected_group_id = st.selectbox(
        "选择目标小组",
        options=list(group_options.keys()),
        format_func=lambda x: group_options[x],
        index=list(group_options.keys()).index(current_group_id) if current_group_id in group_options else 0,
        key="sidebar_group_select",
    )

    if selected_group_id != st.session_state.get("selected_group_id"):
        st.session_state["selected_group_id"] = selected_group_id

    st.caption("新添加的成员将加入此小组（已有成员会自动去重）")


def render_import_section(api_key: str):
    """渲染侧边栏导入区（文件上传 / 文本输入）"""
    st.subheader("📥 导入信息")

    if st.session_state.get("mode") == "multi":
        render_group_selector()
        st.markdown("---")

    tab1, tab2 = st.tabs(["📄 文件上传", "✍️ 文本输入"])

    # ===== Tab 1: 文件上传 =====
    with tab1:
        st.markdown("**支持格式：** CSV, Excel, PDF(简历)")

        uploaded_file = st.file_uploader(
            "上传个人信息表格",
            type=["csv", "xlsx", "xls", "pdf"],
            help="上传包含个人信息的表格文件，或 PDF 简历",
        )

        if uploaded_file is not None:
            try:
                filename = uploaded_file.name.lower()

                # ===== PDF：提取文本 -> AI 解析 -> 保存 =====
                if filename.endswith(".pdf"):
                    # 先检查 PDF 依赖
                    try:
                        import fitz  # PyMuPDF
                        pdf_dependency_ok = True
                        pdf_error_msg = None
                    except ImportError:
                        pdf_dependency_ok = False
                        pdf_error_msg = "缺少依赖：pymupdf"
                    except Exception as e:
                        pdf_dependency_ok = False
                        pdf_error_msg = f"PyMuPDF 导入失败：{str(e)}"
                    
                    if not pdf_dependency_ok:
                        st.error(f"❌ **PDF 导入功能不可用**\n\n{pdf_error_msg}\n\n")
                        st.info(
                            "**解决方案**：\n\n"
                            "1. 打开终端/命令行（Windows: Win+R → 输入 `cmd` → 回车）\n"
                            "2. 切换到项目目录：`cd 项目路径`\n"
                            "3. 运行安装命令：`pip install pymupdf`\n"
                            "4. 重启 Streamlit 应用\n\n"
                            "或安装所有依赖：`pip install -r requirements.txt`"
                        )
                        st.code("pip install pymupdf", language="bash")
                        st.stop()
                    
                    st.markdown("**PDF 简历导入：** 先提取文本（必要时 OCR），再交给 AI 结构化解析。")
                    
                    # 显示文件信息
                    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                    st.caption(f"📄 文件大小：{file_size_mb:.2f} MB")

                    ocr_enabled = st.checkbox(
                        "启用 OCR（扫描件/图片型 PDF 才需要）",
                        value=False,
                        help="若 PDF 是扫描件（复制不出文字），勾选后会在本地对前几页做 OCR，再交给 AI。",
                    )
                    ocr_pages = st.slider("OCR 页数（仅在启用 OCR 时生效）", 1, 8, 3)

                    if st.button("🤖 AI 解析简历并保存", key="analyze_pdf", type="primary", use_container_width=True):
                        if not api_key:
                            st.error("❌ 请先在上方输入 API Key")
                        else:
                            try:
                                with st.spinner("正在从 PDF 提取文本..."):
                                    pdf_bytes = uploaded_file.getvalue()
                                    
                                    # 验证 PDF 文件
                                    if len(pdf_bytes) == 0:
                                        st.error("❌ PDF 文件为空")
                                        st.stop()
                                    
                                    # 检查是否是有效的 PDF（前 4 个字节应该是 %PDF）
                                    if pdf_bytes[:4] != b'%PDF':
                                        st.error("❌ 不是有效的 PDF 文件（文件头不匹配）")
                                        st.info("请确保上传的是 PDF 格式文件")
                                        st.stop()
                                    
                                    result = extract_pdf_text(
                                        pdf_bytes,
                                        ocr_enabled=ocr_enabled,
                                        ocr_max_pages=int(ocr_pages),
                                    )
                            except RuntimeError as e:
                                error_msg = str(e)
                                st.error(f"❌ **PDF 处理失败**\n\n{error_msg}")
                                
                                # 诊断信息
                                with st.expander("🔍 诊断信息", expanded=True):
                                    st.code(f"错误类型：RuntimeError\n错误信息：{error_msg}", language="text")
                                    
                                    # 检查依赖
                                    try:
                                        import fitz
                                        st.success("✅ PyMuPDF 已安装")
                                        st.info(f"PyMuPDF 版本：{fitz.version}")
                                    except ImportError:
                                        st.error("❌ PyMuPDF 未安装")
                                    except Exception as e2:
                                        st.warning(f"⚠️ PyMuPDF 检查失败：{str(e2)}")
                                
                                st.info(
                                    "💡 **解决方案**：\n\n"
                                    "1. 打开终端/命令行（Windows: Win+R → 输入 `cmd` → 回车）\n"
                                    "2. 切换到项目目录\n"
                                    "3. 运行：`pip install pymupdf`\n"
                                    "4. 如果使用 OCR，还需运行：`pip install easyocr pillow numpy`\n"
                                    "5. 重启 Streamlit 应用\n\n"
                                    "或安装所有依赖：`pip install -r requirements.txt`"
                                )
                                st.code("pip install pymupdf", language="bash")
                                st.stop()
                            except Exception as e:
                                import traceback
                                st.error(f"❌ **PDF 处理出错**\n\n{str(e)}")
                                
                                with st.expander("🔍 详细错误信息（调试用）", expanded=False):
                                    st.code(traceback.format_exc(), language="python")
                                
                                st.info("如果问题持续，请检查：\n1. PDF 文件是否损坏\n2. 是否安装了所有依赖\n3. 查看上方的详细错误信息")
                                st.stop()

                            if not result.text or len(result.text) < 50:
                                st.warning("⚠️ PDF 提取到的文字太少。若是扫描件，请勾选 OCR；或将 PDF 另存为可复制文本的版本。")
                            else:
                                raw_text = result.text
                                with st.spinner("正在清洗和结构化文本..."):
                                    cleaned_text = clean_resume_text(raw_text)

                                st.caption(
                                    f"提取方式：{result.method}；页数：{result.page_count}；"
                                    f"原始字符数：{len(raw_text)}；清洗后字符数：{len(cleaned_text)}"
                                )

                                col_raw, col_clean = st.columns(2)
                                with col_raw:
                                    with st.expander("📄 原始提取文本"):
                                        st.text(raw_text[:1500] + ("..." if len(raw_text) > 1500 else ""))
                                with col_clean:
                                    with st.expander("✨ 清洗后文本（用于 AI 解析）", expanded=True):
                                        st.text(cleaned_text[:1500] + ("..." if len(cleaned_text) > 1500 else ""))

                                with st.spinner("🧠 AI 正在解析简历..."):
                                    profile, raw_content, err = analyze_text_with_ai(cleaned_text, api_key)

                                if err:
                                    st.error(err)
                                    if raw_content:
                                        with st.expander("查看 AI 原始返回（调试）"):
                                            st.code(raw_content, language="text")

                                if profile:
                                    if st.session_state.get("mode") == "single":
                                        person_id, is_new, err = save_self_profile(profile, "pdf_resume")
                                        if err:
                                            st.error(f"❌ {err}")
                                        else:
                                            st.success("✅ 简历解析完成，记忆已更新！")
                                            st.rerun()
                                    else:
                                        if add_profile_multi(profile, "pdf_resume", group_id=st.session_state.get("selected_group_id")):
                                            st.success("✅ 简历解析完成，已添加到多人列表！")
                                            st.rerun()

                # ===== CSV/Excel =====
                else:
                    with st.spinner("正在读取文件..."):
                        df = read_uploaded_file(uploaded_file)

                    st.markdown("**预览：**")
                    st.dataframe(df.head(3), use_container_width=True)
                    st.caption(f"共 {len(df)} 行, {len(df.columns)} 列")

                    if st.session_state.get("mode") == "single":
                        if st.button("💾 保存到记忆", key="save_file_single", type="primary", use_container_width=True):
                            data = df.to_dict(orient="records")
                            # 如果是单行，作为个人档案保存
                            if len(data) == 1:
                                person_id, is_new, err = save_self_profile(data[0], "file_upload")
                                if err:
                                    st.error(f"❌ {err}")
                                else:
                                    st.success("✅ 记忆已更新！")
                                    st.rerun()
                            else:
                                st.warning("⚠️ 个人版仅支持单行数据，请切换到多人版导入多行表格")
                    else:
                        st.markdown("---")
                        st.markdown("**多人版批量导入设置**")

                        name_col = None
                        possible_name_cols = ["姓名", "name", "Name", "姓", "名字"]
                        for col in df.columns:
                            if col in possible_name_cols:
                                name_col = col
                                break

                        if name_col and len(df) > 1:
                            st.info(f"📊 检测到多人表格（{len(df)} 行），将逐行导入并自动去重")
                            membership_field_cols = ["职位", "部门", "职称", "研究方向", "角色", "role", "position", "department"]
                            detected_ms_cols = [col for col in df.columns if col in membership_field_cols]
                            if detected_ms_cols:
                                st.caption(f"以下列将作为组内信息：{', '.join(detected_ms_cols)}")

                            # ===== 绩效/贡献导入选项 =====
                            from performance_models import (
                                detect_performance_col,
                                detect_contribution_cols,
                                parse_score,
                                parse_contributions_text,
                                build_import_event,
                            )
                            from store_org import set_person_base_score, add_performance_event

                            perf_col = detect_performance_col(df.columns.tolist())
                            contrib_col, contrib_score_col = detect_contribution_cols(df.columns.tolist())

                            st.markdown("---")
                            st.markdown("**📊 绩效与贡献导入**")

                            # 绩效导入策略
                            if perf_col:
                                st.caption(f"检测到绩效列：`{perf_col}`")
                                perf_strategy = st.radio(
                                    "绩效导入策略",
                                    ["ignore", "new_only", "overwrite"],
                                    format_func=lambda x: {
                                        "ignore": "忽略绩效列（新成员初始为 0）",
                                        "new_only": "仅新成员写入基准分",
                                        "overwrite": "覆盖基准分（并记录事件）",
                                    }[x],
                                    key="perf_import_strategy",
                                )
                            else:
                                st.caption("未检测到绩效列（新成员初始绩效为 0）")
                                perf_strategy = "ignore"

                            # 贡献导入
                            import_contributions = False
                            if contrib_col:
                                st.caption(f"检测到贡献列：`{contrib_col}`" + (f"，分值列：`{contrib_score_col}`" if contrib_score_col else ""))
                                import_contributions = st.checkbox("导入主要贡献", value=True, key="import_contributions")

                            st.markdown("---")

                            if st.button(
                                "💾 批量导入（逐行去重）",
                                key="save_file_multi_rows",
                                type="primary",
                                use_container_width=True,
                            ):
                                selected_group_id = st.session_state.get("selected_group_id")
                                if not selected_group_id:
                                    groups = load_groups()
                                    selected_group_id = create_group("默认小组") if not groups else groups[0]["id"]
                                    st.session_state["selected_group_id"] = selected_group_id

                                new_count = 0
                                update_count = 0

                                for _, row in df.iterrows():
                                    row_dict = row.to_dict()

                                    profile = {}
                                    for col, val in row_dict.items():
                                        if pd.notna(val):
                                            profile[col] = str(val) if not isinstance(val, str) else val

                                    ms_fields = {"source": "file_upload"}
                                    for col in detected_ms_cols:
                                        if col in profile and profile[col]:
                                            ms_fields[col] = profile[col]

                                    person_id, is_new = upsert_person(
                                        profile,
                                        "file_upload",
                                        group_id=selected_group_id,
                                        membership_fields=ms_fields,
                                    )
                                    if is_new:
                                        new_count += 1
                                    else:
                                        update_count += 1

                                    # 写入绩效（按策略）
                                    if person_id and perf_col and perf_strategy != "ignore":
                                        raw_score = parse_score(row_dict.get(perf_col))
                                        if raw_score is not None:
                                            if is_new or perf_strategy == "overwrite":
                                                set_person_base_score(person_id, raw_score)
                                                add_performance_event(
                                                    person_id,
                                                    build_import_event(raw_score, f"导入自列 [{perf_col}]"),
                                                )

                                    # 写入贡献
                                    if person_id and import_contributions and contrib_col:
                                        contrib_text = str(row_dict.get(contrib_col, ""))
                                        default_delta = 0.0
                                        if contrib_score_col:
                                            d = parse_score(row_dict.get(contrib_score_col))
                                            if d is not None:
                                                default_delta = d
                                        events = parse_contributions_text(contrib_text, default_delta)
                                        for ev in events:
                                            ev["group_id"] = selected_group_id
                                            add_performance_event(person_id, ev)

                                st.success(f"✅ 导入完成！新增 {new_count} 人，更新 {update_count} 人")
                                st.rerun()
                        else:
                            if st.button("💾 保存到记忆", key="save_file_multi_one", type="primary", use_container_width=True):
                                data = df.to_dict(orient="records")
                                payload = data[0] if len(data) == 1 else data
                                add_profile_multi(payload, "file_upload", group_id=st.session_state.get("selected_group_id"))
                                st.success("✅ 已添加到多人列表！")
                                st.rerun()

            except Exception as e:
                st.error(f"读取文件失败: {str(e)}")

    # ===== Tab 2: 文本输入 =====
    with tab2:
        st.markdown("**粘贴自我介绍，AI 自动分析**")

        intro_text = st.text_area(
            "自我介绍",
            height=200,
            placeholder="例如：\n我叫张三，毕业于北京大学计算机系...",
            help="输入一段关于自己的介绍，AI 会自动提取关键信息并给出发展建议",
        )

        if st.button("🤖 AI 分析并保存", key="analyze_text", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ 请先在上方输入 API Key")
            elif not intro_text or len(intro_text.strip()) < 10:
                st.warning("⚠️ 请输入至少 10 个字符的自我介绍")
            else:
                with st.spinner("🧠 AI 正在分析中..."):
                    profile, raw_content, err = analyze_text_with_ai(intro_text, api_key)

                if err:
                    st.error(err)
                    if raw_content:
                        with st.expander("查看 AI 原始返回（调试）"):
                            st.code(raw_content, language="text")

                if profile:
                    if st.session_state.get("mode") == "single":
                        person_id, is_new, err = save_self_profile(profile, "text_analysis")
                        if err:
                            st.error(f"❌ {err}")
                        else:
                            st.success("✅ 分析完成，记忆已更新！")
                            st.rerun()
                    else:
                        if add_profile_multi(profile, "text_analysis", group_id=st.session_state.get("selected_group_id")):
                            st.success("✅ 分析完成，已添加到多人列表！")
                            st.rerun()


def render_clear_memory_buttons():
    """清除存储数据按钮"""
    st.markdown("---")
    if st.session_state.get("mode") == "single":
        if single_profile_exists():
            if st.button("🗑️ 清除记忆", use_container_width=True):
                # 清除 self_config 绑定
                clear_self_person_id()
                # 清除 user_profile.json
                if delete_profile_single():
                    st.success("记忆已清除（仅解除个人版绑定，多人版数据保留）")
                    st.rerun()
                else:
                    st.error("清除失败：请检查文件权限或是否被占用")
    else:
        if org_store_exists():
            if st.button("🗑️ 清除所有小组和人员", use_container_width=True):
                # 同时清除 self_config 绑定
                clear_self_person_id()
                if delete_org_store_file():
                    st.session_state["selected_group_id"] = None
                    st.session_state["selected_person_id"] = None
                    st.success("所有小组和人员已清除")
                    st.rerun()
                else:
                    st.error("清除失败：请检查文件权限或是否被占用")

