(() => {
  "use strict";

  /* ============================================================
     CONFIG
     ============================================================ */
  const API_ENDPOINT = "/code-review/review";
  const SUPPORTED_EXTENSIONS = ["py", "js", "c", "cpp", "java", "rs"];
  const EXT_TO_LANGUAGE = {
    py: "python",
    js: "javascript",
    c: "c",
    cpp: "cpp",
    java: "java",
    rs: "rust",
  };
  const LANGUAGE_LABEL = {
    auto: "Auto",
    python: "Python",
    javascript: "JavaScript",
    c: "C",
    cpp: "C++",
    java: "Java",
    rust: "Rust",
  };
  const LOADING_MESSAGES = [
    "Analyzing code…",
    "Computing complexity…",
    "Reviewing architecture…",
    "Looking for logical issues…",
    "Generating suggestions…",
  ];

  /* ============================================================
     ELEMENT REFS
     ============================================================ */
  const el = {
    codeInput: document.getElementById("codeInput"),
    editorShell: document.getElementById("editorShell"),
    editorGutter: document.getElementById("editorGutter"),
    languageSelect: document.getElementById("languageSelect"),

    uploadZone: document.getElementById("uploadZone"),
    fileInput: document.getElementById("fileInput"),
    uploadEmpty: document.getElementById("uploadEmpty"),
    uploadPreview: document.getElementById("uploadPreview"),
    fileName: document.getElementById("fileName"),
    fileLang: document.getElementById("fileLang"),
    fileSize: document.getElementById("fileSize"),
    fileLines: document.getElementById("fileLines"),
    fileRemove: document.getElementById("fileRemove"),

    reviewBtn: document.getElementById("reviewBtn"),
    clearBtn: document.getElementById("clearBtn"),
    progressTrack: document.getElementById("progressTrack"),
    progressFill: document.getElementById("progressFill"),

    resultBadge: document.getElementById("resultBadge"),
    emptyState: document.getElementById("emptyState"),
    loadingState: document.getElementById("loadingState"),
    resultsState: document.getElementById("resultsState"),
    thinkingLabel: document.getElementById("thinkingLabel"),

    overviewGrid: document.getElementById("overviewGrid"),
    summaryBody: document.getElementById("summaryBody"),
    errorsList: document.getElementById("errorsList"),
    errorsCount: document.getElementById("errorsCount"),
    suggestionsList: document.getElementById("suggestionsList"),
    suggestionsCount: document.getElementById("suggestionsCount"),

    toastContainer: document.getElementById("toastContainer"),
  };

  /* ============================================================
     STATE
     ============================================================ */
  const state = {
    selectedFile: null,
    loadingInterval: null,
    progressInterval: null,
  };

  /* ============================================================
     ICONS
     ============================================================ */
  if (window.lucide) window.lucide.createIcons();

  /* ============================================================
     EDITOR — line numbers + scanning affordance
     ============================================================ */
  function updateGutter() {
    const lines = el.codeInput.value.split("\n").length;
    const frag = document.createDocumentFragment();
    for (let i = 1; i <= lines; i++) {
      const span = document.createElement("span");
      span.textContent = i;
      frag.appendChild(span);
    }
    el.editorGutter.innerHTML = "";
    el.editorGutter.appendChild(frag);
  }

  el.codeInput.addEventListener("input", () => {
    updateGutter();
    if (el.codeInput.value.trim().length > 0 && state.selectedFile) {
      clearFile({ silent: true });
    }
    syncReviewButton();
  });

  el.codeInput.addEventListener("scroll", () => {
    el.editorGutter.scrollTop = el.codeInput.scrollTop;
  });

  updateGutter();

  /* ============================================================
     UPLOAD ZONE
     ============================================================ */
  function bytesToReadable(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function extensionOf(filename) {
    const parts = filename.split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  }

  function handleIncomingFile(file) {
    const ext = extensionOf(file.name);

    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      rejectUpload();
      showToast("error", "Unsupported file type.");
      return;
    }

    state.selectedFile = file;

    if (el.codeInput.value.trim().length > 0) {
      el.codeInput.value = "";
      updateGutter();
    }

    const detectedLang = EXT_TO_LANGUAGE[ext] || "auto";
    el.fileName.textContent = file.name;
    el.fileLang.textContent = LANGUAGE_LABEL[detectedLang] || "Auto";
    el.fileSize.textContent = bytesToReadable(file.size);
    el.fileLines.textContent = "— lines";

    // Read locally just to preview line count (does not affect payload)
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = typeof e.target.result === "string" ? e.target.result : "";
      const lineCount = text.length ? text.split("\n").length : 0;
      el.fileLines.textContent = `${lineCount.toLocaleString()} lines`;
    };
    reader.onerror = () => {
      el.fileLines.textContent = "— lines";
    };
    reader.readAsText(file);

    el.uploadEmpty.classList.add("hidden");
    el.uploadPreview.classList.remove("hidden");
    if (window.lucide) window.lucide.createIcons();

    syncReviewButton();
  }

  function rejectUpload() {
    el.uploadZone.classList.add("reject");
    setTimeout(() => el.uploadZone.classList.remove("reject"), 420);
  }

  function clearFile({ silent } = {}) {
    state.selectedFile = null;
    el.fileInput.value = "";
    el.uploadPreview.classList.add("hidden");
    el.uploadEmpty.classList.remove("hidden");
    if (!silent) syncReviewButton();
  }

  el.uploadZone.addEventListener("click", () => el.fileInput.click());
  el.uploadZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      el.fileInput.click();
    }
  });

  el.fileInput.addEventListener("change", () => {
    if (el.fileInput.files && el.fileInput.files[0]) {
      handleIncomingFile(el.fileInput.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach((evt) => {
    el.uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      el.uploadZone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    el.uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      el.uploadZone.classList.remove("drag-over");
    });
  });
  el.uploadZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) handleIncomingFile(file);
  });

  el.fileRemove.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });

  /* ============================================================
     REVIEW BUTTON STATE
     ============================================================ */
  function syncReviewButton() {
    const hasCode = el.codeInput.value.trim().length > 0;
    const hasFile = !!state.selectedFile;
    el.reviewBtn.disabled = !(hasCode || hasFile);
  }
  syncReviewButton();

  /* ============================================================
     CLEAR
     ============================================================ */
  el.clearBtn.addEventListener("click", () => {
    el.codeInput.value = "";
    updateGutter();
    clearFile({ silent: true });
    el.languageSelect.value = "auto";
    syncReviewButton();
    showResultsPanel("empty");
    showToast("info", "Cleared.");
  });

  /* ============================================================
     TOASTS
     ============================================================ */
  const TOAST_ICONS = {
    success: "check-circle-2",
    error: "octagon-x",
    warning: "triangle-alert",
    info: "info",
  };

  function showToast(type, message) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <i data-lucide="${TOAST_ICONS[type] || "info"}" class="toast-icon"></i>
      <span>${message}</span>
      <button class="toast-close" type="button" aria-label="Dismiss">
        <i data-lucide="x"></i>
      </button>
    `;
    el.toastContainer.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    const remove = () => {
      toast.classList.add("removing");
      setTimeout(() => toast.remove(), 200);
    };
    toast.querySelector(".toast-close").addEventListener("click", remove);
    setTimeout(remove, 4000);
  }

  /* ============================================================
     RESULT PANEL SWITCHING
     ============================================================ */
  function showResultsPanel(mode) {
    el.emptyState.classList.toggle("hidden", mode !== "empty");
    el.loadingState.classList.toggle("hidden", mode !== "loading");
    el.resultsState.classList.toggle("hidden", mode !== "results");
    el.resultBadge.classList.toggle("hidden", mode !== "results");
  }

  function startLoadingMessages() {
    let i = 0;
    el.thinkingLabel.textContent = LOADING_MESSAGES[0];
    state.loadingInterval = setInterval(() => {
      i = (i + 1) % LOADING_MESSAGES.length;
      el.thinkingLabel.textContent = LOADING_MESSAGES[i];
    }, 1800);
  }

  function stopLoadingMessages() {
    clearInterval(state.loadingInterval);
  }

  function startProgress() {
    el.progressTrack.classList.remove("hidden");
    let pct = 0;
    el.progressFill.style.width = "0%";
    state.progressInterval = setInterval(() => {
      pct = Math.min(pct + Math.random() * 9, 92);
      el.progressFill.style.width = `${pct}%`;
    }, 350);
  }

  function finishProgress() {
    clearInterval(state.progressInterval);
    el.progressFill.style.width = "100%";
    setTimeout(() => el.progressTrack.classList.add("hidden"), 500);
  }

  /* ============================================================
     REVIEW SUBMISSION
     ============================================================ */
  function setBusy(isBusy) {
    el.reviewBtn.disabled = isBusy || (!el.codeInput.value.trim() && !state.selectedFile);
    el.reviewBtn.querySelector(".btn-icon-default").classList.toggle("hidden", isBusy);
    el.reviewBtn.querySelector(".spinner-ring").classList.toggle("hidden", !isBusy);
    el.reviewBtn.querySelector(".btn-label").textContent = isBusy ? "Reviewing…" : "Review Code";
    el.clearBtn.disabled = isBusy;
    el.codeInput.disabled = isBusy;
    el.languageSelect.disabled = isBusy;
    el.uploadZone.classList.toggle("scanning-disabled", isBusy);
    el.editorShell.classList.toggle("scanning", isBusy);
    if (isBusy) {
      el.uploadZone.setAttribute("aria-disabled", "true");
    } else {
      el.uploadZone.removeAttribute("aria-disabled");
    }
  }

  async function runReview() {
    const hasCode = el.codeInput.value.trim().length > 0;
    const hasFile = !!state.selectedFile;

    if (!hasCode && !hasFile) return;
    if (hasCode && hasFile) {
      showToast("warning", "Provide either pasted code or a file, not both.");
      return;
    }

    setBusy(true);
    showResultsPanel("loading");
    startLoadingMessages();
    startProgress();

    const formData = new FormData();
    formData.append("language", el.languageSelect.value || "auto");
    if (hasCode) {
      formData.append("code", el.codeInput.value);
    } else {
      formData.append("file", state.selectedFile, state.selectedFile.name);
    }

    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        credentials: "include", // session/auth carried via cookies
        body: formData,
      });

      if (!response.ok) {
        let detail = "Request failed.";
        try {
          const errJson = await response.json();
          detail = errJson.detail || detail;
        } catch (_) {
          /* ignore parse errors */
        }
        throw new Error(detail);
      }

      const data = await response.json();
      finishProgress();
      renderResults(normalizeResponse(data));
      showResultsPanel("results");
      showToast("success", "Review completed.");
    } catch (err) {
      finishProgress();
      showResultsPanel("empty");
      const message = err && err.message ? err.message : "Network error.";
      showToast("error", message);
    } finally {
      stopLoadingMessages();
      setBusy(false);
    }
  }

  el.reviewBtn.addEventListener("click", runReview);

  /* ============================================================
     RESPONSE NORMALIZATION
     Backend may respond with either a flat shape:
       { language, lines_of_code, file_size, cyclomatic_complexity:{maximum,average},
         time_complexity, space_complexity, summary, errors[], suggestions[] }
     or a nested shape:
       { overview:{...}, summary, issues[], suggestions[] }
     ============================================================ */
  function normalizeResponse(data) {
    const overview = data.overview || data;
    const cyclomatic = overview.cyclomatic_complexity;
    const isComplexityObject = cyclomatic && typeof cyclomatic === "object";

    return {
      language: overview.language || "—",
      linesOfCode: overview.lines_of_code ?? "—",
      fileSize: overview.file_size ?? "—",
      complexityMax: isComplexityObject ? cyclomatic.maximum : cyclomatic ?? "—",
      complexityAvg: isComplexityObject ? cyclomatic.average : "—",
      timeComplexity: data.time_complexity || overview.estimated_time_complexity || "—",
      spaceComplexity: data.space_complexity || overview.estimated_space_complexity || "—",
      summary: data.summary || "No summary was returned for this review.",
      errors: data.errors || data.issues || [],
      suggestions: data.suggestions || [],
    };
  }

  /* ============================================================
     RENDER RESULTS
     ============================================================ */
  function complexityTone(value) {
    if (value === "—" || value === null || value === undefined) return { color: "var(--text-muted)", label: "—" };
    const n = Number(value);
    if (Number.isNaN(n)) return { color: "var(--text-muted)", label: String(value) };
    if (n <= 5) return { color: "var(--success)", label: "Low" };
    if (n <= 10) return { color: "var(--warning)", label: "Moderate" };
    return { color: "var(--error)", label: "High" };
  }

  function gaugeSVG(value) {
    const n = Number(value);
    const safe = Number.isNaN(n) ? 0 : n;
    const max = 30; // visual ceiling for the ring
    const pct = Math.min(safe / max, 1);
    const r = 18;
    const c = 2 * Math.PI * r;
    const offset = c - pct * c;
    const tone = complexityTone(value);
    return `
      <div class="gauge-wrap">
        <svg width="44" height="44" viewBox="0 0 44 44">
          <circle class="gauge-track" cx="22" cy="22" r="${r}"></circle>
          <circle class="gauge-value-ring" cx="22" cy="22" r="${r}"
            stroke="${tone.color}"
            stroke-dasharray="${c}"
            stroke-dashoffset="${c}"
            data-final-offset="${offset}"></circle>
        </svg>
        <span class="gauge-num">${Number.isNaN(n) ? "—" : safe}</span>
      </div>
    `;
  }

  function metricCard({ icon, label, value, gauge }) {
    const card = document.createElement("div");
    card.className = "metric-card" + (gauge ? " metric-card-gauge" : "");
    card.innerHTML = gauge
      ? `${gaugeSVG(value)}<div class="metric-body"><div class="metric-label">${label}</div><div class="metric-value">${complexityTone(value).label}</div></div>`
      : `<div class="metric-icon"><i data-lucide="${icon}"></i></div><div class="metric-body"><div class="metric-label">${label}</div><div class="metric-value">${escapeHTML(String(value))}</div></div>`;
    return card;
  }

  function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderResults(r) {
    // Overview grid
    el.overviewGrid.innerHTML = "";
    const cards = [
      metricCard({ icon: "code-2", label: "Language", value: LANGUAGE_LABEL[r.language] || r.language }),
      metricCard({ icon: "align-left", label: "Lines of Code", value: r.linesOfCode }),
      metricCard({ icon: "database", label: "File Size", value: typeof r.fileSize === "number" ? `${r.fileSize} MB` : r.fileSize }),
      metricCard({ label: "Max Complexity", value: r.complexityMax, gauge: true }),
      metricCard({ icon: "activity", label: "Avg Complexity", value: r.complexityAvg }),
      metricCard({ icon: "clock", label: "Time Complexity", value: r.timeComplexity }),
      metricCard({ icon: "layers", label: "Space Complexity", value: r.spaceComplexity }),
    ];
    cards.forEach((c, idx) => {
      c.style.animationDelay = `${idx * 45}ms`;
      el.overviewGrid.appendChild(c);
    });

    // Summary
    el.summaryBody.textContent = r.summary;

    // Errors
    renderIssueList(el.errorsList, r.errors.slice(0, 10), {
      emptyText: "No significant issues detected.",
      icon: "octagon-alert",
    });
    el.errorsCount.textContent = String(Math.min(r.errors.length, 10));

    // Suggestions
    renderIssueList(el.suggestionsList, r.suggestions.slice(0, 5), {
      emptyText: "No major improvements suggested.",
      icon: "lightbulb",
    });
    el.suggestionsCount.textContent = String(Math.min(r.suggestions.length, 5));

    if (window.lucide) window.lucide.createIcons();

    // Animate gauge rings after paint
    requestAnimationFrame(() => {
      document.querySelectorAll(".gauge-value-ring").forEach((ring) => {
        const finalOffset = ring.getAttribute("data-final-offset");
        requestAnimationFrame(() => {
          ring.style.strokeDashoffset = finalOffset;
        });
      });
    });
  }

  function renderIssueList(container, items, { emptyText, icon }) {
    container.innerHTML = "";
    if (!items || items.length === 0) {
      const p = document.createElement("p");
      p.className = "issue-empty";
      p.textContent = emptyText;
      container.appendChild(p);
      return;
    }
    items.forEach((item, idx) => {
      const row = document.createElement("div");
      row.className = "issue-item";
      row.style.animationDelay = `${idx * 50}ms`;
      row.innerHTML = `
        <div class="issue-icon"><i data-lucide="${icon}"></i></div>
        <div class="issue-body">
          <div class="issue-title">${escapeHTML(item.title || "Untitled")}</div>
          <div class="issue-desc">${escapeHTML(item.description || "")}</div>
        </div>
      `;
      container.appendChild(row);
    });
  }

  /* ============================================================
     INIT
     ============================================================ */
  showResultsPanel("empty");
})();