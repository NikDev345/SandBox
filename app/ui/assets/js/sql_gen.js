/* ============================================================
   SQL Generator — script.js
   Modular Vanilla JS, ES6+
   ============================================================ */

/* ── STATE ── */
const state = {
  currentSQL: '',
  currentTab: 'ai',
  theme: 'dark',
  isLoading: false,
  columns: [],
  groupBy: [],
  conditions: [],
  having: [],
  joins: [],
  sorts: [],
};

/* ═══════════════════════════════════════════════════════════
   PARTICLES
   ═══════════════════════════════════════════════════════════ */
function initParticles() {
  const canvas = document.getElementById('particleCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function createParticles() {
    const count = Math.min(60, Math.floor(W * H / 18000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.4 + 0.3,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      alpha: Math.random() * 0.4 + 0.05,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = W;
      if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H;
      if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(100,130,255,${p.alpha})`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }

  resize();
  createParticles();
  draw();
  window.addEventListener('resize', () => { resize(); createParticles(); });
}

/* ═══════════════════════════════════════════════════════════
   MOUSE GLOW
   ═══════════════════════════════════════════════════════════ */
function initMouseGlow() {
  const glow = document.getElementById('mouseGlow');
  if (!glow) return;
  let mx = -9999, my = -9999;

  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    glow.style.left = mx + 'px';
    glow.style.top = my + 'px';
    glow.style.opacity = '1';
  });
  document.addEventListener('mouseleave', () => { glow.style.opacity = '0'; });
}

/* ═══════════════════════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════════════════════ */
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const indicator = document.querySelector('.tab-indicator');

  function moveIndicator(btn) {
    const parent = btn.parentElement;
    const pRect = parent.getBoundingClientRect();
    const bRect = btn.getBoundingClientRect();
    indicator.style.left = (bRect.left - pRect.left) + 'px';
    indicator.style.width = bRect.width + 'px';
  }

  function activate(btn) {
    const tab = btn.dataset.tab;
    tabBtns.forEach(b => {
      b.classList.toggle('active', b === btn);
      b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
    });
    document.querySelectorAll('.tab-pane').forEach(p => {
      p.classList.toggle('active', p.id === `tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
    });
    state.currentTab = tab;
    moveIndicator(btn);
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => activate(btn));
  });

  // Init indicator
  const activeBtn = document.querySelector('.tab-btn.active');
  if (activeBtn) {
    requestAnimationFrame(() => moveIndicator(activeBtn));
  }
  window.addEventListener('resize', () => {
    const active = document.querySelector('.tab-btn.active');
    if (active) moveIndicator(active);
  });
}

/* ═══════════════════════════════════════════════════════════
   COLLAPSIBLES
   ═══════════════════════════════════════════════════════════ */
function initCollapsibles() {
  document.querySelectorAll('.collapse-toggle').forEach(btn => {
    const section = btn.closest('.collapsible');
    section.setAttribute('aria-expanded', 'false');

    btn.addEventListener('click', () => {
      const expanded = section.getAttribute('aria-expanded') === 'true';
      section.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    });
  });
}

/* ═══════════════════════════════════════════════════════════
   PILLS — Columns & Group By
   ═══════════════════════════════════════════════════════════ */
function addPill(container, value, arr) {
  if (!value.trim()) return;
  if (arr.includes(value.trim())) {
    showToast('Already added', 'warning'); return;
  }
  arr.push(value.trim());
  renderPills(container, arr);
}

function renderPills(container, arr) {
  container.innerHTML = '';
  arr.forEach((val, i) => {
    const pill = document.createElement('span');
    pill.className = 'pill';
    pill.innerHTML = `${escapeHtml(val)}<button class="pill-remove" aria-label="Remove ${escapeHtml(val)}" data-idx="${i}">✕</button>`;
    pill.querySelector('.pill-remove').addEventListener('click', () => {
      arr.splice(i, 1);
      renderPills(container, arr);
    });
    container.appendChild(pill);
  });
  updateBadge();
}

function initColumns() {
  const input = document.getElementById('columnSearch');
  const addBtn = document.getElementById('addColumnBtn');
  const container = document.getElementById('columnPills');

  function add() {
    addPill(container, input.value, state.columns);
    input.value = '';
    input.focus();
  }

  addBtn.addEventListener('click', add);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); add(); } });
}

function initGroupBy() {
  const input = document.getElementById('groupByInput');
  const addBtn = document.getElementById('addGroupByBtn');
  const container = document.getElementById('groupByPills');

  function add() {
    addPill(container, input.value, state.groupBy);
    input.value = '';
    input.focus();
  }

  addBtn.addEventListener('click', add);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); add(); } });
}

/* ═══════════════════════════════════════════════════════════
   CONDITIONS
   ═══════════════════════════════════════════════════════════ */
