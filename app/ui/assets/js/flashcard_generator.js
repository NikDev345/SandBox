/**
 * flashcard_generator.js
 * Production-grade Flashcard Generator for SandBox AI SaaS Platform
 * ──────────────────────────────────────────────────────────────────
 * Works with: flashcard_generator.html + flashcard_generator.css + FastAPI backend
 * API: POST /flashcard-generator/generate  (JSON body, Bearer token auth)
 */

(() => {
  'use strict';

  // ─────────────────────────────────────────────────────────────
  // CONSTANTS
  // ─────────────────────────────────────────────────────────────

  const API_ENDPOINT = '/flashcard-generator/generate';
  const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB
  const ACCEPTED_TEXT_EXTS = ['.txt', '.md'];
  const BLOCKED_EXTS = ['.pdf', '.docx'];
  const LOADING_STEP_INTERVAL_MS = 1800;

  const CARD_TYPE_LABELS = {
    basic:       'Basic',
    cloze:       'Cloze',
    definition:  'Definition',
    concept:     'Concept',
    interview:   'Interview',
    mixed:       'Mixed',
  };

  const DIFFICULTY_LABELS = {
    easy:   'Easy',
    medium: 'Medium',
    hard:   'Hard',
    mixed:  'Mixed',
  };

  // Study time estimate: ~30s per card for average learner
  const SECONDS_PER_CARD = 30;

  // ─────────────────────────────────────────────────────────────
  // STATE
  // ─────────────────────────────────────────────────────────────

  const state = {
    mode: 'paste',             // 'paste' | 'upload'
    file: null,                // File object (txt/md only)
    extractedText: '',         // text extracted from file client-side
    config: {
      number_of_cards:    10,
      difficulty:         'medium',
      card_type:          'mixed',
      language:           'english',
      include_examples:   true,
      include_memory_tips:true,
      include_keywords:   true,
      include_tags:       true,
      shuffle_cards:      false,
    },
    result: null,              // full backend result object
    flashcards: [],            // active (possibly shuffled) flashcard array
    currentIndex: 0,
    isFlipped: false,
    isAnimating: false,
    flipAngle: {},             // per-card flip angle state
    loadingStepTimer: null,
    rotatorTimer: null,
    rotatorIndex: 0,
    lastRequestPayload: null,  // saved for regenerate
  };

  // ─────────────────────────────────────────────────────────────
  // DOM CACHE
  // ─────────────────────────────────────────────────────────────

  let dom = {};

  const cacheDOM = () => {
    dom = {
      // Phases
      phaseInput:   document.getElementById('fc-phase-input'),
      phaseConfig:  document.getElementById('fc-phase-config'),
      phaseViewer:  document.getElementById('fc-phase-viewer'),
      phaseError:   document.getElementById('fc-phase-error'),
      loadingOverlay: document.getElementById('fc-loading-overlay'),

      // Hero rotator
      rotatorTrack: document.getElementById('fc-rotator-track'),

      // Mode selector
      modePaste:  document.getElementById('fc-mode-paste'),
      modeUpload: document.getElementById('fc-mode-upload'),
      modePill:   document.getElementById('fc-mode-pill'),
      panelPaste: document.getElementById('fc-panel-paste'),
      panelUpload:document.getElementById('fc-panel-upload'),

      // Paste panel
      contentInput: document.getElementById('fc-content-input'),
      charCount:    document.getElementById('fc-char-count'),
      wordCount:    document.getElementById('fc-word-count'),

      // Upload zone
      uploadZone:   document.getElementById('fc-upload-zone'),
      fileInput:    document.getElementById('fc-file-input'),
      uploadIdle:   document.getElementById('fc-upload-idle'),
      uploadFile:   document.getElementById('fc-upload-file'),
      uploadNotice: document.getElementById('fc-upload-notice'),
      fileName:     document.getElementById('fc-file-name'),
      fileSize:     document.getElementById('fc-file-size'),
      fileRemove:   document.getElementById('fc-file-remove'),

      // Input actions
      continueBtn: document.getElementById('fc-continue-btn'),

      // Config
      backBtn:       document.getElementById('fc-back-btn'),
      countSlider:   document.getElementById('fc-count-slider'),
      countValue:    document.getElementById('fc-count-value'),
      languageSelect:document.getElementById('fc-language-select'),
      generateBtn:   document.getElementById('fc-generate-btn'),
      loadingSteps:  document.getElementById('fc-loading-steps'),

      // Viewer
      actionBar:     document.querySelector('.fc-action-bar'),
      deckTitle:     document.getElementById('fc-deck-title'),
      cardCounter:   document.getElementById('fc-card-counter'),
      progressFill:  document.getElementById('fc-progress-fill'),
      progressBar:   document.getElementById('fc-progress-bar'),
      emptyState:    document.getElementById('fc-empty-state'),
      stage:         document.getElementById('fc-stage'),
      deck:          document.getElementById('fc-deck'),
      prevBtn:       document.getElementById('fc-prev-btn'),
      nextBtn:       document.getElementById('fc-next-btn'),
      dotsWrap:      document.getElementById('fc-dots'),
      quitBtn:       document.getElementById('fc-quit-btn'),
      copyCardBtn:   document.getElementById('fc-copy-card-btn'),
      copyAllBtn:    document.getElementById('fc-copy-all-btn'),
      shuffleBtn:    document.getElementById('fc-shuffle-btn'),
      downloadJsonBtn: document.getElementById('fc-download-json-btn'),
      downloadMdBtn: document.getElementById('fc-download-md-btn'),
      printBtn:      document.getElementById('fc-print-btn'),
      regenerateBtn: document.getElementById('fc-regenerate-btn'),

      // Summary
      statTotal:      document.getElementById('fc-stat-total'),
      statTime:       document.getElementById('fc-stat-time'),
      statCategories: document.getElementById('fc-stat-categories'),
      statKeywords:   document.getElementById('fc-stat-keywords'),
      summaryKeywords:document.getElementById('fc-summary-keywords'),
      keywordChips:   document.getElementById('fc-keyword-chips'),

      // Error
      errorMessage:  document.getElementById('fc-error-message'),
      errorBackBtn:  document.getElementById('fc-error-back-btn'),
      errorRetryBtn: document.getElementById('fc-error-retry-btn'),
    };
  };

  // ─────────────────────────────────────────────────────────────
  // PHASE NAVIGATION
  // ─────────────────────────────────────────────────────────────

  const allPhases = () => [
    dom.phaseInput,
    dom.phaseConfig,
    dom.phaseViewer,
    dom.phaseError,
  ];

  const showPhase = (phase) => {
    allPhases().forEach(p => {
      const isTarget = p === phase;
      p.classList.toggle('fc-phase--hidden', !isTarget);
      if (!isTarget) {
        p.setAttribute('aria-hidden', 'true');
      } else {
        p.removeAttribute('aria-hidden');
      }
    });
    phase.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // ─────────────────────────────────────────────────────────────
  // HERO ROTATOR
  // ─────────────────────────────────────────────────────────────

  const initRotator = () => {
    const track = dom.rotatorTrack;
    if (!track) return;

    const words = track.querySelectorAll('.fc-rotator-word');
    if (!words.length) return;

    let index = 0;

    state.rotatorTimer = setInterval(() => {
      index = (index + 1) % words.length;
      track.style.transform = `translateY(-${index * 1.2}em)`;
    }, 1600);
  };

  // ─────────────────────────────────────────────────────────────
  // MODE SWITCH
  // ─────────────────────────────────────────────────────────────

  const setMode = (mode) => {
    state.mode = mode;
    const isPaste = mode === 'paste';

    dom.modePaste.classList.toggle('fc-mode-btn--active', isPaste);
    dom.modeUpload.classList.toggle('fc-mode-btn--active', !isPaste);
    dom.modePaste.setAttribute('aria-selected', String(isPaste));
    dom.modeUpload.setAttribute('aria-selected', String(!isPaste));

    dom.panelPaste.classList.toggle('fc-panel--hidden', !isPaste);
    dom.panelUpload.classList.toggle('fc-panel--hidden', isPaste);

    // Animate sliding pill
    const activeBtn = isPaste ? dom.modePaste : dom.modeUpload;
    dom.modePill.style.width = `${activeBtn.offsetWidth}px`;
    dom.modePill.style.left  = `${activeBtn.offsetLeft}px`;

    updateContinueBtn();
  };

  const initModePill = () => {
    const activeBtn = dom.modePaste;
    dom.modePill.style.width = `${activeBtn.offsetWidth}px`;
    dom.modePill.style.left  = `${activeBtn.offsetLeft}px`;
  };

  // ─────────────────────────────────────────────────────────────
  // UPLOAD HANDLER
  // ─────────────────────────────────────────────────────────────

  const handleUpload = (file) => {
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();

    // Blocked types — show inline notice, don't accept
    if (BLOCKED_EXTS.includes(ext)) {
      dom.uploadNotice.hidden = false;
      toast('PDF and DOCX parsing is coming soon. Please use TXT or Markdown, or paste your content.', 'info');
      return;
    }

    if (!ACCEPTED_TEXT_EXTS.includes(ext)) {
      toast(`Unsupported file type. Please upload: ${ACCEPTED_TEXT_EXTS.join(', ')}`, 'error');
      return;
    }

    if (file.size > MAX_FILE_BYTES) {
      toast('File too large. Maximum size is 10 MB.', 'error');
      return;
    }

    // Read text client-side
    const reader = new FileReader();
    reader.onload = (e) => {
      state.extractedText = e.target.result;
      state.file = file;

      dom.fileName.textContent = file.name;
      dom.fileSize.textContent = formatBytes(file.size);
      dom.uploadIdle.hidden = true;
      dom.uploadFile.hidden = false;
      dom.uploadNotice.hidden = true;
      dom.uploadZone.classList.add('fc-upload-zone--has-file');
      updateContinueBtn();
    };
    reader.onerror = () => {
      toast('Failed to read file. Please try again.', 'error');
    };
    reader.readAsText(file);
  };

  const clearUpload = () => {
    state.file = null;
    state.extractedText = '';
    dom.fileInput.value = '';
    dom.uploadIdle.hidden = false;
    dom.uploadFile.hidden = true;
    dom.uploadNotice.hidden = true;
    dom.uploadZone.classList.remove('fc-upload-zone--has-file');
    updateContinueBtn();
  };

  // ─────────────────────────────────────────────────────────────
  // CONTINUE BUTTON STATE
  // ─────────────────────────────────────────────────────────────

  const updateContinueBtn = () => {
    const ready = state.mode === 'paste'
      ? dom.contentInput.value.trim().length > 10
      : !!state.file;

    dom.continueBtn.disabled = !ready;
    dom.continueBtn.setAttribute('aria-disabled', String(!ready));
  };

  // ─────────────────────────────────────────────────────────────
  // LOADING OVERLAY
  // ─────────────────────────────────────────────────────────────

  const showLoader = () => {
    dom.loadingOverlay.hidden = false;
    dom.loadingOverlay.removeAttribute('aria-hidden');

    const steps = dom.loadingSteps.querySelectorAll('.fc-step');
    steps.forEach(s => s.classList.remove('fc-step--active', 'fc-step--done'));

    let currentStep = 0;
    steps[0]?.classList.add('fc-step--active');

    state.loadingStepTimer = setInterval(() => {
      steps[currentStep]?.classList.replace('fc-step--active', 'fc-step--done');
      currentStep++;
      if (currentStep < steps.length) {
        steps[currentStep].classList.add('fc-step--active');
      } else {
        clearInterval(state.loadingStepTimer);
      }
    }, LOADING_STEP_INTERVAL_MS);
  };

  const hideLoader = () => {
    clearInterval(state.loadingStepTimer);
    dom.loadingOverlay.hidden = true;
    dom.loadingOverlay.setAttribute('aria-hidden', 'true');
  };

  // ─────────────────────────────────────────────────────────────
  // SHOW ERROR
  // ─────────────────────────────────────────────────────────────

  const showError = (message) => {
    dom.errorMessage.textContent = message || 'Something went wrong. Please try again.';
    showPhase(dom.phaseError);
  };

  // ─────────────────────────────────────────────────────────────
  // GENERATE FLASHCARDS — API CALL
  // ─────────────────────────────────────────────────────────────

  const generateFlashcards = async (payload) => {
    if (!payload) {
      payload = buildPayload();
      if (!payload) return;
      state.lastRequestPayload = payload;
    }

    showLoader();
    dom.generateBtn.disabled = true;

    // Retrieve token from cookie (sandbox session pattern)
    const token = getAuthToken();

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(
          data?.error || data?.detail || data?.message || `Server error ${response.status}`
        );
      }

      state.result = data.result;
      state.flashcards = [...(data.result?.flashcards ?? [])];

      if (state.config.shuffle_cards) {
        shuffleArray(state.flashcards);
      }

      hideLoader();
      renderViewer();
      showPhase(dom.phaseViewer);

      if (data.warning) {
        toast(data.warning, 'info');
      }

    } catch (err) {
      hideLoader();
      console.error('[FlashcardGenerator] API error:', err);
      showError(err.message || 'Failed to generate flashcards. Please try again.');
    } finally {
      dom.generateBtn.disabled = false;
    }
  };

  const buildPayload = () => {
    const cfg = state.config;
    let content = '';

    if (state.mode === 'paste') {
      content = dom.contentInput.value.trim();
      if (!content) {
        toast('Please paste some content first.', 'error');
        return null;
      }
    } else {
      content = state.extractedText.trim();
      if (!content) {
        toast('Please upload a file first.', 'error');
        return null;
      }
    }

    return {
      content,
      settings: {
        number_of_cards:     cfg.number_of_cards,
        difficulty:          cfg.difficulty,
        card_type:           cfg.card_type,
        language:            cfg.language,
        include_examples:    cfg.include_examples,
        include_memory_tips: cfg.include_memory_tips,
        include_keywords:    cfg.include_keywords,
        include_tags:        cfg.include_tags,
        // shuffle_cards is NOT sent to backend — applied client-side after generation
      },
    };
  };

  // ─────────────────────────────────────────────────────────────
  // AUTH TOKEN HELPER
  // ─────────────────────────────────────────────────────────────

  const getAuthToken = () => {
    // Try meta tag first (NiceGUI pattern)
    const meta = document.querySelector('meta[name="auth-token"]');
    if (meta) return meta.content;

    // Try cookie
    const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : null;
  };

  // ─────────────────────────────────────────────────────────────
  // VIEWER RENDERING
  // ─────────────────────────────────────────────────────────────

  const renderViewer = () => {
    const cards = state.flashcards;
    const result = state.result;

    // Title
    dom.deckTitle.textContent = result?.title ?? 'Flashcard Deck';

    // Summary stats
    const total = cards.length;
    const studyMins = Math.ceil((total * SECONDS_PER_CARD) / 60);
    const studyLabel = studyMins < 60
      ? `~${studyMins} min`
      : `~${Math.floor(studyMins / 60)}h ${studyMins % 60}m`;

    dom.statTotal.textContent = total;
    dom.statTime.textContent  = studyLabel;

    // Categories from statistics
    const stats = result?.statistics;
    if (stats) {
      const cats = stats.categories?.length ?? 0;
      dom.statCategories.textContent = cats > 0 ? cats : '—';

      const kws = stats.total_keywords ?? stats.keywords?.length ?? 0;
      dom.statKeywords.textContent = kws > 0 ? kws : '—';

      // Keyword chips
      if (stats.keywords?.length) {
        dom.summaryKeywords.hidden = false;
        dom.keywordChips.innerHTML = '';
        stats.keywords.slice(0, 20).forEach(kw => {
          const chip = document.createElement('span');
          chip.className = 'fc-keyword-chip';
          chip.textContent = kw;
          dom.keywordChips.appendChild(chip);
        });
      } else {
        dom.summaryKeywords.hidden = true;
      }
    } else {
      // Derive from cards
      const categories = [...new Set(cards.map(c => c.category).filter(Boolean))];
      dom.statCategories.textContent = categories.length > 0 ? categories.length : '—';

      const allKeywords = [...new Set(cards.flatMap(c => c.keywords ?? []))];
      dom.statKeywords.textContent = allKeywords.length > 0 ? allKeywords.length : '—';

      if (allKeywords.length) {
        dom.summaryKeywords.hidden = false;
        dom.keywordChips.innerHTML = '';
        allKeywords.slice(0, 20).forEach(kw => {
          const chip = document.createElement('span');
          chip.className = 'fc-keyword-chip';
          chip.textContent = kw;
          dom.keywordChips.appendChild(chip);
        });
      }
    }

    // Reset card state
    state.currentIndex = 0;
    state.isFlipped = false;
    state.flipAngle = {};

    // Build deck
    renderDeck(true);
  };

  // ─────────────────────────────────────────────────────────────
  // DECK RENDERING
  // ─────────────────────────────────────────────────────────────

  const renderDeck = (withIntro) => {
    dom.deck.innerHTML = '';
    const cards = state.flashcards;

    if (!cards.length) {
      dom.emptyState.hidden = false;
      return;
    }

    dom.emptyState.hidden = true;

    cards.forEach((cardData, i) => {
      const el = buildCard(cardData, i);
      dom.deck.appendChild(el);
    });

    positionCards(withIntro);
    updateProgress();
  };

  const buildCard = (cardData, index) => {
    const card = document.createElement('div');
    card.className = 'fc-card';
    card.dataset.index = index;

    const difficultyBadgeHTML = cardData.difficulty
      ? `<span class="fc-difficulty-badge fc-difficulty-badge--${cardData.difficulty}">${escapeHTML(DIFFICULTY_LABELS[cardData.difficulty] ?? cardData.difficulty)}</span>`
      : '';

    const categoryHTML = cardData.category
      ? `<span class="fc-card-category">${escapeHTML(cardData.category)}</span>`
      : '';

    const exampleHTML = cardData.example
      ? `<div class="fc-face-extra"><span class="fc-face-extra-label">Example</span>${escapeHTML(cardData.example)}</div>`
      : '';

    const memTipHTML = cardData.memory_tip
      ? `<div class="fc-face-extra"><span class="fc-face-extra-label">Memory Tip 💡</span>${escapeHTML(cardData.memory_tip)}</div>`
      : '';

    const cardTypeLabel = CARD_TYPE_LABELS[cardData.card_type] ?? cardData.card_type ?? 'Card';

    card.innerHTML = `
      <div class="fc-card-inner">
        <div class="fc-card-face fc-card-face--front">
          <div class="fc-face-header">
            <div class="fc-face-kicker">
              <span>${escapeHTML(cardTypeLabel)}</span>
              <span class="fc-face-tag">Card ${index + 1}</span>
            </div>
            ${difficultyBadgeHTML}
          </div>
          <div class="fc-face-body">
            <p>${escapeHTML(cardData.front)}</p>
          </div>
          <div class="fc-face-footer">
            <svg viewBox="0 0 24 24" fill="none"><path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 15v.01M12 7a3 3 0 013 3c0 2-3 2.5-3 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            Tap or drag to flip
          </div>
        </div>
        <div class="fc-card-face fc-card-face--back">
          <div class="fc-face-header">
            <div class="fc-face-kicker">
              <span>Answer</span>
              <span class="fc-face-tag">Card ${index + 1}</span>
            </div>
            ${categoryHTML}
          </div>
          <div class="fc-face-body">
            <p>${escapeHTML(cardData.back)}</p>
          </div>
          ${exampleHTML || memTipHTML ? `<div class="fc-face-extras">${exampleHTML}${memTipHTML}</div>` : ''}
          <div class="fc-face-footer">
            <svg viewBox="0 0 24 24" fill="none"><path d="M21 12a9 9 0 11-3.2-6.9M21 4v5h-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Tap or drag to flip back
          </div>
        </div>
      </div>
    `;

    attachFlipGestures(card);
    return card;
  };

  // ─────────────────────────────────────────────────────────────
  // FLIP MECHANICS (from new.js — production 3D flip with angle tracking)
  // ─────────────────────────────────────────────────────────────

  const getInner = (card) => card.querySelector('.fc-card-inner');

  const setAngle = (card, angle, withTransition) => {
    const inner = getInner(card);
    if (!inner) return;

    inner.style.transition = withTransition
      ? 'transform 0.5s cubic-bezier(0.2, 0.85, 0.32, 1.15)'
      : 'none';
    inner.style.transform = `rotateY(${angle}deg)`;

    // Explicitly control face visibility based on angle — don't trust
    // native backface-visibility under box-shadow/filter in Chromium.
    const normalized = ((angle % 360) + 360) % 360;
    const frontIsForward = normalized <= 90 || normalized >= 270;

    const front = card.querySelector('.fc-card-face--front');
    const back  = card.querySelector('.fc-card-face--back');

    if (front) {
      front.style.transition = 'opacity 0.08s linear';
      front.style.opacity    = frontIsForward ? '1' : '0';
      front.style.visibility = frontIsForward ? 'visible' : 'hidden';
    }
    if (back) {
      back.style.transition = 'opacity 0.08s linear';
      back.style.opacity    = frontIsForward ? '0' : '1';
      back.style.visibility = frontIsForward ? 'hidden' : 'visible';
    }
  };

  const attachFlipGestures = (card) => {
    const inner = getInner(card);
    if (!inner) return;

    let dragging = false;
    let startX = 0;
    let startAngle = 0;
    let moved = false;
    let wheelSettleTimer = null;

    const isActiveCard = () =>
      parseInt(card.dataset.index, 10) === state.currentIndex && !state.isAnimating;

    const currentAngle = () =>
      state.flipAngle[state.currentIndex] ?? (state.isFlipped ? 180 : 0);

    const snapToNearest = () => {
      const angle = state.flipAngle[state.currentIndex] ?? currentAngle();
      const normalized = ((angle % 360) + 360) % 360;
      const snapped = normalized > 90 && normalized < 270 ? 180 : 0;
      state.isFlipped = snapped === 180;
      state.flipAngle[state.currentIndex] = snapped;
      setAngle(card, snapped, true);
      card.classList.toggle('is-flipped', state.isFlipped);
    };

    inner.addEventListener('pointerdown', (e) => {
      if (!isActiveCard()) return;
      dragging  = true;
      moved     = false;
      startX    = e.clientX;
      startAngle = currentAngle();
      inner.setPointerCapture?.(e.pointerId);
      setAngle(card, startAngle, false);
    });

    inner.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 4) moved = true;
      // 280px drag = full 180° flip
      let angle = startAngle - (dx / 280) * 180;
      angle = Math.max(-20, Math.min(200, angle));
      state.flipAngle[state.currentIndex] = angle;
      setAngle(card, angle, false);
    });

    const pointerUp = () => {
      if (!dragging) return;
      dragging = false;
      if (!moved) {
        flipCard();
        return;
      }
      snapToNearest();
    };

    inner.addEventListener('pointerup',     pointerUp);
    inner.addEventListener('pointercancel', pointerUp);

    // Scroll-wheel nudges the flip like a physical dial
    inner.addEventListener('wheel', (e) => {
      if (!isActiveCard()) return;
      e.preventDefault();
      const base  = state.flipAngle[state.currentIndex] ?? currentAngle();
      let angle   = base + e.deltaY * 0.6;
      angle       = Math.max(-20, Math.min(200, angle));
      state.flipAngle[state.currentIndex] = angle;
      setAngle(card, angle, false);

      clearTimeout(wheelSettleTimer);
      wheelSettleTimer = setTimeout(snapToNearest, 140);
    }, { passive: false });
  };

  // ─────────────────────────────────────────────────────────────
  // FLIP CARD
  // ─────────────────────────────────────────────────────────────

  const flipCard = () => {
    const activeCard = dom.deck.querySelector(`.fc-card[data-index="${state.currentIndex}"]`);
    if (!activeCard) return;

    state.isFlipped = !state.isFlipped;
    const angle = state.isFlipped ? 180 : 0;
    state.flipAngle[state.currentIndex] = angle;
    setAngle(activeCard, angle, true);
    activeCard.classList.toggle('is-flipped', state.isFlipped);
  };

  // ─────────────────────────────────────────────────────────────
  // CARD POSITIONING (stacked deck effect)
  // ─────────────────────────────────────────────────────────────

  const positionCards = (withIntro) => {
    const cards = Array.from(dom.deck.children);
    const ci = state.currentIndex;

    cards.forEach((card, i) => {
      card.classList.remove('is-flipped');
      setAngle(card, 0, false);

      let pos = 'hidden';
      if      (i === ci)     pos = 'active';
      else if (i === ci + 1) pos = 'next1';
      else if (i === ci - 1) pos = 'prev1';
      else if (i === ci + 2) pos = 'next2';
      else if (i === ci - 2) pos = 'prev2';
      card.dataset.pos = pos;
    });

    if (withIntro) {
      const active = cards[ci];
      if (active) {
        active.classList.add('intro');
        setTimeout(() => active.classList.remove('intro'), 650);
      }
    }
  };

  // ─────────────────────────────────────────────────────────────
  // NAVIGATION
  // ─────────────────────────────────────────────────────────────

  const nextCard = () => {
    if (state.isAnimating || state.currentIndex >= state.flashcards.length - 1) return;
    state.isAnimating = true;
    state.isFlipped   = false;
    delete state.flipAngle[state.currentIndex];
    state.currentIndex++;
    positionCards(true);
    updateProgress();
    setTimeout(() => { state.isAnimating = false; }, 400);
  };

  const previousCard = () => {
    if (state.isAnimating || state.currentIndex <= 0) return;
    state.isAnimating = true;
    state.isFlipped   = false;
    delete state.flipAngle[state.currentIndex];
    state.currentIndex--;
    positionCards(true);
    updateProgress();
    setTimeout(() => { state.isAnimating = false; }, 400);
  };

  // ─────────────────────────────────────────────────────────────
  // UPDATE PROGRESS
  // ─────────────────────────────────────────────────────────────

  const updateProgress = () => {
    const total = state.flashcards.length;
    const index = state.currentIndex;

    dom.cardCounter.textContent = `Card ${index + 1} of ${total}`;
    dom.prevBtn.disabled = index === 0;
    dom.nextBtn.disabled = index === total - 1;

    const pct = total > 0 ? ((index + 1) / total) * 100 : 0;
    dom.progressFill.style.width = `${pct}%`;
    dom.progressBar.setAttribute('aria-valuenow', String(Math.round(pct)));

    buildDots();
  };

  const buildDots = () => {
    const total = state.flashcards.length;
    // Show dots only for smaller decks (≤ 20); otherwise just use the counter
    if (total > 20) {
      dom.dotsWrap.innerHTML = '';
      return;
    }

    dom.dotsWrap.innerHTML = '';
    state.flashcards.forEach((_, i) => {
      const dot = document.createElement('div');
      dot.className = 'fc-dot' + (i === state.currentIndex ? ' is-active' : '');
      dom.dotsWrap.appendChild(dot);
    });
  };

  // ─────────────────────────────────────────────────────────────
  // COPY CARD
  // ─────────────────────────────────────────────────────────────

  const copyCard = () => {
    const card = state.flashcards[state.currentIndex];
    if (!card) return;

    const text = `Q: ${card.front}\nA: ${card.back}${card.example ? `\nExample: ${card.example}` : ''}`;
    copyToClipboard(text, 'Card copied!');
  };

  // ─────────────────────────────────────────────────────────────
  // COPY ALL
  // ─────────────────────────────────────────────────────────────

  const copyAll = () => {
    if (!state.flashcards.length) return;

    const text = state.flashcards
      .map((c, i) =>
        `Card ${i + 1}\nQ: ${c.front}\nA: ${c.back}${c.example ? `\nExample: ${c.example}` : ''}`
      )
      .join('\n\n---\n\n');

    copyToClipboard(text, 'All cards copied!');
  };

  const copyToClipboard = (text, successMessage) => {
    navigator.clipboard.writeText(text)
      .then(() => toast(successMessage, 'success'))
      .catch(() => {
        // Fallback for older browsers
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand('copy');
          toast(successMessage, 'success');
        } catch {
          toast('Copy failed. Please select and copy manually.', 'error');
        }
        document.body.removeChild(ta);
      });
  };

  // ─────────────────────────────────────────────────────────────
  // DOWNLOAD JSON
  // ─────────────────────────────────────────────────────────────

  const downloadJSON = () => {
    if (!state.result) return;
    const payload = {
      title:       state.result.title,
      description: state.result.description,
      flashcards:  state.flashcards,
      statistics:  state.result.statistics,
    };
    downloadFile(
      JSON.stringify(payload, null, 2),
      `${slugify(state.result.title ?? 'flashcards')}.json`,
      'application/json'
    );
  };

  // ─────────────────────────────────────────────────────────────
  // DOWNLOAD MARKDOWN
  // ─────────────────────────────────────────────────────────────

  const downloadMarkdown = () => {
    if (!state.result) return;

    const lines = [
      `# ${state.result.title ?? 'Flashcards'}`,
      '',
      state.result.description ? `> ${state.result.description}` : '',
      '',
      '---',
      '',
    ];

    state.flashcards.forEach((card, i) => {
      lines.push(`## Card ${i + 1}${card.card_type ? ` · ${CARD_TYPE_LABELS[card.card_type] ?? card.card_type}` : ''}${card.difficulty ? ` · ${card.difficulty}` : ''}`);
      lines.push('');
      lines.push(`**Front:** ${card.front}`);
      lines.push('');
      lines.push(`**Back:** ${card.back}`);
      if (card.example) {
        lines.push('');
        lines.push(`**Example:** ${card.example}`);
      }
      if (card.memory_tip) {
        lines.push('');
        lines.push(`**Memory Tip:** ${card.memory_tip}`);
      }
      if (card.category) {
        lines.push('');
        lines.push(`**Category:** ${card.category}`);
      }
      if (card.tags?.length) {
        lines.push('');
        lines.push(`**Tags:** ${card.tags.join(', ')}`);
      }
      lines.push('');
      lines.push('---');
      lines.push('');
    });

    downloadFile(
      lines.join('\n'),
      `${slugify(state.result.title ?? 'flashcards')}.md`,
      'text/markdown'
    );
  };

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // ─────────────────────────────────────────────────────────────
  // SHUFFLE CARDS
  // ─────────────────────────────────────────────────────────────

  const shuffleCards = () => {
    if (!state.flashcards.length) return;

    shuffleArray(state.flashcards);

    // Reset flip state
    state.currentIndex = 0;
    state.isFlipped    = false;
    state.flipAngle    = {};
    state.isAnimating  = false;

    renderDeck(true);
    toast('Cards shuffled!', 'success');
  };

  const shuffleArray = (arr) => {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  };

  // ─────────────────────────────────────────────────────────────
  // CONFIG CHIP / CARD GROUPS
  // ─────────────────────────────────────────────────────────────

  const initChipGroups = () => {
    // Single-select chip groups: difficulty
    document.querySelectorAll('.fc-chip[data-group]').forEach(btn => {
      btn.addEventListener('click', () => {
        const group = btn.dataset.group;
        document.querySelectorAll(`.fc-chip[data-group="${group}"]`).forEach(b =>
          b.classList.remove('fc-chip--active')
        );
        btn.classList.add('fc-chip--active');
        state.config[group] = btn.dataset.value;
      });
    });

    // Single-select card type cards
    document.querySelectorAll('.fc-type-card[data-group="card_type"]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.fc-type-card[data-group="card_type"]').forEach(b => {
          b.classList.remove('fc-type-card--active');
          b.setAttribute('aria-pressed', 'false');
        });
        btn.classList.add('fc-type-card--active');
        btn.setAttribute('aria-pressed', 'true');
        state.config.card_type = btn.dataset.value;
      });
    });
  };

  const initToggles = () => {
    document.querySelectorAll('.fc-toggle-input[data-toggle]').forEach(toggle => {
      toggle.addEventListener('change', () => {
        const key = toggle.dataset.toggle;
        if (key in state.config) {
          state.config[key] = toggle.checked;
        }
      });
    });
  };

  // ─────────────────────────────────────────────────────────────
  // BIND EVENTS
  // ─────────────────────────────────────────────────────────────

  const bindEvents = () => {
    // Mode tabs
    dom.modePaste.addEventListener('click',  () => setMode('paste'));
    dom.modeUpload.addEventListener('click', () => setMode('upload'));

    // Paste textarea
    dom.contentInput.addEventListener('input', () => {
      const val  = dom.contentInput.value;
      const len  = val.length;
      const words = val.trim() ? val.trim().split(/\s+/).length : 0;
      dom.charCount.textContent = `${len} / 20000`;
      dom.wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
      updateContinueBtn();
    });

    // Upload zone — click to open picker
    dom.uploadZone.addEventListener('click', (e) => {
      if (e.target === dom.uploadZone || e.target.closest('.fc-upload-idle')) {
        dom.fileInput.click();
      }
    });

    dom.fileInput.addEventListener('change', () => {
      if (dom.fileInput.files[0]) handleUpload(dom.fileInput.files[0]);
    });

    // Drag & drop
    dom.uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dom.uploadZone.classList.add('fc-drag-over');
    });

    dom.uploadZone.addEventListener('dragleave', (e) => {
      if (!dom.uploadZone.contains(e.relatedTarget)) {
        dom.uploadZone.classList.remove('fc-drag-over');
      }
    });

    dom.uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dom.uploadZone.classList.remove('fc-drag-over');
      const file = e.dataTransfer?.files[0];
      if (file) handleUpload(file);
    });

    // Remove file
    dom.fileRemove.addEventListener('click', (e) => {
      e.stopPropagation();
      clearUpload();
    });

    // Continue → config
    dom.continueBtn.addEventListener('click', () => showPhase(dom.phaseConfig));

    // Back → input
    dom.backBtn.addEventListener('click', () => showPhase(dom.phaseInput));

    // Card count slider
    dom.countSlider.addEventListener('input', () => {
      const val = Number(dom.countSlider.value);
      dom.countValue.textContent = val;
      dom.countSlider.setAttribute('aria-valuenow', val);
      state.config.number_of_cards = val;
    });

    // Language select
    dom.languageSelect.addEventListener('change', () => {
      state.config.language = dom.languageSelect.value;
    });

    // Generate
    dom.generateBtn.addEventListener('click', () => generateFlashcards(null));

    // Viewer navigation
    dom.prevBtn.addEventListener('click', previousCard);
    dom.nextBtn.addEventListener('click', nextCard);

    // Viewer actions
    dom.quitBtn.addEventListener('click', () => {
      if (confirm('Start a new deck? Current cards will be cleared.')) {
        resetToInput();
      }
    });

    dom.copyCardBtn.addEventListener('click', copyCard);
    dom.copyAllBtn.addEventListener('click',  copyAll);
    dom.shuffleBtn.addEventListener('click',  shuffleCards);
    dom.downloadJsonBtn.addEventListener('click', downloadJSON);
    dom.downloadMdBtn.addEventListener('click',   downloadMarkdown);
    dom.printBtn.addEventListener('click', () => window.print());
    dom.regenerateBtn.addEventListener('click', () => {
      if (state.lastRequestPayload) {
        showPhase(dom.phaseConfig);
        generateFlashcards(state.lastRequestPayload);
      } else {
        showPhase(dom.phaseConfig);
      }
    });

    // Error phase
    dom.errorBackBtn.addEventListener('click',  () => showPhase(dom.phaseInput));
    dom.errorRetryBtn.addEventListener('click', () => {
      if (state.lastRequestPayload) {
        showPhase(dom.phaseConfig);
        generateFlashcards(state.lastRequestPayload);
      } else {
        showPhase(dom.phaseConfig);
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', handleKeydown);

    // Init config controls
    initChipGroups();
    initToggles();
  };

  // ─────────────────────────────────────────────────────────────
  // KEYBOARD
  // ─────────────────────────────────────────────────────────────

  const handleKeydown = (e) => {
    if (dom.phaseViewer.classList.contains('fc-phase--hidden')) return;

    // Don't intercept when focus is inside an input
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    switch (e.key) {
      case 'ArrowRight':
        e.preventDefault();
        nextCard();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        previousCard();
        break;
      case ' ':
      case 'Enter':
        e.preventDefault();
        if (!state.isAnimating) flipCard();
        break;
    }
  };

  // ─────────────────────────────────────────────────────────────
  // RESET
  // ─────────────────────────────────────────────────────────────

  const resetToInput = () => {
    state.result      = null;
    state.flashcards  = [];
    state.currentIndex = 0;
    state.isFlipped   = false;
    state.flipAngle   = {};
    dom.deck.innerHTML = '';
    showPhase(dom.phaseInput);
  };

  // ─────────────────────────────────────────────────────────────
  // TOAST
  // ─────────────────────────────────────────────────────────────

  const toast = (message, type = 'info') => {
    const existing = document.getElementById('fc-toast-container');
    const container = existing ?? (() => {
      const el = document.createElement('div');
      el.id = 'fc-toast-container';
      el.className = 'fc-toast-container';
      el.setAttribute('role', 'alert');
      el.setAttribute('aria-live', 'assertive');
      document.body.appendChild(el);
      return el;
    })();

    const t = document.createElement('div');
    t.className = `fc-toast fc-toast--${type}`;
    t.textContent = message;
    container.appendChild(t);

    requestAnimationFrame(() => t.classList.add('fc-toast--visible'));

    setTimeout(() => {
      t.classList.remove('fc-toast--visible');
      t.addEventListener('transitionend', () => t.remove(), { once: true });
    }, 4000);
  };

  // ─────────────────────────────────────────────────────────────
  // HELPERS
  // ─────────────────────────────────────────────────────────────

  const escapeHTML = (str) => {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  const formatBytes = (bytes) => {
    if (bytes < 1024)       return `${bytes} B`;
    if (bytes < 1024 ** 2)  return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  };

  const slugify = (str) =>
    str.toLowerCase().trim().replace(/[^\w\s-]/g, '').replace(/[\s_-]+/g, '-').replace(/^-+|-+$/g, '') || 'flashcards';

  // ─────────────────────────────────────────────────────────────
  // INIT
  // ─────────────────────────────────────────────────────────────

  const initialize = () => {
    cacheDOM();
    bindEvents();
    initModePill();
    initRotator();
    setMode('paste');
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }

})();