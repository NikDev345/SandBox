/* ============================================================
   DECISION MAKER — decision_maker.js
   Sandbox AI Platform — vanilla JS, no dependencies
   3-step wizard: Question -> Analyzing -> Result
   ============================================================ */

(function () {
  "use strict";

  /* ── CONSTANTS ────────────────────────────────────────────── */

  const API_ENDPOINT = "/decision-maker/analyze";
  const MIN_OPTIONS = 2;
  const MAX_OPTIONS = 10;
  const MAX_TAGS = 10;
  const MIN_QUESTION_LENGTH = 10;
  const MAX_QUESTION_LENGTH = 2000;

  const LOADING_MESSAGES = [
    "Analyzing...",
    "Comparing...",
    "Evaluating...",
    "Finding best option...",
    "Generating recommendation...",
  ];

  /* ── DOM REFS ─────────────────────────────────────────────── */

  const form = document.getElementById("dm-form");
  const questionEl = document.getElementById("dm-question");
  const questionCounterEl = document.getElementById("dm-question-counter");
  const questionFieldEl = document.getElementById("dm-field-question");
  const questionErrorEl = document.getElementById("dm-question-error");

  const decisionTypeEl = document.getElementById("dm-decision-type");

  const optionsListEl = document.getElementById("dm-options-list");
  const optionsCounterEl = document.getElementById("dm-options-counter");
  const optionsFieldEl = document.getElementById("dm-field-options");
  const optionsErrorEl = document.getElementById("dm-options-error");
  const addOptionBtn = document.getElementById("dm-add-option");
  const optionTemplate = document.getElementById("dm-option-template");

  const budgetEl = document.getElementById("dm-budget");
  const timelineEl = document.getElementById("dm-timeline");
  const contextEl = document.getElementById("dm-context");

  const prioritiesBox = document.getElementById("dm-priorities-box");
  const prioritiesInput = document.getElementById("dm-priorities-input");
  const prioritiesCounterEl = document.getElementById("dm-priorities-counter");
  const prioritiesErrorEl = document.getElementById("dm-priorities-error");

  const constraintsBox = document.getElementById("dm-constraints-box");
  const constraintsInput = document.getElementById("dm-constraints-input");
  const constraintsCounterEl = document.getElementById("dm-constraints-counter");
  const constraintsErrorEl = document.getElementById("dm-constraints-error");

  const tagTemplate = document.getElementById("dm-tag-template");

  const criteriaAccordion = document.getElementById("dm-criteria-accordion");
  const criteriaTrigger = document.getElementById("dm-criteria-trigger");

  const analyzeBtn = document.getElementById("dm-analyze-btn");
  const resetBtn = document.getElementById("dm-reset-btn");
  const editBtn = document.getElementById("dm-edit-btn");
  const newBtn = document.getElementById("dm-new-btn");

  const loadingTextEl = document.getElementById("dm-loading-text");

  const summaryEl = document.getElementById("dm-summary");
  const recOptionEl = document.getElementById("dm-rec-option");
  const confidenceFillEl = document.getElementById("dm-confidence-fill");
  const confidenceValueEl = document.getElementById("dm-confidence-value");
  const recReasoningEl = document.getElementById("dm-rec-reasoning");

  const analysisGridEl = document.getElementById("dm-analysis-grid");
  const analysisCardTemplate = document.getElementById("dm-analysis-card-template");

  const keyFactorsEl = document.getElementById("dm-key-factors");
  const finalAdviceEl = document.getElementById("dm-final-advice");
  const disclaimerEl = document.getElementById("dm-disclaimer");

  const toastRegion = document.getElementById("dm-toast-region");

  // Stepper / panels
  const panels = {
    1: document.getElementById("dm-panel-1"),
    2: document.getElementById("dm-panel-2"),
    3: document.getElementById("dm-panel-3"),
  };
  const stepItems = {
    1: document.querySelector('[data-step-item="1"]'),
    2: document.querySelector('[data-step-item="2"]'),
    3: document.querySelector('[data-step-item="3"]'),
  };
  const stepLines = {
    1: document.querySelector('[data-step-line="1"]'),
    2: document.querySelector('[data-step-line="2"]'),
  };

  /* ── STATE ────────────────────────────────────────────────── */

  let optionCounter = 0;
  let priorityTags = [];
  let constraintTags = [];
  let loadingInterval = null;
  let isSubmitting = false;
  let currentStep = 1;

  /* ============================================================
     INIT
     ============================================================ */

  function init() {
    addOptionRow();
    addOptionRow();
    bindEvents();
    updateQuestionCounter();
    updateOptionsCounter();
    updateTagCounters();
    goToStep(1);
  }

  function bindEvents() {
    form.addEventListener("submit", handleSubmit);
    resetBtn.addEventListener("click", resetForm);
    editBtn.addEventListener("click", () => goToStep(1));
    newBtn.addEventListener("click", () => {
      resetForm();
      goToStep(1);
    });

    questionEl.addEventListener("input", updateQuestionCounter);

    addOptionBtn.addEventListener("click", () => addOptionRow());

    optionsListEl.addEventListener("click", (e) => {
      const removeBtn = e.target.closest("[data-option-remove]");
      if (removeBtn) {
        removeOptionRow(removeBtn.closest("[data-option-item]"));
      }
    });

    criteriaTrigger.addEventListener("click", toggleAccordion);

    setupTagInput(prioritiesInput, "priorities");
    setupTagInput(constraintsInput, "constraints");

    form.addEventListener("click", (e) => {
      const suggestion = e.target.closest("[data-suggestions-for] .dm-tag-suggestion");
      if (suggestion) {
        const container = suggestion.closest("[data-suggestions-for]");
        const field = container.dataset.suggestionsFor;
        addTag(field, suggestion.textContent.trim());
      }
    });

    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".dm-btn");
      if (btn) createRipple(btn, e);
    });
  }

  /* ============================================================
     STEP NAVIGATION
     ============================================================ */

  function goToStep(step) {
    currentStep = step;

    Object.keys(panels).forEach((key) => {
      const num = Number(key);
      panels[num].dataset.active = String(num === step);
    });

    Object.keys(stepItems).forEach((key) => {
      const num = Number(key);
      const el = stepItems[num];
      if (num < step) {
        el.dataset.state = "done";
      } else if (num === step) {
        el.dataset.state = "active";
      } else {
        el.dataset.state = "idle";
      }
    });

    stepLines[1].dataset.lineState = step > 1 ? "done" : "idle";
    stepLines[2].dataset.lineState = step > 2 ? "done" : "idle";

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ============================================================
     QUESTION FIELD
     ============================================================ */

  function updateQuestionCounter() {
    const len = questionEl.value.length;
    questionCounterEl.textContent = `${len} / ${MAX_QUESTION_LENGTH}`;
    questionCounterEl.classList.toggle("dm-counter--warn", len > MAX_QUESTION_LENGTH * 0.9);
  }

  /* ============================================================
     OPTIONS (dynamic add/remove)
     ============================================================ */

  function addOptionRow() {
    const currentCount = optionsListEl.querySelectorAll("[data-option-item]").length;
    if (currentCount >= MAX_OPTIONS) return;

    optionCounter += 1;
    const node = optionTemplate.content.cloneNode(true);
    const item = node.querySelector("[data-option-item]");
    item.dataset.optionId = String(optionCounter);

    optionsListEl.appendChild(node);
    renumberOptions();
    updateOptionsCounter();
    updateAddOptionState();
    updateRemoveButtonsState();
  }

  function removeOptionRow(itemEl) {
    if (!itemEl) return;
    const currentCount = optionsListEl.querySelectorAll("[data-option-item]").length;
    if (currentCount <= MIN_OPTIONS) return;

    itemEl.classList.add("dm-option-item--removing");
    itemEl.addEventListener(
      "animationend",
      () => {
        itemEl.remove();
        renumberOptions();
        updateOptionsCounter();
        updateAddOptionState();
        updateRemoveButtonsState();
      },
      { once: true }
    );
  }

  function renumberOptions() {
    const items = optionsListEl.querySelectorAll("[data-option-item]");
    items.forEach((item, idx) => {
      const indexEl = item.querySelector("[data-option-index]");
      if (indexEl) indexEl.textContent = String(idx + 1);
    });
  }

  function updateOptionsCounter() {
    const count = optionsListEl.querySelectorAll("[data-option-item]").length;
    optionsCounterEl.textContent = `${count} / ${MAX_OPTIONS}`;
  }

  function updateAddOptionState() {
    const count = optionsListEl.querySelectorAll("[data-option-item]").length;
    addOptionBtn.disabled = count >= MAX_OPTIONS;
  }

  function updateRemoveButtonsState() {
    const items = optionsListEl.querySelectorAll("[data-option-item]");
    const disableRemove = items.length <= MIN_OPTIONS;
    items.forEach((item) => {
      const btn = item.querySelector("[data-option-remove]");
      if (btn) btn.disabled = disableRemove;
    });
  }

  /* ============================================================
     ACCORDION
     ============================================================ */

  function toggleAccordion() {
    const isOpen = criteriaAccordion.dataset.open === "true";
    criteriaAccordion.dataset.open = isOpen ? "false" : "true";
    criteriaTrigger.setAttribute("aria-expanded", String(!isOpen));
  }

  /* ============================================================
     TAG INPUTS (priorities / constraints)
     ============================================================ */

  function setupTagInput(inputEl, fieldName) {
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        addTag(fieldName, inputEl.value);
        inputEl.value = "";
      } else if (e.key === "Backspace" && inputEl.value === "") {
        const arr = fieldName === "priorities" ? priorityTags : constraintTags;
        if (arr.length > 0) removeTag(fieldName, arr.length - 1);
      }
    });

    inputEl.addEventListener("blur", () => {
      if (inputEl.value.trim()) {
        addTag(fieldName, inputEl.value);
        inputEl.value = "";
      }
    });
  }

  function addTag(fieldName, rawValue) {
    const value = rawValue.trim();
    if (!value) return;

    const arr = fieldName === "priorities" ? priorityTags : constraintTags;
    const boxEl = fieldName === "priorities" ? prioritiesBox : constraintsBox;
    const inputEl = fieldName === "priorities" ? prioritiesInput : constraintsInput;

    if (arr.length >= MAX_TAGS) {
      showFieldError(
        fieldName === "priorities" ? prioritiesErrorEl : constraintsErrorEl,
        `You can add up to ${MAX_TAGS} ${fieldName}.`
      );
      return;
    }

    if (arr.some((t) => t.toLowerCase() === value.toLowerCase())) return;

    arr.push(value);

    const node = tagTemplate.content.cloneNode(true);
    const tagEl = node.querySelector("[data-tag]");
    tagEl.querySelector("[data-tag-text]").textContent = value;
    tagEl.dataset.tagValue = value;
    boxEl.insertBefore(node, inputEl);

    clearFieldError(fieldName === "priorities" ? prioritiesErrorEl : constraintsErrorEl);
    updateTagCounters();
  }

  function removeTag(fieldName, index) {
    const arr = fieldName === "priorities" ? priorityTags : constraintTags;
    const boxEl = fieldName === "priorities" ? prioritiesBox : constraintsBox;
    const value = arr[index];
    if (value === undefined) return;

    arr.splice(index, 1);

    boxEl.querySelectorAll("[data-tag]").forEach((el) => {
      if (el.dataset.tagValue === value) el.remove();
    });

    updateTagCounters();
  }

  [prioritiesBox, constraintsBox].forEach((boxEl) => {
    boxEl.addEventListener("click", (e) => {
      const removeBtn = e.target.closest("[data-tag-remove]");
      if (!removeBtn) return;
      const tagEl = removeBtn.closest("[data-tag]");
      const value = tagEl.dataset.tagValue;
      const fieldName = boxEl.dataset.field;
      const arr = fieldName === "priorities" ? priorityTags : constraintTags;
      const idx = arr.indexOf(value);
      if (idx > -1) removeTag(fieldName, idx);
    });
  });

  function updateTagCounters() {
    prioritiesCounterEl.textContent = `${priorityTags.length} / ${MAX_TAGS}`;
    constraintsCounterEl.textContent = `${constraintTags.length} / ${MAX_TAGS}`;
  }

  /* ============================================================
     FORM COLLECTION
     ============================================================ */

  function collectForm() {
    const optionItems = Array.from(optionsListEl.querySelectorAll("[data-option-item]"));

    const options = optionItems.map((item) => {
      const titleInput = item.querySelector("[data-option-title]");
      const descInput = item.querySelector("[data-option-desc]");
      return {
        title: titleInput.value.trim(),
        description: descInput.value.trim(),
      };
    });

    return {
      question: questionEl.value.trim(),
      decision_type: decisionTypeEl.value,
      options: options,
      budget: budgetEl.value.trim(),
      timeline: timelineEl.value.trim(),
      priorities: priorityTags.slice(),
      constraints: constraintTags.slice(),
      additional_context: contextEl.value.trim(),
    };
  }

  /* ============================================================
     VALIDATION
     ============================================================ */

  function validate(data) {
    let isValid = true;
    clearAllErrors();

    if (!data.question || data.question.length < MIN_QUESTION_LENGTH) {
      showFieldError(
        questionErrorEl,
        `Please provide at least ${MIN_QUESTION_LENGTH} characters describing your decision.`
      );
      questionFieldEl.classList.add("dm-field-error");
      isValid = false;
    }

    if (data.options.length < MIN_OPTIONS) {
      showFieldError(optionsErrorEl, `Provide at least ${MIN_OPTIONS} options for comparison.`);
      optionsFieldEl.classList.add("dm-field-error");
      isValid = false;
    } else if (data.options.length > MAX_OPTIONS) {
      showFieldError(optionsErrorEl, `You can add up to ${MAX_OPTIONS} options.`);
      optionsFieldEl.classList.add("dm-field-error");
      isValid = false;
    } else {
      const emptyTitle = data.options.some((opt) => !opt.title);
      if (emptyTitle) {
        showFieldError(optionsErrorEl, "Every option needs a title.");
        optionsFieldEl.classList.add("dm-field-error");
        isValid = false;
      } else {
        const seen = new Set();
        let hasDuplicate = false;
        data.options.forEach((opt) => {
          const key = opt.title.toLowerCase();
          if (seen.has(key)) hasDuplicate = true;
          seen.add(key);
        });
        if (hasDuplicate) {
          showFieldError(optionsErrorEl, "Option titles must be unique.");
          optionsFieldEl.classList.add("dm-field-error");
          isValid = false;
        }
      }
    }

    if (data.priorities.length > MAX_TAGS) {
      showFieldError(prioritiesErrorEl, `You can specify up to ${MAX_TAGS} priorities.`);
      isValid = false;
    }
    if (data.constraints.length > MAX_TAGS) {
      showFieldError(constraintsErrorEl, `You can specify up to ${MAX_TAGS} constraints.`);
      isValid = false;
    }

    return isValid;
  }

  function showFieldError(errorEl, message) {
    if (!errorEl) return;
    errorEl.textContent = message;
  }

  function clearFieldError(errorEl) {
    if (!errorEl) return;
    errorEl.textContent = "";
  }

  function clearAllErrors() {
    [questionErrorEl, optionsErrorEl, prioritiesErrorEl, constraintsErrorEl].forEach(clearFieldError);
    questionFieldEl.classList.remove("dm-field-error");
    optionsFieldEl.classList.remove("dm-field-error");
  }

  /* ============================================================
     PAYLOAD BUILDING
     ============================================================ */

  function buildPayload(data) {
    return {
      question: data.question,
      decision_type: data.decision_type,
      options: data.options.map((opt) => ({
        title: opt.title,
        description: opt.description || undefined,
      })),
      criteria: {
        budget: data.budget || undefined,
        timeline: data.timeline || undefined,
        priorities: data.priorities,
        constraints: data.constraints,
        additional_context: data.additional_context || undefined,
      },
    };
  }

  /* ============================================================
     SUBMIT FLOW
     ============================================================ */

  async function handleSubmit(e) {
    e.preventDefault();
    if (isSubmitting) return;

    const data = collectForm();

    if (!validate(data)) {
      const firstError = form.querySelector(".dm-field-error");
      if (firstError) firstError.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    const payload = buildPayload(data);
    await submitDecision(payload);
  }

  async function submitDecision(payload) {
    isSubmitting = true;
    showLoading();

    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let body = null;
      try {
        body = await response.json();
      } catch (parseErr) {
        throw new Error("EMPTY_OR_MALFORMED");
      }

      if (!response.ok) {
        const detail = body && body.detail ? body.detail : null;
        if (response.status === 400) {
          throw new Error(detail || "Please check your inputs and try again.");
        }
        if (response.status >= 500) {
          throw new Error(detail || "Something went wrong on our end. Please try again.");
        }
        throw new Error(detail || "The request could not be completed.");
      }

      if (!body || body.success !== true) {
        throw new Error("The AI did not return a valid analysis. Please try again.");
      }

      renderResults(body);
    } catch (err) {
      hideLoading();
      goToStep(1);
      if (err instanceof TypeError) {
        showError("Connection problem", "Couldn't reach the server. Check your connection and try again.");
      } else if (err.message === "EMPTY_OR_MALFORMED") {
        showError("Unexpected response", "The server sent back something we couldn't read. Please try again.");
      } else {
        showError("Analysis failed", err.message || "Something went wrong. Please try again.");
      }
    } finally {
      isSubmitting = false;
      setButtonLoading(false);
    }
  }

  /* ============================================================
     RENDERING
     ============================================================ */

  function renderResults(data) {
    renderSummary(data.summary);
    renderRecommendation(data.recommendation);
    renderAnalysis(data.analysis);
    renderKeyFactors(data.key_factors);
    renderFinalAdvice(data.final_advice);
    renderDisclaimer(data.disclaimer);

    hideLoading();
    goToStep(3);

    const confidence = data.recommendation ? clampNumber(data.recommendation.confidence, 0, 100) : 0;
    requestAnimationFrame(() => {
      confidenceFillEl.style.width = `${confidence}%`;
    });
  }

  function renderSummary(summary) {
    summaryEl.textContent = summary || "";
  }

  function renderRecommendation(recommendation) {
    if (!recommendation) return;
    recOptionEl.textContent = recommendation.selected_option || "";
    recReasoningEl.textContent = recommendation.reasoning || "";
    const confidence = clampNumber(recommendation.confidence, 0, 100);
    confidenceValueEl.textContent = `${confidence}%`;
  }

  function renderAnalysis(analysisList) {
    analysisGridEl.innerHTML = "";
    (analysisList || []).forEach((item) => {
      const node = analysisCardTemplate.content.cloneNode(true);
      const card = node.querySelector(".dm-analysis-card");

      card.querySelector("[data-analysis-name]").textContent = item.option || "Option";

      const score = clampNumber(item.score, 0, 10);
      const scorePercent = (score / 10) * 100;
      const scoreFillEl = card.querySelector("[data-analysis-score-fill]");
      card.querySelector("[data-analysis-score-value]").textContent = score.toFixed(1);

      fillList(card.querySelector("[data-analysis-pros]"), item.pros);
      fillList(card.querySelector("[data-analysis-cons]"), item.cons);
      fillList(card.querySelector("[data-analysis-risks]"), item.risks);

      analysisGridEl.appendChild(node);

      requestAnimationFrame(() => {
        scoreFillEl.style.width = `${scorePercent}%`;
      });
    });
  }

  function fillList(ulEl, items) {
    ulEl.innerHTML = "";
    if (!items || items.length === 0) {
      const li = document.createElement("li");
      li.className = "dm-analysis-list--empty";
      li.textContent = "None noted";
      ulEl.appendChild(li);
      return;
    }
    items.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      ulEl.appendChild(li);
    });
  }

  function renderKeyFactors(factors) {
    keyFactorsEl.innerHTML = "";
    (factors || []).forEach((factor) => {
      const chip = document.createElement("span");
      chip.className = "dm-chip";
      chip.textContent = factor;
      keyFactorsEl.appendChild(chip);
    });
  }

  function renderFinalAdvice(advice) {
    finalAdviceEl.textContent = advice || "";
  }

  function renderDisclaimer(disclaimer) {
    disclaimerEl.textContent = disclaimer || "";
  }

  /* ============================================================
     LOADING STATE
     ============================================================ */

  function showLoading() {
    goToStep(2);
    setButtonLoading(true);
    setFormDisabled(true);
    confidenceFillEl.style.width = "0%";

    let msgIndex = 0;
    loadingTextEl.textContent = LOADING_MESSAGES[msgIndex];
    clearInterval(loadingInterval);
    loadingInterval = setInterval(() => {
      msgIndex = (msgIndex + 1) % LOADING_MESSAGES.length;
      loadingTextEl.textContent = LOADING_MESSAGES[msgIndex];
    }, 1800);
  }

  function hideLoading() {
    clearInterval(loadingInterval);
    setFormDisabled(false);
  }

  function setButtonLoading(isLoading) {
    analyzeBtn.dataset.loading = String(isLoading);
    analyzeBtn.disabled = isLoading;
  }

  function setFormDisabled(disabled) {
    Array.from(form.elements).forEach((el) => {
      if (el === analyzeBtn) return;
      el.disabled = disabled;
    });
  }

  /* ============================================================
     ERROR TOASTS
     ============================================================ */

  function showError(title, message) {
    const toast = document.createElement("div");
    toast.className = "dm-toast dm-toast--error";
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
      <span class="dm-toast-icon" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 8V13M12 16.5H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </span>
      <span class="dm-toast-body">
        <span class="dm-toast-title"></span>
        <span class="dm-toast-msg"></span>
      </span>
      <button type="button" class="dm-toast-close" aria-label="Dismiss">&times;</button>
    `;
    toast.querySelector(".dm-toast-title").textContent = title;
    toast.querySelector(".dm-toast-msg").textContent = message;

    toastRegion.appendChild(toast);

    const dismiss = () => {
      toast.classList.add("dm-toast--leaving");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    };

    toast.querySelector(".dm-toast-close").addEventListener("click", dismiss);
    setTimeout(dismiss, 7000);
  }

  /* ============================================================
     RESET
     ============================================================ */

  function resetForm() {
    form.reset();

    optionsListEl.innerHTML = "";
    optionCounter = 0;
    addOptionRow();
    addOptionRow();

    priorityTags = [];
    constraintTags = [];
    prioritiesBox.querySelectorAll("[data-tag]").forEach((t) => t.remove());
    constraintsBox.querySelectorAll("[data-tag]").forEach((t) => t.remove());
    updateTagCounters();

    criteriaAccordion.dataset.open = "false";
    criteriaTrigger.setAttribute("aria-expanded", "false");

    updateQuestionCounter();
    clearAllErrors();

    confidenceFillEl.style.width = "0%";
  }

  /* ============================================================
     UTILITIES
     ============================================================ */

  function clampNumber(value, min, max) {
    const num = Number(value);
    if (Number.isNaN(num)) return min;
    return Math.min(max, Math.max(min, num));
  }

  function createRipple(btn, event) {
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const ripple = document.createElement("span");
    ripple.className = "dm-btn-ripple";
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
    btn.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove(), { once: true });
  }

  /* ── BOOT ─────────────────────────────────────────────────── */

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();