function createConditionRow(listId, arr) {
  const list = document.getElementById(listId);
  const idx = arr.length;
  arr.push({ field: '', operator: '=', value: '', logical_operator: 'AND' });

  const row = document.createElement('div');
  row.className = 'condition-row';
  row.dataset.idx = idx;
  row.innerHTML = `
    <div class="condition-row-inner">
      <div class="form-group">
        <label class="form-label">Field</label>
        <input type="text" class="form-input cond-field" placeholder="salary" />
      </div>
      <div class="form-group">
        <label class="form-label">Op</label>
        <div class="select-wrap">
          <select class="form-select cond-op">
            <option value="=">=</option>
            <option value="!=">!=</option>
            <option value=">">&gt;</option>
            <option value=">=">&gt;=</option>
            <option value="<">&lt;</option>
            <option value="<=">&lt;=</option>
            <option value="LIKE">LIKE</option>
            <option value="IN">IN</option>
            <option value="BETWEEN">BETWEEN</option>
            <option value="IS NULL">IS NULL</option>
            <option value="IS NOT NULL">IS NOT NULL</option>
          </select>
          <svg class="select-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Value</label>
        <input type="text" class="form-input cond-val" placeholder="50000" />
      </div>
    </div>
    <div class="condition-footer-row">
      <div class="logical-select-wrap">
        <label>Join with next:</label>
        <div class="select-wrap">
          <select class="cond-logical">
            <option value="AND">AND</option>
            <option value="OR">OR</option>
          </select>
        </div>
      </div>
      <button class="btn-remove-row" aria-label="Remove condition">✕</button>
    </div>
  `;

  // Bind
  const i = idx;
  row.querySelector('.cond-field').addEventListener('input', e => { arr[i].field = e.target.value; });
  row.querySelector('.cond-op').addEventListener('change', e => { arr[i].operator = e.target.value; });
  row.querySelector('.cond-val').addEventListener('input', e => { arr[i].value = e.target.value; });
  row.querySelector('.cond-logical').addEventListener('change', e => { arr[i].logical_operator = e.target.value; });
  row.querySelector('.btn-remove-row').addEventListener('click', () => {
    const actualIdx = parseInt(row.dataset.idx, 10);
    arr.splice(actualIdx, 1);
    row.style.animation = 'none';
    row.style.opacity = '0';
    row.style.transform = 'translateY(-4px)';
    row.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
    setTimeout(() => { row.remove(); rebindConditionIndices(list, arr); updateBadge(); }, 150);
    return;
  });

  list.appendChild(row);
  updateBadge();
}

function rebindConditionIndices(list, arr) {
  list.querySelectorAll('.condition-row').forEach((row, i) => row.dataset.idx = i);
}

/* ═══════════════════════════════════════════════════════════
   JOINS
   ═══════════════════════════════════════════════════════════ */
function createJoinRow() {
  const list = document.getElementById('joinsList');
  const idx = state.joins.length;
  state.joins.push({ join_type: 'INNER', table: '', left_column: '', operator: '=', right_column: '' });

  const row = document.createElement('div');
  row.className = 'join-row';
  row.dataset.idx = idx;
  row.innerHTML = `
    <div class="join-row-grid">
      <div class="form-group">
        <label class="form-label">Type</label>
        <div class="select-wrap">
          <select class="form-select join-type">
            <option value="INNER">INNER</option>
            <option value="LEFT">LEFT</option>
            <option value="RIGHT">RIGHT</option>
            <option value="FULL">FULL</option>
          </select>
          <svg class="select-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Table</label>
        <input type="text" class="form-input join-table" placeholder="departments" />
      </div>
      <div class="form-group">
        <label class="form-label">Left Column</label>
        <input type="text" class="form-input join-left" placeholder="e.dept_id" />
      </div>
      <div class="form-group">
        <label class="form-label">Op</label>
        <div class="select-wrap">
          <select class="form-select join-op">
            <option value="=">=</option><option value="!=">!=</option>
            <option value=">">&gt;</option><option value="<">&lt;</option>
          </select>
          <svg class="select-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Right Column</label>
        <input type="text" class="form-input join-right" placeholder="d.id" />
      </div>
    </div>
    <div class="condition-footer-row">
      <span></span>
      <button class="btn-remove-row" aria-label="Remove join">✕</button>
    </div>
  `;

  const i = idx;
  row.querySelector('.join-type').addEventListener('change', e => { state.joins[i].join_type = e.target.value; });
  row.querySelector('.join-table').addEventListener('input', e => { state.joins[i].table = e.target.value; });
  row.querySelector('.join-left').addEventListener('input', e => { state.joins[i].left_column = e.target.value; });
  row.querySelector('.join-op').addEventListener('change', e => { state.joins[i].operator = e.target.value; });
  row.querySelector('.join-right').addEventListener('input', e => { state.joins[i].right_column = e.target.value; });
  row.querySelector('.btn-remove-row').addEventListener('click', () => {
    const i2 = parseInt(row.dataset.idx, 10);
    state.joins.splice(i2, 1);
    row.style.opacity = '0'; row.style.transition = 'opacity 0.15s ease';
    setTimeout(() => { row.remove(); updateBadge(); }, 150);
  });

  list.appendChild(row);
  updateBadge();
}

