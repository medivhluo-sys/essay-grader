"""Essay Grader — 批改结果展示."""
import streamlit as st
from exporter import export_html, export_docx

# 与 grading.py / exporter.py 保持一致的维度颜色
DIMENSION_COLORS = {
    "typos": ("#FF9800", "错别字"),
    "grammar": ("#E91E63", "语法"),
    "structure": ("#4CAF50", "结构"),
    "logic": ("#2196F3", "逻辑"),
    "technique": ("#9C27B0", "技巧"),
    "vocabulary": ("#FDD835", "词汇"),
}


def render_grading_result(original_text: str, result: dict) -> None:
    """渲染批改结果：统计、总评、双栏对照、导出."""
    annotations = result.get("annotations", [])

    # ---- 顶部统计 ----
    cols = st.columns(4)
    cols[0].metric("字数", result.get("word_count", 0))
    cols[1].metric("语言", "中文" if result.get("language") == "zh" else "英文")
    cols[2].metric("批注数", len(annotations))
    cols[3].metric("涉及维度", len({a["dimension"] for a in annotations}))

    st.divider()

    # ---- 总评 ----
    if result.get("overall_comment"):
        st.info(f"**总评**\n\n{result['overall_comment']}")

    # ---- 双栏对照 ----
    left, right = st.columns([3, 2])

    with left:
        st.subheader("📄 作文原文")
        highlighted = _build_highlighted_html(original_text, annotations)
        st.markdown(
            f'<div style="line-height:2;font-size:16px;">{highlighted}</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("💬 批注详情")
        all_dims = sorted({a["dimension"] for a in annotations})
        if all_dims:
            selected_dims = st.multiselect(
                "筛选维度",
                options=all_dims,
                default=all_dims,
                format_func=lambda d: DIMENSION_COLORS.get(d, ("#999", d))[1],
                key="dim_filter",
            )
            filtered = [a for a in annotations if a["dimension"] in selected_dims]

            for ann in filtered:
                color, label = DIMENSION_COLORS.get(
                    ann["dimension"], ("#999", ann["dimension"])
                )
                with st.container(border=True):
                    st.caption(f"🔹 **{label}** · {ann.get('location', '')}")
                    st.markdown(f"**问题**：{ann.get('issue', '')}")
                    st.markdown(f"**建议**：{ann.get('suggestion', '')}")
                    if ann.get("highlight_text"):
                        st.code(ann["highlight_text"], language=None)

    st.divider()

    # ---- 导出按钮 ----
    col_html, col_docx = st.columns(2)
    with col_html:
        html_data = export_html(original_text, result)
        st.download_button(
            "📥 导出 HTML 报告",
            data=html_data,
            file_name="essay_report.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_docx:
        docx_data = export_docx(original_text, result)
        st.download_button(
            "📥 导出 DOCX 报告",
            data=docx_data,
            file_name="essay_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )


def _build_highlighted_html(text: str, annotations: list) -> str:
    """构建带高亮标注的作文 HTML."""
    result = text
    # 按highlight_text长度倒序处理，避免短文本先替换导致长文本匹配失败
    for ann in sorted(
        annotations, key=lambda a: len(a.get("highlight_text", "")), reverse=True
    ):
        ht = ann.get("highlight_text", "")
        if ht and ht in result:
            color, _ = DIMENSION_COLORS.get(ann["dimension"], ("#999", ""))
            replacement = (
                f'<span style="background-color:{color}20;border-bottom:2px solid {color};'
                f'cursor:help" title="[{ann.get("dimension")}] {ann.get("issue", "")}">{ht}</span>'
            )
            result = result.replace(ht, replacement, 1)
    return result
