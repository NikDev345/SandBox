/* ============================================================
   AI SandBox — DASHBOARD + ADMIN TOOL MANAGEMENT
   ============================================================ */
// GLOBAL INTERVAL TRACKER
window.__intervals = window.__intervals || [];

function registerInterval(id) {
  window.__intervals.push(id);
}

function clearAllIntervals() {
  window.__intervals.forEach(clearInterval);
  window.__intervals = [];
}
let appearanceChanged = false;

let selectedTheme =
    localStorage.getItem("sandbox-theme") || "system";

let selectedAccent =
    localStorage.getItem("sandbox-accent") || "blue";

const apiCandidates = {
    metrics: ["/analytics/summary", "/api/analytics/summary", "/admin/metrics"],
    tools:   [],
    files:   ["/api/tools/files"],
    me:      ["/auth/me"]
};


/* ── Context menu state ── */
let activeContextMenu = { id: null, name: null, slug: null };
let toolCards = [];
let searchInput = null;
let emptyState = null;
let resultCount = null;

/* ============================================================
   BOOT
   ============================================================ */

document.addEventListener("DOMContentLoaded", async () => {
    clearAllIntervals();
    /* Cache DOM references after content is ready */
    toolCards  = Array.from(document.querySelectorAll(".tool-card"));
    searchInput = document.getElementById("global-search");
    emptyState  = document.querySelector("[data-empty-state]");
    resultCount = document.querySelector("[data-result-count]");

    initializeSearch();
    initializeNavigation();
    initializeSectionNavigation();
    initializeSettingsNavigation();
    initializeProfile();
    initializeCommandPalette();
    initializeMobileDrawer();
    initializeLogoDropZone();
    initializeAdminControls();
    initToolCategoryFilter();
    await loadDashboardData();
    applyAdminRole();
    updateCategoryBadges();
    await Promise.allSettled([
        loadConnections(),
        loadWorkspace(),
        loadAppearance()
    ]);
    initializeScrollSpy();
    initializeSandboxFooter();

    // =======================================================
    // Theme
    // =======================================================

    document.querySelectorAll(".theme-option").forEach(option => {

        option.addEventListener("click", () => {

            const radio = option.querySelector(".theme-radio");

            radio.checked = true;

            selectedTheme = radio.value;

            window.setTheme(selectedTheme);

            appearanceChanged = true;

            document
            .getElementById("appearance-save-btn")
            .disabled = false;

        });

    });

    // =======================================================
    // Accent
    // =======================================================

    document.querySelectorAll(".accent-option").forEach(option => {

        option.addEventListener("click", () => {

            const radio = option.querySelector(".accent-radio");

            radio.checked = true;

            selectedAccent = radio.value;

            window.setAccent(selectedAccent);

            appearanceChanged = true;

            document
            .getElementById("appearance-save-btn")
            .disabled = false;

        });

    });

    document.getElementById("appearance-save-btn").addEventListener("click", saveAppearance);

    // Load selected values into the radio buttons

    const savedTheme = localStorage.getItem("sandbox-theme") || "dark";
    const themeRadio = document.querySelector(`.theme-radio[value="${savedTheme}"]`);
    if (themeRadio) themeRadio.checked = true;

    const savedAccent = localStorage.getItem("sandbox-accent") || "blue";
    const accentRadio = document.querySelector(`.accent-radio[value="${savedAccent}"]`);
    if (accentRadio) accentRadio.checked = true;

    // =======================================================

    const googleBtn = document.getElementById("google-connect-btn");

    if (googleBtn) {
        googleBtn.addEventListener("click", async () => {

            if (googleBtn.dataset.connected === "true") {

                if (!confirm("Disconnect Google account?")) return;

                const response = await fetch("/settings/disconnect/google", {
                    method: "POST",
                    credentials: "include"
                });

                if (!response.ok) {
                    const err = await response.json();
                    alert(err.detail || "Failed to disconnect Google.");
                    return;
                }

                await loadConnections();
                await settingsManager.loadProfile();

            } else {

                window.location.href = "/settings/connect/google";

            }

        });
    }

    const githubBtn = document.getElementById("github-connect-btn");

    if (githubBtn) {
        githubBtn.addEventListener("click", async () => {

            if (githubBtn.dataset.connected === "true") {

                if (!confirm("Disconnect GitHub account?")) return;

                const response = await fetch("/settings/disconnect/github", {
                    method: "POST",
                    credentials: "include"
                });

                if (!response.ok) {
                    const err = await response.json();
                    alert(err.detail || "Failed to disconnect <Github></Github>.");
                    return;
                }

                await loadConnections();
                await settingsManager.loadProfile();

            } else {

                window.location.href = "/settings/connect/github";

            }

        });
    }

    // ── DELETE ACCOUNT ──
    const deleteAccountBtn = document.getElementById("deleteAccountBtn");
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener("click", async () => {
            // Disable button and show loading state
            deleteAccountBtn.disabled = true;
            const originalHTML = deleteAccountBtn.innerHTML;
            deleteAccountBtn.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round"
                    style="animation:da-spin .7s linear infinite;flex-shrink:0;">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                Loading…`;

            try {
                const confirmRes = await fetch("/auth/confirm-delete", { credentials: "include" });

                if (!confirmRes.ok) {
                    showToast("Failed to initiate account deletion.", "error");
                    return;
                }

                const { confirmation_text } = await confirmRes.json();
                openDeleteAccountModal(confirmation_text);

            } catch {
                showToast("Network error.", "error");
            } finally {
                // Always restore button regardless of success or failure
                deleteAccountBtn.disabled = false;
                deleteAccountBtn.innerHTML = originalHTML;
            }
        });
    }
});
/* ============================================================
   ADMIN CONTROLS — event delegation, no inline handlers
   ============================================================ */
async function refreshWorkspace() {
    const toolsEl   = document.querySelector("[data-workspace-tools]");
    const creditsEl = document.querySelector("[data-workspace-credits]");
    const execEl    = document.querySelector("[data-workspace-executions]");

    try {
        const response = await fetch("/workspace/", { credentials: "include" });
        if (!response.ok) return;

        const data = await response.json();
        if (!data.success || !data.workspace) return;

        const ws = data.workspace;

        if (toolsEl)   toolsEl.textContent   = formatMetric(ws.total_tools);
        if (execEl)    execEl.textContent     = formatMetric(ws.executions);
        if (creditsEl) {
            const dc = ws.daily_credits || {};
            const remaining = dc.remaining ?? "--";
            const limit     = dc.limit     ?? "--";
            creditsEl.textContent = `${remaining} / ${limit}`;
        }
    } catch (err) {
        console.error("refreshWorkspace failed:", err);
    }
}

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
        if (addBtn) addBtn.style.display = "";
        initAdminDashboard();   // ← this is the only change
    } else {
        document.body.classList.remove("is-admin");
    }
}

function isAdmin() {
    return document.body.classList.contains("is-admin");
}



/* ============================================================
   AUTH / SESSION
   ============================================================ */

function authHeaders() {
    return {}
}


function clearAuthSession() {
    localStorage.removeItem("SandBox_user");
    localStorage.removeItem("role");
}


/* ============================================================
   DATA LOADING
   ============================================================ */
async function loadConnections() {

    try {

        const response = await fetch("/auth/settings/connections", {
            credentials: "include"
        });

        if (!response.ok) {
            return;
        }

        const data = await response.json();
       

        const googleStatus = document.getElementById("google-status");
        const githubStatus = document.getElementById("github-status");

        const googleBtn = document.getElementById("google-connect-btn");
        const githubBtn = document.getElementById("github-connect-btn");

        if (!googleStatus || !githubStatus || !googleBtn || !githubBtn) {
            return;
        }

        // Google
        if (data.google_connected) {

            googleBtn.textContent = "Disconnect";
            googleBtn.dataset.connected = "true";
            googleStatus.textContent = 'Connected';

        } else {

            googleBtn.textContent = "Connect";
            googleBtn.dataset.connected = "false";
            googleStatus.textContent = 'Disconnected';

        }

        // GitHub
        if (data.github_connected) {

            githubBtn.textContent = "Disconnect";
            githubBtn.dataset.connected = "true";
            githubStatus.textContent = 'Connected';

        } else {

            githubBtn.textContent = "Connect";
            githubBtn.dataset.connected = "false";
            githubStatus.textContent = 'Disconnected';

        }

    } catch (err) {
        console.error("Failed to load connections:", err);
    }

}
/* ============================================================
   WORKSPACE (live)
   ============================================================ */
let workspaceLoaded = false;

async function loadWorkspace() {
    workspaceLoaded = true;

    const toolsEl     = document.querySelector("[data-workspace-tools]");
    const creditsEl    = document.querySelector("[data-workspace-credits]");
    const execEl        = document.querySelector("[data-workspace-executions]");
    const nameEls       = document.querySelectorAll("[data-workspace-name]");
    const emailEls      = document.querySelectorAll("[data-workspace-email]");
    const avatarEls     = document.querySelectorAll("[data-workspace-avatar]");

    const DEFAULT_AVATAR = "/assets/default_avatar.png";

    try {
        const response = await fetch("/workspace/", {
            credentials: "include"
        });

        if (response.status === 401 || response.status === 403) {
            if (toolsEl) toolsEl.textContent = "--";
            if (creditsEl) creditsEl.textContent = "--";
            if (execEl) execEl.textContent = "--";
            return;
        }

        if (!response.ok) throw new Error("Workspace request failed");

        const data = await response.json();
        if (!data.success || !data.workspace) throw new Error("Malformed workspace response");

        const ws = data.workspace;

        nameEls.forEach(el => el.textContent = ws.name || "Workspace");
        emailEls.forEach(el => el.textContent = ws.email || "Not signed in");
        avatarEls.forEach(img => {
            img.src = ws.avatar || DEFAULT_AVATAR;
            img.onerror = function () { this.src = DEFAULT_AVATAR; };
        });

        if (toolsEl) toolsEl.textContent = formatMetric(ws.total_tools);
        if (execEl) execEl.textContent = formatMetric(ws.executions);

        if (creditsEl) {
            const dc = ws.daily_credits || {};
            const remaining = dc.remaining ?? "--";
            const limit = dc.limit ?? "--";
            creditsEl.textContent = `${remaining} / ${limit}`;
        }

    } catch (err) {
        console.error("Failed to load workspace:", err);
        if (toolsEl) toolsEl.textContent = "Unable to load workspace.";
        if (creditsEl) creditsEl.textContent = "Unable to load workspace.";
        if (execEl) execEl.textContent = "Unable to load workspace.";
    }
}
async function fetchFirstAvailable(urls) {
    for (const url of urls) {
        try {
            const response = await fetch(url, { headers: authHeaders(), credentials: "include", mode: "cors" });
            if (response.ok) return await response.json();
        } catch (_) { continue; }
    }
    return null;
}

async function loadDashboardData() {
    const me = await fetchFirstAvailable(apiCandidates.me);

    if (me) {
        renderProfile(me);

        localStorage.setItem(
            "SandBox_user",
            JSON.stringify(me)
        );

        const passwordEmail =
            document.getElementById("passwordEmail");

        if (passwordEmail) {
            passwordEmail.value = me.email;
        }

        applyAdminRole();
    } else {
        clearAuthSession();
        renderSignedOut();
    }

    
    /* Load tools from API (if available — otherwise static cards remain) */

}

/* ============================================================
   TOOL RENDERING
   ============================================================ */

async function loadAppearance() {

    try {

        const response = await fetch(
            "/user/appearance",
            {
                credentials: "include"
            }
        );

        if (!response.ok) {
            throw new Error("Unable to load appearance.");
        }

        const data = await response.json();

        selectedTheme = data.theme || "system";
        selectedAccent = data.accent_color || "blue";

        window.setTheme(selectedTheme);
        window.setAccent(selectedAccent);

        const themeRadio = document.querySelector(
            `.theme-radio[value="${selectedTheme}"]`
        );

        if (themeRadio) {
            themeRadio.checked = true;
        }

        const accentRadio = document.querySelector(
            `.accent-radio[value="${selectedAccent}"]`
        );

        if (accentRadio) {
            accentRadio.checked = true;
        }

    } catch (err) {

        console.error(err);

    }

}

async function saveAppearance(){

    try{
        const now = new Date();

        const utc = now.toISOString()
            .replace("T", " ")
            .replace("Z", "");

        const response = await fetch(
            "/user/appearance",
            {
                method:"PUT",
                credentials:"include",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({

                    theme:selectedTheme,

                    accent_color:selectedAccent

                })
            }
        );

        if(!response.ok){
            throw new Error("Unable to save appearance.");
        }
        await fetch(
            "/user/last-updated",
            {
                method:"PUT",
                credentials:"include",
            }
        );

        appearanceChanged=false;

        document
        .getElementById("appearance-save-btn")
        .disabled=true;

        showToast("Appearance updated successfully.", "success");

    }

    catch(err){
        showToast(err.message, "error");
    }

}

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

    const es = document.querySelector("[data-empty-state]");
    if (es) {
        es.hidden = visible !== 0;
        const msg = document.getElementById("empty-state-msg");
        const btn = document.getElementById("empty-create-btn");
        if (msg) msg.textContent = needle ? "Try a different search term." : "No tools available yet.";
        if (btn) btn.style.display = isAdmin() && !needle ? "" : "none";
    }
}

function updateResultCount(count) {
    const rc = document.querySelector("[data-result-count]");
    if (rc) rc.textContent = `${count} ${count === 1 ? "tool" : "tools"}`;
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

    let top  = rect.bottom + 4;
    let left = rect.right - menuW;

    if (top + menuH > window.innerHeight) top = rect.top - menuH - 4;
    if (left < 8) left = 8;

    menu.style.top  = `${top}px`;
    menu.style.left = `${left}px`;
    menu.classList.add("open");
    menu.removeAttribute("aria-hidden");

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

    const modal     = document.getElementById("tool-modal");
    const title     = document.getElementById("modal-title");
    const submitBtn = document.getElementById("modal-submit-btn");

    if (!modal || !title || !submitBtn) return;

    const nameInput = document.getElementById("tool-name-input");
    const catSelect = document.getElementById("tool-category-select");
    const descInput = document.getElementById("tool-description-input");
    const fileLabel = document.getElementById("logo-filename");
    const preview   = document.getElementById("logo-preview");

    if (nameInput) nameInput.value = editData?.name || "";
    if (catSelect) catSelect.value = editData?.category || "";
    if (descInput) descInput.value = editData?.description || "";
    if (fileLabel) fileLabel.textContent = "Click to upload or drag PNG here";
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
    if (!modal) return;
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    editingToolId = null;
}

async function openEditToolModal(toolId) {
    try {
        const res = await fetch(`/api/tools/${toolId}`, { headers: authHeaders() });
        if (res.ok) {
            const tool = await res.json();
            openToolModal(tool);
            return;
        }
    } catch (_) {}

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

    select.innerHTML = `
        <option value="">Select Python file…</option>
        <option value="pdf_viewer.py"${selected === "pdf_viewer.py" ? " selected" : ""}>pdf_viewer.py</option>
        <option value="sql_generator.py"${selected === "sql_generator.py" ? " selected" : ""}>sql_generator.py</option>
        <option value="image_resizer.py"${selected === "image_resizer.py" ? " selected" : ""}>image_resizer.py</option>
    `;
}

async function submitToolForm() {
    const name        = document.getElementById("tool-name-input")?.value.trim() || "";
    const category    = document.getElementById("tool-category-select")?.value || "";
    const description = document.getElementById("tool-description-input")?.value.trim() || "";
    const sourceFile  = document.getElementById("tool-file-select")?.value || "";
    const logoInput   = document.getElementById("tool-logo-input");
    const logoFile    = logoInput?.files?.[0] || null;

    if (!name)       return showToast("Tool name is required.", "error");
    if (!category)   return showToast("Please select a category.", "error");
    if (!sourceFile) return showToast("Please select a Python file.", "error");

    const btn = document.getElementById("modal-submit-btn");
    if (!btn) return;
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
    } catch (_) {
        showToast("Network error. Please try again.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = editingToolId
                ? `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Save Changes`
                : `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Create Tool`;
        }
    }
}

function refreshToolCard(tool, oldId = null) {
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
        </a>`;
}

/* ============================================================
   DELETE MODAL
   ============================================================ */

let deletingToolId = null;

function openDeleteModal(toolId, toolName) {
    deletingToolId = toolId;
    const modal = document.getElementById("delete-modal");
    if (!modal) return;
    const nameDisplay = document.getElementById("delete-tool-name-display");
    if (nameDisplay) nameDisplay.textContent = toolName;
    modal.classList.add("open");
    modal.removeAttribute("aria-hidden");
}

function closeDeleteModal() {
    const modal = document.getElementById("delete-modal");
    if (!modal) return;
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    deletingToolId = null;
}
/* ============================================================
   TOOL CATEGORY FILTER
   ============================================================ */

function initToolCategoryFilter() {

    const filters = document.querySelectorAll(".tool-filter");
    const cards = document.querySelectorAll(".tool-card");
    const resultCount = document.querySelector("[data-result-count]");

    if (!filters.length || !cards.length) {
        return;
    }

    filters.forEach((filter) => {

        filter.addEventListener("click", () => {

            const selectedCategory = filter.dataset.filter;

            /* Update active state */
            filters.forEach((item) => {
                item.classList.remove("active");
                item.setAttribute("aria-selected", "false");
            });

            filter.classList.add("active");
            filter.setAttribute("aria-selected", "true");

            /* Filter cards */
            let visibleCount = 0;

            cards.forEach((card) => {

                const category = card.dataset.toolCategory;

                const shouldShow =
                    selectedCategory === "all" ||
                    category === selectedCategory;

                card.hidden = !shouldShow;

                if (shouldShow) {
                    visibleCount++;
                }

            });

            /* Update result count */
            if (resultCount) {
                resultCount.textContent =
                    `${visibleCount} ${visibleCount === 1 ? "tool" : "tools"}`;
            }

        });

    });
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
    const zone    = document.getElementById("logo-drop-zone");
    const input   = document.getElementById("tool-logo-input");
    const label   = document.getElementById("logo-filename");
    const preview = document.getElementById("logo-preview");

    if (!zone || !input) return;

    input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (!file) return;
        if (label) label.textContent = file.name;
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
        if (label) label.textContent = file.name;
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
   NAVIGATION
   ============================================================ */

function initializeNavigation() {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            document.querySelectorAll(".nav-item").forEach(l => l.classList.remove("active"));
            item.classList.add("active");
            const dashboard = document.querySelector("[data-dashboard]");
            dashboard?.classList.remove("nav-open");
            document.querySelector(".mobile-menu")?.setAttribute("aria-expanded", "false");
        });
    });
}

