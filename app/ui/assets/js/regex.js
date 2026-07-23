/* ============================================================
   Regex Generator — Application Logic
   ============================================================ */
(() => {
  "use strict";

  const API_ENDPOINT = "/regex/generate";

  /* ---------------------------------------------------------
     DOM REFS
  --------------------------------------------------------- */
  const $ = (id) => document.getElementById(id);

  const form = $("regexForm");
  const promptInput = $("promptInput");
  const charCounter = $("charCounter");
  const testStringsInput = $("testStringsInput");
  const testCounter = $("testCounter");
  const engineSelect = $("engineSelect");
  const modeSelect = $("modeSelect");
  const generateBtn = $("generateBtn");
  const clearBtn = $("clearBtn");
  const panelRight = $("panelRight");
  const emptyState = $("emptyState");
  const loadingState = $("loadingState");
  const loadingLabel = $("loadingLabel");
  const outputState = $("outputState");

  const regexCode = $("regexCode");
  const engineBadgeLabel = $("engineBadgeLabel");
  const badgeRow = $("badgeRow");
  const explanationText = $("explanationText");
  const matchesSection = $("matchesSection");
  const matchesTableBody = $("matchesTableBody");

  const copyBtn = $("copyBtn");
  const downloadBtn = $("downloadBtn");
  const fullscreenBtn = $("fullscreenBtn");
  const fullscreenOverlay = $("fullscreenOverlay");
  const fullscreenCode = $("fullscreenCode");
  const closeFullscreen = $("closeFullscreen");

  const errorModal = $("errorModal");
  const errorMessage = $("errorMessage");
  const closeError = $("closeError");
  const errorRetryBtn = $("errorRetryBtn");

  const shortcutsModal = $("shortcutsModal");
  const shortcutsBtn = $("shortcutsBtn");
  const closeShortcuts = $("closeShortcuts");

  const cmdOverlay = $("cmdOverlay");
  const cmdPaletteBtn = $("cmdPaletteBtn");
  const cmdInput = $("cmdInput");
  const cmdResults = $("cmdResults");

  const themeToggle = $("themeToggle");
  const resizeHandle = $("resizeHandle");
  const panelLeft = $("panelLeft");
  const toastContainer = $("toastContainer");
  const mouseGlow = $("mouseGlow");

  let currentRegex = "";
  let currentEngine = "python";
  let isGenerating = false;

  /* ---------------------------------------------------------
     TOASTS
  --------------------------------------------------------- */
  const TOAST_ICONS = {
    success: '<path d="M5 13l4 4L19 7"/>',
    error: '<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/>',
    warning: '<path d="M12 9v4M12 17h.01M10.3 3.9L2.5 18a2 2 0 001.7 3h15.6a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M12 12v4"/>'
  };

  function showToast(message, type = "info", duration = 3200) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke-width="2">${TOAST_ICONS[type] || TOAST_ICONS.info}</svg>
      <span>${message}</span>
      <button class="toast-close" aria-label="Dismiss">✕</button>
    `;
    toast.style.setProperty("--toast-progress-duration", duration + "ms");
    const progressAfter = toast.querySelector(".toast-close");
    progressAfter.addEventListener("click", () => removeToast(toast));
    toastContainer.appendChild(toast);

    const timer = setTimeout(() => removeToast(toast), duration);
    toast._timer = timer;
  }

  function removeToast(toast) {
    if (!toast || !toast.parentNode) return;
    clearTimeout(toast._timer);
    toast.classList.add("removing");
    setTimeout(() => toast.remove(), 220);
  }

  /* ---------------------------------------------------------
     THEME TOGGLE
  --------------------------------------------------------- */
  themeToggle.addEventListener("click", () => {
    const html = document.documentElement;
    const isLight = html.getAttribute("data-theme") === "light";
    html.setAttribute("data-theme", isLight ? "dark" : "light");
    showToast(isLight ? "Switched to dark mode" : "Switched to light mode", "info", 1800);
  });

  /* ---------------------------------------------------------
     CHAR / TEST STRING COUNTERS + AUTORESIZE
  --------------------------------------------------------- */
  function autoResize(el, max = 260) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, max) + "px";
  }

  promptInput.addEventListener("input", () => {
    charCounter.textContent = `${promptInput.value.length} / 500`;
    autoResize(promptInput, 220);
  });

  testStringsInput.addEventListener("input", () => {
    const lines = testStringsInput.value.split("\n").map((s) => s.trim()).filter(Boolean);
    testCounter.textContent = `${lines.length} string${lines.length === 1 ? "" : "s"}`;
    autoResize(testStringsInput, 200);
  });

  /* ---------------------------------------------------------
     QUICK PROMPT CHIPS (command palette items reused as fill)
  --------------------------------------------------------- */
  document.querySelectorAll(".cmd-item[data-prompt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      promptInput.value = btn.dataset.prompt;
      promptInput.dispatchEvent(new Event("input"));
      closeCmdPalette();
      promptInput.focus();
    });
  });

  /* ---------------------------------------------------------
     CLEAR FORM
  --------------------------------------------------------- */
  clearBtn.addEventListener("click", () => {
    promptInput.value = "";
    testStringsInput.value = "";
    engineSelect.value = "python";
    modeSelect.value = "auto";
    promptInput.dispatchEvent(new Event("input"));
    testStringsInput.dispatchEvent(new Event("input"));
    autoResize(promptInput);
    autoResize(testStringsInput);
    resetOutput();
    showToast("Form cleared", "info", 1600);
  });

  function resetOutput() {
    outputState.classList.add("hidden");
    loadingState.classList.add("hidden");
    emptyState.classList.remove("hidden");
    currentRegex = "";
  }

  /* ---------------------------------------------------------
     REGEX SYNTAX HIGHLIGHTING (lightweight tokenizer)
  --------------------------------------------------------- */
  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function highlightRegex(pattern) {
    const TOKEN_RE = /(\\[dDwWsSbB0nrtfv])|(\\.)|(\[\^?(?:\\.|[^\]])*\])|(\(\?[:=!<]?|\(|\))|([*+?]|\{\d+(?:,\d*)?\})|(\^|\$)|(\|)|([\s\S])/g;
    let out = "";
    let m;
    while ((m = TOKEN_RE.exec(pattern)) !== null) {
      const [, esc, escOther, cls, grp, quant, anchor, alt, lit] = m;
      if (esc || escOther) out += `<span class="tok-escape">${escapeHtml(m[0])}</span>`;
      else if (cls) out += `<span class="tok-class">${escapeHtml(cls)}</span>`;
      else if (grp) out += `<span class="tok-group">${escapeHtml(grp)}</span>`;
      else if (quant) out += `<span class="tok-quant">${escapeHtml(quant)}</span>`;
      else if (anchor) out += `<span class="tok-anchor">${escapeHtml(anchor)}</span>`;
      else if (alt) out += `<span class="tok-alt">${escapeHtml(alt)}</span>`;
      else out += `<span class="tok-lit">${escapeHtml(lit)}</span>`;
    }
    return out || escapeHtml(pattern);
  }

  /* ---------------------------------------------------------
     FORM SUBMIT — GENERATE
  --------------------------------------------------------- */
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    generate();
  });

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      generate();
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openCmdPalette();
    }
    if (e.key === "Escape") {
      closeCmdPalette();
      closeModal(shortcutsModal);
      closeModal(errorModal);
      closeFullscreenView();
    }
  });

  async function generate() {
    if (isGenerating) return;

    const prompt = promptInput.value.trim();
    if (!prompt) {
      showToast("Please describe the regex you need", "warning");
      promptInput.focus();
      return;
    }

    const testStrings = testStringsInput.value
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const payload = {
      prompt,
      engine: engineSelect.value,
      mode: modeSelect.value,
      test_strings: testStrings.length ? testStrings : null
    };

    setGenerating(true);
    showLoading();

    try {
      const res = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        const message = (data && (data.detail || data.message)) || `Request failed with status ${res.status}`;
        throw new Error(message);
      }
      if (!data || !data.regex) {
        throw new Error("The server returned an unexpected response.");
      }

      renderOutput(data);
      showToast("Regex generated successfully", "success");
    } catch (err) {
      showError(err.message || "Something went wrong while generating the regex.");
    } finally {
      setGenerating(false);
    }
  }

  function setGenerating(state) {
    isGenerating = state;
    generateBtn.disabled = state;
    generateBtn.classList.toggle("is-loading", state);
    generateBtn.querySelector(".btn-label").textContent = state ? "Generating…" : "Generate Regex";
  }

  function showLoading() {
    emptyState.classList.add("hidden");
    outputState.classList.add("hidden");
    loadingState.classList.remove("hidden");
    panelRight.scrollTop = 0;
    const labels = [
      "Analyzing your description…",
      "Choosing the right engine syntax…",
      "Validating pattern safety…",
      "Running test strings…"
    ];
    let i = 0;
    loadingLabel.textContent = labels[0];
    clearInterval(showLoading._t);
    showLoading._t = setInterval(() => {
      i = (i + 1) % labels.length;
      loadingLabel.textContent = labels[i];
    }, 900);
  }

  function stopLoadingLabelCycle() {
    clearInterval(showLoading._t);
  }

  /* ---------------------------------------------------------
     RENDER OUTPUT
  --------------------------------------------------------- */
  const ENGINE_LABELS = {
    python: "PYTHON", javascript: "JAVASCRIPT", java: "JAVA",
    csharp: "C#", go: "GO", pcre: "PCRE"
  };
  const SOURCE_LABELS = { cache: "Cache", ai: "AI Generated", literal: "Literal Match" };

  function renderOutput(data) {
    stopLoadingLabelCycle();
    currentRegex = data.regex;
    currentEngine = data.engine || engineSelect.value;

    regexCode.innerHTML = highlightRegex(data.regex);
    engineBadgeLabel.textContent = ENGINE_LABELS[currentEngine] || currentEngine.toUpperCase();

    // Badges
    badgeRow.innerHTML = "";
    const sourceKey = (data.source || "").toLowerCase();
    const sourceTag = document.createElement("span");
    sourceTag.className = `analysis-tag tag-source-${sourceKey || "ai"}`;
    sourceTag.textContent = SOURCE_LABELS[sourceKey] || (data.source || "Generated");
    badgeRow.appendChild(sourceTag);

    const engineTag = document.createElement("span");
    engineTag.className = "analysis-tag tag-engine";
    engineTag.textContent = ENGINE_LABELS[currentEngine] || currentEngine;
    badgeRow.appendChild(engineTag);

    explanationText.textContent = data.explanation || "No explanation provided.";

    // Matches
    const matches = Array.isArray(data.matches) ? data.matches : null;
    if (matches && matches.length) {
      matchesSection.classList.remove("hidden");
      matchesTableBody.innerHTML = "";
      const anyMatch = matches.some((m) => m.matched);

      matches.forEach((m, idx) => {
        const row = document.createElement("tr");
        row.style.animationDelay = `${idx * 40}ms`;
        row.innerHTML = `
          <td class="match-input-cell">${escapeHtml(m.text)}</td>
          <td>
            <span class="match-icon ${m.matched ? "is-match" : "is-nomatch"}">
              ${m.matched
                ? '<svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg> Yes'
                : '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg> No'}
            </span>
          </td>
          <td>${m.matched ? "Valid input" : "Invalid / rejected"}</td>
        `;
        matchesTableBody.appendChild(row);
      });

      if (!anyMatch) {
        const row = document.createElement("tr");
        row.innerHTML = `<td colspan="3" style="text-align:center; color:var(--text-muted); padding:16px; font-size:var(--text-sm);">⚠ No test strings matched the pattern</td>`;
        matchesTableBody.appendChild(row);
      }
    } else {
      matchesSection.classList.add("hidden");
    }

    loadingState.classList.add("hidden");
    emptyState.classList.add("hidden");
    outputState.classList.remove("hidden");
    panelRight.scrollTop = 0;
  }

  /* ---------------------------------------------------------
     ERROR MODAL
  --------------------------------------------------------- */
  function showError(message) {
    stopLoadingLabelCycle();
    loadingState.classList.add("hidden");
    if (outputState.classList.contains("hidden")) {
      emptyState.classList.remove("hidden");
    }
    panelRight.scrollTop = 0;
    errorMessage.textContent = message;
    openModal(errorModal);
    showToast("Generation failed", "error", 2800);
  }

  closeError.addEventListener("click", () => closeModal(errorModal));
  errorRetryBtn.addEventListener("click", () => {
    closeModal(errorModal);
    generate();
  });

  /* ---------------------------------------------------------
     MODAL HELPERS
  --------------------------------------------------------- */
  function openModal(modal) {
    modal.classList.remove("hidden");
  }
  function closeModal(modal) {
    modal.classList.add("hidden");
  }
  [errorModal, shortcutsModal, cmdOverlay].forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeModal(overlay);
    });
  });

  shortcutsBtn.addEventListener("click", () => openModal(shortcutsModal));
  closeShortcuts.addEventListener("click", () => closeModal(shortcutsModal));

  /* ---------------------------------------------------------
     COMMAND PALETTE
  --------------------------------------------------------- */
  function openCmdPalette() {
    cmdOverlay.classList.remove("hidden");
    cmdInput.value = "";
    setTimeout(() => cmdInput.focus(), 30);
  }
  function closeCmdPalette() {
    cmdOverlay.classList.add("hidden");
  }
  cmdPaletteBtn.addEventListener("click", openCmdPalette);

  cmdInput.addEventListener("input", () => {
    const q = cmdInput.value.toLowerCase();
    cmdResults.querySelectorAll(".cmd-item").forEach((item) => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(q) ? "flex" : "none";
    });
  });

  /* ---------------------------------------------------------
     COPY / DOWNLOAD / FULLSCREEN
  --------------------------------------------------------- */
  copyBtn.addEventListener("click", async () => {
    if (!currentRegex) return;
    try {
      await navigator.clipboard.writeText(currentRegex);
      flashSuccess(copyBtn, "Copied!");
      showToast("Regex copied to clipboard", "success", 2000);
    } catch {
      showToast("Could not copy to clipboard", "error");
    }
  });

  function flashSuccess(btn, label) {
    const original = btn.innerHTML;
    btn.classList.add("success-flash");
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M5 13l4 4L19 7"/></svg><span>${label}</span>`;
    setTimeout(() => {
      btn.classList.remove("success-flash");
      btn.innerHTML = original;
    }, 1600);
  }

  downloadBtn.addEventListener("click", () => {
    if (!currentRegex) return;
    const blob = new Blob([currentRegex], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `regex-${currentEngine}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    flashSuccess(downloadBtn, "Saved!");
    showToast("Regex downloaded as .txt", "success", 2000);
  });

  fullscreenBtn.addEventListener("click", () => {
    if (!currentRegex) return;
    fullscreenCode.innerHTML = regexCode.innerHTML;
    fullscreenOverlay.classList.remove("hidden");
  });
  closeFullscreen.addEventListener("click", closeFullscreenView);
  fullscreenOverlay.addEventListener("click", (e) => {
    if (e.target === fullscreenOverlay) closeFullscreenView();
  });
  function closeFullscreenView() {
    fullscreenOverlay.classList.add("hidden");
  }

  /* ---------------------------------------------------------
     RESIZABLE PANEL
  --------------------------------------------------------- */
  let isResizing = false;
  resizeHandle.addEventListener("mousedown", () => {
    isResizing = true;
    resizeHandle.classList.add("dragging");
    document.body.style.userSelect = "none";
  });
  window.addEventListener("mousemove", (e) => {
    if (!isResizing) return;
    const min = 320, max = 620;
    const w = Math.min(max, Math.max(min, e.clientX));
    panelLeft.style.width = w + "px";
  });
  window.addEventListener("mouseup", () => {
    if (isResizing) {
      isResizing = false;
      resizeHandle.classList.remove("dragging");
      document.body.style.userSelect = "";
    }
  });

  /* ---------------------------------------------------------
     MOUSE GLOW
  --------------------------------------------------------- */
  document.addEventListener("mousemove", (e) => {
    mouseGlow.style.opacity = "1";
    mouseGlow.style.left = e.clientX + "px";
    mouseGlow.style.top = e.clientY + "px";
  });
  document.addEventListener("mouseleave", () => {
    mouseGlow.style.opacity = "0";
  });

  /* ---------------------------------------------------------
     FLOATING PARTICLES CANVAS
  --------------------------------------------------------- */
  (function initParticles() {
    const canvas = $("particleCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let particles = [];
    let w, h;

    function resize() {
      w = canvas.width = canvas.offsetWidth;
      h = canvas.height = canvas.offsetHeight;
    }
    function createParticles() {
      const count = Math.min(60, Math.floor((w * h) / 22000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.6 + 0.4,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        a: Math.random() * 0.5 + 0.15
      }));
    }
    function tick() {
      ctx.clearRect(0, 0, w, h);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(120,160,255,${p.a})`;
        ctx.fill();
      });
      requestAnimationFrame(tick);
    }

    resize();
    createParticles();
    tick();
    window.addEventListener("resize", () => { resize(); createParticles(); });
  })();

  /* ---------------------------------------------------------
     STICKY HEADER SHADOW ON SCROLL (right panel)
  --------------------------------------------------------- */
  panelRight.addEventListener("scroll", () => {
    document.querySelector(".app-header").classList.toggle("glass-header-scrolled", panelRight.scrollTop > 4);
  });

  /* ---------------------------------------------------------
     INIT
  --------------------------------------------------------- */
  autoResize(promptInput);
  autoResize(testStringsInput);
})();