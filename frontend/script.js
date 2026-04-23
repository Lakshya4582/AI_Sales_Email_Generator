const userEmailEl = document.getElementById("user-email");
if (userEmailEl) userEmailEl.textContent = getUserEmail() || "";

// Tracks which history entry the visible result belongs to, for "Save edits".
let currentHistoryId = null;

const els = {
    btn: document.getElementById("generate-btn"),
    product: document.getElementById("product"),
    audience: document.getElementById("audience"),
    tone: document.getElementById("tone"),
    length: document.getElementById("length"),
    resultCard: document.getElementById("result-card"),
    errorCard: document.getElementById("error-card"),
    errorMsg: document.getElementById("error-message"),
    subject: document.getElementById("out-subject"),
    body: document.getElementById("out-body"),
    cta: document.getElementById("out-cta"),
    copyAll: document.getElementById("copy-all-btn"),
};

function setLoading(isLoading) {
    els.btn.disabled = isLoading;
    els.btn.classList.toggle("loading", isLoading);
    els.btn.querySelector(".btn-label").textContent = isLoading
        ? "Generating"
        : "Generate Email";
}

function show(el) { el.hidden = false; }
function hide(el) { el.hidden = true; }

function showError(message) {
    els.errorMsg.textContent = message;
    hide(els.resultCard);
    show(els.errorCard);
}

function parseEmail(raw) {
    const clean = raw.replace(/\*\*/g, "").replace(/(^|\s)\*(\S)/g, "$1$2");
    const sections = { subject: "", body: "", cta: "" };
    const labelRe = /^\s*(subject|email|body|message|cta|call[\s-]?to[\s-]?action)\s*[:\-]\s*(.*)$/i;

    let current = null;
    for (const line of clean.split("\n")) {
        const m = line.match(labelRe);
        if (m) {
            const label = m[1].toLowerCase();
            current = label.startsWith("subject")
                ? "subject"
                : /cta|call/.test(label)
                ? "cta"
                : "body";
            if (m[2]) sections[current] += m[2] + "\n";
        } else if (current) {
            sections[current] += line + "\n";
        } else {
            sections.body += line + "\n";
        }
    }
    for (const k in sections) sections[k] = sections[k].trim();
    return sections;
}

function renderEmail(raw, options = {}) {
    const parsed = parseEmail(raw);
    els.subject.textContent = parsed.subject;
    els.body.textContent = parsed.body;
    els.cta.textContent = parsed.cta;
    currentHistoryId = options.historyId ?? null;
    const saveBtn = document.getElementById("save-edits-btn");
    if (saveBtn) saveBtn.hidden = currentHistoryId == null;
    hide(els.errorCard);
    show(els.resultCard);
}

