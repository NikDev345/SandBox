/* ============================================================
   AI SandBox — DASHBOARD + ADMIN TOOL MANAGEMENT
   ============================================================ */

const dashboard = document.querySelector("[data-dashboard]");
let toolCards = Array.from(document.querySelectorAll(".tool-card"));
const searchInput = document.getElementById("global-search");
const emptyState = document.querySelector("[data-empty-state]");
const resultCount = document.querySelector("[data-result-count]");

const apiCandidates = {
    metrics: ["/analytics/summary", "/api/analytics/summary", "/admin/metrics"],
    tools:   ["/tools", "/api/tools"],
    files:   ["/api/tools/files"],
    me:      ["/auth/me"]
};

/* ── Context menu state ── */
let activeContextMenu = { id: null, name: null, slug: null };

/* ============================================================
   BOOT
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    consumeOAuthCallback();
    initializeMetricCards();
    initializeSearch();
    initializeNavigation();
    initializeProfile();
    initializeCommandPalette();
    initializeMobileDrawer();
    initializeLogoDropZone();
    initializeAdminControls();
    loadDashboardData();
    applyAdminRole();
    updateCategoryBadges();
});

/* ============================================================
   ADMIN CONTROLS — event delegation, no inline handlers
   ============================================================ */

function initializeAdminControls() {
    /* Add Tool button */
    document.getElementById("add-tool-btn")
        ?.addEventListener("click", () => openToolModal());

    /* Empty state "Create First Tool" */
    document.getElementById("empty-create-btn")
        ?.addEventListener("click", () => openToolModal());

    /* Modal submit */
    document.getElementById("modal-submit-btn")
        ?.addEventListener("click", submitToolForm);

    /* Tool modal — close buttons + cancel + backdrop */
    const toolModal = document.getElementById("tool-modal");
    if (toolModal) {
        toolModal.querySelectorAll(".modal-close").forEach(btn =>
            btn.addEventListener("click", closeToolModal)
        );
        /* Cancel button (btn-ghost inside tool-modal footer) */
        toolModal.querySelector(".modal-footer .btn-ghost")
            ?.addEventListener("click", closeToolModal);
        toolModal.addEventListener("click", e => {
            if (e.target === toolModal) closeToolModal();
        });
    }

    /* Delete modal — close buttons + cancel + backdrop + confirm */
    const deleteModal = document.getElementById("delete-modal");
    if (deleteModal) {
        deleteModal.querySelectorAll(".modal-close").forEach(btn =>
            btn.addEventListener("click", closeDeleteModal)
        );
        deleteModal.querySelector(".modal-footer .btn-ghost")
            ?.addEventListener("click", closeDeleteModal);
        deleteModal.querySelector(".btn-danger")
            ?.addEventListener("click", confirmDeleteTool);
        deleteModal.addEventListener("click", e => {
            if (e.target === deleteModal) closeDeleteModal();
        });
    }

    /* Context menu — delegate via data-action */
    document.getElementById("tool-context-menu")
        ?.addEventListener("click", e => {
            const btn = e.target.closest("[data-action]");
            if (btn) contextMenuAction(btn.dataset.action);
        });

    /* 3-dot menu buttons — delegate from tool grid */
    document.querySelector("[data-tool-grid]")
        ?.addEventListener("click", e => {
            const menuBtn = e.target.closest(".tool-menu-btn");
            if (!menuBtn) return;
            e.preventDefault();
            e.stopPropagation();
            const card = menuBtn.closest(".tool-card");
            openToolMenu(
                e,
                card?.dataset.toolId   || "",
                card?.dataset.toolName || "",
                (card?.getAttribute("href") || "").replace("/tools/", "")
            );
        });
}

/* ============================================================
   ROLE / ADMIN
   ============================================================ */

function applyAdminRole() {
    const user = safeJson(localStorage.getItem("SandBox_user"));
    const role = user?.role || localStorage.getItem("role") || "";

    if (role === "admin") {
        document.body.classList.add("is-admin");
        const addBtn = document.getElementById("add-tool-btn");
        if (addBtn) addBtn.style.display = "";  // controlled by .admin-only
    } else {
        document.body.classList.remove("is-admin");
    }
}

