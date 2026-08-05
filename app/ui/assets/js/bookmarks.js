'use strict';

/* ── Config ─────────────────────────────────────────────── */
const API_BASE = '';

/* ── Tool registry ──────────────────────────────────────── */
const TOOL_REGISTRY = {
  /* ── Category A: Developer Tools ── */
  'sql-generator':          { icon: 'fa-solid fa-database',              cat: 'developer', label: 'SQL Generator' },
  'sql_gen':                { icon: 'fa-solid fa-database',              cat: 'developer', label: 'SQL Generator' },
  'regex-generator':        { icon: 'fa-solid fa-code',                  cat: 'developer', label: 'Regex Generator' },
  'json-fixer':             { icon: 'fa-solid fa-file-code',             cat: 'developer', label: 'JSON Fixer' },
  'JSON-FIXER':             { icon: 'fa-solid fa-file-code',             cat: 'developer', label: 'JSON Fixer' },
  'json-formatter':         { icon: 'fa-solid fa-file-code',             cat: 'developer', label: 'JSON Formatter' },
  'mock-api':               { icon: 'fa-solid fa-plug',                  cat: 'developer', label: 'API Mock Generator' },
  'mock_api':               { icon: 'fa-solid fa-plug',                  cat: 'developer', label: 'API Mock Generator' },
  'docker':                 { icon: 'fa-brands fa-docker',               cat: 'developer', label: 'Dockerfile Generator' },
  'dockerfile-generator':   { icon: 'fa-brands fa-docker',               cat: 'developer', label: 'Dockerfile Generator' },
  'yaml':                   { icon: 'fa-solid fa-dharmachakra',          cat: 'developer', label: 'Kubernetes YAML Generator' },
  'kubernetes-yaml':        { icon: 'fa-solid fa-dharmachakra',          cat: 'developer', label: 'Kubernetes YAML Generator' },
  'commit-msg':             { icon: 'fa-solid fa-code-commit',           cat: 'developer', label: 'Commit Message Generator' },
  'code-reviewer':          { icon: 'fa-solid fa-magnifying-glass-code', cat: 'developer', label: 'Code Reviewer' },
  'code':                   { icon: 'fa-solid fa-magnifying-glass-code', cat: 'developer', label: 'Code Reviewer' },
  'error-explainer':        { icon: 'fa-solid fa-triangle-exclamation',  cat: 'developer', label: 'Error Explainer' },
  'error':                  { icon: 'fa-solid fa-triangle-exclamation',  cat: 'developer', label: 'Error Explainer' },

  /* ── Category B: Content Tools ── */
  'youtube-summarizer':     { icon: 'fa-brands fa-youtube',              cat: 'content', label: 'YouTube Summarizer' },
  'pdf-summarizer':         { icon: 'fa-solid fa-file-pdf',              cat: 'content', label: 'PDF Summarizer' },
  'article-summarizer':     { icon: 'fa-solid fa-newspaper',             cat: 'content', label: 'Article Summarizer' },
  'text-summarizer':        { icon: 'fa-solid fa-align-left',            cat: 'content', label: 'Article Summarizer' },
  'eli5':                   { icon: 'fa-solid fa-lightbulb',             cat: 'content', label: 'ELI5 Generator' },
  'quiz-generator':         { icon: 'fa-solid fa-circle-question',       cat: 'content', label: 'Quiz Generator' },
  'flashcard-generator':    { icon: 'fa-solid fa-layer-group',           cat: 'content', label: 'Flashcard Generator' },
  'blog-outline-generator': { icon: 'fa-solid fa-file-lines',            cat: 'content', label: 'Blog Outline Generator' },

  /* ── Category C: Productivity Tools ── */
  'decision-maker':         { icon: 'fa-solid fa-code-branch',           cat: 'productivity', label: 'Decision Maker' },
  'pros-cons-generator':    { icon: 'fa-solid fa-scale-balanced',        cat: 'productivity', label: 'Pros Cons Generator' },
  'pro_cons_gen':           { icon: 'fa-solid fa-scale-balanced',        cat: 'productivity', label: 'Pros Cons Generator' },
  'meeting-summarizer':     { icon: 'fa-solid fa-users',                 cat: 'productivity', label: 'Meeting Summarizer' },
  'action-item':            { icon: 'fa-solid fa-list-check',            cat: 'productivity', label: 'Action Item Extractor' },
  'action-item-extractor':  { icon: 'fa-solid fa-list-check',            cat: 'productivity', label: 'Action Item Extractor' },
  'item':                   { icon: 'fa-solid fa-list-check',            cat: 'productivity', label: 'Action Item Extractor' },
  'notes-cleaner':          { icon: 'fa-solid fa-check-to-slot',         cat: 'productivity', label: 'Note Cleaner' },
  'notes_cleaner':          { icon: 'fa-solid fa-check-to-slot',         cat: 'productivity', label: 'Note Cleaner' },
  'email-rewriter':         { icon: 'fa-solid fa-envelope',              cat: 'productivity', label: 'Email Rewriter' },
  'brainstorm-generator':   { icon: 'fa-solid fa-brain',                 cat: 'productivity', label: 'Brainstorm Generator' },

  /* ── Category D: Image Tools ── */
  'screenshot-explainer':   { icon: 'fa-regular fa-image',               cat: 'image', label: 'Screenshot Explainer' },
  'ss_explain':             { icon: 'fa-regular fa-image',               cat: 'image', label: 'Screenshot Explainer' },
  'ocr-extractor':          { icon: 'fa-solid fa-text-width',            cat: 'image', label: 'OCR Extractor' },
  'image-text-extractor':   { icon: 'fa-solid fa-text-width',            cat: 'image', label: 'Image Text Extractor' },
  'table-extractor':        { icon: 'fa-solid fa-table',                 cat: 'image', label: 'Table Extractor' },
  'table_extractor':        { icon: 'fa-solid fa-table',                 cat: 'image', label: 'Table Extractor' },
  'chart-explainer':        { icon: 'fa-solid fa-chart-line',            cat: 'image', label: 'Chart Explainer' },
};

