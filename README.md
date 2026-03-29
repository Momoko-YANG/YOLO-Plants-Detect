# YOLO Plants Detect

基于 YOLO 的农作物病虫害识别全栈项目，支持图片/视频/摄像头实时识别与结果记录，附带 RAG 知识问答系统。

## 架构总览

```text
浏览器                         服务端
 ┌──────────┐    HTTP/WS     ┌───────────────────┐
 │ Vue3 SPA │ ◄────────────► │  FastAPI + SocketIO│── YOLO 推理
 └──────────┘    :9999       │  (backend/)        │── MySQL
                              └───────────────────┘
                              ┌───────────────────┐
                              │  Streamlit RAG QA  │── LLM / TF-IDF
                              │  (streamlit/)      │── SQLite
                              └───────────────────┘
                                     :8501
```

## 项目结构

```text
.
├── start-all.sh                 # 一键启动（FastAPI + Streamlit + 可选 Vue dev）
├── stop-all.sh                  # 一键停止
├── db/
│   └── yolo_detect.sql          # MySQL 建库脚本与示例数据
├── shared/
│   ├── weights/                 # 模型权重文件
│   ├── uploads/                 # 用户上传的图片/视频
│   └── dist/                    # 前端构建产物（供 FastAPI 静态服务）
├── backend/                     # FastAPI 后端（模块化）
│   ├── main.py                  # 应用入口 + Socket.IO 挂载
│   ├── config.py                # 配置集中管理（路径、DB、端口）
│   ├── requirements.txt
│   ├── database/
│   │   └── db.py                # 数据库连接与通用 CRUD
│   ├── models/
│   │   └── schemas.py           # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── users.py             # /user/* 用户管理
│   │   ├── img_records.py       # /imgRecords/* 图片记录 + 统计
│   │   ├── video_records.py     # /videoRecords/* 视频记录
│   │   ├── camera_records.py    # /cameraRecords/* 摄像记录
│   │   ├── files.py             # /files/* 文件上传/下载
│   │   └── predict.py           # /predict* 图片/视频/摄像头推理
│   ├── services/
│   │   ├── predict.py           # YOLO 推理、视频转码
│   │   └── suggestion.py        # 识别结果建议生成
│   └── utils/
│       ├── response.py          # 统一响应格式
│       └── converters.py        # snake/camel 转换等
├── frontend/                    # Vue3 + Vite + Element Plus 前端
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── views/               # 页面：识别、记录、问答、用户管理等
│       ├── router/              # 路由（Hash 模式）
│       ├── stores/              # Pinia 状态
│       └── utils/               # 请求封装、Socket.IO 客户端等
├── streamlit/                   # Streamlit RAG 问答服务
│   ├── app.py                   # 入口
│   ├── requirements.txt
│   ├── prompt.txt               # LLM Prompt 模板
│   └── *.xlsx                   # 知识库文件
├── springboot/                  # [遗留] Spring Boot 后端（不纳入主架构）
├── datasets/                    # 训练数据集（gitignored）
└── Plant.v4-v4.0.yolov11/      # 训练产物目录（gitignored）
```

## 默认运行架构

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI + Socket.IO | 9999 | 主后端，同时服务前端构建产物 |
| Streamlit RAG QA | 8501 | 知识问答（可选，依赖 streamlit 安装） |
| Vue Dev Server | 8888 | 仅开发模式（`START_VUE=true`） |
| MySQL | 3306 | 数据库（库名 `yolo_detect`） |

生产模式下前端通过 `shared/dist/` 由 FastAPI 直接服务，无需独立 Vue 开发服务器。

## 环境要求

- Python 3.10+
- Node.js 16+、npm 7+（仅开发前端时需要）
- MySQL 8.x
- macOS / Linux（脚本基于 bash）

## 快速开始

### 1) 初始化数据库

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS yolo_detect DEFAULT CHARACTER SET utf8mb4;"
mysql -uroot -p yolo_detect < db/yolo_detect.sql
```

导入后可用默认账号：`admin / admin`

### 2) 安装后端依赖

```bash
python3 -m pip install -r backend/requirements.txt
```

### 3) 放置模型权重

将训练好的 `.pt` 权重文件放入 `shared/weights/` 目录。

### 4) 一键启动

```bash
chmod +x start-all.sh stop-all.sh
./start-all.sh
```

启动成功后访问：`http://localhost:9999/#/login`

### 5) 一键停止

```bash
./stop-all.sh
```

## 可选：安装 Streamlit 问答服务

```bash
python3 -m pip install -r streamlit/requirements.txt
```

安装后重新运行 `./start-all.sh` 即可自动启动 8501 端口。

## 可选：前端开发模式

```bash
cd frontend
npm install
START_VUE=true ../start-all.sh
# 或手动：npm run dev
```

## 配置说明

FastAPI 通过环境变量读取配置（未设置时使用默认值）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MYSQL_HOST` | `localhost` | MySQL 地址 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_USER` | `root` | MySQL 用户 |
| `MYSQL_PASSWORD` | `123456` | MySQL 密码 |
| `MYSQL_DATABASE` | `yolo_detect` | 数据库名 |
| `SERVER_HOST` | `localhost` | 服务绑定地址 |
| `SERVER_PORT` | `9999` | 服务端口 |

示例：

```bash
MYSQL_PASSWORD=你的密码 python3 backend/main.py
```

## 手动启动（不使用脚本）

```bash
# FastAPI
cd backend && python3 main.py

# Streamlit
cd streamlit && python3 -m streamlit run app.py --server.port 8501 --server.headless true

# Vue（开发模式）
cd frontend && npm run dev
```

## 日志

启动后日志输出到 `.run/logs/`：

- `fastapi.log` — 后端日志
- `streamlit.log` — 问答服务日志
- `vue.log` — 前端开发服务器日志

## 常见问题

- **前端起不来**：确认 `frontend/node_modules` 已安装（`npm install`）。
- **识别失败**：确认 `shared/weights/` 下有权重文件。
- **数据库连接失败**：检查 MySQL 是否在 3306 监听，账号密码是否与配置一致。
- **摄像头识别失败**：确认本机摄像头权限已授予浏览器。
- **Streamlit 未启动**：确认已安装 `streamlit/requirements.txt` 中的依赖。
