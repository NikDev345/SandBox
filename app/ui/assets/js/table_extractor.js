/**
 * Table Extractor — Frontend Logic
 * Vanilla JS, no external dependencies.
 * Scoped under the "te" namespace.
 */

'use strict';

/* ============================================================
   STATE
   ============================================================ */

const state = {
  file: null,
  outputFormat: 'json',
  result: null,
  currentTableIndex: 0,
  currentPage: 1,
  rowsPerPage: 50,
  searchQuery: '',
  filteredRows: [],
  elapsedTimer: null,
  stepTimer: null,
};

/* ============================================================
   ROTATING WORDS (HERO)
   ============================================================ */

const ROTATE_WORDS = ['PDF', 'Invoice', 'Bank Statement', 'Spreadsheet', 'Report', 'Image'];
let rotateIdx = 0;

function initRotate() {
  const el = document.getElementById('te-rotate');
  if (!el) return;

  setInterval(() => {
    rotateIdx = (rotateIdx + 1) % ROTATE_WORDS.length;

    el.classList.add('te-rotate-out');
    setTimeout(() => {
      el.textContent = ROTATE_WORDS[rotateIdx];
      el.classList.remove('te-rotate-out');
      el.classList.add('te-rotate-in');
      requestAnimationFrame(() => {
        requestAnimationFrame(() => el.classList.remove('te-rotate-in'));
      });
    }, 220);
  }, 2200);
}

/* ============================================================
   SCREEN MANAGEMENT
   ============================================================ */

const SCREENS = ['screen-upload', 'screen-processing', 'screen-results', 'screen-error'];

function showScreen(id) {
  SCREENS.forEach(s => {
    const el = document.getElementById(s);
    if (!el) return;
    if (s === id) {
      el.classList.remove('te-hidden');
    } else {
      el.classList.add('te-hidden');
    }
  });
}

/* ============================================================
   FILE HANDLING
   ============================================================ */

const MAX_SIZE_BYTES = 200 * 1024 * 1024;
const SUPPORTED_EXTS = new Set(['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp']);
const SUPPORTED_MIME = new Set([
  'application/pdf', 'image/png', 'image/jpeg',
  'image/bmp', 'image/tiff', 'image/webp',
]);

