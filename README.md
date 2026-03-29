# YOLO Plants Detect

基于 **YOLOv11 + FastAPI + Vue3 + Streamlit** 的农作物病虫害智能识别系统。

支持图片 / 视频 / 摄像头实时识别，集成 RAG 知识问答，检测结果自动归档。

## 架构总览

```text
浏览器（Vue3 SPA）
    │
    │  HTTP / WebSocket
    ▼
┌─────────────────────────────────────┐
│  FastAPI + Socket.IO    :9999       │
│  ├─ YOLO 推理（图片/视频/摄像头）     │
│  ├─ 用户管理 / 记录管理              │
│  ├─ 静态文件服务（前端 dist）         │
│  └─ MySQL 持久化                    │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  Streamlit RAG 问答      :8501      │
│  ├─ TF-IDF 知识库检索               │
│  ├─ LLM 流式回答（MiniMax / OpenAI）│
│  ├─ 对话历史管理 + 自动标题生成       │
│  └─ SQLite 本地存储                 │
└─────────────────────────────────────┘
```

## 项目结构

```text
.
├── start-all.sh              # 一键启动
├── stop-all.sh               # 一键停止
├── .env.example              # 环境变量模板
│
├── backend/                  # FastAPI 后端（模块化）
│   ├── main.py               #   入口 + Socket.IO + 中间件
│   ├── config.py             #   路径 / DB / 端口 集中配置
│   ├── database/db.py        #   MySQL 连接与通用 CRUD
│   ├── models/schemas.py     #   Pydantic 请求模型
│   ├── routers/              #   路由层
│   │   ├── users.py          #     用户登录 / 增删改查
│   │   ├── predict.py        #     图片 / 视频 / 摄像头推理
│   │   ├── files.py          #     文件上传下载 / 模型列表
│   │   ├── img_records.py    #     图片检测记录 + 统计
│   │   ├── video_records.py  #     视频检测记录
│   │   └── camera_records.py #     摄像头检测记录
│   ├── services/             #   业务逻辑
│   │   ├── predict.py        #     YOLO 推理 / 视频转码
│   │   └── suggestion.py     #     AI 识别建议生成
│   └── utils/                #   工具层
│       ├── response.py       #     统一响应格式
│       └── converters.py     #     命名风格转换
│
├── frontend/                 # Vue3 + Vite + Element Plus
│   ├── src/views/            #   页面：识别 / 记录 / 问答 / 用户
│   ├── src/router/           #   路由（Hash 模式）
│   ├── src/stores/           #   Pinia 状态管理
│   └── src/utils/            #   请求封装 / Socket.IO 客户端
│
├── streamlit/                # Streamlit RAG 问答（模块化）
│   ├── app.py                #   入口：侧边栏 + 聊天 + 流式输出
│   ├── config.py             #   路径常量 / 环境加载
│   ├── database.py           #   SQLite 会话 / 消息 / 反馈
│   ├── retrieval.py          #   TF-IDF 知识库检索引擎
│   ├── llm.py                #   LLM 初始化 / 消息构建 / 标题生成
│   ├── utils.py              #   think 标签解析 / 消息渲染
│   ├── styles.py             #   ChatGPT 风格 CSS
│   └── prompt.txt            #   RAG Prompt 模板
│
├── shared/
│   ├── weights/              # YOLO 模型权重（.pt）
│   ├── uploads/              # 用户上传的图片 / 视频
│   └── dist/                 # 前端构建产物
│
├── db/
│   └── yolo_detect.sql       # MySQL 建库脚本 + 示例数据
│
├── datasets/                 # 训练数据集
└── springboot/               # [遗留] Spring Boot 后端（不再维护）
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI | 9999 | 主后端，同时托管前端构建产物 |
| Streamlit | 8501 | RAG 知识问答（可选） |
| MySQL | 3306 | 数据库（库名 `yolo_detect`） |

## 环境要求

- Python 3.9+
- Node.js 16+（仅前端开发时需要）
- MySQL 8.x
- macOS / Linux

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 MySQL 密码和 LLM API Key
```

### 2. 初始化数据库

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS yolo_detect DEFAULT CHARSET utf8mb4;"
mysql -u root yolo_detect < db/yolo_detect.sql
```

默认账号：`admin / admin`

### 3. 安装依赖

```bash
# 后端
pip install -r backend/requirements.txt

# 问答服务（可选）
pip install -r streamlit/requirements.txt
```

### 4. 放置模型权重

将 `.pt` 权重文件放入 `shared/weights/` 目录。

### 5. 一键启动

```bash
./start-all.sh
```

启动后访问：**http://localhost:9999**

### 6. 停止服务

```bash
./stop-all.sh
```

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MYSQL_HOST` | `localhost` | MySQL 地址 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_USER` | `root` | MySQL 用户 |
| `MYSQL_PASSWORD` | *(空)* | MySQL 密码 |
| `MYSQL_DATABASE` | `yolo_detect` | 数据库名 |
| `SERVER_HOST` | `localhost` | FastAPI 绑定地址 |
| `SERVER_PORT` | `9999` | FastAPI 端口 |
| `LLM_API_KEY` | | LLM API 密钥 |
| `LLM_API_BASE` | | LLM API 地址（如 `https://api.minimax.io/v1`） |
| `LLM_MODEL` | | 模型名称（如 `MiniMax-M2.7`） |
| `LLM_TEMPERATURE` | `0.7` | 生成温度 |
| `LLM_MAX_TOKENS` | `1000` | 最大 token 数 |

## 功能特性

### 图片识别
上传图片 → YOLO 推理 → 返回标注图、类别、置信度、耗时 → 自动保存记录 → AI 生成识别建议

### 视频识别
上传视频 → 逐帧 YOLO 推理 → 实时流式预览 → 统计最频繁类别 → Socket.IO 进度通知

### 摄像头识别
调用本机摄像头 → 实时 YOLO 推理 → 浏览器流式预览 → 自动录制保存

### RAG 知识问答
- 基于 xlsx 知识库的 TF-IDF 检索
- LLM 流式回答，思考过程可折叠
- 对话历史按日期分组，标题自动生成
- ChatGPT 风格的 UI

## 前端开发

```bash
cd frontend
npm install
npm run dev          # 启动开发服务器 :8888
npm run build        # 构建到 ../shared/dist/
```

## 日志

启动后日志位于 `.run/logs/`：

```
.run/logs/
├── fastapi.log      # 后端日志
└── streamlit.log    # 问答服务日志
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 识别失败 | 确认 `shared/weights/` 下有 `.pt` 权重文件 |
| 数据库连接失败 | 检查 MySQL 是否运行，`.env` 密码是否正确 |
| 记录未保存 | 确认已执行 `db/yolo_detect.sql` 建表 |
| Streamlit 未启动 | `pip install -r streamlit/requirements.txt` |
| 知识问答无回复 | 检查 `.env` 中 `LLM_API_KEY` 和 `LLM_API_BASE` 是否正确 |
| 摄像头无法使用 | 确认浏览器已授予摄像头权限 |
