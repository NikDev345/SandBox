'use strict';

/* ============================================================
   youtube_summarizer.js
   Sandbox — YouTube Summarizer Tool
   Vanilla JS. No dependencies. Matches yts-* HTML/CSS 1:1.
   ============================================================ */

(() => {
  /* ────────────────────────────────────────────
     CONFIG — adjust to match your FastAPI routes
     and response shape. Everything below reads
     from these two calls.
  ──────────────────────────────────────────── */
  const CONFIG = {
    GENERATE_ENDPOINT: "/youtube-summarizer/generate",
  };

  const ROTATE_INTERVAL_MS = 1500;

  const LOADING_HINTS = [
    'Fetching video metadata…',
    'Transcribing audio…',
    'Analyzing key moments…',
    'Structuring the summary…',
    'Polishing the final output…',
  ];

  // Expected generate() response keys → how each renders.
  // Missing/empty keys are simply skipped — no empty cards.
  const SECTION_DEFS = [
    { key: 'summary', title: 'Summary', subtitle: 'The full picture, distilled', icon: '📝' },
    { key: 'key_points', title: 'Key Points', subtitle: 'The essentials at a glance', icon: '📌' },
    { key: 'timeline', title: 'Timeline', subtitle: 'Moments in order', icon: '⏱' },
    { key: 'important_quotes',title: 'Important Quotes',subtitle: 'Notable lines from the video',icon: '💬'},
    { key: 'action_items', title: 'Action Items', subtitle: 'Things worth doing next', icon: '✅' },
    { key: 'keywords', title: 'Keywords', subtitle: 'Topics covered', icon: '🏷️' },
  ];

  const YT_ID_REGEX = /(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/|live\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;

  /* ────────────────────────────────────────────
     DOM REFERENCES
  ──────────────────────────────────────────── */
  const els = {
    overlay: document.getElementById('ytsOverlay'),
    overlayBar: document.getElementById('ytsOverlayBar'),
    overlayHint: document.getElementById('ytsOverlayHint'),
    rotatingTrack: document.getElementById('ytsRotatingTrack'),
    inputCard: document.getElementById('ytsInputCard'),
    urlInput: document.getElementById('ytsUrlInput'),
    urlError: document.getElementById('ytsUrlError'),
    pasteBtn: document.getElementById('ytsPasteBtn'),
    clearBtn: document.getElementById('ytsClearBtn'),
    preview: document.getElementById('ytsPreview'),
    thumb: document.getElementById('ytsThumb'),
    duration: document.getElementById('ytsDuration'),
    videoTitle: document.getElementById('ytsVideoTitle'),
    channel: document.getElementById('ytsChannel'),
    date: document.getElementById('ytsDate'),
    segmentPill: document.getElementById('ytsSegmentPill'),
    generateBtn: document.getElementById('ytsGenerateBtn'),
    results: document.getElementById('ytsResults'),
    cardsGrid: document.getElementById('ytsCardsGrid'),
    copyAllBtn: document.getElementById('ytsCopyAllBtn'),
    newBtn: document.getElementById('ytsNewBtn'),
  };

  const styleCards = Array.from(document.querySelectorAll('.yts-style-card'));
  const segmentBtns = Array.from(document.querySelectorAll('.yts-segment__btn'));
  const toneBtns = Array.from(document.querySelectorAll('.yts-tone-btn'));

  /* ────────────────────────────────────────────
     STATE
  ──────────────────────────────────────────── */
  const state = {
    videoId: null,
    videoMeta: null,
    style: 'standard',
    length: 'medium',
    tone: 'professional',
    isGenerating: false,
    lastResult: null,
    previewDebounce: null,
  };

  let overlayHintTimer = null;
  let overlayProgressTimer = null;

  /* ============================================================
     HERO ROTATING WORDS
     Slides the track up by 1.1em (line-height) every 1.5s.
     Last word is a duplicate of the first so the loop can snap
     back invisibly once the slide-out transition finishes.
  ============================================================ */
  function initRotatingWords() {
    if (!els.rotatingTrack) return;
    const words = els.rotatingTrack.querySelectorAll('.yts-hero__rotating-word');
    if (words.length < 2) return;

    let index = 0;
    const lastIndex = words.length - 1;

    setInterval(() => {
      index += 1;
      els.rotatingTrack.style.transform = `translateY(-${index * 1.1}em)`;

      if (index === lastIndex) {
        window.setTimeout(() => {
          els.rotatingTrack.style.transition = 'none';
          els.rotatingTrack.style.transform = 'translateY(0)';
          index = 0;
          void els.rotatingTrack.offsetHeight; // force reflow before re-enabling transition
          els.rotatingTrack.style.transition = '';
        }, 520);
      }
    }, ROTATE_INTERVAL_MS);
  }

  /* ============================================================
     URL VALIDATION
  ============================================================ */
  function extractVideoId(url) {
    if (!url) return null;
    const match = url.trim().match(YT_ID_REGEX);
    return match ? match[1] : null;
  }

  function setInputError(message) {
    els.urlError.textContent = message || '';
  }

  function setInputFocused(isFocused) {
    els.inputCard.classList.toggle('yts-input-card--focused', isFocused);
  }

  function toggleClearBtn(show) {
    els.clearBtn.style.display = show ? 'flex' : 'none';
  }

  /* ============================================================
     CLIPBOARD ACTIONS
  ============================================================ */
  async function pasteFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      if (!text) return;
      els.urlInput.value = text.trim();
      handleUrlInputChange();
      els.urlInput.focus();
    } catch (err) {
      setInputError('Clipboard access was blocked — paste manually instead.');
    }
  }

  function clearUrlInput() {
    els.urlInput.value = '';
    setInputError('');
    hidePreview();
    toggleClearBtn(false);
    els.urlInput.focus();
  }

  /* ============================================================
     VIDEO PREVIEW
  ============================================================ */
  function hidePreview() {
    els.preview.classList.remove('yts-preview--visible');
    state.videoId = null;
    state.videoMeta = null;
    if (state.previewDebounce) clearTimeout(state.previewDebounce);
  }



  function renderPreview(meta) {
    els.thumb.src = meta.thumbnail_url || `https://img.youtube.com/vi/${state.videoId}/hqdefault.jpg`;
    els.thumb.alt = meta.title ? `Thumbnail for ${meta.title}` : 'Video thumbnail';
    els.videoTitle.textContent = meta.title || 'Untitled video';
    els.channel.textContent = meta.channel || '';
    els.duration.textContent = meta.duration || '';
    els.date.textContent = meta.published_at || '';
    els.preview.classList.add('yts-preview--visible');
  }


  function handleUrlInputChange() {
    const raw = els.urlInput.value.trim();
    toggleClearBtn(raw.length > 0);

    
    if (!raw) {
      setInputError('');
      hidePreview();
      return;
    }

    const videoId = extractVideoId(raw);
    if (!videoId) {
      setInputError('Enter a valid YouTube video URL.');
      hidePreview();
      return;
    }

    setInputError('');
    if (videoId === state.videoId) return;
    state.videoId = videoId;
  }

  /* ============================================================
     STYLE / LENGTH / TONE SELECTION
  ============================================================ */
  function initStyleCards() {
    styleCards.forEach((card) => {
      card.addEventListener('click', () => selectStyleCard(card));
    });
  }

  function selectStyleCard(card) {
    styleCards.forEach((c) => {
      c.classList.remove('yts-style-card--active');
      c.setAttribute('aria-checked', 'false');
    });
    card.classList.add('yts-style-card--active');
    card.setAttribute('aria-checked', 'true');
    state.style = card.dataset.style;
  }

  function getActiveSegmentBtn() {
    return segmentBtns.find((b) => b.classList.contains('yts-segment__btn--active')) || segmentBtns[0];
  }

  function positionSegmentPill(btn) {
    if (!btn || !els.segmentPill) return;
    els.segmentPill.style.left = `${btn.offsetLeft}px`;
    els.segmentPill.style.width = `${btn.offsetWidth}px`;
  }

  function selectSegment(btn) {
    segmentBtns.forEach((b) => {
      b.classList.remove('yts-segment__btn--active');
      b.setAttribute('aria-checked', 'false');
    });
    btn.classList.add('yts-segment__btn--active');
    btn.setAttribute('aria-checked', 'true');
    state.length = btn.dataset.length;
    positionSegmentPill(btn);
  }

  function initSegmentControl() {
    segmentBtns.forEach((btn) => {
      btn.addEventListener('click', () => selectSegment(btn));
    });

    // Position the pill instantly on load (no slide-in from nowhere).
    if (els.segmentPill) els.segmentPill.style.transition = 'none';
    requestAnimationFrame(() => {
      positionSegmentPill(getActiveSegmentBtn());
      requestAnimationFrame(() => {
        if (els.segmentPill) els.segmentPill.style.transition = '';
      });
    });

    window.addEventListener('resize', () => positionSegmentPill(getActiveSegmentBtn()));
  }

  function initToneButtons() {
    toneBtns.forEach((btn) => {
      btn.addEventListener('click', () => selectTone(btn));
    });
  }

  function selectTone(btn) {
    toneBtns.forEach((b) => {
      b.classList.remove('yts-tone-btn--active');
      b.setAttribute('aria-checked', 'false');
    });
    btn.classList.add('yts-tone-btn--active');
    btn.setAttribute('aria-checked', 'true');
    state.tone = btn.dataset.tone;
  }

  /* ============================================================
     LOADING OVERLAY
  ============================================================ */
  function showOverlay() {
    els.overlay.classList.add('yts-overlay--visible');
    els.overlay.setAttribute('aria-hidden', 'false');

    let hintIndex = 0;
    els.overlayHint.textContent = LOADING_HINTS[0];
    els.overlayHint.style.opacity = '1';

    overlayHintTimer = window.setInterval(() => {
      hintIndex = (hintIndex + 1) % LOADING_HINTS.length;
      els.overlayHint.style.opacity = '0';
      window.setTimeout(() => {
        els.overlayHint.textContent = LOADING_HINTS[hintIndex];
        els.overlayHint.style.opacity = '1';
      }, 200);
    }, 1600);

    let progress = 0;
    els.overlayBar.style.width = '0%';
    overlayProgressTimer = window.setInterval(() => {
      progress = Math.min(progress + Math.random() * 12, 92);
      els.overlayBar.style.width = `${progress}%`;
    }, 350);
  }

  function hideOverlay() {
    if (overlayHintTimer) clearInterval(overlayHintTimer);
    if (overlayProgressTimer) clearInterval(overlayProgressTimer);

    els.overlayBar.style.width = '100%';
    window.setTimeout(() => {
      els.overlay.classList.remove('yts-overlay--visible');
      els.overlay.setAttribute('aria-hidden', 'true');
      els.overlayBar.style.width = '0%';
    }, 250);
  }

  /* ============================================================
     GENERATE SUMMARY
  ============================================================ */
  function setGenerateLoading(isLoading) {
    state.isGenerating = isLoading;
    els.generateBtn.classList.toggle('yts-generate-btn--loading', isLoading);
    els.generateBtn.disabled = isLoading;
    els.generateBtn.setAttribute('aria-busy', String(isLoading));
  }

  async function safeJson(res) {
    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  async function handleGenerateClick() {
    if (state.isGenerating) return;

    const raw = els.urlInput.value.trim();
    const videoId = extractVideoId(raw);
    if (!videoId) {
      setInputError('Enter a valid YouTube video URL before generating.');
      els.urlInput.focus();
      return;
    }

    setGenerateLoading(true);
    showOverlay();

    try {
      const res = await fetch(CONFIG.GENERATE_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          youtube_url: raw,
          settings: {
            style: state.style,
            length: state.length,
            tone: state.tone,
          },
        }),
      });

      if (!res.ok) {
        const errBody = await safeJson(res);
        throw new Error((errBody && errBody.detail) || `Generation failed (${res.status})`);
      }

      const data = await res.json();
      state.lastResult = data;
      renderResults(data);
      hideOverlay();
      setGenerateLoading(false);
      showResults();
    } catch (err) {
      hideOverlay();
      setGenerateLoading(false);
      setInputError(err.message || 'Something went wrong while generating the summary.');
    }
  }

  /* ============================================================
     RESULTS RENDERING
  ============================================================ */
  function isEmptyValue(value) {
    if (value === null || value === undefined) return true;
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'string') return value.trim().length === 0;
    return false;
  }

  function renderResults(data) {
    els.cardsGrid.innerHTML = '';

    SECTION_DEFS.forEach((def) => {
      const value = data[def.key];
      if (isEmptyValue(value)) return;
      els.cardsGrid.appendChild(buildResultCard(def, value));
    });

    requestAnimationFrame(() => {
      const cards = els.cardsGrid.querySelectorAll('.yts-result-card');
      cards.forEach((card, i) => {
        window.setTimeout(() => card.classList.add('yts-result-card--visible'), i * 80);
      });
    });
  }

  function buildResultCard(def, value) {
    const card = document.createElement('article');
    card.className = 'yts-result-card';
    card.dataset.section = def.key;

    const header = document.createElement('div');
    header.className = 'yts-result-card__header';
    header.setAttribute('role', 'button');
    header.setAttribute('tabindex', '0');
    header.setAttribute('aria-expanded', 'true');

    const headingGroup = document.createElement('div');
    headingGroup.className = 'yts-result-card__heading-group';

    const iconEl = document.createElement('span');
    iconEl.className = 'yts-result-card__icon';
    iconEl.setAttribute('aria-hidden', 'true');
    iconEl.textContent = def.icon;

    const textGroup = document.createElement('span');
    const titleEl = document.createElement('p');
    titleEl.className = 'yts-result-card__title';
    titleEl.textContent = def.title;
    const subtitleEl = document.createElement('p');
    subtitleEl.className = 'yts-result-card__subtitle';
    subtitleEl.textContent = def.subtitle;
    textGroup.appendChild(titleEl);
    textGroup.appendChild(subtitleEl);

    headingGroup.appendChild(iconEl);
    headingGroup.appendChild(textGroup);

    const controls = document.createElement('div');
    controls.className = 'yts-result-card__controls';

    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'yts-result-card__copy';
    copyBtn.setAttribute('aria-label', `Copy ${def.title}`);
    copyBtn.title = 'Copy';
    copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2"/></svg>';

    const chevron = document.createElement('span');
    chevron.className = 'yts-result-card__chevron';
    chevron.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true" width="18" height="18"><polyline points="6 9 12 15 18 9"/></svg>';

    controls.appendChild(copyBtn);
    controls.appendChild(chevron);

    header.appendChild(headingGroup);
    header.appendChild(controls);

    const body = document.createElement('div');
    body.className = 'yts-result-card__body';
    body.appendChild(buildSectionBody(def.key, value));

    card.appendChild(header);
    card.appendChild(body);

    header.addEventListener('click', (e) => {
      if (e.target.closest('.yts-result-card__copy')) return;
      toggleCard(card, header);
    });
    header.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleCard(card, header);
      }
    });

    copyBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      copyText(sectionToPlainText(def.title, value), copyBtn);
    });

    return card;
  }

  function toggleCard(card, header) {
    const collapsed = card.classList.toggle('yts-result-card--collapsed');
    header.setAttribute('aria-expanded', String(!collapsed));
  }

  function buildSectionBody(key, value) {
    const wrap = document.createElement('div');

    switch (key) {
      case 'summary': {
        wrap.className = 'yts-prose';
        String(value)
          .split(/\n{2,}/)
          .filter(Boolean)
          .forEach((para) => {
            const p = document.createElement('p');
            p.textContent = para.trim();
            wrap.appendChild(p);
          });
        break;
      }

      case 'key_points': {
        const list = document.createElement('ul');
        list.className = 'yts-key-list';
        value.forEach((point) => {
          const li = document.createElement('li');
          li.className = 'yts-key-list__item';
          const bullet = document.createElement('span');
          bullet.className = 'yts-key-list__bullet';
          bullet.setAttribute('aria-hidden', 'true');
          const text = document.createElement('span');
          text.textContent = point;
          li.appendChild(bullet);
          li.appendChild(text);
          list.appendChild(li);
        });
        wrap.appendChild(list);
        break;
      }

      case 'timeline': {
        const timeline = document.createElement('div');
        timeline.className = 'yts-timeline';
        value.forEach((item) => {
          const entry = document.createElement('div');
          entry.className = 'yts-timeline__item';
          const time = document.createElement('span');
          time.className = 'yts-timeline__time';
          time.textContent = item.title || '';
          const text = document.createElement('p');
          text.className = 'yts-timeline__text';
          text.textContent = item.summary || '';
          entry.appendChild(time);
          entry.appendChild(text);
          timeline.appendChild(entry);
        });
        wrap.appendChild(timeline);
        break;
      }

      case 'important_quotes': {
    const quotes = document.createElement('div');
    quotes.className = 'yts-quotes';

    value.forEach((quote) => {
        const quoteCard = document.createElement('div');
        quoteCard.className = 'yts-quote-card';

        const text = document.createElement('p');
        text.className = 'yts-quote-card__text';
        text.textContent = `"${quote}"`;

        quoteCard.appendChild(text);
        quotes.appendChild(quoteCard);
    });

    wrap.appendChild(quotes);
    break;
}

      case 'action_items': {
        const list = document.createElement('ul');
        list.className = 'yts-action-list';
        value.forEach((item) => {
          const li = document.createElement('li');
          li.className = 'yts-action-list__item';
          const check = document.createElement('span');
          check.className = 'yts-action-check';
          check.setAttribute('aria-hidden', 'true');
          const text = document.createElement('span');
          text.textContent = item;
          li.appendChild(check);
          li.appendChild(text);
          list.appendChild(li);
        });
        wrap.appendChild(list);
        break;
      }

      case 'keywords': {
        const chips = document.createElement('div');
        chips.className = 'yts-chips';
        value.forEach((word) => {
          const chip = document.createElement('span');
          chip.className = 'yts-chip';
          chip.textContent = word;
          chips.appendChild(chip);
        });
        wrap.appendChild(chips);
        break;
      }

      default:
        wrap.textContent = String(value);
    }

    return wrap;
  }

  function sectionToPlainText(title, value) {
    let body;
    if (Array.isArray(value)) {
      if (value.length && typeof value[0] === 'object') {
        body = value.map((v) => `${v.time ? `[${v.time}] ` : ''}${v.text || ''}`).join('\n');
      } else {
        body = value.map((v) => `• ${v}`).join('\n');
      }
    } else {
      body = String(value);
    }
    return `${title}\n${'─'.repeat(title.length)}\n${body}`;
  }

  /* ============================================================
     COPY ACTIONS
  ============================================================ */
  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      flashCopied(btn);
    } catch (err) {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      flashCopied(btn);
    }
  }

  function flashCopied(btn) {
    if (!btn) return;
    btn.classList.add('yts-result-card__copy--copied');
    window.setTimeout(() => btn.classList.remove('yts-result-card__copy--copied'), 1500);
  }

  function copyAllResults() {
    if (!state.lastResult) return;
    const parts = SECTION_DEFS
      .filter((def) => !isEmptyValue(state.lastResult[def.key]))
      .map((def) => sectionToPlainText(def.title, state.lastResult[def.key]));
    copyText(parts.join('\n\n'), els.copyAllBtn);
  }

  /* ============================================================
     RESULTS VISIBILITY / RESET
  ============================================================ */
  function showResults() {
    els.results.classList.add('yts-results--visible');
    window.setTimeout(() => {
      els.results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);
  }

  function resetForNewSummary() {
    els.results.classList.remove('yts-results--visible');
    els.cardsGrid.innerHTML = '';
    state.lastResult = null;
    els.urlInput.value = '';
    setInputError('');
    hidePreview();
    toggleClearBtn(false);
    els.inputCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    window.setTimeout(() => els.urlInput.focus(), 300);
  }

  /* ============================================================
     EVENT BINDING + INIT
  ============================================================ */
  function bindEvents() {
    els.urlInput.addEventListener('input', handleUrlInputChange);
    els.urlInput.addEventListener('focus', () => setInputFocused(true));
    els.urlInput.addEventListener('blur', () => setInputFocused(false));
    els.urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleGenerateClick();
      }
    });

    els.pasteBtn.addEventListener('click', pasteFromClipboard);
    els.clearBtn.addEventListener('click', clearUrlInput);

    els.generateBtn.addEventListener('click', handleGenerateClick);
    els.copyAllBtn.addEventListener('click', copyAllResults);
    els.newBtn.addEventListener('click', resetForNewSummary);
  }

  function init() {
    initRotatingWords();
    initStyleCards();
    initSegmentControl();
    initToneButtons();
    bindEvents();
    toggleClearBtn(false);
  }

  document.addEventListener('DOMContentLoaded', init);
})();