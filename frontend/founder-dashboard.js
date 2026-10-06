// Founder Dashboard JavaScript
// Handles authentication and data fetching for the founder-only usage tracker

const isLocalFrontend = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const defaultFounderApiUrl = isLocalFrontend ? "http://127.0.0.1:8000" : "https://buildreadyai.onrender.com";
const rawFounderApiUrl = typeof window.BUILDREADY_CONFIG?.apiBaseUrl === "string" ? window.BUILDREADY_CONFIG.apiBaseUrl : defaultFounderApiUrl;
const API_BASE_URL = rawFounderApiUrl.replace(/\/+$/, "");
const STORAGE_KEY = "founder_session_key";

// DOM Elements
const loginModal = document.getElementById("loginModal");
const loginForm = document.getElementById("loginForm");
const founderKeyInput = document.getElementById("founderKey");
const loginError = document.getElementById("loginError");
const dashboardContent = document.getElementById("dashboardContent");
const logoutBtn = document.getElementById("logoutBtn");
const periodSelect = document.getElementById("periodSelect");
const refreshBtn = document.getElementById("refreshBtn");
const loadingOverlay = document.getElementById("loadingOverlay");

// Summary card elements
const totalUsersEl = document.getElementById("totalUsers");
const totalRequestsEl = document.getElementById("totalRequests");
const inputTokensEl = document.getElementById("inputTokens");
const outputTokensEl = document.getElementById("outputTokens");
const totalTokensEl = document.getElementById("totalTokens");
const avgTokensPerUserEl = document.getElementById("avgTokensPerUser");
const avgTokensPerRequestEl = document.getElementById("avgTokensPerRequest");
const successfulEl = document.getElementById("successful");
const failedEl = document.getElementById("failed");
const highestUserEl = document.getElementById("highestUser");
const lowestUserEl = document.getElementById("lowestUser");

// Table elements
const usersTableBody = document.getElementById("usersTableBody");
const eventsTableBody = document.getElementById("eventsTableBody");

// Initialize
function init() {
    const storedKey = sessionStorage.getItem(STORAGE_KEY);
    if (storedKey) {
        showDashboard(storedKey);
    }

    loginForm.addEventListener("submit", handleLogin);
    logoutBtn.addEventListener("click", handleLogout);
    periodSelect.addEventListener("change", loadData);
    refreshBtn.addEventListener("click", loadData);
}

// Handle login
async function handleLogin(e) {
    e.preventDefault();
    const key = founderKeyInput.value.trim();

    if (!key) {
        showError("Please enter your founder secret key.");
        return;
    }

    loginError.textContent = "";
    founderKeyInput.disabled = true;
    e.target.querySelector("button").disabled = true;

    try {
        // Test the key by fetching stats
        await fetchWithAuth("/founder/stats?period=all", key);
        sessionStorage.setItem(STORAGE_KEY, key);
        showDashboard(key);
    } catch (error) {
        showError(error.message || "Invalid founder secret key. Please try again.");
        founderKeyInput.disabled = false;
        e.target.querySelector("button").disabled = false;
    }
}

// Show error message
function showError(message) {
    loginError.textContent = message;
}

// Show dashboard
function showDashboard(key) {
    loginModal.hidden = true;
    dashboardContent.hidden = false;
    loadData();
}

// Handle logout
function handleLogout() {
    sessionStorage.removeItem(STORAGE_KEY);
    dashboardContent.hidden = true;
    loginModal.hidden = false;
    founderKeyInput.value = "";
    founderKeyInput.disabled = false;
    loginForm.querySelector("button").disabled = false;
    loginError.textContent = "";
}

// Load all data
async function loadData() {
    const period = periodSelect.value;
    const key = sessionStorage.getItem(STORAGE_KEY);

    if (!key) {
        handleLogout();
        return;
    }

    showLoading(true);

    try {
        const [stats, users, events] = await Promise.all([
            fetchWithAuth(`/founder/stats?period=${period}`, key),
            fetchWithAuth(`/founder/users?period=${period}`, key),
            fetchWithAuth("/founder/events?limit=50", key)
        ]);

        updateSummaryCards(stats);
        updateUsersTable(users);
        updateEventsTable(events);
    } catch (error) {
        console.error("Failed to load data:", error);
        if (error.status === 401 || error.status === 403 || error.status === 503) {
            handleLogout();
            showError(error.status === 503 ? error.message : "Session expired or invalid founder key. Please log in again.");
        } else {
            alert(error.message || "Failed to load data. Please check your connection and try again.");
        }
    } finally {
        showLoading(false);
    }
}

