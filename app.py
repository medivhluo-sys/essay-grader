"""Essay Grader — Streamlit 应用入口.

启动: streamlit run app.py --server.port 8505
"""
import hashlib
import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---- 访问密码验证 ----
# 本地开发：在 .streamlit/secrets.toml 中设置 APP_PASSWORD = "你的密码"
# 云端部署：在 Streamlit Cloud → Settings → Secrets 中设置
try:
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
except Exception:
    APP_PASSWORD = os.getenv("APP_PASSWORD", "")


def check_password():
    """验证访问密码，防止他人消耗 API Token."""

    if APP_PASSWORD and not st.session_state.get("authenticated"):
        st.title("📝 作文批改助手")
        st.caption("支持中英文作文 · DeepSeek AI 批改 · HTML/DOCX 报告导出")

        pwd = st.text_input(
            "请输入访问密码",
            type="password",
            placeholder="输入密码后按 Enter",
            key="pwd_input",
        )
        if pwd:
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误")
        st.stop()


check_password()
# ---- 密码验证结束 ----

from doc_parser import extract_text
from grading import grade_essay
from context_collector import collect_background
from ui.sidebar import render_sidebar
from ui.results import render_grading_result

st.set_page_config(page_title="作文批改助手", page_icon="📝", layout="wide")

st.title("📝 作文批改助手")
st.caption("支持中英文作文 · DeepSeek AI 批改 · HTML/DOCX 报告导出")

params = render_sidebar()

# 状态管理：参照 bidding-calculator 的 params-hash 缓存模式
params_hash = json.dumps(params, sort_keys=True, default=str)
if "params_hash" not in st.session_state:
    st.session_state.params_hash = None
if "grading_result" not in st.session_state:
    st.session_state.grading_result = None

params_changed = st.session_state.params_hash != params_hash

run_button = st.sidebar.button("🚀 开始批改", type="primary", use_container_width=True)

if run_button or (st.session_state.grading_result is not None and not params_changed):
    if st.session_state.grading_result is None or params_changed:
        # ---- 解析作文输入 ----
        essay_text = (params["essay_text"] or "").strip()
        if params["essay_file"] is not None:
            try:
                essay_text = extract_text(
                    params["essay_file"].name, params["essay_file"].read()
                )
            except ValueError as e:
                st.error(f"文件解析失败：{e}")
                st.stop()

        if not essay_text:
            st.warning("请输入作文内容或上传文件")
            st.stop()
        if len(essay_text) < 20:
            st.error("作文太短，至少需要 20 个字")
            st.stop()
        if len(essay_text) > 10000:
            st.error("作文过长（超过 10000 字），请精简内容")
            st.stop()

        # ---- 收集背景信息 ----
        background = None
        bg_file_tuple = None
        if params["background_file"] is not None:
            bg_file_tuple = (
                params["background_file"].name,
                params["background_file"].read(),
            )

        if (
            params["background_text"]
            or params["background_url"]
            or bg_file_tuple
        ):
            with st.spinner("正在处理背景信息..."):
                try:
                    background = collect_background(
                        background_text=params["background_text"],
                        background_url=params["background_url"],
                        background_file=bg_file_tuple,
                    )
                except ValueError as e:
                    st.error(f"背景信息处理失败：{e}")
                    st.stop()

        # ---- AI 批改 ----
        with st.spinner("AI 正在批改中，请稍候..."):
            try:
                result = grade_essay(essay_text, background=background)
                result["original_text"] = essay_text
            except RuntimeError as e:
                st.error(f"批改失败：{e}")
                st.stop()

        st.session_state.grading_result = result
        st.session_state.params_hash = params_hash

    render_grading_result(
        st.session_state.grading_result["original_text"],
        st.session_state.grading_result,
    )
else:
    st.info("👈 在左侧输入作文内容（直接输入或上传文件），点击「开始批改」")