/* ============================================================
   SECTION NAVIGATION (dashboard / account)
   ============================================================ */

function initializeSectionNavigation() {
    const navItems = document.querySelectorAll(".nav-item[data-section]");
    const sections = document.querySelectorAll(".dashboard-section");

    if (!navItems.length || !sections.length) return;

    const anchorTargets = ["tools", "workspace"];

    function showSection(sectionId) {
        if (anchorTargets.includes(sectionId)) {
            // Show dashboard section and scroll to anchor
            sections.forEach(section => {
                const active = section.dataset.sectionId === "dashboard";
                section.style.display = active ? "" : "none";
                section.classList.toggle("active", active);
            });

            navItems.forEach(item => {
                item.classList.toggle("active", item.dataset.section === sectionId);
            });

            setTimeout(() => {
                document.getElementById(sectionId)
                    ?.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 50);
            return;
        }

        // Normal section switch (dashboard, account, etc.)
        sections.forEach(section => {
            const active = section.dataset.sectionId === sectionId;
            section.style.display = active ? "" : "none";
            section.classList.toggle("active", active);
        });

        navItems.forEach(item => {
            item.classList.toggle("active", item.dataset.section === sectionId);
        });

        history.replaceState(
            null,
            "",
            sectionId === "dashboard" ? "/" : `#${sectionId}`
        );
    }

    navItems.forEach(item => {
        item.addEventListener("click", function (e) {
            const href = this.getAttribute("href");
            if (href && href.startsWith("#")) {
                e.preventDefault();
                showSection(this.dataset.section);
            }
        });
    });

    // Initial route
    let initial = window.location.hash.replace("#", "");
    if (!initial) initial = "dashboard";

    const exists = [...sections].some(s => s.dataset.sectionId === initial);
    showSection(exists ? initial : "dashboard");
}

function initializeScrollSpy() {
    const sections = [
        { id: "hero-panel",  section: "dashboard" },
        { id: "workspace",   section: "workspace"  },
        { id: "tools",       section: "tools"      },
    ];

    // Get the actual elements
    const observables = sections
        .map(s => ({
            el: s.id === "hero-panel"
                ? document.querySelector(".hero-panel")
                : document.getElementById(s.id),
            section: s.section,
        }))
        .filter(s => s.el);

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;

                const matched = observables.find(s => s.el === entry.target);
                if (!matched) return;

                // Update active nav item
                document.querySelectorAll(".nav-item[data-section]").forEach(item => {
                    item.classList.toggle(
                        "active",
                        item.dataset.section === matched.section
                    );
                });
            });
        },
        {
            root: null,
            rootMargin: "-40% 0px -50% 0px", // triggers when element is near center
            threshold: 0,
        }
    );

    observables.forEach(s => observer.observe(s.el));
}

