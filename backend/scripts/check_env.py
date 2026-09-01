# -*- coding: utf-8 -*-
"""环境自检：Python 版本、依赖、模型、特征库是否就绪。

用法:  cd backend && python scripts/check_env.py
"""
import importlib
import sys
from pathlib import Path

# 使 scripts/ 下的脚本能 import backend 目录中的 config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402


def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, str(exc)
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")
    return ok


def main():
    print(f"Python 版本: {sys.version.split()[0]}")
    results = []
    results.append(check("numpy", lambda: (True, importlib.import_module("numpy").__version__)))
    results.append(check("opencv", lambda: (True, importlib.import_module("cv2").__version__)))
    results.append(check("flask", lambda: (True, importlib.import_module("flask").__version__)))
    results.append(check("insightface", lambda: (True, importlib.import_module("insightface").__version__)))
    results.append(check("onnxruntime", lambda: (True, importlib.import_module("onnxruntime").__version__)))

    model_dir = Path.home() / ".insightface" / "models" / config.MODEL_NAME
    results.append(check(
        f"buffalo_l 模型",
        lambda: (True, "已安装") if model_dir.exists()
        else (False, "未安装（首次运行 app.py 会自动下载，或手动放置到 ~/.insightface/models）"),
    ))
    results.append(check(
        "明星特征库",
        lambda: (True, str(config.DB_PATH)) if config.DB_PATH.exists()
        else (False, "未构建，先准备照片后运行: python build_db.py"),
    ))

    failed = sum(1 for r in results if not r)
    print(f"\n自检{'全部通过' if failed == 0 else f'完成，存在 {failed} 项问题，请按提示修复'}")


if __name__ == "__main__":
    main()
