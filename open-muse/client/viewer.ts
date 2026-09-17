import RFB from "@novnc/novnc";

const params = new URLSearchParams(window.location.search);
const path = params.get("path");
const screen = document.querySelector<HTMLElement>("#screen");

if (!path || !screen || !path.startsWith("/api/conversations/")) {
  throw new Error("The OpenMuse viewer link is invalid. Return to the conversation and try again.");
}

const websocketUrl = new URL(path, window.location.href);
websocketUrl.protocol = websocketUrl.protocol === "https:" ? "wss:" : "ws:";
const viewer = new RFB(screen, websocketUrl.href, { shared: true });
viewer.viewOnly = params.get("mode") !== "read_write";
viewer.scaleViewport = true;
viewer.resizeSession = false;
viewer.focusOnClick = true;
viewer.background = "#080b12";
viewer.addEventListener("connect", () => {
  window.parent.postMessage({ type: "openmuse.viewer.connected" }, window.location.origin);
});
viewer.addEventListener("disconnect", () => {
  window.parent.postMessage({ type: "openmuse.viewer.disconnected" }, window.location.origin);
});
