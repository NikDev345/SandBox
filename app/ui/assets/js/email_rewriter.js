/**
 * AI Email Studio — email_rewriter.js
 * Single IIFE module. No global leakage. No frameworks.
 * Handles: mode switching, counters, chips, API call,
 *          loading states, copy/download/mailto, error handling.
 */
(function () {
  "use strict";

  /* ═══════════════════════════════════════════════════════
     CONSTANTS
  ═══════════════════════════════════════════════════════ */

  const API_ENDPOINT = "/email-rewriter/generate";

  const ROTATING_WORDS = [
    "Professional",
    "Friendly",
    "Persuasive",
    "Concise",
    "Executive",
    "Supportive",
    "Marketing",
    "Sales-Ready",
  ];

  const LOADING_STATUSES = [
    "Reading…",
    "Understanding…",
    "Improving…",
    "Writing…",
    "Generating…",
    "Finalizing…",
  ];

  /* ═══════════════════════════════════════════════════════
     DOM REFERENCES  (matched 1-to-1 with HTML IDs)
  ═══════════════════════════════════════════════════════ */

  const $ = (id) => document.getElementById(id);

  const DOM = {
    // Mode switch
    btnRewrite:       $("er-btn-rewrite"),
    btnGenerate:      $("er-btn-generate"),
    modeIndicator:    $("er-mode-indicator"),

    // Rotating word
    rotatingWord:     $("er-rotating-word"),

    // Panels
    panelRewrite:     $("er-panel-rewrite"),
    panelGenerate:    $("er-panel-generate"),

    // Rewrite inputs
    subject:          $("er-subject"),
    emailBody:        $("er-email-body"),
    wordCount:        $("er-word-count"),
    charCount:        $("er-char-count"),

    // Rewrite settings
    style:            $("er-style"),
    tone:             $("er-tone"),
    length:           $("er-length"),
    language:         $("er-language"),

    // Advanced settings
    advancedToggle:   $("er-advanced-toggle"),
    advancedChevron:  $("er-advanced-chevron"),
    advancedBody:     $("er-advanced-body"),
    preserveIntent:   $("er-preserve-intent"),
    improveSubject:   $("er-improve-subject"),
    improveGreeting:  $("er-improve-greeting"),
    improveClosing:   $("er-improve-closing"),
    fixGrammar:       $("er-fix-grammar"),
    improveClarity:   $("er-improve-clarity"),
    improveReadability: $("er-improve-readability"),

    // Rewrite action button
    submitRewrite:    $("er-submit-rewrite"),
    submitRewriteText: $("er-submit-rewrite-text"),

    // Generate inputs
    prompt:           $("er-prompt"),
    promptWordCount:  $("er-prompt-word-count"),
    chips:            $("er-chips"),
    genTone:          $("er-gen-tone"),
    genLength:        $("er-gen-length"),

    // Generate action button
    submitGenerate:   $("er-submit-generate"),
    submitGenerateText: $("er-submit-generate-text"),

    // Output area
    emptyState:       $("er-empty"),
    emptyTitle:       $("er-empty-title"),
    emptyDesc:        $("er-empty-desc"),
    loadingState:     $("er-loading"),
    loadingStatus:    $("er-loading-status"),
    errorState:       $("er-error"),
    errorMsg:         $("er-error-msg"),
    errorRetry:       $("er-error-retry"),
    outputArea:       $("er-output"),
    actionBar:        $("er-action-bar"),

    // Output card content
    outSubject:       $("er-out-subject"),
    outGreeting:      $("er-out-greeting"),
    outBody:          $("er-out-body"),
    outClosing:       $("er-out-closing"),
    outFull:          $("er-out-full"),
    outSuggestions:   $("er-out-suggestions"),

    // Bar buttons
    btnCopyAll:       $("er-btn-copy-all"),
    btnDownload:      $("er-btn-download"),
    btnMailto:        $("er-btn-mailto"),
    btnRegenerate:    $("er-btn-regenerate"),

    // Toast
    toast:            $("er-toast"),
  };

  /* ═══════════════════════════════════════════════════════
     STATE
  ═══════════════════════════════════════════════════════ */

  const state = {
    mode: "rewrite",          // "rewrite" | "generate"
    isLoading: false,
    lastPayload: null,        // for regenerate
    lastResponse: null,       // for download / mailto
    wordRotateIndex: 0,
    wordRotateTimer: null,
    loadingStatusIndex: 0,
    loadingStatusTimer: null,
    toastTimer: null,
  };

  /* ═══════════════════════════════════════════════════════
     ROTATING WORD
  ═══════════════════════════════════════════════════════ */

  function startRotatingWord() {
    state.wordRotateTimer = setInterval(() => {
      const el = DOM.rotatingWord;
      el.classList.remove("er-fade-in");
      el.classList.add("er-fade-out");

      setTimeout(() => {
        state.wordRotateIndex =
          (state.wordRotateIndex + 1) % ROTATING_WORDS.length;
        el.textContent = ROTATING_WORDS[state.wordRotateIndex];
        el.classList.remove("er-fade-out");
        el.classList.add("er-fade-in");
      }, 220);
    }, 2400);
  }

  /* ═══════════════════════════════════════════════════════
     MODE SWITCH
  ═══════════════════════════════════════════════════════ */

  function setMode(mode) {
    if (state.mode === mode) return;
    state.mode = mode;

    const isRewrite = mode === "rewrite";

    // Tab aria states
    DOM.btnRewrite.setAttribute("aria-selected", isRewrite ? "true" : "false");
    DOM.btnGenerate.setAttribute("aria-selected", isRewrite ? "false" : "true");

    // Active class
    DOM.btnRewrite.classList.toggle("er-mode-switch__btn--active", isRewrite);
    DOM.btnGenerate.classList.toggle("er-mode-switch__btn--active", !isRewrite);

    // Slide indicator
    DOM.modeIndicator.style.transform = isRewrite
      ? "translateX(0)"
      : "translateX(100%)";

    // Panel visibility — smooth cross-fade via class swap
    if (isRewrite) {
      DOM.panelGenerate.classList.add("er-input-panel--hidden");
      DOM.panelRewrite.classList.remove("er-input-panel--hidden");
    } else {
      DOM.panelRewrite.classList.add("er-input-panel--hidden");
      DOM.panelGenerate.classList.remove("er-input-panel--hidden");
    }

    // Reset output to empty
    showEmpty();

    // Update empty state copy
    if (isRewrite) {
      DOM.emptyTitle.textContent = "Ready to rewrite";
      DOM.emptyDesc.innerHTML =
        "Paste your email on the left and click <strong>Rewrite Email</strong> — AI will polish it while preserving your intent.";
    } else {
      DOM.emptyTitle.textContent = "Ready to generate";
      DOM.emptyDesc.innerHTML =
        "Describe your email in a few words and click <strong>Generate Email</strong> — or pick an example to start.";
    }
  }

  /* ═══════════════════════════════════════════════════════
     COUNTERS
  ═══════════════════════════════════════════════════════ */

  function countWords(str) {
    return str.trim() === "" ? 0 : str.trim().split(/\s+/).length;
  }

  function updateBodyCounters() {
    const body = DOM.emailBody.value;
    DOM.wordCount.textContent = `${countWords(body)} words`;
    DOM.charCount.textContent = `${body.length} characters`;
  }

  function updatePromptCounter() {
    DOM.promptWordCount.textContent = `${countWords(DOM.prompt.value)} words`;
  }

  /* ═══════════════════════════════════════════════════════
     ADVANCED SETTINGS TOGGLE
  ═══════════════════════════════════════════════════════ */

  function toggleAdvanced() {
    const isOpen = DOM.advancedBody.classList.toggle("er-advanced__body--open");
    DOM.advancedChevron.classList.toggle("er-advanced__chevron--open", isOpen);
    DOM.advancedToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    DOM.advancedBody.setAttribute("aria-hidden", isOpen ? "false" : "true");
  }

  /* ═══════════════════════════════════════════════════════
     OUTPUT STATE MANAGEMENT
  ═══════════════════════════════════════════════════════ */

  function showEmpty() {
    DOM.emptyState.style.display = "";
    DOM.loadingState.classList.remove("er-loading--visible");
    DOM.errorState.classList.remove("er-error--visible");
    DOM.outputArea.classList.remove("er-output--visible");
    DOM.actionBar.classList.remove("er-action-bar--visible");
  }

  function showLoading() {
    DOM.emptyState.style.display = "none";
    DOM.loadingState.classList.add("er-loading--visible");
    DOM.errorState.classList.remove("er-error--visible");
    DOM.outputArea.classList.remove("er-output--visible");
    DOM.actionBar.classList.remove("er-action-bar--visible");

    // Cycle loading status text
    state.loadingStatusIndex = 0;
    DOM.loadingStatus.textContent = LOADING_STATUSES[0];

    state.loadingStatusTimer = setInterval(() => {
      state.loadingStatusIndex =
        (state.loadingStatusIndex + 1) % LOADING_STATUSES.length;
      DOM.loadingStatus.textContent =
        LOADING_STATUSES[state.loadingStatusIndex];
    }, 1800);
  }

  function stopLoadingCycle() {
    if (state.loadingStatusTimer) {
      clearInterval(state.loadingStatusTimer);
      state.loadingStatusTimer = null;
    }
  }

  function showError(msg) {
    stopLoadingCycle();
    DOM.emptyState.style.display = "none";
    DOM.loadingState.classList.remove("er-loading--visible");
    DOM.outputArea.classList.remove("er-output--visible");
    DOM.actionBar.classList.remove("er-action-bar--visible");
    DOM.errorMsg.textContent = msg || "Something went wrong. Please try again.";
    DOM.errorState.classList.add("er-error--visible");
  }

  function showOutput(data) {
    stopLoadingCycle();
    DOM.emptyState.style.display = "none";
    DOM.loadingState.classList.remove("er-loading--visible");
    DOM.errorState.classList.remove("er-error--visible");

    // Populate card content
    DOM.outSubject.textContent   = data.subject   || "—";
    DOM.outGreeting.textContent  = data.greeting  || "—";
    DOM.outBody.textContent      = data.body       || "—";
    DOM.outClosing.textContent   = data.closing    || "—";
    DOM.outFull.textContent      = data.full_email || "—";

    // Suggestions
    DOM.outSuggestions.innerHTML = "";
    if (Array.isArray(data.suggestions) && data.suggestions.length > 0) {
      data.suggestions.forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        DOM.outSuggestions.appendChild(li);
      });
      $("er-card-suggestions").style.display = "";
    } else {
      $("er-card-suggestions").style.display = "none";
    }

    DOM.outputArea.classList.add("er-output--visible");
    DOM.actionBar.classList.add("er-action-bar--visible");
  }

  /* ═══════════════════════════════════════════════════════
     ACTION BUTTON STATE
  ═══════════════════════════════════════════════════════ */

  function setButtonLoading(isLoading) {
    state.isLoading = isLoading;

    if (state.mode === "rewrite") {
      DOM.submitRewrite.disabled = isLoading;
      DOM.submitRewriteText.textContent = isLoading
        ? "Working on it…"
        : "Rewrite Email";
    } else {
      DOM.submitGenerate.disabled = isLoading;
      DOM.submitGenerateText.textContent = isLoading
        ? "Generating…"
        : "Generate Email";
    }
  }

  /* ═══════════════════════════════════════════════════════
     PAYLOAD BUILDER
  ═══════════════════════════════════════════════════════ */

  function buildPayload() {

    if (state.mode === "rewrite") {

        return {
            mode: "rewrite",

            subject: DOM.subject.value.trim(),

            email: DOM.emailBody.value.trim(),

            instruction: null,

            settings: {
                style: DOM.style.value,
                tone: DOM.tone.value,
                length: DOM.length.value,
                language: DOM.language.value,

                preserve_intent: DOM.preserveIntent.checked,
                improve_subject: DOM.improveSubject.checked,
                improve_greeting: DOM.improveGreeting.checked,
                improve_closing: DOM.improveClosing.checked,
                fix_grammar: DOM.fixGrammar.checked,
                improve_clarity: DOM.improveClarity.checked,
                improve_readability: DOM.improveReadability.checked,
            }
        };

    }

    return {

        mode: "generate",

        subject: null,

        email: null,

        instruction: DOM.prompt.value.trim(),

        settings: {
            style: "improve",
            tone: DOM.genTone.value,
            length: DOM.genLength.value,
            language: "English",

            preserve_intent: false,
            improve_subject: true,
            improve_greeting: true,
            improve_closing: true,
            fix_grammar: true,
            improve_clarity: true,
            improve_readability: true,
        }
    };

}

    function validatePayload(payload) {

        if (
            payload.mode === "rewrite" &&
            !payload.email
        ) {
            return "Please paste an email to rewrite.";
        }

        if (
            payload.mode === "generate" &&
            !payload.instruction
        ) {
            return "Please describe the email you want to generate.";
        }

        return null;
    }

  /* ═══════════════════════════════════════════════════════
     API CALL
  ═══════════════════════════════════════════════════════ */

  async function callAPI(payload) {
    const token = getJWT();

    const headers = { "Content-Type": "application/json" };

    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      credentials: "include",
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let detail = `Server error ${response.status}`;
      try {
        const err = await response.json();
        detail = err.detail || err.message || detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }

    return response.json();
  }

  function getJWT() {
    // NiceGUI stores JWT in a cookie or localStorage — read from both
    try {
      const match = document.cookie
        .split("; ")
        .find((c) => c.startsWith("access_token="));
      if (match) return decodeURIComponent(match.split("=")[1]);

      return (
        localStorage.getItem("access_token") ||
        sessionStorage.getItem("access_token") ||
        null
      );
    } catch (_) {
      return null;
    }
  }

  /* ═══════════════════════════════════════════════════════
     MAIN SUBMIT HANDLER
  ═══════════════════════════════════════════════════════ */

  async function handleSubmit() {
    if (state.isLoading) return;

    const payload = buildPayload();
    const validationError = validatePayload(payload);

    if (validationError) {
      showToast(validationError, "error");
      return;
    }

    state.lastPayload = payload;
    setButtonLoading(true);
    showLoading();

    try {
      const data = await callAPI(payload);
      state.lastResponse = data;
      showOutput(data);
    } catch (err) {
      showError(err.message || "Something went wrong. Please try again.");
    } finally {
      setButtonLoading(false);
    }
  }

  /* ═══════════════════════════════════════════════════════
     COPY TO CLIPBOARD
  ═══════════════════════════════════════════════════════ */

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      if (btn) {
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7L5 10L12 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Copied`;
        btn.classList.add("er-card__btn--success");
        setTimeout(() => {
          btn.innerHTML = originalHTML;
          btn.classList.remove("er-card__btn--success");
        }, 2000);
      }
      showToast("Copied to clipboard");
    } catch (_) {
      showToast("Copy failed — please select and copy manually.", "error");
    }
  }

  /* ═══════════════════════════════════════════════════════
     COPY ALL
  ═══════════════════════════════════════════════════════ */

  function handleCopyAll() {
    if (!state.lastResponse) return;
    const text = state.lastResponse.full_email || "";
    copyText(text, null);
  }

  /* ═══════════════════════════════════════════════════════
     DOWNLOAD
  ═══════════════════════════════════════════════════════ */

  function handleDownload() {
    if (!state.lastResponse) return;
    const text = state.lastResponse.full_email || "";
    const subject = state.lastResponse.subject || "email";
    const filename = `${subject
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .slice(0, 40)}.txt`;

    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }, 1000);
    showToast("Download started");
  }

  /* ═══════════════════════════════════════════════════════
     OPEN IN EMAIL (mailto)
  ═══════════════════════════════════════════════════════ */

  function handleMailto() {
    if (!state.lastResponse) return;
    const subject = encodeURIComponent(state.lastResponse.subject || "");
    const body = encodeURIComponent(state.lastResponse.full_email || "");
    const mailto = `mailto:?subject=${subject}&body=${body}`;
    window.location.href = mailto;
  }

  /* ═══════════════════════════════════════════════════════
     REGENERATE
  ═══════════════════════════════════════════════════════ */

  async function handleRegenerate() {
    if (!state.lastPayload || state.isLoading) return;

    setButtonLoading(true);
    showLoading();

    try {
      const data = await callAPI(state.lastPayload);
      state.lastResponse = data;
      showOutput(data);
    } catch (err) {
      showError(err.message || "Regeneration failed. Please try again.");
    } finally {
      setButtonLoading(false);
    }
  }

  /* ═══════════════════════════════════════════════════════
     COPY CARD BUTTONS (delegated)
  ═══════════════════════════════════════════════════════ */

  function handleCardAction(e) {
    const btn = e.target.closest("[data-copy-target], [data-edit-target]");
    if (!btn) return;

    if (btn.dataset.copyTarget) {
      const el = $(btn.dataset.copyTarget);
      if (el) copyText(el.textContent, btn);
    }

    if (btn.dataset.editTarget) {
      const el = $(btn.dataset.editTarget);
      if (!el) return;

      const isEditing = el.contentEditable === "true";
      if (isEditing) {
        el.contentEditable = "false";
        el.style.outline = "";
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M9.5 2L12 4.5L4.5 12H2V9.5L9.5 2Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg> Edit`;
      } else {
        el.contentEditable = "true";
        el.style.outline = "1px solid rgba(255,255,255,0.2)";
        el.style.borderRadius = "4px";
        el.style.padding = "2px 4px";
        el.focus();
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7L5 10L12 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Done`;
      }
    }
  }

  /* ═══════════════════════════════════════════════════════
     CHIP CLICKS
  ═══════════════════════════════════════════════════════ */

  function handleChipClick(e) {
    const chip = e.target.closest(".er-chip");
    if (!chip) return;
    const prompt = chip.dataset.prompt;
    if (prompt) {
      DOM.prompt.value = prompt;
      updatePromptCounter();
      DOM.prompt.focus();
    }
  }

  /* ═══════════════════════════════════════════════════════
     TOAST
  ═══════════════════════════════════════════════════════ */

  function showToast(msg, type) {
    if (state.toastTimer) clearTimeout(state.toastTimer);
    DOM.toast.textContent = msg;
    DOM.toast.style.borderColor =
      type === "error"
        ? "rgba(239,68,68,0.3)"
        : "rgba(255,255,255,0.12)";
    DOM.toast.style.color =
      type === "error" ? "#ef4444" : "";
    DOM.toast.classList.add("er-toast--visible");
    state.toastTimer = setTimeout(() => {
      DOM.toast.classList.remove("er-toast--visible");
    }, 3000);
  }

  /* ═══════════════════════════════════════════════════════
     EVENT BINDING
  ═══════════════════════════════════════════════════════ */

  function bindEvents() {
    // Mode switch
    DOM.btnRewrite.addEventListener("click", () => setMode("rewrite"));
    DOM.btnGenerate.addEventListener("click", () => setMode("generate"));

    // Body counters
    DOM.emailBody.addEventListener("input", updateBodyCounters);
    DOM.prompt.addEventListener("input", updatePromptCounter);

    // Advanced toggle
    DOM.advancedToggle.addEventListener("click", toggleAdvanced);

    // Submit buttons
    DOM.submitRewrite.addEventListener("click", handleSubmit);
    DOM.submitGenerate.addEventListener("click", handleSubmit);

    // Chips (delegated to container)
    DOM.chips.addEventListener("click", handleChipClick);

    // Card copy / edit buttons (delegated to output area)
    DOM.outputArea.addEventListener("click", handleCardAction);

    // Error retry
    DOM.errorRetry.addEventListener("click", () => {
      if (state.lastPayload) handleRegenerate();
      else showEmpty();
    });

    // Action bar
    DOM.btnCopyAll.addEventListener("click", handleCopyAll);
    DOM.btnDownload.addEventListener("click", handleDownload);
    DOM.btnMailto.addEventListener("click", handleMailto);
    DOM.btnRegenerate.addEventListener("click", handleRegenerate);

    // Keyboard shortcut: Ctrl/Cmd + Enter to submit
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleSubmit();
      }
    });
  }

  /* ═══════════════════════════════════════════════════════
     INIT
  ═══════════════════════════════════════════════════════ */

  function init() {
    // Initialise mode indicator position
    DOM.modeIndicator.style.transform = "translateX(0)";

    // Start rotating word
    startRotatingWord();

    // Set initial empty state copy
    DOM.emptyTitle.textContent = "Ready to rewrite";
    DOM.emptyDesc.innerHTML =
      "Paste your email on the left and click <strong>Rewrite Email</strong> — AI will polish it while preserving your intent.";

    // Bind all events
    bindEvents();
  }

  // Kick off
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();