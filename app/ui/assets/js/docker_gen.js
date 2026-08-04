/* ================================================================
   DOCKERFILE GENERATOR — FRONTEND LOGIC
   ----------------------------------------------------------------
   Sections:
   1.  State & DOM refs
   2.  Ambient background canvas (decorative "container field")
   3.  Theme toggle
   4.  Toasts
   5.  Folder selection (click picker + drag & drop, dir traversal)
   6.  Folder summary rendering
   7.  View-state machine (empty / loading / results / error)
   8.  Loading sequence (rotating messages + progress)
   9.  API call
   10. Dockerfile rendering (line numbers + syntax highlight)
   11. Dockerfile card actions (copy / download / wrap / fullscreen)
   12. Quick Start checklist rendering + per-step copy
   13. Generate button wiring
   ================================================================ */

(() => {
  "use strict";

  /* ============================================================
     1. STATE & DOM REFS
     ============================================================ */
  const state = {
    files: [],          // File[] with .webkitRelativePath set
    folderName: "",
    totalBytes: 0,
    isLoading: false,
    lastResult: null,   // { dockerfile, quick_start }
  };

  const el = {
    dropzone: document.getElementById("dropzone"),
    chooseFolderBtn: document.getElementById("chooseFolderBtn"),
    folderInput: document.getElementById("folderInput"),
    folderSummary: document.getElementById("folderSummary"),
    fsName: document.getElementById("fsName"),
    fsFileCount: document.getElementById("fsFileCount"),
    fsSize: document.getElementById("fsSize"),
    fsClear: document.getElementById("fsClear"),
    uploadStatus: document.getElementById("uploadStatus"),
    generateBtn: document.getElementById("generateBtn"),

    buildConsole: document.getElementById("buildConsole"),
    buildMessage: document.getElementById("buildMessage"),
    buildProgressFill: document.getElementById("buildProgressFill"),
    buildTerminal: document.getElementById("buildTerminal"),

    errorPanel: document.getElementById("errorPanel"),
    errorMessage: document.getElementById("errorMessage"),
    retryBtn: document.getElementById("retryBtn"),

    emptyPanel: document.getElementById("emptyPanel"),
    resultsGrid: document.getElementById("resultsGrid"),

    codeContent: document.getElementById("codeContent"),
    codeBlock: document.getElementById("codeBlock"),
    codeScroll: document.getElementById("codeScroll"),
    lineCount: document.getElementById("lineCount"),
    byteCount: document.getElementById("byteCount"),
    wrapToggleBtn: document.getElementById("wrapToggleBtn"),
    copyDockerfileBtn: document.getElementById("copyDockerfileBtn"),
    downloadDockerfileBtn: document.getElementById("downloadDockerfileBtn"),
    fullscreenBtn: document.getElementById("fullscreenBtn"),
    fullscreenOverlay: document.getElementById("fullscreenOverlay"),
    fullscreenCodeContent: document.getElementById("fullscreenCodeContent"),
    closeFullscreenBtn: document.getElementById("closeFullscreenBtn"),
    bookmarkBtn: document.getElementById("bookmarkBtn"),
    qsList: document.getElementById("qsList"),
    qsProgress: document.getElementById("qsProgress"),

    themeToggle: document.getElementById("themeToggle"),
    toastStack: document.getElementById("toastStack"),
  };

  const API_ENDPOINT = "/docker-generator/generate";
  const BOOKMARK_ENDPOINT = "/bookmarks";

  /* ============================================================
     2. AMBIENT BACKGROUND CANVAS
     A quiet field of drifting "container" squares behind the hero.
     Purely decorative — pauses when off-screen / reduced motion.
     ============================================================ */
  function initContainerField() {
    const canvas = document.getElementById("containerField");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let particles = [];
    let raf = null;

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = Math.min(window.innerHeight, 900);
      const count = Math.round((canvas.width * canvas.height) / 90000);
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: 5 + Math.random() * 9,
        speed: 0.08 + Math.random() * 0.18,
        opacity: 0.04 + Math.random() * 0.08,
      }));
    }

    function tick() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "rgba(36,150,237,1)";
      for (const p of particles) {
        p.y -= p.speed;
        if (p.y < -20) p.y = canvas.height + 20;
        ctx.globalAlpha = p.opacity;
        ctx.strokeRect(p.x, p.y, p.size, p.size);
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(tick);
    }

    resize();
    window.addEventListener("resize", resize);
    if (!prefersReducedMotion) {
      raf = requestAnimationFrame(tick);
    }
  }

  /* ============================================================
     3. THEME TOGGLE
     ============================================================ */
  function initThemeToggle() {
    el.themeToggle.addEventListener("click", () => {
        const isLight = document.documentElement.getAttribute("data-theme") === "light";
        document.documentElement.setAttribute("data-theme", isLight ? "dark" : "light");
        el.themeToggle.textContent = isLight ? "🌙" : "☀️";
    });
    }

  /* ============================================================
     4. TOASTS
     ============================================================ */
  function showToast(message, type = "info") {
    const icons = {
      success: "fa-solid fa-circle-check",
      error: "fa-solid fa-circle-exclamation",
      info: "fa-solid fa-circle-info",
    };
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="toast-icon ${icons[type] || icons.info}"></i><span>${message}</span>`;
    el.toastStack.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("leaving");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    }, 2600);
  }

  /* ============================================================
     5. FOLDER SELECTION
     Supports both the native folder picker (webkitdirectory) and
     drag & drop of a folder via the DataTransferItem API.
     ============================================================ */
  function initFolderSelection() {
    el.chooseFolderBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      el.folderInput.click();
    });

    el.dropzone.addEventListener("click", () => el.folderInput.click());
    el.dropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        el.folderInput.click();
      }
    });

    el.folderInput.addEventListener("change", (e) => {
      const files = Array.from(e.target.files || []);
      if (files.length) handleFolderFiles(files);
    });

    // ---- Drag & drop ----
    ["dragenter", "dragover"].forEach((evt) => {
      el.dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.dropzone.classList.add("drag-active");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      el.dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (evt === "dragleave" && e.target !== el.dropzone) return;
        el.dropzone.classList.remove("drag-active");
      });
    });

    el.dropzone.addEventListener("drop", async (e) => {
      const items = e.dataTransfer && e.dataTransfer.items;
      if (!items || !items.length) return;

      setUploadStatus("Reading folder…", "");
      try {
        const files = await readDroppedItems(items);
        if (!files.length) {
          setUploadStatus("That doesn't look like a folder. Try again.", "status-error");
          return;
        }
        handleFolderFiles(files);
      } catch (err) {
        console.error(err);
        setUploadStatus("Couldn't read that folder.", "status-error");
      }
    });

    el.fsClear.addEventListener("click", (e) => {
      e.stopPropagation();
      clearFolderSelection();
    });
  }

  /** Recursively walks DataTransferItemList entries into a flat File[] list,
   *  stamping each File with a webkitRelativePath so the payload matches
   *  what <input webkitdirectory> would have produced. */
  async function readDroppedItems(items) {
    const entries = [];
    for (const item of items) {
      const entry = item.webkitGetAsEntry && item.webkitGetAsEntry();
      if (entry) entries.push(entry);
    }

    const files = [];

    async function walk(entry, path) {
      if (entry.isFile) {
        const file = await new Promise((resolve, reject) => entry.file(resolve, reject));
        const relativePath = path + entry.name;
        try {
          Object.defineProperty(file, "webkitRelativePath", {
            value: relativePath,
            writable: true,
          });
        } catch (_) {
          file.webkitRelativePath = relativePath;
        }
        files.push(file);
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        const readAllEntries = () =>
          new Promise((resolve, reject) => {
            const all = [];
            function readBatch() {
              reader.readEntries((batch) => {
                if (!batch.length) {
                  resolve(all);
                  return;
                }
                all.push(...batch);
                readBatch();
              }, reject);
            }
            readBatch();
          });
        const children = await readAllEntries();
        for (const child of children) {
          await walk(child, path + entry.name + "/");
        }
      }
    }

    for (const entry of entries) {
      await walk(entry, "");
    }
    return files;
  }

  /* ============================================================
     FILE FILTER
     Strips dependency/build/binary folders and files before upload.
     A real project with node_modules can have 39k+ files; after
     filtering, only the source files the backend actually needs
     for detection are sent.
     ============================================================ */
  const IGNORED_DIRS = new Set([
    // JS / Node
    "node_modules", ".npm", ".yarn", ".pnp",
    // Python
    ".venv", "venv", "env", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".eggs",
    // Build outputs
    "dist", "build", "out", "output", ".next", ".nuxt",
    ".svelte-kit", ".output", "target", "bin", "obj",
    // VCS / tooling
    ".git", ".hg", ".svn", ".bzr",
    // IDE
    ".idea", ".vscode", ".vs",
    // Caches & temp
    ".cache", ".temp", ".tmp", "tmp", "temp",
    "coverage", ".nyc_output", ".turbo",
    // Mobile / native
    "Pods", "DerivedData", ".gradle", "gradle",
    // Misc
    "vendor",
    "bower_components",
    ".terraform",
    ".serverless",
    "htmlcov",
    "storybook-static",
    ".docusaurus",
  ]);

  const IGNORED_EXTENSIONS = new Set([
    // Compiled / binary
    ".pyc", ".pyo", ".pyd",
    ".class",
    ".o", ".a", ".so", ".dll", ".lib", ".exe", ".bin", ".wasm",
    // Archives
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".rar", ".7z",
    // Media — images / video / audio / fonts
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico",
    ".svg", ".mp4", ".webm", ".mov", ".avi",
    ".mp3", ".wav", ".ogg", ".flac",
    ".ttf", ".woff", ".woff2", ".eot", ".otf",
    // Office / data dumps
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".db", ".sqlite", ".sqlite3", ".csv", ".parquet", ".pkl",
    // Source maps
    ".map",
    // Editor swap
    ".swp", ".swo",
  ]);

  // Always-ignored file names regardless of directory
  const IGNORED_FILENAMES = new Set([
    ".DS_Store", "Thumbs.db", "desktop.ini",
  ]);

  /**
   * Returns true if a file should be sent to the backend.
   * Checks every path segment so nested ignored dirs are caught too.
   * Also drops individual files larger than 512 KB (not useful for detection).
   */
  function shouldIncludeFile(file) {
    const relPath = (file.webkitRelativePath || file.name).replace(/\\/g, "/");
    const segments = relPath.split("/");
    const filename = segments[segments.length - 1];

    if (IGNORED_FILENAMES.has(filename)) return false;

    const dotIdx = filename.lastIndexOf(".");
    if (dotIdx !== -1) {
      const ext = filename.slice(dotIdx).toLowerCase();
      if (IGNORED_EXTENSIONS.has(ext)) return false;
    }

    // Check every directory segment (all but the last which is the filename)
    for (let i = 0; i < segments.length - 1; i++) {
      const seg = segments[i];
      if (IGNORED_DIRS.has(seg)) return false;
      if (seg.endsWith(".egg-info") || seg.endsWith(".dist-info")) return false;
    }

    // Skip large binaries that slipped through extension checks
    if (file.size > 512 * 1024) return false;

    return true;
  }

  function handleFolderFiles(files) {
    if (!files.length) return;

    const first = files[0];
    const relPath = first.webkitRelativePath || first.name;
    const rootName = relPath.split("/")[0] || "project";

    const totalRaw = files.length;
    const filtered = files.filter(shouldIncludeFile);
    const skipped = totalRaw - filtered.length;

    if (!filtered.length) {
      setUploadStatus(
        "All files were filtered out — make sure you\'re uploading a source folder, not a build/dist folder.",
        "status-error"
      );
      return;
    }

    state.files = filtered;
    state.folderName = rootName;
    state.totalBytes = filtered.reduce((sum, f) => sum + f.size, 0);

    renderFolderSummary();
    el.generateBtn.disabled = false;

    const statusMsg = skipped > 0
      ? `Ready — ${filtered.length.toLocaleString()} files selected (${skipped.toLocaleString()} build/cache files skipped).`
      : `Ready — ${filtered.length.toLocaleString()} files staged for upload.`;
    setUploadStatus(statusMsg, "status-ok");
    el.dropzone.classList.add("has-folder");
  }

  function clearFolderSelection() {
    state.files = [];
    state.folderName = "";
    state.totalBytes = 0;
    el.folderInput.value = "";
    el.folderSummary.classList.add("hidden");
    el.generateBtn.disabled = true;
    el.dropzone.classList.remove("has-folder");
    setUploadStatus("", "");
  }

  function setUploadStatus(message, cls) {
    el.uploadStatus.textContent = message;
    el.uploadStatus.className = "upload-status" + (cls ? ` ${cls}` : "");
  }

  /* ============================================================
     6. FOLDER SUMMARY RENDERING
     ============================================================ */
  function renderFolderSummary() {
    el.fsName.textContent = state.folderName;
    el.fsFileCount.textContent = state.files.length.toLocaleString();
    el.fsSize.textContent = formatBytes(state.totalBytes);
    el.folderSummary.classList.remove("hidden");
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 KB";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const value = bytes / Math.pow(1024, i);
    return `${value.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
  }

  /* ============================================================
     7. VIEW-STATE MACHINE
     ============================================================ */
  function showView(view) {
    // view: "empty" | "loading" | "results" | "error"
    el.emptyPanel.classList.toggle("hidden", view !== "empty");
    el.buildConsole.classList.toggle("hidden", view !== "loading");
    el.resultsGrid.classList.toggle("hidden", view !== "results");
    el.errorPanel.classList.toggle("hidden", view !== "error");
  }

  /* ============================================================
     8. LOADING SEQUENCE
     ============================================================ */
  const LOADING_STEPS = [
    { msg: "Scanning project…", term: "$ walking project tree" },
    { msg: "Detecting language…", term: "→ inspecting manifests & extensions" },
    { msg: "Detecting framework…", term: "→ matching known framework signatures" },
    { msg: "Detecting runtime…", term: "→ resolving pinned runtime version" },
    { msg: "Detecting entrypoint…", term: "→ locating application entrypoint" },
    { msg: "Generating Dockerfile…", term: "→ writing build stages" },
    { msg: "Preparing Quick Start…", term: "→ composing docker cli commands" },
    { msg: "Done!", term: "✓ build plan ready" },
  ];

  let loadingTimer = null;
  let loadingStepIndex = 0;

  function startLoadingSequence() {
    loadingStepIndex = 0;
    el.buildTerminal.innerHTML = '<span class="term-caret">_</span>';
    applyLoadingStep();
    clearInterval(loadingTimer);
    loadingTimer = setInterval(() => {
      loadingStepIndex = Math.min(loadingStepIndex + 1, LOADING_STEPS.length - 1);
      applyLoadingStep();
    }, 2000);
  }

  function applyLoadingStep() {
    const step = LOADING_STEPS[loadingStepIndex];
    el.buildMessage.classList.add("fade");
    setTimeout(() => {
      el.buildMessage.textContent = step.msg;
      el.buildMessage.classList.remove("fade");
    }, 180);

    const pct = Math.round(((loadingStepIndex + 1) / LOADING_STEPS.length) * 100);
    el.buildProgressFill.style.width = `${pct}%`;

    const line = document.createElement("div");
    line.textContent = step.term;
    el.buildTerminal.insertBefore(line, el.buildTerminal.lastElementChild);
    el.buildTerminal.scrollTop = el.buildTerminal.scrollHeight;
  }

  function stopLoadingSequence() {
    clearInterval(loadingTimer);
    loadingTimer = null;
  }

  /* ============================================================
     9. API CALL
     ============================================================ */
  async function generateDockerfile() {
    if (!state.files.length || state.isLoading) return;

    state.isLoading = true;
    el.generateBtn.disabled = true;
    el.generateBtn.classList.add("is-loading");
    showView("loading");
    startLoadingSequence();

    const formData = new FormData();
    for (const file of state.files) {
      formData.append("folder", file, file.webkitRelativePath || file.name);
    }

    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      let payload = null;
      try {
        payload = await response.json();
      } catch (_) {
        payload = null;
      }

      if (!response.ok) {
        const message =
          (payload && (payload.detail || payload.message)) ||
          `Request failed with status ${response.status}.`;
        throw new Error(message);
      }

      if (!payload || !payload.dockerfile) {
        throw new Error("The server response was missing a Dockerfile.");
      }

      // Let the final loading step land before switching views.
      loadingStepIndex = LOADING_STEPS.length - 1;
      applyLoadingStep();
      setTimeout(() => {
        stopLoadingSequence();
        state.lastResult = payload;
        renderResults(payload);
        showView("results");
        showToast("Dockerfile generated successfully.", "success");
      }, 500);
    } catch (err) {
      stopLoadingSequence();
      console.error(err);
      el.errorMessage.textContent = err.message || "Something went wrong on our end.";
      showView("error");
      showToast("Couldn't generate a Dockerfile.", "error");
    } finally {
      state.isLoading = false;
      el.generateBtn.disabled = false;
      el.generateBtn.classList.remove("is-loading");
    }
  }

  /* ============================================================
     10. DOCKERFILE RENDERING
     ============================================================ */
  const INSTRUCTIONS = [
    "FROM", "WORKDIR", "COPY", "ADD", "RUN", "CMD", "ENTRYPOINT",
    "EXPOSE", "ENV", "ARG", "LABEL", "USER", "VOLUME", "STOPSIGNAL",
    "HEALTHCHECK", "ONBUILD", "SHELL", "AS",
  ];
  const INSTRUCTION_RE = new RegExp(`^(\\s*)(${INSTRUCTIONS.join("|")})\\b`, "i");

  function highlightLine(line) {
    let escaped = line
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Comments
    if (/^\s*#/.test(escaped)) {
      return `<span class="tok-cmt">${escaped}</span>`;
    }

    // Leading instruction keyword
    escaped = escaped.replace(INSTRUCTION_RE, (m, ws, kw) => `${ws}<span class="tok-instr">${kw}</span>`);

    // Quoted strings
    escaped = escaped.replace(/"([^"]*)"/g, '<span class="tok-str">"$1"</span>');

    // Flags like --from=, -p
    escaped = escaped.replace(/(\s)(--?[a-zA-Z][\w-]*)/g, '$1<span class="tok-flag">$2</span>');

    // Standalone numbers (ports, versions)
    escaped = escaped.replace(/\b(\d+)\b/g, '<span class="tok-num">$1</span>');

    return escaped;
  }

  function renderResults(payload) {
    setBookmarkState(false);
    el.bookmarkBtn.disabled = !payload.execution_id;
    renderDockerfile(payload.dockerfile || "");
    renderQuickStart(payload.quick_start || []);
  }

  function renderDockerfile(dockerfile) {
    const lines = dockerfile.replace(/\r\n/g, "\n").split("\n");
    const html = lines
      .map((line) => `<span class="code-line">${highlightLine(line) || "&nbsp;"}</span>`)
      .join("\n");

    el.codeContent.innerHTML = html;
    el.fullscreenCodeContent.innerHTML = html;
    el.lineCount.textContent = lines.length.toLocaleString();
    el.byteCount.textContent = formatBytes(new Blob([dockerfile]).size);
  }

  /* ============================================================
     11. DOCKERFILE CARD ACTIONS
     ============================================================ */
  function initCodeCardActions() {
    el.wrapToggleBtn.addEventListener("click", () => {
      const wrapped = el.codeBlock.classList.toggle("wrap-on");
      el.wrapToggleBtn.classList.toggle("active", wrapped);
    });

    el.copyDockerfileBtn.addEventListener("click", () =>
      copyToClipboard(getRawDockerfile(), el.copyDockerfileBtn)
    );

    el.downloadDockerfileBtn.addEventListener("click", () => {
      const blob = new Blob([getRawDockerfile()], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Dockerfile";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast("Dockerfile downloaded.", "success");
    });

    el.fullscreenBtn.addEventListener("click", () => {
      el.fullscreenOverlay.classList.remove("hidden");
    });
    el.closeFullscreenBtn.addEventListener("click", () => {
      el.fullscreenOverlay.classList.add("hidden");
    });
    el.fullscreenOverlay.addEventListener("click", (e) => {
      if (e.target === el.fullscreenOverlay) el.fullscreenOverlay.classList.add("hidden");
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !el.fullscreenOverlay.classList.contains("hidden")) {
        el.fullscreenOverlay.classList.add("hidden");
      }
    });
  }

  function getRawDockerfile() {
    return state.lastResult ? state.lastResult.dockerfile : "";
  }

  async function copyToClipboard(text, buttonEl) {
    try {
      await navigator.clipboard.writeText(text);
      flashCopied(buttonEl);
    } catch (err) {
      console.error(err);
      showToast("Couldn't copy to clipboard.", "error");
    }
  }

  function flashCopied(buttonEl) {
    const original = buttonEl.innerHTML;
    buttonEl.classList.add("copied");
    buttonEl.innerHTML = `<i class="fa-solid fa-check"></i><span>Copied</span>`;
    showToast("Copied to clipboard.", "success");
    setTimeout(() => {
      buttonEl.classList.remove("copied");
      buttonEl.innerHTML = original;
    }, 1600);
  }

  /* ============================================================
     12. QUICK START CHECKLIST
     ============================================================ */
  function renderQuickStart(steps) {
    el.qsList.innerHTML = "";
    updateQsProgress(0, steps.length);

    steps.forEach((step, index) => {
      const li = document.createElement("li");
      li.className = "qs-item";
      li.style.setProperty("--d", `${index * 70}ms`);

      li.innerHTML = `
        <div class="qs-check"><i class="fa-solid fa-check"></i></div>
        <div class="qs-body">
          <div class="qs-step-title">${escapeHtml(step.title || `Step ${index + 1}`)}</div>
          <div class="qs-cmd-row">
            <code class="qs-cmd">${escapeHtml(step.command || "")}</code>
            <button class="qs-copy" title="Copy command" aria-label="Copy command">
              <i class="fa-regular fa-copy"></i>
            </button>
          </div>
        </div>
      `;

      const copyBtn = li.querySelector(".qs-copy");
      const checkBtn = li.querySelector(".qs-check");

      copyBtn.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(step.command || "");
          copyBtn.classList.add("copied");
          copyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
          markStepDone(li);
          showToast("Command copied.", "success");
          setTimeout(() => {
            copyBtn.classList.remove("copied");
            copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i>';
          }, 1600);
        } catch (err) {
          showToast("Couldn't copy command.", "error");
        }
      });

      checkBtn.addEventListener("click", () => {
        li.classList.toggle("done");
        recomputeQsProgress(steps.length);
      });

      el.qsList.appendChild(li);
    });
  }

  function markStepDone(li) {
    if (!li.classList.contains("done")) {
      li.classList.add("done");
      recomputeQsProgress(el.qsList.children.length);
    }
  }

  function recomputeQsProgress(total) {
    const done = el.qsList.querySelectorAll(".qs-item.done").length;
    updateQsProgress(done, total);
  }

  function updateQsProgress(done, total) {
    el.qsProgress.textContent = `${done}/${total} done`;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ============================================================
     13. WIRE UP
     ============================================================ */

  function initBookmark() {
  el.bookmarkBtn.addEventListener("click", toggleBookmark);
}

async function toggleBookmark() {
  const executionId = state.lastResult && state.lastResult.execution_id;
  if (!executionId) {
    showToast("No execution to bookmark.", "error");
    return;
  }

  const isBookmarked = el.bookmarkBtn.classList.contains("bookmarked");

  if (isBookmarked) {
    // DELETE /bookmarks/{execution_id}
    try {
      el.bookmarkBtn.disabled = true;
      const res = await fetch(`${BOOKMARK_ENDPOINT}/${executionId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to remove bookmark.");
      setBookmarkState(false);
      showToast("Bookmark removed.", "info");
    } catch (err) {
      showToast(err.message || "Couldn't remove bookmark.", "error");
    } finally {
      el.bookmarkBtn.disabled = false;
    }
  } else {
    // POST /bookmarks
    try {
      el.bookmarkBtn.disabled = true;
      const res = await fetch(BOOKMARK_ENDPOINT, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ execution_id: executionId }),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload.detail || "Failed to save bookmark.");
      }
      setBookmarkState(true);
      showToast("Saved to bookmarks.", "success");
    } catch (err) {
      showToast(err.message || "Couldn't save bookmark.", "error");
    } finally {
      el.bookmarkBtn.disabled = false;
    }
  }
}

function setBookmarkState(bookmarked) {
  el.bookmarkBtn.classList.toggle("bookmarked", bookmarked);
  el.bookmarkBtn.setAttribute("aria-pressed", bookmarked ? "true" : "false");
  el.bookmarkBtn.title = bookmarked ? "Remove bookmark" : "Save to bookmarks";
  el.bookmarkBtn.innerHTML = bookmarked
    ? '<i class="fa-solid fa-bookmark"></i>'
    : '<i class="fa-regular fa-bookmark"></i>';
}

  function init() {
    initContainerField();
    initThemeToggle();
    initFolderSelection();
    initCodeCardActions();
    initBookmark();  

    el.generateBtn.addEventListener("click", generateDockerfile);
    el.retryBtn.addEventListener("click", () => {
      if (state.files.length) {
        generateDockerfile();
      } else {
        showView("empty");
      }
    });

    showView("empty");
  }

  document.addEventListener("DOMContentLoaded", init);
})();