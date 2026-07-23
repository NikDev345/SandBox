/**
 * ============================================================
 * Commit AI — AI Commit Message Generator
 * Vanilla JS: form state, validation, API integration, rendering
 * ============================================================
 */

(() => {
  'use strict';

  /* ────────────────────────────────────────────────────────
     CONFIG
     ──────────────────────────────────────────────────────── */
  const API_ENDPOINT = '/commit-message/generate';

  const LOADING_MESSAGES = [
    'Analyzing repository…',
    'Reading git diff…',
    'Generating AI commit messages…'
  ];

  /* ────────────────────────────────────────────────────────
     STATE
     ──────────────────────────────────────────────────────── */
  const state = {
    diffType: 'auto',
    style: 'conventional',
    suggestions: 3,
    lastResponse: null
  };

  /* ────────────────────────────────────────────────────────
     DOM REFERENCES
     ──────────────────────────────────────────────────────── */
  const el = {
    form: document.getElementById('generatorForm'),
    repoPath: document.getElementById('repoPath'),
    repoPathError: document.getElementById('repoPathError'),
    browseBtn: document.getElementById('browseBtn'),
    folderInput: document.getElementById('folderInput'),

    segmented: document.getElementById('diffTypeSegmented'),
    segmentedIndicator: document.getElementById('segmentedIndicator'),

    styleCards: document.getElementById('styleCards'),

    slider: document.getElementById('suggestionsSlider'),
    sliderValue: document.getElementById('suggestionsValue'),

    generateBtn: document.getElementById('generateBtn'),

    emptyState: document.getElementById('emptyState'),
    loadingState: document.getElementById('loadingState'),
    errorState: document.getElementById('errorState'),
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),
    responseSection: document.getElementById('responseSection'),
    thinkingLabel: document.getElementById('thinkingLabel'),

    statRepoName: document.getElementById('statRepoName'),
    statBranch: document.getElementById('statBranch'),
    statDiffType: document.getElementById('statDiffType'),
    statFilesChanged: document.getElementById('statFilesChanged'),

    suggestionsList: document.getElementById('suggestionsList'),
    suggestionTemplate: document.getElementById('suggestionCardTemplate'),
    regenerateAllBtn: document.getElementById('regenerateAllBtn'),

    toastContainer: document.getElementById('toastContainer'),
    mouseGlow: document.getElementById('mouseGlow'),
    particleCanvas: document.getElementById('particleCanvas')
  };

  /* ────────────────────────────────────────────────────────
     TOASTS
     ──────────────────────────────────────────────────────── */
  const TOAST_ICONS = {
    success: 'fa-solid fa-circle-check',
    error: 'fa-solid fa-circle-exclamation',
    warning: 'fa-solid fa-triangle-exclamation',
    info: 'fa-solid fa-circle-info'
  };

  function showToast(message, type = 'info', duration = 3200) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.setProperty('--toast-duration', `${duration}ms`);

    toast.innerHTML = `
      <i class="toast-icon ${TOAST_ICONS[type] || TOAST_ICONS.info}"></i>
      <span class="toast-text"></span>
      <button class="toast-close" type="button" aria-label="Dismiss"><i class="fa-solid fa-xmark"></i></button>
    `;
    toast.querySelector('.toast-text').textContent = message;

    el.toastContainer.appendChild(toast);

    const removeToast = () => {
      toast.classList.add('removing');
      setTimeout(() => toast.remove(), 220);
    };

    toast.querySelector('.toast-close').addEventListener('click', removeToast);
    const timer = setTimeout(removeToast, duration);
    toast.addEventListener('mouseenter', () => clearTimeout(timer));

    return toast;
  }

  // Guard localStorage in case of restricted environments (artifacts/sandboxes)
  function localStorageSafeGet(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }
  function localStorageSafeSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* no-op */ }
  }

  /* ────────────────────────────────────────────────────────
     SEGMENTED CONTROL — Diff Type
     ──────────────────────────────────────────────────────── */
  function initSegmentedControl() {
    const options = Array.from(el.segmented.querySelectorAll('.segmented-option'));

    function moveIndicator(target) {
      const index = options.indexOf(target);
      el.segmentedIndicator.style.transform = `translateX(${index * 100}%)`;
    }

    options.forEach((btn) => {
      btn.addEventListener('click', () => {
        options.forEach((o) => { o.classList.remove('active'); o.setAttribute('aria-checked', 'false'); });
        btn.classList.add('active');
        btn.setAttribute('aria-checked', 'true');
        state.diffType = btn.dataset.value;
        moveIndicator(btn);
      });
    });

    // Set initial position after layout is ready
    requestAnimationFrame(() => moveIndicator(el.segmented.querySelector('.segmented-option.active')));
    window.addEventListener('resize', () => moveIndicator(el.segmented.querySelector('.segmented-option.active')));
  }

  /* ────────────────────────────────────────────────────────
     STYLE CARDS — Commit Style
     ──────────────────────────────────────────────────────── */
  function initStyleCards() {
    const cards = Array.from(el.styleCards.querySelectorAll('.style-card'));
    cards.forEach((card) => {
      card.addEventListener('click', () => {
        cards.forEach((c) => { c.classList.remove('active'); c.setAttribute('aria-checked', 'false'); });
        card.classList.add('active');
        card.setAttribute('aria-checked', 'true');
        state.style = card.dataset.value;
      });
    });
  }

  /* ────────────────────────────────────────────────────────
     SLIDER — Number of Suggestions
     ──────────────────────────────────────────────────────── */
  function initSlider() {
    const update = () => {
      const min = Number(el.slider.min);
      const max = Number(el.slider.max);
      const value = Number(el.slider.value);
      const percent = ((value - min) / (max - min)) * 100;
      el.slider.style.setProperty('--fill', `${percent}%`);
      el.sliderValue.textContent = value;
      state.suggestions = value;
    };
    el.slider.addEventListener('input', update);
    update();
  }

  /* ────────────────────────────────────────────────────────
     REPOSITORY PATH — Validation + Browse
     ──────────────────────────────────────────────────────── */
  function initRepoPath() {
    el.repoPath.addEventListener('input', () => clearFieldError());

    el.browseBtn.addEventListener('click', async () => {
      // Prefer the File System Access API (Chromium) for a native folder picker.
      if (window.showDirectoryPicker) {
        try {
          const handle = await window.showDirectoryPicker();
          el.repoPath.value = handle.name;
          clearFieldError();
          showToast(`Browser can't access the full path. Please type the complete path manually (e.g. /home/user/${folderName})`, 'warning', 5000);
        } catch (err) {
          // User cancelled the picker — no action needed.
        }
        return;
      }
      // Fallback: hidden webkitdirectory input (browser only exposes a relative path).
      el.folderInput.click();
    });

    el.folderInput.addEventListener('change', () => {
      const files = el.folderInput.files;
      if (files && files.length > 0) {
        const relativePath = files[0].webkitRelativePath || '';
        const folderName = relativePath.split('/')[0] || files[0].name;
        el.repoPath.value = folderName;
        clearFieldError();
        showToast(`Browser can't access the full path. Please type the complete path manually (e.g. /home/user/${folderName})`, 'warning', 5000);
      }
    });
  }

  function setFieldError() {
    el.repoPath.classList.add('input-error');
    el.repoPathError.classList.add('visible');
  }
  function clearFieldError() {
    el.repoPath.classList.remove('input-error');
    el.repoPathError.classList.remove('visible');
  }

  /* ────────────────────────────────────────────────────────
     FORM SUBMISSION / GENERATION FLOW
     ──────────────────────────────────────────────────────── */
  function initForm() {
    el.form.addEventListener('submit', (e) => {
      e.preventDefault();
      handleGenerate();
    });

    el.retryBtn.addEventListener('click', handleGenerate);
    el.regenerateAllBtn.addEventListener('click', handleGenerate);
  }

  function validateForm() {
    const path = el.repoPath.value.trim();
    if (!path) {
      setFieldError();
      el.repoPath.focus();
      return false;
    }
    clearFieldError();
    return true;
  }

  async function handleGenerate() {
    if (!validateForm()) return;

    setFormDisabled(true);
    showState('loading');
    animateLoadingMessages();

    const payload = {
      repository_path: el.repoPath.value.trim(),
      diff_type: state.diffType,
      style: state.style,
      suggestions: state.suggestions
    };

    try {
      const data = await requestCommitMessages(payload);
      state.lastResponse = data;
      renderResponse(data);
      showState('response');
      showToast('Commit messages generated successfully.', 'success');
    } catch (err) {
      showError(err.message || 'Something went wrong while generating commit messages.');
      showState('error');
      showToast('Failed to generate commit messages.', 'error');
    } finally {
      setFormDisabled(false);
      stopLoadingMessages();
    }
  }

  async function requestCommitMessages(payload) {
    let response;
    try {
      response = await fetch(API_ENDPOINT, {
        method: 'POST',
        credentials: "include",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (networkErr) {
      throw new Error('Could not reach the server. Check your connection and try again.');
    }

    let body = null;
    try { body = await response.json(); } catch (parseErr) { /* no body */ }

    if (!response.ok) {
      const detail = (body && (body.detail || body.message)) || `Request failed with status ${response.status}.`;
      throw new Error(detail);
    }

    return body;
  }

  function setFormDisabled(disabled) {
    Array.from(el.form.elements).forEach((field) => { field.disabled = disabled; });
    el.segmented.querySelectorAll('.segmented-option').forEach((b) => { b.disabled = disabled; });
    el.styleCards.querySelectorAll('.style-card').forEach((b) => { b.disabled = disabled; });
    el.browseBtn.disabled = disabled;

    el.generateBtn.classList.toggle('is-loading', disabled);
    if (disabled) {
      el.generateBtn.dataset.originalHtml = el.generateBtn.innerHTML;
      el.generateBtn.innerHTML = '<span class="btn-spinner"></span><span>Generating…</span>';
    } else if (el.generateBtn.dataset.originalHtml) {
      el.generateBtn.innerHTML = el.generateBtn.dataset.originalHtml;
    }
  }

  /* ────────────────────────────────────────────────────────
     LOADING MESSAGE ANIMATION
     ──────────────────────────────────────────────────────── */
  let loadingInterval = null;

  function animateLoadingMessages() {
    let index = 0;
    el.thinkingLabel.textContent = LOADING_MESSAGES[0];
    el.thinkingLabel.style.opacity = '1';

    loadingInterval = setInterval(() => {
      index = (index + 1) % LOADING_MESSAGES.length;
      el.thinkingLabel.style.opacity = '0';
      setTimeout(() => {
        el.thinkingLabel.textContent = LOADING_MESSAGES[index];
        el.thinkingLabel.style.opacity = '1';
      }, 200);
    }, 1400);
  }

  function stopLoadingMessages() {
    if (loadingInterval) {
      clearInterval(loadingInterval);
      loadingInterval = null;
    }
  }

  /* ────────────────────────────────────────────────────────
     STATE VISIBILITY (empty / loading / error / response)
     ──────────────────────────────────────────────────────── */
  function showState(name) {
    el.emptyState.classList.add('hidden');
    el.loadingState.classList.add('hidden');
    el.errorState.classList.add('hidden');
    el.responseSection.classList.add('hidden');

    const map = {
      empty: el.emptyState,
      loading: el.loadingState,
      error: el.errorState,
      response: el.responseSection
    };
    const target = map[name];
    if (target) target.classList.remove('hidden');
  }

  function showError(message) {
    el.errorMessage.textContent = message;
  }

  /* ────────────────────────────────────────────────────────
     RENDER RESPONSE
     ──────────────────────────────────────────────────────── */
  function renderResponse(data) {
    el.statRepoName.textContent = data.repository_name ?? '—';
    el.statBranch.textContent = data.branch ?? '—';
    el.statDiffType.textContent = capitalize(data.diff_type ?? '—');
    el.statFilesChanged.textContent = (data.files_changed ?? 0).toString();

    el.suggestionsList.innerHTML = '';
    (data.suggestions || []).forEach((suggestion, i) => {
      const card = buildSuggestionCard(suggestion.message, i + 1);
      el.suggestionsList.appendChild(card);
    });
  }

  function buildSuggestionCard(message, index) {
    const fragment = el.suggestionTemplate.content.cloneNode(true);
    const card = fragment.querySelector('.suggestion-card');
    const indexEl = fragment.querySelector('.suggestion-index');
    const messageEl = fragment.querySelector('.suggestion-message');
    const copyMsgBtn = fragment.querySelector('.btn-copy-message');
    const copyCmdBtn = fragment.querySelector('.btn-copy-command');
    const regenBtn = fragment.querySelector('.btn-regenerate-one');

    indexEl.textContent = String(index).padStart(2, '0');
    messageEl.textContent = message;

    copyMsgBtn.addEventListener('click', () => copyToClipboard(message, copyMsgBtn, 'Message copied to clipboard.'));

    copyCmdBtn.addEventListener('click', () => {
      const command = `git commit -m "${message.replace(/"/g, '\\"')}"`;
      copyToClipboard(command, copyCmdBtn, 'Git command copied to clipboard.');
    });

    regenBtn.addEventListener('click', () => handleRegenerateOne(card));

    return fragment;
  }

  async function handleRegenerateOne(cardEl) {
    // The API generates a full batch rather than a single message, so a per-card
    // regenerate re-runs the whole generation and refreshes the list.
    cardEl.classList.add('regenerating');
    try {
      await handleGenerate();
    } finally {
      // handleGenerate re-renders the entire list, so nothing further to clean up here.
    }
  }

  /* ────────────────────────────────────────────────────────
     CLIPBOARD
     ──────────────────────────────────────────────────────── */
  async function copyToClipboard(text, triggerBtn, successMessage) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        fallbackCopy(text);
      }
      flashButtonSuccess(triggerBtn);
      showToast(successMessage, 'success', 2200);
    } catch (err) {
      showToast('Could not copy to clipboard.', 'error');
    }
  }

  function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }

  function flashButtonSuccess(btn) {
    if (!btn) return;
    const originalHtml = btn.innerHTML;
    const iconEl = btn.querySelector('i');
    const originalIconClass = iconEl ? iconEl.className : '';

    btn.classList.add('success-flash');
    if (iconEl) iconEl.className = 'fa-solid fa-check';

    setTimeout(() => {
      btn.classList.remove('success-flash');
      if (iconEl) iconEl.className = originalIconClass;
    }, 1400);
  }

  /* ────────────────────────────────────────────────────────
     UTILITIES
     ──────────────────────────────────────────────────────── */
  function capitalize(str) {
    if (!str) return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  /* ────────────────────────────────────────────────────────
     AMBIENT BACKGROUND — MOUSE GLOW + PARTICLES
     ──────────────────────────────────────────────────────── */
  function initMouseGlow() {
    let raf = null;
    document.addEventListener('mousemove', (e) => {
      el.mouseGlow.style.opacity = '1';
      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        el.mouseGlow.style.left = `${e.clientX}px`;
        el.mouseGlow.style.top = `${e.clientY}px`;
      });
    });
    document.addEventListener('mouseleave', () => { el.mouseGlow.style.opacity = '0'; });
  }

  function initParticles() {
    const canvas = el.particleCanvas;
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext('2d');
    let width, height, particles;

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }

    function createParticles() {
      const count = Math.min(60, Math.floor((width * height) / 30000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 1.4 + 0.4,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        alpha: Math.random() * 0.4 + 0.1
      }));
    }

    function tick() {
      ctx.clearRect(0, 0, width, height);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(148, 163, 184, ${p.alpha})`;
        ctx.fill();
      });
      requestAnimationFrame(tick);
    }

    resize();
    createParticles();
    tick();

    window.addEventListener('resize', () => {
      resize();
      createParticles();
    });
  }

  /* ────────────────────────────────────────────────────────
     INIT
     ──────────────────────────────────────────────────────── */
  function init() {
    initSegmentedControl();
    initStyleCards();
    initSlider();
    initRepoPath();
    initForm();
    initMouseGlow();
    initParticles();
    showState('empty');
  }

  document.addEventListener('DOMContentLoaded', init);
})();