/* ============================================================
   SETTINGS NAVIGATION (within account section)
   ============================================================ */

function initializeSettingsNavigation() {
    const settingsLinks   = document.querySelectorAll(".settings-nav-link[data-settings-section]");
    const settingsSections = document.querySelectorAll(".settings-section[data-settings-section]");

    if (!settingsLinks.length || !settingsSections.length) return;

    function showSettingsSection(sectionId) {
        settingsSections.forEach(section => {
            const active = section.dataset.settingsSection === sectionId;
            section.style.display = active ? "" : "none";
            section.classList.toggle("active", active);
        });

        settingsLinks.forEach(link => {
            link.classList.toggle("active", link.dataset.settingsSection === sectionId);
        });
    }

    settingsLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            showSettingsSection(this.dataset.settingsSection);
        });
    });

    /* Activate first settings section by default */
    const firstActive = document.querySelector(".settings-section.active[data-settings-section]");
    const firstSection = firstActive?.dataset.settingsSection
        || settingsSections[0]?.dataset.settingsSection;
    if (firstSection) showSettingsSection(firstSection);
}

/* ============================================================
   PROFILE
   ============================================================ */

function initializeProfile() {
    const profileButton = document.querySelector(".profile-trigger");
    const profileMenu   = document.querySelector(".profile-menu");

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
    if (storedUser) {
        renderProfile(storedUser);
    } else {
        renderSignedOut();
    }

    document.querySelector("[data-logout]")?.addEventListener("click", logout);
}

