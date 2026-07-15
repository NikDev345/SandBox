/**
 * ============================================================
 * pro_cons_generator.js
 * Pro & Cons Generator — SandBox AI Platform
 * Frontend-only implementation with realistic mock data.
 * Future-ready: replace runAnalysis() with real API call.
 * ============================================================
 *
 * API endpoint (future):
 *   POST /pro_cons/generate
 *   Body: { topic, context, analysis_depth }
 *   Response: ProConsResponse (see schemas below)
 *
 * ============================================================
 */


/* ════════════════════════════════════════════════════════════
   EXAMPLE TOPICS
════════════════════════════════════════════════════════════ */

const EXAMPLE_TOPICS = [
  "Should I buy a MacBook Pro?",
  "React vs Angular",
  "Should I move to Australia?",
  "Start an online textile business",
  "Buy an electric vehicle",
  "Mechanical Keyboard — worth it?",
  "Learn Rust in 2026",
  "iPhone vs Samsung Galaxy",
];

/* ════════════════════════════════════════════════════════════
   LOADING MESSAGES
════════════════════════════════════════════════════════════ */

const LOADING_MESSAGES = [
  "Understanding your request…",
  "Collecting comparison points…",
  "Analyzing advantages…",
  "Analyzing disadvantages…",
  "Preparing recommendation…",
  "Finalizing report…",
];

/* ════════════════════════════════════════════════════════════
   STATE
════════════════════════════════════════════════════════════ */

const state = {
  currentData: null,         // ProConsResponse
  filteredPros: [],
  filteredCons: [],
  searchQuery: "",
  impactFilter: "all",
  contentFilter: "all",
  sortMode: "original",
  allExpanded: false,
  exampleIndex: 0,
};

/* ════════════════════════════════════════════════════════════
   ELEMENT REFERENCES
════════════════════════════════════════════════════════════ */

const $ = (id) => document.getElementById(id);

const el = {
  root: $("pc-root"),
  topicInput: $("pc-topic-input"),
  charCount: $("pc-char-count"),
  wordCount: $("pc-word-count"),
  pasteBtn: $("pc-paste-btn"),
  clearBtn: $("pc-clear-btn"),
  exampleBtn: $("pc-example-btn"),
  settingsToggle: $("pc-settings-toggle"),
  settingsPanel: $("pc-settings-panel"),
  generateBtn: $("pc-generate-btn"),
  emptyState: $("pc-empty-state"),
  loadingState: $("pc-loading-state"),
  loadingMessage: $("pc-loading-message"),
  progressFill: $("pc-progress-fill"),
  results: $("pc-results"),
  errorState: $("pc-error-state"),
  errorMsg: $("pc-error-msg"),
  // Summary
  summaryTopic: $("pc-summary-topic"),
  summaryText: $("pc-summary-text"),
  verdictBadge: $("pc-verdict-badge"),
  // Stats
  statPros: $("stat-pros"),
  statCons: $("stat-cons"),
  statScore: $("stat-score"),
  statConfidence: $("stat-confidence"),
  statRisk: $("stat-risk"),
  recoIcon: $("pc-reco-icon"),
  // Tables
  prosTbody: $("pc-pros-tbody"),
  consTbody: $("pc-cons-tbody"),
  prosCount: $("pc-pros-count"),
  consCount: $("pc-cons-count"),
  prosEmpty: $("pc-pros-empty"),
  consEmpty: $("pc-cons-empty"),
  // Recommendation
  recoSummary: $("pc-reco-summary-text"),
  recoRecommendation: $("pc-reco-recommendation-text"),
  recoVerdict: $("pc-reco-verdict-text"),
  recoMeta: $("pc-reco-meta"),
  confidenceFill: $("pc-confidence-fill"),
  confidencePct: $("pc-confidence-pct"),
  // Filter / Search
  searchInput: $("pc-search"),
  searchClear: $("pc-search-clear"),
  sortSelect: $("pc-sort"),
  // Toast container
  toastContainer: $("pc-toast-container"),
};

/* ════════════════════════════════════════════════════════════
   INITIALISE
════════════════════════════════════════════════════════════ */

function init() {
  bindInputEvents();
  bindSettingsEvents();
  bindToolbarEvents();
  bindFilterEvents();
  bindSearchEvents();
  bindEmptyStateEvents();
  bindErrorStateEvents();
  showPhase("empty");
}