function isAdmin() {
    return document.body.classList.contains("is-admin");
}

/* ============================================================
   METRICS
   ============================================================ */

function initializeMetricCards() {
    document.querySelectorAll(".metric-card").forEach(card => card.classList.add("loading"));
}

function setMetric(key, value, note) {
    document.querySelectorAll(`[data-metric="${key}"]`).forEach(el => {
        el.textContent = value;
        el.closest(".metric-card")?.classList.remove("loading");
    });
    document.querySelectorAll(`[data-metric-note="${key}"]`).forEach(el => el.textContent = note);
}

/* ============================================================
   AUTH / SESSION
   ============================================================ */

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function persistAuthSession(token, user) {
    localStorage.setItem("access_token", token);
    localStorage.setItem("user_id", user.id);
    localStorage.setItem("SandBox_user", JSON.stringify(user));
}

function clearAuthSession() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("SandBox_user");
    localStorage.removeItem("role");
}

function consumeOAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("auth_token");
    const user = safeJson(params.get("auth_user"));
    if (!token || !user) return;
    persistAuthSession(token, user);
    window.history.replaceState({}, document.title, window.location.pathname);
}

/* ============================================================
   DATA LOADING
   ============================================================ */

async function fetchFirstAvailable(urls) {
    for (const url of urls) {
        try {
            const response = await fetch(url, { headers: authHeaders() });
            if (response.ok) return await response.json();
        } catch (_) { continue; }
    }
    return null;
}

async function loadDashboardData() {
    const me = await fetchFirstAvailable(apiCandidates.me);

    if (me) {
        renderProfile(me);
        localStorage.setItem("SandBox_user", JSON.stringify(me));
        applyAdminRole();
    } else if (localStorage.getItem("access_token")) {
        clearAuthSession();
        renderSignedOut();
    }

    /* Load tool metrics */
    const metrics = await fetchFirstAvailable(apiCandidates.metrics);
    if (metrics) {
        setMetric("totalTools", formatMetric(metrics.total_tools ?? metrics.totalTools), "in workspace");
        setMetric("executions", formatMetric(metrics.executions ?? metrics.total_executions), "all time");
        setMetric("users", formatMetric(metrics.active_users ?? metrics.users), "active");
        setMetric("uptime", metrics.uptime ?? "99.9%", "");
    } else {
        ["totalTools","executions","users","uptime"].forEach(k => setMetric(k, "--", "Unavailable"));
    }

    /* Load tools from API (if available — otherwise static cards remain) */
    const toolsData = await fetchFirstAvailable(apiCandidates.tools);
    if (toolsData) {
        const tools = normalizeTools(toolsData);
        if (tools.length) renderTools(tools);
    }
}

/* ============================================================
   TOOL RENDERING
   ============================================================ */

function normalizeTools(payload) {
    const list = Array.isArray(payload) ? payload : payload?.tools;
    if (!Array.isArray(list)) return [];
    return list
        .map(tool => ({
            id: tool.id || tool.slug || slugify(tool.name || ""),
            name: tool.name || tool.title,
            description: tool.description || "Open this workflow in SandBox.",
            category: tool.category || "Developer Tools",
            slug: tool.slug || slugify(tool.name || tool.title || ""),
            is_active: tool.is_active !== false,
            icon_url: tool.icon_url || null
        }))
        .filter(t => t.name && t.slug);
}

