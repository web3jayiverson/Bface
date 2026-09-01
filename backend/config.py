# -*- coding: utf-8 -*-
"""全局配置：服务地址、模型、特征库、识别参数、性能参数。"""
from pathlib import Path

# ---------------------------------------------------------------- 服务监听
HOST = "127.0.0.1"      # 仅本机可访问，隐私安全
PORT = 5000

# ---------------------------------------------------------------- InsightFace 模型
MODEL_NAME = "buffalo_l"
DET_SIZE = (640, 640)                       # 检测分辨率，越大越准但越慢
# 有 NVIDIA GPU 时可改为 ["CUDAExecutionProvider", "CPUExecutionProvider"]
PROVIDERS = ["CPUExecutionProvider"]

# ---------------------------------------------------------------- 特征库
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DB_PATH = DATA_DIR / "star_features.pkl"    # {姓名: 512维归一化向量}
FACES_DIR = DATA_DIR / "faces"              # 原始照片目录（按姓名分组）

# ---------------------------------------------------------------- 识别参数
SIMILARITY_THRESHOLD = 0.60   # 余弦相似度阈值，>阈值才认为是已知明星
MAX_FACES = 10                # 单帧最多返回的人脸数
UNKNOWN_NAME = "未知"          # 未匹配到特征库时显示的名字

# ---------------------------------------------------------------- 性能
FRAME_CACHE_SIZE = 4          # 后端帧缓存（内容哈希去重），暂停/重复帧直接命中
THREADED = True               # Flask 多线程处理并发请求

# ---------------------------------------------------------------- 日志
LOG_LEVEL = "INFO"