async function generateEmail() {
    const product = els.product.value.trim();
    const audience = els.audience.value.trim();

    if (!product || !audience) {
        showError("Please enter both a product and a target audience.");
        return;
    }

    setLoading(true);
    hide(els.errorCard);
    hide(els.resultCard);

    try {
        const response = await apiFetch("/generate-email", {
            method: "POST",
            body: JSON.stringify({
                product,
                audience,
                tone: els.tone.value,
                length: els.length.value,
            }),
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            const detail = data.detail || data.error || response.statusText;
            showError(
                `Request failed (${response.status}): ` +
                (typeof detail === "string" ? detail : JSON.stringify(detail))
            );
            return;
        }

        if (data.error) { showError(data.error); return; }

        if (!data.result) { showError("Empty response from server."); return; }

        renderEmail(data.result, { historyId: data.history_id });
        loadHistory();
    } catch (err) {
        showError(`Network error: ${err.message}. Is the backend running?`);
    } finally {
        setLoading(false);
    }
}

async function copyText(text, btn) {
    try {
        await navigator.clipboard.writeText(text);
        const original = btn.textContent;
        btn.textContent = "Copied!";
        btn.classList.add("copied");
        setTimeout(() => {
            btn.textContent = original;
            btn.classList.remove("copied");
        }, 1500);
    } catch {
        btn.textContent = "Copy failed";
    }
}

document.addEventListener("click", (e) => {
    const btn = e.target.closest(".copy-btn");
    if (!btn) return;
    const targetId = btn.dataset.target;
    const text = document.getElementById(targetId)?.textContent ?? "";
    copyText(text, btn);
});

function currentSubject() { return els.subject.textContent.trim(); }
function currentBody() {
    const body = els.body.textContent.trim();
    const cta = els.cta.textContent.trim();
    return cta ? `${body}\n\n${cta}` : body;
}

function openInGmail() {
    const to = document.getElementById("send-to").value.trim();
    const params = new URLSearchParams({
        view: "cm",
        fs: "1",
        su: currentSubject(),
        body: currentBody(),
    });
    if (to) params.set("to", to);
    window.open(`https://mail.google.com/mail/?${params.toString()}`, "_blank", "noopener");
}

function openInDefault() {
    const to = document.getElementById("send-to").value.trim();
    const params = new URLSearchParams({
        subject: currentSubject(),
        body: currentBody(),
    });
    window.location.href = `mailto:${encodeURIComponent(to)}?${params.toString()}`;
}

async function saveEdits() {
    if (currentHistoryId == null) return;
    const saveBtn = document.getElementById("save-edits-btn");
    const original = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving…";

    const fullResult = [
        `Subject: ${currentSubject()}`,
        els.body.textContent.trim(),
        els.cta.textContent.trim() ? `CTA: ${els.cta.textContent.trim()}` : "",
    ].filter(Boolean).join("\n\n");

    try {
        const res = await apiFetch(`/history/${currentHistoryId}`, {
            method: "PATCH",
            body: JSON.stringify({ result: fullResult }),
        });
        if (res.ok) {
            saveBtn.textContent = "Saved!";
            setTimeout(() => { saveBtn.textContent = original; saveBtn.disabled = false; }, 1200);
            loadHistory();
        } else {
            const data = await res.json().catch(() => ({}));
            saveBtn.textContent = original;
            saveBtn.disabled = false;
            showError(data.detail || `Save failed (${res.status})`);
        }
    } catch (err) {
        saveBtn.textContent = original;
        saveBtn.disabled = false;
        showError(`Network error: ${err.message}`);
    }
}

function copyAll() {
    const parts = [
        els.subject.textContent && `Subject: ${els.subject.textContent}`,
        els.body.textContent,
        els.cta.textContent && `CTA: ${els.cta.textContent}`,
    ].filter(Boolean);
    copyText(parts.join("\n\n"), els.copyAll);
}

[els.product, els.audience].forEach((el) =>
    el.addEventListener("keydown", (e) => {
        if (e.key === "Enter") generateEmail();
    })
);

// --- Email improver ---

const improver = {
    btn: document.getElementById("improve-btn"),
    draft: document.getElementById("draft"),
    tone: document.getElementById("improve-tone"),
};

function setImproverLoading(isLoading) {
    improver.btn.disabled = isLoading;
    improver.btn.classList.toggle("loading", isLoading);
    improver.btn.querySelector(".btn-label").textContent = isLoading
        ? "Improving"
        : "Improve email";
}

async function improveEmail() {
    const draft = improver.draft.value.trim();
    if (draft.length < 10) {
        showError("Please paste a draft of at least 10 characters.");
        return;
    }

    setImproverLoading(true);
    hide(els.errorCard);
    hide(els.resultCard);

    try {
        const res = await apiFetch("/improve-email", {
            method: "POST",
            body: JSON.stringify({
                draft,
                tone: improver.tone.value || null,
            }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const detail = data.detail || res.statusText;
            showError(typeof detail === "string" ? detail : JSON.stringify(detail));
            return;
        }
        if (data.error) { showError(data.error); return; }
        if (!data.result) { showError("Empty response from server."); return; }

        renderEmail(data.result);
        window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
        showError(`Network error: ${err.message}.`);
    } finally {
        setImproverLoading(false);
    }
}

// --- Subject lines ---

const subjectsEls = {
    btn: document.getElementById("subjects-btn"),
    card: document.getElementById("subjects-card"),
    list: document.getElementById("subjects-list"),
};

function hideSubjects() {
    subjectsEls.card.hidden = true;
}

function setSubjectsLoading(isLoading) {
    subjectsEls.btn.disabled = isLoading;
    subjectsEls.btn.classList.toggle("loading", isLoading);
    subjectsEls.btn.querySelector(".btn-label").textContent = isLoading
        ? "Brainstorming"
        : "Brainstorm subject lines";
}

function renderSubjects(subjects) {
    subjectsEls.list.innerHTML = "";
    for (const subject of subjects) {
        const li = document.createElement("li");
        li.className = "subject-item";
        li.innerHTML = `
            <span class="subject-text"></span>
            <button class="copy-btn">Copy</button>
        `;
        li.querySelector(".subject-text").textContent = subject;
        li.querySelector(".copy-btn").addEventListener("click", (e) => {
            copyText(subject, e.currentTarget);
        });
        subjectsEls.list.appendChild(li);
    }
    subjectsEls.card.hidden = false;
}

async function generateSubjects() {
    const product = els.product.value.trim();
    const audience = els.audience.value.trim();
    if (!product || !audience) {
        showError("Please enter both a product and a target audience.");
        return;
    }

    setSubjectsLoading(true);
    hide(els.errorCard);
    try {
        const res = await apiFetch("/subject-lines", {
            method: "POST",
            body: JSON.stringify({
                product, audience, tone: els.tone.value,
            }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const detail = data.detail || res.statusText;
            showError(typeof detail === "string" ? detail : JSON.stringify(detail));
            return;
        }
        if (!data.subjects || !data.subjects.length) {
            showError("No subject lines were generated. Try again.");
            return;
        }
        renderSubjects(data.subjects);
        subjectsEls.card.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (err) {
        showError(`Network error: ${err.message}.`);
    } finally {
        setSubjectsLoading(false);
    }
}

// --- Follow-up ---

const followup = {
    card: document.getElementById("followup-card"),
    context: document.getElementById("followup-context"),
    days: document.getElementById("followup-days"),
    note: document.getElementById("followup-note"),
    btn: document.getElementById("followup-btn"),
    sourceId: null,
};

function showFollowUp(item) {
    followup.sourceId = item.id;
    followup.context.textContent =
        `Following up on "${item.product}" sent to ${item.audience}`;
    followup.note.value = "";
    followup.days.value = 5;
    followup.card.hidden = false;
    followup.card.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideFollowUp() {
    followup.card.hidden = true;
    followup.sourceId = null;
}

async function submitFollowUp() {
    if (!followup.sourceId) return;
    const days = parseInt(followup.days.value, 10);
    if (isNaN(days) || days < 0) {
        showError("Days since sent must be 0 or more.");
        return;
    }

    followup.btn.disabled = true;
    followup.btn.classList.add("loading");
    followup.btn.querySelector(".btn-label").textContent = "Generating";
    hide(els.errorCard);
    hide(els.resultCard);

    try {
        const res = await apiFetch("/follow-up", {
            method: "POST",
            body: JSON.stringify({
                history_id: followup.sourceId,
                days_since_sent: days,
                note: followup.note.value.trim() || null,
            }),
        });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            const detail = data.detail || res.statusText;
            showError(typeof detail === "string" ? detail : JSON.stringify(detail));
            return;
        }
        if (data.error) { showError(data.error); return; }
        if (!data.result) { showError("Empty response from server."); return; }

        hideFollowUp();
        renderEmail(data.result, { historyId: data.history_id });
        loadHistory();
    } catch (err) {
        showError(`Network error: ${err.message}.`);
    } finally {
        followup.btn.disabled = false;
        followup.btn.classList.remove("loading");
        followup.btn.querySelector(".btn-label").textContent = "Generate follow-up";
    }
}

// --- History ---

const historyList = document.getElementById("history-list");

function formatDate(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    });
}

function renderHistory(items) {
    if (!items.length) {
        historyList.innerHTML = '<p class="history-empty">No emails yet. Generate one above!</p>';
        return;
    }
    historyList.innerHTML = "";
    for (const item of items) {
        const isFollowUp = item.parent_id != null;
        const row = document.createElement("div");
        row.className = "history-item" + (isFollowUp ? " is-followup" : "");
        row.innerHTML = `
            <div class="history-meta">
                <div class="history-title">
                    <span class="title-text"></span>
                    <span class="badge" hidden>Follow-up</span>
                </div>
                <div class="history-sub"></div>
            </div>
            <div class="history-actions">
                <button class="copy-btn view-btn">View</button>
                <button class="copy-btn followup-trigger">Follow up</button>
                <button class="copy-btn delete-btn" title="Delete">✕</button>
            </div>
        `;
        row.querySelector(".title-text").textContent = item.product;
        if (isFollowUp) row.querySelector(".badge").hidden = false;
        row.querySelector(".history-sub").textContent =
            `${item.audience} • ${item.tone} • ${item.length} • ${formatDate(item.created_at)}`;

        row.querySelector(".view-btn").addEventListener("click", () => {
            els.product.value = item.product;
            els.audience.value = item.audience;
            els.tone.value = item.tone;
            els.length.value = item.length;
            renderEmail(item.result, { historyId: item.id });
            hideFollowUp();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
        row.querySelector(".followup-trigger").addEventListener("click", () => {
            showFollowUp(item);
        });
        row.querySelector(".delete-btn").addEventListener("click", async () => {
            if (!confirm("Delete this email from your history?")) return;
            try {
                const res = await apiFetch(`/history/${item.id}`, { method: "DELETE" });
                if (res.ok) loadHistory();
            } catch (err) { /* redirected on 401 */ }
        });
        historyList.appendChild(row);
    }
}

async function loadHistory() {
    historyList.innerHTML = '<p class="history-empty">Loading…</p>';
    try {
        const res = await apiFetch("/history");
        if (!res.ok) {
            historyList.innerHTML = '<p class="history-empty">Could not load history.</p>';
            return;
        }
        const items = await res.json();
        renderHistory(items);
    } catch (err) { /* redirected on 401 */ }
}

loadHistory();
