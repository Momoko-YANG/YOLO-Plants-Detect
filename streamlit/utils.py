import os
import re
import random
from datetime import datetime

import streamlit as st

from config import PROMPT_FILE


def parse_think_content(text: str):
    """将 <think>...</think> 部分从回答中分离，返回 (think_text, answer_text)"""
    pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)
    thinks = pattern.findall(text)
    answer = pattern.sub("", text).strip()
    think_text = "\n\n".join(t.strip() for t in thinks if t.strip())
    return think_text, answer


def render_message(content: str):
    """渲染一条消息：think 块折叠，正文正常显示"""
    think_text, answer_text = parse_think_content(content)
    if think_text:
        with st.expander("💭 思考过程", expanded=False):
            st.markdown(think_text)
    if answer_text:
        st.markdown(answer_text)


def generate_conversation_id():
    return f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"


def load_prompt_template():
    default_prompt = """你是一个专家，需要回答学生的问题，具体要求如下：
1. 优先参考检索到的知识库内容（按相似度从高到低排列），若能直接回答问题，必须严格引用相关内容，并在回答末尾用**明确的引用格式**标注来源（格式：`参考来源：[文件名+工作表]，例如：知识库.xlsx[Sheet1]`）。
2. 若引用多个来源，用顿号分隔（例如：`参考来源：知识库.xlsx[Sheet1]`）。
3. 引用时需保留知识的核心信息，但可根据问题语境调整表述方式，确保逻辑连贯。
4. 若检索到的知识无法回答问题，仅用自身知识回答，无需标注来源。
5. 回答需使用Markdown格式（可适当使用加粗、列表等），语言简洁易懂，与学生问题自然衔接。
以下是学生问题及检索到的知识（按相关性排序）：
- 学生问题：{prompt}
- 检索到的知识：
{retrieval_results}""".strip()

    path = str(PROMPT_FILE)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(default_prompt)
        return default_prompt
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return default_prompt