/* ════════════════════════════════════════════════════════════
   PHASE MANAGEMENT
════════════════════════════════════════════════════════════ */

function showPhase(phase) {
  // Hide all
  el.emptyState.hidden = true;
  el.loadingState.hidden = true;
  el.results.hidden = true;
  el.errorState.hidden = true;

  switch (phase) {
    case "empty":
      el.emptyState.hidden = false;
      break;
    case "loading":
      el.loadingState.hidden = false;
      break;
    case "results":
      el.results.hidden = false;
      break;
    case "error":
      el.errorState.hidden = false;
      break;
  }
}

/* ════════════════════════════════════════════════════════════
   INPUT EVENTS
════════════════════════════════════════════════════════════ */

function bindInputEvents() {
  // Character / word counter
  el.topicInput.addEventListener("input", () => {
    const val = el.topicInput.value;
    el.charCount.textContent = val.length;
    el.wordCount.textContent = val.trim() === "" ? 0 : val.trim().split(/\s+/).length;
    el.generateBtn.disabled = val.trim().length < 3;
  });

  // Paste from clipboard
  el.pasteBtn.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      el.topicInput.value = text;
      el.topicInput.dispatchEvent(new Event("input"));
      showToast("Pasted from clipboard", "success");
    } catch {
      showToast("Clipboard access denied. Paste manually.", "error");
    }
  });

  // Clear
  el.clearBtn.addEventListener("click", () => {
    el.topicInput.value = "";
    el.topicInput.dispatchEvent(new Event("input"));
    el.topicInput.focus();
  });

  // Load example
  el.exampleBtn.addEventListener("click", loadNextExample);

  // Generate
  el.generateBtn.addEventListener("click", runAnalysis);

  // Allow Ctrl+Enter to generate
  el.topicInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!el.generateBtn.disabled) runAnalysis();
    }
  });
}

function loadNextExample() {
  const topic = EXAMPLE_TOPICS[state.exampleIndex % EXAMPLE_TOPICS.length];
  el.topicInput.value = topic;
  el.topicInput.dispatchEvent(new Event("input"));
  state.exampleIndex++;
  showToast(`Loaded example: "${topic}"`, "info");
}

/* ════════════════════════════════════════════════════════════
   SETTINGS EVENTS
════════════════════════════════════════════════════════════ */

function bindSettingsEvents() {
  el.settingsToggle.addEventListener("click", () => {
    const isOpen = el.settingsToggle.getAttribute("aria-expanded") === "true";
    el.settingsToggle.setAttribute("aria-expanded", String(!isOpen));
    el.settingsPanel.hidden = isOpen;
  });
}

/* ════════════════════════════════════════════════════════════
   ANALYSIS (MOCK SIMULATION)
════════════════════════════════════════════════════════════ */

/**
 * runAnalysis — simulates an AI API call with loading states.
 *
 * FUTURE INTEGRATION:
 * Replace the mock timeout below with:
 *
 *   const resp = await fetch('/pro_cons/generate', {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
 *     body: JSON.stringify({
 *       topic: el.topicInput.value.trim(),
 *       context: null,
 *       analysis_depth: $('pc-depth').value,
 *     })
 *   });
 *   const data = await resp.json();
 *   renderResults(data);
 */
async function runAnalysis() {
  const topic = el.topicInput.value.trim();
  if (topic.length < 3) return;

  el.generateBtn.disabled = true;
  el.topicInput.disabled = true;

  showPhase("loading");
  const loadingAnim = animateLoading(); // fires alongside the fetch, not before it

  try {
    const [response] = await Promise.all([
      fetch("/pro_cons/generate", {
        method: "POST",
        credentials: "include",              // ← sends the httpOnly session cookie automatically
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic,
          context: null,
          analysis_depth: $("pc-depth").value,
        }),
      }),
      loadingAnim,
    ]);

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    data.topic = data.topic || topic;

    state.currentData = data;
    renderResults(data);
    showPhase("results");
    showToast("Analysis complete!", "success");
  } catch (err) {
    el.errorMsg.textContent = err.message || "Unable to generate analysis. Please try again.";
    showPhase("error");
  } finally {
    el.topicInput.disabled = false;
    el.generateBtn.disabled = false;
  }
}

