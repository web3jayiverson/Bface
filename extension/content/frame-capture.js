// ============================================================================
// 视频帧捕获：定位 B 站播放器 <video>，用 canvas 抽帧并编码为 base64 JPEG
// ============================================================================

const FrameCapture = {
  // B 站播放器选择器（按优先级），页面结构更新时可在此补充
  SELECTORS: [
    "#bilibili-player video",
    ".bilibili-player-video video",
    "#bilibili-player-wrap video",
    "#bilibiliPlayer video",
    "video",
  ],

  findVideo() {
    for (const sel of this.SELECTORS) {
      const el = document.querySelector(sel);
      if (el && el.videoWidth > 0) return el;
    }
    // 兜底：取页面上第一个有真实尺寸的 video
    const videos = document.querySelectorAll("video");
    for (const v of videos) {
      if (v.videoWidth > 0) return v;
    }
    return null;
  },

  /**
   * 抓取当前帧。
   * @returns {{width:number, height:number, dataUrl:string}|null}
   *          dataUrl 为 "data:image/jpeg;base64,..."
   */
  capture(video) {
    if (!video || !video.videoWidth || !video.videoHeight) return null;

    const scale = Math.min(1, CONFIG.maxFrameWidth / video.videoWidth);
    const w = Math.max(1, Math.round(video.videoWidth * scale));
    const h = Math.max(1, Math.round(video.videoHeight * scale));

    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, w, h);
    return {
      width: w,
      height: h,
      dataUrl: canvas.toDataURL("image/jpeg", CONFIG.jpegQuality),
    };
  },
};
