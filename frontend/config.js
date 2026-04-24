// =============================================================================
//  Frontend runtime config
// -----------------------------------------------------------------------------
//  One line to edit when deploying: set API_BASE to your deployed backend URL.
//  Local dev: http://127.0.0.1:8000
//  Production example: https://ai-email-backend.onrender.com
// =============================================================================

window.APP_CONFIG = {
    API_BASE: resolveApiBase(),
};

function resolveApiBase() {
    const host = window.location.hostname;
    const isLocal =
        host === "127.0.0.1" ||
        host === "localhost" ||
        host === "" ||
        window.location.protocol === "file:";

    if (isLocal) return "http://127.0.0.1:8000";

    // 👇 DEPLOYMENT: replace the URL below with your Render backend URL.
    return "https://laksh-ai-sales-email-generator.onrender.com/";
}