function getExtension(filename) {
  const idx = filename.lastIndexOf('.');
  return idx >= 0 ? filename.slice(idx).toLowerCase() : '';
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateFile(file) {
  const ext = getExtension(file.name);
  if (!SUPPORTED_EXTS.has(ext)) {
    return `Unsupported file type "${ext}". Use PDF, PNG, JPEG, BMP, TIFF, or WEBP.`;
  }
  if (file.type && !SUPPORTED_MIME.has(file.type)) {
    return `Unsupported MIME type "${file.type}".`;
  }
  if (file.size > MAX_SIZE_BYTES) {
    return `File too large (${formatBytes(file.size)}). Maximum is 200 MB.`;
  }
  if (file.size === 0) {
    return 'The file is empty.';
  }
  return null;
}

function acceptFile(file) {
  const err = validateFile(file);
  if (err) { showToast(err, 'error'); return; }

  state.file = file;
  renderFilePreview(file);
  document.getElementById('te-generate-btn').disabled = false;
}

function renderFilePreview(file) {
  const ext = getExtension(file.name).replace('.', '').toUpperCase();
  const isImage = SUPPORTED_MIME.has(file.type) && file.type.startsWith('image/');

  document.getElementById('fc-name').textContent = file.name;
  document.getElementById('fc-meta').textContent = `${ext} · ${formatBytes(file.size)}`;

  const pdfIcon = document.getElementById('fc-pdf-icon');
  const imgThumb = document.getElementById('fc-img-thumb');

  if (isImage) {
    const url = URL.createObjectURL(file);
    imgThumb.src = url;
    imgThumb.onload = () => URL.revokeObjectURL(url);
    imgThumb.classList.remove('te-hidden');
    pdfIcon.classList.add('te-hidden');
  } else {
    imgThumb.classList.add('te-hidden');
    pdfIcon.classList.remove('te-hidden');
  }

  document.getElementById('dz-idle').classList.add('te-hidden');
  document.getElementById('dz-preview').classList.remove('te-hidden');
}

function clearFile() {
  state.file = null;
  document.getElementById('te-file-input').value = '';
  document.getElementById('dz-idle').classList.remove('te-hidden');
  document.getElementById('dz-preview').classList.add('te-hidden');
  document.getElementById('te-generate-btn').disabled = true;
}

/* ============================================================
   DRAG & DROP
   ============================================================ */

function initDropzone() {
  const dz = document.getElementById('te-dropzone');
  const fileInput = document.getElementById('te-file-input');
  const browseBtn = document.getElementById('dz-browse-btn');
  const replaceBtn = document.getElementById('fc-replace-btn');
  const removeBtn = document.getElementById('fc-remove-btn');

  dz.addEventListener('click', (e) => {
    if (e.target === browseBtn || e.target.closest('#dz-browse-btn')) return;
    if (e.target === replaceBtn || e.target.closest('#fc-replace-btn')) return;
    if (e.target === removeBtn || e.target.closest('#fc-remove-btn')) return;
    fileInput.click();
  });

  dz.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
  });

  browseBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
  replaceBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
  removeBtn.addEventListener('click', (e) => { e.stopPropagation(); clearFile(); });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) acceptFile(fileInput.files[0]);
  });

  dz.addEventListener('dragover', (e) => {
    e.preventDefault();
    dz.classList.add('te-dragging');
  });

  dz.addEventListener('dragleave', (e) => {
    if (!dz.contains(e.relatedTarget)) dz.classList.remove('te-dragging');
  });

  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('te-dragging');
    const file = e.dataTransfer.files[0];
    if (file) acceptFile(file);
  });
}

/* ============================================================
   CLIPBOARD PASTE
   ============================================================ */

function initClipboardPaste() {
  document.addEventListener('paste', (e) => {
    const screen = document.getElementById('screen-upload');
    if (screen.classList.contains('te-hidden')) return;

    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.kind === 'file' && item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) { acceptFile(file); break; }
      }
    }
  });
}

/* ============================================================
   FORMAT SELECT
   ============================================================ */

function initFormatSelect() {
  const select = document.getElementById('te-format-select');
  select.addEventListener('change', () => { state.outputFormat = select.value; });
}

/* ============================================================
   PROCESSING — STEPS & PROGRESS
   ============================================================ */

const STEPS_COUNT = 6;

function initProcessingUI(filename) {
  document.getElementById('proc-filename').textContent = filename;

  // Reset steps
  document.querySelectorAll('.te-step').forEach(s => {
    s.classList.remove('te-step--active', 'te-step--done');
  });

  // Reset progress
  setProgress(0);
  document.getElementById('proc-progress-label').textContent = '0%';
  document.getElementById('proc-elapsed').textContent = '0s elapsed';
}

function setProgress(pct) {
  document.getElementById('te-progress-bar').style.width = `${pct}%`;
  document.getElementById('proc-progress-label').textContent = `${Math.round(pct)}%`;
}

function activateStep(idx) {
  document.querySelectorAll('.te-step').forEach((s, i) => {
    s.classList.remove('te-step--active', 'te-step--done');
    if (i < idx) s.classList.add('te-step--done');
    if (i === idx) s.classList.add('te-step--active');
  });
  setProgress((idx / STEPS_COUNT) * 90 + 5);
}

function startElapsedTimer() {
  let secs = 0;
  const el = document.getElementById('proc-elapsed');
  clearInterval(state.elapsedTimer);
  state.elapsedTimer = setInterval(() => {
    secs++;
    el.textContent = `${secs}s elapsed`;
  }, 1000);
}

function stopElapsedTimer() {
  clearInterval(state.elapsedTimer);
  state.elapsedTimer = null;
}