function renderProfile(user) {
    const name = user.name || "Workspace";
    const email = user.email || "Not signed in";
    const bio = user.bio || "Hey, there!";
    const provider = user.provider || "local";

    const DEFAULT_AVATAR = "/assets/default_avatar.png";

    document.querySelectorAll("[data-user-avatar]").forEach(img => {
        img.src = user.avatar || DEFAULT_AVATAR;
        img.onerror = function () { this.src = DEFAULT_AVATAR; };
    });
    document.querySelectorAll("[data-user-name]").forEach(t => t.textContent = name);
    document.querySelectorAll("[data-user-bio]").forEach(t => t.textContent = bio);
    document.querySelectorAll("[data-user-email]").forEach(t => t.textContent = email);

    const profileName = document.getElementById("profileFullName");
    if (profileName) profileName.value = user.name || "";

    const profileEmail = document.getElementById("profileEmail");
    if (profileEmail) profileEmail.value = user.email || "";

    const profileBio = document.getElementById("profileBio");
    if (profileBio) profileBio.value = user.bio || "";


    const wt = document.querySelector("[data-workspace-title]");
    const ws = document.querySelector("[data-workspace-subtitle]");
    if (wt) wt.textContent = `${name}'s workspace`;
    if (ws) ws.textContent = `${email} authenticated with ${provider}.`;

    document.querySelectorAll("[data-auth-link]").forEach(l => l.hidden = true);
    const logoutBtn = document.querySelector("[data-logout]");
    if (logoutBtn) logoutBtn.hidden = false;
}

function renderSignedOut() {
    const DEFAULT_AVATAR = "/assets/default_avatar.png";

    document.querySelectorAll("[data-user-avatar]").forEach(img => { img.src = DEFAULT_AVATAR; });
    document.querySelectorAll("[data-user-name]").forEach(t => t.textContent = "Workspace");
    document.querySelectorAll("[data-user-bio]").forEach(t => t.textContent = "Hey, there");
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
    try {
        await fetch("/auth/logout", { method: "POST", credentials: "include" });
    } finally {
        clearAuthSession();
        renderSignedOut();
        window.location.href = "/login";
    }
}

/* ============================================================
   COMMAND PALETTE
   ============================================================ */

