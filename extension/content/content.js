// ============================================================================
// 主控逻辑：轮询捕获帧 → 请求本地识别服务 → 渲染覆盖层
//  - 视频未播放/页面隐藏时跳过，避免空转
//  - 请求进行中不重复发送（节流）
//  - 相同帧跳过（暂停/画面静止）
//  - 服务未连接时显示提示条，每 5s 自动探测恢复
// ============================================================================
(() => {
  "use strict";

  let video = null;
  let timer = null;
  let inFlight = false;
  let lastFrameKey = null;
  let serviceOk = false;
  let lastHealth = null;
  let prevFaces = [];
  let toastEl = null;
  let toastTimer = null;

  // ---------------------------------------------------------------- 初始化
  async function init() {
    await loadConfig();
    listenConfigChange(onConfigChange);
    chrome.runtime.onMessage.addListener(onMessage);
    watchForVideo();
    setInterval(checkHealth, 5000);
    checkHealth();
  }

  // ----------------------------------------------------------- 视频元素探测
  function watchForVideo() {
    const tryFind = () => {
      if (video) return;
      const v = FrameCapture.findVideo();
      if (v) {
        video = v;
        Overlay.attach(v);
        startLoop();
      }
    };
    tryFind();
    // B 站播放器异步加载，监听 DOM 变化
    new MutationObserver(tryFind).observe(document.body, {
      childList: true,
      subtree: true,
    });
    setInterval(tryFind, 3000); // 兜底轮询
  }

  // ---------------------------------------------------------------- 主循环
  function startLoop() {
    if (timer) clearInterval(timer);
    timer = setInterval(tick, CONFIG.intervalMs);
  }

  async function tick() {
    if (!CONFIG.enabled || !video || document.hidden) return;
    if (video.paused || video.ended) {
      if (prevFaces.length) {
        Overlay.clear();
        prevFaces = [];
      }
      return;
    }
    if (inFlight) return;

    const frame = FrameCapture.capture(video);
    if (!frame) return;

    // 画面未变化时跳过请求（暂停或静止帧）
    const key = frame.dataUrl.slice(-64);
    if (key === lastFrameKey) return;
    lastFrameKey = key;

    inFlight = true;
    try {
      const faces = await requestRecognize(frame.dataUrl);
      if (video && !video.paused) {
        Overlay.render(smoothFaces(faces), frame.width, frame.height);
      }
      setService(true);
    } catch (err) {
      setService(false, err.message);
      Overlay.clear();
      prevFaces = [];
    } finally {
      inFlight = false;
    }
  }

  // --------------------------------------------------------------- 网络请求
  async function requestRecognize(dataUrl) {
    const resp = await fetch(`${CONFIG.apiBase}/recognize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl }),
    });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new Error(body.error || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    return data.faces || [];
  }

  async function checkHealth() {
    try {
      const resp = await fetch(`${CONFIG.apiBase}/health`, { method: "GET" });
      if (resp.ok) {
        lastHealth = await resp.json();
        setService(true);
      } else {
        setService(false, `HTTP ${resp.status}`);
      }
    } catch {
      setService(false);
    }
  }

  // ---------------------------------------------------------------- 状态提示
  function setService(ok, errMsg) {
    if (ok === serviceOk) return;
    const wasOk = serviceOk;
    serviceOk = ok;

    chrome.runtime.sendMessage({ type: "SERVICE_STATUS", connected: ok })
      .catch(() => {});

    if (!ok) {
      showToast(errMsg
        ? `识别服务错误：${errMsg}`
        : "识别服务未连接，请先启动本地服务（backend/scripts/start.bat）");
    } else if (!wasOk) {
      const stars = lastHealth && typeof lastHealth.stars === "number"
        ? lastHealth.stars : "?";
      showToast(`识别服务已连接 · 已入库 ${stars} 位明星`, 2500);
    }
  }

  function showToast(text, timeout = 6000) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.id = "bface-toast";
      toastEl.style.cssText = [
        "position:fixed",
        "right:16px",
        "bottom:16px",
        "z-index:2147483647",
        "background:rgba(20,24,34,.92)",
        "color:#fff",
        "font:13px/1.5 'Microsoft YaHei','PingFang SC',sans-serif",
        "padding:10px 14px",
        "border-radius:8px",
        "box-shadow:0 4px 16px rgba(0,0,0,.35)",
        "max-width:340px",
        "transition:opacity .3s",
      ].join(";");
      (document.body || document.documentElement).appendChild(toastEl);
    }
    toastEl.textContent = text;
    toastEl.style.opacity = "1";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.style.opacity = "0"; }, timeout);
  }

  // ------------------------------------------------------------ 识别平滑去抖
  // 前一帧已确认为已知明星、当前帧闪成"未知"时，保持原名字（时间维度上的迟滞）
  function smoothFaces(faces) {
    const out = [];
    for (const f of faces) {
      const copy = { ...f };
      if (f.name === CONFIG.unknownLabel) {
        for (const p of prevFaces) {
          if (p.name !== CONFIG.unknownLabel && iou(f.bbox, p.bbox) > 0.5) {
            copy.name = p.name;
            break;
          }
        }
      }
      out.push(copy);
    }
    prevFaces = out;
    return out;
  }

  function iou(a, b) {
    const x1 = Math.max(a[0], b[0]);
    const y1 = Math.max(a[1], b[1]);
    const x2 = Math.min(a[2], b[2]);
    const y2 = Math.min(a[3], b[3]);
    const inter = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
    const areaA = (a[2] - a[0]) * (a[3] - a[1]);
    const areaB = (b[2] - b[0]) * (b[3] - b[1]);
    const union = areaA + areaB - inter;
    return union > 0 ? inter / union : 0;
  }

  // ------------------------------------------------------------------ 配置变更
  function onConfigChange() {
    if (CONFIG.enabled) {
      if (!timer && video) startLoop();
    } else {
      if (timer) { clearInterval(timer); timer = null; }
      Overlay.clear();
      prevFaces = [];
    }
  }

  // ---------------------------------------------------------------- 消息处理
  function onMessage(msg, _sender, sendResponse) {
    if (!msg) return;
    if (msg.type === "GET_STATUS") {
      sendResponse({
        enabled: CONFIG.enabled,
        connected: serviceOk,
        stars: lastHealth ? lastHealth.stars : null,
        threshold: CONFIG.threshold,
      });
    } else if (msg.type === "SET_ENABLED") {
      CONFIG.enabled = !!msg.enabled;
      onConfigChange();
      sendResponse({ ok: true });
    }
  }

  init();
})();