async function animateLoading() {
  return new Promise((resolve) => {
    let step = 0;
    const totalSteps = LOADING_MESSAGES.length;
    const stepDuration = 500; // ms per message step

    el.loadingMessage.textContent = LOADING_MESSAGES[0];
    el.progressFill.style.width = "8%";

    const interval = setInterval(() => {
      step++;
      if (step >= totalSteps) {
        clearInterval(interval);
        el.progressFill.style.width = "100%";
        setTimeout(resolve, 300);
        return;
      }
      el.loadingMessage.textContent = LOADING_MESSAGES[step];
      el.progressFill.style.width = `${Math.round(((step + 1) / totalSteps) * 100)}%`;
    }, stepDuration);
  });
}

/* ════════════════════════════════════════════════════════════
   RENDER RESULTS
════════════════════════════════════════════════════════════ */

function renderResults(data) {
  // Summary card
  el.summaryTopic.textContent = data.topic;
  el.summaryText.textContent = data.summary;

  // Verdict badge on summary
  el.verdictBadge.innerHTML = renderVerdictBadge(data.recommendation.verdict);

  // Stats
  el.statPros.textContent = data.pros.length;
  el.statCons.textContent = data.cons.length;

  const score = computeScore(data);
  el.statScore.textContent = `${score}%`;

  el.statConfidence.textContent = `${data.recommendation.confidence_score}%`;
  el.statRisk.textContent = capitalize(data.recommendation.risk_level);

  // Recommendation card
  el.recoSummary.textContent = data.recommendation.summary;
  el.recoRecommendation.textContent = data.recommendation.recommendation;
  el.recoVerdict.textContent = data.recommendation.verdict;
  el.recoIcon.innerHTML = getVerdictIcon(data.recommendation.verdict);
  el.recoMeta.innerHTML = `
    ${renderRiskBadge(data.recommendation.risk_level)}
  `;

  // Confidence bar (delayed for CSS transition)
  el.confidencePct.textContent = `${data.recommendation.confidence_score}%`;
  requestAnimationFrame(() => {
    el.confidenceFill.style.width = `${data.recommendation.confidence_score}%`;
  });

  // Reset filters and render tables
  state.searchQuery = "";
  state.impactFilter = "all";
  state.contentFilter = "all";
  state.sortMode = "original";
  el.searchInput.value = "";
  el.sortSelect.value = "original";
  document.querySelectorAll(".pc-filter-chip").forEach((c) => {
    c.classList.remove("pc-filter-chip--active");
    if (c.dataset.impact === "all" || c.dataset.content === "all") {
      c.classList.add("pc-filter-chip--active");
    }
  });

  applyFiltersAndRender();
}

function computeScore(data) {
  // Simple heuristic: high-impact pros vs high-impact cons ratio
  const highPros = data.pros.filter((p) => p.impact === "high").length;
  const highCons = data.cons.filter((c) => c.impact === "high").length;
  const total = data.pros.length + data.cons.length;
  const base = Math.round((data.pros.length / total) * 100);
  const adjustment = (highPros - highCons) * 3;
  return Math.min(100, Math.max(0, base + adjustment));
}

/* ════════════════════════════════════════════════════════════
   FILTER, SEARCH, SORT
════════════════════════════════════════════════════════════ */

function applyFiltersAndRender() {
  if (!state.currentData) return;

  const { pros, cons } = state.currentData;
  let filteredPros = [...pros];
  let filteredCons = [...cons];

  // Content filter
  const showPros = state.contentFilter === "all" || state.contentFilter === "pros";
  const showCons = state.contentFilter === "all" || state.contentFilter === "cons";

  // Impact filter
  if (state.impactFilter !== "all") {
    filteredPros = filteredPros.filter((p) => (p.impact || '').toLowerCase() === state.impactFilter);
    filteredCons = filteredCons.filter((c) => (c.impact || '').toLowerCase() === state.impactFilter);
  }

  // Search
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    filteredPros = filteredPros.filter(
      (p) => p.title.toLowerCase().includes(q) || p.description.toLowerCase().includes(q)
    );
    filteredCons = filteredCons.filter(
      (c) => c.title.toLowerCase().includes(q) || c.description.toLowerCase().includes(q)
    );
  }

  // Sort
  const sortFn = getSortFn(state.sortMode);
  filteredPros.sort(sortFn);
  filteredCons.sort(sortFn);

  state.filteredPros = filteredPros;
  state.filteredCons = filteredCons;

  // Render tables
  renderTable(el.prosTbody, el.prosEmpty, el.prosCount, filteredPros, "pros", showPros);
  renderTable(el.consTbody, el.consEmpty, el.consCount, filteredCons, "cons", showCons);
}

