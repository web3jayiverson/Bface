# -*- coding: utf-8 -*-
"""API 单元测试（无需真实人脸图片）。

运行:  cd backend && python -m unittest test_api -v
"""
import base64
import unittest

import cv2
import numpy as np

import app as app_module


def blank_image_b64():
    """生成一张纯色 JPEG 的 base64 data URL（无人脸）。"""
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


class TestApi(unittest.TestCase):

    def setUp(self):
        self.client = app_module.app.test_client()

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("model_loaded", data)
        self.assertIn("stars", data)
        self.assertEqual(data["status"], "ok")

    def test_recognize_blank_image(self):
        """纯色图无人脸：模型就绪应返回 200 且 faces 为空列表；
        模型未加载时按设计返回 500 'Model not loaded'。"""
        resp = self.client.post("/recognize", json={"image": blank_image_b64()})
        if app_module.recognizer.model_loaded:
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json()["faces"], [])
        else:
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.get_json()["error"], "Model not loaded")

    def test_missing_image_field(self):
        resp = self.client.post("/recognize", json={})
        self.assertEqual(resp.status_code, 400)

    def test_invalid_image_data(self):
        resp = self.client.post("/recognize", json={"image": "not-base64!!"})
        self.assertEqual(resp.status_code, 400)

    def test_cors_header(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")


if __name__ == "__main__":
    unittest.main()