const CAT_LABELS = {
  developer:   'Developer Tools',
  content:     'Content Tools',
  productivity: 'Productivity Tools',
  image:       'Image Tools',
};

function toolInfo(slug) {
  const key = slug?.toLowerCase?.() || '';
  for (const [k, v] of Object.entries(TOOL_REGISTRY)) {
    if (k.toLowerCase() === key) return v;
  }
  return { icon: 'fa-solid fa-wand-magic-sparkles', cat: 'other', label: null };
}

function toolCategory(slug) {
  return toolInfo(slug).cat || 'other';
}

/* ── Cookie auth ────────────────────────────────────────── */
function getCookie(name) {
  const m = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}
function authHeaders() {
  const token = getCookie('access_token') || getCookie('token') || getCookie('auth_token');
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

/* ── State ──────────────────────────────────────────────── */
const S = {
  all: [], filtered: [], sorted: [],
  search: '', toolFilter: '', catFilter: '', timeFilter: '', sort: 'newest',
  view: 'grid',
  pendingDeleteId: null, pendingCard: null,
  activeModal: null,
};

/* ── Helpers ─────────────────────────────────────────────── */
function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function fmtDate(iso) {
  if (!iso) return 'Unknown date';
  const d = new Date(iso);
  if (isNaN(d)) return 'Unknown date';
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60)    return 'Just now';
  if (diff < 3600)  return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  if (diff < 604800)return `${Math.floor(diff/86400)}d ago`;
  return d.toLocaleDateString(undefined, { month:'short', day:'numeric', year:'numeric' });
}

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

/* ── API ─────────────────────────────────────────────────── */
async function fetchBookmarks() {
  const r = await fetch(`${API_BASE}/bookmarks`, {
    credentials: 'include', headers: authHeaders(),
  });
  if (r.status === 401) throw new Error('Not authenticated. Please sign in.');
  if (!r.ok) throw new Error(`Server error (${r.status}). Please try again.`);
  return r.json();
}

