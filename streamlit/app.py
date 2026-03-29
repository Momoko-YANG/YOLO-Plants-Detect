import streamlit as st
import sqlite3
import time
import random
import json
import os
import jieba
import numpy as np
import pandas as pd

from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# 初始化大语言模型
def init_llm():
    return ChatOpenAI(
        openai_api_key="661e5d5a-8513-4329-8cea-7659345f6d03",
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
        model_name="deepseek-v3-1-terminus",
        temperature=0.7,
        max_tokens=1000
    )

class QARetrievalSystem:
    def __init__(self, qa_dir=None):  # 修改默认值为None，后续会自动替换为当前文件目录
        """初始化QA检索系统"""
        # 获取当前文件所在的目录路径
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 如果未指定qa_dir，默认使用当前文件目录；否则使用传入的路径（基于当前文件目录拼接）
        if qa_dir is None:
            self.qa_dir = current_file_dir
        else:
            self.qa_dir = os.path.join(current_file_dir, qa_dir)
        
        print(f"QA目录路径: {self.qa_dir}")

        self.qa_pairs = []
        self.questions = []
        self.vectorizer = TfidfVectorizer(tokenizer=self.tokenize)

    def tokenize(self, text):
        """使用jieba进行中文分词并过滤停用词"""
        # 进行分词
        tokens = jieba.cut(text)
        # 过滤停用词和空字符
        filtered_tokens = [token for token in tokens if token.strip()]
        return filtered_tokens

    def load_qa_pairs(self):
        """从本地加载QA对"""
        if not os.path.exists(self.qa_dir):
            print(f"QA目录 {self.qa_dir} 不存在")
            return False

        for file_name in os.listdir(self.qa_dir):
            if file_name.endswith(('.xlsx')):
                file_path = os.path.join(self.qa_dir, file_name)
                self._load_file(file_path)

        if not self.qa_pairs:
            print("未加载到任何QA对")
            return False

        self.questions = [qa["question"] for qa in self.qa_pairs]
        self._build_index()
        return True

    def _load_file(self, file_path):
        """加载单个文件中的QA对，增强xlsx文件支持"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.xlsx':
            self._load_xlsx_file(file_path)  # 单独处理xlsx文件

    def _load_xlsx_file(self, file_path):
        """专门处理xlsx文件，支持多工作表和灵活列名"""
        try:
            # 读取xlsx文件
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            for sheet_name in sheet_names:
                df = excel_file.parse(sheet_name)

                # 自动检测问题和答案列
                question_col = None
                answer_col = None

                # 检查常见列名
                for col in df.columns:
                    if 'question' in col.lower() or '问题' in col or 'query' in col.lower():
                        question_col = col
                    if 'answer' in col.lower() or '答案' in col:
                        answer_col = col

                # 如果找到问题和答案列
                if question_col and answer_col:
                    for _, row in df.iterrows():
                        question = str(row[question_col]).strip()
                        answer = str(row[answer_col]).strip()
                        if question:
                            self.qa_pairs.append({
                                "question": question,
                                "answer": answer,
                                "source": f"{file_path}[{sheet_name}]"
                            })
                else:
                    print(f"在xlsx文件 {file_path} 的 {sheet_name} 工作表中未找到问题和答案列")

        except Exception as e:
            print(f"加载xlsx文件 {file_path} 出错: {e}")

    def _build_index(self):
        """构建TF-IDF索引"""
        if self.questions:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

    def search(self, user_question, top_n=5, threshold=0.1):
        """搜索相关问题"""
        if not self.questions:
            print("没有可搜索的QA对")
            return []

        # 转换用户问题为TF-IDF向量
        user_tfidf = self.vectorizer.transform([user_question])

        # 计算余弦相似度
        similarities = cosine_similarity(user_tfidf, self.tfidf_matrix)[0]

        # 获取相似度最高的top_n个问题
        related_indices = np.argsort(similarities)[::-1][:top_n]

        # 过滤低于阈值的结果
        results = []
        for idx in related_indices:
            if similarities[idx] >= threshold:
                results.append({
                    "question": self.qa_pairs[idx]["question"],
                    "answer": self.qa_pairs[idx]["answer"],
                    "similarity": similarities[idx],
                    "source": self.qa_pairs[idx]["source"]
                })

        return results


# 初始化数据库
def init_db():
    conn = sqlite3.connect('chat_system.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            content TEXT,
            response_time REAL,
            conversation_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            message_id INTEGER,
            rating INTEGER,
            feedback TEXT,
            FOREIGN KEY(message_id) REFERENCES chat_history(id)
        )
    ''')
    conn.commit()
    conn.close()

# 保存聊天记录
def save_chat(role, content, response_time=None, conversation_id=None):
    conn = sqlite3.connect('chat_system.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO chat_history (timestamp, role, content, response_time, conversation_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, content, response_time, conversation_id))
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

# 保存用户反馈
def save_feedback(message_id, rating, feedback=None):
    conn = sqlite3.connect('chat_system.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_feedback (timestamp, message_id, rating, feedback)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message_id, rating, feedback))
    conn.commit()
    conn.close()

# 加载聊天历史
def load_chat_history(limit=20, conversation_id=None):
    conn = sqlite3.connect('chat_system.db')
    c = conn.cursor()
    
    if conversation_id:
        c.execute('''
            SELECT id, timestamp, role, content, response_time 
            FROM chat_history 
            WHERE conversation_id = ?
            ORDER BY timestamp ASC 
            LIMIT ?
        ''', (conversation_id, limit))
    else:
        c.execute('''
            SELECT id, timestamp, role, content, response_time 
            FROM chat_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
    history = c.fetchall()
    conn.close()
    return history

# 获取所有会话ID
def get_conversation_ids():
    conn = sqlite3.connect('chat_system.db')
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT conversation_id 
        FROM chat_history 
        WHERE conversation_id IS NOT NULL
        ORDER BY timestamp DESC
    ''')
    conversations = c.fetchall()
    conn.close()
    return [conv[0] for conv in conversations]

# 获取AI回答
def get_ai_response(question, conversation_context=None):
    llm = init_llm()
    start_time = time.time()
    
    messages = [
        SystemMessage(content="你是一个专家，请用中文回答用户的问题。回答要专业、详细且友好。")
    ]
    
    if conversation_context:
        messages.extend(conversation_context)
    
    messages.append(HumanMessage(content=question))
    
    response = llm(messages)
    end_time = time.time()
    
    return response.content, end_time - start_time

# 生成随机会话ID
def generate_conversation_id():
    return f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

# 读取prompt模板文件
def load_prompt_template(file_path="prompt.txt"):
    """
    从指定文件读取prompt模板
    如果文件不存在，创建默认模板并返回
    """
    default_prompt = """
        你是一个专家，需要回答学生的问题，具体要求如下：
        1. 优先参考检索到的知识库内容（按相似度从高到低排列），若能直接回答问题，必须严格引用相关内容，并在回答末尾用**明确的引用格式**标注来源（格式：`参考来源：[文件名+工作表]，例如：知识库.xlsx[Sheet1]`）。
        2. 若引用多个来源，用顿号分隔（例如：`参考来源：知识库.xlsx[Sheet1]`）。
        3. 引用时需保留知识的核心信息，但可根据问题语境调整表述方式，确保逻辑连贯。
        4. 若检索到的知识无法回答问题，仅用自身知识回答，无需标注来源。
        5. 回答需使用Markdown格式（可适当使用加粗、列表等），语言简洁易懂，与学生问题自然衔接。
        以下是学生问题及检索到的知识（按相关性排序）：
        - 学生问题：{prompt}
        - 检索到的知识：
        {retrieval_results}
    """.strip()
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 创建默认模板文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(default_prompt)
        print(f"已创建默认prompt模板文件：{file_path}")
        return default_prompt
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"读取prompt文件失败，使用默认模板：{e}")
        return default_prompt

# 主应用
def main():
    # 初始化数据库
    init_db()
    
    # 设置页面配置为宽屏模式
    st.set_page_config(
        page_title="💬RAG问答系统",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 应用绿植问答系统的样式（核心替换部分）
    st.markdown("""
        <style>
            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 3rem;  /* 从8rem减到3rem：减少底部预留空间，让输入框上移 */
                max-width: 1100px;     /* 限制最大宽度，避免过宽导致阅读困难 */
            }
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
                padding: 1rem;
            }
            /* 修复输入框边框溢出问题 */
            .stChatInput {
                padding: 0 !important;  /* 移除容器内边距，避免叠加导致溢出 */
                box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
                margin-top: 0.5rem;    /* 从2rem减到0.5rem：大幅拉近与上文内容的距离 */
                border-radius: 8px;
                background-color: #ffffff;
                overflow: hidden;  /* 隐藏超出容器的内容 */
            }

            /* 调整输入框本身样式 */
            [data-testid="stChatInputTextArea"] {
                border-radius: 8px !important;
                padding: 0.8rem 1rem !important;
                border: 1px solid #ddd !important;
                box-sizing: border-box !important;  /* 确保边框包含在元素尺寸内 */
                width: calc(100% - 40px) !important;  /* 预留发送按钮空间 */
                margin: 0 !important;  /* 移除默认外边距 */
            }

            /* 发送按钮样式调整 */
            [data-testid="stChatInputSubmitButton"] {
                box-sizing: border-box !important;
                height: 100% !important;
                margin: 0 !important;
                border-radius: 0 8px 8px 0 !important;  /* 与容器右侧圆角匹配 */
            }
            .stChatMessage {
                padding: 12px 16px;
                border-radius: 18px;
                margin: 8px 0;
                max-width: 80%;  /* 适当放宽最大宽度 */
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            [data-testid="stChatMessage-user"] {
                margin-left: auto;
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
            }
            [data-testid="stChatMessage-assistant"] {
                margin-right: auto;
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
            }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            /* 修复反馈按钮布局 */
            .feedback-buttons {
                margin-top: 0.5rem;
                display: flex;
                gap: 0.5rem;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.conversation_id = generate_conversation_id()
        st.session_state.show_feedback = {}
    
    # 侧边栏 - 会话管理和设置（保留原有逻辑，应用新样式）
    with st.sidebar:
        st.title("会话管理")
        
        # 会话选择器
        conversations = get_conversation_ids()
        selected_conversation = st.selectbox(
            "选择历史会话",
            options=conversations,
            index=0 if not conversations or st.session_state.conversation_id not in conversations 
                  else conversations.index(st.session_state.conversation_id),
            placeholder="选择一个会话"
        )
        
        # 优化侧边栏按钮布局（应用绿植系统的双列样式）
        col1, col2 = st.columns(2)
        with col1:
            if st.button("加载会话"):
                if selected_conversation:
                    st.session_state.conversation_id = selected_conversation
                    st.session_state.messages = []
                    db_history = load_chat_history(50, selected_conversation)
                    for record in db_history:
                        st.session_state.messages.append({
                            "id": record[0],
                            "role": record[2],
                            "content": record[3],
                            "timestamp": record[1][11:19],  # 只显示时间部分
                            "response_time": record[4]
                        })
                    st.rerun()
        
        with col2:
            if st.button("新建会话"):
                st.session_state.conversation_id = generate_conversation_id()
                st.session_state.messages = []
                st.rerun()

        # 清除历史记录（应用primary按钮样式）
        if st.button("清除当前会话", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
           
        st.markdown("---")
        st.title("帮助")
        st.info("""
            这是一个基于于LangChain + DeepSeek AI的智能聊天系统。  
            您可以:  
            - 输入问题获取AI回答  
            - 管理多个会话  
            - 对回答进行反馈  
        """)
    
    # 主聊天区域
    st.title("💬 RAG问答系统")
    st.caption(f"当前会话ID: {st.session_state.conversation_id}")
    
    # 聊天容器（应用新的消息样式）
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # 显示历史消息（优化反馈按钮布局）
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # 底部信息栏
                col1, col2 = st.columns([4, 1])
                with col1:
                    if "timestamp" in message:
                        st.caption(message["timestamp"])
                
                with col2:
                    if message["role"] == "assistant" and "response_time" in message:
                        st.caption(f"⏱️ {message['response_time']:.2f}s")
                
                # 反馈按钮（使用绿植系统的双列布局）
                if message["role"] == "assistant":
                    with st.container():  # 用容器隔离反馈按钮
                        fb_col1, fb_col2 = st.columns(2)
                        with fb_col1:
                            if st.button("👍 有帮助", key=f"like_{message['id']}", use_container_width=True):
                                save_feedback(message['id'], 1)
                                st.success("感谢您的反馈!")
                        with fb_col2:
                            if st.button("👎 无帮助", key=f"dislike_{message['id']}", use_container_width=True):
                                feedback = st.text_input("请告诉我们如何改进", key=f"fb_{message['id']}")
                                if feedback:
                                    save_feedback(message['id'], 0, feedback)
                                    st.success("感谢您的反馈!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 用户输入区域（使用Streamlit原生chat_input，应用新样式）
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息到会话状态
        timestamp = datetime.now().strftime("%H:%M:%S")
        user_msg_id = save_chat("user", prompt, conversation_id=st.session_state.conversation_id)

        # 将知识传递给LLM，让LLM选择最合适的回答
        results = retrieval_system.search(prompt, top_n=5, threshold=0.1)

        # 构建检索结果字符串
        retrieval_results = chr(10).join([
            f'  {i+1}. 问题：{item["question"]}{chr(10)}    答案：{item["answer"]}{chr(10)}    来源：{item["source"].split(os.sep)[-1]}' 
            for i, item in enumerate(results)
        ])
        
        # 读取prompt模板并替换变量
        prompt_template = load_prompt_template()
        final_prompt = prompt_template.format(
            prompt=prompt,
            retrieval_results=retrieval_results
        )
       
        st.session_state.messages.append({
            "id": user_msg_id,
            "role": "user", 
            "content": prompt,
            "timestamp": timestamp
        })
        
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(timestamp)
        
        # 获取AI回复
        with st.spinner("AI正在思考..."):
            # 构建对话上下文 (最近3轮对话)
            context = []
            for msg in st.session_state.messages[-6:]:  # 保留最近3轮对话(6条消息)
                if msg["role"] == "user":
                    context.append(HumanMessage(content=msg["content"]))
                else:
                    context.append(SystemMessage(content=msg["content"]))
            
            response, response_time = get_ai_response(final_prompt, context)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 添加AI回复到会话状态
            ai_msg_id = save_chat("assistant", response, response_time, st.session_state.conversation_id)
            st.session_state.messages.append({
                "id": ai_msg_id,
                "role": "assistant",
                "content": response,
                "timestamp": timestamp,
                "response_time": response_time
            })
            
            # 显示AI回复
            with st.chat_message("assistant"):
                st.markdown(response)
                
                # 底部信息栏
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.caption(timestamp)
                with col2:
                    st.caption(f"⏱️ {response_time:.2f}s")
        
        # 滚动到最新消息
        st.rerun()

if __name__ == "__main__":
    # 初始化检索系统
    retrieval_system = QARetrievalSystem()
    retrieval_system.load_qa_pairs()
    main()