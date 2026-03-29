CUSTOM_CSS = """
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
        padding: 1rem;
    }
    .stChatInput {
        padding: 0 !important;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        margin-top: 0.5rem;
        border-radius: 8px;
        background-color: #ffffff;
        overflow: hidden;
    }
    [data-testid="stChatInputTextArea"] {
        border-radius: 8px !important;
        padding: 0.8rem 1rem !important;
        border: 1px solid #ddd !important;
        box-sizing: border-box !important;
        width: calc(100% - 40px) !important;
        margin: 0 !important;
    }
    [data-testid="stChatInputSubmitButton"] {
        box-sizing: border-box !important;
        height: 100% !important;
        margin: 0 !important;
        border-radius: 0 8px 8px 0 !important;
    }
    .stChatMessage {
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
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
    .stChatMessage h1 { font-size: 1.25rem !important; margin: 0.6em 0 0.4em !important; }
    .stChatMessage h2 { font-size: 1.1rem !important;  margin: 0.5em 0 0.3em !important; }
    .stChatMessage h3 { font-size: 1rem !important;    margin: 0.4em 0 0.2em !important; }
    .stChatMessage h4,
    .stChatMessage h5,
    .stChatMessage h6 { font-size: 0.95rem !important; margin: 0.3em 0 0.2em !important; }
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
    section[data-testid="stSidebar"] .stButton > button {
        text-align: left !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.6rem !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    section[data-testid="stSidebar"] .stCaption {
        margin-top: -0.6rem !important;
        padding-left: 0.6rem;
        font-size: 0.7rem !important;
    }
</style>
"""
