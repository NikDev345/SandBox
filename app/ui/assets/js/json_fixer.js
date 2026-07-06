/* ==========================================================================
   JSON Repair Tool — json_fixer.js
   SandBox Developer Tools
   Vanilla ES6+ · No frameworks · No jQuery
   ========================================================================== */

/* ─── Namespace ─────────────────────────────────────────────────────────── */

const JsonFixer = (() => {

  /* ─── DOM Cache ─────────────────────────────────────────────────────────
     All DOM references resolved once on init.
     Never call querySelector again outside this block.
  ─────────────────────────────────────────────────────────────────────── */

  let el = {};

  const cacheDOM = () => {
    el = {
      input:        document.getElementById('json-input-textarea'),
      output:       document.getElementById('json-output-textarea'),
      fileInput:    document.getElementById('json-file-input'),
      dropzone:   document.querySelector('.jf-upload-strip'),
      repairBtn:    document.querySelector('.repair-action-btn'),
      copyBtn:      document.querySelector('[data-action="copy"]'),
      downloadBtn:  document.querySelector('[data-action="download"]'),
      clearBtn:     document.querySelector('[data-action="clear"]'),
      exampleChips: document.querySelectorAll('.chip[data-example]'),
      statusCard:   document.getElementById('repair-status-card'),
      statusList: document.getElementById('jf-repairs-list'),
      charCount:    document.getElementById('jf-char-count'),
      outputHint:   document.getElementById('jf-output-hint'),
    };
  };

  /* ─── Example Payloads ──────────────────────────────────────────────────
     Predefined malformed JSON snippets mapped to chip data-example values.
  ─────────────────────────────────────────────────────────────────────── */

  const EXAMPLES = {
    'trailing-commas': `{
  "name": "Alex",
  "age": 30,
  "skills": ["JavaScript", "Python",],
}`,

    'single-quotes': `{
  'name': 'Jordan',
  'role': 'developer',
  'active': true
}`,

    'missing-commas': `{
  "host": "localhost"
  "port": 5432
  "database": "sandbox_db"
}`,

    'unquoted-keys': `{
  name: "Taylor",
  age: 28,
  department: "Engineering"
}`,

    'comments': `{
  // Server configuration
  "host": "localhost",
  /* Port number */
  "port": 8080,
  "debug": true // enable debug mode
}`,

    'markdown-wrapper': `\`\`\`json
{
  "model": "claude-sonnet-4-6",
  "temperature": 0.7,
  "max_tokens": 1000
}
\`\`\``,

    'broken-arrays': `{
  "tags": ["alpha", "beta" "gamma",],
  "scores": [10, 20, 30,
  "matrix": [[1,2],[3,4]
}`,
  };

  /* ─── State ─────────────────────────────────────────────────────────────
     Minimal mutable state for the tool session.
  ─────────────────────────────────────────────────────────────────────── */

  const state = {
    isRepairing:   false,
    lastFixedJson: '',
  };

  /* ─── Notifications ─────────────────────────────────────────────────────
     Lightweight toast system. Never uses alert().
     Injects a transient DOM node, auto-removes after 3 s.
  ─────────────────────────────────────────────────────────────────────── */

  const createToast = (message, type) => {
    const existing = document.getElementById('jf-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'jf-toast';

    const colors = {
      success: { bg: 'rgba(34,197,94,0.12)',   border: 'rgba(34,197,94,0.3)',   text: '#22c55e' },
      error:   { bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)',   text: '#ef4444' },
      info:    { bg: 'rgba(255,255,255,0.07)', border: 'rgba(255,255,255,0.15)', text: '#a0a0a0' },
    };

    const c    = colors[type] || colors.info;
    const icons = { success: '✓', error: '✕', info: 'i' };

    Object.assign(toast.style, {
      position:     'fixed',
      bottom:       '1.5rem',
      right:        '1.5rem',
      zIndex:       '9999',
      display:      'flex',
      alignItems:   'center',
      gap:          '0.625rem',
      background:   c.bg,
      border:       `1px solid ${c.border}`,
      borderRadius: '10px',
      padding:      '0.75rem 1.125rem',
      color:        c.text,
      fontSize:     '0.8125rem',
      fontWeight:   '500',
      boxShadow:    '0 8px 32px rgba(0,0,0,0.4)',
      opacity:      '0',
      transform:    'translateY(8px)',
      transition:   'opacity 0.2s ease, transform 0.2s ease',
      maxWidth:     '360px',
      lineHeight:   '1.4',
    });

    toast.innerHTML = `<span style="font-size:0.875rem;flex-shrink:0">${icons[type] || 'i'}</span><span>${message}</span>`;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity   = '1';
      toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity   = '0';
      toast.style.transform = 'translateY(8px)';
      setTimeout(() => toast.remove(), 220);
    }, 3000);
  };

  const showSuccess = (message) => createToast(message, 'success');
  const showError   = (message) => createToast(message, 'error');
  const showInfo    = (message) => createToast(message, 'info');

  /* ─── Character / Line / Word Counter ──────────────────────────────────
     Updates the subtitle badge next to the Input JSON card header.
  ─────────────────────────────────────────────────────────────────────── */

  const updateCounter = () => {
    if (!el.charCount || !el.input) return;

    const text = el.input.value;

    if (!text.trim()) {
      el.charCount.textContent = '0 characters';
      return;
    }

    const chars = text.length;
    const lines = text.split('\n').length;
    const words = text.trim().split(/\s+/).filter(Boolean).length;

    el.charCount.textContent = `${chars.toLocaleString()} chars · ${lines} lines · ${words} words`;
  };

  /* ─── Status Card ───────────────────────────────────────────────────────
     Shows the repair summary panel below the output.
  ─────────────────────────────────────────────────────────────────────── */

  const showStatusCard = (repairs = []) => {
    if (!el.statusCard) return;

    if (el.statusList) {
      el.statusList.innerHTML = '';

      repairs.forEach((repair) => {
        const li = document.createElement('li');
        li.textContent = repair;
        el.statusList.appendChild(li);
      });
    }

    el.statusCard.removeAttribute('hidden');
  };

  const hideStatusCard = () => {
    if (el.statusCard) el.statusCard.setAttribute('hidden', '');
  };

  /* ─── Repair Button State ───────────────────────────────────────────────
     Toggle loading UI without re-querying the DOM.
  ─────────────────────────────────────────────────────────────────────── */

  const setRepairLoading = (loading) => {
    if (!el.repairBtn) return;
    el.repairBtn.disabled      = loading;
    el.repairBtn.textContent   = loading ? 'Repairing…' : 'Repair JSON';
    el.repairBtn.style.opacity = loading ? '0.65' : '1';
  };

  /* ─── Repair JSON ───────────────────────────────────────────────────────
     Core async function. POSTs to /json-fixer/fix and handles response.
  ─────────────────────────────────────────────────────────────────────── */

  const repairJson = async () => {
    if (state.isRepairing) return;

    const rawInput = el.input?.value?.trim();

    if (!rawInput) {
      showError('Input is empty. Paste or upload some JSON first.');
      return;
    }

    state.isRepairing = true;
    setRepairLoading(true);
    hideStatusCard();

    try {
      const token    = localStorage.getItem('access_token');
      const response = await fetch('/json-fixer/fix', {
        method:  'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ json_text: rawInput }),
      });

      if (!response.ok) {
        let detail = `Server error (${response.status})`;
        try {
          const err = await response.json();
          if (err?.detail || err?.message) detail = err.detail || err.message;
        } catch (_) { /* non-JSON error body */ }
        throw new Error(detail);
      }

      const data = await response.json();

      if (!data?.fixed_json) {
        throw new Error('Unexpected response format from server.');
      }

      state.lastFixedJson = data.fixed_json;

      if (el.output) {
        el.output.value = data.fixed_json;
      }

      if (el.outputHint) {
        el.outputHint.hidden = true;
      }

      // Use repairs from backend; fall back to empty array (never crash).
      const repairs = Array.isArray(data.repairs) && data.repairs.length
        ? data.repairs
        : [];

      showStatusCard(repairs);
      showSuccess(data.message || 'JSON repaired successfully.');

    } catch (err) {
      console.error('[JsonFixer] Repair failed:', err);
      showError(err.message || 'Repair failed. Please try again.');
    } finally {
      state.isRepairing = false;
      setRepairLoading(false);
    }
  };

  /* ─── Copy Output ───────────────────────────────────────────────────────
     Writes repaired JSON to clipboard with visual confirmation.
  ─────────────────────────────────────────────────────────────────────── */

  const copyOutput = async () => {
    const text = el.output?.value?.trim();

    if (!text) {
      showError('Nothing to copy. Run a repair first.');
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      showSuccess('Copied to clipboard.');

      if (el.copyBtn) {
        const original = el.copyBtn.innerHTML;
        el.copyBtn.innerHTML = '<span aria-hidden="true">✓</span>';
        setTimeout(() => { el.copyBtn.innerHTML = original; }, 1800);
      }
    } catch (err) {
      console.error('[JsonFixer] Clipboard write failed:', err);
      showError('Could not access clipboard.');
    }
  };

  /* ─── Download Output ───────────────────────────────────────────────────
     Triggers a browser download of the repaired JSON as fixed.json.
  ─────────────────────────────────────────────────────────────────────── */

  const downloadOutput = () => {
    const text = el.output?.value?.trim();

    if (!text) {
      showError('Nothing to download. Run a repair first.');
      return;
    }

    const blob = new Blob([text], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href          = url;
    link.download      = 'fixed.json';
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
    showSuccess('Downloaded as fixed.json.');
  };

  /* ─── Clear All ─────────────────────────────────────────────────────────
     Resets the entire tool to its initial empty state.
  ─────────────────────────────────────────────────────────────────────── */

  const clearAll = () => {
    if (el.input)      el.input.value  = '';
    if (el.output)     el.output.value = '';
    if (el.outputHint) el.outputHint.hidden = false;
    if (el.fileInput)  el.fileInput.value   = '';

    state.lastFixedJson = '';

    hideStatusCard();
    if (el.statusList) el.statusList.innerHTML = '';
    updateCounter();

    const uploadText = el.dropzone?.querySelector('.jf-upload-trigger-text');
    const uploadHint = el.dropzone?.querySelector('.jf-upload-types');
    if (uploadText) uploadText.textContent = 'Upload file';
    if (uploadHint) uploadHint.textContent = '.json · .txt · .log · .md';

    showInfo('Cleared.');
  };

  /* ─── File Upload ───────────────────────────────────────────────────────
     Reads the selected file with FileReader. Populates input textarea.
     Does NOT send anything to the backend.
  ─────────────────────────────────────────────────────────────────────── */

  const ALLOWED_EXTENSIONS = ['.json', '.txt', '.log', '.md'];

  const formatBytes = (bytes) => {
    if (bytes < 1024)    return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(2)} MB`;
  };

  const handleFileUpload = (file) => {
    if (!file) return;

    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      showError(`Unsupported file type "${ext}". Use .json, .txt, .log, or .md.`);
      return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
      const content = e.target.result;

      if (el.input) {
        el.input.value = content;
        updateCounter();
      }

      const uploadText = el.dropzone?.querySelector('.jf-upload-trigger-text');
    const uploadHint = el.dropzone?.querySelector('.jf-upload-types');
    if (uploadText) uploadText.textContent = file.name;
    if (uploadHint) uploadHint.textContent = formatBytes(file.size);

      showSuccess(`Loaded "${file.name}" (${formatBytes(file.size)})`);
    };

    reader.onerror = () => {
      showError('Failed to read the file.');
    };

    reader.readAsText(file);
  };

  /* ─── Example Loader ────────────────────────────────────────────────────
     Clicking a chip fills the input textarea with a preset broken JSON.
  ─────────────────────────────────────────────────────────────────────── */

  const loadExample = (key) => {
    const payload = EXAMPLES[key];

    if (!payload) {
      showError('Example not found.');
      return;
    }

    if (el.input) {
      el.input.value = payload;
      updateCounter();
      el.input.focus();
    }

    const chip = document.querySelector(`.chip[data-example="${key}"]`);
    if (chip) {
      chip.classList.add('chip--active');
      setTimeout(() => chip.classList.remove('chip--active'), 700);
    }
  };

  /* ─── Drag & Drop ───────────────────────────────────────────────────────
     Allows users to drag a file directly onto the dropzone.
  ─────────────────────────────────────────────────────────────────────── */

  const bindDragDrop = () => {
    if (!el.dropzone) return;

    el.dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      el.dropzone.style.borderColor = 'rgba(255,255,255,0.35)';
      el.dropzone.style.background  = 'rgba(255,255,255,0.04)';
    });

    el.dropzone.addEventListener('dragleave', () => {
      el.dropzone.style.borderColor = '';
      el.dropzone.style.background  = '';
    });

    el.dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      el.dropzone.style.borderColor = '';
      el.dropzone.style.background  = '';
      const file = e.dataTransfer?.files?.[0];
      if (file) handleFileUpload(file);
    });
  };

  /* ─── Event Binding ─────────────────────────────────────────────────────
     All event listeners registered in one place, once.
  ─────────────────────────────────────────────────────────────────────── */

  const bindEvents = () => {
    el.repairBtn?.addEventListener('click', repairJson);

    el.copyBtn?.addEventListener('click',     copyOutput);
    el.downloadBtn?.addEventListener('click', downloadOutput);
    el.clearBtn?.addEventListener('click',    clearAll);

    el.fileInput?.addEventListener('change', (e) => {
      handleFileUpload(e.target.files?.[0]);
    });

    el.input?.addEventListener('input', updateCounter);

    el.exampleChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        loadExample(chip.dataset.example);
      });
    });

    bindDragDrop();

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        repairJson();
      }
    });
  };

  /* ─── Init ──────────────────────────────────────────────────────────────
     Entry point. Wires everything up after DOM is ready.
  ─────────────────────────────────────────────────────────────────────── */

  const init = () => {
    cacheDOM();
    bindEvents();
    updateCounter();
    hideStatusCard();
    if (el.outputHint) el.outputHint.hidden = false;
  };

  /* ─── Bootstrap ─────────────────────────────────────────────────────────
     Safe to call after DOMContentLoaded or immediately if DOM is ready.
  ─────────────────────────────────────────────────────────────────────── */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ─── Public API ─────────────────────────────────────────────────────── */
  return { repairJson, copyOutput, downloadOutput, clearAll };

})();