function renderTools(tools) {
    const grid = document.querySelector("[data-tool-grid]");
    if (!grid) return;

    grid.innerHTML = tools.map(tool => `
        <a class="tool-card"
           href="/tools/${escapeHtml(tool.slug)}"
           data-tool-name="${escapeHtml(tool.name)}"
           data-tool-category="${escapeHtml(tool.category)}"
           data-tool-id="${escapeHtml(tool.id)}"
           ${!tool.is_active ? 'data-disabled="true"' : ""}
        >
            <div class="tool-card-header">
                ${tool.icon_url
                    ? `<img class="tool-logo" src="${escapeHtml(tool.icon_url)}" alt="${escapeHtml(tool.name)} logo" style="width:36px;height:36px;object-fit:contain;">`
                    : `<svg class="tool-logo" viewBox="0 0 48 48"><rect x="8" y="8" width="32" height="32" rx="6" stroke-width="2"/><line x1="16" y1="24" x2="32" y2="24"/><line x1="24" y1="16" x2="24" y2="32"/></svg>`
                }
                <button class="tool-menu-btn admin-only" type="button" aria-label="Tool options">
                    <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
                </button>
            </div>
            <h3>${escapeHtml(tool.name)}</h3>
            <p>${escapeHtml(tool.description)}</p>
            <div class="tool-meta">
                <span class="tool-category-badge" data-cat="${escapeHtml(tool.category)}">${escapeHtml(tool.category)}</span>
                <svg class="tool-arrow" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
        </a>
    `).join("");

    toolCards = Array.from(document.querySelectorAll(".tool-card"));
    filterTools(searchInput?.value || "");

    /* Show empty-create button for admin when no tools */
    const emptyCreateBtn = document.getElementById("empty-create-btn");
    if (emptyCreateBtn && isAdmin()) emptyCreateBtn.style.display = "";
}

function updateCategoryBadges() {
    document.querySelectorAll(".tool-category-badge").forEach(badge => {
        const cat = badge.textContent.trim();
        badge.setAttribute("data-cat", cat);
    });
}

/* ============================================================
   SEARCH
   ============================================================ */

function initializeSearch() {
    updateResultCount(toolCards.length);
    searchInput?.addEventListener("input", e => filterTools(e.target.value));
}

function filterTools(query) {
    const needle = query.trim().toLowerCase();
    let visible = 0;

    toolCards.forEach(card => {
        /* Non-admin users never see disabled tools */
        if (!isAdmin() && card.dataset.disabled === "true") {
            card.hidden = true;
            return;
        }
        const haystack = `${card.dataset.toolName || ""} ${card.dataset.toolCategory || ""} ${card.textContent}`.toLowerCase();
        const match = !needle || haystack.includes(needle);
        card.hidden = !match;
        if (match) visible += 1;
    });

    updateResultCount(visible);

    if (emptyState) {
        emptyState.hidden = visible !== 0;
        const msg = document.getElementById("empty-state-msg");
        const btn = document.getElementById("empty-create-btn");
        if (msg) msg.textContent = needle ? "Try a different search term." : "No tools available yet.";
        if (btn) btn.style.display = isAdmin() && !needle ? "" : "none";
    }
}

function updateResultCount(count) {
    if (resultCount) resultCount.textContent = `${count} ${count === 1 ? "tool" : "tools"}`;
}

/* ============================================================
   CONTEXT MENU (3-dot)
   ============================================================ */

function openToolMenu(event, toolId, toolName, toolSlug) {
    event.preventDefault();
    event.stopPropagation();

    activeContextMenu = { id: toolId, name: toolName, slug: toolSlug };

    const menu = document.getElementById("tool-context-menu");
    if (!menu) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const menuW = 180;
    const menuH = 160;

    let top = rect.bottom + 4;
    let left = rect.right - menuW;

    if (top + menuH > window.innerHeight) top = rect.top - menuH - 4;
    if (left < 8) left = 8;

    menu.style.top  = `${top}px`;
    menu.style.left = `${left}px`;
    menu.classList.add("open");
    menu.removeAttribute("aria-hidden");

    /* Close on outside click */
    setTimeout(() => {
        document.addEventListener("click", closeContextMenuOnOutside, { once: true });
    }, 0);
}

function closeContextMenuOnOutside(e) {
    const menu = document.getElementById("tool-context-menu");
    if (menu && !menu.contains(e.target)) closeContextMenu();
}

function closeContextMenu() {
    const menu = document.getElementById("tool-context-menu");
    if (!menu) return;
    menu.classList.remove("open");
    menu.setAttribute("aria-hidden", "true");
}

function contextMenuAction(action) {
    closeContextMenu();
    const { id, name, slug } = activeContextMenu;

    if (action === "open")    window.location.href = `/tools/${slug}`;
    if (action === "edit")    openEditToolModal(id);
    if (action === "disable") disableTool(id, name);
    if (action === "delete")  openDeleteModal(id, name);
}