// Simulates progressive step UI while the real request runs
function runStepSimulation() {
  const delays = [0, 800, 1800, 3000, 4500, 6200];
  clearTimeout(state.stepTimer);

  delays.forEach((delay, idx) => {
    state.stepTimer = setTimeout(() => activateStep(idx), delay);
  });
}

function finalizeSteps(success) {
  clearTimeout(state.stepTimer);
  stopElapsedTimer();

  document.querySelectorAll('.te-step').forEach(s => {
    s.classList.remove('te-step--active');
    if (success) s.classList.add('te-step--done');
  });

  setProgress(success ? 100 : 0);
}

/* ============================================================
   API CALL
   ============================================================ */

async function extractTables() {
  if (!state.file) return;

  const btn = document.getElementById('te-generate-btn');
  btn.disabled = true;
  btn.classList.add('te-ripple');
  setTimeout(() => btn.classList.remove('te-ripple'), 600);

  showScreen('screen-processing');
  initProcessingUI(state.file.name);
  startElapsedTimer();
  runStepSimulation();

  const formData = new FormData();
  formData.append('file', state.file);
  formData.append('output_format', state.outputFormat);

  try {
    const response = await fetch('/table-extractor/extract', {
      method: 'POST',
      body: formData,
    });

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error('The server returned an invalid response.');
    }

    if (!response.ok) {
      const msg = data?.detail || data?.error || `Server error ${response.status}.`;
      throw new Error(msg);
    }

    finalizeSteps(true);

    // Brief pause so the "100%" state is visible
    await sleep(400);

    state.result = data;
    renderResults(data);
    showScreen('screen-results');
    showToast('Tables extracted successfully', 'success');

  } catch (err) {
    finalizeSteps(false);
    await sleep(200);
    showError(err.message || 'An unexpected error occurred.');
  }
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

/* ============================================================
   RESULTS RENDERING
   ============================================================ */

function renderResults(data) {
  renderStatCards(data);
  renderTable(data);
  renderJSON(data);
  renderMetadata(data);
  renderStatsPanel(data);
}

function renderStatCards(data) {
  const stats = data.statistics || {};
  const tables = data.tables || [];

  const total_rows = tables.reduce((acc, t) => acc + (t.rows?.length ?? 1) - 1, 0);
  const total_cols = tables.reduce((acc, t) => {
    return acc + (t.headers?.length ?? 0);
    }, 0);  

  const items = [
    { label: 'Tables', value: stats.tables ?? tables.length },
    { label: 'Pages',  value: stats.pages  ?? '—' },
    { label: 'Rows',   value: total_rows },
    { label: 'Columns', value: total_cols },
    { label: 'OCR Items', value: stats.ocr_items ?? '—' },
    { label: 'Time', value: stats.processing_time != null ? `${Number(stats.processing_time).toFixed(2)}s` : '—' },
  ];

  const container = document.getElementById('te-stats-row');
  container.innerHTML = items.map((item, i) => `
    <div class="te-stat-card" style="animation-delay:${i * 50}ms">
      <span class="te-stat-card__value">${item.value}</span>
      <span class="te-stat-card__label">${item.label}</span>
    </div>
  `).join('');
}

function renderTable(data) {
  const tables = data.tables || [];
  state.currentTableIndex = 0;
  state.currentPage = 1;

  const nav = document.getElementById('te-table-nav');
  if (tables.length > 1) {
    nav.classList.remove('te-hidden');
    updateTableNavLabel(tables.length);
  } else {
    nav.classList.add('te-hidden');
  }

  renderCurrentTable(tables);
}

function updateTableNavLabel(total) {
  document.getElementById('tbl-nav-label').textContent =
    `Table ${state.currentTableIndex + 1} / ${total}`;
}

function renderCurrentTable(tables) {

    const table = tables[state.currentTableIndex];

    if (!table) {
        document.getElementById('te-table-wrap').innerHTML =
            '<div class="te-table-empty">No table data</div>';
        return;
    }

    const headers = table.headers || [];

    const bodyRows = (table.rows || [])
        .slice(1)
        .map(row =>
            (row.cells || []).map(cell => cell.text ?? '')
        );

    state.filteredRows = filterRows(bodyRows, state.searchQuery);

    renderTablePage(headers, state.filteredRows);
}

