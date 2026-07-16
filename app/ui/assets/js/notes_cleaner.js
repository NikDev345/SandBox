'use strict';

/* ============================================================
   NOTES CLEANER — script.js
   Vanilla JS, no dependencies.
   Talks to: POST /notes_cleaner/clean  (multipart/form-data)
   Fields:   text (string, optional) | file (File, optional)
   Response: { title: string, cleaned_notes: string }
   ============================================================ */

(() => {
  const API_ENDPOINT = '/notes_cleaner/clean';
  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
  const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.docx'];

  const LOADING_MESSAGES = [
    'Extracting document...',
    'Reading notes...',
    'Cleaning grammar...',
    'Improving formatting...',
    'Organizing content...',
    'Finalizing cleaned notes...',
  ];

  /* ---------- DOM refs ---------- */
  const $ = (id) => document.getElementById(id);

  const inputCard      = $('inputCard');
  const textField       = $('textField');
  const fileField        = $('fileField');
  const notesText        = $('notesText');
  const charCounter      = $('charCounter');

  const dropzone          = $('dropzone');
  const dropzoneContent   = $('dropzoneContent');
  const fileInput         = $('fileInput');
  const browseBtn         = $('browseBtn');
  const filePreview       = $('filePreview');
  const fileNameEl        = $('fileName');
  const fileSizeEl        = $('fileSize');
  const fileRemoveBtn     = $('fileRemoveBtn');

  const cleanBtn          = $('cleanBtn');
  const cleanSpinner      = $('cleanSpinner');

  const loadingCard       = $('loadingCard');
  const loadingStatus     = $('loadingStatus');
  const progressFill      = $('progressFill');

  const outputCard        = $('outputCard');
  const outputTitle       = $('outputTitle');
  const outputBody        = $('outputBody');
  const copyBtn           = $('copyBtn');
  const downloadBtn       = $('downloadBtn');
  const clearBtn          = $('clearBtn');

  const toastStack        = $('toastStack');

  /* ---------- state ---------- */
  let selectedFile = null;
  let loadingInterval = null;
  let progressInterval = null;

  /* ============================================================
     TOASTS
     ============================================================ */
  const TOAST_ICONS = {
    success: '<path d="M20 6L9 17l-5-5"/>',
    error: '<circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  };

  function showToast(message, type = 'info', duration = 4200) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <svg viewBox="0 0 24 24">${TOAST_ICONS[type] || TOAST_ICONS.info}</svg>
      <p></p>
      <button type="button" class="toast-close" aria-label="Dismiss notification">
        <svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    `;
    toast.querySelector('p').textContent = message;
    toastStack.appendChild(toast);

    const remove = () => {
      toast.classList.add('leaving');
      toast.addEventListener('animationend', () => toast.remove(), { once: true });
    };

    toast.querySelector('.toast-close').addEventListener('click', remove);
    const timer = setTimeout(remove, duration);
    toast.addEventListener('mouseenter', () => clearTimeout(timer));
  }

  /* ============================================================
     CHARACTER COUNTER + TEXT / FILE MUTUAL EXCLUSIVITY
     ============================================================ */
  function formatCount(n) {
    return n.toLocaleString() + (n === 1 ? ' character' : ' characters');
  }

  function updateCharCounter() {
    const len = notesText.value.length;
    charCounter.textContent = formatCount(len);
    charCounter.classList.toggle('near-limit', len > 900000);
  }

  function syncInputLock() {
    const hasText = notesText.value.trim().length > 0;
    const hasFile = !!selectedFile;

    fileField.classList.toggle('is-locked', hasText);
    textField.classList.toggle('is-locked', hasFile);

    cleanBtn.disabled = !(hasText || hasFile);
  }

  notesText.addEventListener('input', () => {
    updateCharCounter();
    syncInputLock();
  });

  /* ============================================================
     FILE HANDLING
     ============================================================ */
  function extensionOf(filename) {
    const idx = filename.lastIndexOf('.');
    return idx === -1 ? '' : filename.slice(idx).toLowerCase();
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function validateFile(file) {
    const ext = extensionOf(file.name);
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type "${ext || 'unknown'}". Please upload a PDF, TXT or DOCX file.`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return `"${file.name}" is ${formatBytes(file.size)}, which exceeds the 50MB limit.`;
    }
    if (file.size === 0) {
      return `"${file.name}" appears to be empty.`;
    }
    return null;
  }

  function setFile(file) {
    const error = validateFile(file);
    if (error) {
      showToast(error, 'error');
      fileInput.value = '';
      return;
    }

    selectedFile = file;
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatBytes(file.size);

    dropzoneContent.classList.add('hidden');
    filePreview.classList.remove('hidden');
    dropzone.classList.add('has-file');
    dropzone.setAttribute('aria-label', `${file.name} selected. Use the remove button to choose a different file.`);

    syncInputLock();
  }

  function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    dropzoneContent.classList.remove('hidden');
    filePreview.classList.add('hidden');
    dropzone.classList.remove('has-file');
    dropzone.setAttribute('aria-label', 'Upload a PDF, TXT or DOCX file, up to 50 megabytes');
    syncInputLock();
  }

  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener('click', () => {
    if (!selectedFile) fileInput.click();
  });

  dropzone.addEventListener('keydown', (e) => {
    if ((e.key === 'Enter' || e.key === ' ') && !selectedFile) {
      e.preventDefault();
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      setFile(fileInput.files[0]);
    }
  });

  fileRemoveBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFile();
  });

  ['dragenter', 'dragover'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!selectedFile && !textField.classList.contains('is-locked')) {
        dropzone.classList.add('drag-over');
      }
    });
  });

  ['dragleave', 'dragend'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove('drag-over');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-over');

    if (notesText.value.trim().length > 0) {
      showToast('Clear the pasted text before uploading a file.', 'error');
      return;
    }

    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  /* ============================================================
     LOADING STATE
     ============================================================ */
  function startLoading() {
    inputCard.classList.add('hidden');
    outputCard.classList.add('hidden');
    loadingCard.classList.remove('hidden');

    let msgIndex = 0;
    loadingStatus.textContent = LOADING_MESSAGES[0];
    progressFill.style.width = '6%';

    loadingInterval = setInterval(() => {
      msgIndex = (msgIndex + 1) % LOADING_MESSAGES.length;
      loadingStatus.style.opacity = '0';
      setTimeout(() => {
        loadingStatus.textContent = LOADING_MESSAGES[msgIndex];
        loadingStatus.style.opacity = '1';
      }, 180);
    }, 2200);

    // Simulated progress toward 90%; final jump to 100% happens on completion.
    let progress = 6;
    progressInterval = setInterval(() => {
      progress = Math.min(progress + Math.random() * 9, 90);
      progressFill.style.width = `${progress}%`;
    }, 650);

    loadingStatus.style.transition = 'opacity 180ms ease';
  }

  function stopLoading() {
    clearInterval(loadingInterval);
    clearInterval(progressInterval);
    loadingCard.classList.add('hidden');
  }

  /* ============================================================
     SUBMIT
     ============================================================ */
  function triggerRipple(e) {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height) * 1.4;
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${(e.clientX ?? rect.left + rect.width / 2) - rect.left - size / 2}px`;
    ripple.style.top = `${(e.clientY ?? rect.top + rect.height / 2) - rect.top - size / 2}px`;
    btn.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  }

  async function handleClean(e) {
    if (cleanBtn.disabled) return;
    triggerRipple(e);

    const hasText = notesText.value.trim().length > 0;
    const hasFile = !!selectedFile;

    if (hasText === hasFile) {
      showToast(
        hasText ? 'Please use only one input method — text or file, not both.' : 'Paste some notes or upload a file to continue.',
        'error'
      );
      return;
    }

    cleanBtn.disabled = true;
    cleanBtn.classList.add('is-loading');
    cleanSpinner.classList.remove('hidden');
    inputCard.classList.add('sweeping');

    const formData = new FormData();
    if (hasText) {
      formData.append('text', notesText.value.trim());
    } else {
      formData.append('file', selectedFile);
    }

    await new Promise((r) => setTimeout(r, 320)); // let the sweep animation read
    inputCard.classList.remove('sweeping');
    startLoading();

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      let payload = null;
      try {
        payload = await response.json();
      } catch (_) {
        // no JSON body
      }

      if (!response.ok) {
        const detail =
          (payload && (payload.detail || payload.message)) ||
          `Something went wrong (${response.status}). Please try again.`;
        throw new Error(detail);
      }

      if (!payload || typeof payload.cleaned_notes !== 'string') {
        throw new Error('Received an unexpected response from the server.');
      }

      progressFill.style.width = '100%';
      await new Promise((r) => setTimeout(r, 260));

      showResult(payload);
      showToast('Your notes have been cleaned.', 'success');
    } catch (err) {
      const message =
        err instanceof TypeError
          ? 'Could not reach the server. Please check your connection and try again.'
          : (err.message || 'Failed to clean notes. Please try again.');
      showToast(message, 'error');
      stopLoading();
      inputCard.classList.remove('hidden');
    } finally {
      cleanBtn.disabled = false;
      cleanBtn.classList.remove('is-loading');
      cleanSpinner.classList.add('hidden');
      syncInputLock();
    }
  }

  cleanBtn.addEventListener('click', handleClean);

  /* ============================================================
     MARKDOWN RENDERING
     The backend returns cleaned notes as markdown (#, **, -, >, etc).
     Render it to HTML for display; keep the raw markdown source
     around for copy / download so nothing is lost either way.
     ============================================================ */
  let rawCleanedText = '';

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function inlineFormat(line) {
    return line
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.+?)__/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/(?<![\w*])_(.+?)_(?![\w*])/g, '<em>$1</em>');
  }

  function renderMarkdown(raw) {
    const lines = escapeHtml(raw).replace(/\r\n/g, '\n').split('\n');
    let html = '';
    let listType = null; // 'ul' | 'ol'
    let i = 0;

    const closeList = () => {
      if (listType) { html += `</${listType}>`; listType = null; }
    };

    const isBlockStart = (s) =>
      s.trim() === '' ||
      /^(#{1,6})\s+/.test(s.trim()) ||
      /^(-{3,}|\*{3,}|_{3,})$/.test(s.trim()) ||
      /^[-*]\s+/.test(s.trim()) ||
      /^\d+\.\s+/.test(s.trim()) ||
      /^>\s?/.test(s.trim());

    while (i < lines.length) {
      const trimmed = lines[i].trim();

      if (trimmed === '') { closeList(); i++; continue; }

      if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
        closeList();
        html += '<hr>';
        i++; continue;
      }

      const heading = trimmed.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        closeList();
        const level = heading[1].length;
        html += `<h${level}>${inlineFormat(heading[2])}</h${level}>`;
        i++; continue;
      }

      if (/^>\s?/.test(trimmed)) {
        closeList();
        const quoteLines = [];
        while (i < lines.length && /^>\s?/.test(lines[i].trim())) {
          quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
          i++;
        }
        html += `<blockquote>${inlineFormat(quoteLines.join(' '))}</blockquote>`;
        continue;
      }

      const ul = trimmed.match(/^[-*]\s+(.*)$/);
      if (ul) {
        if (listType !== 'ul') { closeList(); html += '<ul>'; listType = 'ul'; }
        html += `<li>${inlineFormat(ul[1])}</li>`;
        i++; continue;
      }

      const ol = trimmed.match(/^\d+\.\s+(.*)$/);
      if (ol) {
        if (listType !== 'ol') { closeList(); html += '<ol>'; listType = 'ol'; }
        html += `<li>${inlineFormat(ol[1])}</li>`;
        i++; continue;
      }

      closeList();
      const paraLines = [trimmed];
      i++;
      while (i < lines.length && !isBlockStart(lines[i])) {
        paraLines.push(lines[i].trim());
        i++;
      }
      html += `<p>${inlineFormat(paraLines.join(' '))}</p>`;
    }

    closeList();
    return html;
  }

  /* ============================================================
     OUTPUT
     ============================================================ */
  function showResult(payload) {
    stopLoading();
    rawCleanedText = payload.cleaned_notes;
    outputTitle.textContent = payload.title || 'Cleaned Notes';
    outputBody.innerHTML = renderMarkdown(rawCleanedText);
    outputCard.classList.remove('hidden');
    outputCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(rawCleanedText);
      showToast('Copied to clipboard.', 'success', 2200);
    } catch (_) {
      showToast('Could not copy automatically — please select and copy manually.', 'error');
    }
  });

  downloadBtn.addEventListener('click', () => {
    const blob = new Blob([rawCleanedText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const safeName = (outputTitle.textContent || 'cleaned-notes').trim().replace(/[^\w\- ]+/g, '').slice(0, 60) || 'cleaned-notes';
    a.href = url;
    a.download = `${safeName}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Download started.', 'success', 2200);
  });

  clearBtn.addEventListener('click', () => {
    outputCard.classList.add('hidden');
    outputBody.innerHTML = '';
    rawCleanedText = '';
    notesText.value = '';
    clearFile();
    updateCharCounter();
    syncInputLock();
    inputCard.classList.remove('hidden');
    inputCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  /* ============================================================
     INIT
     ============================================================ */
  updateCharCounter();
  syncInputLock();
})();