function getSortFn(mode) {
    const impactOrder = { high: 0, medium: 1, low: 2 };
    if (mode === "impact") return (a, b) =>
        impactOrder[(a.impact || '').toLowerCase()] - impactOrder[(b.impact || '').toLowerCase()];
    if (mode === "alpha")  return (a, b) => a.title.localeCompare(b.title);
    return () => 0; // original
}

function renderTable(tbody, emptyEl, countEl, items, type, visible) {
  const card = type === "pros" ? document.getElementById("pc-pros-card") : document.getElementById("pc-cons-card");
  if (!visible) {
    card.style.display = "none";
    return;
  }
  card.style.display = "";

  countEl.textContent = items.length;
  tbody.innerHTML = "";

  if (items.length === 0) {
    emptyEl.hidden = false;
    return;
  }
  emptyEl.hidden = true;

  items.forEach((item, i) => {
    const tr = document.createElement("tr");
    tr.className = "pc-tr";
    tr.setAttribute("data-impact", item.impact);
    tr.setAttribute("data-type", type);
    tr.style.animationDelay = `${i * 30}ms`;

    const titleHtml = highlight(item.title, state.searchQuery);
    const descHtml = highlight(item.description, state.searchQuery);

    tr.innerHTML = `
      <td class="pc-td pc-td-num">${i + 1}</td>
      <td class="pc-td">
        <div class="pc-td-title">${titleHtml}</div>
        <div class="pc-td-desc">${descHtml}</div>
      </td>
      <td class="pc-td pc-td-impact">
        <span class="pc-impact-badge pc-impact-badge--${(item.impact || '').toLowerCase()}">${capitalize(item.impact)}</span>
      </td>
    `;

    // Toggle expand on click
    tr.addEventListener("click", () => {
      tr.classList.toggle("is-expanded");
    });

    tbody.appendChild(tr);
  });
}

function highlight(text, query) {
  if (!query) return escapeHtml(text);
  const escaped = escapeHtml(text);
  const escapedQuery = escapeHtml(query).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return escaped.replace(
    new RegExp(`(${escapedQuery})`, "gi"),
    '<mark class="pc-highlight">$1</mark>'
  );
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ════════════════════════════════════════════════════════════
   FILTER BAR EVENTS
════════════════════════════════════════════════════════════ */

function bindFilterEvents() {
  // Impact filter chips
  document.querySelectorAll("[data-impact]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-impact]").forEach((b) =>
        b.classList.remove("pc-filter-chip--active")
      );
      btn.classList.add("pc-filter-chip--active");
      state.impactFilter = btn.dataset.impact;
      applyFiltersAndRender();
    });
  });

  // Content filter chips
  document.querySelectorAll("[data-content]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-content]").forEach((b) =>
        b.classList.remove("pc-filter-chip--active")
      );
      btn.classList.add("pc-filter-chip--active");
      state.contentFilter = btn.dataset.content;
      applyFiltersAndRender();
    });
  });

  // Sort
  el.sortSelect.addEventListener("change", () => {
    state.sortMode = el.sortSelect.value;
    applyFiltersAndRender();
  });

  // Reset filters
  $("pc-reset-filters").addEventListener("click", () => {
    state.impactFilter = "all";
    state.contentFilter = "all";
    state.sortMode = "original";
    state.searchQuery = "";
    el.searchInput.value = "";
    el.sortSelect.value = "original";
    el.searchClear.hidden = true;
    document.querySelectorAll(".pc-filter-chip").forEach((c) => {
      c.classList.remove("pc-filter-chip--active");
      if (c.dataset.impact === "all" || c.dataset.content === "all") {
        c.classList.add("pc-filter-chip--active");
      }
    });
    applyFiltersAndRender();
  });
}

/* ════════════════════════════════════════════════════════════
   SEARCH EVENTS
════════════════════════════════════════════════════════════ */