async function deleteBookmark(execId) {
  const r = await fetch(`${API_BASE}/bookmarks/${encodeURIComponent(execId)}`, {
    method: 'DELETE', headers: authHeaders(),
  });
  if (r.status === 401) throw new Error('Not authenticated.');
  if (!r.ok) throw new Error(`Could not remove bookmark (${r.status}).`);
  return r.json();
}

/* ── Normalise ───────────────────────────────────────────── */
function normalise(raw) {
  if (raw && !Array.isArray(raw) && Array.isArray(raw.bookmarks)) raw = raw.bookmarks;
  if (!Array.isArray(raw)) return [];

  return raw.map(item => {
    let bm, exec, tool;
    if (Array.isArray(item)) {
      [bm, exec, tool] = item;
    } else {
      bm = item; exec = item.execution || {}; tool = item.tool || {};
    }
    const slug = tool?.slug || bm?.tool_slug || exec?.tool_slug || '';
    const name = tool?.name || bm?.tool_name || exec?.tool_name || toolInfo(slug).label || slug || 'Unknown Tool';
    const input  = bm?.user_input  || exec?.input || exec?.payload?.input || bm?.input || '';
    const output = bm?.output      || exec?.output || exec?.result        || '';
    const execAt = bm?.created_at  || exec?.created_at || bm?.executed_at || '';
    const bmAt   = bm?.created_at  || bm?.bookmarkedAt || execAt          || '';
    return {
      id:           bm?.bookmark_id  || bm?.id   || '',
      executionId:  bm?.execution_id || exec?.id  || bm?.id || '',
      bookmarkedAt: bmAt, executedAt: execAt,
      toolSlug: slug, toolName: name,
      toolCat: toolCategory(slug), input, output,
    };
  });
}

