/**
 * image_text_extractor.js
 * SandBox AI SaaS — Image Text Extractor Module
 *
 * Architecture:
 *   - IIFE / module scope to avoid polluting window
 *   - DOM references resolved once in init()
 *   - State held in a single plain object
 *   - API interaction via uploadImage() → POST /image-text-extractor/extract
 *   - Falls back to Tesseract.js (loaded lazily) when API is unavailable
 */

(function ImageTextExtractorModule() {
  'use strict';

  /* ═══════════════════════════════════════════════════════════════════════════
     STATE
  ═══════════════════════════════════════════════════════════════════════════ */

  const state = {
    file:        null,   // File object
    objectURL:   null,   // revocable URL for the preview image
    imgWidth:    0,
    imgHeight:   0,
    zoom:        1,
    rotation:    0,      // degrees (multiples of 90)
    extractedText: '',
    isExtracting: false,
    startTime:   0,
  };

  /* ═══════════════════════════════════════════════════════════════════════════
     DOM REFS
  ═══════════════════════════════════════════════════════════════════════════ */

  let dom = {};

  function resolveDOM() {
    const root = document.querySelector('.image-text-extractor');
    if (!root) {
      console.error('[ITE] Root element .image-text-extractor not found.');
      return false;
    }

    const q = (sel) => root.querySelector(sel);

    dom = {
      root,

      // Upload
      uploadZone:       q('#iteUploadZone'),
      fileInput:        q('#iteFileInput'),
      replaceInput:     document.querySelector('#iteReplaceInput'),
      uploadIdle:       q('#iteUploadIdle'),
      uploadDropping:   q('#iteUploadDropping'),
      uploadTrigger:    q('#iteUploadTrigger'),

      // Workspace
      workspace:        q('#iteWorkspace'),
      imageViewport:    q('#iteImageViewport'),
      imagePreview:     q('#iteImagePreview'),
      imageInfo:        q('#iteImageInfo'),

      // Image info
      infoName:         q('#iteInfoName'),
      infoRes:          q('#iteInfoRes'),
      infoFormat:       q('#iteInfoFormat'),
      infoSize:         q('#iteInfoSize'),

      // Image controls
      btnZoomIn:        q('#iteZoomIn'),
      btnZoomOut:       q('#iteZoomOut'),
      btnRotateLeft:    q('#iteRotateLeft'),
      btnRotateRight:   q('#iteRotateRight'),
      btnFit:           q('#iteFit'),
      btnReplace:       q('#iteReplace'),
      btnRemove:        q('#iteRemove'),

      // Output
      outputEmpty:      q('#iteOutputEmpty'),
      outputLoading:    q('#iteOutputLoading'),
      outputTextarea:   q('#iteOutputTextarea'),
      progressFill:     q('#iteProgressFill'),

      // Output controls
      btnCopy:          q('#iteCopy'),
      btnDownloadTxt:   q('#iteDownloadTxt'),
      btnDownloadJson:  q('#iteDownloadJson'),
      btnDownloadPdf:   q('#iteDownloadPdf'),
      btnClearOutput:   q('#iteClearOutput'),

      // Action bar
      actionBar:        q('#iteActionBar'),
      extractBtn:       q('#iteExtractBtn'),

      // Status
      statusCard:       q('#iteStatusCard'),
      statusIcon:       q('#iteStatusIcon'),
      statusTitle:      q('#iteStatusTitle'),
      statusBody:       q('#iteStatusBody'),

      // Stats
      statsGrid:        q('#iteStatsGrid'),
      statChars:        q('#statChars'),
      statWords:        q('#statWords'),
      statLines:        q('#statLines'),
      statParagraphs:   q('#statParagraphs'),
      statConfidence:   q('#statConfidence'),
      statTime:         q('#statTime'),
      statLang:         q('#statLang'),
    };

    return true;
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     INITIALISE
  ═══════════════════════════════════════════════════════════════════════════ */

  function initialize() {
    if (!resolveDOM()) return;
    bindEvents();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     EVENT BINDING
  ═══════════════════════════════════════════════════════════════════════════ */

  function bindEvents() {
    // Upload zone — click
    dom.uploadTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      dom.fileInput.click();
    });

    // Clicking anywhere in the zone also opens the picker
    dom.uploadZone.addEventListener('click', () => {
      if (!state.file) dom.fileInput.click();
    });

    // Keyboard activation for the zone
    dom.uploadZone.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && !state.file) {
        e.preventDefault();
        dom.fileInput.click();
      }
    });

    // File input change
    dom.fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) uploadImage(file);
      dom.fileInput.value = '';
    });

    // Drag & Drop
    dragAndDrop();

    // Paste
    pasteImage();

    // Image controls
    dom.btnZoomIn.addEventListener('click',      zoomIn);
    dom.btnZoomOut.addEventListener('click',     zoomOut);
    dom.btnRotateLeft.addEventListener('click',  rotateLeft);
    dom.btnRotateRight.addEventListener('click', rotateRight);
    dom.btnFit.addEventListener('click',         fitImage);
    dom.btnReplace.addEventListener('click',     () => dom.replaceInput.click());
    dom.btnRemove.addEventListener('click',      removeImage);

    if (dom.replaceInput) {
      dom.replaceInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) replaceImage(file);
        dom.replaceInput.value = '';
      });
    }

    // Output controls
    dom.btnCopy.addEventListener('click',         copyText);
    dom.btnDownloadTxt.addEventListener('click',  downloadTXT);
    dom.btnDownloadJson.addEventListener('click', downloadJSON);
    dom.btnDownloadPdf.addEventListener('click',  downloadPDF);
    dom.btnClearOutput.addEventListener('click',  clearOutput);

    // Extract
    dom.extractBtn.addEventListener('click', extractText);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     DRAG & DROP
  ═══════════════════════════════════════════════════════════════════════════ */

  function dragAndDrop() {
    const zone = dom.uploadZone;

    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
      zone.classList.add('is-dragging');
    });

    zone.addEventListener('dragleave', (e) => {
      if (!zone.contains(e.relatedTarget)) {
        zone.classList.remove('is-dragging');
      }
    });

    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('is-dragging');

      const files = e.dataTransfer.files;
      if (!files.length) return;

      const file = files[0];
      if (!isValidImageFile(file)) {
        showError('Unsupported file type.', 'Please upload a PNG, JPG, WEBP, BMP, TIFF, or GIF image.');
        return;
      }

      uploadImage(file);
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     PASTE IMAGE
  ═══════════════════════════════════════════════════════════════════════════ */

  function pasteImage() {
    document.addEventListener('paste', (e) => {
      // Only handle if the tool is in view
      if (!dom.root.getBoundingClientRect().height) return;

      const items = Array.from(e.clipboardData?.items || []);
      const imageItem = items.find((item) => item.type.startsWith('image/'));
      if (!imageItem) return;

      const file = imageItem.getAsFile();
      if (file) uploadImage(file);
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     UPLOAD IMAGE
  ═══════════════════════════════════════════════════════════════════════════ */

  function uploadImage(file) {
    if (!isValidImageFile(file)) {
      showError('Unsupported file type.', `"${file.name}" is not a supported image format.`);
      return;
    }

    const maxBytes = 25 * 1024 * 1024; // 25 MB
    if (file.size > maxBytes) {
      showError('File too large.', `"${file.name}" exceeds the 25 MB limit (${formatBytes(file.size)}).`);
      return;
    }

    // Clean up previous object URL
    if (state.objectURL) URL.revokeObjectURL(state.objectURL);

    state.file      = file;
    state.objectURL = URL.createObjectURL(file);
    state.zoom      = 1;
    state.rotation  = 0;

    previewImage();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     PREVIEW IMAGE
  ═══════════════════════════════════════════════════════════════════════════ */

  function previewImage() {
    const img = dom.imagePreview;
    img.src = state.objectURL;

    img.onload = () => {
      state.imgWidth  = img.naturalWidth;
      state.imgHeight = img.naturalHeight;

      applyTransform();
      updateImageInfo();

      // Show workspace
      dom.workspace.hidden = false;
      dom.actionBar.hidden = false;

      // Reset output when a new image is loaded
      clearOutput(false);
      hideStatus();
    };

    img.onerror = () => {
      showError('Preview failed.', 'Could not render the image. The file may be corrupt.');
    };
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     REPLACE / REMOVE IMAGE
  ═══════════════════════════════════════════════════════════════════════════ */

  function replaceImage(file) {
    uploadImage(file);
  }

  function removeImage() {
    if (state.objectURL) {
      URL.revokeObjectURL(state.objectURL);
    }

    state.file         = null;
    state.objectURL    = null;
    state.imgWidth     = 0;
    state.imgHeight    = 0;
    state.zoom         = 1;
    state.rotation     = 0;
    state.extractedText = '';

    dom.imagePreview.src = '';
    dom.workspace.hidden = true;
    dom.actionBar.hidden = true;
    dom.statsGrid.hidden = true;
    clearOutput(false);
    hideStatus();
    resetStats();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     IMAGE TRANSFORM CONTROLS
  ═══════════════════════════════════════════════════════════════════════════ */

  function applyTransform() {
    dom.imagePreview.style.transform =
      `rotate(${state.rotation}deg) scale(${state.zoom})`;
  }

  function zoomIn() {
    state.zoom = Math.min(state.zoom + 0.25, 4);
    applyTransform();
  }

  function zoomOut() {
    state.zoom = Math.max(state.zoom - 0.25, 0.25);
    applyTransform();
  }

  function rotateLeft() {
    state.rotation = (state.rotation - 90 + 360) % 360;
    applyTransform();
  }

  function rotateRight() {
    state.rotation = (state.rotation + 90) % 360;
    applyTransform();
  }

  function fitImage() {
    state.zoom     = 1;
    state.rotation = 0;
    applyTransform();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     IMAGE INFO
  ═══════════════════════════════════════════════════════════════════════════ */

  function updateImageInfo() {
    const f = state.file;
    if (!f) return;

    dom.infoName.textContent   = truncate(f.name, 20);
    dom.infoRes.textContent    = `${state.imgWidth} × ${state.imgHeight}`;
    dom.infoFormat.textContent = (f.type.split('/')[1] || '—').toUpperCase();
    dom.infoSize.textContent   = formatBytes(f.size);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     EXTRACT TEXT
  ═══════════════════════════════════════════════════════════════════════════ */

  async function extractText() {
    if (!state.file || state.isExtracting) return;

    state.isExtracting = true;
    state.startTime    = performance.now();

    showLoader();
    setProgress(5);

    try {
      const result = await callExtractAPI(state.file);

      const elapsed = ((performance.now() - state.startTime) / 1000).toFixed(2);
      const r = result.result;
      state.extractedText = r.extracted_text || '';

      hideLoader();
      renderOutput(state.extractedText);
      updateStatistics({
      confidence: r.statistics?.confidence != null
                    ? `${(r.statistics.confidence).toFixed(1)}%`
                    : '—',
      language:   r.language || 'eng',
      time:       elapsed,
      });

      showSuccess(
        'Extraction complete',
        `${formatNumber(state.extractedText.length)} characters extracted in ${elapsed}s.`
      );

    } catch (err) {
      hideLoader();
      showError('Extraction failed', err.message || 'An unexpected error occurred. Please try again.');
    } finally {
      state.isExtracting = false;
      dom.extractBtn.classList.remove('is-loading');
      dom.extractBtn.disabled = false;
    }
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     API CALL
  ═══════════════════════════════════════════════════════════════════════════ */

  async function callExtractAPI(file) {
    const formData = new FormData();
    formData.append('image', file);

    setProgress(20);

    let response;
    try {
      response = await fetch('/image-text-extractor/extract', {
        method: 'POST',
        body:   formData,
      });
    } catch (networkErr) {
      // Network error — try local Tesseract fallback
      return await runTesseractFallback(file);
    }

    setProgress(80);

    if (response.status === 401 || response.status === 403) {
      throw new Error('Authentication error. Please sign in again.');
    }

    if (response.status === 413) {
      throw new Error('The image is too large for the server. Try reducing its resolution.');
    }

    if (response.status === 422) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.message || 'Validation error: the server rejected the image.');
    }

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.message || `Server error (${response.status}). Please try again later.`);
    }

    const data = await response.json();
    setProgress(100);
    return data;
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     TESSERACT FALLBACK (client-side OCR)
  ═══════════════════════════════════════════════════════════════════════════ */

  async function runTesseractFallback(file) {
    // Dynamically load Tesseract.js if not already present
    if (typeof Tesseract === 'undefined') {
      await loadScript('https://unpkg.com/tesseract.js@5/dist/tesseract.min.js');
    }

    return new Promise((resolve, reject) => {
      const objectURL = URL.createObjectURL(file);

      Tesseract.recognize(objectURL, 'eng', {
        logger: (m) => {
          if (m.status === 'recognizing text') {
            const pct = 20 + Math.round(m.progress * 75);
            setProgress(pct);
          }
        },
      })
        .then(({ data }) => {
          URL.revokeObjectURL(objectURL);
          setProgress(100);
          resolve({
            text:       data.text,
            confidence: data.confidence ? `${Math.round(data.confidence)}%` : '—',
            language:   'eng',
          });
        })
        .catch((err) => {
          URL.revokeObjectURL(objectURL);
          reject(new Error('Client-side OCR failed: ' + (err.message || 'unknown error')));
        });
    });
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s   = document.createElement('script');
      s.src     = src;
      s.async   = true;
      s.onload  = resolve;
      s.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(s);
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     RENDER OUTPUT
  ═══════════════════════════════════════════════════════════════════════════ */

  function renderOutput(text) {
    dom.outputTextarea.value = text;
    dom.outputEmpty.style.display = text ? 'none' : '';
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     OUTPUT ACTIONS
  ═══════════════════════════════════════════════════════════════════════════ */

  async function copyText() {
    const text = dom.outputTextarea.value;
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      flashButton(dom.btnCopy, 'Copied!');
    } catch {
      // Fallback for older browsers
      dom.outputTextarea.select();
      document.execCommand('copy');
      flashButton(dom.btnCopy, 'Copied!');
    }
  }

  function downloadTXT() {
    const text = dom.outputTextarea.value;
    if (!text) return;
    downloadBlob(new Blob([text], { type: 'text/plain' }), getBaseName() + '.txt');
  }

  function downloadJSON() {
    const text = dom.outputTextarea.value;
    if (!text) return;

    const obj = {
      source:    state.file ? state.file.name : 'unknown',
      extracted: new Date().toISOString(),
      text,
      stats: {
        characters: text.length,
        words:      countWords(text),
        lines:      countLines(text),
        paragraphs: countParagraphs(text),
      },
    };

    downloadBlob(
      new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' }),
      getBaseName() + '.json'
    );
  }

  function downloadPDF() {
    const text = dom.outputTextarea.value;
    if (!text) return;

    // Build a minimal printable HTML page and trigger print-to-PDF
    const win = window.open('', '_blank');
    if (!win) {
      showError('Popup blocked', 'Please allow popups for this site to generate a PDF.');
      return;
    }

    const escaped = escapeHTML(text);
    const lines   = escaped.split('\n').join('<br>');

    win.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${escapeHTML(getBaseName())}</title>
  <style>
    body {
      font-family: ui-monospace, "Courier New", monospace;
      font-size: 12pt;
      line-height: 1.7;
      margin: 2cm;
      color: #111;
    }
    h1 {
      font-size: 14pt;
      margin-bottom: 1em;
      border-bottom: 1px solid #ccc;
      padding-bottom: 0.5em;
      color: #333;
      font-family: system-ui, sans-serif;
    }
    p {
      margin: 0;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <h1>Extracted Text — ${escapeHTML(state.file ? state.file.name : 'image')}</h1>
  <p>${lines}</p>
</body>
</html>`);

    win.document.close();
    win.focus();
    setTimeout(() => { win.print(); win.close(); }, 400);
  }

  function clearOutput(resetStatus = true) {
    state.extractedText   = '';
    dom.outputTextarea.value = '';
    dom.outputEmpty.style.display = '';
    dom.statsGrid.hidden  = true;
    if (resetStatus) hideStatus();
    resetStats();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     STATISTICS
  ═══════════════════════════════════════════════════════════════════════════ */

  function updateStatistics({ confidence = '—', language = '—', time = '—' } = {}) {
    const text = dom.outputTextarea.value;

    dom.statChars.textContent      = formatNumber(text.length);
    dom.statWords.textContent      = formatNumber(countWords(text));
    dom.statLines.textContent      = formatNumber(countLines(text));
    dom.statParagraphs.textContent = formatNumber(countParagraphs(text));
    dom.statConfidence.textContent = confidence || '—';
    dom.statTime.textContent       = time ? `${time}s` : '—';
    dom.statLang.textContent       = language ? language.toUpperCase() : '—';

    dom.statsGrid.hidden = false;
  }

  function resetStats() {
    ['statChars', 'statWords', 'statLines', 'statParagraphs',
     'statConfidence', 'statTime', 'statLang'].forEach((id) => {
      if (dom[id]) dom[id].textContent = '—';
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     LOADER / PROGRESS
  ═══════════════════════════════════════════════════════════════════════════ */

  function showLoader() {
    dom.outputEmpty.style.display    = 'none';
    dom.outputLoading.hidden         = false;
    dom.extractBtn.disabled          = true;
    dom.extractBtn.classList.add('is-loading');
    setProgress(0);
  }

  function hideLoader() {
    dom.outputLoading.hidden = true;
  }

  function setProgress(pct) {
    if (dom.progressFill) {
      dom.progressFill.style.width = `${Math.min(100, Math.max(0, pct))}%`;
    }
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     STATUS CARD
  ═══════════════════════════════════════════════════════════════════════════ */

  const STATUS_ICONS = {
    success:    svgCheck(),
    error:      svgX(),
    warning:    svgWarning(),
    processing: svgSpinner(),
  };

  function showStatus(type, title, body) {
    dom.statusCard.hidden = false;
    dom.statusCard.className = `ite-status-card is-${type}`;
    dom.statusIcon.innerHTML  = STATUS_ICONS[type] || '';
    dom.statusTitle.textContent = title;
    dom.statusBody.textContent  = body || '';
  }

  function hideStatus() {
    dom.statusCard.hidden = true;
  }

  function showSuccess(title, body) {
    showStatus('success', title, body);
  }

  function showError(title, body) {
    showStatus('error', title, body);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     RESET TOOL
  ═══════════════════════════════════════════════════════════════════════════ */

  function resetTool() {
    removeImage();
    hideStatus();
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     VALIDATION
  ═══════════════════════════════════════════════════════════════════════════ */

  const VALID_TYPES = new Set([
    'image/png', 'image/jpeg', 'image/webp',
    'image/bmp', 'image/tiff', 'image/gif',
  ]);

  function isValidImageFile(file) {
    if (!file) return false;
    if (VALID_TYPES.has(file.type)) return true;
    // Fallback: check extension
    const ext = file.name.split('.').pop().toLowerCase();
    return ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif', 'gif'].includes(ext);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     UTILITIES
  ═══════════════════════════════════════════════════════════════════════════ */

  function formatBytes(bytes) {
    if (bytes < 1024)       return bytes + ' B';
    if (bytes < 1024 ** 2)  return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 ** 2).toFixed(2) + ' MB';
  }

  function formatNumber(n) {
    return n.toLocaleString();
  }

  function countWords(text) {
    return (text.trim().match(/\S+/g) || []).length;
  }

  function countLines(text) {
    if (!text.trim()) return 0;
    return text.split('\n').length;
  }

  function countParagraphs(text) {
    if (!text.trim()) return 0;
    return text.split(/\n\s*\n/).filter((p) => p.trim().length > 0).length;
  }

  function truncate(str, maxLen) {
    return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str;
  }

  function getBaseName() {
    if (!state.file) return 'extracted-text';
    return state.file.name.replace(/\.[^.]+$/, '') || 'extracted-text';
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }

  function escapeHTML(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function flashButton(btn, label) {
    const original = btn.textContent.trim();
    const originalHTML = btn.innerHTML;
    btn.textContent = label;
    btn.disabled    = true;
    setTimeout(() => {
      btn.innerHTML  = originalHTML;
      btn.disabled   = false;
    }, 1500);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     INLINE SVG ICONS
  ═══════════════════════════════════════════════════════════════════════════ */

  function svgCheck() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>`;
  }

  function svgX() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
  }

  function svgWarning() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
  }

  function svgSpinner() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" aria-hidden="true" style="animation:ite-spin 1s linear infinite"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>`;
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     BOOT
  ═══════════════════════════════════════════════════════════════════════════ */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }

  // Expose for external routing (e.g., dashboard SPA re-initialises the tool)
  window.ImageTextExtractor = { initialize, resetTool };

})();