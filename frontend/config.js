window.BUILDREADY_CONFIG = window.BUILDREADY_CONFIG || {};
const isLocalFrontend = ["localhost", "127.0.0.1"].includes(window.location.hostname);
if (typeof window.BUILDREADY_CONFIG.apiBaseUrl === "undefined") {
    window.BUILDREADY_CONFIG.apiBaseUrl = isLocalFrontend ? "http://127.0.0.1:8000" : "https://buildreadyai.onrender.com";
}