function filterRows(rows, query) {
  if (!query) return rows;
  const q = query.toLowerCase();
  return rows.filter(row => row.some(cell => String(cell ?? '').toLowerCase().includes(q)));
}

function renderTablePage(headers, rows) {
  const { currentPage, rowsPerPage } = state;
  const totalPages = Math.max(1, Math.ceil(rows.length / rowsPerPage));
  const page = Math.min(currentPage, totalPages);
  const slice = rows.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  const wrap = document.getElementById('te-table-wrap');
  const query = state.searchQuery;


  const headerHtml = headers.map(h => `<th>${escHtml(String(h ?? ''))}</th>`).join('');
  const rowsHtml = slice.map(row => {
    const cells = headers.map((_, ci) => {
      const val = String(row[ci] ?? '');
      return `<td>${highlight(escHtml(val), query)}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');

  wrap.innerHTML = `
    <table>
      <thead><tr>${headerHtml}</tr></thead>
      <tbody>${rowsHtml || '<tr><td colspan="${headers.length}" style="text-align:center;padding:24px;color:var(--text-muted)">No matching rows</td></tr>'}</tbody>
    </table>
  `;

  // Pagination
  const pg = document.getElementById('te-pagination');
  if (totalPages > 1) {
    pg.classList.remove('te-hidden');
    document.getElementById('pg-label').textContent = `Page ${page} of ${totalPages}`;
    document.getElementById('pg-prev').disabled = page <= 1;
    document.getElementById('pg-next').disabled = page >= totalPages;
  } else {
    pg.classList.add('te-hidden');
  }
}

function highlight(text, query) {
  if (!query) return text;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark class="te-highlight">$1</mark>');
}

function escHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderJSON(data) {
  document.getElementById('te-json-view').textContent = JSON.stringify(data, null, 2);
}

function renderMetadata(data) {
  const meta = data.metadata || {};
  const grid = document.getElementById('te-metadata-grid');
  grid.innerHTML = Object.entries(meta).map(([k, v]) => `
    <div class="te-kv">
      <span class="te-kv__key">${escHtml(k)}</span>
      <span class="te-kv__val">${escHtml(String(v ?? '—'))}</span>
    </div>
  `).join('');
}

function renderStatsPanel(data) {
  const stats = data.statistics || {};
  const grid = document.getElementById('te-stats-grid');
  grid.innerHTML = Object.entries(stats).map(([k, v]) => `
    <div class="te-kv">
      <span class="te-kv__key">${escHtml(k)}</span>
      <span class="te-kv__val">${escHtml(String(v ?? '—'))}</span>
    </div>
  `).join('');
}

/* ============================================================
   TABS
   ============================================================ */

function initTabs() {
  const tabs = document.querySelectorAll('.te-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('te-tab--active');
        t.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.te-tab-panel').forEach(p => p.classList.add('te-hidden'));

      tab.classList.add('te-tab--active');
      tab.setAttribute('aria-selected', 'true');
      document.getElementById(`panel-${tab.dataset.tab}`).classList.remove('te-hidden');
    });
  });
}

/* ============================================================
   TABLE NAV & PAGINATION
   ============================================================ */

function initTableControls() {
  document.getElementById('tbl-prev').addEventListener('click', () => {
    const tables = state.result?.tables || [];
    if (state.currentTableIndex > 0) {
      state.currentTableIndex--;
      state.currentPage = 1;
      updateTableNavLabel(tables.length);
      renderCurrentTable(tables);
    }
  });

  document.getElementById('tbl-next').addEventListener('click', () => {
    const tables = state.result?.tables || [];
    if (state.currentTableIndex < tables.length - 1) {
      state.currentTableIndex++;
      state.currentPage = 1;
      updateTableNavLabel(tables.length);
      renderCurrentTable(tables);
    }
  });

  document.getElementById('pg-prev').addEventListener('click', () => {
    if (state.currentPage > 1) { state.currentPage--; rerenderPage(); }
  });

  document.getElementById('pg-next').addEventListener('click', () => {
    const tables = state.result?.tables || [];
    const table = tables[state.currentTableIndex];
    const bodyRows = (table?.rows || []).slice(1);
    const totalPages = Math.ceil(bodyRows.length / state.rowsPerPage);
    if (state.currentPage < totalPages) { state.currentPage++; rerenderPage(); }
  });

  document.getElementById('te-table-search').addEventListener('input', (e) => {
    state.searchQuery = e.target.value.trim();
    state.currentPage = 1;
    const tables = state.result?.tables || [];
    renderCurrentTable(tables);
  });
}

function rerenderPage() {
  const tables = state.result?.tables || [];
  const table = tables[state.currentTableIndex];
  if (!table) return;
  const headers = table.rows?.[0] || [];
  renderTablePage(headers, state.filteredRows);
}

/* ============================================================
   EXPORT
   ============================================================ */

function initExport() {
  document.querySelectorAll('.te-export-btn').forEach(btn => {
    btn.addEventListener('click', () => handleExport(btn.dataset.action, btn));
  });
}

async function handleExport(action, btn) {
  if (!state.result) return;

  btn.classList.add('te-loading');

  try {
    switch (action) {
      case 'copy-json':
        await navigator.clipboard.writeText(JSON.stringify(state.result, null, 2));
        showToast('JSON copied to clipboard', 'success');
        break;

      case 'download-json':
        downloadBlob(
          new Blob([JSON.stringify(state.result, null, 2)], { type: 'application/json' }),
          'extracted_tables.json'
        );
        break;

      case 'download-csv':
        downloadBlob(
          new Blob([tablesToCSV(state.result.tables)], { type: 'text/csv' }),
          'extracted_tables.csv'
        );
        break;

      case 'download-html':
        downloadBlob(
          new Blob([tablesToHTML(state.result.tables)], { type: 'text/html' }),
          'extracted_tables.html'
        );
        break;

      case 'download-markdown':
        downloadBlob(
          new Blob([tablesToMarkdown(state.result.tables)], { type: 'text/markdown' }),
          'extracted_tables.md'
        );
        break;

      case 'download-excel':
        showToast('Excel export requires the server endpoint — use JSON or CSV instead.', 'info');
        break;

      default:
        break;
    }
  } catch (err) {
    showToast('Export failed. Please try again.', 'error');
    console.error(err);
  } finally {
    await sleep(300);
    btn.classList.remove('te-loading');
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function tablesToCSV(tables) {
  return (tables || []).map((table, i) => {
    const rows = table.rows || [];
    const header = i > 0 ? `\n\n# Table ${i + 1}\n` : '';
    return header + rows.map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
  }).join('');
}

function tablesToHTML(tables) {
  const body = (tables || []).map((table, i) => {
    const rows = table.rows || [];
    const [headers, ...bodyRows] = rows;
    const head = (headers || []).map(h => `<th>${escHtml(String(h ?? ''))}</th>`).join('');
    const body = bodyRows.map(r => `<tr>${r.map(c => `<td>${escHtml(String(c ?? ''))}</td>`).join('')}</tr>`).join('');
    return `<h2>Table ${i + 1}</h2><table border="1" cellpadding="6"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }).join('<br/><br/>');
  return `<!DOCTYPE html><html><body>${body}</body></html>`;
}

function tablesToMarkdown(tables) {
  return (tables || []).map((table, i) => {
    const rows = table.rows || [];
    if (!rows.length) return '';
    const [headers, ...bodyRows] = rows;
    const head = '| ' + (headers || []).map(h => String(h ?? '')).join(' | ') + ' |';
    const sep  = '| ' + (headers || []).map(() => '---').join(' | ') + ' |';
    const body = bodyRows.map(r => '| ' + r.map(c => String(c ?? '')).join(' | ') + ' |').join('\n');
    return `## Table ${i + 1}\n\n${head}\n${sep}\n${body}`;
  }).join('\n\n');
}

/* ============================================================
   ERROR SCREEN
   ============================================================ */

function showError(message) {
  const friendly = friendlyError(message);
  document.getElementById('err-title').textContent = friendly.title;
  document.getElementById('err-message').textContent = friendly.detail;
  showScreen('screen-error');
}

function friendlyError(raw) {
  const msg = String(raw || '').toLowerCase();

  if (msg.includes('413') || msg.includes('too large') || msg.includes('maximum allowed'))
    return { title: 'File too large', detail: 'Your file exceeds the 200 MB limit. Please compress or split it and try again.' };

  if (msg.includes('415') || msg.includes('unsupported') || msg.includes('extension'))
    return { title: 'Unsupported file type', detail: 'Please upload a PDF, PNG, JPEG, BMP, TIFF, or WEBP file.' };

  if (msg.includes('422') || msg.includes('unprocessable') || msg.includes('document load'))
    return { title: 'Could not read document', detail: 'The file may be corrupted, password-protected, or too complex. Try a different file.' };

  if (msg.includes('401') || msg.includes('authentication'))
    return { title: 'Session expired', detail: 'Please refresh the page and log in again.' };

  if (msg.includes('403') || msg.includes('forbidden'))
    return { title: 'Access denied', detail: 'You do not have permission to use this feature.' };

  if (msg.includes('500') || msg.includes('unexpected'))
    return { title: 'Server error', detail: 'Something went wrong on our end. Please try again in a moment.' };

  if (msg.includes('network') || msg.includes('failed to fetch'))
    return { title: 'Connection lost', detail: 'Check your internet connection and try again.' };

  return { title: 'Extraction failed', detail: raw || 'An unexpected error occurred. Please try again.' };
}

function initErrorButtons() {
  document.getElementById('err-retry-btn').addEventListener('click', () => {
    if (state.file) extractTables();
  });

  document.getElementById('err-replace-btn').addEventListener('click', resetToUpload);
}

/* ============================================================
   RESET
   ============================================================ */

function resetToUpload() {
  state.result = null;
  state.currentTableIndex = 0;
  state.currentPage = 1;
  state.searchQuery = '';
  state.filteredRows = [];
  clearFile();

  // Reset search
  const searchEl = document.getElementById('te-table-search');
  if (searchEl) searchEl.value = '';

  // Reset tabs to Table
  document.querySelectorAll('.te-tab').forEach(t => {
    t.classList.remove('te-tab--active');
    t.setAttribute('aria-selected', 'false');
  });
  document.querySelectorAll('.te-tab-panel').forEach(p => p.classList.add('te-hidden'));
  document.getElementById('tab-table')?.classList.add('te-tab--active');
  document.getElementById('tab-table')?.setAttribute('aria-selected', 'true');
  document.getElementById('panel-table')?.classList.remove('te-hidden');

  showScreen('screen-upload');
}

/* ============================================================
   GENERATE BUTTON
   ============================================================ */

function initGenerateButton() {
  document.getElementById('te-generate-btn').addEventListener('click', extractTables);
  document.getElementById('te-reset-btn').addEventListener('click', resetToUpload);
}

/* ============================================================
   TOAST NOTIFICATIONS
   ============================================================ */

function showToast(message, type = 'info') {
  const container = document.getElementById('te-toast-container');
  const toast = document.createElement('div');
  toast.className = `te-toast te-toast--${type}`;
  toast.innerHTML = `<span class="te-toast__dot"></span><span>${escHtml(message)}</span>`;
  container.appendChild(toast);

  const duration = type === 'error' ? 5000 : 3000;
  setTimeout(() => {
    toast.classList.add('te-toast--exit');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }, duration);
}

/* ============================================================
   BOOT
   ============================================================ */

function boot() {
  initRotate();
  initDropzone();
  initClipboardPaste();
  initFormatSelect();
  initTabs();
  initTableControls();
  initExport();
  initGenerateButton();
  initErrorButtons();
  showScreen('screen-upload');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}