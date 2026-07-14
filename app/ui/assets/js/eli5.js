(function () {
  "use strict";

  // ─── State ────────────────────────────────────────────────────────────────────
  const state = {
    loading: false,
    lastTopic: "",
    abortController: null,
  };

  // ─── Element refs ─────────────────────────────────────────────────────────────
  const root          = document.querySelector(".eli5-tool");
  if (!root) return;

  const topicInput    = root.querySelector("#eli5-topic-input");
  const charCount     = root.querySelector("#eli5-char-count");
  const explainBtn    = root.querySelector("#eli5-explain-btn");
  const loadingEl     = root.querySelector("#eli5-loading");
  const emptyEl       = root.querySelector("#eli5-empty");
  const outputCard    = root.querySelector("#eli5-output-card");
  const outputTitle   = root.querySelector("#eli5-output-title");
  const summaryText   = root.querySelector("#eli5-summary-text");
  const explanationEl = root.querySelector("#eli5-explanation-text");
  const copyBtn       = root.querySelector("#eli5-copy-btn");
  const againBtn      = root.querySelector("#eli5-again-btn");
  const clearBtn      = root.querySelector("#eli5-clear-btn");

  // ─── Toast ────────────────────────────────────────────────────────────────────
  function toast(message) {
    const id = "eli5-toast";
    let el = document.getElementById(id);
    if (!el) {
      el = document.createElement("div");
      el.id = id;
      Object.assign(el.style, {
        position: "fixed", right: "16px", bottom: "16px",
        padding: "10px 14px", background: "rgba(0,0,0,0.82)",
        color: "white", borderRadius: "8px", zIndex: 99999,
        maxWidth: "320px", fontSize: "13px", transition: "opacity 0.2s",
      });
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.style.opacity = "1";
    el.style.display = "block";
    clearTimeout(el._timer);
    el._timer = setTimeout(() => { el.style.display = "none"; }, 3000);
  }

  // ─── UI state helpers ─────────────────────────────────────────────────────────
  function showLoading() {
    if (loadingEl)  loadingEl.hidden  = false;
    if (emptyEl)    emptyEl.hidden    = true;
    if (outputCard) outputCard.hidden = true;
  }

  function showEmpty() {
    if (loadingEl)  loadingEl.hidden  = true;
    if (emptyEl)    emptyEl.hidden    = false;
    if (outputCard) outputCard.hidden = true;
  }

  function showOutput() {
    if (loadingEl)  loadingEl.hidden  = true;
    if (emptyEl)    emptyEl.hidden    = true;
    if (outputCard) outputCard.hidden = false;
  }

  function setExplainBtnLoading(loading) {
    state.loading = loading;
    if (!explainBtn) return;
    explainBtn.disabled = loading;
    const textEl = explainBtn.querySelector(".eli5-btn-text");
    if (textEl) textEl.textContent = loading ? "Explaining…" : "Explain";
  }

  // ─── Character counter ────────────────────────────────────────────────────────
  function updateCharCount() {
    if (!topicInput || !charCount) return;
    charCount.textContent = `${topicInput.value.length} / 300`;
  }

  // ─── Markdown → HTML (bold, italic only) ─────────────────────────────────────
  function parseMarkdown(text) {
    return (text || "")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+?)\*/g,  "<em>$1</em>");
  }

  // ─── Render paragraphs with markdown ─────────────────────────────────────────
  function renderParagraphs(container, text) {
    container.innerHTML = "";
    if (!text) return;
    // Split on one or more blank lines; skip whitespace-only chunks
    text.split(/\n{2,}/).forEach((block) => {
      const trimmed = block.trim();
      if (!trimmed) return;
      // Each block becomes one <p>; internal single newlines become <br>
      const p = document.createElement("p");
      p.innerHTML = parseMarkdown(trimmed.replace(/\n/g, "<br>"));
      container.appendChild(p);
    });
  }

  // ─── Render full output ───────────────────────────────────────────────────────
  function renderOutput(topic, data) {
    if (outputTitle)   outputTitle.textContent = topic;
    if (summaryText)   summaryText.innerHTML   = parseMarkdown(data.summary || "");
    if (explanationEl) renderParagraphs(explanationEl, data.explanation || "");
    showOutput();
    outputCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ─── Error message helper ─────────────────────────────────────────────────────
  function errorMessage(status, bodyText) {
    const map = {
      400: "Invalid request. Please check your input.",
      401: "You must be logged in to use this tool.",
      403: "Access denied.",
      404: "Service not found. Please try again later.",
      429: "Too many requests. Please slow down.",
      500: "Server error. Please try again.",
      502: "Service unavailable. Please try again.",
      503: "Service temporarily unavailable.",
      504: "Request timed out on the server.",
    };
    if (bodyText) {
      try {
        const parsed = JSON.parse(bodyText);
        if (parsed.detail) return parsed.detail;
      } catch (_) {}
      if (bodyText.length < 120) return bodyText;
    }
    return map[status] || "Something went wrong. Please try again.";
  }

  // ─── API call ─────────────────────────────────────────────────────────────────
  async function callELI5API(topic) {
    if (state.abortController) state.abortController.abort();
    state.abortController = new AbortController();
    const timer = setTimeout(() => state.abortController.abort(), 30000);

    try {
      const res = await fetch("/eli5/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        signal: state.abortController.signal,
        body: JSON.stringify({ topic }),
      });

      const bodyText = await res.text();

      if (!res.ok) {
        throw new Error(errorMessage(res.status, bodyText));
      }

      return JSON.parse(bodyText);

    } catch (err) {
      if (err.name === "AbortError") throw new Error("Request timed out. Please try again.");
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  // ─── Generate ─────────────────────────────────────────────────────────────────
  async function generate(topic) {
    topic = topic.trim();
    if (!topic) { toast("Please enter a topic first."); return; }
    if (state.loading) return;

    state.lastTopic = topic;
    setExplainBtnLoading(true);
    showLoading();

    try {
      const data = await callELI5API(topic);
      renderOutput(topic, data);
    } catch (err) {
      showEmpty();
      toast(err.message || "Failed to generate explanation.");
    } finally {
      setExplainBtnLoading(false);
    }
  }

  // ─── Explain button ───────────────────────────────────────────────────────────
  if (explainBtn) {
    explainBtn.addEventListener("click", () => {
      generate(topicInput?.value || "");
    });
  }

  // ─── Textarea keyboard shortcuts ──────────────────────────────────────────────
  if (topicInput) {
    topicInput.addEventListener("input", updateCharCount);

    topicInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        generate(topicInput.value);
      }
      if (e.key === "Escape") {
        topicInput.blur();
      }
    });
  }

  // ─── Example chips ────────────────────────────────────────────────────────────
  root.querySelectorAll(".eli5-chip[data-topic]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const topic = chip.getAttribute("data-topic");
      if (topicInput) {
        topicInput.value = topic;
        updateCharCount();
        topicInput.focus();
      }
    });
  });

  // ─── Explore topic cards ──────────────────────────────────────────────────────
  root.querySelectorAll(".eli5-topic-card[data-topic]").forEach((card) => {
    card.addEventListener("click", () => {
      const topic = card.getAttribute("data-topic");
      if (topicInput) {
        topicInput.value = topic;
        updateCharCount();
      }
      const workspace = root.querySelector("#eli5-workspace");
      if (workspace) workspace.scrollIntoView({ behavior: "smooth", block: "start" });
      generate(topic);
    });
  });

  // ─── Copy ─────────────────────────────────────────────────────────────────────
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const title       = outputTitle?.textContent  || "";
      const summary     = summaryText?.innerText    || "";
      const explanation = explanationEl?.innerText  || "";
      const text        = [title, summary, explanation].filter(Boolean).join("\n\n");

      if (!text.trim()) { toast("Nothing to copy."); return; }
      try {
        await navigator.clipboard.writeText(text);
        toast("Copied to clipboard.");
      } catch (_) { toast("Copy failed."); }
    });
  }

  // ─── Generate Again ───────────────────────────────────────────────────────────
  if (againBtn) {
    againBtn.addEventListener("click", () => {
      const topic = topicInput?.value?.trim() || state.lastTopic;
      generate(topic);
    });
  }

  // ─── Clear ────────────────────────────────────────────────────────────────────
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (topicInput)    topicInput.value        = "";
      if (summaryText)   summaryText.innerHTML   = "";
      if (explanationEl) explanationEl.innerHTML = "";
      if (outputTitle)   outputTitle.textContent = "";
      state.lastTopic = "";
      updateCharCount();
      showEmpty();
    });
  }

  // ─── Init ─────────────────────────────────────────────────────────────────────
  updateCharCount();
  showEmpty();

})();