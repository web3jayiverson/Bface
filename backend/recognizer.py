# -*- coding: utf-8 -*-
"""人脸检测与识别核心逻辑。

职责：
1. 加载 InsightFace (buffalo_l) 模型，完成人脸检测 + 512 维特征提取；
2. 加载明星特征库 star_features.pkl；
3. 对输入图像执行检测，并将每个人脸 embedding 与特征库做余弦相似度比对，
   返回 [{bbox, name, confidence}]。
"""
import hashlib
from collections import OrderedDict

import cv2
import numpy as np
from insightface.app import FaceAnalysis

from config import (DET_SIZE, FRAME_CACHE_SIZE, MAX_FACES, MODEL_NAME,
                    PROVIDERS, SIMILARITY_THRESHOLD, UNKNOWN_NAME)


class FaceRecognizer:
    """封装 InsightFace 检测 + 特征库比对，供 Flask 路由调用。"""

    def __init__(self, db_path, threshold=SIMILARITY_THRESHOLD,
                 model_name=MODEL_NAME, det_size=DET_SIZE):
        self.threshold = threshold
        self.db_path = db_path
        self.embeddings = {}          # name -> 归一化 (512,) float32
        self.model_loaded = False
        self._face_app = None
        self._cache = OrderedDict()   # 内容哈希 -> 识别结果

        self._load_model(model_name, det_size)
        self.load_database(db_path)

    # ------------------------------------------------------------ 模型
    def _load_model(self, model_name, det_size):
        """加载 buffalo_l（含 RetinaFace 检测 + ArcFace 识别）。

        模型不存在时 insightface 会自动从官方源下载到 ~/.insightface/models，
        网络受限时可手动放置模型包。
        """
        try:
            self._face_app = FaceAnalysis(name=model_name, providers=PROVIDERS)
            self._face_app.prepare(ctx_id=0, det_size=det_size)
            self.model_loaded = True
            print(f"[recognizer] InsightFace 模型加载成功: {model_name}")
        except Exception as exc:  # noqa: BLE001
            print(f"[recognizer] 模型加载失败: {exc}")
            self.model_loaded = False

    # ------------------------------------------------------------ 特征库
    def load_database(self, db_path):
        """加载 {name: embedding} 特征库并统一归一化（便于点积求余弦）。"""
        self.embeddings = {}
        if not db_path or not db_path.exists():
            print(f"[recognizer] 特征库不存在: {db_path}（可运行 build_db.py 构建）")
            return
        try:
            import joblib
            data = joblib.load(str(db_path))
        except Exception:  # noqa: BLE001
            import pickle
            with open(db_path, "rb") as f:
                data = pickle.load(f)

        for name, emb in data.items():
            arr = np.asarray(emb, dtype=np.float32).reshape(-1)
            norm = np.linalg.norm(arr)
            if norm > 0:
                self.embeddings[name] = arr / norm
        print(f"[recognizer] 特征库加载完成: {len(self.embeddings)} 位明星 <- {db_path}")

    # ------------------------------------------------------------ 识别
    def recognize(self, image_bgr, with_cache=True):
        """输入 BGR 图像，返回识别结果列表。

        结果元素: {"bbox": [x1,y1,x2,y2], "name": str, "confidence": float}
        未匹配到特征库的人脸 name 为 UNKNOWN_NAME（默认"未知"）。
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        if with_cache:
            key = self._content_hash(image_bgr)
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]

        faces = self._face_app.get(image_bgr)
        results = []
        for face in faces[:MAX_FACES]:
            x1, y1, x2, y2 = [float(v) for v in face.bbox]
            emb = np.asarray(face.embedding, dtype=np.float32)
            norm = np.linalg.norm(emb)
            emb = emb / norm if norm > 0 else emb
            name, conf = self._match(emb)
            results.append({
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "name": name,
                "confidence": round(float(conf), 4),
            })

        if with_cache:
            key = self._content_hash(image_bgr)
            self._cache[key] = results
            self._cache.move_to_end(key)
            while len(self._cache) > FRAME_CACHE_SIZE:
                self._cache.popitem(last=False)
        return results

    def _match(self, embedding):
        """余弦相似度比对：与特征库中所有向量做点积，取最高分。"""
        best_name, best_score = UNKNOWN_NAME, 0.0
        for name, ref in self.embeddings.items():
            score = float(np.dot(embedding, ref))
            if score > best_score:
                best_score, best_name = score, name
        if best_score < self.threshold:
            return UNKNOWN_NAME, best_score
        return best_name, best_score

    # ------------------------------------------------------------ 工具
    @staticmethod
    def _content_hash(image_bgr):
        """对 64x64 下采样图取 MD5，作为帧缓存键。"""
        small = cv2.resize(image_bgr, (64, 64))
        return hashlib.md5(small.tobytes()).hexdigest()
