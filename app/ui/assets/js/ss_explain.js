/**
 * ============================================================
 * SCREENSHOT EXPLAINER — script.js
 * Vanilla JS. No dependencies.
 * Sections:
 *   1. Config & State
 *   2. DOM References
 *   3. Toast System
 *   4. Utilities
 *   5. Upload / Drag & Drop / Preview
 *   6. Custom Dropdown (Action Select)
 *   7. Custom Action Textarea + Word Counter
 *   8. Explain Button State + Ripple
 *   9. Loading State (rotating messages + progress)
 *   10. API Call
 *   11. Result Rendering + Copy / Download / Clear
 *   12. Init
 * ============================================================
 */

(() => {
  "use strict";

  /* ============================================================
     1. CONFIG & STATE
     ============================================================ */
  const API_ENDPOINT = "/screenshot-explainer/explain";

  const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
  const ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
  const ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"];
  const MAX_CUSTOM_ACTION_WORDS = 200;

  const LOADING_MESSAGES = [
    "Analyzing screenshot...",
    "Detecting important elements...",
    "Understanding interface...",
    "Reading visible text...",
    "Generating explanation...",
  ];

  const state = {
    selectedFile: null,
    selectedAction: "general_explanation",
    isSubmitting: false,
    loadingMessageTimer: null,
    loadingProgressTimer: null,
    lastExplanation: { title: "", explanation: "" },
  };

  /* ============================================================
     2. DOM REFERENCES
     ============================================================ */
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropzoneEmpty = document.getElementById("dropzoneEmpty");
  const dropzonePreview = document.getElementById("dropzonePreview");
  const previewImg = document.getElementById("previewImg");
  const fileNameEl = document.getElementById("fileName");
  const fileSizeEl = document.getElementById("fileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const scanBeam = document.querySelector(".scan-beam");

  const actionSelect = document.getElementById("actionSelect");
  const actionTrigger = document.getElementById("actionTrigger");
  const actionMenu = document.getElementById("actionMenu");
  const selectedIcon = document.getElementById("selectedIcon");
  const selectedValue = document.getElementById("selectedValue");

  const customActionWrap = document.getElementById("customActionWrap");
  const customActionInput = document.getElementById("customActionInput");
  const wordCounter = document.getElementById("wordCounter");

  const explainBtn = document.getElementById("explainBtn");

  const loadingCard = document.getElementById("loadingCard");
  const loadingMessageEl = document.getElementById("loadingMessage");
  const progressFill = document.getElementById("progressFill");

  const resultCard = document.getElementById("resultCard");
  const resultTitle = document.getElementById("resultTitle");
  const resultBody = document.getElementById("resultBody");
  const copyBtn = document.getElementById("copyBtn");
  const downloadBtn = document.getElementById("downloadBtn");
  const clearBtn = document.getElementById("clearBtn");

  const toastContainer = document.getElementById("toastContainer");

  /* ============================================================
     3. TOAST SYSTEM
     ============================================================ */
  const TOAST_ICONS = {
    error: `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/><path d="M12 8v5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>`,
    success: `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/><path d="m8 12.5 2.5 2.5L16 9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    warning: `<svg viewBox="0 0 24 24" fill="none"><path d="M12 3.5 21 19.5H3L12 3.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 10v4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="16.5" r="1" fill="currentColor"/></svg>`,
  };

  function showToast(type, title, description = "", duration = 4200) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${TOAST_ICONS[type] || TOAST_ICONS.warning}</span>
      <div class="toast-text">
        <div class="toast-title">${escapeHtml(title)}</div>
        ${description ? `<div class="toast-desc">${escapeHtml(description)}</div>` : ""}
      </div>
    `;
    toastContainer.appendChild(toast);

    const remove = () => {
      toast.classList.add("toast-out");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    };

    const timer = setTimeout(remove, duration);
    toast.addEventListener("click", () => {
      clearTimeout(timer);
      remove();
    });
  }

  /* ============================================================
     4. UTILITIES
     ============================================================ */
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 KB";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
    const value = bytes / Math.pow(1024, i);
    return `${i === 0 ? value : value.toFixed(1)} ${units[i]}`;
  }

  function countWords(text) {
    const trimmed = text.trim();
    if (!trimmed) return 0;
    return trimmed.split(/\s+/).length;
  }

  function getFileExtension(filename) {
    const idx = filename.lastIndexOf(".");
    return idx === -1 ? "" : filename.slice(idx).toLowerCase();
  }

  /* ============================================================
     5. UPLOAD / DRAG & DROP / PREVIEW
     ============================================================ */
  function validateFile(file) {
    if (!file) {
      showToast("error", "No image uploaded", "Please choose a screenshot to continue.");
      return false;
    }

    const extOk = ALLOWED_EXTENSIONS.includes(getFileExtension(file.name));
    const mimeOk = ALLOWED_MIME_TYPES.includes(file.type);

    if (!extOk || !mimeOk) {
      showToast(
        "error",
        "Invalid file type",
        "Please upload a PNG, JPG, JPEG, or WEBP image."
      );
      return false;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      showToast(
        "error",
        "Image too large",
        "Please upload an image smaller than 50 MB."
      );
      return false;
    }

    return true;
  }

  function setSelectedFile(file) {
    if (!validateFile(file)) return;

    state.selectedFile = file;

    const objectUrl = URL.createObjectURL(file);
    previewImg.src = objectUrl;
    previewImg.onload = () => URL.revokeObjectURL(objectUrl);

    fileNameEl.textContent = file.name;
    fileNameEl.title = file.name;
    fileSizeEl.textContent = formatBytes(file.size);

    dropzoneEmpty.hidden = true;
    dropzonePreview.hidden = false;
    dropzonePreview.classList.add("animate-scale-in");

    updateExplainButtonState();
  }

  function clearSelectedFile() {
    state.selectedFile = null;
    fileInput.value = "";
    previewImg.src = "";
    dropzonePreview.hidden = true;
    dropzoneEmpty.hidden = false;
    updateExplainButtonState();
  }

  browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener("click", (e) => {
    // Avoid double-trigger when clicking the remove button or browse button (they stop propagation)
    if (dropzonePreview.hidden) fileInput.click();
  });

  dropzone.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && dropzonePreview.hidden) {
      e.preventDefault();
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files && fileInput.files[0];
    if (file) setSelectedFile(file);
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("drag-active");
    });
  });

  ["dragleave", "dragend"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("drag-active");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("drag-active");

    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  });

  /* ============================================================
     6. CUSTOM DROPDOWN (ACTION SELECT)
     ============================================================ */
  const menuItems = Array.from(actionMenu.querySelectorAll("li"));

  function openMenu() {
  actionMenu.hidden = false;
  actionSelect.classList.add("open");
  actionSelect.setAttribute("aria-expanded", "true");

  // Blur everything except the dropdown panel's select widget
  document.querySelectorAll(
    ".upload-panel, .explain-section, #customActionWrap, #loadingCard, #resultCard, .app-header, .app-footer"
  ).forEach(el => el.classList.add("dropdown-blurred"));
}

function closeMenu() {
  actionMenu.hidden = true;
  actionSelect.classList.remove("open");
  actionSelect.setAttribute("aria-expanded", "false");

  document.querySelectorAll(
    ".upload-panel, .explain-section, #customActionWrap, #loadingCard, #resultCard, .app-header, .app-footer"
  ).forEach(el => el.classList.remove("dropdown-blurred"));
}

  function toggleMenu() {
    if (actionMenu.hidden) openMenu();
    else closeMenu();
  }

  function selectAction(item) {
    const value = item.dataset.value;
    const icon = item.dataset.icon;
    const label = item.querySelector("span:last-child").textContent;

    state.selectedAction = value;
    selectedIcon.textContent = icon;
    selectedValue.textContent = label;

    menuItems.forEach((li) => {
      li.classList.toggle("active", li === item);
      li.setAttribute("aria-selected", li === item ? "true" : "false");
    });

    toggleCustomActionVisibility(value === "other");
    closeMenu();
    updateExplainButtonState();
  }

  actionTrigger.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleMenu();
  });

  menuItems.forEach((item) => {
    item.addEventListener("click", () => selectAction(item));
  });

  actionSelect.addEventListener("keydown", (e) => {
    const openNow = !actionMenu.hidden;

    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleMenu();
    } else if (e.key === "Escape" && openNow) {
      closeMenu();
    } else if ((e.key === "ArrowDown" || e.key === "ArrowUp") && openNow) {
      e.preventDefault();
      const currentIndex = menuItems.findIndex((li) => li.classList.contains("hovered"));
      let nextIndex;
      if (currentIndex === -1) {
        nextIndex = 0;
      } else {
        nextIndex = e.key === "ArrowDown"
          ? Math.min(menuItems.length - 1, currentIndex + 1)
          : Math.max(0, currentIndex - 1);
      }
      menuItems.forEach((li, i) => li.classList.toggle("hovered", i === nextIndex));
      menuItems[nextIndex].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && openNow) {
      const hovered = menuItems.find((li) => li.classList.contains("hovered"));
      if (hovered) selectAction(hovered);
    }
  });

  document.addEventListener("click", (e) => {
    if (!actionSelect.contains(e.target)) closeMenu();
  });

  /* ============================================================
     7. CUSTOM ACTION TEXTAREA + WORD COUNTER
     ============================================================ */
  function toggleCustomActionVisibility(show) {
    customActionWrap.hidden = !show;
    if (!show) {
      customActionInput.value = "";
      updateWordCounter();
    }
  }

  function autoResizeTextarea() {
    customActionInput.style.height = "auto";
    customActionInput.style.height = `${Math.min(260, customActionInput.scrollHeight)}px`;
  }

  function updateWordCounter() {
    const words = countWords(customActionInput.value);
    wordCounter.textContent = `${words} / ${MAX_CUSTOM_ACTION_WORDS} words`;

    wordCounter.classList.remove("limit-warn", "limit-exceeded");
    customActionInput.classList.remove("input-error");

    if (words > MAX_CUSTOM_ACTION_WORDS) {
      wordCounter.classList.add("limit-exceeded");
      customActionInput.classList.add("input-error");
    } else if (words > MAX_CUSTOM_ACTION_WORDS * 0.9) {
      wordCounter.classList.add("limit-warn");
    }

    updateExplainButtonState();
  }

  customActionInput.addEventListener("input", () => {
    autoResizeTextarea();
    updateWordCounter();
  });

  /* ============================================================
     8. EXPLAIN BUTTON STATE + RIPPLE
     ============================================================ */
  function updateExplainButtonState() {
    if (state.isSubmitting) {
      explainBtn.disabled = true;
      return;
    }

    const hasFile = Boolean(state.selectedFile);

    let customActionValid = true;
    if (state.selectedAction === "other") {
      const words = countWords(customActionInput.value);
      customActionValid = words > 0 && words <= MAX_CUSTOM_ACTION_WORDS;
    }

    explainBtn.disabled = !(hasFile && customActionValid);
  }

  explainBtn.addEventListener("click", (e) => {
    createRipple(e);
    handleExplainSubmit();
  });

  function createRipple(e) {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
    btn.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove());
  }

  /* ============================================================
     9. LOADING STATE (rotating messages + progress)
     ============================================================ */
  function startLoadingState() {
    loadingCard.hidden = false;
    loadingCard.classList.add("animate-fade-in-up");
    resultCard.hidden = true;

    if (scanBeam) scanBeam.classList.add("scanning");

    let msgIndex = 0;
    loadingMessageEl.textContent = LOADING_MESSAGES[0];

    state.loadingMessageTimer = setInterval(() => {
      msgIndex = (msgIndex + 1) % LOADING_MESSAGES.length;
      loadingMessageEl.style.opacity = "0";
      setTimeout(() => {
        loadingMessageEl.textContent = LOADING_MESSAGES[msgIndex];
        loadingMessageEl.style.opacity = "1";
      }, 180);
    }, 1900);

    // Simulated progress creep — never reaches 100% until real completion
    let progress = 6;
    progressFill.style.width = `${progress}%`;
    state.loadingProgressTimer = setInterval(() => {
      progress += (90 - progress) * 0.12;
      progressFill.style.width = `${Math.min(progress, 92)}%`;
    }, 500);

    loadingMessageEl.style.transition = "opacity 180ms ease";
  }

  function stopLoadingState(success) {
    clearInterval(state.loadingMessageTimer);
    clearInterval(state.loadingProgressTimer);
    state.loadingMessageTimer = null;
    state.loadingProgressTimer = null;

    if (scanBeam) scanBeam.classList.remove("scanning");

    if (success) {
      progressFill.style.width = "100%";
      setTimeout(() => {
        loadingCard.hidden = true;
        progressFill.style.width = "6%";
      }, 350);
    } else {
      loadingCard.hidden = true;
      progressFill.style.width = "6%";
    }
  }

  /* ============================================================
     10. API CALL
     ============================================================ */
  function setSubmittingState(isSubmitting) {
    state.isSubmitting = isSubmitting;
    explainBtn.classList.toggle("is-loading", isSubmitting);
    explainBtn.querySelector(".explain-btn-spinner").hidden = !isSubmitting;
    updateExplainButtonState();
  }

  async function handleExplainSubmit() {
    if (state.isSubmitting) return;

    if (!state.selectedFile) {
      showToast("error", "No image uploaded", "Please upload a screenshot before continuing.");
      return;
    }

    if (state.selectedAction === "other") {
      const words = countWords(customActionInput.value);
      if (words === 0) {
        showToast("error", "Custom instruction required", "Tell the AI what you'd like explained.");
        return;
      }
      if (words > MAX_CUSTOM_ACTION_WORDS) {
        showToast(
          "error",
          "Custom action too long",
          `Please keep your instruction under ${MAX_CUSTOM_ACTION_WORDS} words.`
        );
        return;
      }
    }

    const formData = new FormData();
    formData.append("image", state.selectedFile);
    formData.append("action", state.selectedAction);
    if (state.selectedAction === "other") {
      formData.append("custom_action", customActionInput.value.trim());
    }

    setSubmittingState(true);
    startLoadingState();

    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        let detail = "Something went wrong while explaining the screenshot.";
        try {
          const errBody = await response.json();
          if (errBody && errBody.detail) detail = errBody.detail;
        } catch (_) {
          /* response wasn't JSON — keep default message */
        }

        if (response.status >= 500) {
          throw new ApiError("Backend unavailable", detail);
        }
        throw new ApiError("Request failed", detail);
      }

      const data = await response.json();

      if (!data || typeof data.explanation !== "string") {
        throw new ApiError("Request failed", "The server returned an unexpected response.");
      }

      stopLoadingState(true);
      setTimeout(() => renderResult(data), 380);
    } catch (err) {
      stopLoadingState(false);

      if (err instanceof ApiError) {
        showToast("error", err.title, err.message);
      } else if (err instanceof TypeError) {
        // fetch network failure
        showToast("error", "Backend unavailable", "Could not reach the server. Please try again.");
      } else {
        showToast("error", "Request failed", "An unexpected error occurred. Please try again.");
      }
    } finally {
      setSubmittingState(false);
    }
  }

  class ApiError extends Error {
    constructor(title, message) {
      super(message);
      this.title = title;
      this.message = message;
    }
  }

  /* ============================================================
     11. RESULT RENDERING + COPY / DOWNLOAD / CLEAR
     ============================================================ */

  function restoreMath(str, tokens) {
    return str.replace(/%%MATH(\d+)%%/g, (_, i) => tokens[parseInt(i)]);
    }
  function renderResult(data) {
    state.lastExplanation = {
        title: data.title || "Screenshot Explanation",
        explanation: data.explanation || "",
    };

    resultTitle.textContent = state.lastExplanation.title;
    resultBody.innerHTML = markdownToHtml(state.lastExplanation.explanation);

    resultCard.hidden = false;
    resultCard.classList.remove("animate-fade-in-up");
    void resultCard.offsetWidth;
    resultCard.classList.add("animate-fade-in-up");

    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise([resultBody]).catch(console.error);
    }
    }

    function markdownToHtml(text) {
    const lines = text.split("\n");
    const html = [];
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];


            // Extract math BEFORE escaping so delimiters aren't corrupted
            const mathTokens = [];
            line = line.replace(/\$\$(.+?)\$\$/g, (_, m) => {
                const idx = mathTokens.length;
                mathTokens.push(`<span class="math-block">\\[${m}\\]</span>`);
                return `%%MATH${idx}%%`;
            });
            line = line.replace(/\$(.+?)\$/g, (_, m) => {
                const idx = mathTokens.length;
                mathTokens.push(`<span class="math-inline">\\(${m}\\)</span>`);
                return `%%MATH${idx}%%`;
            });

            // NOW escape HTML entities
            line = line
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");

        // Headings
        if (/^#### (.+)/.test(line)) {
            if (inList) { html.push("</ul>"); inList = false; }
            html.push(restoreMath(`<h3>${inlineFormat(line.replace(/^#### /, ""))}</h3>`, mathTokens));
            continue;
        }
        if (/^### (.+)/.test(line)) {
        if (inList) { html.push("</ul>"); inList = false; }
        html.push(restoreMath(`<h3>${inlineFormat(line.replace(/^### /, ""))}</h3>`, mathTokens));
        continue;
        }
        if (/^## (.+)/.test(line)) {
        if (inList) { html.push("</ul>"); inList = false; }
        html.push(restoreMath(`<h2>${inlineFormat(line.replace(/^## /, ""))}</h2>`, mathTokens));
        continue;
        }
        if (/^# (.+)/.test(line)) {
        if (inList) { html.push("</ul>"); inList = false; }
        html.push(restoreMath(`<h1>${inlineFormat(line.replace(/^# /, ""))}</h1>`, mathTokens));
        continue;
        }

        // Horizontal rule
        if (/^---+$/.test(line.trim())) {
        if (inList) { html.push("</ul>"); inList = false; }
        html.push("<hr />");
        continue;
        }

        // Bullet list items (-, *, •)
        if (/^[\s]*[-*•] (.+)/.test(line)) {
        if (!inList) { html.push("<ul>"); inList = true; }
        const content = line.replace(/^[\s]*[-*•] /, "");
        html.push(restoreMath(`<li>${inlineFormat(content)}</li>`, mathTokens));
        continue;
        }

        // Numbered list items
        if (/^[\s]*\d+\. (.+)/.test(line)) {
        if (inList) { html.push("</ul>"); inList = false; }
        // Start an <ol> group — simplification: treat each as its own for now
        const content = line.replace(/^[\s]*\d+\. /, "");
        html.push(restoreMath(`<p class="numbered-item">${inlineFormat(content)}</p>`, mathTokens));
        continue;
        }

        // Empty line
        if (line.trim() === "") {
        if (inList) { html.push("</ul>"); inList = false; }
        html.push("<br />");
        continue;
        }

        // Regular paragraph line
        if (inList) { html.push("</ul>"); inList = false; }
        html.push(restoreMath(`<p>${inlineFormat(line)}</p>`, mathTokens));
    }
    if (inList) html.push("</ul>");
    return html.join("\n");
    }

    function inlineFormat(text) {
    return text
        // Bold+italic ***text***
        .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
        // Bold **text**
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        // Italic *text* or _text_
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/_(.+?)_/g, "<em>$1</em>")
        // Inline code `code`
        .replace(/`(.+?)`/g, "<code>$1</code>")
    }

  copyBtn.addEventListener("click", async () => {
    if (!state.lastExplanation.explanation) return;

    try {
      await navigator.clipboard.writeText(state.lastExplanation.explanation);
      flashIconSuccess(copyBtn);
      showToast("success", "Copied to clipboard");
    } catch (_) {
      showToast("error", "Copy failed", "Your browser blocked clipboard access.");
    }
  });

  downloadBtn.addEventListener("click", () => {
    if (!state.lastExplanation.explanation) return;

    const blob = new Blob([state.lastExplanation.explanation], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "screenshot-explanation.txt";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    flashIconSuccess(downloadBtn);
    showToast("success", "Downloaded", "Saved as screenshot-explanation.txt");
  });

  clearBtn.addEventListener("click", () => {
    resultCard.hidden = true;
    resultBody.textContent = "";
    resultTitle.textContent = "Screenshot Explanation";
    state.lastExplanation = { title: "", explanation: "" };
  });

  function flashIconSuccess(btn) {
    btn.classList.add("is-success");
    setTimeout(() => btn.classList.remove("is-success"), 1400);
  }

  /* ============================================================
     12. INIT
     ============================================================ */
  function init() {
    updateExplainButtonState();
    updateWordCounter();
  }

  init();
})();