(() => {
  'use strict';

  /* ============================================================
     THEME
     ============================================================ */
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const iconMoon = document.getElementById('themeIconMoon');
  const iconSun = document.getElementById('themeIconSun');

  function applyTheme(t) {
    root.setAttribute('data-theme', t);
    iconMoon.classList.toggle('hidden', t === 'light');
    iconSun.classList.toggle('hidden', t !== 'light');
    localStorage.setItem('helmsman_theme', t);
  }
  applyTheme(localStorage.getItem('helmsman_theme') || 'dark');
  themeToggle.addEventListener('click', () => {
    applyTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
  });

  /* Mouse glow */
  const glow = document.getElementById('mouseGlow');
  window.addEventListener('mousemove', (e) => {
    glow.style.opacity = '1';
    glow.style.left = e.clientX + 'px';
    glow.style.top = e.clientY + 'px';
  });
  window.addEventListener('mouseleave', () => { glow.style.opacity = '0'; });

  /* ============================================================
     TABS (Form / Compose)
     ============================================================ */
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabIndicator = document.getElementById('tabIndicator');
  const panes = { form: document.getElementById('tab-form'), compose: document.getElementById('tab-compose') };

  function positionIndicator(btn) {
    tabIndicator.style.left = btn.offsetLeft + 'px';
    tabIndicator.style.width = btn.offsetWidth + 'px';
  }
  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      Object.values(panes).forEach((p) => p.classList.remove('active'));
      panes[btn.dataset.tab].classList.add('active');
      positionIndicator(btn);
    });
  });
  window.addEventListener('resize', () => positionIndicator(document.querySelector('.tab-btn.active')));
  requestAnimationFrame(() => positionIndicator(document.querySelector('.tab-btn.active')));

  /* ============================================================
     COLLAPSIBLES
     ============================================================ */
  document.querySelectorAll('.collapse-toggle').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (e.target.closest('.mini-switch')) return; // don't toggle collapse when flipping the switch
      const target = document.getElementById(btn.dataset.target);
      const open = target.getAttribute('aria-expanded') === 'true';
      target.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  });

  /* Auto-expand + enable/disable fields tied to a "section enabled" switch */
  function wireSectionSwitch(switchId, collapsibleId, fieldIds) {
    const sw = document.getElementById(switchId);
    const collapsible = document.getElementById(collapsibleId);
    sw.addEventListener('change', () => {
      fieldIds.forEach((id) => { document.getElementById(id).disabled = !sw.checked; });
      if (sw.checked) collapsible.setAttribute('aria-expanded', 'true');
    });
  }
  wireSectionSwitch('f_storage_enabled', 'storageBody', ['f_pvc_name', 'f_storage_size', 'f_mount_path', 'f_access_mode']);
  wireSectionSwitch('f_ingress_enabled', 'ingressBody', ['f_ingress_host', 'f_ingress_path', 'f_ingress_tls']);
  wireSectionSwitch('f_hpa_enabled', 'hpaBody', ['f_hpa_min', 'f_hpa_max', 'f_hpa_cpu']);

  document.getElementById('f_readiness_enabled').addEventListener('change', function () {
    ['f_readiness_path', 'f_readiness_port', 'f_readiness_delay', 'f_readiness_period'].forEach((id) => {
      document.getElementById(id).disabled = !this.checked;
    });
  });
  document.getElementById('f_liveness_enabled').addEventListener('change', function () {
    ['f_liveness_path', 'f_liveness_port', 'f_liveness_delay', 'f_liveness_period'].forEach((id) => {
      document.getElementById(id).disabled = !this.checked;
    });
  });

  /* HPA slider fill + readout */
  const hpaCpu = document.getElementById('f_hpa_cpu');
  const hpaCpuVal = document.getElementById('hpaCpuVal');
  function syncHpaSlider() {
    hpaCpuVal.textContent = hpaCpu.value;
    hpaCpu.style.setProperty('--fill', hpaCpu.value + '%');
  }
  hpaCpu.addEventListener('input', syncHpaSlider);
  syncHpaSlider();

  /* Pill toggles (output format) */
  document.querySelectorAll('.pill-toggle').forEach((group) => {
    group.querySelectorAll('.pill-toggle-opt').forEach((opt) => {
      opt.addEventListener('click', () => {
        group.querySelectorAll('.pill-toggle-opt').forEach((o) => o.classList.remove('active'));
        opt.classList.add('active');
        group.dataset.value = opt.dataset.val;
      });
    });
  });

  /* ============================================================
     DYNAMIC ROWS — Ports / Env / Secrets
     ============================================================ */
  let rowSeq = 0;

  function makeRow(listEl, badgeEl, fields, opts = {}) {
    rowSeq += 1;
    const id = `row_${rowSeq}`;
    const row = document.createElement('div');
    row.className = `dynamic-row ${fields.length === 2 ? 'two-field' : ''}`;
    row.dataset.id = id;

    fields.forEach((f) => {
      let el;
      if (f.type === 'select') {
        el = document.createElement('select');
        el.className = 'form-select';
        f.options.forEach((o) => {
          const opt = document.createElement('option');
          opt.value = o; opt.textContent = o;
          if (o === f.value) opt.selected = true;
          el.appendChild(opt);
        });
      } else {
        el = document.createElement('input');
        el.className = 'form-input' + (f.mono ? ' mono-input' : '');
        el.type = f.type || 'text';
        el.placeholder = f.placeholder || '';
        if (f.value !== undefined) el.value = f.value;
      }
      el.dataset.field = f.name;
      row.appendChild(el);
    });

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn-remove-row';
    removeBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>';
    removeBtn.addEventListener('click', () => {
      row.style.animation = 'none';
      row.remove();
      updateBadge(listEl, badgeEl);
    });
    row.appendChild(removeBtn);

    listEl.appendChild(row);
    updateBadge(listEl, badgeEl);
    return row;
  }

  function updateBadge(listEl, badgeEl) {
    const n = listEl.children.length;
    badgeEl.textContent = n;
    badgeEl.classList.toggle('has-items', n > 0);
  }

  // Ports
  const portsList = document.getElementById('portsList');
  const portsBadge = document.getElementById('portsBadge');
  document.getElementById('addPortBtn').addEventListener('click', () => {
    makeRow(portsList, portsBadge, [
      { name: 'container_port', type: 'number', placeholder: 'Container port (8080)' },
      { name: 'service_port', type: 'number', placeholder: 'Service port (80)' },
      { name: 'protocol', type: 'select', options: ['TCP', 'UDP'], value: 'TCP' },
    ]);
  });
  // seed with one sensible default row
  document.getElementById('addPortBtn').click();
  portsList.querySelector('.dynamic-row [data-field="container_port"]').value = 8080;
  portsList.querySelector('.dynamic-row [data-field="service_port"]').value = 80;

  // Env
  const envList = document.getElementById('envList');
  const envBadge = document.getElementById('envBadge');
  document.getElementById('addEnvBtn').addEventListener('click', () => {
    makeRow(envList, envBadge, [
      { name: 'key', type: 'text', placeholder: 'KEY', mono: true },
      { name: 'value', type: 'text', placeholder: 'value', mono: true },
    ]);
  });

  // Secrets
  const secretsList = document.getElementById('secretsList');
  const secretsBadge = document.getElementById('secretsBadge');
  document.getElementById('addSecretBtn').addEventListener('click', () => {
    makeRow(secretsList, secretsBadge, [
      { name: 'key', type: 'text', placeholder: 'KEY', mono: true },
      { name: 'value', type: 'password', placeholder: '••••••', mono: true },
    ]);
  });

  function readRows(listEl, fieldNames) {
    return Array.from(listEl.children).map((row) => {
      const obj = {};
      fieldNames.forEach((name) => {
        const el = row.querySelector(`[data-field="${name}"]`);
        obj[name] = el.type === 'number' ? Number(el.value) : el.value;
      });
      return obj;
    }).filter((o) => Object.values(o).some((v) => v !== '' && v !== null && !Number.isNaN(v)));
  }

  /* ============================================================
     COMPOSE FILE DROPZONE
     ============================================================ */
  const dropzone = document.getElementById('dropzone');
  const composeFileInput = document.getElementById('composeFileInput');
  const composeFileChip = document.getElementById('composeFileChip');
  const composeFileName = document.getElementById('composeFileName');
  const composeFileRemove = document.getElementById('composeFileRemove');
  const generateComposeBtn = document.getElementById('generateComposeBtn');
  let composeFile = null;

  function setComposeFile(file) {
    composeFile = file;
    if (file) {
      composeFileName.textContent = file.name;
      composeFileChip.classList.remove('hidden');
      dropzone.classList.add('hidden');
      generateComposeBtn.disabled = false;
    } else {
      composeFileChip.classList.add('hidden');
      dropzone.classList.remove('hidden');
      generateComposeBtn.disabled = true;
    }
  }

  dropzone.addEventListener('click', () => composeFileInput.click());
  composeFileInput.addEventListener('change', () => {
    if (composeFileInput.files[0]) setComposeFile(composeFileInput.files[0]);
  });
  ['dragenter', 'dragover'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  });
  ['dragleave', 'drop'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove('drag-over'); });
  });
  dropzone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (file) setComposeFile(file);
  });
  composeFileRemove.addEventListener('click', (e) => { e.stopPropagation(); setComposeFile(null); composeFileInput.value = ''; });

  /* ============================================================
     RESET
     ============================================================ */
  document.getElementById('resetFormBtn').addEventListener('click', () => {
    document.getElementById('f_app_name').value = '';
    document.getElementById('f_namespace').value = 'default';
    document.getElementById('f_image').value = '';
    document.getElementById('f_replicas').value = 1;
    document.getElementById('f_pull_policy').value = 'IfNotPresent';
    document.getElementById('f_service_type').value = 'ClusterIP';
    portsList.innerHTML = ''; envList.innerHTML = ''; secretsList.innerHTML = '';
    updateBadge(portsList, portsBadge); updateBadge(envList, envBadge); updateBadge(secretsList, secretsBadge);
    document.getElementById('addPortBtn').click();
    ['f_storage_enabled', 'f_ingress_enabled', 'f_hpa_enabled', 'f_readiness_enabled', 'f_liveness_enabled'].forEach((id) => {
      const el = document.getElementById(id);
      el.checked = false;
      el.dispatchEvent(new Event('change'));
    });
    showToast('Form spec reset', 'info');
  });

  document.getElementById('resetFormBtn').addEventListener('click', () => {
    window.location.reload();
  });

  document.getElementById('resetComposeBtn').addEventListener('click', () => {
    window.location.reload();
  });


  /* ============================================================
     TOASTS
     ============================================================ */
  const toastContainer = document.getElementById('toastContainer');
  const TOAST_ICONS = {
    success: '<path d="M20 6 9 17l-5-5"/>',
    error: '<circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  };
  function showToast(message, type = 'info', duration = 3800) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <svg class="toast-icon" viewBox="0 0 24 24">${TOAST_ICONS[type] || TOAST_ICONS.info}</svg>
      <span>${message}</span>
      <button class="toast-close" aria-label="Dismiss">✕</button>
    `;
    toast.style.setProperty('--barDur', duration + 'ms');
    toast.querySelector('.toast-close').addEventListener('click', () => removeToast(toast));
    toastContainer.appendChild(toast);
    setTimeout(() => removeToast(toast), duration);
  }
  function removeToast(toast) {
    if (!toast.isConnected) return;
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 220);
  }

  /* ============================================================
     RESOURCE META (for constellation + pills)
     ============================================================ */
  const RESOURCE_META = {
    DEPLOYMENT: { label: 'Deployment', color: '#4c8dff', log: 'Rendering Deployment spec',
      icon: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>' },
    SERVICE: { label: 'Service', color: '#22d3ee', log: 'Wiring up the Service',
      icon: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>' },
    CONFIGMAP: { label: 'ConfigMap', color: '#8b5cf6', log: 'Packing env into a ConfigMap',
      icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>' },
    SECRET: { label: 'Secret', color: '#f59e0b', log: 'Encoding Secret values',
      icon: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>' },
    PVC: { label: 'PVC', color: '#22c55e', log: 'Provisioning a PersistentVolumeClaim',
      icon: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>' },
    INGRESS: { label: 'Ingress', color: '#ec4899', log: 'Routing Ingress rules',
      icon: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z"/>' },
    HPA: { label: 'HPA', color: '#f97316', log: 'Tuning the autoscaler',
      icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' },
  };
  // maps backend ResourceKind strings -> our internal keys
  const KIND_TO_META = {
    Deployment: RESOURCE_META.DEPLOYMENT,
    Service: RESOURCE_META.SERVICE,
    ConfigMap: RESOURCE_META.CONFIGMAP,
    Secret: RESOURCE_META.SECRET,
    PersistentVolumeClaim: RESOURCE_META.PVC,
    Ingress: RESOURCE_META.INGRESS,
    HorizontalPodAutoscaler: RESOURCE_META.HPA,
  };

  /* ============================================================
     PANEL STATE SWITCHING
     ============================================================ */
  const emptyState = document.getElementById('emptyState');
  const loadingState = document.getElementById('loadingState');
  const resultsState = document.getElementById('resultsState');
  const errorState = document.getElementById('errorState');

  function showPanel(which) {
    [emptyState, loadingState, resultsState, errorState].forEach((el) => el.classList.add('hidden'));
    which.classList.remove('hidden');
  }

  /* ============================================================
     CONSTELLATION LOADING ANIMATION
     ============================================================ */
  const constNodesG = document.getElementById('constNodes');
  const constLinesG = document.getElementById('constLines');
  const buildLog = document.getElementById('buildLog');
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const CX = 160, CY = 132, R = 92;

  function buildConstellation(keys) {
    constNodesG.innerHTML = '';
    constLinesG.innerHTML = '';
    buildLog.innerHTML = '';

    // Hub
    const hub = document.createElementNS(SVG_NS, 'g');
    hub.innerHTML = `
      <circle class="const-hub-ring" cx="${CX}" cy="${CY}" r="34"></circle>
      <circle class="const-hub-circle" cx="${CX}" cy="${CY}" r="22"></circle>
      <g transform="translate(${CX - 10},${CY - 10}) scale(0.83)">
        <path class="const-hub-icon" d="M12 2 L21 7 V17 L12 22 L3 17 V7 Z"/>
        <circle class="const-hub-dot" cx="12" cy="12" r="2.6"></circle>
      </g>`;
    constNodesG.appendChild(hub);

    const n = keys.length;
    const nodes = keys.map((key, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const x = CX + R * Math.cos(angle);
      const y = CY + R * Math.sin(angle);
      return { key, x, y };
    });

    nodes.forEach((node) => {
      const line = document.createElementNS(SVG_NS, 'line');
      line.setAttribute('class', 'const-link');
      line.setAttribute('x1', CX); line.setAttribute('y1', CY);
      line.setAttribute('x2', node.x); line.setAttribute('y2', node.y);
      line.dataset.key = node.key;
      constLinesG.appendChild(line);

      const meta = RESOURCE_META[node.key];
      const s = 0.72; const off = 12 * s;
      const g = document.createElementNS(SVG_NS, 'g');
      g.setAttribute('class', 'const-node');
      g.dataset.key = node.key;
      g.innerHTML = `
        <circle class="const-node-circle" cx="${node.x}" cy="${node.y}" r="21"></circle>
        <g class="const-node-icon" transform="translate(${node.x - off},${node.y - off}) scale(${s})">${meta.icon}</g>
        <text class="const-node-label" x="${node.x}" y="${node.y + 34}" text-anchor="middle">${meta.label}</text>
      `;
      constNodesG.appendChild(g);
    });

    return nodes;
  }

  function addLogLine(text, done = false) {
    const line = document.createElement('div');
    line.className = 'build-log-line' + (done ? ' log-done' : '');
    line.innerHTML = `<span class="log-dot"></span><span>${text}</span>`;
    buildLog.appendChild(line);
    while (buildLog.children.length > 5) buildLog.removeChild(buildLog.firstChild);
    return line;
  }

  function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

  async function playConstellation(keys) {
    buildConstellation(keys);
    addLogLine('Validating application spec');
    await sleep(420);

    for (const key of keys) {
      const node = constNodesG.querySelector(`.const-node[data-key="${key}"]`);
      const link = constLinesG.querySelector(`.const-link[data-key="${key}"]`);
      link.classList.add('drawing');
      node.classList.add('active');
      const line = addLogLine(RESOURCE_META[key].log);
      await sleep(430);
      link.classList.remove('drawing'); link.classList.add('drawn');
      node.classList.remove('active'); node.classList.add('done');
      line.classList.add('log-done');
    }
    addLogLine('Finalizing manifests');
  }

  /* ============================================================
     PREDICTING RESOURCES (drives the animation, purely visual)
     ============================================================ */
  function predictFormResources(payload) {
    const keys = ['DEPLOYMENT'];
    if (payload.ports && payload.ports.length) keys.push('SERVICE');
    if (payload.env && payload.env.length) keys.push('CONFIGMAP');
    if (payload.secrets && payload.secrets.length) keys.push('SECRET');
    if (payload.storage && payload.storage.enabled) keys.push('PVC');
    if (payload.ingress && payload.ingress.enabled) keys.push('INGRESS');
    if (payload.hpa && payload.hpa.enabled) keys.push('HPA');
    return keys;
  }
  function predictComposeResources(payload) {
    const keys = ['DEPLOYMENT', 'SERVICE', 'CONFIGMAP'];
    if (payload.enable_ingress) keys.push('INGRESS');
    if (payload.enable_hpa) keys.push('HPA');
    return keys;
  }

  /* ============================================================
     COLLECT PAYLOADS
     ============================================================ */
  function val(id) { return document.getElementById(id).value; }
  function num(id) { return Number(document.getElementById(id).value); }
  function chk(id) { return document.getElementById(id).checked; }

  function collectFormPayload() {
    const ports = readRows(portsList, ['container_port', 'service_port', 'protocol']).map((p) => ({
      container_port: Number(p.container_port), service_port: Number(p.service_port), protocol: p.protocol,
    }));
    const env = readRows(envList, ['key', 'value']);
    const secrets = readRows(secretsList, ['key', 'value']);

    const payload = {
      app_name: val('f_app_name').trim(),
      namespace: val('f_namespace').trim() || 'default',
      image: val('f_image').trim(),
      image_pull_policy: val('f_pull_policy'),
      replicas: num('f_replicas') || 1,
      ports,
      service_type: val('f_service_type'),
      env,
      secrets,
      resources: {
        cpu_request: val('f_cpu_request').trim() || null,
        cpu_limit: val('f_cpu_limit').trim() || null,
        memory_request: val('f_mem_request').trim() || null,
        memory_limit: val('f_mem_limit').trim() || null,
      },
      storage: null,
      readiness_probe: null,
      liveness_probe: null,
      ingress: null,
      hpa: null,
      output_format: document.getElementById('f_output_format').dataset.value,
    };

    if (chk('f_storage_enabled')) {
      payload.storage = {
        enabled: true,
        pvc_name: val('f_pvc_name').trim() || null,
        storage_size: val('f_storage_size').trim() || null,
        mount_path: val('f_mount_path').trim() || null,
        access_mode: val('f_access_mode'),
      };
    }
    if (chk('f_readiness_enabled')) {
      payload.readiness_probe = {
        enabled: true,
        path: val('f_readiness_path').trim() || null,
        port: val('f_readiness_port') ? Number(val('f_readiness_port')) : null,
        initial_delay_seconds: num('f_readiness_delay') || 10,
        period_seconds: num('f_readiness_period') || 10,
      };
    }
    if (chk('f_liveness_enabled')) {
      payload.liveness_probe = {
        enabled: true,
        path: val('f_liveness_path').trim() || null,
        port: val('f_liveness_port') ? Number(val('f_liveness_port')) : null,
        initial_delay_seconds: num('f_liveness_delay') || 10,
        period_seconds: num('f_liveness_period') || 10,
      };
    }
    if (chk('f_ingress_enabled')) {
      payload.ingress = {
        enabled: true,
        host: val('f_ingress_host').trim() || null,
        path: val('f_ingress_path').trim() || '/',
        tls_enabled: chk('f_ingress_tls'),
      };
    }
    if (chk('f_hpa_enabled')) {
      payload.hpa = {
        enabled: true,
        min_replicas: num('f_hpa_min') || 1,
        max_replicas: num('f_hpa_max') || 5,
        target_cpu_utilization_percentage: num('f_hpa_cpu') || 80,
      };
    }
    return payload;
  }

  function collectComposePayload() {
    return {
      namespace: val('c_namespace').trim() || 'default',
      output_format: document.getElementById('c_output_format').dataset.value,
      override_service_type: val('c_service_type'),
      enable_ingress: chk('c_enable_ingress'),
      enable_hpa: chk('c_enable_hpa'),
    };
  }

  function validateFormPayload(p) {
    if (!p.app_name) return 'Application name is required.';
    if (!p.image) return 'Container image is required.';
    if (p.replicas < 1) return 'Replicas must be at least 1.';
    return null;
  }

  /* ============================================================
     API CALL
     ============================================================ */
  async function submitGeneration(mode, payload, file) {
    const url = `/yaml-generator/generate`;

    const form = new FormData();
    form.append('mode', mode);
    form.append('data', JSON.stringify(payload));
    if (file) form.append('compose_file', file);

    const headers = {};

    const res = await fetch(url, { method: 'POST', credentials: 'include', headers, body: form });
    if (!res.ok) {
      let detail = `Request failed with status ${res.status}`;
      try { const err = await res.json(); if (err.detail) detail = err.detail; } catch { /* ignore */ }
      throw new Error(detail);
    }
    return res.json();
  }

  async function runGeneration(mode) {
    let payload, file = null, predicted;

    if (mode === 'form') {
      payload = collectFormPayload();
      const err = validateFormPayload(payload);
      if (err) { showToast(err, 'error'); return; }
      predicted = predictFormResources(payload);
    } else {
      if (!composeFile) { showToast('Choose a docker-compose file first.', 'error'); return; }
      payload = collectComposePayload();
      file = composeFile;
      predicted = predictComposeResources(payload);
    }

    showPanel(loadingState);
    const minAnimation = playConstellation(predicted);
    const requestPromise = submitGeneration(mode, payload, file).catch((e) => ({ __error: e }));

    const [, result] = await Promise.all([minAnimation, requestPromise]);

    if (result && result.__error) {
      renderError(result.__error.message || 'Could not reach the API.');
      return;
    }
    renderResults(result);
  }

  document.getElementById('generateFormBtn').addEventListener('click', () => runGeneration('form'));
  document.getElementById('generateComposeBtn').addEventListener('click', () => runGeneration('compose'));

  function renderError(message) {
    document.getElementById('errorMessage').textContent = message;
    showPanel(errorState);
  }
  document.getElementById('errorRetryBtn').addEventListener('click', () => showPanel(emptyState));

  /* ============================================================
     YAML SYNTAX HIGHLIGHT
     ============================================================ */
  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function highlightYaml(text) {
    return text.split('\n').map((line) => {
      const escaped = escapeHtml(line);
      const trimmed = escaped.trim();
      if (trimmed.startsWith('#')) return `<span class="tok-cmt">${escaped}</span>`;
      if (trimmed === '---') return `<span class="tok-pun">${escaped}</span>`;

      const m = escaped.match(/^(\s*(?:-\s+)?)([A-Za-z0-9_.\-\/]+)(:)(\s*)(.*)$/);
      if (m) {
        const [, indent, key, colon, gap, rest] = m;
        let restHtml = rest;
        if (/^["'].*["']$/.test(rest)) restHtml = `<span class="tok-str">${rest}</span>`;
        else if (/^-?\d+(\.\d+)?$/.test(rest)) restHtml = `<span class="tok-num">${rest}</span>`;
        else if (/^(true|false|null)$/.test(rest)) restHtml = `<span class="tok-kw">${rest}</span>`;
        else if (rest.startsWith('#')) restHtml = `<span class="tok-cmt">${rest}</span>`;
        else if (rest) restHtml = `<span class="tok-str">${rest}</span>`;
        const dashPart = indent.includes('-') ? indent.replace('-', '<span class="tok-dash">-</span>') : indent;
        return `${dashPart}<span class="tok-key">${key}</span><span class="tok-pun">${colon}</span>${gap}${restHtml}`;
      }
      const dashOnly = escaped.match(/^(\s*)-(\s+)(.*)$/);
      if (dashOnly) {
        const [, indent, gap, rest] = dashOnly;
        return `${indent}<span class="tok-dash">-</span>${gap}<span class="tok-str">${rest}</span>`;
      }
      return escaped;
    }).join('\n');
  }

  /* ============================================================
     RENDER RESULTS
     ============================================================ */
  let currentFiles = [];
  let activeFileIndex = 0;

  const validationBadge = document.getElementById('validationBadge');
  const namespaceBadge = document.getElementById('namespaceBadge');
  const countBadge = document.getElementById('countBadge');
  const summaryText = document.getElementById('summaryText');
  const resourcePillsEl = document.getElementById('resourcePills');
  const fileTabsEl = document.getElementById('fileTabs');
  const yamlCodeEl = document.getElementById('yamlCode')?.querySelector('code') || document.getElementById('yamlCode');
 
  function renderResults(data) {
    currentFiles = data.files || [];
    activeFileIndex = 0;

    const summary = data.summary || {};
    namespaceBadge.textContent = `ns/${summary.namespace || 'default'}`;
    countBadge.textContent = `${(data.resources || []).length} resource${(data.resources || []).length === 1 ? '' : 's'}`;
    validationBadge.innerHTML = summary.validation_passed
      ? '<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg> Validated'
      : '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/></svg> Check warnings';
    summaryText.textContent = summary.summary || '';

    // Resource pills
    resourcePillsEl.innerHTML = '';
    (data.resources || []).forEach((r) => {
      const meta = KIND_TO_META[r.kind] || { color: '#a1a1aa', label: r.kind };
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'resource-pill';
      pill.innerHTML = `<span class="rk-dot" style="background:${meta.color}"></span>${meta.label} · ${r.name}`;
      pill.addEventListener('click', () => {
        const idx = currentFiles.findIndex((f) => f.filename === r.filename);
        if (idx >= 0) selectFile(idx);
      });
      resourcePillsEl.appendChild(pill);
    });

    // File tabs
    fileTabsEl.innerHTML = '';
    currentFiles.forEach((f, i) => {
      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'file-tab';
      tab.textContent = f.filename;
      tab.addEventListener('click', () => selectFile(i));
      fileTabsEl.appendChild(tab);
    });

    selectFile(0);
    showPanel(resultsState);
    showToast('Manifests generated', 'success');
  }

  function selectFile(idx) {
    if (!currentFiles.length) return;
    activeFileIndex = idx;
    Array.from(fileTabsEl.children).forEach((tab, i) => tab.classList.toggle('active', i === idx));
    Array.from(resourcePillsEl.children).forEach((p) => p.classList.remove('active'));
    yamlCodeEl.innerHTML = highlightYaml(currentFiles[idx].content);
  }

  /* Copy / Download */
  document.getElementById('copyBtn').addEventListener('click', async () => {
    if (!currentFiles.length) return;
    try {
      await navigator.clipboard.writeText(currentFiles[activeFileIndex].content);
      showToast('Copied to clipboard', 'success');
    } catch {
      showToast('Could not copy — select and copy manually', 'error');
    }
  });

  function downloadBlob(filename, content) {
    const blob = new Blob([content], { type: 'text/yaml' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  document.getElementById('downloadFileBtn').addEventListener('click', () => {
    if (!currentFiles.length) return;
    const f = currentFiles[activeFileIndex];
    downloadBlob(f.filename, f.content);
    showToast(`Saved ${f.filename}`, 'success');
  });

  let jsZipLoading = null;
  function ensureJSZip() {
    if (window.JSZip) return Promise.resolve();
    if (jsZipLoading) return jsZipLoading;
    jsZipLoading = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
    return jsZipLoading;
  }

  document.getElementById('downloadAllBtn').addEventListener('click', async () => {
    if (!currentFiles.length) return;
    if (currentFiles.length === 1) {
      downloadBlob(currentFiles[0].filename, currentFiles[0].content);
      return;
    }
    try {
      await ensureJSZip();
      const zip = new window.JSZip();
      currentFiles.forEach((f) => zip.file(f.filename, f.content));
      const blob = await zip.generateAsync({ type: 'blob' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'kubernetes-manifests.zip';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      showToast('Downloaded all manifests', 'success');
    } catch {
      currentFiles.forEach((f) => downloadBlob(f.filename, f.content));
      showToast('Zipping unavailable — downloaded files individually', 'info');
    }
  });

})();