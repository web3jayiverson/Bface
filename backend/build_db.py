# -*- coding: utf-8 -*-
"""构建明星特征库：遍历按姓名分组的图片目录 -> star_features.pkl。

用法:
    python build_db.py [--data-dir ../data/faces] [--output ../data/star_features.pkl]

目录结构（data/faces 下每个子文件夹 = 一位明星）:
    data/faces/
        周杰伦/001.jpg 002.jpg ...
        林俊杰/001.jpg 002.jpg ...

流程:
    1. 加载 InsightFace 模型（与识别服务同一套配置）；
    2. 对每人每张图提取最大人脸的特征向量；
    3. 取均值并 L2 归一化，作为该明星的代表向量；
    4. 保存为 pickle 字典 {name: ndarray(512, float32)}。
"""
import argparse
import pickle
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def imread_unicode(path):
    """读取图片，兼容 Windows 下的中文/非 ASCII 路径。

    cv2.imread 在 Windows 上不支持非 ASCII 路径（会静默返回 None），
    改用 np.fromfile + cv2.imdecode 绕过该限制。
    """
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def extract_embedding(face_app, image_bgr):
    """提取图像中最大人脸的特征向量（归一化）。多人合照取最大脸。"""
    faces = face_app.get(image_bgr)
    if not faces:
        return None
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    emb = np.asarray(face.embedding, dtype=np.float32)
    norm = np.linalg.norm(emb)
    return emb / norm if norm > 0 else None


def build(data_dir, output, min_images=3):
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise SystemExit(f"数据目录不存在: {data_dir}")

    print(f"[build_db] 加载模型 {config.MODEL_NAME} ...")
    face_app = FaceAnalysis(name=config.MODEL_NAME, providers=config.PROVIDERS)
    face_app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    database = {}
    skipped = []
    person_dirs = sorted(p for p in data_dir.iterdir() if p.is_dir())

    for person_dir in person_dirs:
        name = person_dir.name.strip()
        imgs = [p for p in sorted(person_dir.iterdir())
                if p.suffix.lower() in IMAGE_EXTS]
        if len(imgs) < min_images:
            skipped.append((name, f"图片不足 {min_images} 张（{len(imgs)}）"))
            continue

        embeddings = []
        for img_path in imgs:
            img = imread_unicode(img_path)
            if img is None:
                continue
            emb = extract_embedding(face_app, img)
            if emb is not None:
                embeddings.append(emb)

        if not embeddings:
            skipped.append((name, "未检测到人脸"))
            continue

        mean = np.mean(embeddings, axis=0).astype(np.float32)
        mean = mean / np.linalg.norm(mean)
        database[name] = mean
        print(f"  [OK] {name}: {len(embeddings)}/{len(imgs)} 张有效")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        pickle.dump(database, f, protocol=4)

    print(f"\n完成: {len(database)} 位明星 -> {output}")
    if skipped:
        print("跳过:")
        for name, reason in skipped:
            print(f"  - {name}: {reason}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建明星特征库")
    parser.add_argument("--data-dir", default=str(config.FACES_DIR),
                        help="按姓名分组的图片目录")
    parser.add_argument("--output", default=str(config.DB_PATH),
                        help="输出 pkl 路径")
    parser.add_argument("--min-images", type=int, default=3,
                        help="每位明星最少有效图片数")
    args = parser.parse_args()
    build(args.data_dir, args.output, args.min_images)