/* ═══════════════════════════════════════════════════════════
   SORTS
   ═══════════════════════════════════════════════════════════ */
function createSortRow() {
  const list = document.getElementById('sortList');
  const idx = state.sorts.length;
  state.sorts.push({ field: '', direction: 'ASC' });

  const row = document.createElement('div');
  row.className = 'sort-row';
  row.dataset.idx = idx;
  row.innerHTML = `
    <div class="sort-row-inner">
      <div class="form-group">
        <label class="form-label">Field</label>
        <input type="text" class="form-input sort-field" placeholder="salary" />
      </div>
      <div class="form-group">
        <label class="form-label">Direction</label>
        <div class="sort-direction-group">
          <button class="dir-btn active" data-dir="ASC">ASC</button>
          <button class="dir-btn" data-dir="DESC">DESC</button>
        </div>
      </div>
    </div>
    <div class="condition-footer-row">
      <span></span>
      <button class="btn-remove-row" aria-label="Remove sort">✕</button>
    </div>
  `;

  const i = idx;
  row.querySelector('.sort-field').addEventListener('input', e => { state.sorts[i].field = e.target.value; });
  row.querySelectorAll('.dir-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      row.querySelectorAll('.dir-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.sorts[i].direction = btn.dataset.dir;
    });
  });
  row.querySelector('.btn-remove-row').addEventListener('click', () => {
    const i2 = parseInt(row.dataset.idx, 10);
    state.sorts.splice(i2, 1);
    row.style.opacity = '0'; row.style.transition = 'opacity 0.15s ease';
    setTimeout(() => { row.remove(); updateBadge(); }, 150);
  });

  list.appendChild(row);
  updateBadge();
}

/* ── bind add buttons ── */
function initBuilderControls() {
  document.getElementById('addConditionBtn').addEventListener('click', () => {
    createConditionRow('conditionsList', state.conditions);
    document.getElementById('conditionsSection').setAttribute('aria-expanded', 'true');
  });
  document.getElementById('addHavingBtn').addEventListener('click', () => {
    createConditionRow('havingList', state.having);
    document.getElementById('havingSection').setAttribute('aria-expanded', 'true');
  });
  document.getElementById('addJoinBtn').addEventListener('click', () => {
    createJoinRow();
    document.getElementById('joinsSection').setAttribute('aria-expanded', 'true');
  });
  document.getElementById('addSortBtn').addEventListener('click', () => {
    createSortRow();
    document.getElementById('sortSection').setAttribute('aria-expanded', 'true');
  });
  document.getElementById('clearBuilderBtn').addEventListener('click', clearBuilder);
  document.getElementById('generateBuilderBtn').addEventListener('click', generateFromBuilder);
}

/* ── badge counts ── */
function updateBadge() {
  const map = [
    ['conditionsBadge', state.conditions],
    ['joinsBadge', state.joins],
    ['groupByBadge', state.groupBy],
    ['havingBadge', state.having],
    ['sortBadge', state.sorts],
  ];
  map.forEach(([id, arr]) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = arr.length;
    el.classList.toggle('has-items', arr.length > 0);
  });
}

/* ═══════════════════════════════════════════════════════════
   CLEAR BUILDER
   ═══════════════════════════════════════════════════════════ */
function clearBuilder() {
  state.columns = []; state.groupBy = []; state.conditions = []; state.having = []; state.joins = []; state.sorts = [];
  document.getElementById('builderDatabase').value = '';
  document.getElementById('builderTable').value = '';
  document.getElementById('columnSearch').value = '';
  document.getElementById('groupByInput').value = '';
  document.getElementById('builderLimit').value = '';
  document.getElementById('columnPills').innerHTML = '';
  document.getElementById('groupByPills').innerHTML = '';
  document.getElementById('conditionsList').innerHTML = '';
  document.getElementById('havingList').innerHTML = '';
  document.getElementById('joinsList').innerHTML = '';
  document.getElementById('sortList').innerHTML = '';
  updateBadge();
  showToast('Builder cleared', 'info');
}

/* ═══════════════════════════════════════════════════════════
   GENERATE — MOCK RESPONSE
   ═══════════════════════════════════════════════════════════ */
const MOCK_THINKING_MSGS = [
  'Analyzing your query…',
  'Resolving table relationships…',
  'Optimizing join strategy…',
  'Building SQL clauses…',
  'Applying dialect rules…',
  'Finalizing your query…',
];