/* ════════════════════════════════════════════════════════════
   Everything that touches the DOM lives inside DOMContentLoaded
   ════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {

  const $  = id => document.getElementById(id);
  const E  = {
    grid:        $('bm-grid'),
    empty:       $('bm-empty'),
    noResults:   $('bm-no-results'),
    error:       $('bm-error'),
    errorMsg:    $('bm-error-msg'),
    statTotal:   $('stat-total'),
    statWeek:    $('stat-week'),
    statTools:   $('stat-tools'),
    statToday:   $('stat-today'),
    count:       $('bm-count'),
    search:      $('bm-search'),
    toolFilter:  $('bm-tool-filter'),
    catFilter:   $('bm-cat-filter'),
    timeFilter:  $('bm-time-filter'),
    sort:        $('bm-sort'),
    refresh:     $('bm-refresh'),
    viewGrid:    $('view-grid'),
    viewList:    $('view-list'),
    clearFilters:$('bm-clear-filters'),
    chips:       $('bm-filter-chips'),
    resetBtn:    $('bm-reset-btn'),
    modal:       $('bm-modal'),
    mIcon:       $('bm-modal-icon'),
    mTitle:      $('bm-modal-title'),
    mInput:      $('bm-modal-input'),
    mOutput:     $('bm-modal-output'),
    mMeta:       $('bm-modal-meta'),
    mClose:      $('bm-modal-close'),
    mCopy:       $('bm-modal-copy'),
    mCopyHdr:    $('bm-modal-copy-hdr'),
    mDelete:     $('bm-modal-delete'),
    mTabs:       document.querySelectorAll('.modal__tab'),
    mPaneInput:  $('modal-pane-input'),
    mPaneDivider:document.querySelector('.modal__pane-divider'),
    mPaneOutput: $('modal-pane-output'),
    confirm:     $('bm-confirm'),
    cClose:      $('bm-confirm-close'),
    cCancel:     $('bm-confirm-cancel'),
    cOk:         $('bm-confirm-ok'),
    toasts:      $('bm-toasts'),
  };

  let _modalBm = null;

  /* ── Load ──────────────────────────────────────────────── */
  async function load() {
    showSkeletons();
    try {
      const raw = await fetchBookmarks();
      S.all = normalise(raw);
      populateToolFilter();
      applyFilters();
      updateStats();
      render();
    } catch (err) {
      showError(err.message);
    }
  }

  /* ── Filter & Sort ─────────────────────────────────────── */
  function applyFilters() {
    const q    = S.search.toLowerCase().trim();
    const slug = S.toolFilter;
    const cat  = S.catFilter;
    const now  = Date.now();
    const timeMap = { today: now - 86400000, week: now - 7*86400000, month: now - 30*86400000 };
    const since = timeMap[S.timeFilter] || 0;

    S.filtered = S.all.filter(bm => {
      if (slug && bm.toolSlug !== slug) return false;
      if (cat  && bm.toolCat  !== cat)  return false;
      if (since && new Date(bm.bookmarkedAt).getTime() < since) return false;
      if (q) {
        const hay = [bm.toolName, bm.toolSlug, String(bm.input), String(bm.output)].join(' ').toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    applySort(); updateChips(); updateClearBtn();
  }

  function applySort() {
    const dir = S.sort;
    S.sorted = [...S.filtered].sort((a, b) => {
      if (dir === 'newest') return new Date(b.bookmarkedAt) - new Date(a.bookmarkedAt);
      if (dir === 'oldest') return new Date(a.bookmarkedAt) - new Date(b.bookmarkedAt);
      if (dir === 'az')     return a.toolName.localeCompare(b.toolName);
      if (dir === 'za')     return b.toolName.localeCompare(a.toolName);
      return 0;
    });
  }

  /* ── Tool filter dropdown ──────────────────────────────── */
  function populateToolFilter() {
    const slugs = [...new Set(S.all.map(b => b.toolSlug).filter(Boolean))].sort();
    Array.from(E.toolFilter.options).slice(1).forEach(o => o.remove());
    slugs.forEach(slug => {
      const opt = document.createElement('option');
      opt.value = slug;
      opt.textContent = toolInfo(slug).label || (S.all.find(b => b.toolSlug === slug)?.toolName) || slug;
      E.toolFilter.appendChild(opt);
    });
  }

  /* ── Filter chips ──────────────────────────────────────── */
  function updateChips() {
    E.chips.innerHTML = '';
    const add = (label, reset) => {
      const chip = document.createElement('span');
      chip.className = 'filter-chip';
      chip.innerHTML = `${escHtml(label)}<button aria-label="Remove filter"><i class="fa-solid fa-xmark"></i></button>`;
      chip.querySelector('button').addEventListener('click', reset);
      E.chips.appendChild(chip);
    };
    if (S.search)     add(`"${S.search}"`, () => { S.search = ''; E.search.value = ''; applyFilters(); render(); });
    if (S.toolFilter) add(E.toolFilter.options[E.toolFilter.selectedIndex]?.text || S.toolFilter,
                          () => { S.toolFilter = ''; E.toolFilter.value = ''; markActive(); applyFilters(); render(); });
    if (S.catFilter)  add(CAT_LABELS[S.catFilter] || S.catFilter,
                          () => { S.catFilter = ''; E.catFilter.value = ''; markActive(); applyFilters(); render(); });
    if (S.timeFilter) add(E.timeFilter.options[E.timeFilter.selectedIndex]?.text || S.timeFilter,
                          () => { S.timeFilter = ''; E.timeFilter.value = ''; markActive(); applyFilters(); render(); });
  }

  function updateClearBtn() {
    E.clearFilters.hidden = !(S.search || S.toolFilter || S.catFilter || S.timeFilter);
  }

  function markActive() {
    const fp = (id, val) => {
      const pill = document.getElementById(id)?.closest?.('.filter-pill');
      if (pill) pill.classList.toggle('active', !!val);
    };
    fp('bm-tool-filter', S.toolFilter);
    fp('bm-cat-filter',  S.catFilter);
    fp('bm-time-filter', S.timeFilter);
  }

  function resetAllFilters() {
    S.search = ''; E.search.value = '';
    S.toolFilter = ''; E.toolFilter.value = '';
    S.catFilter  = ''; E.catFilter.value  = '';
    S.timeFilter = ''; E.timeFilter.value = '';
    markActive(); applyFilters(); render();
  }

  /* ── Stats ─────────────────────────────────────────────── */
  function updateStats() {
    const now  = Date.now();
    const day  = now - 86400000;
    const week = now - 7 * 86400000;
    const tools    = new Set(S.all.map(b => b.toolSlug).filter(Boolean)).size;
    const thisWeek = S.all.filter(b => new Date(b.bookmarkedAt).getTime() >= week).length;
    const today    = S.all.filter(b => new Date(b.bookmarkedAt).getTime() >= day).length;
    animCount(E.statTotal, S.all.length);
    animCount(E.statWeek,  thisWeek);
    animCount(E.statTools, tools);
    animCount(E.statToday, today);
  }

  function animCount(el, target) {
    const start = parseInt(el.textContent) || 0;
    const dur = 700, step = 16, steps = Math.ceil(dur / step);
    let i = 0;
    const t = setInterval(() => {
      i++;
      el.textContent = Math.round(start + (target - start) * easeOut(i / steps));
      if (i >= steps) { el.textContent = target; clearInterval(t); }
    }, step);
  }
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

  /* ── Render ────────────────────────────────────────────── */
  function render() {
    clearGrid();
    const count = S.sorted.length;
    E.count.textContent = count === 1 ? '1 bookmark' : `${count} bookmarks`;
    if (S.all.length === 0) { E.empty.hidden = false; return; }
    const filtersActive = S.search || S.toolFilter || S.catFilter || S.timeFilter;
    if (count === 0 && filtersActive) { E.noResults.hidden = false; return; }
    S.sorted.forEach((bm, i) => {
      const card = buildCard(bm);
      E.grid.appendChild(card);
      requestAnimationFrame(() => setTimeout(() => card.classList.add('visible'), i * 40));
    });
  }

  function clearGrid() {
    Array.from(E.grid.querySelectorAll('.bm-card')).forEach(c => c.remove());
    E.empty.hidden = true; E.noResults.hidden = true; E.error.hidden = true;
  }

  /* ── Skeleton ──────────────────────────────────────────── */
  function showSkeletons() {
    clearGrid();
    for (let i = 0; i < 6; i++) {
      const sk = document.createElement('div');
      sk.className = 'bm-skeleton';
      sk.setAttribute('aria-hidden', 'true');
      sk.innerHTML = `
        <div class="sk-header"><div class="sk sk-icon"></div><div class="sk sk-title"></div></div>
        <div class="sk sk-line w${['90','80','70','60','50'][i%5]}"></div>
        <div class="sk sk-line w${['60','75','55','80','65'][i%5]}"></div>
        <div class="sk sk-line w${['70','50','90','60','85'][i%5]}"></div>
        <div class="sk-actions"><div class="sk sk-btn"></div><div class="sk sk-btn"></div><div class="sk sk-btn"></div></div>`;
      E.grid.appendChild(sk);
    }
  }

  function hideSkeletons() {
    E.grid.querySelectorAll('.bm-skeleton').forEach(s => s.remove());
  }

  function showError(msg) {
    hideSkeletons();
    E.error.hidden = false;
    E.errorMsg.textContent = msg || 'Unable to load bookmarks.';
  }

  /* ── Build card ────────────────────────────────────────── */
  function buildCard(bm) {
    const info   = toolInfo(bm.toolSlug);
    const catCls = `cat--${bm.toolCat}`;
    const catLbl = CAT_LABELS[bm.toolCat] || 'Other';
    const input  = String(bm.input  || '').trim() || '(no input)';
    const output = String(bm.output || '').trim() || '(no output)';
    const date   = fmtDate(bm.bookmarkedAt);

    const card = document.createElement('article');
    card.className = 'bm-card';
    card.dataset.executionId = bm.executionId;
    card.dataset.id = bm.id;
    card.setAttribute('aria-label', `Bookmark: ${bm.toolName}`);
    card.innerHTML = `
      <div class="bm-card__head">
        <div class="bm-card__identity">
          <div class="bm-card__icon" aria-hidden="true"><i class="${info.icon}"></i></div>
          <div class="bm-card__meta">
            <div class="bm-card__tool">${escHtml(bm.toolName)}</div>
            <div class="bm-card__time"><i class="fa-regular fa-clock"></i>${escHtml(date)}</div>
          </div>
        </div>
        <div class="bm-card__star" aria-hidden="true"><i class="fa-solid fa-star"></i></div>
      </div>
      <div class="bm-card__category ${catCls}" aria-label="Category: ${catLbl}">${escHtml(catLbl)}</div>
      <div class="bm-card__previews">
        <div class="bm-card__preview">
          <div class="bm-card__preview-lbl"><i class="fa-solid fa-arrow-right-to-bracket"></i>Input</div>
          <div class="bm-card__preview-txt">${escHtml(input)}</div>
        </div>
        <div class="bm-card__preview">
          <div class="bm-card__preview-lbl"><i class="fa-solid fa-arrow-right-from-bracket"></i>Output</div>
          <div class="bm-card__preview-txt">${escHtml(output)}</div>
        </div>
      </div>
      <div class="bm-card__actions">
        <button class="card-btn card-btn--open" data-action="open"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open</button>
        <button class="card-btn" data-action="copy"><i class="fa-regular fa-copy"></i> Copy</button>
        <button class="card-btn card-btn--del" data-action="delete"><i class="fa-regular fa-trash-can"></i> Remove</button>
      </div>`;

    card.addEventListener('click', e => {
      const btn = e.target.closest('[data-action]');
      if (!btn) return;
      const a = btn.dataset.action;
      if (a === 'open')   openModal(bm);
      if (a === 'copy')   copyText(String(bm.output || '').trim(), btn);
      if (a === 'delete') promptDelete(bm.executionId, card);
    });
    return card;
  }

  /* ── Modal ─────────────────────────────────────────────── */
  function openModal(bm) {
    _modalBm = bm;
    const info = toolInfo(bm.toolSlug);
    E.mIcon.innerHTML     = `<i class="${info.icon}"></i>`;
    E.mTitle.textContent  = bm.toolName;
    E.mInput.textContent  = String(bm.input  || '(no input)').trim();
    E.mOutput.textContent = String(bm.output || '(no output)').trim();
    E.mMeta.textContent   = `Bookmarked ${fmtDate(bm.bookmarkedAt)}`;
    switchTab('both');
    E.modal.classList.add('open');
    E.modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    E.mClose.focus();
  }

  function closeModal() {
    E.modal.classList.remove('open');
    E.modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  function switchTab(tab) {
    E.mTabs.forEach(t => {
      const active = t.dataset.tab === tab;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active);
    });
    E.mPaneInput.hidden   = tab === 'output';
    E.mPaneDivider.hidden = tab !== 'both';
    E.mPaneOutput.hidden  = tab === 'input';
  }

  /* ── Delete flow ───────────────────────────────────────── */
  function promptDelete(execId, cardEl) {
    S.pendingDeleteId = execId;
    S.pendingCard     = cardEl;
    E.confirm.classList.add('open');
    E.confirm.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    E.cOk.focus();
  }

  function closeConfirm() {
    E.confirm.classList.remove('open');
    E.confirm.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  async function confirmDelete() {
    const execId = S.pendingDeleteId;
    const card   = S.pendingCard;
    closeConfirm();
    if (!execId) return;
    try {
      await deleteBookmark(execId);
      if (card) {
        card.classList.add('collapsing');
        card.addEventListener('animationend', () => card.remove(), { once: true });
      }
      S.all = S.all.filter(b => b.executionId !== execId);
      applyFilters(); updateStats();
      const c = S.sorted.length;
      E.count.textContent = c === 1 ? '1 bookmark' : `${c} bookmarks`;
      if (S.all.length === 0) setTimeout(() => { E.empty.hidden = false; }, 420);
      toast('Bookmark removed', 'success');
    } catch (err) {
      toast(err.message || 'Could not remove bookmark.', 'error');
    }
  }

  /* ── Copy ──────────────────────────────────────────────── */
  function copyText(text, btn) {
    if (!text || text === '(no output)') { toast('Nothing to copy.', 'info'); return; }
    navigator.clipboard.writeText(text)
      .then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.innerHTML = orig; btn.classList.remove('copied'); }, 1800);
        toast('Copied to clipboard', 'success');
      })
      .catch(() => toast('Clipboard access denied.', 'error'));
  }

  /* ── Toast ─────────────────────────────────────────────── */
  function toast(msg, type = 'info') {
    const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.innerHTML = `<i class="fa-solid ${icons[type]} toast__icon"></i><span>${escHtml(msg)}</span>`;
    E.toasts.appendChild(el);
    setTimeout(() => {
      el.classList.add('out');
      el.addEventListener('animationend', () => el.remove(), { once: true });
    }, 3200);
  }

  /* ── Events ────────────────────────────────────────────── */
  E.search.addEventListener('input', debounce(ev => { S.search = ev.target.value; applyFilters(); render(); }, 180));

  E.toolFilter.addEventListener('change', ev => {
    S.toolFilter = ev.target.value;
    ev.target.closest('.filter-pill').classList.toggle('active', !!S.toolFilter);
    applyFilters(); render();
  });
  E.catFilter.addEventListener('change', ev => {
    S.catFilter = ev.target.value;
    ev.target.closest('.filter-pill').classList.toggle('active', !!S.catFilter);
    applyFilters(); render();
  });
  E.timeFilter.addEventListener('change', ev => {
    S.timeFilter = ev.target.value;
    ev.target.closest('.filter-pill').classList.toggle('active', !!S.timeFilter);
    applyFilters(); render();
  });
  E.sort.addEventListener('change', ev => { S.sort = ev.target.value; applySort(); render(); });

  E.clearFilters.addEventListener('click', resetAllFilters);
  E.resetBtn.addEventListener('click', resetAllFilters);

  E.refresh.addEventListener('click', () => {
    E.refresh.classList.add('spinning');
    load().finally(() => { hideSkeletons(); E.refresh.classList.remove('spinning'); });
  });

  $('bm-retry').addEventListener('click', () => load().finally(hideSkeletons));

  E.viewGrid.addEventListener('click', () => {
    S.view = 'grid'; E.grid.classList.remove('list-view');
    E.viewGrid.classList.add('active'); E.viewList.classList.remove('active');
  });
  E.viewList.addEventListener('click', () => {
    S.view = 'list'; E.grid.classList.add('list-view');
    E.viewList.classList.add('active'); E.viewGrid.classList.remove('active');
  });

  E.mClose.addEventListener('click', closeModal);
  E.mCopy.addEventListener('click', () => copyText(String(_modalBm?.output || '').trim(), E.mCopy));
  E.mCopyHdr.addEventListener('click', () => copyText(String(_modalBm?.output || '').trim(), E.mCopyHdr));
  E.mDelete.addEventListener('click', () => {
    closeModal();
    const card = document.querySelector(`[data-execution-id="${_modalBm?.executionId}"]`);
    promptDelete(_modalBm?.executionId, card);
  });
  E.modal.addEventListener('click', ev => { if (ev.target === E.modal) closeModal(); });

  E.mTabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

  E.cClose.addEventListener('click', closeConfirm);
  E.cCancel.addEventListener('click', closeConfirm);
  E.cOk.addEventListener('click', confirmDelete);
  E.confirm.addEventListener('click', ev => { if (ev.target === E.confirm) closeConfirm(); });

  document.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') { closeModal(); closeConfirm(); }
    if ((ev.metaKey || ev.ctrlKey) && ev.key === 'k') { ev.preventDefault(); E.search.focus(); }
  });

  /* ── Boot ──────────────────────────────────────────────── */
  const params = new URLSearchParams(window.location.search);
  const toolParam = params.get('tool') || '';
  if (toolParam) {
    E.toolFilter.value = toolParam;
    S.toolFilter = toolParam;
    E.toolFilter.closest?.('.filter-pill')?.classList.add('active');
  }
  load().finally(hideSkeletons);

  window.BookmarksPage = { reload: () => load().finally(hideSkeletons), toast };

}); // end DOMContentLoaded