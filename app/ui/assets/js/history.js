/* =========================================================
   SANDBOX — HISTORY LOGIC
   Wired to the live /history/ API. All UI states (skeleton,
   empty, error, no-results) are handled explicitly.
   ========================================================= */

(() => {
  'use strict';

  /* ---------- tool icon/color registry (fallback only —
     a real tool_icon URL from the API always wins) ---------- */
  const TOOL_STYLES = {
    'Quiz Generator':      { icon:'❓',  bg:'rgba(124,140,255,0.14)', fg:'#98a4ff' },
    'SQL Generator':       { icon:'▤',  bg:'rgba(52,208,182,0.14)',  fg:'#34d0b6' },
    'JSON Fixer':          { icon:'{ }', bg:'rgba(242,184,102,0.14)', fg:'#f2b866' },
    'Regex Generator':     { icon:'/.*/',bg:'rgba(210,155,255,0.14)', fg:'#d29bff' },
    'Blog Generator':      { icon:'✎',  bg:'rgba(124,140,255,0.14)', fg:'#98a4ff' },
    'Decision Maker':      { icon:'⚖',  bg:'rgba(255,140,140,0.14)', fg:'#ff8f8f' },
    'OCR':                 { icon:'▣',  bg:'rgba(52,208,182,0.14)',  fg:'#34d0b6' },
    'Table Extractor':     { icon:'▦',  bg:'rgba(242,184,102,0.14)', fg:'#f2b866' },
    'Email Rewriter':      { icon:'✉',  bg:'rgba(124,140,255,0.14)', fg:'#98a4ff' },
    'Flashcard Generator': { icon:'▮▮', bg:'rgba(210,155,255,0.14)', fg:'#d29bff' },
    'Screenshot Explainer':{ icon:'▢',  bg:'rgba(52,208,182,0.14)',  fg:'#34d0b6' },
  };
  const DEFAULT_STYLE = { icon:'✦', bg:'rgba(124,140,255,0.14)', fg:'#98a4ff' };

  function styleFor(toolName){ return TOOL_STYLES[toolName] || DEFAULT_STYLE; }

  /* ---------- API helpers ---------- */
  async function fetchHistory() {
    const res = await fetch('/history/', { credentials:'include' });
    if (!res.ok) throw new Error(`Request failed (${res.status})`);
    const data = await res.json();
    if (!data.success) throw new Error('The server could not load your history.');
    return data.history; // array of { title, items: [...] }
  }

  async function fetchHistoryDetail(executionId) {
    const res = await fetch(`/history/${executionId}`, { credentials:'include' });
    if (!res.ok) throw new Error(`Request failed (${res.status})`);
    const data = await res.json();
    if (!data.success) throw new Error(data.message || "That entry couldn't be opened.");
    return data.history;
  }

  async function deleteHistoryRequest(executionId) {
    const res = await fetch(`/history/${executionId}`, { method:'DELETE', credentials:'include' });
    if (!res.ok) throw new Error(`Request failed (${res.status})`);
    const data = await res.json();
    if (!data.success) throw new Error(data.message || 'Unable to delete history.');
    return data;
  }

  /* ---------- formatting helpers ---------- */
  function previewFromInput(userInput) {
    if (!userInput) return 'No input recorded';
    let text = userInput;
    try {
      const parsed = JSON.parse(userInput);
      if (parsed && typeof parsed === 'object') {
        const values = Object.values(parsed);
        text = parsed.filename || parsed.query || parsed.prompt || parsed.text || values[0] || userInput;
      }
    } catch { /* not JSON — use as-is */ }
    text = String(text).trim();
    return text.length > 90 ? text.slice(0, 90) + '…' : (text || 'No input recorded');
  }

  function fmtCardTime(iso, bucketTitle) {
    try {
      const date = new Date(iso);
      if (bucketTitle === 'Today' || bucketTitle === 'Yesterday') {
        return date.toLocaleTimeString(undefined, { hour:'numeric', minute:'2-digit' }).toLowerCase();
      }
      return date.toLocaleDateString(undefined, { month:'short', day:'numeric' });
    } catch { return ''; }
  }

  function fmtFullDate(iso) {
    try {
      const date = new Date(iso);
      return date.toLocaleString(undefined, { day:'numeric', month:'short', year:'numeric', hour:'numeric', minute:'2-digit' });
    } catch { return iso || '—'; }
  }

  function escapeHtml(str){
    const div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
  }

  function highlightJSON(str){
    if (str == null) return '';
    let escaped = escapeHtml(str);
    escaped = escaped.replace(/(&quot;[^&]*?&quot;)(\s*:)/g, '<span class="tok-key">$1</span>$2');
    escaped = escaped.replace(/:\s*(&quot;.*?&quot;)/g, ': <span class="tok-str">$1</span>');
    escaped = escaped.replace(/:\s*(-?\d+\.?\d*)/g, ': <span class="tok-num">$1</span>');
    escaped = escaped.replace(/\b(true|false|null)\b/g, '<span class="tok-bool">$1</span>');
    return escaped;
  }

  /* ---------- state ---------- */
  let sections = null;   // raw grouped history from the API: [{ title, items:[...] }]
  let status = 'loading'; // loading | ready | error
  let errorMessage = '';
  let searchQuery = '';
  let pendingDeleteId = null;

  /* ---------- DOM refs ---------- */
  const timelineEl = document.getElementById('timeline');
  const emptyEl = document.getElementById('emptyState');
  const searchInput = document.getElementById('searchInput');

  const filterBtn = document.getElementById('filterBtn');
  const sortBtn = document.getElementById('sortBtn');
  const filterMenu = document.getElementById('filterMenu');
  const sortMenu = document.getElementById('sortMenu');
  const filterLabel = document.getElementById('filterLabel');
  const sortLabel = document.getElementById('sortLabel');
  const resultCount = document.getElementById('resultCount');
  // Sort/filter operate client-side on top of whatever grouping the API
  // returns; "tool" filter options are populated dynamically once data loads.
  let filterTool = 'all';
  let sortMode = 'newest';

  const modalRoot = document.getElementById('modalRoot');
  const modalOverlay = document.getElementById('modalOverlay');
  const modal = document.getElementById('modal');
  const modalClose = document.getElementById('modalClose');
  const modalIcon = document.getElementById('modalIcon');
  const modalTitle = document.getElementById('modalTitle');
  const modalDateText = document.getElementById('modalDateText');
  const modalTabs = document.getElementById('modalTabs');
  const tabIndicator = document.getElementById('tabIndicator');
  const panelInput = document.querySelector('#panelInput code');
  const panelOutput = document.querySelector('#panelOutput code');
  const panelMeta = document.getElementById('panelMeta');

  const copyBtn = document.getElementById('copyBtn');
  const bookmarkBtn = document.getElementById('bookmarkBtn');
  const deleteBtn = document.getElementById('deleteBtn');

  const confirmRoot = document.getElementById('confirmRoot');
  const confirmOverlay = document.getElementById('confirmOverlay');
  const confirmCancel = document.getElementById('confirmCancel');
  const confirmDelete = document.getElementById('confirmDelete');

  const toastEl = document.getElementById('toast');

  // TRUE PORTAL: physically move both dropdown menus to be direct children
  // of <body>. This is the actual fix for "renders on top but still not
  // clickable" — position:fixed only anchors to the real viewport if NO
  // ancestor has a transform/filter/perspective/contain/will-change. Inside
  // a NiceGUI/Quasar page shell there is almost always such a wrapper
  // somewhere up the tree, which silently turns "fixed" back into
  // "contained/absolute-like" and desyncs the click hit-area from what's
  // painted. Reparenting to <body> removes every ancestor, so there is
  // nothing left that can ever trap it again. Event listeners already
  // bound to these elements survive the move (same DOM node, same object).
  if (filterMenu.parentElement !== document.body) document.body.appendChild(filterMenu);
  if (sortMenu.parentElement !== document.body) document.body.appendChild(sortMenu);

  let activeExecutionId = null;
  let detailRequestToken = 0; // guards against stale responses from fast clicking

  function toast(msg){
    toastEl.textContent = msg;
    toastEl.classList.add('is-visible');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => toastEl.classList.remove('is-visible'), 2200);
  }

  function iconMarkup(item){
    const style = styleFor(item.tool_name);
    if (item.tool_icon){
      return `<img src="${escapeHtml(item.tool_icon)}" alt="" onerror="this.remove()" style="width:22px;height:22px;object-fit:contain;" />`;
    }
    return style.icon;
  }

  /* ---------- filtering / sorting (client-side, on top of API grouping) ---------- */
  function getFilteredSections(){
    if (!sections) return [];
    const q = searchQuery.trim().toLowerCase();

    let out = sections.map(section => ({
      title: section.title,
      items: section.items.filter(item => {
        const matchesTool = filterTool === 'all' || item.tool_name === filterTool;
        const haystack = `${item.tool_name} ${previewFromInput(item.user_input)}`.toLowerCase();
        const matchesQuery = !q || haystack.includes(q);
        return matchesTool && matchesQuery;
      })
    })).filter(section => section.items.length > 0);

    if (sortMode === 'az'){
      out = out.map(s => ({ ...s, items:[...s.items].sort((a,b) => a.tool_name.localeCompare(b.tool_name)) }));
    } else if (sortMode === 'oldest'){
      out = out.map(s => ({ ...s, items:[...s.items].sort((a,b) => new Date(a.created_at) - new Date(b.created_at)) })).reverse();
    }
    // 'newest' relies on the API's own ordering/grouping.

    return out;
  }

  function allToolNames(){
    if (!sections) return [];
    const names = new Set();
    sections.forEach(s => s.items.forEach(i => names.add(i.tool_name)));
    return [...names].sort();
  }

  function populateFilterMenu(){
    const names = allToolNames();
    filterMenu.innerHTML = [
      `<button class="dropdown__item ${filterTool === 'all' ? 'is-active' : ''}" data-filter="all">All tools</button>`,
      ...names.map(n => `<button class="dropdown__item ${filterTool === n ? 'is-active' : ''}" data-filter="${escapeHtml(n)}">${escapeHtml(n)}</button>`)
    ].join('');
  }

  /* ---------- card / section markup ---------- */
  function cardHTML(item, bucketTitle){
    const style = styleFor(item.tool_name);
    return `
      <article class="card" data-execution-id="${escapeHtml(item.execution_id)}" tabindex="0" style="--icon-bg:${style.bg};--icon-fg:${style.fg}">
        <div class="card__icon">${iconMarkup(item)}</div>
        <div class="card__main">
          <div class="card__top">
            <span class="card__name">${escapeHtml(item.tool_name)}</span>
          </div>
          <div class="card__preview">${escapeHtml(previewFromInput(item.user_input))}</div>
        </div>
        <div class="card__meta">
          <span class="card__time">${fmtCardTime(item.created_at, bucketTitle)}</span>
          <svg class="card__chevron" width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M9 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
      </article>`;
  }

  /* ---------- top-level render states ---------- */
  function renderSkeleton(){
    emptyEl.hidden = true;
    timelineEl.style.display = '';
    const section = () => `
      <div class="section">
        <div class="section__label">Loading</div>
        <div class="section__list">
          <div class="skeleton"></div>
          <div class="skeleton"></div>
          <div class="skeleton"></div>
        </div>
      </div>`;
    timelineEl.innerHTML = section() + section();
  }

  function renderErrorState(message){
    emptyEl.hidden = true;
    timelineEl.style.display = '';
    timelineEl.innerHTML = `
      <div class="empty">
        <div class="empty__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><polyline points="1 4 1 10 7 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <h2>Unable to load history</h2>
        <p>${escapeHtml(message || "Something went wrong while fetching your activity.")}</p>
        <button class="btn btn--ghost" id="retryBtn">Retry</button>
      </div>`;
    document.getElementById('retryBtn').addEventListener('click', loadHistory);
  }

  function renderNoResults(){
    emptyEl.hidden = true;
    timelineEl.style.display = '';
    timelineEl.innerHTML = `
      <div class="empty">
        <div class="empty__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="1.6"/><path d="M21 21l-4.35-4.35" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        </div>
        <h2>No results</h2>
        <p>Nothing matches "${escapeHtml(searchQuery)}". Try a different search or filter.</p>
      </div>`;
  }

  function render(){
    if (status === 'loading'){ resultCount.hidden = true; renderSkeleton(); return; }
    if (status === 'error'){ resultCount.hidden = true; renderErrorState(errorMessage); return; }

    const totalItems = (sections || []).reduce((n, s) => n + s.items.length, 0);
    if (totalItems === 0){
      resultCount.hidden = true;
      timelineEl.style.display = 'none';
      timelineEl.innerHTML = '';
      emptyEl.hidden = false;
      return;
    }

    const filtered = getFilteredSections();
    const visibleItems = filtered.reduce((n, s) => n + s.items.length, 0);

    // Show a count whenever a filter or search is active, so selecting a
    // filter always gives visible confirmation — even when it happens to
    // match the same items already on screen.
    const filterActive = filterTool !== 'all' || searchQuery.trim().length > 0;
    if (filterActive){
      resultCount.hidden = false;
      resultCount.innerHTML = `Showing <strong>${visibleItems}</strong> of <strong>${totalItems}</strong>${filterTool !== 'all' ? ` for <strong>${escapeHtml(filterTool)}</strong>` : ''}`;
    } else {
      resultCount.hidden = true;
    }

    emptyEl.hidden = true;
    timelineEl.style.display = '';

    if (visibleItems === 0){ renderNoResults(); return; }

    timelineEl.innerHTML = filtered.map(section => `
      <section class="section">
        <div class="section__label">${escapeHtml(section.title)}</div>
        <div class="section__list">
          ${section.items.map(item => cardHTML(item, section.title)).join('')}
        </div>
      </section>
    `).join('');

    timelineEl.querySelectorAll('.card').forEach((el, i) => {
      el.style.animationDelay = `${Math.min(i * 45, 400)}ms`;
    });

    bindCardEvents();
  }

  function bindCardEvents(){
    timelineEl.querySelectorAll('.card').forEach(card => {
      card.addEventListener('click', () => openModal(card.dataset.executionId));
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); openModal(card.dataset.executionId); }
      });
    });
  }

  /* ---------- loading the list ---------- */
  function loadHistory(){
    status = 'loading';
    render();
    fetchHistory()
      .then(history => {
        sections = history;
        status = 'ready';
        populateFilterMenu();
        render();
      })
      .catch(err => {
        console.error('History load failed:', err);
        status = 'error';
        errorMessage = err.message;
        render();
      });
  }

  /* ---------- modal (fetches full detail on open) ---------- */
  function openModal(executionId){
    activeExecutionId = executionId;

    modalTitle.textContent = 'Loading…';
    modalIcon.textContent = '✦';
    modalIcon.style.removeProperty('--icon-bg');
    modalIcon.style.removeProperty('--icon-fg');
    modalDateText.textContent = '—';
    panelInput.innerHTML = '';
    panelOutput.innerHTML = '';
    panelMeta.innerHTML = '';
    setActiveTab('input');

    modalRoot.classList.add('is-open');
    modalRoot.setAttribute('aria-hidden','false');
    document.body.style.overflow = 'hidden';
    modal.focus();

    const token = ++detailRequestToken;
    fetchHistoryDetail(executionId)
      .then(detail => {
        if (token !== detailRequestToken) return; // superseded by a newer click
        renderModalDetail(detail);
      })
      .catch(err => {
        if (token !== detailRequestToken) return;
        panelInput.innerHTML = `<span style="color:var(--danger)">${escapeHtml(err.message)}</span>`;
        modalTitle.textContent = 'Unable to load';
      });
  }

  function renderModalDetail(detail){
    const toolName = detail.tool?.name || 'Execution';
    const style = styleFor(toolName);

    if (detail.tool?.icon){
      modalIcon.innerHTML = `<img src="${escapeHtml(detail.tool.icon)}" alt="" style="width:22px;height:22px;object-fit:contain;" onerror="this.remove()" />`;
    } else {
      modalIcon.textContent = style.icon;
    }
    modalIcon.style.setProperty('--icon-bg', style.bg);
    modalIcon.style.setProperty('--icon-fg', style.fg);

    modalTitle.textContent = toolName;
    modalDateText.textContent = detail.created_at ? fmtFullDate(detail.created_at) : '—';

    panelInput.innerHTML = highlightJSON(detail.user_input) || '<span style="color:var(--text-muted)">No input recorded</span>';
    panelOutput.innerHTML = highlightJSON(detail.output) || '<span style="color:var(--text-muted)">No output recorded</span>';

    // Metadata: surface any additional fields the API returns beyond the
    // core input/output/tool/created_at, so this stays useful whatever
    // the backend adds later without needing a UI change.
    const known = new Set(['tool','user_input','output','created_at','execution_id']);
    const metaEntries = Object.entries(detail).filter(([k]) => !known.has(k));
    if (metaEntries.length){
      panelMeta.innerHTML = metaEntries.map(([k,v]) => `
        <div class="meta-item">
          <div class="meta-item__label">${escapeHtml(k.replace(/_/g,' '))}</div>
          <div class="meta-item__value">${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : v)}</div>
        </div>`).join('');
    } else {
      panelMeta.innerHTML = `<div style="color:var(--text-muted);font-size:13.5px;">No metadata available for this execution.</div>`;
    }
  }

  function closeModal(){
    modalRoot.classList.remove('is-open');
    modalRoot.setAttribute('aria-hidden','true');
    document.body.style.overflow = '';
    activeExecutionId = null;
  }

  function setActiveTab(tab){
    modalTabs.querySelectorAll('.modal__tab').forEach(t => t.classList.toggle('is-active', t.dataset.tab === tab));
    document.querySelectorAll('.modal__panel').forEach(p => p.classList.toggle('is-active', p.dataset.panel === tab));
    positionTabIndicator();
  }

  function positionTabIndicator(){
    const activeTab = modalTabs.querySelector('.modal__tab.is-active');
    if (!activeTab) return;
    tabIndicator.style.width = activeTab.offsetWidth + 'px';
    tabIndicator.style.left = activeTab.offsetLeft + 'px';
  }

  modalTabs.addEventListener('click', (e) => {
    const btn = e.target.closest('.modal__tab');
    if (!btn) return;
    setActiveTab(btn.dataset.tab);
  });

  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape'){
      if (confirmRoot.classList.contains('is-open')) closeConfirm();
      else if (modalRoot.classList.contains('is-open')) closeModal();
    }
  });

  window.addEventListener('resize', () => {
    if (modalRoot.classList.contains('is-open')) positionTabIndicator();
  });

  /* ---------- copy / bookmark ---------- */
  copyBtn.addEventListener('click', () => {
    const activePanel = document.querySelector('.modal__panel.is-active').dataset.panel;
    const source = activePanel === 'output' ? panelOutput : panelInput;
    const text = source.textContent || '';
    if (!text || !navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(() => {
      copyBtn.classList.add('is-success');
      copyBtn.querySelector('span').textContent = 'Copied';
      setTimeout(() => {
        copyBtn.classList.remove('is-success');
        copyBtn.querySelector('span').textContent = 'Copy';
      }, 1600);
    }).catch(() => {});
  });

  bookmarkBtn.addEventListener('click', () => {
    // No bookmark endpoint yet — UI-only toggle until the API exists.
    bookmarkBtn.classList.toggle('is-success');
    const saved = bookmarkBtn.classList.contains('is-success');
    bookmarkBtn.querySelector('span').textContent = saved ? 'Saved' : 'Save';
    toast(saved ? 'Saved to bookmarks' : 'Removed from bookmarks');
  });

  /* ---------- delete flow (premium confirm dialog, not window.confirm) ---------- */
  deleteBtn.addEventListener('click', () => openConfirm(activeExecutionId));

  function openConfirm(id){
    if (!id) return;
    pendingDeleteId = id;
    confirmDelete.disabled = false;
    confirmDelete.textContent = 'Delete';
    confirmRoot.classList.add('is-open');
    confirmRoot.setAttribute('aria-hidden','false');
  }
  function closeConfirm(){
    confirmRoot.classList.remove('is-open');
    confirmRoot.setAttribute('aria-hidden','true');
    pendingDeleteId = null;
  }
  confirmCancel.addEventListener('click', closeConfirm);
  confirmOverlay.addEventListener('click', closeConfirm);

  confirmDelete.addEventListener('click', async () => {
    const id = pendingDeleteId;
    if (!id) return;

    confirmDelete.disabled = true;
    confirmDelete.textContent = 'Deleting…';

    try {
      await deleteHistoryRequest(id);
      closeConfirm();
      closeModal();

      const cardEl = timelineEl.querySelector(`.card[data-execution-id="${id}"]`);
      if (cardEl){
        cardEl.classList.add('is-removing');
        cardEl.addEventListener('animationend', () => {
          removeFromLocalState(id);
          render();
          toast('History entry deleted');
        }, { once:true });
      } else {
        removeFromLocalState(id);
        render();
        toast('History entry deleted');
      }
    } catch (err) {
      confirmDelete.disabled = false;
      confirmDelete.textContent = 'Delete';
      toast(err.message || 'Unable to delete history.');
    }
  });

  function removeFromLocalState(id){
    if (!sections) return;
    sections = sections
      .map(s => ({ ...s, items: s.items.filter(i => i.execution_id !== id) }))
      .filter(s => s.items.length > 0);
  }

  /* ---------- search ---------- */
  let searchDebounce;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      searchQuery = e.target.value;
      render();
    }, 120);
  });

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k'){
      e.preventDefault();
      searchInput.focus();
    }
  });

  /* ---------- filter / sort dropdowns ----------
     .dropdown is `position:fixed` in CSS (see history.css). Because a
     fixed element is positioned against the viewport, not its DOM parent,
     we compute its top/left here from the trigger button's own
     getBoundingClientRect() every time it opens. This is what actually
     keeps it out of the timeline's stacking context permanently — no
     ancestor animation, filter, or z-index change can trap it again. */
  function positionDropdown(menuEl, btnEl){
    const rect = btnEl.getBoundingClientRect();
    menuEl.style.top = `${rect.bottom + 8}px`;
    if (menuEl.classList.contains('dropdown--right')){
      menuEl.style.left = 'auto';
      menuEl.style.right = `${window.innerWidth - rect.right}px`;
    } else {
      menuEl.style.left = `${rect.left}px`;
      menuEl.style.right = 'auto';
    }
  }

  function closeAllMenus(){
    document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('is-open'));
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('is-open'));
  }

  function toggleMenu(menuEl, btnEl, open){
    const isOpen = open ?? !menuEl.classList.contains('is-open');
    closeAllMenus();
    if (isOpen){
      positionDropdown(menuEl, btnEl);
      menuEl.classList.add('is-open');
      btnEl.classList.add('is-open');
    }
  }

  filterBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleMenu(filterMenu, filterBtn); });
  sortBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleMenu(sortMenu, sortBtn); });

  document.addEventListener('click', closeAllMenus);

  // Fixed-position menus don't move with the trigger on scroll/resize —
  // close them in that case rather than let them drift out of alignment.
  window.addEventListener('scroll', () => {
    if (filterMenu.classList.contains('is-open') || sortMenu.classList.contains('is-open')) closeAllMenus();
  }, { passive:true, capture:true });
  window.addEventListener('resize', closeAllMenus);

  filterMenu.addEventListener('click', (e) => {
    const item = e.target.closest('.dropdown__item');
    if (!item) return;
    e.stopPropagation();
    filterTool = item.dataset.filter;
    filterLabel.textContent = filterTool === 'all' ? 'All tools' : filterTool;
    filterMenu.querySelectorAll('.dropdown__item').forEach(i => i.classList.toggle('is-active', i === item));
    toggleMenu(filterMenu, filterBtn, false);
    render();
  });

  sortMenu.addEventListener('click', (e) => {
    const item = e.target.closest('.dropdown__item');
    if (!item) return;
    e.stopPropagation();
    sortMode = item.dataset.sort;
    sortLabel.textContent = item.textContent;
    sortMenu.querySelectorAll('.dropdown__item').forEach(i => i.classList.toggle('is-active', i === item));
    toggleMenu(sortMenu, sortBtn, false);
    render();
  });

  /* ---------- init ---------- */
  loadHistory();

})();