/* ============================================================
   ADD / EDIT TOOL MODAL
   ============================================================ */

let editingToolId = null;

function openToolModal(editData = null) {
    editingToolId = editData?.id || null;

    const modal    = document.getElementById("tool-modal");
    const title    = document.getElementById("modal-title");
    const submitBtn = document.getElementById("modal-submit-btn");

    /* Reset form */
    document.getElementById("tool-name-input").value = editData?.name || "";
    document.getElementById("tool-category-select").value = editData?.category || "";
    document.getElementById("tool-description-input").value = editData?.description || "";
    document.getElementById("logo-filename").textContent = "Click to upload or drag PNG here";
    const preview = document.getElementById("logo-preview");
    if (preview) {
        preview.hidden = true;
        preview.src = "";
        if (editData?.icon_url) {
            preview.src = editData.icon_url;
            preview.hidden = false;
        }
    }

    title.textContent = editData ? "Edit Tool" : "Add Tool";
    submitBtn.innerHTML = editData
        ? `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Save Changes`
        : `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Create Tool`;

    modal.classList.add("open");
    modal.removeAttribute("aria-hidden");

    loadToolFiles(editData?.source_path);

    setTimeout(() => document.getElementById("tool-name-input")?.focus(), 100);
}

function closeToolModal() {
    const modal = document.getElementById("tool-modal");
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    editingToolId = null;
}

function handleModalBackdropClick(e) {
    if (e.target === document.getElementById("tool-modal")) closeToolModal();
}

async function openEditToolModal(toolId) {
    /* Fetch tool data from API */
    try {
        const res = await fetch(`/api/tools/${toolId}`, { headers: authHeaders() });
        if (res.ok) {
            const tool = await res.json();
            openToolModal(tool);
            return;
        }
    } catch (_) {}

    /* Fallback: read from DOM */
    const card = document.querySelector(`.tool-card[data-tool-id="${toolId}"]`);
    if (card) {
        openToolModal({
            id: toolId,
            name: card.dataset.toolName || "",
            category: card.dataset.toolCategory || "",
            description: card.querySelector("p")?.textContent || ""
        });
    }
}

async function loadToolFiles(selected = "") {
    const select = document.getElementById("tool-file-select");
    if (!select) return;

    select.innerHTML = `<option value="">Loading…</option>`;

    try {
        const res = await fetch("/api/tools/files", { headers: authHeaders() });
        if (res.ok) {
            const { files = [] } = await res.json();
            select.innerHTML = `<option value="">Select Python file…</option>` +
                files.map(f => `<option value="${escapeHtml(f)}"${f === selected ? " selected" : ""}>${escapeHtml(f)}</option>`).join("");
            return;
        }
    } catch (_) {}

    /* Fallback placeholder list */
    select.innerHTML = `
        <option value="">Select Python file…</option>
        <option value="pdf_viewer.py"${selected === "pdf_viewer.py" ? " selected" : ""}>pdf_viewer.py</option>
        <option value="sql_generator.py"${selected === "sql_generator.py" ? " selected" : ""}>sql_generator.py</option>
        <option value="image_resizer.py"${selected === "image_resizer.py" ? " selected" : ""}>image_resizer.py</option>
    `;
}