function initializeCommandPalette() {
    document.querySelectorAll("[data-open-command]").forEach(button => {
        button.addEventListener("click", openCommandPalette);
    });

    document.addEventListener("keydown", event => {
        const dashboard = document.querySelector("[data-dashboard]");
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

/* ============================================================
   MOBILE DRAWER
   ============================================================ */

function initializeMobileDrawer() {
    const button    = document.querySelector(".mobile-menu");
    const dashboard = document.querySelector("[data-dashboard]");
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
window.refreshWorkspace = refreshWorkspace;
/* ============================================================
   ADMIN DASHBOARD — COMPLETE UNIFIED JS
   Replace ALL previous admin JS (admin_dashboard_fixed.js +
   admin_user_table.js) with this single file.
   ============================================================ */

/* ── State ── */
const ADMIN_PAGE_SIZE      = 20;
const ADMIN_USER_PAGE_SIZE = 20;

let adminExecPage     = 0;
let adminExecAll      = [];
let adminExecFiltered = [];

let adminUserPage     = 0;
let adminUserAll      = [];
let adminUserFiltered = [];

/* ============================================================
   ENTRY POINT
   ============================================================ */

async function initAdminDashboard() {
  injectAdminNavItem();
  initAdminTabs();
  await Promise.allSettled([
    loadAdminStats(),
    loadAdminExecutions(),
    loadAdminToolViews(),
    loadAdminUsers(),
  ]);
  wireAdminControls();
  injectExecDetailModal();
  injectUserDetailModal();
}

/* ============================================================
   SIDEBAR NAV ITEM
   ============================================================ */

function injectAdminNavItem() {
  if (document.getElementById("nav-admin")) return;
  const nav = document.querySelector(".sidebar-nav");
  if (!nav) return;

  const a = document.createElement("a");
  a.className       = "nav-item nav-item--admin";
  a.id              = "nav-admin";
  a.href            = "#admin-dashboard";
  a.dataset.section = "admin-dashboard";
  a.innerHTML = `
    <span class="nav-icon">
      <svg viewBox="0 0 24 24">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
    </span>
    <span>Admin</span>`;

  const bottom = nav.parentElement.querySelector(".sidebar-bottom");
  if (bottom) nav.parentElement.insertBefore(a, bottom);
  else nav.appendChild(a);

  a.addEventListener("click", e => { e.preventDefault(); showAdminSection(); });
}

function showAdminSection() {
  document.querySelectorAll(".dashboard-section").forEach(s => {
    const active = s.dataset.sectionId === "admin-dashboard";
    s.style.display = active ? "" : "none";
    s.classList.toggle("active", active);
  });
  document.querySelectorAll(".nav-item[data-section]").forEach(item =>
    item.classList.toggle("active", item.dataset.section === "admin-dashboard")
  );
  history.replaceState(null, "", "#admin-dashboard");
}

/* ============================================================
   TABS
   ============================================================ */

function initAdminTabs() {
  document.querySelectorAll(".admin-tab").forEach(tab => {
    tab.addEventListener("click", () => switchAdminTab(tab.dataset.adminTab));
  });
}

function switchAdminTab(tabId) {
  document.querySelectorAll(".admin-tab").forEach(t => {
    const active = t.dataset.adminTab === tabId;
    t.classList.toggle("active", active);
    t.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".admin-tab-panel").forEach(p => {
    const active = p.dataset.adminPanel === tabId;
    p.classList.toggle("active", active);
  });
}

/* ============================================================
   WIRE CONTROLS — clone buttons to prevent listener stacking
   ============================================================ */

function wireAdminControls() {
  /* Refresh */
  cloneAndListen("admin-refresh-btn", "click", async () => {
    adminExecPage = 0;
    adminUserPage = 0;
    await Promise.allSettled([
      loadAdminStats(),
      loadAdminExecutions(),
      loadAdminToolViews(),
      loadAdminUsers(),
    ]);
    showToast("Dashboard refreshed.", "success");
  });

  /* Exec search */
  cloneAndListen("admin-exec-search", "input", e => filterAdminExecTable(e.target.value));

  /* Exec pagination */
  cloneAndListen("admin-prev-btn", "click", () => {
    if (adminExecPage > 0) { adminExecPage--; renderAdminExecPage(); }
  });
  cloneAndListen("admin-next-btn", "click", () => {
    const max = Math.ceil(adminExecFiltered.length / ADMIN_PAGE_SIZE) - 1;
    if (adminExecPage < max) { adminExecPage++; renderAdminExecPage(); }
  });

  /* User search */
  cloneAndListen("admin-user-search", "input", e => filterAdminUserTable(e.target.value));

  /* User pagination */
  cloneAndListen("admin-user-prev-btn", "click", () => {
    if (adminUserPage > 0) { adminUserPage--; renderAdminUserPage(); }
  });
  cloneAndListen("admin-user-next-btn", "click", () => {
    const max = Math.ceil(adminUserFiltered.length / ADMIN_USER_PAGE_SIZE) - 1;
    if (adminUserPage < max) { adminUserPage++; renderAdminUserPage(); }
  });
}

/* Clone element → strip old listeners → attach new one */
function cloneAndListen(id, event, handler) {
  const el = document.getElementById(id);
  if (!el) return;
  const clone = el.cloneNode(true);
  el.replaceWith(clone);
  clone.addEventListener(event, handler);
}

/* ============================================================
   STATS
   ============================================================ */

async function loadAdminStats() {
  try {
    const res  = await fetch("/admin/stats", { credentials: "include" });
    if (!res.ok) throw new Error();
    const data = await res.json();
    animateCount("admin-total-users", data.total_users);
    animateCount("admin-total-tools", data.total_tools);
    animateCount("admin-total-exec",  data.total_executions);
  } catch {
    ["admin-total-users","admin-total-tools","admin-total-exec"]
      .forEach(id => setEl(id, "—"));
  }
}

/* ============================================================
   EXECUTIONS
   ============================================================ */

async function loadAdminExecutions() {
  const tbody = document.getElementById("admin-exec-tbody");
  if (!tbody) return;
  skeletons(tbody, 5, 5);

  try {
    const res  = await fetch("/admin/executions?limit=500&offset=0", { credentials: "include" });
    if (!res.ok) throw new Error();
    const data = await res.json();

    adminExecAll      = data.executions || [];
    adminExecFiltered = [...adminExecAll];
    adminExecPage     = 0;

    setEl("admin-exec-count",      `${(data.total || adminExecAll.length).toLocaleString()} records`);
    setEl("admin-tab-exec-count",  String(data.total || adminExecAll.length));

    renderAdminExecPage();
  } catch {
    tbody.innerHTML = emptyRow(5, "Failed to load executions.");
  }
}

function renderAdminExecPage() {
  const tbody = document.getElementById("admin-exec-tbody");
  if (!tbody) return;
  const start = adminExecPage * ADMIN_PAGE_SIZE;
  const slice = adminExecFiltered.slice(start, start + ADMIN_PAGE_SIZE);

  if (!slice.length) {
    tbody.innerHTML = emptyRow(5, "No executions match your filter.");
    updatePagination("admin-page-info", "admin-prev-btn", "admin-next-btn",
                     adminExecPage, adminExecFiltered.length, ADMIN_PAGE_SIZE);
    return;
  }

  tbody.innerHTML = slice.map((row, i) => `
    <tr class="admin-exec-row" data-idx="${start + i}" style="cursor:pointer;" title="Click to view details">
      <td title="${esc(row.exec_id)}">${esc(truncId(row.exec_id))}</td>
      <td><span class="admin-chip admin-chip--tool">${esc(row.tool_name)}</span></td>
      <td>${esc(row.user_email)}</td>
      <td><span class="admin-chip admin-chip--user">${esc(truncId(row.user_id))}</span></td>
      <td><span class="admin-ts">${fmtTs(row.timestamp)}</span></td>
    </tr>`).join("");

  tbody.querySelectorAll(".admin-exec-row").forEach(row =>
    row.addEventListener("click", () => openExecDetail(adminExecFiltered[+row.dataset.idx]))
  );

  updatePagination("admin-page-info", "admin-prev-btn", "admin-next-btn",
                   adminExecPage, adminExecFiltered.length, ADMIN_PAGE_SIZE);
}

function filterAdminExecTable(q) {
  const n = q.trim().toLowerCase();
  adminExecFiltered = n
    ? adminExecAll.filter(r => [r.exec_id, r.tool_name, r.user_email, r.user_id]
        .some(v => (v||"").toLowerCase().includes(n)))
    : [...adminExecAll];
  adminExecPage = 0;
  renderAdminExecPage();
}

/* ============================================================
   TOOL VIEWS — now renders into a proper table
   ============================================================ */

async function loadAdminToolViews() {
  const tbody = document.getElementById("admin-tool-tbody");
  if (!tbody) return;
  skeletons(tbody, 3, 5);

  try {
    const res  = await fetch("/admin/tool-views", { credentials: "include" });
    if (!res.ok) throw new Error();
    const { tools = [] } = await res.json();

    setEl("admin-tool-views-count", `${tools.length} tool${tools.length !== 1 ? "s" : ""}`);
    setEl("admin-tab-tools-count",  String(tools.length));

    if (!tools.length) { tbody.innerHTML = emptyRow(5, "No tools found."); return; }

    const max = Math.max(...tools.map(t => t.execution_count), 1);

    tbody.innerHTML = tools.map((tool, i) => `
      <tr>
        <td style="color:var(--text-muted);font-weight:700;">${i + 1}</td>
        <td style="font-weight:500;color:var(--ink-1);">${esc(tool.tool_name)}</td>
        <td><span class="tool-category-badge" data-cat="${esc(tool.category)}">${esc(tool.category || "—")}</span></td>
        <td>
          <div class="admin-inline-bar-bg">
            <div class="admin-inline-bar-fill"
                 style="width:${Math.max(4, Math.round((tool.execution_count / max) * 100))}%">
            </div>
          </div>
        </td>
        <td style="text-align:right;font-weight:700;color:var(--ink-1);">
          ${(tool.execution_count || 0).toLocaleString()}
        </td>
      </tr>`).join("");
  } catch {
    tbody.innerHTML = emptyRow(5, "Failed to load tool usage.");
  }
}

/* ============================================================
   USERS
   ============================================================ */

async function loadAdminUsers() {
  const tbody = document.getElementById("admin-user-tbody");
  if (!tbody) return;
  skeletons(tbody, 5, 10);

  try {
    const res  = await fetch("/admin/users?limit=500&offset=0", { credentials: "include" });
    if (!res.ok) throw new Error();
    const data = await res.json();

    adminUserAll      = data.users || [];
    adminUserFiltered = [...adminUserAll];
    adminUserPage     = 0;

    setEl("admin-user-count",      `${data.total.toLocaleString()} users`);
    setEl("admin-tab-users-count", String(data.total));

    renderAdminUserPage();
  } catch {
    tbody.innerHTML = emptyRow(10, "Failed to load users.");
  }
}

function renderAdminUserPage() {
  const tbody = document.getElementById("admin-user-tbody");
  if (!tbody) return;
  const start = adminUserPage * ADMIN_USER_PAGE_SIZE;
  const slice = adminUserFiltered.slice(start, start + ADMIN_USER_PAGE_SIZE);

  if (!slice.length) {
    tbody.innerHTML = emptyRow(10, "No users match your filter.");
    updatePagination("admin-user-page-info","admin-user-prev-btn","admin-user-next-btn",
                     adminUserPage, adminUserFiltered.length, ADMIN_USER_PAGE_SIZE);
    return;
  }

  tbody.innerHTML = slice.map((u, i) => {
    const pct = u.credits_total > 0
      ? Math.round((u.credits_remaining / u.credits_total) * 100) : 0;
    return `
      <tr class="admin-user-row" data-idx="${start + i}" style="cursor:pointer;" title="Click to view details">
        <td style="padding:8px 16px;">
          <img class="admin-user-avatar"
               src="${esc(u.avatar_url || "/assets/default_avatar.png")}"
               alt=""
               onerror="this.src='/assets/default_avatar.png'">
        </td>
        <td style="font-weight:500;color:var(--ink-1);">${esc(u.name || "—")}</td>
        <td>${esc(u.email || "—")}</td>
        <td>${u.role === "admin"
          ? `<span class="admin-chip admin-chip--admin">admin</span>`
          : `<span class="admin-chip admin-chip--user-role">user</span>`}</td>
        <td style="color:var(--text-muted);font-size:11px;">${esc(u.provider || "—")}</td>
        <td>${u.google_connected
          ? `<span class="admin-badge admin-badge--yes">✓ Yes</span>`
          : `<span class="admin-badge admin-badge--no">— No</span>`}</td>
        <td>${u.github_connected
          ? `<span class="admin-badge admin-badge--yes">✓ Yes</span>`
          : `<span class="admin-badge admin-badge--no">— No</span>`}</td>
        <td>
          <div class="admin-credit-wrap">
            <span class="admin-credit-label">${u.credits_remaining} / ${u.credits_total}</span>
            <div class="admin-credit-bar-bg">
              <div class="admin-credit-bar-fill" style="width:${pct}%"></div>
            </div>
          </div>
        </td>
        <td><span class="admin-ts">${fmtTs(u.created_at)}</span></td>
        <td><span class="admin-ts">${esc(u.last_updated || "—")}</span></td>
      </tr>`;
  }).join("");

  tbody.querySelectorAll(".admin-user-row").forEach(row =>
    row.addEventListener("click", () => openUserDetail(adminUserFiltered[+row.dataset.idx]))
  );

  updatePagination("admin-user-page-info","admin-user-prev-btn","admin-user-next-btn",
                   adminUserPage, adminUserFiltered.length, ADMIN_USER_PAGE_SIZE);
}

function filterAdminUserTable(q) {
  const n = q.trim().toLowerCase();
  adminUserFiltered = n
    ? adminUserAll.filter(u => [u.name, u.email, u.role, u.provider]
        .some(v => (v||"").toLowerCase().includes(n)))
    : [...adminUserAll];
  adminUserPage = 0;
  renderAdminUserPage();
}

/* ============================================================
   EXEC DETAIL MODAL
   ============================================================ */

function injectExecDetailModal() {
  if (document.getElementById("exec-detail-modal")) return;
  const m = document.createElement("div");
  m.id = "exec-detail-modal";
  m.className = "modal-backdrop";
  m.setAttribute("aria-hidden","true");
  m.innerHTML = `
    <div class="modal-box" role="dialog" aria-modal="true" style="max-width:560px;">
      <div class="modal-header">
        <h3>Execution Detail</h3>
        <button class="modal-close" id="exec-detail-close" type="button" aria-label="Close">
          <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="modal-body" id="exec-detail-body" style="gap:14px;"></div>
    </div>`;
  document.body.appendChild(m);
  m.addEventListener("click", e => { if (e.target === m) closeExecDetail(); });
  document.getElementById("exec-detail-close")?.addEventListener("click", closeExecDetail);
}

function openExecDetail(row) {
  const modal = document.getElementById("exec-detail-modal");
  const body  = document.getElementById("exec-detail-body");
  if (!modal || !body || !row) return;
  body.innerHTML = `
    ${dField("Execution ID", row.exec_id, "mono")}
    ${dField("Tool",         row.tool_name)}
    ${dField("User Email",   row.user_email)}
    ${dField("User ID",      row.user_id, "mono")}
    ${dField("Timestamp",    fmtTs(row.timestamp))}
    ${row.user_input ? dBlock("User Input", row.user_input) : ""}
    ${row.output     ? dBlock("Output",     row.output)     : ""}`;
  modal.classList.add("open");
  modal.removeAttribute("aria-hidden");
}

function closeExecDetail() {
  const m = document.getElementById("exec-detail-modal");
  if (m) { m.classList.remove("open"); m.setAttribute("aria-hidden","true"); }
}

/* ============================================================
   USER DETAIL MODAL
   ============================================================ */

function injectUserDetailModal() {
  if (document.getElementById("user-detail-modal")) return;
  const m = document.createElement("div");
  m.id = "user-detail-modal";
  m.className = "modal-backdrop";
  m.setAttribute("aria-hidden","true");
  m.innerHTML = `
    <div class="modal-box" role="dialog" aria-modal="true" style="max-width:620px;">
      <div class="modal-header">
        <h3>User Detail</h3>
        <button class="modal-close" id="user-detail-close" type="button" aria-label="Close">
          <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="modal-body" id="user-detail-body"></div>
    </div>`;
  document.body.appendChild(m);
  m.addEventListener("click", e => { if (e.target === m) closeUserDetail(); });
  document.getElementById("user-detail-close")?.addEventListener("click", closeUserDetail);
}

function openUserDetail(u) {
  const modal = document.getElementById("user-detail-modal");
  const body  = document.getElementById("user-detail-body");
  if (!modal || !body || !u) return;

  const pct = u.credits_total > 0
    ? Math.round((u.credits_remaining / u.credits_total) * 100) : 0;

  body.innerHTML = `
    <div class="user-detail-grid">
      <!-- Avatar row -->
      <div class="user-detail-avatar-row">
        <img class="user-detail-avatar-img"
             src="${esc(u.avatar_url || "/assets/default_avatar.png")}"
             alt=""
             onerror="this.src='/assets/default_avatar.png'">
        <div class="user-detail-avatar-meta">
          <strong>${esc(u.name || "—")}</strong>
          <span>${esc(u.email || "—")}</span>
          <span style="margin-top:4px;display:block;">
            ${u.role === "admin"
              ? `<span class="admin-chip admin-chip--admin">admin</span>`
              : `<span class="admin-chip admin-chip--user-role">user</span>`}
          </span>
        </div>
      </div>

      ${uField("User ID",    u.id,       "mono")}
      ${uField("Provider",   u.provider)}
      ${uField("Bio",        u.bio || "—")}
      ${uField("Avatar URL", u.avatar_url, "mono")}

      <div style="display:flex;flex-direction:column;gap:6px;">
        ${label("Google")}
        ${u.google_connected
          ? `<span class="admin-badge admin-badge--yes">✓ Connected${u.google_email ? " · "+esc(u.google_email) : ""}</span>`
          : `<span class="admin-badge admin-badge--no">Not connected</span>`}
      </div>
      <div style="display:flex;flex-direction:column;gap:6px;">
        ${label("GitHub")}
        ${u.github_connected
          ? `<span class="admin-badge admin-badge--yes">✓ Connected${u.github_email ? " · "+esc(u.github_email) : ""}</span>`
          : `<span class="admin-badge admin-badge--no">Not connected</span>`}
      </div>

      <div class="user-detail-full" style="display:flex;flex-direction:column;gap:8px;">
        ${label("Credits")}
        <div style="display:flex;align-items:center;gap:14px;">
          <span style="font-size:var(--text-xl);font-weight:700;color:var(--ink-0);">${u.credits_remaining}</span>
          <span style="color:var(--text-muted);font-size:var(--text-sm);">/ ${u.credits_total} total</span>
          <span style="color:var(--text-muted);font-size:var(--text-xs);">(reset: ${esc(u.last_credit_reset || "—")})</span>
        </div>
        <div class="admin-credit-bar-bg" style="height:6px;">
          <div class="admin-credit-bar-fill" style="width:${pct}%"></div>
        </div>
      </div>

      ${uField("Joined",       fmtTs(u.created_at))}
      ${uField("Last Updated", u.last_updated || "—")}
    </div>`;

  modal.classList.add("open");
  modal.removeAttribute("aria-hidden");
}

function closeUserDetail() {
  const m = document.getElementById("user-detail-modal");
  if (m) { m.classList.remove("open"); m.setAttribute("aria-hidden","true"); }
}

/* ============================================================
   SHARED HELPERS
   ============================================================ */

function updatePagination(infoId, prevId, nextId, page, total, pageSize) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  setEl(infoId, `Page ${page + 1} of ${totalPages}`);
  const prev = document.getElementById(prevId);
  const next = document.getElementById(nextId);
  if (prev) prev.disabled = page === 0;
  if (next) next.disabled = page >= totalPages - 1;
}

function skeletons(tbody, rows, cols) {
  tbody.innerHTML = Array(rows).fill(0).map(() =>
    `<tr><td colspan="${cols}"><div class="skeleton" style="height:18px;border-radius:6px;"></div></td></tr>`
  ).join("");
}

function emptyRow(cols, msg) {
  return `<tr><td colspan="${cols}" class="admin-table-empty">${msg}</td></tr>`;
}

function setEl(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function truncId(id) {
  if (!id) return "—";
  return id.length > 10 ? id.slice(0, 8) + "…" : id;
}

function fmtTs(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: true,
    });
  } catch { return iso; }
}

function esc(v) { return escapeHtml(String(v ?? "")); }

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = performance.now();
  const dur   = 800;
  (function step(now) {
    const p = Math.min((now - start) / dur, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))).toLocaleString();
    if (p < 1) requestAnimationFrame(step);
  })(start);
}

