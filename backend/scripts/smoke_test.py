# -*- coding: utf-8 -*-
"""路由冒烟测试（开发/CI 用）：无需安装 insightface 与模型。

用 stub 替换 insightface.app.FaceAnalysis，验证 Flask 的路由、参数校验、
base64 解码、识别流程与错误码逻辑。真实识别准确率需在装好依赖后
运行 test_api.py 与端到端人工测试验证。

用法: cd backend && python scripts/smoke_test.py
依赖: flask numpy opencv-python-headless（轻量）
"""
import base64
import sys
import types
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _install_insightface_stub():
    """在导入 recognizer/app 之前注入 insightface 桩模块。"""
    fake = types.ModuleType("insightface")
    app_mod = types.ModuleType("insightface.app")

    class FakeFace:
        bbox = [10.0, 20.0, 90.0, 110.0]
        embedding = [0.1] * 512

    class FaceAnalysis:
        def __init__(self, *args, **kwargs):
            pass

        def prepare(self, *args, **kwargs):
            pass

        def get(self, image):
            # 约定：近黑图返回 1 张人脸，其余返回空（用于验证两种分支）
            if image is not None and float(image.mean()) < 5:
                return [FakeFace()]
            return []

    app_mod.FaceAnalysis = FaceAnalysis
    fake.app = app_mod
    sys.modules["insightface"] = fake
    sys.modules["insightface.app"] = app_mod


_install_insightface_stub()
sys.path.insert(0, str(BACKEND_DIR))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import app as app_module  # noqa: E402


def jpeg_b64(image):
    ok, buf = cv2.imencode(".jpg", image)
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def main():
    client = app_module.app.test_client()
    passed = 0

    def expect(name, cond, detail=""):
        nonlocal passed
        if cond:
            passed += 1
            print(f"  [OK] {name}")
        else:
            print(f"  [FAIL] {name} {detail}")
            raise SystemExit(1)

    print("[1] GET /health")
    r = client.get("/health")
    expect("状态码 200", r.status_code == 200, r.status_code)
    d = r.get_json()
    expect("含 model_loaded", "model_loaded" in d)
    expect("含 stars", "stars" in d)

    print("[2] POST /recognize 近黑图（stub 返回 1 张脸）")
    r = client.post("/recognize", json={"image": jpeg_b64(np.zeros((64, 64, 3), dtype=np.uint8))})
    expect("状态码 200", r.status_code == 200, r.status_code)
    faces = r.get_json()["faces"]
    expect("返回 1 张人脸", len(faces) == 1, len(faces))
    expect("bbox 为 4 元素", len(faces[0]["bbox"]) == 4)
    expect("未建库时姓名为'未知'", faces[0]["name"] == "未知", faces[0]["name"])

    print("[3] POST /recognize 噪声图（stub 返回空）")
    noise = np.random.randint(60, 255, (64, 64, 3), dtype=np.uint8)
    r = client.post("/recognize", json={"image": jpeg_b64(noise)})
    expect("状态码 200", r.status_code == 200, r.status_code)
    expect("faces 为空", r.get_json()["faces"] == [])

    print("[4] 参数校验")
    r = client.post("/recognize", json={})
    expect("缺 image 字段 -> 400", r.status_code == 400, r.status_code)
    r = client.post("/recognize", json={"image": "not-base64!!"})
    expect("非法 base64 -> 400", r.status_code == 400, r.status_code)

    print("[5] CORS 头")
    r = client.get("/health")
    expect("Access-Control-Allow-Origin: *",
           r.headers.get("Access-Control-Allow-Origin") == "*")

    print(f"\n冒烟测试通过: {passed} 项")


if __name__ == "__main__":
    main()
