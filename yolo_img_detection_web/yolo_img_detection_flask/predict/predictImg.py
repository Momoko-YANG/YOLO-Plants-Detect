import json
import traceback
import time
from ultralytics import YOLO


class ImagePredictor:
    def __init__(self, weights_path, img_path, kind, save_path="./runs/result.jpg", conf=0.5):
        """
        初始化ImagePredictor类
        :param weights_path: 权重文件路径
        :param img_path: 输入图像路径
        :param save_path: 结果保存路径
        :param conf: 置信度阈值
        """
        self.model = YOLO(weights_path)
        self.conf = conf
        self.img_path = img_path
        self.save_path = save_path
        self.kind = {
            'plants': [
                '苹果黑星病叶',          # Apple Scab Leaf
                '苹果叶片',              # Apple leaf
                '苹果锈病叶',            # Apple rust leaf
                '甜椒叶片',              # Bell_pepper leaf
                '甜椒叶斑病叶',          # Bell_pepper leaf spot
                '蓝莓叶片',              # Blueberry leaf
                '樱桃叶片',              # Cherry leaf
                '玉米灰斑病叶',          # Corn Gray leaf spot
                '玉米叶枯病叶',          # Corn leaf blight
                '玉米锈病叶',            # Corn rust leaf
                '桃树叶片',              # Peach leaf
                '马铃薯叶片',            # Potato leaf
                '马铃薯早疫病叶',        # Potato leaf early blight
                '马铃薯晚疫病叶',        # Potato leaf late blight
                '覆盆子叶片',            # Raspberry leaf
                '大豆叶片（拼写变体）',  # Soyabean leaf（Soyabean是Soybean的拼写变体）
                '大豆叶片',              # Soybean leaf
                '南瓜白粉病叶',          # Squash Powdery mildew leaf
                '草莓叶片',              # Strawberry leaf
                '番茄早疫病叶',          # Tomato Early blight leaf
                '番茄斑枯病叶',          # Tomato Septoria leaf spot
                '番茄叶片',              # Tomato leaf
                '番茄细菌性斑点病叶',    # Tomato leaf bacterial spot
                '番茄晚疫病叶',          # Tomato leaf late blight
                '番茄花叶病毒病叶',      # Tomato leaf mosaic virus
                '番茄黄化病毒病叶',      # Tomato leaf yellow virus
                '番茄霉病叶',            # Tomato mold leaf
                '番茄二斑叶螨危害叶',    # Tomato two spotted spider mites leaf
                '葡萄叶片',              # grape leaf
                '葡萄黑腐病叶'           # grape leaf black rot
            ]
        }
        self.labels = self.kind[kind]

    def predict(self):
        """
        预测图像并保存结果
        """
        start_time = time.time()  # 开始计时

        # 执行预测
        results = self.model(source=self.img_path, conf=self.conf, half=True, save_conf=True)

        end_time = time.time()  # 结束计时
        elapsed_time = end_time - start_time  # 计算用时

        all_results = {
            'labels': [],  # 存储所有标签
            'confidences': [],  # 存储所有置信度
            'allTime': f"{elapsed_time:.3f}秒"
        }

        try:
            # 检查是否有检测结果
            if len(results) == 0:
                print("未检测到目标，请换一张图片。")
                all_results = {
                    'labels': '预测失败',  # 存储所有标签
                    'confidences': "0.00%",  # 存储所有置信度
                    'allTime': f"{elapsed_time:.3f}秒"
                }
                return all_results

            for result in results:
                # 提取置信度和标签
                confidences = result.boxes.conf if hasattr(result.boxes, 'conf') else []
                labels = result.boxes.cls if hasattr(result.boxes, 'cls') else []

                # 检查 confidences 和 labels 是否为空
                if confidences.numel() == 0 or labels.numel() == 0:
                    print("未检测到目标，请换一张图片。")
                    all_results = {
                        'labels': '预测失败',  # 存储所有标签
                        'confidences': "0.00%",  # 存储所有置信度
                        'allTime': f"{elapsed_time:.3f}秒"
                    }
                    return all_results

                # 获取标签名称和对应置信度
                label_names = [self.labels[int(cls)] for cls in labels]
                predictions = list(zip(label_names, confidences))

                # 将每个结果保存到字典中
                for label, conf in predictions:
                    all_results['labels'].append(label)
                    all_results['confidences'].append(f"{conf * 100:.2f}%")

                result.save(filename=self.save_path)  # 保存结果

            return all_results  # 返回包含标签和置信度的字典
        except Exception as e:
            # 如果预测过程中发生异常，打印错误信息并返回空结果
            print(f"预测过程中发生异常: {e}")
            print(traceback.format_exc())
            all_results = {
                'labels': '预测失败',  # 存储所有标签
                'confidences': "0.00%",  # 存储所有置信度
                'allTime': f"{elapsed_time:.3f}秒"
            }
            return all_results


if __name__ == '__main__':
    # 初始化预测器
    predictor = ImagePredictor("../weights/rice_best.pt", "../rice_test.png", 'rice', save_path="../runs/result.jpg", conf=0.5)

    # 执行预测
    result = predictor.predict()
    labels_str = json.dumps(result['labels'])  # 将列表转换为 JSON 格式的字符串
    confidences_str = json.dumps(result['confidences'])  # 将列表转换为 JSON 格式的字符串
    print(labels_str)
    print(confidences_str)
    print(result['allTime'])