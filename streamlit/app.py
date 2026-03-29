import os
import time
from datetime import datetime

import streamlit as st
from langchain.schema import HumanMessage, SystemMessage

import config  # noqa: F401  (触发 load_dotenv)
from database import (
    create_conversation,
    delete_conversation,
    get_conversations,
    init_db,
    load_chat_history,
    save_chat,
    save_feedback,
    update_conversation_title,
)
from llm import build_chat_messages, generate_conversation_title, init_llm
from retrieval import QARetrievalSystem
from styles import CUSTOM_CSS
from utils import (
    generate_conversation_id,
    load_prompt_template,
    parse_think_content,
    render_message,
)


def render_sidebar():
    """侧边栏：新建对话 + 历史会话列表"""
    with st.sidebar:
        if st.button("➕ 新建对话", use_container_width=True, type="primary"):
            new_id = generate_conversation_id()
            create_conversation(new_id)
            st.session_state.conversation_id = new_id
            st.session_state.messages = []
            st.session_state.title_generated = False
            st.rerun()

        st.markdown("---")
        st.markdown("##### 对话历史")

        for conv_id, title, updated_at in get_conversations():
            is_active = conv_id == st.session_state.conversation_id
            date_str = updated_at[:10] if updated_at else ""

            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                label = f"{'▶ ' if is_active else ''}{title}"
                if st.button(label, key=f"conv_{conv_id}", use_container_width=True,
                             disabled=is_active):
                    st.session_state.conversation_id = conv_id
                    st.session_state.messages = []
                    for rec in load_chat_history(50, conv_id):
                        st.session_state.messages.append({
                            "id": rec[0], "role": rec[2], "content": rec[3],
                            "timestamp": rec[1][11:19], "response_time": rec[4],
                        })
                    st.session_state.title_generated = True
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{conv_id}", help="删除此对话"):
                    delete_conversation(conv_id)
                    if conv_id == st.session_state.conversation_id:
                        new_id = generate_conversation_id()
                        create_conversation(new_id)
                        st.session_state.conversation_id = new_id
                        st.session_state.messages = []
                        st.session_state.title_generated = False
                    st.rerun()

            if not is_active:
                st.caption(f"　{date_str}")


def render_history():
    """渲染历史消息列表"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            render_message(message["content"])

            col1, col2 = st.columns([4, 1])
            with col1:
                if "timestamp" in message:
                    st.caption(message["timestamp"])
            with col2:
                if message["role"] == "assistant" and "response_time" in message:
                    st.caption(f"⏱️ {message['response_time']:.2f}s")

            if message["role"] == "assistant":
                fb1, fb2 = st.columns(2)
                with fb1:
                    if st.button("👍 有帮助", key=f"like_{message['id']}", use_container_width=True):
                        save_feedback(message["id"], 1)
                        st.success("感谢您的反馈!")
                with fb2:
                    if st.button("👎 无帮助", key=f"dislike_{message['id']}", use_container_width=True):
                        fb = st.text_input("请告诉我们如何改进", key=f"fb_{message['id']}")
                        if fb:
                            save_feedback(message["id"], 0, fb)
                            st.success("感谢您的反馈!")


def handle_user_input(retrieval_system: QARetrievalSystem):
    """处理用户输入、RAG 检索、流式 AI 回复"""
    prompt = st.chat_input("请输入您的问题...")
    if not prompt:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    user_msg_id = save_chat("user", prompt, conversation_id=st.session_state.conversation_id)

    # RAG 检索
    results = retrieval_system.search(prompt, top_n=5, threshold=0.1)
    retrieval_text = "\n".join(
        f"  {i+1}. 问题：{r['question']}\n    答案：{r['answer']}\n    来源：{r['source'].split(os.sep)[-1]}"
        for i, r in enumerate(results)
    )
    final_prompt = load_prompt_template().format(prompt=prompt, retrieval_results=retrieval_text)

    st.session_state.messages.append({
        "id": user_msg_id, "role": "user", "content": prompt, "timestamp": timestamp,
    })

    with st.chat_message("user"):
        render_message(prompt)
        st.caption(timestamp)

    # 构建上下文（最近 3 轮）
    context = []
    for msg in st.session_state.messages[-6:]:
        cls = HumanMessage if msg["role"] == "user" else SystemMessage
        context.append(cls(content=msg["content"]))

    # 流式输出
    with st.chat_message("assistant"):
        think_ph = st.empty()
        answer_ph = st.empty()
        time_ph = st.empty()

        full_response = ""
        start_time = time.time()
        llm = init_llm(streaming=True)

        for chunk in llm.stream(build_chat_messages(final_prompt, context)):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if not token:
                continue
            full_response += token

            if "<think>" in full_response and "</think>" not in full_response:
                think_ph.markdown("💭 *思考中...*")
            elif "</think>" in full_response:
                think_ph.markdown("💭 *思考完成*")
                answer_ph.markdown(full_response.split("</think>", 1)[1].strip() + "▌")
            else:
                answer_ph.markdown(full_response + "▌")

        response_time = time.time() - start_time
        _, answer_text = parse_think_content(full_response)
        think_ph.empty()
        answer_ph.markdown(answer_text)

        timestamp = datetime.now().strftime("%H:%M:%S")
        c1, c2 = time_ph.columns([4, 1])
        c1.caption(timestamp)
        c2.caption(f"⏱️ {response_time:.2f}s")

    # 持久化
    ai_msg_id = save_chat("assistant", full_response, response_time,
                          st.session_state.conversation_id)
    st.session_state.messages.append({
        "id": ai_msg_id, "role": "assistant", "content": full_response,
        "timestamp": timestamp, "response_time": response_time,
    })

    # 首次对话后自动生成标题
    if not st.session_state.get("title_generated", False):
        _, clean = parse_think_content(full_response)
        title = generate_conversation_title(prompt, clean)
        update_conversation_title(st.session_state.conversation_id, title)
        st.session_state.title_generated = True

    st.rerun()


def main():
    init_db()

    st.set_page_config(
        page_title="💬RAG问答系统", page_icon="🤖",
        layout="wide", initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
        new_id = generate_conversation_id()
        create_conversation(new_id)
        st.session_state.conversation_id = new_id
        st.session_state.show_feedback = {}
        st.session_state.title_generated = False

    render_sidebar()

    st.title("💬 RAG问答系统")
    render_history()
    handle_user_input(retrieval_system)


if __name__ == "__main__":
    retrieval_system = QARetrievalSystem()
    retrieval_system.load_qa_pairs()
    main()
