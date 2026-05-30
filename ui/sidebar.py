"""Essay Grader — 侧边栏参数面板."""
import streamlit as st


def render_sidebar() -> dict:
    """渲染侧边栏输入面板，返回用户输入字典."""
    st.sidebar.header("📝 作文输入")

    essay_text = st.sidebar.text_area(
        "直接输入作文",
        height=300,
        placeholder="在此粘贴或输入作文内容...",
        key="essay_text",
    )

    essay_file = st.sidebar.file_uploader(
        "或上传文件",
        type=["txt", "docx", "pdf"],
        key="essay_file",
        help="支持 .txt / .docx / .pdf 格式",
    )

    st.sidebar.divider()
    st.sidebar.header("📎 背景信息（可选）")

    with st.sidebar.expander("展开背景信息"):
        background_text = st.text_area(
            "背景文字",
            placeholder="如：作文题目、阅读材料等",
            key="bg_text",
        )
        background_url = st.text_input(
            "参考链接",
            placeholder="https://...",
            key="bg_url",
        )
        background_file = st.file_uploader(
            "背景文件",
            type=["txt", "docx", "pdf", "png", "jpg", "jpeg"],
            key="bg_file",
        )

    return {
        "essay_text": essay_text,
        "essay_file": essay_file,
        "background_text": background_text,
        "background_url": background_url,
        "background_file": background_file,
    }