function showLoading() {
  state.isLoading = true;
  el('emptyState').classList.add('hidden');
  el('sqlOutput').classList.add('hidden');
  el('loadingState').classList.remove('hidden');

  let msgIdx = 0;
  const label = el('thinkingLabel');
  const interval = setInterval(() => {
    msgIdx = (msgIdx + 1) % MOCK_THINKING_MSGS.length;
    label.style.opacity = '0';
    label.style.transition = 'opacity 0.2s ease';
    setTimeout(() => {
      label.textContent = MOCK_THINKING_MSGS[msgIdx];
      label.style.opacity = '1';
    }, 200);
  }, 900);

  return interval;
}

function hideLoading(interval) {
  clearInterval(interval);
  state.isLoading = false;
  el('loadingState').classList.add('hidden');
}

// REMOVE this entire function and replace with:
async function generateFromAI() {
  const prompt = document.getElementById('aiPrompt').value.trim();
  if (!prompt) { showToast('Please enter a prompt', 'warning'); return; }

  const interval = showLoading();

  try {
    const token = localStorage.getItem('access_token'); // adjust if you store token differently

    const response = await fetch('/sql-generator/generate', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mode: 'ai',
        prompt: prompt,
        dialect: 'mysql',  // or pull from a dialect selector if you add one
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'API error');
    }

    const data = await response.json();
    hideLoading(interval);
    displayResult(data);
    showToast('SQL generated successfully', 'success');

  } catch (err) {
    hideLoading(interval);
    showToast(err.message || 'Failed to generate SQL', 'error');
  }
}

async function generateFromBuilder() {
  const table = document.getElementById('builderTable').value.trim();
  if (!table) { showToast('Table name is required', 'warning'); return; }

  const interval = showLoading();

  try {
    const token = localStorage.getItem('access_token');

    const payload = {
      mode: 'builder',
      dialect: document.getElementById('builderDialect').value,
      builder: {
        table: table,
        database: document.getElementById('builderDatabase').value.trim() || null,
        columns: state.columns,
        conditions: state.conditions,
        joins: state.joins,
        group_by: state.groupBy,
        having: state.having,
        sort: state.sorts,
        limit: document.getElementById('builderLimit').value
          ? parseInt(document.getElementById('builderLimit').value)
          : null,
      },
    };

    const response = await fetch('/sql-generator/generate', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'API error');
    }

    const data = await response.json();
    hideLoading(interval);
    displayResult(data);
    showToast('Query built successfully', 'success');

  } catch (err) {
    hideLoading(interval);
    showToast(err.message || 'Failed to build query', 'error');
  }
}

/* ── Build mock AI response based on prompt keywords ── */
function buildMockAIResponse(prompt) {
  const lower = prompt.toLowerCase();

  if (lower.includes('revenue') || lower.includes('sales')) {
    return {
      success: true,
      sql: `SELECT\n    p.category,\n    SUM(oi.quantity * oi.unit_price) AS total_revenue,\n    COUNT(DISTINCT o.id) AS order_count\nFROM orders o\nINNER JOIN order_items oi\n    ON o.id = oi.order_id\nINNER JOIN products p\n    ON oi.product_id = p.id\nWHERE\n    o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)\n    AND o.status = 'completed'\nGROUP BY\n    p.category\nORDER BY\n    total_revenue DESC\nLIMIT 10;`,
      query_type: 'SELECT',
      tables: ['orders', 'order_items', 'products'],
      complexity: 'Complex',
      execution_cost: { label: 'High', score: 72 },
      explanation: 'Aggregates revenue across product categories from the last 30 days, joining three tables to connect orders, line items, and products.',
      warnings: ['Ensure indexes exist on orders.created_at and order_items.order_id for optimal performance.'],
    };
  }

  if (lower.includes('duplicate') || lower.includes('email')) {
    return {
      success: true,
      sql: `SELECT\n    email,\n    COUNT(*) AS occurrences\nFROM users\nGROUP BY\n    email\nHAVING\n    COUNT(*) > 1\nORDER BY\n    occurrences DESC;`,
      query_type: 'SELECT',
      tables: ['users'],
      complexity: 'Moderate',
      execution_cost: { label: 'Low', score: 28 },
      explanation: 'Finds email addresses that appear more than once in the users table using a GROUP BY + HAVING pattern.',
      warnings: [],
    };
  }

  if (lower.includes('customer') || lower.includes('top')) {
    return {
      success: true,
      sql: `SELECT\n    c.id,\n    c.name,\n    c.email,\n    COUNT(o.id) AS order_count,\n    SUM(o.total_amount) AS total_spent\nFROM customers c\nINNER JOIN orders o\n    ON c.id = o.customer_id\nGROUP BY\n    c.id,\n    c.name,\n    c.email\nORDER BY\n    total_spent DESC\nLIMIT 10;`,
      query_type: 'SELECT',
      tables: ['customers', 'orders'],
      complexity: 'Moderate',
      execution_cost: { label: 'Medium', score: 45 },
      explanation: 'Retrieves the top 10 customers ranked by total spending, with their email and order count.',
      warnings: [],
    };
  }

  if (lower.includes('inventory') || lower.includes('stock')) {
    return {
      success: true,
      sql: `SELECT\n    p.id,\n    p.name,\n    p.sku,\n    i.quantity,\n    i.reorder_level\nFROM products p\nINNER JOIN inventory i\n    ON p.id = i.product_id\nWHERE\n    i.quantity < 10\nORDER BY\n    i.quantity ASC;`,
      query_type: 'SELECT',
      tables: ['products', 'inventory'],
      complexity: 'Simple',
      execution_cost: { label: 'Low', score: 18 },
      explanation: 'Lists all products with fewer than 10 units in stock, ordered from lowest to highest inventory.',
      warnings: [],
    };
  }

  // Default employee response
  return {
    success: true,
    sql: `SELECT\n    e.name,\n    e.salary,\n    d.department_name\nFROM employees e\nINNER JOIN departments d\n    ON e.department_id = d.id\nWHERE\n    e.salary > 50000\n    AND d.department_name = 'IT'\nGROUP BY\n    e.name,\n    e.salary,\n    d.department_name\nORDER BY\n    e.salary DESC\nLIMIT 10;`,
    query_type: 'SELECT',
    tables: ['employees', 'departments'],
    complexity: 'Moderate',
    execution_cost: { label: 'Medium', score: 44 },
    explanation: 'Selects employees in the IT department earning above ₹50,000, joined with department data, ordered by salary.',
    warnings: [],
  };
}

