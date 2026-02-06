"""
Digital Twin (数字分身) - Streamlit App Entry
=============================================
保持入口文件"轻薄"：仅负责页面编排与路由。
业务逻辑分别放在：
- ui_sidebar.py / ui_import.py：侧边栏（模式/API/导入/清除）
- ui_data_management.py：数据管理页（个人/多人）
- smart_form_filler.py：智能填表
- research_extension.py：科研表单
"""

from __future__ import annotations

import streamlit as st

# Streamlit 页面配置必须尽早调用（在任何 st.* 输出之前）
st.set_page_config(page_title="Digital Twin - 数字分身", page_icon="🧠", layout="wide")

from ui_state import init_session_state  # noqa: E402
from ui_sidebar import render_sidebar  # noqa: E402
from ui_data_management import render_data_management  # noqa: E402


def _check_pdf_dependencies():
    """检查 PDF 处理所需的依赖"""
    try:
        import fitz  # PyMuPDF
        return True, None
    except ImportError:
        return False, "pymupdf"
    except Exception as e:
        return False, f"pymupdf (错误: {str(e)})"


def main():
    # 初始化 session_state
    init_session_state()
    
    # 检查 PDF 依赖（仅在首次运行时显示）
    if "pdf_dependency_checked" not in st.session_state:
        pdf_ok, pdf_error = _check_pdf_dependencies()
        if not pdf_ok:
            st.warning(
                f"⚠️ **PDF 导入功能不可用**：缺少依赖 `{pdf_error}`\n\n"
                "**解决方案**：\n"
                "1. 打开终端/命令行\n"
                "2. 运行：`pip install pymupdf`\n"
                "3. 重启应用\n\n"
                "或安装所有依赖：`pip install -r requirements.txt`"
            )
        st.session_state["pdf_dependency_checked"] = True

    # 侧边栏（模式/API/导入/清除）
    api_key = render_sidebar()

    # 主区域
    st.title("🧠 Digital Twin - 数字分身")

    mode_labels = {"single": "👤 个人版", "multi": "👥 多人版"}
    mode_label = mode_labels.get(st.session_state.get("mode", "single"), "👤 个人版")
    st.markdown(f"**当前用户模式：** {mode_label}")

    func_tab1, func_tab2, func_tab3 = st.tabs(["📋 数据管理", "🪄 智能填表", "📚 科研表单"])

    with func_tab1:
        st.markdown("---")
        render_data_management()

    with func_tab2:
        st.markdown("---")
        from smart_form_filler import render_smart_form_filler

        render_smart_form_filler(api_key)

    with func_tab3:
        st.markdown("---")
        from research_extension import render_research_mode

        render_research_mode()


if __name__ == "__main__":
    main()
