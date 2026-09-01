// ============================================================================
// 全局配置与设置存取（content script 与 popup 共用，chrome.storage.sync 持久化）
// ============================================================================

const DEFAULT_CONFIG = {
  enabled: true,          // 总开关
  threshold: 0.6,         // 相似度阈值（0.40~0.90）
  intervalMs: 300,        // 识别采样间隔（毫秒）
  jpegQuality: 0.7,       // 帧 JPEG 压缩质量
  maxFrameWidth: 960,     // 发送帧的最大宽度（降低传输与计算量）
  apiBase: "http://127.0.0.1:5000", // 本地识别服务地址
  showBoxes: true,        // 是否显示人脸框
  unknownLabel: "未知",    // 未匹配明星时的显示文本
};

const CONFIG = { ...DEFAULT_CONFIG };

async function loadConfig() {
  const stored = await chrome.storage.sync.get(DEFAULT_CONFIG);
  Object.assign(CONFIG, stored);
  return CONFIG;
}

function listenConfigChange(callback) {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "sync") return;
    let changed = false;
    for (const [key, { newValue }] of Object.entries(changes)) {
      if (key in CONFIG) {
        CONFIG[key] = newValue;
        changed = true;
      }
    }
    if (changed && callback) callback(CONFIG);
  });
}
