/**
 * ============================================================
 * ui.js — Rendering, toasts, modals, tables, JSON editor.
 * No network calls live here; app.js orchestrates state + api.js.
 * ============================================================
 */

const UI = (() => {
  /* ---------------------------------------------------------
     Icons (small inline SVG library, reused across the app)
     --------------------------------------------------------- */
  const ICONS = {
    check: `<svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>`,
    alert: `<svg viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01M10.29 3.86l-8.18 14.18A2 2 0 0 0 3.82 21h16.36a2 2 0 0 0 1.71-3.14L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>`,
    info: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 16v-5M12 8h.01"/></svg>`,
    x: `<svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>`,
    trash: `<svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6h16z"/></svg>`,
    edit: `<svg viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>`,
    copy: `<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`,
  };

  /* ---------------------------------------------------------
     Toasts
     --------------------------------------------------------- */
  const toastContainer = () => document.getElementById("toastContainer");

  function toast(message, type = "info", duration = 4000) {
    const container = toastContainer();
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    const icon = type === "success" ? ICONS.check : type === "error" ? ICONS.alert : type === "warning" ? ICONS.alert : ICONS.info;
    el.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-msg"></span>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;
    el.querySelector(".toast-msg").textContent = message;
    el.style.setProperty("--toast-dur", `${duration}ms`);
    const bar = el.querySelector.bind(el);
    container.appendChild(el);

    const remove = () => {
      el.classList.add("removing");
      setTimeout(() => el.remove(), 220);
    };
    el.querySelector(".toast-close").addEventListener("click", remove);
    const timer = setTimeout(remove, duration);
    el.addEventListener("mouseenter", () => clearTimeout(timer));
    return el;
  }

  /* ---------------------------------------------------------
     Modal helpers
     --------------------------------------------------------- */
  function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }

  function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add("closing");
    setTimeout(() => {
      el.classList.remove("closing");
      el.classList.add("hidden");
      document.body.style.overflow = "";
    }, 160);
  }

  /* ---------------------------------------------------------
     Formatting helpers
     --------------------------------------------------------- */
  function statusClass(code) {
    if (code >= 200 && code < 300) return "s-2xx";
    if (code >= 300 && code < 400) return "s-3xx";
    if (code >= 400 && code < 500) return "s-4xx";
    return "s-5xx";
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function timeAgo(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return "";
    const diffMs = Date.now() - date.getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  }

  /* ---------------------------------------------------------
     Stats cards
     --------------------------------------------------------- */
  function renderStats(mocks) {
    const total = mocks.length;
    const active = mocks.filter((m) => m.is_active).length;
    const disabled = total - active;
    const hits = mocks.reduce((sum, m) => sum + (m.hit_count || 0), 0);

    setText("statTotal", total);
    setText("statActive", active);
    setText("statDisabled", disabled);
    setText("statHits", hits.toLocaleString());
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  /* ---------------------------------------------------------
     Table rendering
     --------------------------------------------------------- */
  function renderSkeletonRows(count = 5) {
    const rows = [];
    for (let i = 0; i < count; i++) {
      rows.push(`
        <tr class="skeleton-row">
          <td><div class="sk-bar sk-w-60"></div></td>
          <td><div class="sk-bar sk-w-40"></div></td>
          <td><div class="sk-bar sk-w-50"></div></td>
          <td><div class="sk-bar sk-w-30"></div></td>
          <td><div class="sk-bar sk-w-20"></div></td>
          <td><div class="sk-bar sk-w-30"></div></td>
          <td><div class="sk-bar sk-w-40"></div></td>
        </tr>
      `);
    }
    return rows.join("");
  }

  function renderTableRows(mocks, baseUrl) {
    return mocks
      .map((mock) => {
        const rawUrl = mock.endpoint_url || "";
        const fullUrl = rawUrl.startsWith("http")
          ? rawUrl
          : `${baseUrl}${rawUrl}`;
        return `
        <tr data-id="${mock.id}" class="animate-fade-in-up">
          <td>
            <div class="cell-name">
              <span class="n-title">${escapeHtml(mock.name)}</span>
              <span class="n-sub">${escapeHtml(mock.endpoint_token)}</span>
            </div>
          </td>
          <td><span class="badge badge-method m-${mock.method}">${mock.method}</span></td>
          <td>
            <div class="cell-endpoint" title="${escapeHtml(fullUrl)}">
              <span>${escapeHtml(mock.endpoint_url)}</span>
            </div>
          </td>
          <td><span class="badge badge-status ${statusClass(mock.status_code)}">${mock.status_code}</span></td>
          <td>${(mock.hit_count || 0).toLocaleString()}</td>
          <td>
            <label class="switch">
              <input type="checkbox" class="row-active-toggle" data-id="${mock.id}" ${mock.is_active ? "checked" : ""} />
              <span class="switch-track"></span>
            </label>
          </td>
          <td>
            <div class="row-actions">
              <button class="row-action-btn" data-action="copy" data-url="${escapeHtml(fullUrl)}" title="Copy URL">${ICONS.copy}</button>
              <button class="row-action-btn" data-action="edit" data-id="${mock.id}" title="Edit">${ICONS.edit}</button>
              <button class="row-action-btn danger" data-action="delete" data-id="${mock.id}" data-name="${escapeHtml(mock.name)}" title="Delete">${ICONS.trash}</button>
            </div>
          </td>
        </tr>
      `;
      })
      .join("");
  }

  function renderEmptyTable() {
    return `
      <tr>
        <td colspan="7">
          <div class="empty-state">
            <div class="empty-illustration">
              <svg viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M4 6h16M4 12h16M4 18h7"/></svg>
            </div>
            <div class="empty-title">No mock APIs yet</div>
            <div class="empty-sub">Create your first mock endpoint to start returning fake JSON responses for testing.</div>
            <button class="btn btn-primary btn-sm" id="emptyCreateBtn">+ Create Mock API</button>
          </div>
        </td>
      </tr>
    `;
  }

  /* ---------------------------------------------------------
     JSON editor — line numbers + light syntax highlight
     --------------------------------------------------------- */
  function highlightJson(rawText) {
    const escaped = escapeHtml(rawText);
    return escaped.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+\.?\d*([eE][+-]?\d+)?)/g,
      (match) => {
        let cls = "tok-num";
        if (/^"/.test(match)) {
          cls = /:\s*$/.test(match) ? "tok-key" : "tok-str";
        } else if (/true|false/.test(match)) {
          cls = "tok-bool";
        } else if (/null/.test(match)) {
          cls = "tok-null";
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
  }

  function updateJsonEditor(textareaEl, lineNumbersEl, highlightEl) {
    const value = textareaEl.value;
    const lineCount = value.split("\n").length;
    let lines = "";
    for (let i = 1; i <= lineCount; i++) lines += i + "\n";
    lineNumbersEl.textContent = lines;
    highlightEl.innerHTML = highlightJson(value) + "\n";
  }

  function syncEditorScroll(textareaEl, lineNumbersEl, highlightEl) {
    lineNumbersEl.scrollTop = textareaEl.scrollTop;
    highlightEl.scrollTop = textareaEl.scrollTop;
    highlightEl.scrollLeft = textareaEl.scrollLeft;
  }

  /* ---------------------------------------------------------
     Key/value (headers) rows
     --------------------------------------------------------- */
  function createKvRow(key = "", value = "") {
    const row = document.createElement("div");
    row.className = "kv-row";
    row.innerHTML = `
      <input type="text" class="form-input kv-key" placeholder="Header name (e.g. X-Custom-Header)" value="${escapeHtml(key)}" />
      <input type="text" class="form-input kv-value" placeholder="Header value" value="${escapeHtml(value)}" />
      <button type="button" class="kv-remove-btn" title="Remove header">${ICONS.x}</button>
    `;
    return row;
  }

  /* ---------------------------------------------------------
     Auth field visibility
     --------------------------------------------------------- */
  function setAuthFieldsVisibility(authType) {
    document.querySelectorAll("[data-auth-group]").forEach((group) => {
      const shouldShow = group.dataset.authGroup === authType;
      group.classList.toggle("hidden", !shouldShow);
    });
  }

  return {
    ICONS,
    toast,
    openModal,
    closeModal,
    statusClass,
    escapeHtml,
    timeAgo,
    renderStats,
    setText,
    renderSkeletonRows,
    renderTableRows,
    renderEmptyTable,
    highlightJson,
    updateJsonEditor,
    syncEditorScroll,
    createKvRow,
    setAuthFieldsVisibility,
  };
})();