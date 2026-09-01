#!/usr/bin/env bash
# ============================================================
#  B站明星人脸识别 - 本地服务一键启动 (macOS / Linux)
#  首次运行自动创建虚拟环境并安装依赖
# ============================================================
set -e
cd "$(dirname "$0")/.."
VENV_DIR=".venv"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "[1/3] 创建虚拟环境 .venv ..."
  python3 -m venv "$VENV_DIR"
else
  echo "[1/3] 虚拟环境已存在"
fi

echo "[2/3] 安装依赖 ..."
"$VENV_DIR/bin/python" -m pip install -r requirements.txt -q

echo "[3/3] 启动识别服务 (http://127.0.0.1:5000, Ctrl+C 退出) ..."
"$VENV_DIR/bin/python" app.py