/* Modal field helpers */
function dField(label, value, style = "") {
  const mono = style === "mono"
    ? "font-family:ui-monospace,monospace;font-size:11px;word-break:break-all;" : "";
  return `<div style="display:flex;flex-direction:column;gap:4px;">
    <span style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--text-muted);">${esc(label)}</span>
    <span style="font-size:var(--text-sm);color:var(--ink-1);${mono}">${esc(value || "—")}</span>
  </div>`;
}

function dBlock(lbl, value) {
  return `<div style="display:flex;flex-direction:column;gap:6px;">
    <span style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--text-muted);">${esc(lbl)}</span>
    <pre style="margin:0;padding:14px;border:1px solid var(--border-1);border-radius:var(--radius-md);
                background:var(--surface-1);color:var(--ink-2);
                font-family:ui-monospace,monospace;font-size:11px;line-height:1.6;
                white-space:pre-wrap;word-break:break-word;max-height:200px;overflow-y:auto;">${esc(value)}</pre>
  </div>`;
}

function uField(lbl, value, style = "") {
  const mono = style === "mono"
    ? "font-family:ui-monospace,monospace;font-size:11px;word-break:break-all;" : "";
  return `<div style="display:flex;flex-direction:column;gap:4px;">
    <span style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--text-muted);">${esc(lbl)}</span>
    <span style="font-size:var(--text-sm);color:var(--ink-1);${mono}">${esc(String(value ?? "—"))}</span>
  </div>`;
}

