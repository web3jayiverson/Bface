// ============================================================================
// Service Worker（MV3）：轻量职责——根据识别服务连接状态同步插件角标
// ============================================================================

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "SERVICE_STATUS") {
    const tabId = sender.tab && sender.tab.id;
    if (tabId != null) {
      if (msg.connected) {
        chrome.action.setBadgeText({ tabId, text: "" });
      } else {
        chrome.action.setBadgeText({ tabId, text: "!" });
        chrome.action.setBadgeBackgroundColor({ tabId, color: "#e02020" });
      }
    }
    sendResponse({ ok: true });
  }
  return true; // 保持消息通道
});
