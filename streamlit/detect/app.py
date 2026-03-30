"""
YOLO 图像/视频检测 Flask API
运行: python -m detect.app (从 Streamlit/ 目录)
"""
import json
import os
import sys
import time

import cv2
import requests
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from ultralytics import YOLO

# 确保能找到上级目录的 config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import WEIGHTS_DIR, RUNS_DIR  # noqa: E402

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class VideoProcessingApp:
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.host = host
        self.port = port
        self.setup_routes()
        self.data = {}
        self.paths = {
            'download': str(RUNS_DIR / 'video' / 'download.mp4'),
            'output': str(RUNS_DIR / 'video' / 'output.mp4'),
            'camera_output': str(RUNS_DIR / 'video' / 'camera_output.avi'),
            'video_output': str(RUNS_DIR / 'video' / 'camera_output.avi'),
        }
        self.recording = False
        os.makedirs(os.path.dirname(self.paths['download']), exist_ok=True)

    def setup_routes(self):
        self.app.add_url_rule('/file_names', 'file_names', self.file_names, methods=['GET'])
        self.app.add_url_rule('/predictImg', 'predictImg', self.predictImg, methods=['POST'])
        self.app.add_url_rule('/predictVideo', 'predictVideo', self.predictVideo, methods=['GET'])
        self.app.add_url_rule('/predictCamera', 'predictCamera', self.predictCamera, methods=['GET'])
        self.app.add_url_rule('/stopCamera', 'stopCamera', self.stopCamera, methods=['GET'])
        self.app.add_url_rule('/suggest', 'suggest', self.suggest, methods=['POST'])

        @self.socketio.on('connect')
        def handle_connect():
            print("WebSocket connected!")
            emit('message', {'data': 'Connected to WebSocket server!'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("WebSocket disconnected!")

    def run(self):
        self.socketio.run(self.app, host=self.host, port=self.port, allow_unsafe_werkzeug=True)

    def init_llm(self):
        return ChatOpenAI(
            openai_api_key=os.getenv("LLM_API_KEY", ""),
            openai_api_base=os.getenv("LLM_API_BASE", ""),
            model_name=os.getenv("LLM_MODEL", ""),
            temperature=0.7,
            max_tokens=1000,
        )

    def get_ai_response(self, question, conversation_context=None):
        llm = self.init_llm()
        start_time = time.time()
        messages = [SystemMessage(content="")]
        if conversation_context:
            messages.extend(conversation_context)
        messages.append(HumanMessage(content=question))
        response = llm(messages)
        return response.content, time.time() - start_time

    def suggest(self):
        try:
            data = request.get_json()
            result = data.get('result')
            if not result:
                return jsonify({"code": 400, "msg": "缺少名称参数", "data": None})

            prompt = f"""
                你是一个农作物病虫害专家，请根据识别的结果给出相应的建议
                识别结果：{result}。
                结构：1.引起原因；2.种植建议；3.治理方式；
                不要生成markdown格式，语言生动，避免术语，300-500字左右，每个段落前都要带上标题（结构中的5点就是对应的标题），并且标题前需要加上一个小图标。
            """
            ai_response, cost_time = self.get_ai_response(prompt)
            formatted_response = ai_response.replace('\n', '<br>')
            return jsonify({
                "code": 0, "msg": "成功介绍",
                "data": {"suggestion": formatted_response, "generate_time": f"{cost_time:.2f}秒"},
            })
        except Exception as e:
            print(f"生成建议错误：{str(e)}")
            return jsonify({"code": 500, "msg": f"生成失败：{str(e)}", "data": None})

    def file_names(self):
        weight_items = [{'value': name, 'label': name} for name in self.get_file_names(str(WEIGHTS_DIR))]
        return json.dumps({'weight_items': weight_items})

    def predictImg(self):
        data = request.get_json()
        self.data.clear()
        self.data.update({
            "username": data.get('username'), "weight": data.get('weight'),
            "conf": data.get('conf'), "startTime": data.get('startTime'),
            "inputImg": data.get('inputImg'), "kind": data.get('kind'),
        })

        from predict import predictImg
        predict = predictImg.ImagePredictor(
            weights_path=str(WEIGHTS_DIR / self.data["weight"]),
            img_path=self.data["inputImg"],
            save_path=str(RUNS_DIR / 'result.jpg'),
            kind=self.data["kind"],
            conf=float(self.data["conf"]),
        )
        results = predict.predict()
        uploadedUrl = self.upload(str(RUNS_DIR / 'result.jpg'))

        if results.get('labels') != '预测失败':
            self.data.update({
                "status": 200, "message": "预测成功", "outImg": uploadedUrl,
                "allTime": results.get('allTime'),
                "confidence": json.dumps(results.get('confidences')),
                "label": json.dumps(results.get('labels')).replace('HUO', '火').replace('YAN', '烟'),
            })
        else:
            self.data.update({"status": 400, "message": "该图片无法识别，请重新上传！"})

        path = self.data["inputImg"].split('/')[-1]
        if os.path.exists(path):
            os.remove(path)
        return json.dumps(self.data, ensure_ascii=False)

    def predictVideo(self):
        self.data.clear()
        self.data.update({
            "username": request.args.get('username', ''),
            "weight": request.args.get('weight', ''),
            "conf": request.args.get('conf', 0.5),
            "startTime": request.args.get('startTime', ''),
            "inputVideo": request.args.get('inputVideo', ''),
            "kind": request.args.get('kind', ''),
        })

        class_counter = {}
        total_frames = 0
        current_socket_id = getattr(request, 'sid', None)

        try:
            self.download(self.data["inputVideo"], self.paths['download'])
            cap = cv2.VideoCapture(self.paths['download'])
            if not cap.isOpened():
                return Response("无法打开视频文件", status=500)

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_width, frame_height = 640, 480
            video_writer = cv2.VideoWriter(
                self.paths['video_output'], cv2.VideoWriter_fourcc(*'XVID'),
                fps, (frame_width, frame_height),
            )

            try:
                model = YOLO(str(WEIGHTS_DIR / self.data["weight"]))
            except Exception as e:
                cap.release()
                return Response(f"模型加载失败: {str(e)}", status=500)

            def generate():
                nonlocal total_frames
                try:
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        total_frames += 1
                        frame = cv2.resize(frame, (frame_width, frame_height))
                        results = model.predict(source=frame, conf=float(self.data['conf']), show=False)
                        for box in results[0].boxes:
                            cls_name = model.names[int(box.cls[0])]
                            class_counter[cls_name] = class_counter.get(cls_name, 0) + 1
                        processed_frame = results[0].plot()
                        video_writer.write(processed_frame)
                        _, jpeg = cv2.imencode('.jpg', processed_frame)
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'
                finally:
                    self.cleanup_resources(cap, video_writer)
                    if class_counter:
                        most_name, most_count = max(class_counter.items(), key=lambda x: x[1])
                        most_name = most_name.replace('HUO', '火').replace('YAN', '烟')
                        prompt = f"""
                            你是一个农作物病虫害专家，请根据识别的结果给出相应的建议
                            识别结果：{most_name}。
                            结构：1.引起原因；2.种植建议；3.治理方式；
                            不要生成markdown格式，语言生动，避免术语，300-500字左右。
                        """
                        ai_response, _ = self.get_ai_response(prompt)
                        desc = ai_response.replace('\n', '<br>')
                        self.socketio.emit(
                            'most_frequent_class',
                            {"data": {'name': most_name, 'count': most_count, 'desc': desc}},
                            room=current_socket_id,
                        )
                        self.socketio.emit('total_frames', {"data": total_frames}, room=current_socket_id)
                    else:
                        self.socketio.emit(
                            'most_frequent_class',
                            {"data": {'name': '未识别到任何类别', 'count': 0}},
                            room=current_socket_id,
                        )
                    self.socketio.emit('message', {"data": '处理完成，正在保存！'}, room=current_socket_id)
                    for progress in self.convert_avi_to_mp4(self.paths['video_output']):
                        self.socketio.emit('progress', {"data": progress}, room=current_socket_id)
                    uploadedUrl = self.upload(self.paths['output'])
                    self.data["outVideo"] = uploadedUrl
                    self.save_data(json.dumps(self.data), 'http://localhost:9999/videoRecords')
                    self.cleanup_files([self.paths['download'], self.paths['output'], self.paths['video_output']])

            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        except Exception as e:
            print(f"视频处理错误: {str(e)}")
            return Response(f"视频处理失败: {str(e)}", status=500)

    def predictCamera(self):
        self.data.clear()
        self.data.update({
            "username": request.args.get('username', ''),
            "weight": request.args.get('weight', ''),
            "kind": request.args.get('kind', ''),
            "conf": request.args.get('conf', 0.5),
            "startTime": request.args.get('startTime', ''),
        })
        self.socketio.emit('message', '正在加载，请稍等！')

        try:
            model = YOLO(str(WEIGHTS_DIR / self.data["weight"]))
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            video_writer = cv2.VideoWriter(
                self.paths['camera_output'], cv2.VideoWriter_fourcc(*'XVID'), 20, (640, 480),
            )
            self.recording = True

            def generate():
                try:
                    while self.recording:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        results = model.predict(source=frame, imgsz=640, conf=float(self.data['conf']), show=False)
                        processed_frame = results[0].plot()
                        if self.recording and video_writer:
                            video_writer.write(processed_frame)
                        _, jpeg = cv2.imencode('.jpg', processed_frame)
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'
                finally:
                    self.cleanup_resources(cap, video_writer)
                    self.socketio.emit('message', {'data': '处理完成，正在保存！'})
                    for progress in self.convert_avi_to_mp4(self.paths['camera_output']):
                        self.socketio.emit('progress', {'data': progress})
                    uploadedUrl = self.upload(self.paths['output'])
                    self.data["outVideo"] = uploadedUrl
                    self.save_data(json.dumps(self.data), 'http://localhost:9999/cameraRecords')
                    self.cleanup_files([self.paths['download'], self.paths['output'], self.paths['camera_output']])

            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        except Exception as e:
            print(f"摄像头处理错误: {str(e)}")
            return Response(f"摄像头处理失败: {str(e)}", status=500)

    def stopCamera(self):
        self.recording = False
        return json.dumps({"status": 200, "message": "预测成功", "code": 0})

    def save_data(self, data, path):
        try:
            response = requests.post(path, data=data, headers={'Content-Type': 'application/json'})
            print(f"记录上传{'成功' if response.status_code == 200 else f'失败，状态码: {response.status_code}'}")
        except Exception as e:
            print(f"上传记录错误: {str(e)}")

    def convert_avi_to_mp4(self, temp_output):
        cap = cv2.VideoCapture(temp_output)
        if not cap.isOpened():
            raise ValueError(f"无法打开AVI文件: {temp_output}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(self.paths['output'], fourcc, fps, (width, height))
        if not out.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.paths['output'], fourcc, fps, (width, height))
        if not out.isOpened():
            raise ValueError(f"无法创建MP4文件: {self.paths['output']}")

        try:
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frame_count += 1
                yield int((frame_count / total_frames) * 100)
            yield 100
        finally:
            cap.release()
            out.release()

    def get_file_names(self, directory):
        try:
            return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        except Exception as e:
            print(f"获取文件列表错误: {e}")
            return []

    def upload(self, out_path):
        if not os.path.exists(out_path):
            print(f"文件不存在: {out_path}")
            return ""
        try:
            with open(out_path, 'rb') as file:
                response = requests.post(
                    "http://localhost:9999/files/upload",
                    files={'file': (os.path.basename(out_path), file)},
                )
                return response.json().get('data', '') if response.status_code == 200 else ""
        except Exception as e:
            print(f"文件上传错误: {str(e)}")
            return ""

    def download(self, url, save_path):
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"文件下载成功: {save_path}")
        except Exception as e:
            print(f"文件下载错误: {str(e)}")
            raise

    def cleanup_files(self, file_paths):
        for path in file_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"清理文件错误 {path}: {str(e)}")

    def cleanup_resources(self, cap, video_writer):
        if cap and cap.isOpened():
            cap.release()
        if video_writer:
            video_writer.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    video_app = VideoProcessingApp()
    video_app.run()