function label(text) {
  return `<span style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--text-muted);">${esc(text)}</span>`;
}

/* ============================================================
   DELETE ACCOUNT MODAL
   ============================================================ */

function openDeleteAccountModal(phrase) {
    document.getElementById("delete-account-modal")?.remove();

    const modal = document.createElement("div");
    modal.id = "delete-account-modal";
    modal.style.cssText = [
        "position:fixed",
        "inset:0",
        "z-index:9999",
        "background:rgba(0,0,0,.72)",
        "backdrop-filter:blur(18px) saturate(160%)",
        "-webkit-backdrop-filter:blur(18px) saturate(160%)",
        "display:flex",
        "align-items:center",
        "justify-content:center",
        "padding:1rem"
    ].join(";");

    modal.innerHTML = `
    <div class="da-card">

        <div class="da-header">
            <div class="da-icon">
                <svg viewBox="0 0 24 24">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14H6L5 6"/>
                    <path d="M10 11v6"/><path d="M14 11v6"/>
                    <path d="M9 6V4h6v2"/>
                </svg>
            </div>
            <div>
                <p class="da-title">Delete account</p>
                <p class="da-subtitle">This action cannot be undone.</p>
            </div>
            <button id="da-close" class="da-close-btn" type="button" aria-label="Close">
                <svg viewBox="0 0 24 24">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>

        <div class="da-warning">
            <svg viewBox="0 0 24 24">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span>All your data, tools, history, and settings will be permanently deleted. You won't be able to recover anything.</span>
        </div>

        <div class="da-divider"></div>

        <label class="da-label" for="da-input">
            To confirm, type <code>${escapeHtml(phrase)}</code> below
        </label>

        <input
            id="da-input"
            class="da-input"
            type="text"
            autocomplete="off"
            spellcheck="false"
            placeholder="Type the phrase exactly…"
        >

        <p class="da-error" id="da-err" aria-live="polite"></p>

        <div class="da-actions">
            <button id="da-cancel" class="da-btn-cancel" type="button">Cancel</button>
            <button id="da-submit" class="da-btn-delete" type="button" disabled>
                <svg viewBox="0 0 24 24">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14H6L5 6"/>
                    <path d="M10 11v6"/><path d="M14 11v6"/>
                    <path d="M9 6V4h6v2"/>
                </svg>
                Delete my account
            </button>
        </div>
    </div>`;

    document.body.appendChild(modal);

    const inp    = modal.querySelector("#da-input");
    const submit = modal.querySelector("#da-submit");
    const errEl  = modal.querySelector("#da-err");

    inp.focus();

    // Enable button only when phrase matches exactly
    inp.addEventListener("input", () => {
        errEl.textContent = "";
        inp.style.borderColor = "";
        const match = inp.value.trim() === phrase;
        submit.disabled   = !match;
        submit.style.opacity = match ? "1" : ".45";
        submit.style.cursor  = match ? "pointer" : "not-allowed";
    });

    // Close handlers
    const closeModal = () => modal.remove();
    modal.querySelector("#da-close").addEventListener("click", closeModal);
    modal.querySelector("#da-cancel").addEventListener("click", closeModal);
    modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });

    // Escape key
    const onKeyDown = e => { if (e.key === "Escape") { closeModal(); document.removeEventListener("keydown", onKeyDown); } };
    document.addEventListener("keydown", onKeyDown);

    // Submit
    submit.addEventListener("click", async () => {
        if (inp.value.trim() !== phrase) {
            errEl.textContent = "Phrase doesn't match. Check for typos.";
            inp.style.borderColor = "var(--border-danger)";
            inp.focus();
            return;
        }

        submit.disabled = true;
        submit.style.opacity = ".6";
        submit.style.cursor = "not-allowed";
        submit.innerHTML = `
            <svg class="da-spinner" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            Deleting…`;

        try {
            const res = await fetch("/auth/account", {
                method: "DELETE",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ confirmation_text: inp.value.trim() })
            });

            if (res.ok) {
                modal.remove();
                showToast("Account deleted successfully.", "success");
                clearAuthSession();
                setTimeout(() => window.location.href = "/login", 1500);
            } else {
                const err = await res.json().catch(() => ({}));
                errEl.textContent = err.detail || "Something went wrong. Try again.";
                inp.style.borderColor = "var(--border-danger)";
                submit.disabled = false;
                submit.style.opacity = "1";
                submit.style.cursor = "pointer";
                submit.innerHTML = `
                    <svg viewBox="0 0 24 24">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14H6L5 6"/>
                        <path d="M10 11v6"/><path d="M14 11v6"/>
                        <path d="M9 6V4h6v2"/>
                    </svg>
                    Delete my account`;
            }
        } catch {
            errEl.textContent = "Network error. Check your connection.";
            submit.disabled = !match;
            submit.style.opacity = "1";
            submit.style.cursor = "pointer";
        }
    });
}

/* Spinner keyframe — injected once */
if (!document.getElementById("da-spin-style")) {
    const s = document.createElement("style");
    s.id = "da-spin-style";
    s.textContent = "@keyframes da-spin { to { transform: rotate(360deg); } }";
    document.head.appendChild(s);
}
/* =========================================================
   SANDBOX FOOTER
   ========================================================= */

function initSandboxFooter() {

    const yearElement = document.getElementById(
        "sb-footer-year"
    );

    if (!yearElement) {
        return;
    }

    yearElement.textContent = new Date().getFullYear();
}


/* ---------------------------------------------------------
   Initialize
   --------------------------------------------------------- */

if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initSandboxFooter,
        { once: true }
    );

} else {

    initSandboxFooter();

}