function bindSearchEvents() {
  el.searchInput.addEventListener("input", () => {
    state.searchQuery = el.searchInput.value.trim();
    el.searchClear.hidden = state.searchQuery === "";
    applyFiltersAndRender();
  });

  el.searchClear.addEventListener("click", () => {
    el.searchInput.value = "";
    state.searchQuery = "";
    el.searchClear.hidden = true;
    applyFiltersAndRender();
    el.searchInput.focus();
  });
}

/* ════════════════════════════════════════════════════════════
   TOOLBAR EVENTS
════════════════════════════════════════════════════════════ */

function bindToolbarEvents() {
  // Copy entire report
  $("tb-copy-all").addEventListener("click", () => {
    const text = buildReportText();
    copyToClipboard(text, "Entire report copied!");
  });

  // Copy pros
  $("tb-copy-pros").addEventListener("click", () => {
    if (!state.currentData) return;
    const text = state.currentData.pros
      .map((p, i) => `${i + 1}. ${p.title} (${capitalize(p.impact)} impact)\n   ${p.description}`)
      .join("\n\n");
    copyToClipboard(text, "Pros copied!");
  });

  // Copy cons
  $("tb-copy-cons").addEventListener("click", () => {
    if (!state.currentData) return;
    const text = state.currentData.cons
      .map((c, i) => `${i + 1}. ${c.title} (${capitalize(c.impact)} impact)\n   ${c.description}`)
      .join("\n\n");
    copyToClipboard(text, "Cons copied!");
  });

  // JSON export
  $("tb-download-json").addEventListener("click", exportJSON);

  // PDF export
  $("tb-download-pdf").addEventListener("click", exportPDF);

  // Print
  $("tb-print").addEventListener("click", () => window.print());

  // Expand all
  $("tb-expand-all").addEventListener("click", () => {
    document.querySelectorAll(".pc-tr").forEach((tr) => tr.classList.add("is-expanded"));
    state.allExpanded = true;
    showToast("All rows expanded", "info");
  });

  // Collapse all
  $("tb-collapse-all").addEventListener("click", () => {
    document.querySelectorAll(".pc-tr").forEach((tr) => tr.classList.remove("is-expanded"));
    state.allExpanded = false;
    showToast("All rows collapsed", "info");
  });

  // Regenerate
  $("tb-regenerate").addEventListener("click", () => {
    if (el.topicInput.value.trim().length >= 3) {
      runAnalysis();
    } else {
      showToast("Enter a topic first", "error");
    }
  });
}

/* ════════════════════════════════════════════════════════════
   EMPTY & ERROR STATE EVENTS
════════════════════════════════════════════════════════════ */

function bindEmptyStateEvents() {
  $("pc-load-example-empty").addEventListener("click", () => {
    loadNextExample();
    el.topicInput.focus();
  });
}

function bindErrorStateEvents() {
  $("pc-retry-btn").addEventListener("click", runAnalysis);
  $("pc-error-example-btn").addEventListener("click", () => {
    loadNextExample();
    showPhase("empty");
  });
}

/* ════════════════════════════════════════════════════════════
   EXPORT — JSON
════════════════════════════════════════════════════════════ */