async function submitToolForm() {
    const name        = document.getElementById("tool-name-input").value.trim();
    const category    = document.getElementById("tool-category-select").value;
    const description = document.getElementById("tool-description-input").value.trim();
    const sourceFile  = document.getElementById("tool-file-select").value;
    const logoInput   = document.getElementById("tool-logo-input");
    const logoFile    = logoInput?.files?.[0] || null;

    if (!name)       return showToast("Tool name is required.", "error");
    if (!category)   return showToast("Please select a category.", "error");
    if (!sourceFile) return showToast("Please select a Python file.", "error");

    const btn = document.getElementById("modal-submit-btn");
    btn.disabled = true;
    btn.textContent = editingToolId ? "Saving…" : "Creating…";

    try {
        const formData = new FormData();
        formData.append("name", name);
        formData.append("category", category);
        formData.append("description", description);
        formData.append("source_path", sourceFile);
        if (logoFile) formData.append("logo", logoFile);

        const url    = editingToolId ? `/api/tools/${editingToolId}` : "/api/tools";
        const method = editingToolId ? "PUT" : "POST";

        const res = await fetch(url, {
            method,
            headers: authHeaders(),
            body: formData
        });

        if (res.ok) {
            const created = await res.json();
            closeToolModal();
            showToast(editingToolId ? "Tool updated successfully." : "Tool created successfully.", "success");
            refreshToolCard(created, editingToolId);
        } else {
            const err = await res.json().catch(() => ({}));
            showToast(err.detail || "Failed to save tool.", "error");
        }
    } catch (e) {
        showToast("Network error. Please try again.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = editingToolId
            ? `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Save Changes`
            : `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Create Tool`;
    }
}

function refreshToolCard(tool, oldId = null) {
    /* Re-render a single card or append new one */
    const grid = document.querySelector("[data-tool-grid]");
    if (!grid) return;

    const normalized = normalizeTools([tool])[0];
    if (!normalized) return;

    const existing = oldId
        ? document.querySelector(`.tool-card[data-tool-id="${oldId}"]`)
        : null;

    const cardHtml = buildToolCardHtml(normalized);

    if (existing) {
        existing.outerHTML = cardHtml;
    } else {
        grid.insertAdjacentHTML("beforeend", cardHtml);
    }

    toolCards = Array.from(document.querySelectorAll(".tool-card"));
    updateCategoryBadges();
    filterTools(searchInput?.value || "");
}

function buildToolCardHtml(tool) {
    const logoHtml = tool.icon_url
        ? `<img class="tool-logo" src="${escapeHtml(tool.icon_url)}" alt="${escapeHtml(tool.name)} logo" style="width:36px;height:36px;object-fit:contain;">`
        : `<svg class="tool-logo" viewBox="0 0 48 48"><rect x="8" y="8" width="32" height="32" rx="6" stroke-width="2"/><line x1="16" y1="24" x2="32" y2="24"/><line x1="24" y1="16" x2="24" y2="32"/></svg>`;

    return `
        <a class="tool-card"
           href="/tools/${escapeHtml(tool.slug)}"
           data-tool-name="${escapeHtml(tool.name)}"
           data-tool-category="${escapeHtml(tool.category)}"
           data-tool-id="${escapeHtml(tool.id)}"
           ${!tool.is_active ? 'data-disabled="true"' : ""}
        >
            <div class="tool-card-header">
                ${logoHtml}
                <button class="tool-menu-btn admin-only" type="button" aria-label="Tool options"
>
                    <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
                </button>
            </div>
            <h3>${escapeHtml(tool.name)}</h3>
            <p>${escapeHtml(tool.description)}</p>
            <div class="tool-meta">
                <span class="tool-category-badge" data-cat="${escapeHtml(tool.category)}">${escapeHtml(tool.category)}</span>
                <svg class="tool-arrow" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
        </a>`;
}

/* ============================================================
   DELETE MODAL
   ============================================================ */

let deletingToolId = null;

function openDeleteModal(toolId, toolName) {
    deletingToolId = toolId;
    const modal = document.getElementById("delete-modal");
    const nameDisplay = document.getElementById("delete-tool-name-display");
    if (nameDisplay) nameDisplay.textContent = toolName;
    modal.classList.add("open");
    modal.removeAttribute("aria-hidden");
}

function closeDeleteModal() {
    const modal = document.getElementById("delete-modal");
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    deletingToolId = null;
}

function handleDeleteBackdropClick(e) {
    if (e.target === document.getElementById("delete-modal")) closeDeleteModal();
}

async function confirmDeleteTool() {
    if (!deletingToolId) return;

    try {
        const res = await fetch(`/api/tools/${deletingToolId}`, {
            method: "DELETE",
            headers: authHeaders()
        });

        if (res.ok || res.status === 204) {
            document.querySelector(`.tool-card[data-tool-id="${deletingToolId}"]`)?.remove();
            toolCards = Array.from(document.querySelectorAll(".tool-card"));
            filterTools(searchInput?.value || "");
            closeDeleteModal();
            showToast("Tool deleted.", "success");
        } else {
            const err = await res.json().catch(() => ({}));
            showToast(err.detail || "Failed to delete tool.", "error");
            closeDeleteModal();
        }
    } catch (_) {
        showToast("Network error.", "error");
        closeDeleteModal();
    }
}

/* ============================================================
   DISABLE TOOL
   ============================================================ */

async function disableTool(toolId, toolName) {
    try {
        const res = await fetch(`/api/tools/${toolId}/disable`, {
            method: "PATCH",
            headers: authHeaders()
        });

        if (res.ok) {
            const card = document.querySelector(`.tool-card[data-tool-id="${toolId}"]`);
            if (card) card.dataset.disabled = "true";
            showToast(`"${toolName}" has been disabled.`, "info");
        } else {
            const err = await res.json().catch(() => ({}));
            showToast(err.detail || "Failed to disable tool.", "error");
        }
    } catch (_) {
        showToast("Network error.", "error");
    }
}

/* ============================================================
   LOGO FILE UPLOAD
   ============================================================ */

function initializeLogoDropZone() {
    const zone  = document.getElementById("logo-drop-zone");
    const input = document.getElementById("tool-logo-input");
    const label = document.getElementById("logo-filename");
    const preview = document.getElementById("logo-preview");

    if (!zone || !input) return;

    input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (!file) return;
        label.textContent = file.name;
        if (preview) {
            preview.src = URL.createObjectURL(file);
            preview.hidden = false;
        }
    });

    zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
    zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
    zone.addEventListener("drop", e => {
        e.preventDefault();
        zone.classList.remove("drag-over");
        const file = e.dataTransfer?.files?.[0];
        if (!file) return;

        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        label.textContent = file.name;
        if (preview) {
            preview.src = URL.createObjectURL(file);
            preview.hidden = false;
        }
    });
}

