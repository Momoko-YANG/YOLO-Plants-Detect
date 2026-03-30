"""
RAG + LLM 智能问答系统 — Streamlit 入口
运行: streamlit run main.py
"""
import os
import time
from datetime import datetime, timedelta

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage

from config import BASE_DIR
from core.database import (
    init_db,
    create_conversation,
    update_conversation_title,
    delete_conversation,
    get_conversations,
    save_chat,
    save_feedback,
    load_chat_history,
)
from core.llm import init_llm, generate_conversation_title
from core.retrieval import get_retrieval_system
from ui.styles import CUSTOM_CSS
from ui.components import (
    parse_think_content,
    render_message,
    generate_conversation_id,
    load_prompt_template,
)

# ── 页面配置 ──────────────────────────────────────────────
st.set_page_config(
    page_title="RAG问答系统",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── 初始化 ────────────────────────────────────────────────
init_db()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = generate_conversation_id()
    create_conversation(st.session_state.conversation_id)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = {}


# ── 侧边栏：会话管理 ─────────────────────────────────────
def _date_group(updated_at: str) -> str:
    """将更新时间归入 今天 / 昨天 / 最近7天 / 更早"""
    try:
        dt = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return "更早"
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if dt >= today:
        return "今天"
    if dt >= today - timedelta(days=1):
        return "昨天"
    if dt >= today - timedelta(days=7):
        return "最近7天"
    return "更早"


def render_sidebar():
    with st.sidebar:
        if st.button("＋ 新建对话", use_container_width=True):
            st.session_state.conversation_id = generate_conversation_id()
            create_conversation(st.session_state.conversation_id)
            st.session_state.messages = []
            st.rerun()

        conversations = get_conversations()
        grouped: dict[str, list] = {}
        for cid, title, updated_at in conversations:
            grouped.setdefault(_date_group(updated_at), []).append((cid, title))

        for label in ["今天", "昨天", "最近7天", "更早"]:
            items = grouped.get(label)
            if not items:
                continue
            st.markdown(f'<p class="sidebar-group-label">{label}</p>', unsafe_allow_html=True)
            for cid, title in items:
                col_title, col_del = st.columns([8, 1])
                is_active = cid == st.session_state.conversation_id
                with col_title:
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(title or "新对话", key=f"conv_{cid}", use_container_width=True, type=btn_type):
                        if not is_active:
                            st.session_state.conversation_id = cid
                            st.session_state.messages = []
                            history = load_chat_history(50, cid)
                            for record in history:
                                st.session_state.messages.append({
                                    "id": record[0],
                                    "role": record[2],
                                    "content": record[3],
                                    "timestamp": record[1][11:19] if record[1] else "",
                                    "response_time": record[4],
                                })
                            st.rerun()
                with col_del:
                    if st.button("×", key=f"del_{cid}"):
                        delete_conversation(cid)
                        if is_active:
                            st.session_state.conversation_id = generate_conversation_id()
                            create_conversation(st.session_state.conversation_id)
                            st.session_state.messages = []
                        st.rerun()


render_sidebar()

# ── 页面标题 ──────────────────────────────────────────────
st.title("💬 RAG问答系统")


# ── 聊天历史渲染 ──────────────────────────────────────────
def render_history():
    # 空对话欢迎语
    if not st.session_state.messages:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem 1rem; color:#888;">
                <h3 style="color:#555;">👋 你好，欢迎使用 RAG 问答系统</h3>
                <p>我是基于知识库的智能助手，可以回答关于作物病虫害的相关问题。</p>
                <p style="font-size:0.85rem;">在下方输入框中输入您的问题，即可开始对话。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            render_message(msg["content"])
            # 底部信息栏
            col1, col2 = st.columns([4, 1])
            with col1:
                if msg.get("timestamp"):
                    st.caption(msg["timestamp"])
            with col2:
                if msg["role"] == "assistant" and msg.get("response_time"):
                    st.caption(f"⏱️ {msg['response_time']:.2f}s")
            # 反馈按钮（仅 assistant）
            if msg["role"] == "assistant":
                fb1, fb2 = st.columns(2)
                with fb1:
                    if st.button("👍 有帮助", key=f"like_{msg['id']}", use_container_width=True):
                        save_feedback(msg["id"], 1)
                        st.success("感谢您的反馈!")
                with fb2:
                    if st.button("👎 无帮助", key=f"dislike_{msg['id']}", use_container_width=True):
                        fb = st.text_input("请告诉我们如何改进", key=f"fb_{msg['id']}")
                        if fb:
                            save_feedback(msg["id"], 0, fb)
                            st.success("感谢您的反馈!")


render_history()


# ── 用户输入 & RAG + LLM 流式响应 ─────────────────────────
def handle_user_input():
    prompt = st.chat_input("请输入您的问题...")
    if not prompt:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    conv_id = st.session_state.conversation_id

    # 保存用户消息
    user_msg_id = save_chat("user", prompt, conversation_id=conv_id)
    st.session_state.messages.append({
        "id": user_msg_id, "role": "user", "content": prompt, "timestamp": timestamp,
    })
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(timestamp)

    # RAG 检索
    retrieval_system = get_retrieval_system()
    results = retrieval_system.search(prompt, top_n=5, threshold=0.1)
    retrieval_results = "\n".join(
        f"  {i+1}. 问题：{r['question']}\n    答案：{r['answer']}\n    来源：{r['source'].split(os.sep)[-1]}"
        for i, r in enumerate(results)
    )

    # 构建最终 prompt
    prompt_template = load_prompt_template()
    final_prompt = prompt_template.format(prompt=prompt, retrieval_results=retrieval_results)

    # 对话上下文（最近几轮）
    context = []
    for msg in st.session_state.messages[-6:]:
        if msg["role"] == "user":
            context.append(HumanMessage(content=msg["content"]))
        else:
            context.append(SystemMessage(content=msg["content"]))

    # 构建消息列表
    messages = [
        SystemMessage(content="你是一个专家，请用中文回答用户的问题。回答要专业、详细且友好。"),
        *context,
        HumanMessage(content=final_prompt),
    ]

    # 流式响应
    llm = init_llm(streaming=True)
    start = time.time()
    full_response = ""

    with st.chat_message("assistant"):
        placeholder = st.empty()
        for chunk in llm.stream(messages):
            full_response += chunk.content
            _, display_text = parse_think_content(full_response)
            placeholder.markdown(display_text + "▌")
        response_time = time.time() - start

        # 最终渲染（含思考折叠）
        placeholder.empty()
        render_message(full_response)

        cols = st.columns([4, 1])
        with cols[0]:
            st.caption(datetime.now().strftime("%H:%M:%S"))
        with cols[1]:
            st.caption(f"⏱️ {response_time:.2f}s")

    # 保存到数据库
    ai_msg_id = save_chat("assistant", full_response, response_time, conv_id)
    st.session_state.messages.append({
        "id": ai_msg_id,
        "role": "assistant",
        "content": full_response,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "response_time": response_time,
    })

    # 首条消息时自动生成标题
    if len(st.session_state.messages) == 2:
        _, answer = parse_think_content(full_response)
        title = generate_conversation_title(prompt, answer)
        update_conversation_title(conv_id, title)


handle_user_input()
