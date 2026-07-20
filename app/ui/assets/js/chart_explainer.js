/**
 * chart_explainer.js
 * AI Chart Explainer — AI SandBox Platform
 * ─────────────────────────────────────────────────────────────
 * Works with: chart_explainer.html + chart_explainer.css + FastAPI backend
 * API: POST /chart-explainer/analyze  (multipart/form-data)
 *
 * BACKEND CONTRACT — do not rename these, they are fixed server-side:
 *   Request fields:  image, language, explanation_level,
 *                     include_summary, include_axis_explanation,
 *                     include_key_insights, include_trend_analysis,
 *                     include_outliers, include_business_insights,
 *                     include_recommendations, include_questions_answered,
 *                     include_limitations, include_eli5, include_confidence
 *   Response fields: chart_type, executive_summary, axis_explanation,
 *                     key_insights[], trend_analysis, outliers[],
 *                     business_insights, recommendations[],
 *                     questions_answered[], limitations[],
 *                     eli5_explanation, confidence_score
 */

(() => {
  'use strict';

  // ─────────────────────────────────────────────────────────────
  // CONSTANTS
  // ─────────────────────────────────────────────────────────────

  const API_ENDPOINT = '/chart-explainer/analyze';
  const MAX_FILE_BYTES = 15 * 1024 * 1024; // 15 MB
  const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'];

  const LOADING_MESSAGES = [
    'Reading chart…',
    'Understanding axes…',
    'Finding trends…',
    'Finding insights…',
    'Generating report…',
    'Preparing explanation…',
    'Almost done…',
  ];
  const LOADING_STEP_INTERVAL_MS = 1600;

  // Card definitions: response key → render metadata.
  // Order here is the render order. Cards are skipped entirely when the
  // field is absent, empty, or its "include_*" toggle was switched off.
  const CARD_DEFS = [
    { key: 'executive_summary', title: 'Executive Summary', type: 'hero', toggle: 'summary' },
    { key: 'axis_explanation', title: 'Axis Explanation', type: 'text', toggle: 'axis' },
    { key: 'key_insights', title: 'Key Insights', type: 'list', toggle: 'insights' },
    { key: 'trend_analysis', title: 'Trend Analysis', type: 'text', toggle: 'trend' },
    { key: 'outliers', title: 'Outliers', type: 'list', toggle: 'outliers', variant: 'outliers' },
    { key: 'business_insights', title: 'Business Insights', type: 'text', toggle: 'business' },
    { key: 'recommendations', title: 'Recommendations', type: 'list', toggle: 'recommendations' },
    { key: 'questions_answered', title: 'Questions Answered', type: 'list', toggle: 'questions' },
    { key: 'limitations', title: 'Limitations', type: 'list', toggle: 'limitations', variant: 'limitations' },
    { key: 'eli5_explanation', title: "Explain Like I'm 5", type: 'text', toggle: 'eli5', variant: 'eli5' },
    { key: 'confidence_score', title: 'Confidence', type: 'confidence', toggle: 'confidence' },
  ];

  // ─────────────────────────────────────────────────────────────
  // STATE
  // ─────────────────────────────────────────────────────────────

  const state = {
    phase: 'upload', // 'upload' | 'configure' | 'results' | 'error'
    file: null,
    previewUrl: null,
    config: {
      language: 'English',
      explanation_level: 'Intermediate',
      toggles: {
        summary: true,
        axis: true,
        insights: true,
        trend: true,
        outliers: true,
        business: true,
        recommendations: true,
        questions: true,
        limitations: true,
        eli5: true,
        confidence: true,
      },
    },
    result: null,       // raw backend response
    loadingTimer: null,
    lastErrorRetry: null, // fn to retry the last failed action
  };

  // ─────────────────────────────────────────────────────────────
  // DOM CACHE
  // ─────────────────────────────────────────────────────────────

  let dom = {};

  const cacheDOM = () => {
    dom = {
      root: document.getElementById('ce-root'),
      dropOverlay: document.getElementById('ce-drop-overlay'),

      // Phases
      phaseUpload: document.getElementById('ce-phase-upload'),
      phaseConfigure: document.getElementById('ce-phase-configure'),
      phaseResults: document.getElementById('ce-phase-results'),
      phaseError: document.getElementById('ce-phase-error'),
      loadingOverlay: document.getElementById('ce-loading-overlay'),
      loadingStatus: document.getElementById('ce-loading-status'),
      loadingFill: document.getElementById('ce-loading-fill'),

      // Upload
      uploadZone: document.getElementById('ce-upload-zone'),
      fileInput: document.getElementById('ce-file-input'),
      uploadIdle: document.getElementById('ce-upload-idle'),
      uploadPreview: document.getElementById('ce-upload-preview'),
      previewImage: document.getElementById('ce-preview-image'),
      previewFilename: document.getElementById('ce-preview-filename'),
      previewFilesize: document.getElementById('ce-preview-filesize'),
      previewDims: document.getElementById('ce-preview-dims'),
      previewFullscreenBtn: document.getElementById('ce-preview-fullscreen-btn'),
      replaceBtn: document.getElementById('ce-replace-btn'),
      removeBtn: document.getElementById('ce-remove-btn'),
      continueBtn: document.getElementById('ce-continue-btn'),

      // Configure
      backBtn: document.getElementById('ce-back-btn'),
      languageSelect: document.getElementById('ce-language-select'),
      segmented: document.querySelectorAll('.ce-segmented-option'),
      analyzeBtn: document.getElementById('ce-analyze-btn'),

      // Results
      chartTypeBadge: document.getElementById('ce-chart-type-badge'),
      resultsBody: document.getElementById('ce-results-body'),
      copyAllBtn: document.getElementById('ce-copy-all-btn'),
      exportBtn: document.getElementById('ce-export-btn'),
      exportDropdown: document.getElementById('ce-export-dropdown'),
      newAnalysisBtn: document.getElementById('ce-new-analysis-btn'),

      // Error
      errorMessage: document.getElementById('ce-error-message'),
      errorRetryBtn: document.getElementById('ce-error-retry-btn'),
      errorBackBtn: document.getElementById('ce-error-back-btn'),

      // Lightbox
      lightbox: document.getElementById('ce-lightbox'),
      lightboxImage: document.getElementById('ce-lightbox-image'),
      lightboxClose: document.getElementById('ce-lightbox-close'),
    };
  };

  // ─────────────────────────────────────────────────────────────
  // PHASE NAVIGATION
  // ─────────────────────────────────────────────────────────────

  const allPhases = () => [dom.phaseUpload, dom.phaseConfigure, dom.phaseResults, dom.phaseError];

  const showPhase = (phase) => {
    allPhases().forEach((p) => {
      const isTarget = p === phase;
      p.classList.toggle('ce-phase--hidden', !isTarget);
      if (!isTarget) p.setAttribute('aria-hidden', 'true');
      else p.removeAttribute('aria-hidden');
    });
    phase.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // ─────────────────────────────────────────────────────────────
  // UPLOAD MANAGER
  // ─────────────────────────────────────────────────────────────

  const UploadManager = {
    handle(file) {
      if (!file) return;

      if (!ACCEPTED_TYPES.includes(file.type)) {
        Toast.show('Unsupported file type. Please upload a PNG, JPG, WEBP, or GIF image.', 'error');
        return;
      }

      if (file.size > MAX_FILE_BYTES) {
        Toast.show('Image too large. Maximum size is 15 MB.', 'error');
        return;
      }

      if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);

      state.file = file;
      state.previewUrl = URL.createObjectURL(file);

      dom.previewImage.src = state.previewUrl;
      dom.previewImage.onload = () => {
        dom.previewDims.textContent = `${dom.previewImage.naturalWidth} × ${dom.previewImage.naturalHeight}`;
      };

      dom.previewFilename.textContent = file.name;
      dom.previewFilesize.textContent = Formatters.bytes(file.size);

      dom.uploadIdle.hidden = true;
      dom.uploadPreview.hidden = false;
      dom.uploadZone.classList.add('ce-upload-zone--has-file');

      this.updateContinueBtn();
    },

    clear() {
      if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
      state.file = null;
      state.previewUrl = null;
      dom.fileInput.value = '';
      dom.uploadIdle.hidden = false;
      dom.uploadPreview.hidden = true;
      dom.uploadZone.classList.remove('ce-upload-zone--has-file');
      this.updateContinueBtn();
    },

    updateContinueBtn() {
      const ready = !!state.file;
      dom.continueBtn.disabled = !ready;
      dom.continueBtn.setAttribute('aria-disabled', String(!ready));
    },
  };

  // ─────────────────────────────────────────────────────────────
  // CLIPBOARD MANAGER (paste-to-upload + copy-to-clipboard)
  // ─────────────────────────────────────────────────────────────

  const ClipboardManager = {
    initPaste() {
      document.addEventListener('paste', (e) => {
        if (state.phase !== 'upload') return;
        const items = e.clipboardData?.items;
        if (!items) return;

        for (const item of items) {
          if (item.type.startsWith('image/')) {
            const file = item.getAsFile();
            if (file) {
              e.preventDefault();
              UploadManager.handle(file);
            }
            break;
          }
        }
      });
    },

    async copyText(text, successMessage = 'Copied to clipboard') {
      try {
        await navigator.clipboard.writeText(text);
        Toast.show(successMessage, 'success');
      } catch (err) {
        Toast.show('Could not copy — please copy manually.', 'error');
      }
    },
  };

  // ─────────────────────────────────────────────────────────────
  // DRAG & DROP (anywhere on page)
  // ─────────────────────────────────────────────────────────────

  const DragDropManager = {
    dragCounter: 0,

    init() {
      window.addEventListener('dragenter', (e) => {
        if (state.phase !== 'upload') return;
        if (!e.dataTransfer?.types?.includes('Files')) return;
        e.preventDefault();
        this.dragCounter++;
        dom.dropOverlay.hidden = false;
        dom.dropOverlay.removeAttribute('aria-hidden');
      });

      window.addEventListener('dragover', (e) => {
        if (state.phase !== 'upload') return;
        e.preventDefault();
      });

      window.addEventListener('dragleave', (e) => {
        if (state.phase !== 'upload') return;
        this.dragCounter = Math.max(0, this.dragCounter - 1);
        if (this.dragCounter === 0) {
          dom.dropOverlay.hidden = true;
          dom.dropOverlay.setAttribute('aria-hidden', 'true');
        }
      });

      window.addEventListener('drop', (e) => {
        if (state.phase !== 'upload') return;
        e.preventDefault();
        this.dragCounter = 0;
        dom.dropOverlay.hidden = true;
        dom.dropOverlay.setAttribute('aria-hidden', 'true');

        const file = e.dataTransfer?.files?.[0];
        if (file) UploadManager.handle(file);
      });

      // Zone-level drag styling
      dom.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dom.uploadZone.classList.add('ce-upload-zone--drag');
      });
      dom.uploadZone.addEventListener('dragleave', () => {
        dom.uploadZone.classList.remove('ce-upload-zone--drag');
      });
      dom.uploadZone.addEventListener('drop', () => {
        dom.uploadZone.classList.remove('ce-upload-zone--drag');
      });
    },
  };

  // ─────────────────────────────────────────────────────────────
  // ANIMATION MANAGER — loading overlay status rotation
  // ─────────────────────────────────────────────────────────────

  const AnimationManager = {
    startLoading() {
      dom.loadingOverlay.hidden = false;
      dom.loadingOverlay.removeAttribute('aria-hidden');

      let index = 0;
      dom.loadingStatus.textContent = LOADING_MESSAGES[0];
      dom.loadingFill.style.width = `${100 / LOADING_MESSAGES.length}%`;

      state.loadingTimer = setInterval(() => {
        index = Math.min(index + 1, LOADING_MESSAGES.length - 1);
        dom.loadingStatus.textContent = LOADING_MESSAGES[index];
        dom.loadingFill.style.width = `${((index + 1) / LOADING_MESSAGES.length) * 100}%`;
        if (index === LOADING_MESSAGES.length - 1) clearInterval(state.loadingTimer);
      }, LOADING_STEP_INTERVAL_MS);
    },

    stopLoading() {
      clearInterval(state.loadingTimer);
      dom.loadingOverlay.hidden = true;
      dom.loadingOverlay.setAttribute('aria-hidden', 'true');
      dom.loadingFill.style.width = '0%';
    },
  };

  // ─────────────────────────────────────────────────────────────
  // BUILD REQUEST — field names are FIXED by the backend contract
  // ─────────────────────────────────────────────────────────────

  const buildFormData = () => {
    const fd = new FormData();
    const cfg = state.config;
    const t = cfg.toggles;

    fd.append('image', state.file);
    fd.append('language', cfg.language);
    fd.append('explanation_level', cfg.explanation_level);

    fd.append('include_summary', String(t.summary));
    fd.append('include_axis_explanation', String(t.axis));
    fd.append('include_key_insights', String(t.insights));
    fd.append('include_trend_analysis', String(t.trend));
    fd.append('include_outliers', String(t.outliers));
    fd.append('include_business_insights', String(t.business));
    fd.append('include_recommendations', String(t.recommendations));
    fd.append('include_questions_answered', String(t.questions));
    fd.append('include_limitations', String(t.limitations));
    fd.append('include_eli5', String(t.eli5));
    fd.append('include_confidence', String(t.confidence));

    return fd;
  };

  // ─────────────────────────────────────────────────────────────
  // ANALYZE — API CALL
  // ─────────────────────────────────────────────────────────────

  const analyzeChart = async () => {
    if (!state.file) {
      Toast.show('Please upload a chart image first.', 'error');
      return;
    }

    state.lastErrorRetry = analyzeChart;

    dom.analyzeBtn.disabled = true;
    dom.analyzeBtn.classList.add('ce-analyze-btn--loading');
    AnimationManager.startLoading();

    const token = AuthHelper.getToken();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: buildFormData(),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw await ErrorHandler.fromResponse(response);
      }

      const data = await response.json();

      state.result = data;
      state.phase = 'results';

      AnimationManager.stopLoading();
      Renderer.renderResults(data);
      showPhase(dom.phaseResults);

    } catch (err) {
      clearTimeout(timeoutId);
      AnimationManager.stopLoading();
      ErrorHandler.show(err);
    } finally {
      dom.analyzeBtn.disabled = false;
      dom.analyzeBtn.classList.remove('ce-analyze-btn--loading');
    }
  };

  // ─────────────────────────────────────────────────────────────
  // ERROR HANDLER
  // ─────────────────────────────────────────────────────────────

  const ErrorHandler = {
    async fromResponse(response) {
      let detail = null;
      try {
        const data = await response.json();
        detail = data?.detail || data?.message || null;
      } catch (_) { /* body wasn't JSON */ }

      const messages = {
        400: detail || 'This image could not be processed. Please try a clearer chart image.',
        401: 'Your session has expired. Please sign in again.',
        403: "You don't have permission to use this tool.",
        404: 'The Chart Explainer service is unavailable right now.',
        422: detail || 'Some of the settings sent were invalid. Please adjust and try again.',
        500: 'The AI service ran into a problem while analyzing this chart. Please try again.',
        502: 'The AI service is temporarily unreachable. Please try again shortly.',
      };

      const message = messages[response.status] || detail || `Unexpected error (${response.status}).`;
      const error = new Error(message);
      error.status = response.status;
      return error;
    },

    show(err) {
      let message;

      if (err?.name === 'AbortError') {
        message = 'The analysis took too long and timed out. Please try again.';
      } else if (!navigator.onLine) {
        message = "You're offline. Check your connection and try again.";
      } else if (err instanceof TypeError) {
        message = 'Could not reach the server. Please check your connection and try again.';
      } else {
        message = err?.message || 'Something went wrong. Please try again.';
      }

      dom.errorMessage.textContent = message;
      state.phase = 'error';
      showPhase(dom.phaseError);
    },
  };

  // ─────────────────────────────────────────────────────────────
  // RENDERER — only renders response fields that actually exist
  // ─────────────────────────────────────────────────────────────

  const Renderer = {
    renderResults(data) {
      dom.resultsBody.innerHTML = '';

      if (data.chart_type) {
        dom.chartTypeBadge.textContent = data.chart_type;
        dom.chartTypeBadge.hidden = false;
      } else {
        dom.chartTypeBadge.hidden = true;
      }

      let delay = 0;
      CARD_DEFS.forEach((def) => {
        const value = data[def.key];
        if (!this.hasContent(value)) return;

        const card = this.buildCard(def, value);
        card.style.animationDelay = `${delay}ms`;
        dom.resultsBody.appendChild(card);
        delay += 60;
      });

      if (!dom.resultsBody.children.length) {
        const empty = document.createElement('div');
        empty.className = 'ce-empty-state metric-card';
        empty.textContent = 'No sections were returned for this chart.';
        dom.resultsBody.appendChild(empty);
      }
    },

    hasContent(value) {
      if (value === null || value === undefined) return false;
      if (Array.isArray(value)) return value.length > 0;
      if (typeof value === 'string') return value.trim().length > 0;
      if (typeof value === 'number') return true;
      return false;
    },

    buildCard(def, value) {
      const card = document.createElement('article');
      card.className = `ce-card metric-card ce-card--${def.variant || def.type}`;
      card.dataset.field = def.key;

      const header = document.createElement('div');
      header.className = 'ce-card-header';

      const title = document.createElement('h3');
      title.className = 'ce-card-title';
      title.textContent = def.title;
      header.appendChild(title);

      const copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'ce-icon-btn ce-card-copy';
      copyBtn.setAttribute('aria-label', `Copy ${def.title}`);
      copyBtn.innerHTML = '<svg viewBox="0 0 16 16"><rect x="5" y="5" width="8" height="8" rx="1"/><path d="M3 11V3a1 1 0 0 1 1-1h8"/></svg>';
      copyBtn.addEventListener('click', () => {
        ClipboardManager.copyText(this.toPlainText(def, value), `${def.title} copied`);
      });
      header.appendChild(copyBtn);

      card.appendChild(header);
      card.appendChild(this.buildBody(def, value));

      return card;
    },

    buildBody(def, value) {
      const body = document.createElement('div');
      body.className = 'ce-card-body';

      if (def.type === 'hero' || def.type === 'text') {
        body.textContent = value;
        return body;
      }

      if (def.type === 'list') {
        const list = document.createElement('ul');
        list.className = 'ce-card-list';
        value.forEach((item) => {
          const li = document.createElement('li');
          li.textContent = item;
          list.appendChild(li);
        });
        body.appendChild(list);
        return body;
      }

      if (def.type === 'confidence') {
        const score = Math.max(0, Math.min(100, Number(value)));
        const row = document.createElement('div');
        row.className = 'ce-confidence-row';

        const track = document.createElement('div');
        track.className = 'ce-confidence-track';
        const fill = document.createElement('div');
        fill.className = 'ce-confidence-fill';
        fill.style.width = '0%';
        track.appendChild(fill);

        const valueEl = document.createElement('span');
        valueEl.className = 'ce-confidence-value';
        valueEl.textContent = `${score}%`;

        row.appendChild(track);
        row.appendChild(valueEl);
        body.appendChild(row);

        requestAnimationFrame(() => {
          requestAnimationFrame(() => { fill.style.width = `${score}%`; });
        });

        return body;
      }

      return body;
    },

    toPlainText(def, value) {
      if (Array.isArray(value)) {
        return `${def.title}\n${value.map((v) => `- ${v}`).join('\n')}`;
      }
      if (def.type === 'confidence') {
        return `${def.title}: ${value}%`;
      }
      return `${def.title}\n${value}`;
    },
  };

  // ─────────────────────────────────────────────────────────────
  // EXPORT MANAGER
  // ─────────────────────────────────────────────────────────────

  const ExportManager = {
    buildReportSections() {
      if (!state.result) return [];
      return CARD_DEFS
        .filter((def) => Renderer.hasContent(state.result[def.key]))
        .map((def) => ({ title: def.title, value: state.result[def.key], type: def.type }));
    },

    toMarkdown() {
      const chartType = state.result.chart_type ? `**Chart Type:** ${state.result.chart_type}\n\n` : '';
      const sections = this.buildReportSections().map(({ title, value, type }) => {
        if (Array.isArray(value)) {
          return `## ${title}\n\n${value.map((v) => `- ${v}`).join('\n')}`;
        }
        if (type === 'confidence') {
          return `## ${title}\n\n${value}%`;
        }
        return `## ${title}\n\n${value}`;
      });
      return `# Chart Analysis\n\n${chartType}${sections.join('\n\n')}\n`;
    },

    toPlainText() {
      const chartType = state.result.chart_type ? `Chart Type: ${state.result.chart_type}\n\n` : '';
      const sections = this.buildReportSections().map(({ title, value, type }) => {
        if (Array.isArray(value)) {
          return `${title}\n${value.map((v) => `- ${v}`).join('\n')}`;
        }
        if (type === 'confidence') {
          return `${title}: ${value}%`;
        }
        return `${title}\n${value}`;
      });
      return `CHART ANALYSIS\n\n${chartType}${sections.join('\n\n')}\n`;
    },

    toJSON() {
      return JSON.stringify(state.result, null, 2);
    },

    download(content, filename, mimeType) {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },

    run(format) {
      if (!state.result) return;

      switch (format) {
        case 'markdown':
          this.download(this.toMarkdown(), 'chart-analysis.md', 'text/markdown');
          break;
        case 'txt':
          this.download(this.toPlainText(), 'chart-analysis.txt', 'text/plain');
          break;
        case 'json':
          this.download(this.toJSON(), 'chart-analysis.json', 'application/json');
          break;
        case 'print':
          window.print();
          break;
      }
    },
  };

  // ─────────────────────────────────────────────────────────────
  // TOAST (reuses existing platform .toast* classes)
  // ─────────────────────────────────────────────────────────────

  const Toast = {
    show(message, type = 'info') {
      const container = document.getElementById('toast-container') || (() => {
        const el = document.createElement('div');
        el.id = 'toast-container';
        el.className = 'toast-container';
        el.setAttribute('role', 'status');
        el.setAttribute('aria-live', 'polite');
        document.body.appendChild(el);
        return el;
      })();

      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.textContent = message;
      container.appendChild(toast);

      setTimeout(() => {
        toast.classList.add('toast-exit');
        toast.addEventListener('animationend', () => toast.remove(), { once: true });
      }, 3600);
    },
  };

  // ─────────────────────────────────────────────────────────────
  // AUTH TOKEN HELPER
  // ─────────────────────────────────────────────────────────────

  const AuthHelper = {
    getToken() {
      const meta = document.querySelector('meta[name="auth-token"]');
      if (meta) return meta.content;

      const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
      return match ? decodeURIComponent(match[1]) : null;
    },
  };

  // ─────────────────────────────────────────────────────────────
  // FORMATTERS
  // ─────────────────────────────────────────────────────────────

  const Formatters = {
    bytes(size) {
      if (size < 1024) return `${size} B`;
      if (size < 1024 ** 2) return `${(size / 1024).toFixed(1)} KB`;
      return `${(size / 1024 ** 2).toFixed(1)} MB`;
    },
  };

  // ─────────────────────────────────────────────────────────────
  // RESET
  // ─────────────────────────────────────────────────────────────

  const resetAll = () => {
    UploadManager.clear();
    state.result = null;
    state.phase = 'upload';
    dom.resultsBody.innerHTML = '';
    showPhase(dom.phaseUpload);
  };

  // ─────────────────────────────────────────────────────────────
  // BIND EVENTS
  // ─────────────────────────────────────────────────────────────

  const bindEvents = () => {
    // Upload zone
    dom.uploadZone.addEventListener('click', (e) => {
      if (dom.uploadZone.classList.contains('ce-upload-zone--has-file')) return;
      dom.fileInput.click();
    });
    dom.uploadZone.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && !dom.uploadZone.classList.contains('ce-upload-zone--has-file')) {
        e.preventDefault();
        dom.fileInput.click();
      }
    });
    dom.fileInput.addEventListener('change', () => {
      if (dom.fileInput.files[0]) UploadManager.handle(dom.fileInput.files[0]);
    });

    dom.replaceBtn.addEventListener('click', (e) => { e.stopPropagation(); dom.fileInput.click(); });
    dom.removeBtn.addEventListener('click', (e) => { e.stopPropagation(); UploadManager.clear(); });

    dom.previewFullscreenBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dom.lightboxImage.src = state.previewUrl;
      dom.lightbox.hidden = false;
      dom.lightbox.removeAttribute('aria-hidden');
    });
    dom.lightboxClose.addEventListener('click', () => {
      dom.lightbox.hidden = true;
      dom.lightbox.setAttribute('aria-hidden', 'true');
    });
    dom.lightbox.addEventListener('click', (e) => {
      if (e.target === dom.lightbox) dom.lightboxClose.click();
    });

    // Continue → configure
    dom.continueBtn.addEventListener('click', () => {
      state.phase = 'configure';
      showPhase(dom.phaseConfigure);
    });

    // Back → upload
    dom.backBtn.addEventListener('click', () => {
      state.phase = 'upload';
      showPhase(dom.phaseUpload);
    });

    // Language
    dom.languageSelect.addEventListener('change', () => {
      state.config.language = dom.languageSelect.value;
    });

    // Segmented control (explanation level)
    dom.segmented.forEach((btn) => {
      btn.addEventListener('click', () => {
        dom.segmented.forEach((b) => {
          b.classList.remove('ce-segmented-option--active');
          b.setAttribute('aria-checked', 'false');
        });
        btn.classList.add('ce-segmented-option--active');
        btn.setAttribute('aria-checked', 'true');
        state.config.explanation_level = btn.dataset.value;
      });
    });

    // Toggles
    const toggleMap = {
      'ce-toggle-summary': 'summary',
      'ce-toggle-axis': 'axis',
      'ce-toggle-insights': 'insights',
      'ce-toggle-trend': 'trend',
      'ce-toggle-outliers': 'outliers',
      'ce-toggle-business': 'business',
      'ce-toggle-recommendations': 'recommendations',
      'ce-toggle-questions': 'questions',
      'ce-toggle-limitations': 'limitations',
      'ce-toggle-eli5': 'eli5',
      'ce-toggle-confidence': 'confidence',
    };
    Object.entries(toggleMap).forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('change', () => { state.config.toggles[key] = el.checked; });
    });

    // Analyze
    dom.analyzeBtn.addEventListener('click', analyzeChart);

    // Results actions
    dom.copyAllBtn.addEventListener('click', () => {
      ClipboardManager.copyText(ExportManager.toPlainText(), 'Report copied to clipboard');
    });

    dom.exportBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = !dom.exportDropdown.hidden;
      dom.exportDropdown.hidden = isOpen;
      dom.exportBtn.setAttribute('aria-expanded', String(!isOpen));
    });
    document.addEventListener('click', (e) => {
      if (!dom.exportDropdown.hidden && !e.target.closest('.ce-export-menu')) {
        dom.exportDropdown.hidden = true;
        dom.exportBtn.setAttribute('aria-expanded', 'false');
      }
    });
    dom.exportDropdown.querySelectorAll('[data-export]').forEach((btn) => {
      btn.addEventListener('click', () => {
        ExportManager.run(btn.dataset.export);
        dom.exportDropdown.hidden = true;
        dom.exportBtn.setAttribute('aria-expanded', 'false');
      });
    });

    dom.newAnalysisBtn.addEventListener('click', resetAll);

    // Error phase actions
    dom.errorRetryBtn.addEventListener('click', () => {
      if (state.lastErrorRetry) {
        state.phase = 'configure';
        showPhase(dom.phaseConfigure);
        state.lastErrorRetry();
      }
    });
    dom.errorBackBtn.addEventListener('click', resetAll);

    // Escape closes lightbox
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !dom.lightbox.hidden) dom.lightboxClose.click();
    });

    // Offline/online awareness
    window.addEventListener('offline', () => Toast.show("You're offline. Some features may not work.", 'error'));
    window.addEventListener('online', () => Toast.show('Back online.', 'success'));
  };

  // ─────────────────────────────────────────────────────────────
  // INIT
  // ─────────────────────────────────────────────────────────────

  const init = () => {
    cacheDOM();
    bindEvents();
    DragDropManager.init();
    ClipboardManager.initPaste();
    UploadManager.updateContinueBtn();
    showPhase(dom.phaseUpload);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();