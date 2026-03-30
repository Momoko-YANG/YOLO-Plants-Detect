import os

from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ui.components import parse_think_content


def init_llm(streaming=False):
    return ChatOpenAI(
        openai_api_key=os.getenv("LLM_API_KEY", ""),
        openai_api_base=os.getenv("LLM_API_BASE", ""),
        model_name=os.getenv("LLM_MODEL", ""),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
        streaming=streaming,
    )


def build_chat_messages(question, conversation_context=None):
    messages = [
        SystemMessage(content="你是一个专家，请用中文回答用户的问题。回答要专业、详细且友好。")
    ]
    if conversation_context:
        messages.extend(conversation_context)
    messages.append(HumanMessage(content=question))
    return messages


def generate_conversation_title(first_user_msg, first_ai_msg):
    """用 LLM 生成 <=12 字的简短会话标题"""
    try:
        llm = ChatOpenAI(
            openai_api_key=os.getenv("LLM_API_KEY", ""),
            openai_api_base=os.getenv("LLM_API_BASE", ""),
            model_name=os.getenv("LLM_MODEL", ""),
            temperature=0.3,
            max_tokens=30,
        )
        resp = llm.invoke([
            SystemMessage(content="根据以下对话生成一个简短的中文标题（不超过12个字，不要加标点符号和引号，直接输出标题）"),
            HumanMessage(content=f"用户：{first_user_msg}\n助手：{first_ai_msg[:200]}"),
        ])
        _, title = parse_think_content(resp.content)
        return title.strip().strip('"\'""「」【】') or first_user_msg[:15]
    except Exception:
        return first_user_msg[:15] or "新对话"
