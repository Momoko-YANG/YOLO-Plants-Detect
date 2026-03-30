CUSTOM_CSS = """
<style>
    /* ========== 侧边栏 - ChatGPT 浅色风格 ========== */
    section[data-testid="stSidebar"] {
        background-color: #f7f7f8 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #353535 !important;
    }

    /* 新建对话按钮 */
    section[data-testid="stSidebar"] > div > div > div > div:first-child .stButton > button {
        background-color: #ffffff !important;
        border: 1px solid #d9d9d9 !important;
        border-radius: 10px !important;
        color: #353535 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 0.8rem !important;
        margin-bottom: 0.3rem !important;
        transition: background-color 0.15s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] > div > div > div > div:first-child .stButton > button:hover {
        background-color: #ececec !important;
        border-color: #bbb !important;
    }

    /* 日期分组标签 */
    .sidebar-group-label {
        font-size: 0.7rem !important;
        font-weight: 600;
        color: #999 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.7rem 0.5rem 0.25rem 0.5rem;
        margin: 0;
    }

    /* 会话按钮行 - 紧凑无间距 */
    section[data-testid="stSidebar"] .stColumn {
        padding: 0 !important;
        gap: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        gap: 0 !important;
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
    }

    /* 会话标题按钮 */
    section[data-testid="stSidebar"] .stColumn .stButton > button {
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        color: #555 !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        padding: 0.45rem 0.6rem !important;
        text-align: left !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: background-color 0.15s;
        min-height: 0 !important;
        height: auto !important;
    }
    section[data-testid="stSidebar"] .stColumn .stButton > button:hover {
        background-color: rgba(0,0,0,0.05) !important;
    }

    /* 当前激活的对话（primary 按钮） */
    section[data-testid="stSidebar"] .stColumn .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stColumn .stButton > button[data-testid*="primary"] {
        background-color: #e8e8e8 !important;
        color: #1a1a1a !important;
        font-weight: 500 !important;
    }

    /* 删除按钮 × */
    section[data-testid="stSidebar"] .stColumn:last-child .stButton > button {
        opacity: 0.25;
        font-size: 0.9rem !important;
        padding: 0.4rem 0 !important;
        min-height: 0 !important;
        border: none !important;
        background: transparent !important;
        transition: opacity 0.15s;
    }
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:hover .stColumn:last-child .stButton > button {
        opacity: 0.7;
    }
    section[data-testid="stSidebar"] .stColumn:last-child .stButton > button:hover {
        opacity: 1 !important;
        color: #ff6b6b !important;
    }

    /* 隐藏侧边栏默认装饰 */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapsedControl"] {
        color: #ececec !important;
    }

    /* ========== 主聊天区域 ========== */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }
    /* ========== 输入框 - ChatGPT 风格 ========== */
    .stChatInput {
        padding: 0 !important;
        margin-top: 0.5rem;
        border-radius: 24px !important;
        background-color: #ffffff;
        border: 1px solid #d9d9e3 !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        overflow: hidden;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .stChatInput:focus-within {
        border-color: #10a37f !important;
        box-shadow: 0 2px 16px rgba(16,163,127,0.15);
    }
    [data-testid="stChatInputTextArea"] {
        border: none !important;
        border-radius: 24px !important;
        padding: 0.75rem 1.2rem !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        box-sizing: border-box !important;
        width: calc(100% - 48px) !important;
        margin: 0 !important;
        background: transparent !important;
        resize: none;
    }
    [data-testid="stChatInputTextArea"]:focus,
    [data-testid="stChatInputTextArea"]:focus-visible,
    [data-testid="stChatInputTextArea"]:active {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }
    .stChatInput [data-baseweb="textarea"],
    .stChatInput [data-baseweb="textarea"]:focus-within,
    .stChatInput textarea,
    .stChatInput textarea:focus,
    .stChatInput textarea:focus-visible {
        border-color: transparent !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInputSubmitButton"] {
        box-sizing: border-box !important;
        height: 100% !important;
        margin: 0 !important;
        border-radius: 0 24px 24px 0 !important;
        padding: 0 0.6rem !important;
    }
    [data-testid="stChatInputSubmitButton"] button {
        background-color: #10a37f !important;
        color: #fff !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background-color 0.15s;
    }
    [data-testid="stChatInputSubmitButton"] button:hover {
        background-color: #0d8a6a !important;
    }
    [data-testid="stChatInputSubmitButton"] button:disabled {
        background-color: #d9d9e3 !important;
    }
    .stChatMessage {
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: visible;
    }
    /* 防止聊天气泡内的列布局溢出重叠 */
    .stChatMessage [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap;
        gap: 0.5rem;
    }
    .stChatMessage .stColumn {
        min-width: 0;
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

    /* 聊天消息标题字号 */
    .stChatMessage h1 { font-size: 1.25rem !important; margin: 0.6em 0 0.4em !important; }
    .stChatMessage h2 { font-size: 1.1rem !important;  margin: 0.5em 0 0.3em !important; }
    .stChatMessage h3 { font-size: 1rem !important;    margin: 0.4em 0 0.2em !important; }
    .stChatMessage h4,
    .stChatMessage h5,
    .stChatMessage h6 { font-size: 0.95rem !important; margin: 0.3em 0 0.2em !important; }

    /* 思考过程折叠面板 */
    .stChatMessage .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        color: #888 !important;
    }
    .stChatMessage .streamlit-expanderContent {
        font-size: 0.85rem !important;
        color: #666 !important;
        background-color: #f9f9f9;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
    }
</style>
"""
