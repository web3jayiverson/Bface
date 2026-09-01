# B站视频明星人脸识别浏览器插件

在观看 B 站视频（综艺 / 访谈 / 影视剪辑）时，自动识别画面中的中国明星并实时叠加显示姓名。
**所有图像数据均在本机处理，不上传任何内容。**

- 前端：Chrome 扩展（Manifest V3），捕获视频帧 → 绘制姓名标签
- 后端：Python + Flask + InsightFace（本地识别服务，`http://127.0.0.1:5000`）
- 数据：明星 512 维人脸特征库 `star_features.pkl`

---

## 目录结构

```
Bface/
├── Bface.md                  # 需求文档（原始）
├── README.md                 # 本文档
├── docs/
│   └── DESIGN.md             # 详细设计文档（架构/接口/模块/测试）
├── backend/                  # 本地识别服务 (Python)
│   ├── app.py                # Flask 入口（/health, /recognize）
│   ├── config.py             # 全局配置
│   ├── recognizer.py         # 检测+识别核心（InsightFace + 余弦比对）
│   ├── build_db.py           # 明星特征库构建脚本
│   ├── test_api.py           # API 单元测试
│   ├── requirements.txt
│   └── scripts/
│       ├── start.bat         # Windows 一键启动
│       ├── start.sh          # macOS/Linux 一键启动
│       └── check_env.py      # 环境自检
├── extension/                # Chrome 插件
│   ├── manifest.json
│   ├── content/              # content script（config/frame-capture/overlay/content）
│   ├── popup/                # 设置面板
│   ├── background/           # service worker（角标）
│   └── icons/
├── data/                     # 明星数据集与特征库（不入库 Git）
│   └── README.md
└── tools/
    └── make_icons.ps1        # 插件图标生成脚本
```

## 快速开始（3 步）

### 1. 启动本地识别服务

```bash
cd backend
# Windows:
scripts\start.bat
# macOS / Linux:
bash scripts/start.sh
```

首次运行自动创建虚拟环境并安装依赖（`insightface` 首次运行会自动下载
buffalo_l 模型，需联网，约 300MB）。启动成功后会看到：

```
[app] 识别服务启动: http://127.0.0.1:5000
[app] 模型加载: 成功
```

> 若只想检查环境：`python scripts/check_env.py`

### 2. 准备明星特征库（可选，识别必需）

`data/faces/` 下按姓名建文件夹放照片（每人 ≥3 张），然后：

```bash
cd backend
python build_db.py
```

完成后重启服务，日志会显示 `特征库加载完成: N 位明星`。
（详见 `data/README.md`；未构建特征库时服务仍可启动，但所有人脸显示"未知"。）

### 3. 加载 Chrome 插件

1. 打开 `chrome://extensions/`，开启右上角"开发者模式"；
2. 点击"加载已解压的扩展程序"，选择本项目的 `extension/` 目录；
3. 打开任意 B 站视频页面播放，识别标签即自动出现；
4. 点击工具栏插件图标可开关识别、调整阈值与频率、查看服务状态。

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 自动识别 | 播放中每 ~300ms 采样一帧，检测人脸并与本地明星库比对 |
| 实时标签 | 姓名标签显示在人脸框上方，随视频缩放/全屏自适应 |
| 未知人脸 | 未匹配到特征库显示灰色"未知"标签 |
| 开关控制 | popup 一键启用/禁用，配置持久化（chrome.storage.sync） |
| 服务检测 | 服务未启动时页面提示"服务未连接"，每 5s 自动重连 |
| 隐私安全 | 帧数据仅发送到 127.0.0.1 本地服务，绝不外传 |
| 状态角标 | 服务断开时插件图标显示红色 "!" |

## 配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| 相似度阈值 | 0.60 | 越高越严格，未知脸越多 |
| 识别频率 | 300ms | 越低越流畅，CPU 占用越高 |
| 帧压缩质量 | 0.7 | JPEG 质量 |
| 发送帧最大宽度 | 960px | 降低传输与计算量 |

以上可在插件 popup 中实时调整；高级参数见 `backend/config.py` 与
`extension/content/config.js`。

## 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 服务状态：模型/特征库就绪情况、入库明星数 |
| POST | `/recognize` | 输入 base64 帧，返回 `{faces:[{bbox,name,confidence}], processing_time}` |

完整协议见 `docs/DESIGN.md` §6。

## 测试

```bash
cd backend
python -m unittest test_api -v     # API 层测试（无需真实人脸图）
```

端到端测试：启动服务 + 加载插件 → 播放含明星的视频，观察标签；
对照 `Bface.md` §5 测试计划逐项验收。

## 常见问题

| 现象 | 处理 |
|------|------|
| 页面提示"识别服务未连接" | 运行 `scripts/start.bat`；确认 5000 端口未被占用 |
| 所有人脸都显示"未知" | 尚未构建特征库：准备照片后运行 `python build_db.py` |
| 模型加载失败 | 运行 `python scripts/check_env.py` 定位；网络受限时手动下载 buffalo_l 放到 `~/.insightface/models/` |
| 识别慢 / CPU 高 | popup 中调大识别频率（如 500ms）或降低 `DET_SIZE`；有 NVIDIA 显卡时在 `config.py` 改用 CUDA provider |
| B 站页面改版后不识别 | 更新 `extension/content/frame-capture.js` 中的播放器选择器 |

## 路线图（超出 MVP）

- 特征库扩展至 CN-Celeb（数百至上千位明星），支持动态热更新
- 场景变化触发识别（帧差异检测）代替固定轮询，进一步降 CPU
- 可选 GPU 推理（onnxruntime CUDA），支持 ≥5fps
- 打包 crx / 上架 Chrome 应用商店

## 参考

- InsightFace: https://github.com/deepinsight/insightface
- Chrome Extensions 文档: https://developer.chrome.com/docs/extensions/
- Flask: https://flask.palletsprojects.com/
# Bface
