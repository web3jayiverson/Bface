// ============================================================================
// 覆盖层渲染：在人脸位置上方绘制姓名标签
//  - 覆盖层容器与 <video> 的父级对齐，用百分比坐标映射（自动适配缩放/全屏）
//  - 标签默认在人脸框上方，人脸贴近视频顶部时自动翻转到框内，避免被裁切
// ============================================================================

const Overlay = (() => {
  let container = null;
  let video = null;
  let labels = [];

  function ensureContainer() {
    if (container) return container;
    container = document.createElement("div");
    container.id = "bface-overlay";
    container.style.cssText =
      "position:absolute;pointer-events:none;z-index:999999;overflow:hidden;";
    return container;
  }

  function attach(targetVideo) {
    video = targetVideo;
    const parent = targetVideo.parentElement;
    if (!parent) return;

    const el = ensureContainer();
    // 父级需为定位上下文
    if (getComputedStyle(parent).position === "static") {
      parent.style.position = "relative";
    }
    if (el.parentElement !== parent) parent.appendChild(el);

    syncRect();
    if ("ResizeObserver" in window) {
      if (!attach._ro) {
        attach._ro = new ResizeObserver(() => syncRect());
        attach._ro.observe(targetVideo);
      }
    } else {
      window.addEventListener("resize", syncRect);
      document.addEventListener("fullscreenchange", syncRect);
    }
  }

  function syncRect() {
    if (!video || !container || !video.parentElement) return;
    const vr = video.getBoundingClientRect();          // 含 transform 的实际显示区域
    const pr = video.parentElement.getBoundingClientRect();
    container.style.left = (vr.left - pr.left) + "px";
    container.style.top = (vr.top - pr.top) + "px";
    container.style.width = vr.width + "px";
    container.style.height = vr.height + "px";
  }

  /**
   * 渲染识别结果。
   * @param {Array} faces       [{bbox:[x1,y1,x2,y2], name}]
   * @param {number} frameW     捕获帧原始宽度
   * @param {number} frameH     捕获帧原始高度
   */
  function render(faces, frameW, frameH) {
    clear();
    if (!faces || !faces.length || !container) return;

    // 标签字号随视频大小自适应
    const fs = Math.max(11, Math.min(22, Math.floor(container.clientWidth / 70)));

    for (const face of faces) {
      const [x1, y1, x2, y2] = face.bbox;
      const px = (x1 / frameW) * 100;
      const py = (y1 / frameH) * 100;
      const pw = ((x2 - x1) / frameW) * 100;
      const ph = ((y2 - y1) / frameH) * 100;
      const known = !!face.name && face.name !== CONFIG.unknownLabel;

      const box = document.createElement("div");
      const boxStyles = [
        "position:absolute",
        `left:${px}%`,
        `top:${py}%`,
        `width:${pw}%`,
        `height:${ph}%`,
        "box-sizing:border-box",
      ];
      if (CONFIG.showBoxes) {
        boxStyles.push("border:2px solid rgba(0,170,255,.9)", "border-radius:6px");
      }
      box.style.cssText = boxStyles.join(";");

      const tag = document.createElement("div");
      tag.textContent = known ? face.name : CONFIG.unknownLabel;
      // 人脸贴近视频顶部(14%)时标签放到框内，否则放在框上方
      const above = py > 14;
      tag.style.cssText = [
        "position:absolute",
        "left:0",
        "top:0",
        above ? "transform:translateY(-100%) translateY(-4px)" : "",
        "background:" + (known
          ? "linear-gradient(135deg,#0091ff,#0060d6)"
          : "rgba(80,80,80,.88)"),
        "color:#fff",
        `font:600 ${fs}px/1.3 'Microsoft YaHei','PingFang SC',sans-serif`,
        "padding:2px 8px",
        "border-radius:4px",
        "white-space:nowrap",
        "text-shadow:0 1px 2px rgba(0,0,0,.4)",
      ].join(";");

      box.appendChild(tag);
      container.appendChild(box);
      labels.push(box);
    }
  }

  function clear() {
    labels.forEach((l) => l.remove());
    labels = [];
  }

  return { attach, render, clear };
})();