/* ── Build mock builder response ── */
function buildMockBuilderResponse() {
  const table = document.getElementById('builderTable').value.trim() || 'table';
  const cols = state.columns.length ? state.columns.join(', ') : '*';
  const limit = document.getElementById('builderLimit').value;
  const dialect = document.getElementById('builderDialect').value;

  let sql = `SELECT\n    ${cols}\nFROM ${table}`;

  state.joins.forEach(j => {
    if (j.table && j.left_column && j.right_column) {
      sql += `\n${j.join_type} JOIN ${j.table}\n    ON ${j.left_column} ${j.operator} ${j.right_column}`;
    }
  });

  const validConds = state.conditions.filter(c => c.field && c.operator);
  if (validConds.length) {
    sql += '\nWHERE\n    ' + validConds.map((c, i) => {
      const val = c.operator.includes('NULL') ? '' : ` '${c.value}'`;
      const logOp = i < validConds.length - 1 ? ` ${c.logical_operator}` : '';
      return `${c.field} ${c.operator}${val}${logOp}`;
    }).join('\n    ');
  }

  if (state.groupBy.length) {
    sql += `\nGROUP BY\n    ${state.groupBy.join(', ')}`;
  }

  const validHaving = state.having.filter(h => h.field && h.operator);
  if (validHaving.length) {
    sql += '\nHAVING\n    ' + validHaving.map((h, i) => {
      const val = h.operator.includes('NULL') ? '' : ` '${h.value}'`;
      const logOp = i < validHaving.length - 1 ? ` ${h.logical_operator}` : '';
      return `${h.field} ${h.operator}${val}${logOp}`;
    }).join('\n    ');
  }

  const validSorts = state.sorts.filter(s => s.field);
  if (validSorts.length) {
    sql += `\nORDER BY\n    ${validSorts.map(s => `${s.field} ${s.direction}`).join(', ')}`;
  }

  if (limit) {
    if (dialect === 'sqlserver') {
      sql += `\nOFFSET 0 ROWS FETCH NEXT ${limit} ROWS ONLY`;
    } else if (dialect === 'oracle') {
      sql += `\nFETCH FIRST ${limit} ROWS ONLY`;
    } else {
      sql += `\nLIMIT ${limit}`;
    }
  }

  sql += ';';

  const tables = [table, ...state.joins.filter(j => j.table).map(j => j.table)];
  const complexity = estimateComplexity(sql);
  const cost = estimateCost(sql);

  return {
    success: true,
    sql,
    query_type: 'SELECT',
    tables,
    complexity,
    execution_cost: { label: cost, score: costToScore(cost) },
    explanation: `Generated from Visual Builder: selecting from "${table}" with ${state.conditions.length} condition(s), ${state.joins.length} join(s), and ${state.sorts.length} sort(s).`,
    warnings: state.columns.length === 0 ? ['Using SELECT * can be costly on large tables. Consider specifying columns.'] : [],
  };
}