function exportJSON() {
  if (!state.currentData) {
    showToast("No data to export", "error");
    return;
  }

  const payload = {
    generated_at: new Date().toISOString(),
    ...state.currentData,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `pro-cons-${slugify(state.currentData.topic)}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast("JSON downloaded!", "success");
}

/* ════════════════════════════════════════════════════════════
   EXPORT — PDF (frontend, no library required)
════════════════════════════════════════════════════════════ */

function exportPDF() {
  if (!state.currentData) {
    showToast("No data to export", "error");
    return;
  }

  const d = state.currentData;
  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const prosRows = d.pros
    .map(
      (p, i) => `
      <tr>
        <td style="padding:8px 12px;color:#94a3b8;font-size:12px;border-bottom:1px solid #1e293b;text-align:center">${i + 1}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #1e293b;">
          <div style="font-size:13px;font-weight:600;color:#f1f5f9;margin-bottom:3px">${p.title}</div>
          <div style="font-size:11px;color:#94a3b8;line-height:1.5">${p.description}</div>
        </td>
        <td style="padding:8px 12px;border-bottom:1px solid #1e293b;text-align:right">
          <span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:99px;background:${impactBgPdf(p.impact)};color:${impactColorPdf(p.impact)}">${capitalize(p.impact)}</span>
        </td>
      </tr>`
    )
    .join("");

  const consRows = d.cons
    .map(
      (c, i) => `
      <tr>
        <td style="padding:8px 12px;color:#94a3b8;font-size:12px;border-bottom:1px solid #1e293b;text-align:center">${i + 1}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #1e293b;">
          <div style="font-size:13px;font-weight:600;color:#f1f5f9;margin-bottom:3px">${c.title}</div>
          <div style="font-size:11px;color:#94a3b8;line-height:1.5">${c.description}</div>
        </td>
        <td style="padding:8px 12px;border-bottom:1px solid #1e293b;text-align:right">
          <span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:99px;background:${impactBgPdf(c.impact)};color:${impactColorPdf(c.impact)}">${capitalize(c.impact)}</span>
        </td>
      </tr>`
    )
    .join("");

  const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <title>Pro & Cons: ${d.topic}</title>
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #09090b; color: #e2e8f0; padding: 48px; line-height: 1.6; }
        h1 { font-size: 28px; font-weight: 800; letter-spacing: -0.04em; color: #f8fafc; }
        h2 { font-size: 16px; font-weight: 700; color: #f1f5f9; margin-bottom: 14px; letter-spacing: -0.02em; }
        .eyebrow { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
        .section { margin-bottom: 36px; }
        table { width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 10px; overflow: hidden; }
        thead { background: #1e293b; }
        th { padding: 10px 12px; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; text-align: left; }
        .summary-box { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 20px; margin-bottom: 12px; }
        .footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid #1e293b; font-size: 11px; color: #475569; display: flex; justify-content: space-between; }
        @media print { body { background: white; color: black; } }
      </style>
    </head>
    <body>
      <div class="section">
        <div class="eyebrow">Pro &amp; Cons Analysis Report</div>
        <h1>${d.topic}</h1>
        <p style="color:#94a3b8;font-size:13px;margin-top:8px">${date}</p>
      </div>

      <div class="section">
        <h2>Summary</h2>
        <div class="summary-box">
          <p style="font-size:13px;color:#cbd5e1;line-height:1.7">${d.summary}</p>
        </div>
      </div>

      <div class="section">
        <h2 style="color:#4ade80">✓ Advantages (${d.pros.length})</h2>
        <table>
          <thead><tr><th style="width:36px">#</th><th>Title &amp; Description</th><th style="text-align:right;width:80px">Impact</th></tr></thead>
          <tbody>${prosRows}</tbody>
        </table>
      </div>

      <div class="section">
        <h2 style="color:#f87171">✗ Disadvantages (${d.cons.length})</h2>
        <table>
          <thead><tr><th style="width:36px">#</th><th>Title &amp; Description</th><th style="text-align:right;width:80px">Impact</th></tr></thead>
          <tbody>${consRows}</tbody>
        </table>
      </div>

      <div class="section">
        <h2>Recommendation</h2>
        <div class="summary-box">
          <p style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:6px">Summary</p>
          <p style="font-size:13px;color:#cbd5e1;line-height:1.7;margin-bottom:14px">${d.recommendation.summary}</p>
          <p style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:6px">Recommendation</p>
          <p style="font-size:13px;color:#cbd5e1;line-height:1.7;margin-bottom:14px">${d.recommendation.recommendation}</p>
          <p style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:6px">Verdict</p>
          <p style="font-size:13px;color:#cbd5e1;line-height:1.7">${d.recommendation.verdict}</p>
          <div style="margin-top:16px;display:flex;gap:16px">
            <span style="font-size:12px;color:#94a3b8">Risk Level: <strong style="color:#f1f5f9">${capitalize(d.recommendation.risk_level)}</strong></span>
            <span style="font-size:12px;color:#94a3b8">Confidence: <strong style="color:#f1f5f9">${d.recommendation.confidence_score}%</strong></span>
          </div>
        </div>
      </div>

      <div class="footer">
        <span>Generated by SandBox AI — Pro &amp; Cons Generator</span>
        <span>${date}</span>
      </div>
    </body>
    </html>`;

  const win = window.open("", "_blank");
  if (!win) {
    showToast("Popup blocked. Allow popups and try again.", "error");
    return;
  }
  win.document.write(html);
  win.document.close();
  win.addEventListener("load", () => {
    win.print();
  });
  showToast("PDF export ready — print to save as PDF.", "success");
}

function impactBgPdf(impact) {
  return { high: "rgba(239,68,68,0.15)", medium: "rgba(245,158,11,0.15)", low: "rgba(99,102,241,0.15)" }[impact];
}
function impactColorPdf(impact) {
  return { high: "#f87171", medium: "#fcd34d", low: "#a5b4fc" }[impact];
}

/* ════════════════════════════════════════════════════════════
   COPY HELPERS
════════════════════════════════════════════════════════════ */

async function copyToClipboard(text, successMsg) {
  try {
    await navigator.clipboard.writeText(text);
    showToast(successMsg, "success");
  } catch {
    // Fallback for non-secure contexts
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    showToast(successMsg, "success");
  }
}

function buildReportText() {
  if (!state.currentData) return "";
  const d = state.currentData;
  const lines = [
    `PRO & CONS ANALYSIS: ${d.topic}`,
    "=".repeat(60),
    "",
    "SUMMARY",
    d.summary,
    "",
    `PROS (${d.pros.length})`,
    "-".repeat(40),
    ...d.pros.map((p, i) => `${i + 1}. ${p.title} [${capitalize(p.impact)} Impact]\n   ${p.description}`),
    "",
    `CONS (${d.cons.length})`,
    "-".repeat(40),
    ...d.cons.map((c, i) => `${i + 1}. ${c.title} [${capitalize(c.impact)} Impact]\n   ${c.description}`),
    "",
    "RECOMMENDATION",
    "-".repeat(40),
    d.recommendation.recommendation,
    "",
    `Verdict: ${d.recommendation.verdict}`,
    `Risk Level: ${capitalize(d.recommendation.risk_level)}`,
    `Confidence: ${d.recommendation.confidence_score}%`,
    "",
    `Generated: ${new Date().toLocaleString()}`,
  ];
  return lines.join("\n");
}

/* ════════════════════════════════════════════════════════════
   BADGE HELPERS
════════════════════════════════════════════════════════════ */

function getVerdictIcon(verdict) {
  const v = (verdict || "").toLowerCase();
  if (v.includes("avoid") || v.includes("no")) {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
  }
  if (v.includes("caution") || v.includes("condition") || v.includes("consider")) {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>`;
  }
  if (v.includes("recommend") || v.includes("yes") || v.includes("go for")) {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
  }
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="8"/><line x1="12" y1="12" x2="12" y2="16"/></svg>`;
}

function renderVerdictBadge(verdict) {
  const v = verdict.toLowerCase();
  let cls = "pc-verdict-badge--neutral";
  if (v.includes("recommend") || v.includes("yes") || v.includes("go for")) cls = "pc-verdict-badge--recommended";
  else if (v.includes("caution") || v.includes("condition") || v.includes("consider")) cls = "pc-verdict-badge--caution";
  else if (v.includes("avoid") || v.includes("no")) cls = "pc-verdict-badge--avoid";
  return `<span class="pc-verdict-badge ${cls}">${verdict}</span>`;
}

function renderRiskBadge(risk) {
  return `<span class="pc-risk-badge pc-risk-badge--${risk}">${capitalize(risk)} Risk</span>`;
}

/* ════════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
════════════════════════════════════════════════════════════ */

const TOAST_ICONS = {
  success: `<svg class="pc-toast-icon" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`,
  error:   `<svg class="pc-toast-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  info:    `<svg class="pc-toast-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="8"/><line x1="12" y1="12" x2="12" y2="16"/></svg>`,
};

function showToast(message, type = "info", duration = 3000) {
  const toast = document.createElement("div");
  toast.className = `pc-toast pc-toast--${type}`;
  toast.innerHTML = `${TOAST_ICONS[type]}<span>${message}</span>`;
  el.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("is-exiting");
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

/* ════════════════════════════════════════════════════════════
   UTILITY
════════════════════════════════════════════════════════════ */

function capitalize(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function slugify(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/* ════════════════════════════════════════════════════════════
   BOOT
════════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", init);