async function fetchWithAuth(path, key) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            headers: {
                "X-Founder-Key": key
            }
        });
    } catch (error) {
        throw new Error(`Unable to connect to BuildReady at ${API_BASE_URL}. Check that the backend is running.`);
    }

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const message = typeof data.detail === "string" ? data.detail : `HTTP ${response.status}: ${response.statusText}`;
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }

    return response.json();
}

// Update summary cards
function updateSummaryCards(stats) {
    totalUsersEl.textContent = formatNumber(stats.total_users);
    totalRequestsEl.textContent = formatNumber(stats.total_requests);
    inputTokensEl.textContent = formatNumber(stats.input_tokens);
    outputTokensEl.textContent = formatNumber(stats.output_tokens);
    totalTokensEl.textContent = formatNumber(stats.total_tokens);
    avgTokensPerUserEl.textContent = formatNumber(stats.avg_tokens_per_user);
    avgTokensPerRequestEl.textContent = formatNumber(stats.avg_tokens_per_request);
    successfulEl.textContent = formatNumber(stats.successful);
    failedEl.textContent = formatNumber(stats.failed);

    if (stats.highest_usage_user) {
        highestUserEl.textContent = `${stats.highest_usage_user.user_id} (${formatNumber(stats.highest_usage_user.total_tokens)} tokens)`;
    } else {
        highestUserEl.textContent = "No data";
    }

    if (stats.lowest_usage_user) {
        lowestUserEl.textContent = `${stats.lowest_usage_user.user_id} (${formatNumber(stats.lowest_usage_user.total_tokens)} tokens)`;
    } else {
        lowestUserEl.textContent = "No data";
    }
}

// Update users table
function updateUsersTable(users) {
    if (!users || users.length === 0) {
        usersTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="no-data">No usage data recorded yet.</td>
            </tr>
        `;
        return;
    }

    usersTableBody.innerHTML = users.map(user => `
        <tr>
            <td>${escapeHtml(user.user_id)}</td>
            <td>${formatNumber(user.requests)}</td>
            <td>${formatNumber(user.input_tokens)}</td>
            <td>${formatNumber(user.output_tokens)}</td>
            <td>${formatNumber(user.total_tokens)}</td>
            <td>${formatTimestamp(user.last_active)}</td>
        </tr>
    `).join("");
}

// Update events table
function updateEventsTable(events) {
    if (!events || events.length === 0) {
        eventsTableBody.innerHTML = `
            <tr>
                <td colspan="9" class="no-data">No usage events recorded yet.</td>
            </tr>
        `;
        return;
    }

    eventsTableBody.innerHTML = events.map(event => `
        <tr>
            <td>${event.id}</td>
            <td>${escapeHtml(event.user_id)}</td>
            <td>${formatTimestamp(event.timestamp)}</td>
            <td>${escapeHtml(event.feature)}</td>
            <td>${formatNumber(event.input_tokens)}</td>
            <td>${formatNumber(event.output_tokens)}</td>
            <td>${formatNumber(event.total_tokens)}</td>
            <td class="${event.success ? 'status-success' : 'status-failed'}">${event.success ? 'Yes' : 'No'}</td>
            <td>${escapeHtml(event.model_used || '-')}</td>
        </tr>
    `).join("");
}

// Format number with commas
function formatNumber(num) {
    if (num === null || num === undefined) return "-";
    return num.toLocaleString();
}

// Format timestamp
function formatTimestamp(timestamp) {
    if (!timestamp) return "-";
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (e) {
        return timestamp;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return "-";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Show/hide loading overlay
function showLoading(show) {
    loadingOverlay.hidden = !show;
}

// Initialize on DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