function estimateComplexity(sql) {
  const s = sql.toUpperCase();
  let score = 0;
  score += (s.match(/ JOIN/g) || []).length * 2;
  if (s.includes(' WHERE ')) score += 1;
  if (s.includes(' GROUP BY ')) score += 2;
  if (s.includes(' HAVING ')) score += 2;
  if (s.includes(' ORDER BY ')) score += 1;
  if (score <= 2) return 'Simple';
  if (score <= 6) return 'Moderate';
  if (score <= 12) return 'Complex';
  return 'Very Complex';
}

function estimateCost(sql) {
  const s = sql.toUpperCase();
  let score = 0;
  if (s.includes('SELECT *')) score += 2;
  score += (s.match(/ JOIN/g) || []).length * 3;
  if (!s.includes(' WHERE ')) score += 3;
  if (s.includes(' GROUP BY ')) score += 2;
  if (s.includes(' ORDER BY ')) score += 2;
  if (s.includes(' LIMIT ')) score -= 1;
  if (score <= 3) return 'Low';
  if (score <= 8) return 'Medium';
  if (score <= 14) return 'High';
  return 'Very High';
}

function costToScore(label) {
  return { Low: 20, Medium: 48, High: 72, 'Very High': 92 }[label] || 50;
}

/* ═══════════════════════════════════════════════════════════
   DISPLAY RESULT
   ═══════════════════════════════════════════════════════════ */
function displayResult(resp) {
  state.currentSQL = resp.formatted_sql || resp.sql || '';

  // SQL code
  el('sqlCodeContent').innerHTML = syntaxHighlight(state.currentSQL);

  // Analysis cards
  el('queryTypeVal').textContent = resp.query_type || '—';
  el('queryTypeVal').className = 'analysis-value';

  // Tables
  const tablesEl = el('tablesVal');
  tablesEl.innerHTML = '';
  (resp.tables || []).forEach(t => {
    const tag = document.createElement('span');
    tag.className = 'analysis-tag';
    tag.textContent = t;
    tablesEl.appendChild(tag);
  });

  // Complexity
  const cx = resp.complexity || '—';
  const cxEl = el('complexityVal');
  cxEl.textContent = cx;
  cxEl.className = `analysis-value complexity-${cx.toLowerCase().replace(' ', '-')}`;

  // Execution cost
  const cost = typeof resp.execution_cost === 'object' ? resp.execution_cost.label : resp.execution_cost;
  const costEl = el('executionCostVal');
  costEl.textContent = cost || '—';
  costEl.className = `analysis-value cost-${(cost || '').toLowerCase().replace(' ', '-')}`;

  // Explanation
  if (resp.explanation) {
    el('explanationText').textContent = resp.explanation;
    el('explanationBlock').classList.remove('hidden');
  } else {
    el('explanationBlock').classList.add('hidden');
  }

  // Warnings
  const warnings = resp.warnings || [];
  if (warnings.length) {
    const ul = el('warningsList');
    ul.innerHTML = '';
    warnings.forEach(w => {
      const li = document.createElement('li');
      li.textContent = w;
      ul.appendChild(li);
    });
    el('warningsBlock').classList.remove('hidden');
  } else {
    el('warningsBlock').classList.add('hidden');
  }

  el('sqlOutput').classList.remove('hidden');
  el('sqlOutput').style.animation = 'none';
  requestAnimationFrame(() => { el('sqlOutput').style.animation = ''; });
}

/* ── SQL Syntax Highlighter ── */
function syntaxHighlight(sql) {
  const keywords = /\b(SELECT|FROM|WHERE|AND|OR|ORDER BY|GROUP BY|HAVING|LIMIT|JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|ON|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|WITH|CASE|WHEN|THEN|ELSE|END|IN|LIKE|BETWEEN|IS NULL|IS NOT NULL|NOT|EXISTS|UNION|ALL|OFFSET|FETCH|NEXT|ROWS|ONLY|INTERVAL|DATE_SUB|NOW|DATE_ADD|COALESCE|NULLIF|CAST|CONVERT|ASC|DESC|INTO|VALUES|SET|TABLE|INDEX|VIEW|PROCEDURE|FUNCTION|TRIGGER|DATABASE)\b/gi;

  // Escape HTML first
  let out = sql
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
  // Do NOT escape single quotes — they should render as ' in SQL

  // Strings — match single-quoted values (already HTML-safe, no &#039;)
  out = out.replace(/'[^']*'/g, m => `<span class="tok-str">${m}</span>`);

  // Keywords
  out = out.replace(keywords, m => `<span class="tok-kw">${m.toUpperCase()}</span>`);

  // Numbers
  out = out.replace(/\b(\d+(\.\d+)?)\b/g, m => `<span class="tok-num">${m}</span>`);

  return out;
}

/* ═══════════════════════════════════════════════════════════
   TOOLBAR ACTIONS
   ═══════════════════════════════════════════════════════════ */
