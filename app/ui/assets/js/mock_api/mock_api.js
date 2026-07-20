/**
 * ============================================================
 * app.js — Initialization, routing, state, event listeners.
 * ============================================================
 */

(() => {
  "use strict";

  /* ---------------------------------------------------------
     Application state
     --------------------------------------------------------- */
  const state = {
    mocks: [],
    loading: false,
    view: "dashboard",
    editingId: null, // null => create mode, else editing this mock's id
    deleteTargetId: null,
    filters: { search: "", method: "", active: "" },
  };

  /* ---------------------------------------------------------
     DOM shortcuts
     --------------------------------------------------------- */
  const $ = (id) => document.getElementById(id);
  const els = {}; // populated on DOMContentLoaded

  /* ---------------------------------------------------------
     Init
     --------------------------------------------------------- */
  document.addEventListener("DOMContentLoaded", () => {
    cacheElements();
    hydrateSettings();
    bindNavigation();
    bindTopbar();
    bindTableActions();
    bindFormEvents();
    bindModalEvents();
    bindSettingsEvents();
    initHeaderRow(); // start create form with one empty header row
    updateJsonPreview();
    updateLivePreview();
    loadMocks();
  });

  function cacheElements() {
    [
      "sidebar", "sidebarOverlay", "sidebarCollapseBtn", "topbarMenuBtn",
      "globalSearch", "refreshBtn", "dashboardTableBody", "myApisTableBody",
      "tableSearch", "methodFilter", "activeFilter", "navApiCount",
      "mockForm", "nameInput", "nameGroup", "methodSelect", "methodDot",
      "statusCodeInput", "statusCodeGroup", "delayInput", "delayGroup",
      "responseBodyInput", "jsonLineNumbers", "jsonHighlight", "jsonEditorWrap",
      "jsonError", "formatJsonBtn", "headersList", "addHeaderBtn",
      "authTypeGrid", "bearerTokenInput", "apiKeyInput", "apiKeyHeaderInput",
      "usernameInput", "passwordInput", "resetFormBtn", "submitFormBtn",
      "submitFormBtnLabel", "formTitle", "formEyebrow", "editingBadge",
      "formStatusHint", "previewMethodBadge", "previewEndpointText",
      "previewStatusText", "previewJson", "modalDelete", "deleteTargetName",
      "confirmDeleteBtn", "modalSuccess", "successSubText", "successEndpointUrl",
      "copySuccessUrlBtn", "successMethodBadge", "successStatusBadge",
      "viewInMyApisBtn", "baseUrlInput", "authTokenInput", "saveSettingsBtn",
      "fabCreate", "statTotal", "statActive", "statDisabled", "statHits",
    ].forEach((id) => (els[id] = $(id)));
  }

  /* ---------------------------------------------------------
     Settings hydration
     --------------------------------------------------------- */
  function hydrateSettings() {
    els.baseUrlInput.value = API.getBaseUrl();
    els.authTokenInput.value = API.getToken();
  }

  function bindSettingsEvents() {
    els.saveSettingsBtn.addEventListener("click", () => {
      const url = els.baseUrlInput.value.trim() || API.DEFAULT_BASE_URL;
      API.setBaseUrl(url);
      API.setToken(els.authTokenInput.value.trim());
      UI.toast("Settings saved.", "success");
      loadMocks();
    });
  }

  /* ---------------------------------------------------------
     Routing / navigation
     --------------------------------------------------------- */
  function bindNavigation() {
    document.querySelectorAll(".nav-item[data-view]").forEach((item) => {
      item.addEventListener("click", () => switchView(item.dataset.view));
    });
    document.querySelectorAll("[data-view-link]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.dataset.viewLink === "create") startCreateFlow();
        switchView(btn.dataset.viewLink);
      });
    });
    els.fabCreate.addEventListener("click", () => {
      startCreateFlow();
      switchView("create");
    });

    // Sidebar collapse (desktop)
    els.sidebarCollapseBtn.addEventListener("click", () => {
      els.sidebar.classList.toggle("collapsed");
    });

    // Mobile sidebar toggle
    els.topbarMenuBtn.addEventListener("click", () => {
      els.sidebar.classList.add("mobile-open");
      els.sidebarOverlay.classList.add("show");
    });
    els.sidebarOverlay.addEventListener("click", closeMobileSidebar);
  }

  function closeMobileSidebar() {
    els.sidebar.classList.remove("mobile-open");
    els.sidebarOverlay.classList.remove("show");
  }

  function switchView(viewName) {
    state.view = viewName;
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    const target = $(`view-${viewName}`);
    if (target) target.classList.add("active");

    document.querySelectorAll(".nav-item[data-view]").forEach((item) => {
      item.classList.toggle("active", item.dataset.view === viewName);
    });

    closeMobileSidebar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ---------------------------------------------------------
     Topbar (search + refresh)
     --------------------------------------------------------- */
  function bindTopbar() {
    els.refreshBtn.addEventListener("click", () => loadMocks(true));

    els.globalSearch.addEventListener("input", (e) => {
      const q = e.target.value.trim();
      if (q) {
        els.tableSearch.value = q;
        state.filters.search = q.toLowerCase();
        switchView("myapis");
        renderMyApisTable();
      }
    });

    els.tableSearch.addEventListener("input", (e) => {
      state.filters.search = e.target.value.trim().toLowerCase();
      renderMyApisTable();
    });
    els.methodFilter.addEventListener("change", (e) => {
      state.filters.method = e.target.value;
      renderMyApisTable();
    });
    els.activeFilter.addEventListener("change", (e) => {
      state.filters.active = e.target.value;
      renderMyApisTable();
    });
  }

  /* ---------------------------------------------------------
     Data loading
     --------------------------------------------------------- */
  async function loadMocks(showToast) {
    state.loading = true;
    renderLoadingTables();
    try {
      const res = await API.listMocks();
      state.mocks = (res && res.mocks) || [];
      renderAll();
      if (showToast) UI.toast("Mock APIs refreshed.", "success", 2500);
    } catch (err) {
      state.mocks = [];
      renderAll();
      UI.toast(err.message || "Failed to load mock APIs.", "error", 5500);
    } finally {
      state.loading = false;
    }
  }

  function renderLoadingTables() {
    els.dashboardTableBody.innerHTML = UI.renderSkeletonRows(3);
    els.myApisTableBody.innerHTML = UI.renderSkeletonRows(6);
  }

  function renderAll() {
    UI.renderStats(state.mocks);
    UI.setText("navApiCount", state.mocks.length);
    renderDashboardTable();
    renderMyApisTable();
  }

  function renderDashboardTable() {
    const recent = [...state.mocks]
      .slice(0, 5);
    if (recent.length === 0) {
      els.dashboardTableBody.innerHTML = UI.renderEmptyTable();
      bindEmptyCreateButtons();
      return;
    }
    els.dashboardTableBody.innerHTML = UI.renderTableRows(recent, API.getBaseUrl());
  }

  function renderMyApisTable() {
    let filtered = state.mocks.filter((m) => {
      if (state.filters.method && m.method !== state.filters.method) return false;
      if (state.filters.active === "active" && !m.is_active) return false;
      if (state.filters.active === "inactive" && m.is_active) return false;
      if (state.filters.search) {
        const haystack = `${m.name} ${m.endpoint_url} ${m.endpoint_token}`.toLowerCase();
        if (!haystack.includes(state.filters.search)) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      els.myApisTableBody.innerHTML = UI.renderEmptyTable();
      bindEmptyCreateButtons();
      return;
    }
    els.myApisTableBody.innerHTML = UI.renderTableRows(filtered, API.getBaseUrl());
  }

  function bindEmptyCreateButtons() {
    document.querySelectorAll("#emptyCreateBtn").forEach((btn) => {
      btn.addEventListener("click", () => {
        startCreateFlow();
        switchView("create");
      });
    });
  }

  /* ---------------------------------------------------------
     Table row action delegation (edit / delete / copy / toggle)
     --------------------------------------------------------- */
  function bindTableActions() {
    document.addEventListener("click", (e) => {
      const actionBtn = e.target.closest("[data-action]");
      if (!actionBtn) return;
      const action = actionBtn.dataset.action;
      const id = actionBtn.dataset.id;

      if (action === "copy") {
        copyToClipboard(actionBtn.dataset.url, actionBtn);
      } else if (action === "edit") {
        startEditFlow(id);
        switchView("create");
      } else if (action === "delete") {
        state.deleteTargetId = id;
        els.deleteTargetName.textContent = actionBtn.dataset.name || "this mock";
        UI.openModal("modalDelete");
      }
    });

    document.addEventListener("change", (e) => {
      if (e.target.classList.contains("row-active-toggle")) {
        toggleActive(e.target.dataset.id, e.target.checked, e.target);
      }
    });
  }

  async function toggleActive(id, isActive, checkboxEl) {
    const mock = state.mocks.find((m) => m.id === id);
    if (!mock) return;
    checkboxEl.disabled = true;
    try {
      const detail = await API.getMock(id);
      const payload = detailToRequestPayload(detail);
      payload.is_active = isActive; // informational; backend controls status via other fields today
      await API.updateMock(id, payload);
      mock.is_active = isActive;
      UI.renderStats(state.mocks);
      UI.toast(`"${mock.name}" is now ${isActive ? "active" : "disabled"}.`, "success", 2500);
    } catch (err) {
      checkboxEl.checked = !isActive;
      UI.toast(err.message || "Could not update status.", "error");
    } finally {
      checkboxEl.disabled = false;
    }
  }

  function copyToClipboard(text, triggerEl) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        UI.toast("Endpoint URL copied to clipboard.", "success", 2500);
        if (triggerEl) {
          triggerEl.classList.add("success-flash");
          setTimeout(() => triggerEl.classList.remove("success-flash"), 900);
        }
      })
      .catch(() => UI.toast("Could not copy to clipboard.", "error"));
  }

  /* ---------------------------------------------------------
     Modal wiring (delete confirm + success)
     --------------------------------------------------------- */
  function bindModalEvents() {
    document.querySelectorAll("[data-close-modal]").forEach((btn) => {
      btn.addEventListener("click", () => UI.closeModal(btn.dataset.closeModal));
    });
    [els.modalDelete, els.modalSuccess].forEach((overlay) => {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) UI.closeModal(overlay.id);
      });
    });

    els.confirmDeleteBtn.addEventListener("click", handleConfirmDelete);
    els.copySuccessUrlBtn.addEventListener("click", () => {
      copyToClipboard(els.successEndpointUrl.value, els.copySuccessUrlBtn);
    });
    els.viewInMyApisBtn.addEventListener("click", () => {
      UI.closeModal("modalSuccess");
      switchView("myapis");
    });
  }

  async function handleConfirmDelete() {
    if (!state.deleteTargetId) return;
    const id = state.deleteTargetId;
    setBtnLoading(els.confirmDeleteBtn, true, "Deleting...");
    try {
      await API.deleteMock(id);
      state.mocks = state.mocks.filter((m) => m.id !== id);
      renderAll();
      UI.closeModal("modalDelete");
      UI.toast("Mock API deleted.", "success");
    } catch (err) {
      UI.toast(err.message || "Failed to delete mock API.", "error");
    } finally {
      setBtnLoading(els.confirmDeleteBtn, false, "Delete Permanently");
      state.deleteTargetId = null;
    }
  }

  /* ---------------------------------------------------------
     CREATE / EDIT FORM
     --------------------------------------------------------- */
  function bindFormEvents() {
    els.mockForm.addEventListener("submit", handleSubmit);
    els.resetFormBtn.addEventListener("click", () => {
      if (state.editingId) {
        startEditFlow(state.editingId);
      } else {
        startCreateFlow();
      }
      UI.toast("Form reset.", "info", 2000);
    });

    // Method select color dot + live preview
    els.methodSelect.addEventListener("change", () => {
      applyMethodDot();
      updateLivePreview();
    });
    applyMethodDot();

    els.statusCodeInput.addEventListener("input", updateLivePreview);
    els.responseBodyInput.addEventListener("input", () => {
      updateJsonPreview();
      updateLivePreview();
    });
    els.responseBodyInput.addEventListener("scroll", () =>
      UI.syncEditorScroll(els.responseBodyInput, els.jsonLineNumbers, els.jsonHighlight)
    );
    els.formatJsonBtn.addEventListener("click", formatJsonField);

    // Headers
    els.addHeaderBtn.addEventListener("click", () => addHeaderRow());
    els.headersList.addEventListener("click", (e) => {
      const removeBtn = e.target.closest(".kv-remove-btn");
      if (removeBtn) {
        removeBtn.closest(".kv-row").remove();
        updateLivePreview();
        renderHeadersEmptyState();
      }
    });
    els.headersList.addEventListener("input", updateLivePreview);

    // Auth type radio switching
    els.authTypeGrid.addEventListener("change", (e) => {
      if (e.target.name === "authType") {
        UI.setAuthFieldsVisibility(e.target.value);
        clearAuthFieldErrors();
        updateLivePreview();
      }
    });

    // Clear field error on input
    [
      els.nameInput, els.statusCodeInput, els.delayInput, els.bearerTokenInput,
      els.apiKeyInput, els.apiKeyHeaderInput, els.usernameInput, els.passwordInput,
    ].forEach((input) => {
      input.addEventListener("input", () => clearFieldError(input.closest(".form-group")));
    });
  }

  function applyMethodDot() {
    const colors = {
      GET: "var(--m-get)", POST: "var(--m-post)", PUT: "var(--m-put)",
      PATCH: "var(--m-patch)", DELETE: "var(--m-delete)",
    };
    els.methodDot.style.background = colors[els.methodSelect.value] || "var(--m-get)";
  }

  function updateJsonPreview() {
    UI.updateJsonEditor(els.responseBodyInput, els.jsonLineNumbers, els.jsonHighlight);
  }

  function formatJsonField() {
    try {
      const parsed = JSON.parse(els.responseBodyInput.value || "{}");
      els.responseBodyInput.value = JSON.stringify(parsed, null, 2);
      updateJsonPreview();
      updateLivePreview();
      clearFieldError(els.jsonEditorWrap.parentElement);
      els.jsonEditorWrap.classList.remove("invalid");
      UI.toast("JSON formatted.", "success", 2000);
    } catch (err) {
      UI.toast("Cannot format: invalid JSON.", "error");
    }
  }

  function initHeaderRow() {
    addHeaderRow();
  }

  function addHeaderRow(key = "", value = "") {
    const row = UI.createKvRow(key, value);
    els.headersList.appendChild(row);
    renderHeadersEmptyState();
  }

  function renderHeadersEmptyState() {
    const existing = els.headersList.querySelector(".kv-empty");
    if (els.headersList.children.length === 0) {
      if (!existing) {
        const p = document.createElement("div");
        p.className = "kv-empty";
        p.textContent = "No custom headers added.";
        els.headersList.appendChild(p);
      }
    } else if (existing && els.headersList.children.length > 1) {
      existing.remove();
    }
  }

  function clearHeaderRows() {
    els.headersList.innerHTML = "";
  }

  function getHeadersFromForm() {
    const headers = {};
    els.headersList.querySelectorAll(".kv-row").forEach((row) => {
      const key = row.querySelector(".kv-key").value.trim();
      const value = row.querySelector(".kv-value").value;
      if (key) headers[key] = value;
    });
    return headers;
  }

  function getSelectedAuthType() {
    const checked = els.authTypeGrid.querySelector('input[name="authType"]:checked');
    return checked ? checked.value : "NONE";
  }

  function setSelectedAuthType(type) {
    const radio = els.authTypeGrid.querySelector(`input[value="${type}"]`);
    if (radio) radio.checked = true;
    UI.setAuthFieldsVisibility(type || "NONE");
  }

  /* ---- Live preview panel ---- */
  function updateLivePreview() {
    const method = els.methodSelect.value;
    const status = els.statusCodeInput.value || "200";
    els.previewMethodBadge.textContent = method;
    els.previewMethodBadge.className = `badge badge-method m-${method}`;
    els.previewStatusText.textContent = status;

    let bodyPreview = "{}";
    try {
      bodyPreview = JSON.stringify(JSON.parse(els.responseBodyInput.value || "{}"), null, 2);
    } catch (_) {
      bodyPreview = "// Invalid JSON — fix errors above";
    }
    els.previewJson.textContent = bodyPreview;
  }

  /* ---------------------------------------------------------
     Form <-> payload conversion
     --------------------------------------------------------- */
  function buildAuthentication() {
    const authType = getSelectedAuthType();
    return {
      auth_type: authType,
      bearer_token: authType === "BEARER" ? els.bearerTokenInput.value.trim() : null,
      api_key: authType === "API_KEY" ? els.apiKeyInput.value.trim() : null,
      api_key_header:
        authType === "API_KEY" ? els.apiKeyHeaderInput.value.trim() || "X-API-Key" : "X-API-Key",
      username: authType === "BASIC" ? els.usernameInput.value.trim() : null,
      password: authType === "BASIC" ? els.passwordInput.value : null,
    };
  }

  function buildPayload() {
    let responseBody = {};
    try {
      responseBody = JSON.parse(els.responseBodyInput.value || "{}");
    } catch (_) {
      responseBody = {};
    }
    return {
      name: els.nameInput.value.trim(),
      method: els.methodSelect.value,
      status_code: parseInt(els.statusCodeInput.value, 10) || 200,
      response_body: responseBody,
      response_headers: getHeadersFromForm(),
      response_delay_ms: parseInt(els.delayInput.value, 10) || 0,
      authentication: buildAuthentication(),
    };
  }

  function detailToRequestPayload(detail) {
    return {
      name: detail.name,
      method: detail.method,
      status_code: detail.status_code,
      response_body: detail.response_body,
      response_headers: detail.response_headers,
      response_delay_ms: detail.response_delay_ms,
      authentication: {
        auth_type: detail.authentication.auth_type,
        bearer_token: detail.authentication.bearer_token,
        api_key: detail.authentication.api_key,
        api_key_header: detail.authentication.api_key_header || "X-API-Key",
        username: detail.authentication.username,
        password: detail.authentication.password,
      },
    };
  }

  /* ---------------------------------------------------------
     Validation (mirrors backend MockAPIService._validate_request)
     --------------------------------------------------------- */
  function clearFieldError(group) {
    if (group) group.classList.remove("has-error");
  }
  function setFieldError(group) {
    if (group) group.classList.add("has-error");
  }
  function clearAuthFieldErrors() {
    [
      els.bearerTokenInput, els.apiKeyInput, els.apiKeyHeaderInput,
      els.usernameInput, els.passwordInput,
    ].forEach((input) => clearFieldError(input.closest(".form-group")));
  }

  function validateForm() {
    let valid = true;

    // Name required
    clearFieldError(els.nameGroup);
    if (!els.nameInput.value.trim()) {
      setFieldError(els.nameGroup);
      valid = false;
    }

    // Status code 100-599
    clearFieldError(els.statusCodeGroup);
    const status = parseInt(els.statusCodeInput.value, 10);
    if (isNaN(status) || status < 100 || status > 599) {
      setFieldError(els.statusCodeGroup);
      valid = false;
    }

    // Delay >= 0
    clearFieldError(els.delayGroup);
    const delay = parseInt(els.delayInput.value, 10);
    if (isNaN(delay) || delay < 0) {
      setFieldError(els.delayGroup);
      valid = false;
    }

    // JSON body valid + must be an object
    els.jsonEditorWrap.classList.remove("invalid");
    els.jsonError.style.display = "none";
    try {
      const parsed = JSON.parse(els.responseBodyInput.value || "{}");
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("must be an object");
      }
    } catch (_) {
      els.jsonEditorWrap.classList.add("invalid");
      els.jsonError.style.display = "flex";
      valid = false;
    }

    // Authentication fields
    clearAuthFieldErrors();
    const authType = getSelectedAuthType();
    if (authType === "BEARER" && !els.bearerTokenInput.value.trim()) {
      setFieldError(els.bearerTokenInput.closest(".form-group"));
      valid = false;
    } else if (authType === "API_KEY") {
      if (!els.apiKeyInput.value.trim()) {
        setFieldError(els.apiKeyInput.closest(".form-group"));
        valid = false;
      }
      if (!els.apiKeyHeaderInput.value.trim()) {
        setFieldError(els.apiKeyHeaderInput.closest(".form-group"));
        valid = false;
      }
    } else if (authType === "BASIC") {
      if (!els.usernameInput.value.trim()) {
        setFieldError(els.usernameInput.closest(".form-group"));
        valid = false;
      }
      if (!els.passwordInput.value) {
        setFieldError(els.passwordInput.closest(".form-group"));
        valid = false;
      }
    }

    return valid;
  }

  /* ---------------------------------------------------------
     Create / Edit flow control
     --------------------------------------------------------- */
  function startCreateFlow() {
    state.editingId = null;
    els.formEyebrow.textContent = "New Endpoint";
    els.formTitle.textContent = "Create Mock API";
    els.editingBadge.classList.add("hidden");
    els.submitFormBtnLabel.textContent = "Create Mock";
    els.formStatusHint.textContent = "";

    els.nameInput.value = "";
    els.methodSelect.value = "GET";
    els.statusCodeInput.value = "200";
    els.delayInput.value = "0";
    els.responseBodyInput.value = '{\n  "message": "Hello from your mock API!"\n}';
    clearHeaderRows();
    addHeaderRow();
    setSelectedAuthType("NONE");
    els.bearerTokenInput.value = "";
    els.apiKeyInput.value = "";
    els.apiKeyHeaderInput.value = "X-API-Key";
    els.usernameInput.value = "";
    els.passwordInput.value = "";

    document
      .querySelectorAll(".form-group.has-error")
      .forEach((g) => g.classList.remove("has-error"));
    els.jsonEditorWrap.classList.remove("invalid");
    els.jsonError.style.display = "none";

    applyMethodDot();
    updateJsonPreview();
    updateLivePreview();
  }

  async function startEditFlow(id) {
    state.editingId = id;
    els.formEyebrow.textContent = "Edit Endpoint";
    els.formTitle.textContent = "Edit Mock API";
    els.editingBadge.classList.remove("hidden");
    els.submitFormBtnLabel.textContent = "Save Changes";
    els.formStatusHint.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Loading mock details...`;

    try {
      const detail = await API.getMock(id);
      els.nameInput.value = detail.name || "";
      els.methodSelect.value = detail.method;
      els.statusCodeInput.value = detail.status_code;
      els.delayInput.value = detail.response_delay_ms;
      els.responseBodyInput.value = JSON.stringify(detail.response_body || {}, null, 2);

      clearHeaderRows();
      const headerEntries = Object.entries(detail.response_headers || {});
      if (headerEntries.length === 0) {
        addHeaderRow();
      } else {
        headerEntries.forEach(([k, v]) => addHeaderRow(k, v));
      }

      const auth = detail.authentication || { auth_type: "NONE" };
      setSelectedAuthType(auth.auth_type || "NONE");
      els.bearerTokenInput.value = auth.bearer_token || "";
      els.apiKeyInput.value = auth.api_key || "";
      els.apiKeyHeaderInput.value = auth.api_key_header || "X-API-Key";
      els.usernameInput.value = auth.username || "";
      els.passwordInput.value = auth.password || "";

      applyMethodDot();
      updateJsonPreview();
      updateLivePreview();
      els.formStatusHint.textContent = `Editing "${detail.name}"`;
    } catch (err) {
      UI.toast(err.message || "Failed to load mock API details.", "error");
      startCreateFlow();
    }
  }

  function setBtnLoading(btn, isLoading, label) {
    if (!btn) return;
    btn.disabled = isLoading;
    btn.classList.toggle("btn-loading", isLoading);
    const labelEl = btn.querySelector(".btn-label");
    if (isLoading) {
      btn.dataset.originalHtml = btn.innerHTML;
      btn.innerHTML = `<span class="btn-spin"></span><span class="btn-label">${label}</span>`;
    } else if (btn.dataset.originalHtml) {
      btn.innerHTML = btn.dataset.originalHtml;
      if (labelEl) labelEl.textContent = label;
    } else if (labelEl) {
      labelEl.textContent = label;
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validateForm()) {
      UI.toast("Please fix the highlighted fields before submitting.", "warning");
      return;
    }

    const payload = buildPayload();
    setBtnLoading(els.submitFormBtn, true, state.editingId ? "Saving..." : "Creating...");

    try {
      if (state.editingId) {
        const updated = await API.updateMock(state.editingId, payload);
        UI.toast(`"${updated.name}" updated successfully.`, "success");
        await loadMocks();
        switchView("myapis");
      } else {
        const created = await API.createMock(payload);
        await loadMocks();
        showSuccessModal(created);
        startCreateFlow();
      }
    } catch (err) {
      UI.toast(err.message || "Something went wrong. Please try again.", "error", 6000);
    } finally {
      setBtnLoading(els.submitFormBtn, false, state.editingId ? "Save Changes" : "Create Mock");
    }
  }

  function showSuccessModal(created) {
    // MockAPIResponse.endpoint_url is already a fully-qualified URL
    // (built server-side from the service's own BASE_URL), so it is
    // used as-is rather than prefixed again with the dashboard's base URL.
    const fullUrl = created.endpoint_url;
    els.successSubText.textContent = created.message || "Your endpoint has been created and is ready to receive requests.";
    els.successEndpointUrl.value = fullUrl;
    els.successMethodBadge.textContent = created.method;
    els.successMethodBadge.className = `badge badge-method m-${created.method}`;
    els.successStatusBadge.textContent = created.status_code;
    els.successStatusBadge.className = `badge badge-status ${UI.statusClass(created.status_code)}`;
    UI.openModal("modalSuccess");
  }
})();