/* ============================================================
   TOAST
   ============================================================ */

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const icons = {
        success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
        error:   `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
        info:    `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>`
    };

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `${icons[type] || icons.info}<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-exit");
        toast.addEventListener("animationend", () => toast.remove(), { once: true });
    }, 3500);
}

/* ============================================================
   NAVIGATION / PROFILE / COMMAND PALETTE
   ============================================================ */

function initializeNavigation() {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            document.querySelectorAll(".nav-item").forEach(l => l.classList.remove("active"));
            item.classList.add("active");
            dashboard?.classList.remove("nav-open");
            document.querySelector(".mobile-menu")?.setAttribute("aria-expanded", "false");
        });
    });
}

function initializeProfile() {
    const profileButton = document.querySelector(".profile-trigger");
    const profileMenu = document.querySelector(".profile-menu");

    profileButton?.addEventListener("click", () => {
        const isOpen = profileMenu?.classList.toggle("open");
        profileButton.setAttribute("aria-expanded", String(Boolean(isOpen)));
    });

    document.addEventListener("click", event => {
        if (!profileMenu?.contains(event.target)) {
            profileMenu?.classList.remove("open");
            profileButton?.setAttribute("aria-expanded", "false");
        }
    });

    const storedUser = safeJson(localStorage.getItem("SandBox_user"));
    if (storedUser && localStorage.getItem("access_token")) {
        renderProfile(storedUser);
    } else {
        renderSignedOut();
    }

    document.querySelector("[data-logout]")?.addEventListener("click", logout);
}

function renderProfile(user) {
    const name     = user.name || user.email?.split("@")[0] || "Workspace";
    const email    = user.email || "Not signed in";
    const provider = user.provider || user.auth_provider || "Local";
    const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map(p => p[0]).join("").toUpperCase() || "TB";

    document.querySelectorAll("[data-user-avatar]").forEach(img => {
        if (user.avatar) {
            img.src = user.avatar;
        } else {
            img.src = "/static/default-avatar.png";
        }
    });
    document.querySelectorAll("[data-user-name]").forEach(t => t.textContent = name);
    document.querySelectorAll("[data-user-provider]").forEach(t => t.textContent = provider);
    document.querySelectorAll("[data-user-email]").forEach(t => t.textContent = email);
    const wt = document.querySelector("[data-workspace-title]");
    const ws = document.querySelector("[data-workspace-subtitle]");
    if (wt) wt.textContent = `${name}'s workspace`;
    if (ws) ws.textContent = `${email} authenticated with ${provider}.`;
    document.querySelectorAll("[data-auth-link]").forEach(l => l.hidden = true);
    const logoutBtn = document.querySelector("[data-logout]");
    if (logoutBtn) logoutBtn.hidden = false;
}