function initToolbarActions() {
  el('copyBtn').addEventListener('click', copySQL);
  el('fsCopyBtn').addEventListener('click', copySQL);
  el('formatBtn').addEventListener('click', formatSQL);
  el('downloadBtn').addEventListener('click', downloadSQL);
  el('fullscreenBtn').addEventListener('click', openFullscreen);
  el('closeFullscreenBtn').addEventListener('click', closeFullscreen);
}

function copySQL() {
  if (!state.currentSQL) { showToast('No SQL to copy', 'warning'); return; }
  navigator.clipboard.writeText(state.currentSQL).then(() => {
    const btn = el('copyBtn');
    btn.classList.add('success-flash');
    btn.textContent = '✓ Copied';
    setTimeout(() => { btn.classList.remove('success-flash'); btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>Copy`; }, 2000);
    showToast('SQL copied to clipboard', 'success');
  }).catch(() => showToast('Copy failed — please copy manually', 'error'));
}

function formatSQL() {
  if (!state.currentSQL) return;
  // Simple reformat — ensure consistent indentation
  let sql = state.currentSQL
    .replace(/\n+/g, '\n')
    .replace(/\s{2,}/g, ' ')
    .trim();
  showToast('SQL formatted', 'info');
}

function downloadSQL() {
  if (!state.currentSQL) { showToast('No SQL to download', 'warning'); return; }
  const blob = new Blob([state.currentSQL], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'query.sql';
  a.click();
  URL.revokeObjectURL(a.href);
  showToast('query.sql downloaded', 'success');
}

function openFullscreen() {
  if (!state.currentSQL) return;
  el('fsSqlContent').innerHTML = syntaxHighlight(state.currentSQL);
  el('fullscreenOverlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeFullscreen() {
  el('fullscreenOverlay').classList.add('hidden');
  document.body.style.overflow = '';
}

/* ═══════════════════════════════════════════════════════════
   COMMAND PALETTE
   ═══════════════════════════════════════════════════════════ */
function initCommandPalette() {
  const overlay = el('cmdOverlay');
  const input = el('cmdInput');

  function open() {
    overlay.classList.remove('hidden');
    input.value = '';
    input.focus();
    renderCmdItems('');
  }
  function close() { overlay.classList.add('hidden'); }

  el('cmdPaletteHint').addEventListener('click', open);

  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });

  input.addEventListener('input', e => renderCmdItems(e.target.value));

  el('cmdResults').addEventListener('click', e => {
    const item = e.target.closest('[data-action]');
    if (!item) return;
    close();
    handleCmdAction(item.dataset.action);
  });

  window._openCmdPalette = open;
  window._closeCmdPalette = close;
}

function renderCmdItems(query) {
  const items = el('cmdResults').querySelectorAll('.cmd-item');
  const q = query.toLowerCase();
  items.forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = !q || text.includes(q) ? '' : 'none';
  });
}

function handleCmdAction(action) {
  const actions = {
    generateAI: () => {
      switchTab('ai');
      setTimeout(() => el('generateBtn').click(), 100);
    },
    switchAI: () => switchTab('ai'),
    switchBuilder: () => switchTab('builder'),
    copySQL: copySQL,
    downloadSQL: downloadSQL,
    clearBuilder: clearBuilder,
    toggleTheme: toggleTheme,
    shortcutHelp: openShortcutModal,
  };
  if (actions[action]) actions[action]();
}

function switchTab(tab) {
  const btn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
  if (btn) btn.click();
}

/* ═══════════════════════════════════════════════════════════
   PROMPT CHIPS
   ═══════════════════════════════════════════════════════════ */
function initChips() {
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const textarea = el('aiPrompt');
      textarea.value = chip.dataset.prompt;
      textarea.focus();
      chip.classList.add('chip-active');
      setTimeout(() => chip.classList.remove('chip-active'), 400);
    });
  });
}

/* ═══════════════════════════════════════════════════════════
   THEME TOGGLE
   ═══════════════════════════════════════════════════════════ */
function initTheme() {
  const saved = localStorage.getItem('sqg-theme') || 'dark';
  state.theme = saved;
  applyTheme(saved);
  el('themeToggle').addEventListener('click', toggleTheme);
}

function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('sqg-theme', state.theme);
  applyTheme(state.theme);
  showToast(`Switched to ${state.theme} mode`, 'info');
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = el('themeIcon');
  if (theme === 'light') {
    icon.innerHTML = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>`;
  } else {
    icon.innerHTML = `<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>`;
  }
}

/* ═══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS
   ═══════════════════════════════════════════════════════════ */
function initKeyboard() {
  document.addEventListener('keydown', e => {
    // Ctrl+Enter — generate
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (state.currentTab === 'ai') el('generateBtn').click();
      else el('generateBuilderBtn').click();
    }

    // Ctrl+K — command palette
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      window._openCmdPalette && window._openCmdPalette();
    }

    // Ctrl+Shift+C — copy SQL
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
      e.preventDefault();
      copySQL();
    }

    // Esc — close overlays
    if (e.key === 'Escape') {
      el('cmdOverlay').classList.add('hidden');
      el('shortcutModal').classList.add('hidden');
      el('fullscreenOverlay').classList.add('hidden');
      document.body.style.overflow = '';
    }

    // ? — shortcuts modal
    if (e.key === '?' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) {
      openShortcutModal();
    }
  });
}

