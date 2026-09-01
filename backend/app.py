# -*- coding: utf-8 -*-
"""B站明星人脸识别 —— 本地识别服务 (Flask)。

启动:  python app.py    （或使用 scripts/start.bat / start.sh）
接口:
  GET  /health     服务状态（模型/特征库就绪情况）
  POST /recognize  人脸识别，body={"image": "data:image/jpeg;base64,..."}
"""
import base64
import time

import cv2
import numpy as np
from flask import Flask, jsonify, request

import config
from recognizer import FaceRecognizer

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# 全局识别器：启动即加载模型与特征库
recognizer = FaceRecognizer(db_path=config.DB_PATH,
                            threshold=config.SIMILARITY_THRESHOLD)


@app.after_request
def add_cors_headers(resp):
    """插件 content script / popup 跨源访问需要（扩展来源 chrome-extension://）。"""
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/health", methods=["GET", "OPTIONS"])
def health():
    """服务状态检测：插件据此判断是否可用，并展示入库明星数。"""
    if request.method == "OPTIONS":
        return ("", 204)
    return jsonify({
        "status": "ok",
        "model_loaded": recognizer.model_loaded,
        "stars": len(recognizer.embeddings),
        "threshold": recognizer.threshold,
        "version": "1.0.0",
    })


@app.route("/recognize", methods=["POST", "OPTIONS"])
def recognize():
    """人脸识别主接口。

    请求: {"image": "data:image/jpeg;base64,/9j/..."}
    响应: {"faces": [{"bbox":[x1,y1,x2,y2], "name":"周杰伦", "confidence":0.82}],
            "processing_time": 0.21}
    """
    if request.method == "OPTIONS":
        return ("", 204)
    if not recognizer.model_loaded:
        return jsonify({"error": "Model not loaded"}), 500

    payload = request.get_json(silent=True)
    if not payload or "image" not in payload:
        return jsonify({"error": "Missing 'image' field (base64 data URL)"}), 400

    image_bgr = _decode_image(payload["image"])
    if image_bgr is None:
        return jsonify({"error": "Invalid image data"}), 400

    start = time.perf_counter()
    try:
        faces = recognizer.recognize(image_bgr)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Recognition failed: {exc}"}), 500

    return jsonify({
        "faces": faces,
        "processing_time": round(time.perf_counter() - start, 4),
    })


def _decode_image(data_url):
    """解析 data:image/jpeg;base64,xxx 或纯 base64 字符串为 BGR 图像。"""
    try:
        if "," in data_url:
            data_url = data_url.split(",", 1)[1]
        raw = base64.b64decode(data_url)
        arr = np.frombuffer(raw, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:  # noqa: BLE001
        return None


if __name__ == "__main__":
    print(f"[app] 识别服务启动: http://{config.HOST}:{config.PORT}")
    print(f"[app] 模型加载: {'成功' if recognizer.model_loaded else '失败（请先安装 buffalo_l 模型）'}")
    print(f"[app] 特征库: {len(recognizer.embeddings)} 位明星 @ {config.DB_PATH}")
    print(f"[app] 相似度阈值: {recognizer.threshold}")
    app.run(host=config.HOST, port=config.PORT, threaded=config.THREADED)
