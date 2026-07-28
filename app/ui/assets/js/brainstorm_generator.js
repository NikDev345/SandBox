/**
 * brainstorm_generator.js
 * SandBox AI SaaS — Brainstorm Generator Module
 *
 * Architecture:
 *   - IIFE / module scope to avoid polluting window
 *   - DOM references resolved once in initialize()
 *   - State held in a single plain object
 *   - API interaction via submitBrainstorm() → POST /brainstorm-generator/generate
 *
 * Enhancements in this pass:
 *   - AbortController so a second submit cancels an in-flight request
 *   - Arrow-key navigation across the creativity radio group (roving tabindex)
 *   - Slider fill percentage driven via CSS var + a small "bump" pulse
 *   - Invalid shake feedback on topic/constraint errors
 *   - Skeleton idea cards during loading instead of only the spinner
 *   - Score bars tagged with a data-tier so CSS can color by strength
 *   - Toast is dismissible and animates out instead of hard-hiding
 *   - Duplicate/overflow constraint chip removal animates out
 *   - Focus + scroll-into-view on validation errors for a11y
 */

(function BrainstormGeneratorModule() {
  'use strict';

  /* ═══════════════════════════════════════════════════════════════════════════
     STATE
  ═══════════════════════════════════════════════════════════════════════════ */

  const state = {
    constraints:  [],
    creativity:   'medium',
    isGenerating: false,
    loadingTimer: null,
    loadingIndex: 0,
    abortCtrl:    null,
  };

  const LOADING_MESSAGES = [
    'Analyzing possibilities…',
    'Thinking creatively…',
    'Finding unique ideas…',
    'Evaluating innovation…',
    'Building recommendations…',
  ];

  const MIN_TOPIC_LENGTH = 3;
  const MAX_TOPIC_LENGTH = 300;
  const MIN_IDEA_COUNT = 3;
  const MAX_IDEA_COUNT = 20;
  const MAX_CONSTRAINTS = 10;
  const CREATIVITY_VALUES = ['low', 'medium', 'high'];

  /* ═══════════════════════════════════════════════════════════════════════════
     DOM REFS
  ═══════════════════════════════════════════════════════════════════════════ */

  let dom = {};

  function resolveDOM() {
    const root = document.querySelector('.brn-tool');
    if (!root) {
      console.error('[BRN] Root element .brn-tool not found.');
      return false;
    }

    const q = (sel) => root.querySelector(sel);

    dom = {
      root,

      // Form
      form:              q('#brnForm'),
      topic:             q('#brnTopic'),
      topicCounter:      q('#brnTopicCounter .count'),
      topicError:        q('#brnTopicError'),
      category:          q('#brnCategory'),
      goal:              q('#brnGoal'),
      audience:          q('#brnAudience'),

      // Creativity
      creativityGrid:    q('#brnCreativityGrid'),
      creativityCards:   Array.from(root.querySelectorAll('.brn-creativity-card')),
      creativityInput:   q('#brnCreativity'),

      // Idea count
      ideaCount:         q('#brnIdeaCount'),
      ideaCountValue:    q('#brnIdeaCountValue'),

      // Constraints
      constraintInput:   q('#brnConstraintInput'),
      constraintChips:   q('#brnConstraintChips'),
      constraintError:   q('#brnConstraintError'),
      chipInputWrapper:  q('#brnChipInput'),

      // Context
      context:           q('#brnContext'),

      // Actions
      generateBtn:       q('#brnGenerateBtn'),
      resetBtn:          q('#brnResetBtn'),

      // Examples
      examples:          root.querySelectorAll('.brn-example-chip'),

      // Loading
      loading:           q('#brnLoading'),
      loadingText:       q('#brnLoadingText'),

      // Empty state
      emptyState:        q('#brnEmptyState'),

      // Results
      results:           q('#brnResults'),
      summaryText:       q('#brnSummaryText'),
      ideasGrid:         q('#brnIdeasGrid'),
      bestIdea:          q('#brnBestIdea'),
      bestIdeaText:      q('#brnBestIdeaText'),
      tipsSection:       q('#brnTipsSection'),
      tipsGrid:          q('#brnTipsGrid'),
      mistakesSection:   q('#brnMistakesSection'),
      mistakesGrid:      q('#brnMistakesGrid'),
      recommendation:    q('#brnRecommendation'),
      recommendationText: q('#brnRecommendationText'),

      // Status
      statusCard:        q('#brnStatusCard'),
      statusIcon:        q('#brnStatusIcon'),
      statusTitle:       q('#brnStatusTitle'),
      statusBody:        q('#brnStatusBody'),
    };

    return true;
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     INITIALIZE
  ═══════════════════════════════════════════════════════════════════════════ */

  function initialize() {
    if (!resolveDOM()) return;

    dom.topic.addEventListener('input', () => {
      updateCounter();
      clearFieldError(dom.topic, dom.topicError);
    });

    dom.creativityCards.forEach((card, i) => {
      card.setAttribute('tabindex', card.dataset.value === state.creativity ? '0' : '-1');

      card.addEventListener('click', () => toggleCreativity(card.dataset.value));

      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleCreativity(card.dataset.value);
          return;
        }
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          e.preventDefault();
          focusCreativityCard((i + 1) % dom.creativityCards.length);
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          e.preventDefault();
          focusCreativityCard((i - 1 + dom.creativityCards.length) % dom.creativityCards.length);
        }
      });
    });

    dom.ideaCount.addEventListener('input', () => {
      dom.ideaCountValue.textContent = dom.ideaCount.value;
      dom.ideaCount.setAttribute('aria-valuenow', dom.ideaCount.value);
      updateSliderFill();
      bumpSliderValue();
    });

    dom.constraintInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addConstraint(dom.constraintInput.value);
      }
    });

    dom.examples.forEach((chip) => {
      chip.addEventListener('click', () => {
        dom.topic.value = chip.dataset.example;
        updateCounter();
        clearFieldError(dom.topic, dom.topicError);
        dom.topic.focus();
      });
    });

    dom.form.addEventListener('submit', (e) => {
      e.preventDefault();
      submitBrainstorm();
    });

    dom.resetBtn.addEventListener('click', resetForm);

    updateCounter();
    updateSliderFill();
  }

  function focusCreativityCard(index) {
    dom.creativityCards.forEach((c, i) => c.setAttribute('tabindex', i === index ? '0' : '-1'));
    dom.creativityCards[index].focus();
    toggleCreativity(dom.creativityCards[index].dataset.value);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     FORM HELPERS
  ═══════════════════════════════════════════════════════════════════════════ */

  function updateCounter() {
    const len = dom.topic.value.length;
    dom.topicCounter.textContent = len;

    const wrapper = dom.topicCounter.closest('.char-counter');
    wrapper.classList.remove('warning', 'danger');
    if (len > MAX_TOPIC_LENGTH * 0.9) {
      wrapper.classList.add('danger');
    } else if (len > MAX_TOPIC_LENGTH * 0.7) {
      wrapper.classList.add('warning');
    }
  }

  function updateSliderFill() {
    const min = parseFloat(dom.ideaCount.min);
    const max = parseFloat(dom.ideaCount.max);
    const val = parseFloat(dom.ideaCount.value);
    const pct = ((val - min) / (max - min)) * 100;
    dom.ideaCount.style.setProperty('--brn-slider-pct', `${pct}%`);
  }

  function bumpSliderValue() {
    dom.ideaCountValue.classList.remove('is-bumped');
    // Force reflow so the animation can retrigger on rapid drags.
    void dom.ideaCountValue.offsetWidth;
    dom.ideaCountValue.classList.add('is-bumped');
  }

  function toggleCreativity(value) {
    if (!CREATIVITY_VALUES.includes(value)) return;

    state.creativity = value;
    dom.creativityInput.value = value;

    dom.creativityCards.forEach((card) => {
      const active = card.dataset.value === value;
      card.classList.toggle('is-active', active);
      card.setAttribute('aria-checked', String(active));
      card.setAttribute('tabindex', active ? '0' : '-1');
    });
  }

  function addConstraint(rawValue) {
    const value = (rawValue || '').trim();
    clearFieldError(dom.chipInputWrapper, dom.constraintError);

    if (!value) return;

    if (state.constraints.length >= MAX_CONSTRAINTS) {
      showFieldError(dom.chipInputWrapper, dom.constraintError, `You can add at most ${MAX_CONSTRAINTS} constraints.`);
      return;
    }

    const normalized = value.toLowerCase();
    if (state.constraints.some((c) => c.toLowerCase() === normalized)) {
      showFieldError(dom.chipInputWrapper, dom.constraintError, 'That constraint has already been added.');
      dom.constraintInput.value = '';
      return;
    }

    state.constraints.push(value);
    renderConstraintChips();
    dom.constraintInput.value = '';
  }

  function removeConstraint(index) {
    const chipEl = dom.constraintChips.children[index];
    if (chipEl) {
      chipEl.classList.add('is-removing');
      chipEl.addEventListener('animationend', () => {
        state.constraints.splice(index, 1);
        renderConstraintChips();
      }, { once: true });
    } else {
      state.constraints.splice(index, 1);
      renderConstraintChips();
    }
  }

  function renderConstraintChips() {
    dom.constraintChips.innerHTML = '';

    state.constraints.forEach((constraint, index) => {
      const chip = document.createElement('span');
      chip.className = 'brn-chip';

      const label = document.createElement('span');
      label.className = 'brn-chip-label';
      label.textContent = constraint;

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'brn-chip-remove';
      removeBtn.setAttribute('aria-label', `Remove constraint: ${constraint}`);
      removeBtn.textContent = '×';
      removeBtn.addEventListener('click', () => removeConstraint(index));

      chip.appendChild(label);
      chip.appendChild(removeBtn);
      dom.constraintChips.appendChild(chip);
    });

    dom.chipInputWrapper.classList.toggle('is-full', state.constraints.length >= MAX_CONSTRAINTS);
  }

  function showFieldError(containerEl, msgEl, message) {
    if (msgEl) {
      msgEl.textContent = message;
      msgEl.hidden = false;
    }
    if (containerEl) {
      containerEl.classList.remove('brn-shake');
      void containerEl.offsetWidth;
      containerEl.classList.add('brn-shake');
    }
  }

  function clearFieldError(containerEl, msgEl) {
    if (msgEl) {
      msgEl.textContent = '';
      msgEl.hidden = true;
    }
    if (containerEl) {
      containerEl.classList.remove('brn-shake');
    }
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     COLLECT / VALIDATE / BUILD PAYLOAD
  ═══════════════════════════════════════════════════════════════════════════ */

  function collectForm() {
    return {
      topic:        dom.topic.value.trim(),
      category:     dom.category.value,
      creativity:   dom.creativityInput.value,
      ideaCount:    parseInt(dom.ideaCount.value, 10),
      goal:         dom.goal.value.trim(),
      audience:     dom.audience.value.trim(),
      constraints:  state.constraints.slice(),
      context:      dom.context.value.trim(),
    };
  }

  function validate(data) {
    clearFieldError(dom.topic, dom.topicError);

    if (!data.topic || data.topic.length < MIN_TOPIC_LENGTH) {
      showFieldError(dom.topic, dom.topicError, `Topic must be at least ${MIN_TOPIC_LENGTH} characters.`);
      dom.topic.focus();
      dom.topic.scrollIntoView({ block: 'center', behavior: 'smooth' });
      return false;
    }

    if (data.topic.length > MAX_TOPIC_LENGTH) {
      showFieldError(dom.topic, dom.topicError, `Topic cannot exceed ${MAX_TOPIC_LENGTH} characters.`);
      dom.topic.focus();
      return false;
    }

    if (data.ideaCount < MIN_IDEA_COUNT || data.ideaCount > MAX_IDEA_COUNT) {
      showError('Invalid idea count', `Idea count must be between ${MIN_IDEA_COUNT} and ${MAX_IDEA_COUNT}.`);
      return false;
    }

    if (!CREATIVITY_VALUES.includes(data.creativity)) {
      showError('Invalid creativity level', 'Please select a creativity level.');
      return false;
    }

    return true;
  }

  function buildPayload(data) {
    return {
      topic:       data.topic,
      category:    data.category,
      creativity:  data.creativity,
      idea_count:  data.ideaCount,
      criteria: {
        goal:                data.goal || null,
        target_audience:     data.audience || null,
        constraints:         data.constraints,
        additional_context:  data.context || null,
      },
    };
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     API CALL
  ═══════════════════════════════════════════════════════════════════════════ */

  async function submitBrainstorm() {
    const data = collectForm();
    if (!validate(data)) return;

    // Cancel any in-flight request before starting a new one.
    if (state.abortCtrl) {
      state.abortCtrl.abort();
    }
    state.abortCtrl = new AbortController();

    const payload = buildPayload(data);

    state.isGenerating = true;
    dom.generateBtn.disabled = true;
    dom.resetBtn.disabled = true;
    clearResults();
    showLoading();

    try {
      const response = await fetch('/brainstorm-generator/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: state.abortCtrl.signal,
      });

      if (response.status === 401 || response.status === 403) {
        throw new Error('Authentication error. Please sign in again.');
      }

      if (response.status === 400) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || 'Validation error: the request was rejected.');
      }

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Server error (${response.status}). Please try again later.`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error('The AI was unable to generate ideas. Please try again.');
      }

      renderSummary(result.summary);
      renderIdeas(result.ideas);
      renderBestIdea(result.best_idea);
      renderImplementationTips(result.implementation_tips);
      renderCommonMistakes(result.common_mistakes);
      renderRecommendation(result.final_recommendation);

      hideLoading();
      dom.emptyState.hidden = true;
      dom.results.hidden = false;
      dom.results.classList.add('brn-reveal');

      showSuccess('Ideas generated', `${result.ideas.length} ideas ready for "${data.topic}".`);

    } catch (err) {
      if (err && err.name === 'AbortError') {
        // Superseded by a newer request; don't show an error toast.
        return;
      }
      hideLoading();
      dom.emptyState.hidden = false;
      showError('Generation failed', err.message || 'An unexpected error occurred. Please try again.');
    } finally {
      state.isGenerating = false;
      state.abortCtrl = null;
      dom.generateBtn.disabled = false;
      dom.resetBtn.disabled = false;
    }
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     RENDERING
  ═══════════════════════════════════════════════════════════════════════════ */

  function renderSummary(summary) {
    dom.summaryText.textContent = summary || '';
  }

  function renderIdeas(ideas) {
    dom.ideasGrid.innerHTML = '';
    (ideas || []).forEach((idea) => {
      dom.ideasGrid.appendChild(renderIdeaCard(idea));
    });
  }

  function scoreTier(score) {
    if (score >= 7) return 'high';
    if (score >= 4) return 'mid';
    return 'low';
  }

  function renderIdeaCard(idea) {
    const card = document.createElement('div');
    card.className = 'brn-idea-card metric-card';

    const difficultyClass = `brn-difficulty-${(idea.difficulty || '').toLowerCase()}`;
    const score = typeof idea.innovation_score === 'number' ? idea.innovation_score : 0;
    const scorePct = Math.max(0, Math.min(100, (score / 10) * 100));
    const tier = scoreTier(score);

    const nextSteps = (idea.next_steps || [])
      .map((step) => `<li>${escapeHTML(step)}</li>`)
      .join('');

    card.innerHTML = `
      <div class="brn-idea-header">
        <h3 class="brn-idea-title">${escapeHTML(idea.title || '')}</h3>
        <span class="brn-difficulty-badge ${difficultyClass}">${escapeHTML(idea.difficulty || '')}</span>
      </div>
      <p class="brn-idea-desc">${escapeHTML(idea.description || '')}</p>
      <p class="brn-idea-why"><strong>Why it works:</strong> ${escapeHTML(idea.why_it_works || '')}</p>
      <div class="brn-idea-score">
        <div class="brn-score-header">
          <span>Innovation Score</span>
          <span>${score.toFixed(1)} / 10</span>
        </div>
        <div class="brn-progress-bar" role="progressbar" aria-valuenow="${score}" aria-valuemin="0" aria-valuemax="10">
          <div class="brn-progress-fill" data-tier="${tier}" style="width:${scorePct}%"></div>
        </div>
      </div>
      ${nextSteps ? `<div class="brn-idea-steps"><span class="brn-idea-steps-label">Next Steps</span><ul>${nextSteps}</ul></div>` : ''}
    `;

    return card;
  }

  function renderBestIdea(bestIdea) {
    if (!bestIdea) {
      dom.bestIdea.hidden = true;
      return;
    }
    dom.bestIdeaText.textContent = bestIdea;
    dom.bestIdea.hidden = false;
  }

  function renderImplementationTips(tips) {
    dom.tipsGrid.innerHTML = '';

    if (!tips || tips.length === 0) {
      dom.tipsSection.hidden = true;
      return;
    }

    tips.forEach((tip) => {
      const card = document.createElement('div');
      card.className = 'brn-tip-card metric-card';
      card.innerHTML = `
        <span class="brn-tip-icon" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </span>
        <p>${escapeHTML(tip)}</p>
      `;
      dom.tipsGrid.appendChild(card);
    });

    dom.tipsSection.hidden = false;
  }

  function renderCommonMistakes(mistakes) {
    dom.mistakesGrid.innerHTML = '';

    if (!mistakes || mistakes.length === 0) {
      dom.mistakesSection.hidden = true;
      return;
    }

    mistakes.forEach((mistake) => {
      const card = document.createElement('div');
      card.className = 'brn-mistake-card metric-card';
      card.innerHTML = `
        <span class="brn-mistake-icon" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </span>
        <p>${escapeHTML(mistake)}</p>
      `;
      dom.mistakesGrid.appendChild(card);
    });

    dom.mistakesSection.hidden = false;
  }

  function renderRecommendation(recommendation) {
    if (!recommendation) {
      dom.recommendation.hidden = true;
      return;
    }
    dom.recommendationText.textContent = recommendation;
    dom.recommendation.hidden = false;
  }

  function clearResults() {
    dom.summaryText.textContent = '';
    dom.ideasGrid.innerHTML = '';
    dom.bestIdeaText.textContent = '';
    dom.tipsGrid.innerHTML = '';
    dom.mistakesGrid.innerHTML = '';
    dom.recommendationText.textContent = '';
    dom.bestIdea.hidden = true;
    dom.tipsSection.hidden = true;
    dom.mistakesSection.hidden = true;
    dom.recommendation.hidden = true;
    dom.results.hidden = true;
    dom.results.classList.remove('brn-reveal');
  }

  function resetForm() {
    if (state.abortCtrl) {
      state.abortCtrl.abort();
      state.abortCtrl = null;
    }
    dom.form.reset();
    state.constraints = [];
    renderConstraintChips();
    toggleCreativity('medium');
    dom.ideaCountValue.textContent = '10';
    updateSliderFill();
    clearFieldError(dom.topic, dom.topicError);
    clearFieldError(dom.chipInputWrapper, dom.constraintError);
    updateCounter();
    clearResults();
    dom.emptyState.hidden = false;
    hideStatus();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     LOADING STATE
  ═══════════════════════════════════════════════════════════════════════════ */

  function showLoading() {
    dom.emptyState.hidden = true;
    dom.results.hidden = true;
    dom.loading.hidden = false;
    state.loadingIndex = 0;
    dom.loadingText.textContent = LOADING_MESSAGES[0];

    state.loadingTimer = window.setInterval(() => {
      state.loadingIndex = (state.loadingIndex + 1) % LOADING_MESSAGES.length;
      dom.loadingText.textContent = LOADING_MESSAGES[state.loadingIndex];
    }, 2200);
  }

  function hideLoading() {
    dom.loading.hidden = true;
    if (state.loadingTimer) {
      window.clearInterval(state.loadingTimer);
      state.loadingTimer = null;
    }
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     STATUS / TOAST
  ═══════════════════════════════════════════════════════════════════════════ */

  function showSuccess(title, body) {
    setStatus('success', title, body);
  }

  function showError(title, body) {
    setStatus('error', title, body);
  }

  function setStatus(type, title, body) {
    dom.statusCard.hidden = false;
    dom.statusCard.classList.remove('is-leaving');
    dom.statusCard.className = `brn-status-card brn-status-${type}`;
    dom.statusTitle.textContent = title;
    dom.statusBody.textContent = body || '';

    dom.statusIcon.innerHTML = type === 'success'
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

    // Ensure a single dismissible close button (build once, reused across calls).
    let closeBtn = dom.statusCard.querySelector('.brn-status-close');
    if (!closeBtn) {
      closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'brn-status-close';
      closeBtn.setAttribute('aria-label', 'Dismiss notification');
      closeBtn.textContent = '×';
      closeBtn.addEventListener('click', hideStatus);
      dom.statusCard.appendChild(closeBtn);
    }

    window.clearTimeout(dom.statusCard._hideTimer);
    dom.statusCard._hideTimer = window.setTimeout(hideStatus, 6000);
  }

  function hideStatus() {
    if (dom.statusCard.hidden) return;
    dom.statusCard.classList.add('is-leaving');
    window.clearTimeout(dom.statusCard._hideTimer);
    dom.statusCard.addEventListener('animationend', () => {
      dom.statusCard.hidden = true;
      dom.statusCard.classList.remove('is-leaving');
    }, { once: true });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     UTIL
  ═══════════════════════════════════════════════════════════════════════════ */

  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     BOOT
  ═══════════════════════════════════════════════════════════════════════════ */

  document.addEventListener('DOMContentLoaded', initialize);

})();