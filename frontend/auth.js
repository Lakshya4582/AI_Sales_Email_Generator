const API_BASE = (window.APP_CONFIG && window.APP_CONFIG.API_BASE) || "http://127.0.0.1:8000";
const TOKEN_KEY = "aiemail_token";
const EMAIL_KEY = "aiemail_user";

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getUserEmail() {
    return localStorage.getItem(EMAIL_KEY);
}

function setAuth(token, email) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(EMAIL_KEY, email);
}

function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = "login.html";
        return false;
    }
    return true;
}

function redirectIfAuthenticated() {
    if (getToken()) window.location.href = "index.html";
}

async function apiFetch(path, options = {}) {
    const token = getToken();
    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type") && options.body) {
        headers.set("Content-Type", "application/json");
    }
    if (token) headers.set("Authorization", `Bearer ${token}`);

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (response.status === 401) {
        clearAuth();
        window.location.href = "login.html";
        throw new Error("Session expired. Please log in again.");
    }
    return response;
}

function logout() {
    clearAuth();
    window.location.href = "login.html";
}