/* ═══════════════════════════════════════════════════════════
   SHORTCUT MODAL
   ═══════════════════════════════════════════════════════════ */
function openShortcutModal() {
  el('shortcutModal').classList.remove('hidden');
}

function initShortcutModal() {
  el('closeShortcutModal').addEventListener('click', () => el('shortcutModal').classList.add('hidden'));
  el('shortcutModal').addEventListener('click', e => { if (e.target === el('shortcutModal')) el('shortcutModal').classList.add('hidden'); });
}

/* ═══════════════════════════════════════════════════════════
   RESIZE PANEL
   ═══════════════════════════════════════════════════════════ */
function initResizePanel() {
  const handle = el('resizeHandle');
  const panelLeft = el('panelLeft');
  let dragging = false;
  let startX, startW;

  handle.addEventListener('mousedown', e => {
    dragging = true;
    startX = e.clientX;
    startW = panelLeft.offsetWidth;
    handle.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  });

  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const delta = e.clientX - startX;
    const newW = Math.min(600, Math.max(300, startW + delta));
    panelLeft.style.width = newW + 'px';
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    handle.classList.remove('dragging');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  });
}

/* ═══════════════════════════════════════════════════════════
   TOAST
   ═══════════════════════════════════════════════════════════ */
const TOAST_ICONS = {
  success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  error: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  info: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
};

const TOAST_DURATION = { success: 3000, error: 5000, warning: 4000, info: 3000 };

function showToast(message, type = 'info') {
  const container = el('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const duration = TOAST_DURATION[type] || 3000;
  toast.style.setProperty('--toast-duration', duration + 'ms');
  toast.querySelector?.('::after');

  toast.innerHTML = `
    ${TOAST_ICONS[type] || TOAST_ICONS.info}
    <span>${escapeHtml(message)}</span>
    <button class="toast-close" aria-label="Dismiss">✕</button>
  `;

  toast.style.setProperty('--toast-duration', duration + 'ms');
  // Apply progress bar duration inline
  const style = document.createElement('style');
  style.textContent = '';
  toast.querySelector('.toast-close').addEventListener('click', () => dismiss(toast));

  // Set animation duration on ::after via inline style trick
  toast.style.setProperty('--d', duration + 'ms');
  toast.insertAdjacentHTML('beforeend', `<style>.toast:last-child::after { animation-duration: ${duration}ms; }</style>`);

  container.appendChild(toast);

  const timer = setTimeout(() => dismiss(toast), duration);
  toast.dataset.timer = timer;

  function dismiss(t) {
    clearTimeout(t.dataset.timer);
    t.classList.add('removing');
    setTimeout(() => t.remove(), 220);
  }
}

/* ═══════════════════════════════════════════════════════════
   EXAMPLES MODAL (simple)
   ═══════════════════════════════════════════════════════════ */
function initExamplesBtn() {
  el('examplesBtn').addEventListener('click', () => {
    switchTab('ai');
    el('aiPrompt').value = 'Show all employees earning more than ₹50,000 in the IT department ordered by salary descending.';
    el('aiPrompt').focus();
    showToast('Example prompt loaded', 'info');
  });
}

/* ═══════════════════════════════════════════════════════════
   UTILITY
   ═══════════════════════════════════════════════════════════ */
function el(id) { return document.getElementById(id); }

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/* ═══════════════════════════════════════════════════════════
   INIT — run after DOM ready
   ═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initMouseGlow();
  initTabs();
  initCollapsibles();
  initColumns();
  initGroupBy();
  initBuilderControls();
  initChips();
  initTheme();
  initKeyboard();
  initCommandPalette();
  initShortcutModal();
  initToolbarActions();
  initResizePanel();
  initExamplesBtn();
  updateBadge();

  // Generate button
  el('generateBtn').addEventListener('click', generateFromAI);

  // Clear prompt
  el('clearPromptBtn').addEventListener('click', () => {
    el('aiPrompt').value = '';
    el('aiPrompt').focus();
  });

  // Prompt textarea — auto grow
  el('aiPrompt').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 280) + 'px';
  });

  // Page entry animation
  document.body.style.opacity = '0';
  requestAnimationFrame(() => {
    document.body.style.transition = 'opacity 0.4s ease';
    document.body.style.opacity = '1';
  });
});