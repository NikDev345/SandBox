const dashboard = document.querySelector("[data-dashboard]");
const toolCards = Array.from(document.querySelectorAll(".tool-card"));
const searchInput = document.getElementById("global-search");
const emptyState = document.querySelector("[data-empty-state]");
const resultCount = document.querySelector("[data-result-count]");

const apiCandidates = {
    metrics: ["/analytics/summary", "/api/analytics/summary", "/admin/metrics"],
    tools: ["/tools", "/api/tools"],
    me: ["/auth/me", "/api/auth/me"]
};

document.addEventListener("DOMContentLoaded", () => {
    consumeOAuthCallback();
    initializeMetricCards();
    initializeSearch();
    initializeNavigation();
    initializeProfile();
    initializeCommandPalette();
    initializeMobileDrawer();
    loadDashboardData();
});

function initializeMetricCards() {
    document.querySelectorAll(".metric-card").forEach(card => {
        card.classList.add("loading");
    });
}

function setMetric(key, value, note) {
    const valueTarget = document.querySelector(`[data-metric="${key}"]`);
    const noteTarget = document.querySelector(`[data-metric-note="${key}"]`);
    valueTarget && (valueTarget.textContent = value);
    noteTarget && (noteTarget.textContent = note);
    valueTarget?.closest(".metric-card")?.classList.remove("loading");
}

async function fetchFirstAvailable(urls) {
    for (const url of urls) {
        try {
            const response = await fetch(url, {
                headers: authHeaders()
            });
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            continue;
        }
    }
    return null;
}

function authHeaders() {
    const token = localStorage.getItem("access_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function persistAuthSession(token, user) {
    localStorage.setItem("access_token", token);
    localStorage.setItem("user_id", user.id);
    localStorage.setItem("toolbox_user", JSON.stringify(user));
}

function clearAuthSession() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("toolbox_user");
}

function consumeOAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("auth_token");
    const user = safeJson(params.get("auth_user"));

    if (!token || !user) return;

    persistAuthSession(token, user);
    window.history.replaceState({}, document.title, window.location.pathname);
}

async function loadDashboardData() {
    const [metrics, tools, me] = await Promise.all([
        fetchFirstAvailable(apiCandidates.metrics),
        fetchFirstAvailable(apiCandidates.tools),
        fetchFirstAvailable(apiCandidates.me)
    ]);

    const discoveredTools = normalizeTools(tools);
    const totalTools = discoveredTools.length || toolCards.length;

    setMetric("totalTools", totalTools.toLocaleString(), discoveredTools.length ? "Loaded from API" : "Using local tool registry");
    setMetric("executions", formatMetric(metrics?.executions), metrics?.executions == null ? "Analytics API pending" : "Live analytics");
    setMetric("users", formatMetric(metrics?.users), metrics?.users == null ? "User metric pending" : "Live users");
    setMetric("uptime", metrics?.uptime || "--", metrics?.uptime ? "Status API connected" : "Status API pending");

    if (discoveredTools.length) {
        renderTools(discoveredTools);
    }

    if (me) {
        renderProfile(me);
        localStorage.setItem("toolbox_user", JSON.stringify(me));
    } else if (localStorage.getItem("access_token")) {
        clearAuthSession();
        renderSignedOut();
    }
}

function normalizeTools(payload) {
    const list = Array.isArray(payload) ? payload : payload?.tools;
    if (!Array.isArray(list)) return [];
    return list
        .map(tool => ({
            name: tool.name || tool.title,
            description: tool.description || "Open this workflow in ToolBox.",
            category: tool.category || "Tool",
            slug: tool.slug || slugify(tool.name || tool.title || "")
        }))
        .filter(tool => tool.name && tool.slug);
}

function renderTools(tools) {
    const grid = document.querySelector("[data-tool-grid]");
    if (!grid) return;

    grid.innerHTML = tools.map(tool => `
        <a class="tool-card" href="/tools/${tool.slug}" data-tool-name="${escapeHtml(tool.name)}" data-tool-category="${escapeHtml(tool.category)}">
            <span class="tool-icon" data-icon="bolt"></span>
            <h3>${escapeHtml(tool.name)}</h3>
            <p>${escapeHtml(tool.description)}</p>
            <span class="tool-meta">${escapeHtml(tool.category)} <b>Open</b></span>
        </a>
    `).join("");

    updateToolReferences();
    filterTools(searchInput?.value || "");
}

function updateToolReferences() {
    toolCards.splice(0, toolCards.length, ...Array.from(document.querySelectorAll(".tool-card")));
}

function formatMetric(value) {
    if (value == null) return "--";
    if (typeof value === "number") return value.toLocaleString();
    return value;
}

