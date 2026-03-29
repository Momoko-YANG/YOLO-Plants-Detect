# YOLO Plants Detect

基于 YOLO 的农作物病虫害识别项目，包含前端、后端、数据集与训练产物，支持图片/视频/摄像头识别与结果记录。

## 项目结构

```text
.
├── start-all.sh                      # 一键启动（FastAPI + Vue + Streamlit可选）
├── stop-all.sh                       # 一键停止
├── db/
│   └── yolo_detect.sql               # MySQL 初始化脚本
├── datasets/                         # 训练/数据目录（大文件）
├── Plant.v4-v4.0.yolov11/            # 数据集与训练相关目录（大文件）
├── yolo11n.pt                        # 基础模型权重
└── yolo_img_detection_web/
    ├── yolo_img_detection_fastapi/   # 主后端（默认，端口 9999）
    ├── yolo_img_detection_flask/     # Streamlit 问答与历史功能（端口 8501）
    ├── yolo_img_detection_vue/       # 前端（Vite，端口 8888）
    └── yolo_img_detection_springboot/# SpringBoot 版本后端（可选）
```

## 默认运行架构

- 前端：`Vue`（`http://localhost:8888`）
- 主后端：`FastAPI + Socket.IO`（`http://localhost:9999`）
- 可选服务：`Streamlit`（`http://localhost:8501`）
- 数据库：`MySQL`（默认 `localhost:3306`，库名 `yolo_detect`）
- 上传文件目录：`yolo_img_detection_web/yolo_img_detection_springboot/files/`
- 权重目录：`yolo_img_detection_web/yolo_img_detection_flask/weights/`

## 环境要求

- Python 3.10+（建议）
- Node.js 16+，npm 7+
- MySQL 8.x（本地）
- JDK 17+（仅在使用 SpringBoot 后端时需要）
- macOS / Linux（脚本基于 bash）

## 快速开始（推荐）

### 1) 初始化数据库

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS yolo_detect DEFAULT CHARACTER SET utf8mb4;"
mysql -uroot -p yolo_detect < db/yolo_detect.sql
```

导入示例数据后，可用默认账号：
- `admin / admin`

### 2) 安装依赖

安装 FastAPI 依赖：

```bash
python3 -m pip install -r yolo_img_detection_web/yolo_img_detection_fastapi/requirements.txt
```

安装前端依赖：

```bash
cd yolo_img_detection_web/yolo_img_detection_vue
npm install
cd ../../
```

可选：安装 Streamlit 问答服务依赖（如需 8501）：

```bash
python3 -m pip install streamlit jieba numpy pandas scikit-learn langchain
```

### 3) 一键启动

```bash
chmod +x start-all.sh stop-all.sh
./start-all.sh
```

启动成功后访问：
- 前端：`http://localhost:8888`
- FastAPI：`http://localhost:9999`
- Streamlit：`http://localhost:8501`

日志目录：
- `.run/logs/fastapi.log`
- `.run/logs/vue.log`
- `.run/logs/streamlit.log`

### 4) 一键停止

```bash
./stop-all.sh
```

## 配置说明

FastAPI 默认读取以下环境变量（未设置时使用默认值）：

- `MYSQL_HOST=localhost`
- `MYSQL_PORT=3306`
- `MYSQL_USER=root`
- `MYSQL_PASSWORD=123456`
- `MYSQL_DATABASE=yolo_detect`
- `SERVER_HOST=localhost`
- `SERVER_PORT=9999`

示例：

```bash
MYSQL_PASSWORD=你的密码 SERVER_PORT=9999 python3 yolo_img_detection_web/yolo_img_detection_fastapi/main.py
```

## 手动启动（不使用脚本）

### FastAPI

```bash
cd yolo_img_detection_web/yolo_img_detection_fastapi
python3 main.py
```

### Vue

```bash
cd yolo_img_detection_web/yolo_img_detection_vue
npm run dev
```

### Streamlit（可选）

```bash
cd yolo_img_detection_web/yolo_img_detection_flask
python3 -m streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false
```

## SpringBoot 后端（可选模式）

目录：`yolo_img_detection_web/yolo_img_detection_springboot`

```bash
cd yolo_img_detection_web/yolo_img_detection_springboot
./mvnw spring-boot:run
```

注意：
- 默认也是 `9999` 端口，和 FastAPI 冲突。
- 运行 SpringBoot 时请先停止 FastAPI，二者二选一。

## 常见问题

- 前端起不来：先确认 `yolo_img_detection_vue/node_modules` 已安装。
- 识别失败：确认权重文件在 `yolo_img_detection_web/yolo_img_detection_flask/weights/`。
- 数据库连接失败：检查 MySQL 是否在 `3306` 监听，账号密码是否与配置一致。
- 摄像头识别失败：确认本机摄像头权限已授予。