function renderSignedOut() {
    document.querySelectorAll("[data-user-avatar]").forEach(t => t.textContent = "TB");
    document.querySelectorAll("[data-user-name]").forEach(t => t.textContent = "Workspace");
    document.querySelectorAll("[data-user-provider]").forEach(t => t.textContent = "Signed out");
    document.querySelectorAll("[data-user-email]").forEach(t => t.textContent = "Not signed in");
    const wt = document.querySelector("[data-workspace-title]");
    const ws = document.querySelector("[data-workspace-subtitle]");
    if (wt) wt.textContent = "Your active workspace";
    if (ws) ws.textContent = "Sign in to sync your tools, history, and saved workflows.";
    document.querySelectorAll("[data-auth-link]").forEach(l => l.hidden = false);
    const logoutBtn = document.querySelector("[data-logout]");
    if (logoutBtn) logoutBtn.hidden = true;
}

async function logout() {
    const token = localStorage.getItem("access_token");
    try {
        if (token) {
            await fetch("/auth/logout", { method: "POST", headers: authHeaders() });
        }
    } finally {
        clearAuthSession();
        renderSignedOut();
        window.location.href = "/login";
    }
}

function initializeCommandPalette() {
    document.querySelectorAll("[data-open-command]").forEach(button => {
        button.addEventListener("click", openCommandPalette);
    });
    document.addEventListener("keydown", event => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            openCommandPalette();
        }
        if (event.key === "Escape") {
            closeCommandPalette();
            closeContextMenu();
            closeToolModal();
            closeDeleteModal();
            dashboard?.classList.remove("nav-open");
        }
    });
}

function openCommandPalette() {
    closeCommandPalette();
    const currentCards = Array.from(document.querySelectorAll(".tool-card"));
    const modal = document.createElement("div");
    modal.className = "command-modal";
    modal.innerHTML = `
        <div class="command-box" role="dialog" aria-modal="true" aria-label="Command search">
            <input type="search" placeholder="Search tools…" autocomplete="off">
            <div class="command-list">
                ${currentCards.map(card => `
                    <a class="command-item" href="${card.getAttribute("href")}">
                        <span>${escapeHtml(card.dataset.toolName || card.querySelector("h3")?.textContent || "Tool")}</span>
                        <small>${escapeHtml(card.dataset.toolCategory || "Tool")}</small>
                    </a>
                `).join("")}
            </div>
        </div>`;

    document.body.appendChild(modal);
    const input = modal.querySelector("input");
    const items = Array.from(modal.querySelectorAll(".command-item"));
    input?.focus();
    input?.addEventListener("input", e => {
        const q = e.target.value.toLowerCase();
        items.forEach(item => { item.hidden = !item.textContent.toLowerCase().includes(q); });
    });
    modal.addEventListener("click", e => { if (e.target === modal) closeCommandPalette(); });
}

function closeCommandPalette() {
    document.querySelector(".command-modal")?.remove();
}

function initializeMobileDrawer() {
    const button = document.querySelector(".mobile-menu");
    button?.addEventListener("click", () => {
        const isOpen = dashboard?.classList.toggle("nav-open");
        button.setAttribute("aria-expanded", String(Boolean(isOpen)));
    });
}

/* ============================================================
   UTILITIES
   ============================================================ */

function formatMetric(value) {
    if (value == null) return "--";
    if (typeof value === "number") return value.toLocaleString();
    return value;
}

function safeJson(value) {
    try { return value ? JSON.parse(value) : null; } catch (_) { return null; }
}

function slugify(value) {
    return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}