function initializeSearch() {
    updateResultCount(toolCards.length);
    searchInput?.addEventListener("input", event => {
        filterTools(event.target.value);
    });
}

function filterTools(query) {
    const needle = query.trim().toLowerCase();
    let visible = 0;

    toolCards.forEach(card => {
        const haystack = `${card.dataset.toolName || ""} ${card.dataset.toolCategory || ""} ${card.textContent}`.toLowerCase();
        const match = !needle || haystack.includes(needle);
        card.hidden = !match;
        if (match) visible += 1;
    });

    updateResultCount(visible);
    if (emptyState) emptyState.hidden = visible !== 0;
}

function updateResultCount(count) {
    if (resultCount) {
        resultCount.textContent = `${count} ${count === 1 ? "tool" : "tools"}`;
    }
}

function initializeNavigation() {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            document.querySelectorAll(".nav-item").forEach(link => link.classList.remove("active"));
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

    const storedUser = safeJson(localStorage.getItem("toolbox_user"));
    if (storedUser && localStorage.getItem("access_token")) {
        renderProfile(storedUser);
    } else {
        renderSignedOut();
    }

    document.querySelector("[data-logout]")?.addEventListener("click", logout);
}

function renderProfile(user) {
    const name = user.name || user.email?.split("@")[0] || "Workspace";
    const email = user.email || "Not signed in";
    const provider = user.provider || user.auth_provider || "Local";
    const initials = name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(part => part[0])
        .join("")
        .toUpperCase() || "TB";

    document.querySelectorAll("[data-user-avatar]").forEach(target => target.textContent = initials);
    document.querySelectorAll("[data-user-name]").forEach(target => target.textContent = name);
    document.querySelectorAll("[data-user-provider]").forEach(target => target.textContent = provider);
    document.querySelectorAll("[data-user-email]").forEach(target => target.textContent = email);
    document.querySelector("[data-workspace-title]") && (document.querySelector("[data-workspace-title]").textContent = `${name}'s workspace`);
    document.querySelector("[data-workspace-subtitle]") && (document.querySelector("[data-workspace-subtitle]").textContent = `${email} authenticated with ${provider}.`);
    document.querySelectorAll("[data-auth-link]").forEach(link => link.hidden = true);
    document.querySelector("[data-logout]") && (document.querySelector("[data-logout]").hidden = false);
}

function renderSignedOut() {
    document.querySelectorAll("[data-user-avatar]").forEach(target => target.textContent = "TB");
    document.querySelectorAll("[data-user-name]").forEach(target => target.textContent = "Workspace");
    document.querySelectorAll("[data-user-provider]").forEach(target => target.textContent = "Signed out");
    document.querySelectorAll("[data-user-email]").forEach(target => target.textContent = "Not signed in");
    document.querySelector("[data-workspace-title]") && (document.querySelector("[data-workspace-title]").textContent = "Your active workspace");
    document.querySelector("[data-workspace-subtitle]") && (document.querySelector("[data-workspace-subtitle]").textContent = "Sign in to sync your tools, history, and saved workflows.");
    document.querySelectorAll("[data-auth-link]").forEach(link => link.hidden = false);
    document.querySelector("[data-logout]") && (document.querySelector("[data-logout]").hidden = true);
}

async function logout() {
    const token = localStorage.getItem("access_token");

    try {
        if (token) {
            await fetch("/auth/logout", {
                method: "POST",
                headers: authHeaders()
            });
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
            dashboard?.classList.remove("nav-open");
        }
    });
}

function openCommandPalette() {
    closeCommandPalette();

    const modal = document.createElement("div");
    modal.className = "command-modal";
    modal.innerHTML = `
        <div class="command-box" role="dialog" aria-modal="true" aria-label="Command search">
            <input type="search" placeholder="Search tools..." autocomplete="off">
            <div class="command-list">
                ${toolCards.map(card => `
                    <a class="command-item" href="${card.getAttribute("href")}">
                        <span>${escapeHtml(card.dataset.toolName || card.querySelector("h3")?.textContent || "Tool")}</span>
                        <small>${escapeHtml(card.dataset.toolCategory || "Tool")}</small>
                    </a>
                `).join("")}
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    const input = modal.querySelector("input");
    const items = Array.from(modal.querySelectorAll(".command-item"));
    input?.focus();

    input?.addEventListener("input", event => {
        const query = event.target.value.toLowerCase();
        items.forEach(item => {
            item.hidden = !item.textContent.toLowerCase().includes(query);
        });
    });

    modal.addEventListener("click", event => {
        if (event.target === modal) closeCommandPalette();
    });
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

function safeJson(value) {
    try {
        return value ? JSON.parse(value) : null;
    } catch (error) {
        return null;
    }
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
