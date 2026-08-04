/* ============================================================
   ACTION ITEM EXTRACTOR — App Logic
   Organized into small, single-purpose functions.
   ============================================================ */

/* ------------------------------------------------------------
   CONFIG
   Auth is handled via an httpOnly cookie set by the backend
   (nothing is read from or written to localStorage). We simply
   send `credentials: "include"` so the cookie rides along.
   ------------------------------------------------------------ */
const CONFIG = {
  API_BASE_URL: "",                       // e.g. "https://api.yourapp.com"
  ENDPOINT: "/item-extractor/extract",
  MAX_FILE_SIZE: 25 * 1024 * 1024,        // 25MB, mirrors backend limit
  ALLOWED_EXTENSIONS: [".pdf", ".docx", ".txt"],
  PROGRESS_STEP_DURATION: 650,            // ms between simulated progress steps
};

/* ------------------------------------------------------------
   STATE
   ------------------------------------------------------------ */
const state = {
  mode: "text",                 // "text" | "file"
  selectedFile: null,           // File object currently staged
  actionItems: [],              // last successful response
  filteredItems: [],            // after search/sort applied
  allCollapsed: false,
  isSubmitting: false,
  progressTimer: null,
  currentExecutionId: null,
};

/* ------------------------------------------------------------
   DOM REFS
   ------------------------------------------------------------ */
const el = {};

function cacheDom() {
  el.themeToggle = document.getElementById("themeToggle");
  el.mouseGlow = document.getElementById("mouseGlow");

  el.tabTextBtn = document.getElementById("tabTextBtn");
  el.tabFileBtn = document.getElementById("tabFileBtn");
  el.segmentedIndicator = document.getElementById("segmentedIndicator");
  el.textPane = document.getElementById("textPane");
  el.filePane = document.getElementById("filePane");

  el.textInput = document.getElementById("textInput");
  el.charCounter = document.getElementById("charCounter");

  el.dropzone = document.getElementById("dropzone");
  el.fileInput = document.getElementById("fileInput");
  el.dropzoneIdle = document.getElementById("dropzoneIdle");
  el.dropzoneFile = document.getElementById("dropzoneFile");
  el.fileIcon = document.getElementById("fileIcon");
  el.fileName = document.getElementById("fileName");
  el.fileSize = document.getElementById("fileSize");
  el.fileRemoveBtn = document.getElementById("fileRemoveBtn");
  el.fileSuccessRing = document.getElementById("fileSuccessRing");

  el.validationMsg = document.getElementById("validationMsg");
  el.submitBtn = document.getElementById("submitBtn");

  el.stateEmpty = document.getElementById("stateEmpty");
  el.stateLoading = document.getElementById("stateLoading");
  el.stateError = document.getElementById("stateError");
  el.stateResults = document.getElementById("stateResults");
  el.progressSteps = document.getElementById("progressSteps");
  el.errorMessage = document.getElementById("errorMessage");
  el.retryBtn = document.getElementById("retryBtn");

  el.resultsCount = document.getElementById("resultsCount");
  el.resultsList = document.getElementById("resultsList");
  el.noMatchMsg = document.getElementById("noMatchMsg");
  el.searchInput = document.getElementById("searchInput");
  el.sortSelect = document.getElementById("sortSelect");
  el.collapseAllBtn = document.getElementById("collapseAllBtn");
  el.copyAllBtn = document.getElementById("copyAllBtn");
  el.downloadJsonBtn = document.getElementById("downloadJsonBtn");
  el.clearResultsBtn = document.getElementById("clearResultsBtn");
  el.bookmarkBtn = document.getElementById("bookmarkBtn");

  el.toastContainer = document.getElementById("toastContainer");
}

/* ============================================================
   INITIALIZATION
   ============================================================ */
function initializeUI() {
  cacheDom();
  bindThemeToggle();
  bindMouseGlow();
  bindInputModeToggle();
  bindTextInput();
  bindDropzone();
  bindSubmit();
  bindResultsToolbar();
  bindRetry();
  renderEmptyState();
}

document.addEventListener("DOMContentLoaded", initializeUI);

/* ============================================================
   THEME
   ============================================================ */
