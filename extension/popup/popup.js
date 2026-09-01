// ============================================================================
// popup 面板逻辑：开关 / 阈值 / 频率 / 服务状态 / 当前页面状态
// 配置写入 chrome.storage.sync，content script 监听变更即时生效
// ============================================================================

const $ = (id) => document.getElementById(id);

async function init() {
  const cfg = await loadConfig();

  $("toggle").checked = cfg.enabled;
  $("showBoxes").checked = cfg.showBoxes;
  $("threshold").value = cfg.threshold;
  $("thresholdVal").textContent = cfg.threshold.toFixed(2);
  $("interval").value = cfg.intervalMs;
  $("intervalVal").textContent = cfg.intervalMs + "ms";

  bind();
  refreshStatus();
  refreshPageStatus();
}

function bind() {
  $("toggle").addEventListener("change", (e) => {
    chrome.storage.sync.set({ enabled: e.target.checked });
  });
  $("showBoxes").addEventListener("change", (e) => {
    chrome.storage.sync.set({ showBoxes: e.target.checked });
  });
  $("threshold").addEventListener("input", (e) => {
    const v = parseFloat(e.target.value);
    $("thresholdVal").textContent = v.toFixed(2);
    chrome.storage.sync.set({ threshold: v });
  });
  $("interval").addEventListener("input", (e) => {
    const v = parseInt(e.target.value, 10);
    $("intervalVal").textContent = v + "ms";
    chrome.storage.sync.set({ intervalMs: v });
  });
  $("refresh").addEventListener("click", () => {
    refreshStatus();
    refreshPageStatus();
  });
}

// ------------------------------------------------------------ 本地服务状态
async function refreshStatus() {
  const dot = $("statusDot");
  const text = $("statusText");
  try {
    const resp = await fetch("http://127.0.0.1:5000/health");
    const data = await resp.json();
    if (resp.ok && data.model_loaded) {
      dot.className = "dot ok";
      text.textContent = `已连接 · 模型就绪 · 入库 ${data.stars} 位明星`;
    } else if (resp.ok) {
      dot.className = "dot warn";
      text.textContent = "服务在线，但模型未加载（见后端日志）";
    } else {
      dot.className = "dot err";
      text.textContent = `服务异常 HTTP ${resp.status}`;
    }
  } catch {
    dot.className = "dot err";
    text.textContent = "未连接：请先启动本地服务";
  }
}

// ------------------------------------------------------------ 当前页面状态
async function refreshPageStatus() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];
  const el = $("pageStatus");
  if (!tab || !/bilibili\.com/.test(tab.url || "")) {
    el.textContent = "当前页面不是 B 站视频页";
    return;
  }
  try {
    const resp = await chrome.tabs.sendMessage(tab.id, { type: "GET_STATUS" });
    el.textContent = resp && resp.connected
      ? "插件已在此页面运行 · 服务已连接"
      : "插件已在此页面运行";
  } catch {
    el.textContent = "插件未注入该页面（请刷新页面重试）";
  }
}

document.addEventListener("DOMContentLoaded", init);
