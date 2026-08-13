/* ==========================================================
   TEXT SUMMARIZER — vanilla JS controller
   No frameworks. No page reloads. No navigation.
   Safe to run more than once (NiceGUI may re-init the DOM).
   ========================================================== */

(function () {
  "use strict";

  /* ============================================================
     1. INITIALIZATION
     ============================================================ */

  function initTextSummarizer() {
    const root = document.querySelector(".text-summarizer-root");

    if (!root) return;

    // Guard against duplicate initialization if NiceGUI
    // re-renders / re-mounts this fragment.
    if (root.dataset.initialized === "true") {
      return;
    }
    root.dataset.initialized = "true";

    /* ============================================================
       2. DOM REFERENCES
       ============================================================ */

    const dom = {
      root: root,

      // Mode switch
      modeBtns: root.querySelectorAll("[data-mode-btn]"),
      modePanels: root.querySelectorAll("[data-mode-panel]"),

      // Paste mode
      inputText: root.querySelector("[data-input-text]"),
      statChars: root.querySelector("[data-stat-chars]"),
      statWords: root.querySelector("[data-stat-words]"),
      clearTextBtn: root.querySelector("[data-clear-text]"),

      // Upload mode
      dropzone: root.querySelector("[data-dropzone]"),
      fileInput: root.querySelector("[data-file-input]"),
      fileCard: root.querySelector("[data-file-card]"),
      fileName: root.querySelector("[data-file-name]"),
      fileSub: root.querySelector("[data-file-sub]"),
      fileWords: root.querySelector("[data-file-words]"),
      fileChars: root.querySelector("[data-file-chars]"),
      fileTime: root.querySelector("[data-file-time]"),
      fileStatus: root.querySelector("[data-file-status]"),
      fileStatusDot: root.querySelector("[data-file-status-dot]"),
      fileStatusText: root.querySelector("[data-file-status-text]"),
      removeFileBtn: root.querySelector("[data-remove-file]"),

      // Settings
      lengthGroup: root.querySelector("[data-length-group]"),
      lengthSegments: root.querySelectorAll("[data-length]"),
      instructions: root.querySelector("[data-input-instructions]"),

      // Generate
      generateBtn: root.querySelector("[data-generate]"),
      generateLabel: root.querySelector("[data-generate-label]"),

      // Output
      outputStatus: root.querySelector("[data-output-status]"),
      outputBody: root.querySelector("[data-output-body]"),
      emptyState: root.querySelector("[data-empty-state]"),
      loadingState: root.querySelector("[data-loading-state]"),
      loadingText: root.querySelector("[data-loading-text]"),
      summaryContent: root.querySelector("[data-summary-content]"),
      outputActions: root.querySelector("[data-output-actions]"),

      // Actions
      copyBtn: root.querySelector("[data-copy]"),
      copyLabel: root.querySelector("[data-copy-label]"),
      downloadBtn: root.querySelector("[data-download]"),
      downloadLabel: root.querySelector("[data-download-label]"),
      bookmarkBtn: root.querySelector("[data-bookmark]"),
      bookmarkLabel: root.querySelector("[data-bookmark-label]"),

      // Toasts
      toastContainer: root.querySelector("[data-toast-container]"),
    };

    /* ============================================================
       3. STATE
       ============================================================ */

    const state = {
      mode: "paste", // "paste" | "upload"
      selectedLength: "short",
      extractedFile: null, // { name, type, size, uploadedAt }
      extractedPdfText: "", // holds extracted text from uploaded doc
      lastSummary: "",
      lastExecutionId: null,
      isBookmarked: false,
      isGenerating: false,
      isExtracting: false,
      isDownloading: false,
      activeGenerateController: null,
    };

    /* ============================================================
       4. AUTHENTICATION
       ============================================================ */

    function authHeaders(extra = {}) {
      const token = localStorage.getItem("access_token");

      return Object.assign(
        token ? { Authorization: "Bearer " + token } : {},
        extra
      );
    }

    /* ============================================================
       5. TOAST SYSTEM
       ============================================================ */

    function showToast(message, type = "info", duration = 3200) {
      if (!dom.toastContainer) return;

      const toast = document.createElement("div");
      toast.className = "ts-toast" + (type === "error" ? " is-error" : type === "success" ? " is-success" : "");
      toast.setAttribute("role", "status");

      const dot = document.createElement("span");
      dot.className = "ts-toast-dot";

      const text = document.createElement("span");
      text.textContent = message;

      toast.appendChild(dot);
      toast.appendChild(text);
      dom.toastContainer.appendChild(toast);

      window.setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.2s ease";
        window.setTimeout(() => toast.remove(), 220);
      }, duration);
    }

    /* ============================================================
       6. INPUT HANDLING (PASTE MODE)
       ============================================================ */

    function updateTextStats() {
      if (!dom.inputText) return;

      const value = dom.inputText.value || "";
      const chars = value.length;
      const words = value.trim() ? value.trim().split(/\s+/).length : 0;

      if (dom.statChars) dom.statChars.textContent = String(chars);
      if (dom.statWords) dom.statWords.textContent = String(words);
    }

    function switchMode(mode) {
      if (mode === state.mode) return;
      state.mode = mode;

      dom.modeBtns.forEach((btn) => {
        const isActive = btn.dataset.modeBtn === mode;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-selected", String(isActive));
      });

      dom.modePanels.forEach((panel) => {
        const isActive = panel.dataset.modePanel === mode;
        panel.classList.toggle("is-active", isActive);
        panel.hidden = !isActive;
      });
    }

    /* ============================================================
       7. FILE UPLOAD
       ============================================================ */

    function formatFileSize(bytes) {
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
      return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    function getFileExtLabel(filename) {
      const lower = filename.toLowerCase();
      if (lower.endsWith(".pdf")) return "PDF";
      if (lower.endsWith(".docx")) return "DOCX";
      if (lower.endsWith(".txt")) return "TXT";
      return "FILE";
    }

    function isAllowedFile(filename) {
      const lower = filename.toLowerCase();
      return lower.endsWith(".pdf") || lower.endsWith(".docx") || lower.endsWith(".txt");
    }

    function handleFileSelected(file) {
      if (!file) return;

      if (!isAllowedFile(file.name)) {
        showToast("Unsupported file type. Use PDF, DOCX or TXT.", "error");
        return;
      }

      state.extractedFile = {
        name: file.name,
        type: getFileExtLabel(file.name),
        size: file.size,
        uploadedAt: new Date(),
      };
      state.extractedPdfText = "";

      renderFileCard();
      extractDocumentText(file);
    }

    function renderFileCard() {
      const f = state.extractedFile;
      if (!f || !dom.fileCard) return;

      dom.fileCard.hidden = false;
      if (dom.fileName) dom.fileName.textContent = f.name;
      if (dom.fileSub) dom.fileSub.textContent = f.type + " · " + formatFileSize(f.size);
      if (dom.fileTime) {
        dom.fileTime.textContent = "Uploaded " + f.uploadedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      }
    }

    function updateFileTextStats() {
      const text = state.extractedPdfText || "";
      const words = text.trim() ? text.trim().split(/\s+/).length : 0;
      const chars = text.length;

      if (dom.fileWords) dom.fileWords.textContent = words + " words";
      if (dom.fileChars) dom.fileChars.textContent = chars + " characters";
    }

    function setFileStatus(state_, text) {
      // state_: "loading" | "success" | "error" | "idle"
      if (!dom.fileStatusDot || !dom.fileStatusText) return;

      dom.fileStatusDot.classList.remove("is-loading", "is-success", "is-error");
      if (state_ !== "idle") {
        dom.fileStatusDot.classList.add("is-" + state_);
      }
      dom.fileStatusText.textContent = text;
    }

    function resetFileUpload() {
      state.extractedFile = null;
      state.extractedPdfText = "";
      state.isExtracting = false;

      if (dom.fileCard) dom.fileCard.hidden = true;
      if (dom.fileInput) dom.fileInput.value = "";
      updateFileTextStats();
    }

    function setupDropzone() {
      if (!dom.dropzone || !dom.fileInput) return;

      dom.dropzone.addEventListener("click", () => {
        dom.fileInput.click();
      });

      dom.dropzone.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          dom.fileInput.click();
        }
      });

      dom.fileInput.addEventListener("change", () => {
        const file = dom.fileInput.files && dom.fileInput.files[0];
        if (file) handleFileSelected(file);
      });

      ["dragenter", "dragover"].forEach((evt) => {
        dom.dropzone.addEventListener(evt, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dom.dropzone.classList.add("is-dragover");
        });
      });

      ["dragleave", "drop"].forEach((evt) => {
        dom.dropzone.addEventListener(evt, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dom.dropzone.classList.remove("is-dragover");
        });
      });

      dom.dropzone.addEventListener("drop", (e) => {
        const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
        if (file) handleFileSelected(file);
      });

      if (dom.removeFileBtn) {
        dom.removeFileBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          resetFileUpload();
        });
      }
    }

    /* ============================================================
       8. DOCUMENT EXTRACTION
       ============================================================ */

    async function extractDocumentText(file) {
      state.isExtracting = true;
      setFileStatus("loading", "Extracting text...");

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("/summarizer/extract", {
          method: "POST",
          credentials: "include",
          headers: authHeaders(), // do NOT set Content-Type for FormData
          body: formData,
        });

        if (!response.ok) {
          const message = await parseApiError(response);
          throw new Error(message);
        }

        const data = await safeParseJson(response);
        const text = (data && data.text) || "";

        if (!text) {
          throw new Error("No text could be extracted from this file.");
        }

        state.extractedPdfText = text;
        updateFileTextStats();
        setFileStatus("success", "Ready to summarize");
      } catch (err) {
        setFileStatus("error", err.message || "Extraction failed.");
        showToast(err.message || "Failed to extract text from file.", "error");
      } finally {
        state.isExtracting = false;
      }
    }

    /* ============================================================
       9. SUMMARY GENERATION
       ============================================================ */

    function getActiveInputText() {
      if (state.mode === "upload") {
        return state.extractedPdfText || "";
      }
      return (dom.inputText && dom.inputText.value) || "";
    }

    async function handleGenerate() {
      if (state.isGenerating) return; // prevent duplicate submissions

      const text = getActiveInputText().trim();

      if (!text) {
        showToast(
          state.mode === "upload"
            ? "Upload and extract a document first."
            : "Please enter some text to summarize.",
          "error"
        );
        return;
      }

      if (state.mode === "upload" && state.isExtracting) {
        showToast("Please wait for extraction to finish.", "error");
        return;
      }

      state.isGenerating = true;
      setGenerateButtonLoading(true);
      showLoadingState("Analyzing...");

      window.setTimeout(() => {
        if (state.isGenerating) {
          showLoadingState("Generating summary...");
        }
      }, 1200);

      const controller = new AbortController();
      state.activeGenerateController = controller;

      try {
        const response = await fetch("/summarizer/generate", {
          method: "POST",
          credentials: "include",
          headers: authHeaders({ "Content-Type": "application/json" }),
          signal: controller.signal,
          body: JSON.stringify({
            text: text,
            length: state.selectedLength,
            instructions: (dom.instructions && dom.instructions.value.trim()) || "",
          }),
        });

        if (!response.ok) {
          const message = await parseApiError(response);
          throw new Error(message);
        }

        const data = await safeParseJson(response);

        if (!data || !data.summary) {
          throw new Error("The AI returned an empty summary.");
        }

        state.lastSummary = data.summary;
        state.lastExecutionId = data.execution_id || null;
        state.isBookmarked = false;

        renderSummary(data.summary);
        setOutputActionsEnabled(true);
        updateBookmarkButtonState();

        if (typeof window.refreshWorkspace === "function") {
          window.refreshWorkspace();
        }

        showToast("Summary generated.", "success");
      } catch (err) {
        if (err.name === "AbortError") {
          // Request intentionally cancelled — no user-facing error.
        } else {
          showToast(err.message || "Failed to generate summary.", "error");
          showEmptyOrPreviousState();
        }
      } finally {
        state.isGenerating = false;
        state.activeGenerateController = null;
        setGenerateButtonLoading(false);
      }
    }

    /* ============================================================
       10. BOOKMARKING
       ============================================================ */

    async function handleBookmark() {
      if (!state.lastExecutionId || state.isBookmarked) return;

      const original = dom.bookmarkLabel ? dom.bookmarkLabel.textContent : "";
      if (dom.bookmarkLabel) dom.bookmarkLabel.textContent = "Bookmarking...";
      if (dom.bookmarkBtn) dom.bookmarkBtn.disabled = true;

      try {
        const response = await fetch("/bookmarks", {
          method: "POST",
          credentials: "include",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ execution_id: state.lastExecutionId }),
        });

        if (!response.ok) {
          const message = await parseApiError(response);
          throw new Error(message);
        }

        state.isBookmarked = true;
        updateBookmarkButtonState();
        showToast("Bookmarked.", "success");
      } catch (err) {
        if (dom.bookmarkLabel) dom.bookmarkLabel.textContent = original || "Bookmark";
        if (dom.bookmarkBtn) dom.bookmarkBtn.disabled = !state.lastExecutionId;
        showToast(err.message || "Failed to bookmark this summary.", "error");
      }
    }

    function updateBookmarkButtonState() {
      if (!dom.bookmarkBtn || !dom.bookmarkLabel) return;

      if (state.isBookmarked) {
        dom.bookmarkBtn.disabled = true;
        dom.bookmarkBtn.classList.add("is-success");
        dom.bookmarkLabel.textContent = "Bookmarked ✓";
      } else {
        dom.bookmarkBtn.disabled = !state.lastExecutionId;
        dom.bookmarkBtn.classList.remove("is-success");
        dom.bookmarkLabel.textContent = "Bookmark";
      }
    }

    /* ============================================================
       11. COPY
       ============================================================ */

    async function handleCopy() {
      if (!state.lastSummary) return;

      try {
        await navigator.clipboard.writeText(state.lastSummary);
        flashLabel(dom.copyLabel, "Copied", "Copy");
      } catch (err) {
        showToast("Could not copy summary to clipboard.", "error");
      }
    }

    function flashLabel(el, tempText, restoreText, duration = 1600) {
      if (!el) return;
      el.textContent = tempText;
      window.setTimeout(() => {
        el.textContent = restoreText;
      }, duration);
    }

    /* ============================================================
       12. PDF DOWNLOAD
       ============================================================ */

    async function handleDownload() {
      if (!state.lastSummary || state.isDownloading) return;

      state.isDownloading = true;
      if (dom.downloadLabel) dom.downloadLabel.textContent = "Preparing PDF...";
      if (dom.downloadBtn) dom.downloadBtn.disabled = true;

      try {
        const response = await fetch("/summarizer/download", {
          method: "POST",
          credentials: "include",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ summary: state.lastSummary }),
        });

        if (!response.ok) {
          const message = await parseApiError(response);
          throw new Error(message);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "summary.pdf";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        flashLabel(dom.downloadLabel, "Downloaded", "Download PDF");
      } catch (err) {
        if (dom.downloadLabel) dom.downloadLabel.textContent = "Download PDF";
        showToast(err.message || "Failed to download PDF.", "error");
      } finally {
        state.isDownloading = false;
        if (dom.downloadBtn) dom.downloadBtn.disabled = false;
      }
    }

    /* ============================================================
       13. CLEAR / RESET
       ============================================================ */

    function handleClearText() {
      if (dom.inputText) {
        dom.inputText.value = "";
        updateTextStats();
        dom.inputText.focus();
      }
    }

    /* ============================================================
       14. ERROR HANDLING
       ============================================================ */

    async function safeParseJson(response) {
      try {
        return await response.json();
      } catch (err) {
        return null;
      }
    }

    async function parseApiError(response) {
      let raw = null;

      try {
        raw = await response.clone().json();
      } catch (err) {
        try {
          raw = await response.text();
        } catch (err2) {
          raw = null;
        }
      }

      if (response.status === 401 || response.status === 403) {
        return "Authentication required.";
      }

      if (raw && typeof raw === "object") {
        if (typeof raw.detail === "string" && raw.detail.trim()) {
          return raw.detail;
        }
        if (Array.isArray(raw.detail) && raw.detail.length) {
          const first = raw.detail[0];
          if (first && typeof first.msg === "string") {
            return first.msg;
          }
        }
        if (typeof raw.message === "string" && raw.message.trim()) {
          return raw.message;
        }
      }

      if (typeof raw === "string" && raw.trim()) {
        // Avoid dumping raw HTML/error pages into the UI.
        if (raw.trim().startsWith("<")) {
          return "Something went wrong. Please try again.";
        }
        return raw.trim();
      }

      if (response.status >= 500) {
        return "Something went wrong on our end. Please try again.";
      }

      return "Something went wrong. Please try again.";
    }

    /* ============================================================
       15. UI STATE HELPERS
       ============================================================ */

    function setGenerateButtonLoading(isLoading) {
      if (!dom.generateBtn) return;

      dom.generateBtn.disabled = isLoading;
      dom.generateBtn.classList.toggle("is-loading", isLoading);

      if (dom.generateLabel) {
        dom.generateLabel.textContent = isLoading ? "Generating..." : "Generate Summary";
      }
    }

    function showLoadingState(text) {
      if (dom.loadingText) dom.loadingText.textContent = text;
      if (dom.loadingState) dom.loadingState.hidden = false;
      if (dom.emptyState) dom.emptyState.hidden = true;
      if (dom.summaryContent) dom.summaryContent.hidden = true;
      setOutputStatus("busy", "Generating");
    }

    function showEmptyOrPreviousState() {
      if (state.lastSummary) {
        renderSummary(state.lastSummary);
      } else {
        if (dom.loadingState) dom.loadingState.hidden = true;
        if (dom.summaryContent) dom.summaryContent.hidden = true;
        if (dom.emptyState) dom.emptyState.hidden = false;
        setOutputStatus("idle", "Ready");
      }
    }

    function setOutputStatus(kind, label) {
      if (!dom.outputStatus) return;
      dom.outputStatus.textContent = label;
      dom.outputStatus.classList.remove("is-ready", "is-busy");
      if (kind === "ready") dom.outputStatus.classList.add("is-ready");
      if (kind === "busy") dom.outputStatus.classList.add("is-busy");
    }

    function setOutputActionsEnabled(enabled) {
      if (dom.outputActions) dom.outputActions.hidden = !enabled;
      if (dom.copyBtn) dom.copyBtn.disabled = !enabled;
      if (dom.downloadBtn) dom.downloadBtn.disabled = !enabled;
    }

    /**
     * Renders the summary using safe DOM construction / a minimal
     * markdown-like formatter. Never uses innerHTML with raw
     * untrusted AI output.
     */
    function renderSummary(summaryText) {
      if (!dom.summaryContent) return;

      dom.loadingState && (dom.loadingState.hidden = true);
      dom.emptyState && (dom.emptyState.hidden = true);

      dom.summaryContent.innerHTML = "";
      dom.summaryContent.hidden = false;

      const fragment = buildSafeSummaryFragment(summaryText);
      dom.summaryContent.appendChild(fragment);

      setOutputStatus("ready", "Ready");
    }

    function buildSafeSummaryFragment(text) {
      const fragment = document.createDocumentFragment();
      const lines = String(text).replace(/\r\n/g, "\n").split("\n");

      let listEl = null;
      let listType = null; // "ul" | "ol"

      function closeList() {
        listEl = null;
        listType = null;
      }

      lines.forEach((rawLine) => {
        const line = rawLine.trim();

        if (!line) {
          closeList();
          return;
        }

        const headingMatch = /^(#{1,3})\s+(.*)$/.exec(line);
        const bulletMatch = /^[-*•]\s+(.*)$/.exec(line);
        const numberedMatch = /^\d+[.)]\s+(.*)$/.exec(line);

        if (headingMatch) {
          closeList();
          const level = headingMatch[1].length;
          const tag = level === 1 ? "h1" : level === 2 ? "h2" : "h3";
          const el = document.createElement(tag);
          appendInlineFormatted(el, headingMatch[2]);
          fragment.appendChild(el);
          return;
        }

        if (bulletMatch) {
          if (listType !== "ul") {
            listEl = document.createElement("ul");
            fragment.appendChild(listEl);
            listType = "ul";
          }
          const li = document.createElement("li");
          appendInlineFormatted(li, bulletMatch[1]);
          listEl.appendChild(li);
          return;
        }

        if (numberedMatch) {
          if (listType !== "ol") {
            listEl = document.createElement("ol");
            fragment.appendChild(listEl);
            listType = "ol";
          }
          const li = document.createElement("li");
          appendInlineFormatted(li, numberedMatch[1]);
          listEl.appendChild(li);
          return;
        }

        closeList();
        const p = document.createElement("p");
        appendInlineFormatted(p, line);
        fragment.appendChild(p);
      });

      return fragment;
    }

    /**
     * Appends text to an element, safely converting **bold**
     * markers to <strong> without ever using innerHTML on
     * untrusted content.
     */
    function appendInlineFormatted(el, text) {
      const parts = String(text).split(/(\*\*[^*]+\*\*)/g);

      parts.forEach((part) => {
        if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
          const strong = document.createElement("strong");
          strong.textContent = part.slice(2, -2);
          el.appendChild(strong);
        } else if (part) {
          el.appendChild(document.createTextNode(part));
        }
      });
    }

    /* ============================================================
       EVENT WIRING
       ============================================================ */

    // Mode switch
    dom.modeBtns.forEach((btn) => {
      btn.addEventListener("click", () => switchMode(btn.dataset.modeBtn));
    });

    // Paste mode
    if (dom.inputText) {
      dom.inputText.addEventListener("input", updateTextStats);
    }
    if (dom.clearTextBtn) {
      dom.clearTextBtn.addEventListener("click", handleClearText);
    }

    // Upload mode
    setupDropzone();

    // Settings — length segments (event delegation on the group)
    if (dom.lengthGroup) {
      dom.lengthGroup.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-length]");
        if (!btn) return;

        state.selectedLength = btn.dataset.length;

        dom.lengthSegments.forEach((segment) => {
          const isActive = segment === btn;
          segment.classList.toggle("is-active", isActive);
          segment.setAttribute("aria-checked", String(isActive));
        });
      });
    }

    // Generate
    if (dom.generateBtn) {
      dom.generateBtn.addEventListener("click", handleGenerate);
    }

    // Keyboard shortcut: Cmd/Ctrl + Enter
    root.addEventListener("keydown", (e) => {
      const isModEnter = (e.metaKey || e.ctrlKey) && e.key === "Enter";
      if (isModEnter) {
        e.preventDefault();
        handleGenerate();
      }
    });

    // Output actions
    if (dom.copyBtn) dom.copyBtn.addEventListener("click", handleCopy);
    if (dom.downloadBtn) dom.downloadBtn.addEventListener("click", handleDownload);
    if (dom.bookmarkBtn) dom.bookmarkBtn.addEventListener("click", handleBookmark);

    /* ============================================================
       INITIAL RENDER
       ============================================================ */

    updateTextStats();
    updateFileTextStats();
    setOutputActionsEnabled(false);
    updateBookmarkButtonState();
  }

  // Run now if the DOM is ready, and also on DOMContentLoaded to
  // cover NiceGUI fragments injected before/after this script runs.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTextSummarizer);
  } else {
    initTextSummarizer();
  }

  // Expose a manual re-init hook in case NiceGUI swaps the DOM
  // fragment without a full page reload (e.g. tool re-mounted).
  window.initTextSummarizer = initTextSummarizer;
})();