function bindThemeToggle() {
  el.themeToggle.addEventListener("click", () => {
    const html = document.documentElement;
    const isLight = html.getAttribute("data-theme") === "light";
    html.setAttribute("data-theme", isLight ? "dark" : "light");
    el.themeToggle.querySelector(".icon-moon").hidden = !isLight;
    el.themeToggle.querySelector(".icon-sun").hidden = isLight;
  });
}

function bindMouseGlow() {
  window.addEventListener("pointermove", (e) => {
    el.mouseGlow.style.opacity = "1";
    el.mouseGlow.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
  });
  window.addEventListener("pointerleave", () => { el.mouseGlow.style.opacity = "0"; });
}

/* ============================================================
   INPUT MODE (Text / File)
   ============================================================ */
function bindInputModeToggle() {
  el.tabTextBtn.addEventListener("click", () => toggleInputMode("text"));
  el.tabFileBtn.addEventListener("click", () => toggleInputMode("file"));
}

function toggleInputMode(mode) {
  if (state.mode === mode) return;
  state.mode = mode;

  const isText = mode === "text";
  el.tabTextBtn.classList.toggle("active", isText);
  el.tabFileBtn.classList.toggle("active", !isText);
  el.tabTextBtn.setAttribute("aria-selected", String(isText));
  el.tabFileBtn.setAttribute("aria-selected", String(!isText));
  el.segmentedIndicator.classList.toggle("pos-1", !isText);

  el.textPane.hidden = !isText;
  el.filePane.hidden = isText;

  clearValidation();
}

/* ============================================================
   TEXT MODE
   ============================================================ */
function bindTextInput() {
  el.textInput.addEventListener("input", () => {
    autoExpandTextarea(el.textInput);
    updateCharCounter();
    clearValidation();
  });
}

function autoExpandTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 420)}px`;
}

function updateCharCounter() {
  const count = el.textInput.value.length;
  el.charCounter.textContent = `${count.toLocaleString()} character${count === 1 ? "" : "s"}`;
  el.charCounter.classList.toggle("warn", count > 8000);
}

/* ============================================================
   FILE MODE
   ============================================================ */
function bindDropzone() {
  el.dropzone.addEventListener("click", (e) => {
    if (state.selectedFile) return; // clicking the file preview shouldn't reopen picker
    el.fileInput.click();
  });

  el.dropzone.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && !state.selectedFile) {
      e.preventDefault();
      el.fileInput.click();
    }
  });

  el.fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) handleFileSelection(e.target.files[0]);
  });

  ["dragenter", "dragover"].forEach((evt) => {
    el.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      el.dropzone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    el.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      el.dropzone.classList.remove("drag-over");
    });
  });

  el.dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) handleFileSelection(file);
  });

  el.fileRemoveBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });
}

function handleFileSelection(file) {
  clearValidation();

  const ext = getFileExtension(file.name);
  if (!CONFIG.ALLOWED_EXTENSIONS.includes(ext)) {
    showValidation(`Unsupported file type "${ext}". Supported types: .pdf, .docx, .txt`);
    el.dropzone.classList.add("has-error");
    return;
  }

  if (file.size > CONFIG.MAX_FILE_SIZE) {
    showValidation("File exceeds the 25MB size limit.");
    el.dropzone.classList.add("has-error");
    return;
  }

  el.dropzone.classList.remove("has-error");
  state.selectedFile = file;

  el.fileName.textContent = file.name;
  el.fileSize.textContent = formatFileSize(file.size);
  el.dropzoneIdle.hidden = true;
  el.dropzoneFile.hidden = false;

  // Success flash animation
  el.fileSuccessRing.classList.remove("flash");
  void el.fileSuccessRing.offsetWidth; // restart animation
  el.fileSuccessRing.classList.add("flash");
}

function clearSelectedFile() {
  state.selectedFile = null;
  el.fileInput.value = "";
  el.dropzoneIdle.hidden = false;
  el.dropzoneFile.hidden = true;
  el.dropzone.classList.remove("has-error");
  clearValidation();
}

function getFileExtension(filename) {
  const idx = filename.lastIndexOf(".");
  return idx === -1 ? "" : filename.slice(idx).toLowerCase();
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* ============================================================
   VALIDATION
   ============================================================ */
function validateForm() {
  const hasText = state.mode === "text" && el.textInput.value.trim().length > 0;
  const hasFile = state.mode === "file" && state.selectedFile !== null;

  if (state.mode === "text" && !hasText) {
    showValidation("Please paste some text before extracting.");
    return false;
  }
  if (state.mode === "file" && !hasFile) {
    showValidation("Please select a file before extracting.");
    return false;
  }
  return true;
}

function showValidation(message) {
  el.validationMsg.textContent = message;
  el.validationMsg.hidden = false;
}

function clearValidation() {
  el.validationMsg.hidden = true;
  el.validationMsg.textContent = "";
}

/* ============================================================
   FILE PATH RESOLUTION (DEMO PLACEHOLDER)
   ------------------------------------------------------------
   The backend's request model only accepts a server-side
   `file_path`, so a real deployment needs an upload endpoint
   that stores the file and returns its path. That endpoint
   doesn't exist yet, so this function simulates it. Swap the
   body of this function out for a real upload call — the rest
   of the app doesn't need to change.
   ============================================================ */
async function resolveFilePath(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${CONFIG.API_BASE_URL}/item-extractor/upload`, {
    method: "POST",
    credentials: "include",
    body: formData,
    // Do NOT set Content-Type — browser sets it with the correct boundary
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed with status ${res.status}`);
  }

  const { file_path } = await res.json();
  return file_path;
}

/* ============================================================
   SUBMIT / API CALL
   ============================================================ */
function bindSubmit() {
  el.submitBtn.addEventListener("click", submitRequest);
}

function bindRetry() {
  el.retryBtn.addEventListener("click", submitRequest);
}

async function submitRequest() {
  if (state.isSubmitting) return;
  if (!validateForm()) return;

  state.isSubmitting = true;
  setSubmitButtonState("loading");
  showLoader();

  try {
    const payload = await buildPayload();
    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINT}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include", // auth cookie travels automatically; no localStorage involved
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errBody = await safeParseJson(response);
      throw new Error(errBody?.detail || `Request failed with status ${response.status}`);
    }

    const data = await response.json();
    hideLoader();
    setSubmitButtonState("success");
    state.actionItems = Array.isArray(data.action_items) ? data.action_items : [];
    renderResults(state.actionItems);
    state.currentExecutionId = data.execution_id || null;
    if (state.currentExecutionId) {
      el.bookmarkBtn.hidden = false;
      el.bookmarkBtn.classList.remove('is-bookmarked');
      el.bookmarkBtn.title = 'Bookmark results';
      el.bookmarkBtn.disabled = false;
    } else {
      el.bookmarkBtn.hidden = true;
    }
  } catch (err) {
    hideLoader();
    setSubmitButtonState("error");
    renderError(err.message || "Something went wrong while extracting action items.");
    showToast(err.message || "Extraction failed.", "error");
  } finally {
    state.isSubmitting = false;
    setTimeout(() => setSubmitButtonState("idle"), 1800);
  }
}

async function buildPayload() {
  if (state.mode === "text") {
    return { text: el.textInput.value.trim(), file_path: null };
  }
  const filePath = await resolveFilePath(state.selectedFile);
  return { text: null, file_path: filePath };
}

async function safeParseJson(response) {
  try { return await response.json(); } catch { return null; }
}

function setSubmitButtonState(mode) {
  const contents = {
    idle: el.submitBtn.querySelector(".submit-idle"),
    loading: el.submitBtn.querySelector(".submit-loading"),
    success: el.submitBtn.querySelector(".submit-success"),
    error: el.submitBtn.querySelector(".submit-error"),
  };
  Object.values(contents).forEach((node) => { node.hidden = true; });
  contents[mode].hidden = false;

  el.submitBtn.classList.remove("state-success", "state-error");
  el.submitBtn.disabled = mode === "loading";
  if (mode === "success") el.submitBtn.classList.add("state-success");
  if (mode === "error") el.submitBtn.classList.add("state-error");
}

/* ============================================================
   LOADER / PROGRESS STEPS
   ============================================================ */
function showLoader() {
  setActiveState("loading");
  const steps = Array.from(el.progressSteps.querySelectorAll("li"));
  steps.forEach((step) => step.classList.remove("active", "done"));

  let current = 0;
  steps[0]?.classList.add("active");

  clearInterval(state.progressTimer);
  state.progressTimer = setInterval(() => {
    if (current >= steps.length) {
      clearInterval(state.progressTimer);
      return;
    }
    steps[current].classList.remove("active");
    steps[current].classList.add("done");
    current += 1;
    if (steps[current]) steps[current].classList.add("active");
    else clearInterval(state.progressTimer);
  }, CONFIG.PROGRESS_STEP_DURATION);
}

function hideLoader() {
  clearInterval(state.progressTimer);
  const steps = Array.from(el.progressSteps.querySelectorAll("li"));
  steps.forEach((step) => { step.classList.remove("active"); step.classList.add("done"); });
}

/* ============================================================
   STATE VIEW SWITCHING
   ============================================================ */
function setActiveState(target) {
  el.stateEmpty.hidden = target !== "empty";
  el.stateLoading.hidden = target !== "loading";
  el.stateError.hidden = target !== "error";
  el.stateResults.hidden = target !== "results";
}

function renderEmptyState() {
  setActiveState("empty");
}

function renderError(message) {
  el.errorMessage.textContent = message || "Something went wrong while extracting action items.";
  setActiveState("error");
}

/* ============================================================
   RESULTS RENDERING
   ============================================================ */
function renderResults(items) {
  if (!items || items.length === 0) {
    setActiveState("empty");
    el.stateEmpty.querySelector(".state-title").textContent = "No action items found";
    el.stateEmpty.querySelector(".state-desc").textContent =
      "The AI couldn't find any actionable tasks in what you provided. Try adding more detail.";
    return;
  }

  setActiveState("results");
  el.resultsCount.textContent = `${items.length} item${items.length === 1 ? "" : "s"}`;
  el.searchInput.value = "";
  el.sortSelect.value = "default";
  state.allCollapsed = false;
  applyFilterAndSort();
}

function applyFilterAndSort() {
  const query = el.searchInput.value.trim().toLowerCase();
  const sortBy = el.sortSelect.value;

  let items = state.actionItems.filter((item) => {
    if (!query) return true;
    const haystack = `${item.task || ""} ${item.assignee || ""} ${item.deadline || ""}`.toLowerCase();
    return haystack.includes(query);
  });

  items = sortItems(items, sortBy);
  state.filteredItems = items;

  el.noMatchMsg.hidden = items.length !== 0;
  paintTaskCards(items);
}

function sortItems(items, sortBy) {
  const copy = [...items];
  const collator = new Intl.Collator("en", { sensitivity: "base" });

  if (sortBy === "task") {
    copy.sort((a, b) => collator.compare(a.task || "", b.task || ""));
  } else if (sortBy === "assignee") {
    copy.sort((a, b) => collator.compare(a.assignee || "\uffff", b.assignee || "\uffff"));
  } else if (sortBy === "deadline") {
    copy.sort((a, b) => collator.compare(a.deadline || "\uffff", b.deadline || "\uffff"));
  }
  return copy;
}

function paintTaskCards(items) {
  el.resultsList.innerHTML = "";
  const fragment = document.createDocumentFragment();

  items.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "task-card";
    card.style.animationDelay = `${Math.min(index * 60, 600)}ms`;

    const assignee = item.assignee && item.assignee.trim() ? item.assignee : null;
    const deadline = item.deadline && item.deadline.trim() ? item.deadline : null;

    card.innerHTML = `
      <div class="task-card-header">
        <span class="task-card-index">${index + 1}</span>
        <span class="task-card-task">${escapeHtml(item.task || "Untitled task")}</span>
        <span class="task-card-chevron">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
        </span>
      </div>
      <div class="task-card-body">
        <span class="badge-chip badge-assignee ${assignee ? "" : "unassigned"}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.2"/><path d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6"/></svg>
          ${escapeHtml(assignee || "Unassigned")}
        </span>
        <span class="badge-chip badge-deadline ${deadline ? "" : "none"}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="4.5" width="17" height="16" rx="2.5"/><path d="M8 2.5v4M16 2.5v4M3.5 9.5h17"/></svg>
          ${escapeHtml(deadline || "No Deadline")}
        </span>
      </div>
    `;

    card.querySelector(".task-card-header").addEventListener("click", () => {
      card.classList.toggle("collapsed");
    });

    fragment.appendChild(card);
  });

  el.resultsList.appendChild(fragment);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ============================================================
   RESULTS TOOLBAR (search, sort, copy, export, clear, collapse)
   ============================================================ */
function bindResultsToolbar() {
  el.searchInput.addEventListener("input", applyFilterAndSort);
  el.sortSelect.addEventListener("change", applyFilterAndSort);
  el.collapseAllBtn.addEventListener("click", toggleAllCards);
  el.copyAllBtn.addEventListener("click", copyResults);
  el.downloadJsonBtn.addEventListener("click", downloadJSON);
  el.clearResultsBtn.addEventListener("click", clearResults);
  el.bookmarkBtn.addEventListener("click", async () => {
    if (!state.currentExecutionId || el.bookmarkBtn.disabled) return;
    el.bookmarkBtn.disabled = true;
    try {
      const res = await fetch("/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ execution_id: state.currentExecutionId }),
      });
      if (res.status === 401) {
        showToast("Please sign in to bookmark.", "error");
        el.bookmarkBtn.disabled = false;
        return;
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to bookmark");
      }
      el.bookmarkBtn.classList.add("is-bookmarked");
      el.bookmarkBtn.title = "Bookmarked";
      showToast("Result bookmarked.", "success");
    } catch (err) {
      el.bookmarkBtn.disabled = false;
      showToast(err.message || "Could not bookmark.", "error");
    }
  });
}

function toggleAllCards() {
  state.allCollapsed = !state.allCollapsed;
  document.querySelectorAll(".task-card").forEach((card) => {
    card.classList.toggle("collapsed", state.allCollapsed);
  });
}

function copyResults() {
  const text = state.filteredItems
    .map((item, i) => {
      const assignee = item.assignee || "Unassigned";
      const deadline = item.deadline || "No Deadline";
      return `${i + 1}. ${item.task}  [Assignee: ${assignee} | Deadline: ${deadline}]`;
    })
    .join("\n");

  navigator.clipboard
    .writeText(text)
    .then(() => {
      flashSuccess(el.copyAllBtn);
      showToast("Tasks copied to clipboard.", "success");
    })
    .catch(() => showToast("Couldn't copy tasks to clipboard.", "error"));
}

function downloadJSON() {
  const payload = { action_items: state.actionItems, total_action_items: state.actionItems.length };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "action-items.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  flashSuccess(el.downloadJsonBtn);
  showToast("JSON file downloaded.", "success");
}

function clearResults() {
  state.actionItems = [];
  state.filteredItems = [];
  state.currentExecutionId = null;        
  el.bookmarkBtn.hidden = true;           
  el.bookmarkBtn.classList.remove('is-bookmarked');
  el.resultsList.innerHTML = "";
  el.searchInput.value = "";
  el.sortSelect.value = "default";
  el.stateEmpty.querySelector(".state-title").textContent = "No action items yet";
  el.stateEmpty.querySelector(".state-desc").textContent =
    "Paste your notes or upload a document, then extract to see structured tasks appear here.";
  renderEmptyState();
  showToast("Results cleared.", "info");
}

function flashSuccess(button) {
  button.classList.add("success-flash");
  setTimeout(() => button.classList.remove("success-flash"), 1200);
}

/* ============================================================
   TOASTS
   ============================================================ */
function showToast(message, type = "info") {
  const icons = {
    success: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
    error: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01"/><circle cx="12" cy="12" r="9"/></svg>',
    info: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16v-4M12 8h.01"/><circle cx="12" cy="12" r="9"/></svg>',
  };

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `${icons[type] || icons.info}<span>${escapeHtml(message)}</span>`;
  el.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("removing");
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}