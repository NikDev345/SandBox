/**
 * ============================================================
 * ERROR EXPLAINER — Frontend logic
 * Vanilla JS. No frameworks, no dependencies beyond Font Awesome.
 * ============================================================
 */

(() => {
  'use strict';

  const THRESHOLD = 1500; // must mirror backend threshold behaviour

  /* ── Element refs ── */
  const errorInput = document.getElementById('errorInput');
  const codeInput = document.getElementById('codeInput');
  const errorCounter = document.getElementById('errorCounter');
  const codeCounter = document.getElementById('codeCounter');
  const errorFileStatus = document.getElementById('errorFileStatus');
  const codeFileStatus = document.getElementById('codeFileStatus');

  const explainBtn = document.getElementById('explainBtn');
  const explainBtnMobile = document.getElementById('explainBtnMobile');

  const resultSection = document.getElementById('resultSection');
  const emptyState = document.getElementById('emptyState');
  const resultTitle = document.getElementById('resultTitle');
  const resultExplanation = document.getElementById('resultExplanation');
  const resultCode = document.getElementById('resultCode');
  const codeCard = document.getElementById('codeCard');
  const copyCodeBtn = document.getElementById('copyCodeBtn');

  const shortcutsBtn = document.getElementById('shortcutsBtn');
  const shortcutsModal = document.getElementById('shortcutsModal');
  const closeShortcuts = document.getElementById('closeShortcuts');

  const toastContainer = document.getElementById('toastContainer');
  const mouseGlow = document.getElementById('mouseGlow');

  /* ── Auto-resize textareas ── */
  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 420) + 'px';
  }

  /* ── Char counter + threshold → collapse into a file chip ── */
  function wireField(textarea, counterEl, statusEl, chipEl, fileName) {
    let wasOverLimit = false;
    let collapseTimer = null;
    let manuallyExpanded = false; // true while the user clicked "edit" on the chip

    const sizeEl = chipEl.querySelector('.file-chip-size');

    function collapseToChip() {
      textarea.classList.add('collapsed');
      chipEl.classList.add('visible');
      statusEl.classList.remove('visible', 'leaving');
    }

    function expandFromChip(focus = true) {
      chipEl.classList.remove('visible');
      textarea.classList.remove('collapsed');
      autoResize(textarea);
      if (focus) textarea.focus();
    }

    function update() {
      const len = textarea.value.length;
      counterEl.textContent = `${len} / ${THRESHOLD}`;
      counterEl.classList.toggle('over-limit', len > THRESHOLD);

      const isOverLimit = len > THRESHOLD;
      sizeEl.textContent = `${len.toLocaleString()} chars`;

      if (isOverLimit && !wasOverLimit) {
        // Crossing into "large input" territory:
        // 1) show the "preparing .txt" animation briefly
        // 2) then collapse the textarea into the compact file chip
        counterEl.style.display = 'none';
        statusEl.classList.remove('leaving');
        statusEl.classList.add('visible');

        clearTimeout(collapseTimer);
        collapseTimer = setTimeout(() => {
          if (textarea.value.length > THRESHOLD && !manuallyExpanded) {
            collapseToChip();
          }
        }, 900); // matches the "preparing" animation duration
      } else if (!isOverLimit && wasOverLimit) {
        // Dropped back below threshold — restore the plain textarea
        clearTimeout(collapseTimer);
        counterEl.style.display = '';
        statusEl.classList.add('leaving');
        expandFromChip(false);
        setTimeout(() => statusEl.classList.remove('visible', 'leaving'), 260);
      } else if (isOverLimit) {
        counterEl.style.display = 'none';
      }

      wasOverLimit = isOverLimit;
      if (!textarea.classList.contains('collapsed')) autoResize(textarea);
    }

    textarea.addEventListener('input', update);

    // Re-collapse automatically when the user clicks away, if still oversized
    textarea.addEventListener('blur', () => {
      manuallyExpanded = false;
      if (textarea.value.length > THRESHOLD) collapseToChip();
    });

    chipEl.addEventListener('click', (e) => {
      const action = e.target.closest('.file-chip-btn')?.dataset.action;
      if (action === 'expand') {
        manuallyExpanded = true;
        expandFromChip(true);
      } else if (action === 'remove') {
        textarea.value = '';
        manuallyExpanded = false;
        expandFromChip(false);
        update();
      } else if (!action) {
        // Clicking the chip body (not a button) also opens it for editing
        manuallyExpanded = true;
        expandFromChip(true);
      }
    });

    update();
  }

  wireField(errorInput, errorCounter, errorFileStatus, document.getElementById('errorFileChip'), 'error.txt');
  wireField(codeInput, codeCounter, codeFileStatus, document.getElementById('codeFileChip'), 'source.txt');

  /* ── Toasts ── */
  function showToast(message, icon = 'fa-circle-check') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('removing');
      setTimeout(() => toast.remove(), 220);
    }, 2600);
  }

  /* ── Simulated API call ──
     Mirrors the backend's ErrorExplainerResponse schema:
     { title, explanation, code } */
  /* ── Real API call ── */
    async function simulateExplainRequest(errorText, codeText) {
    const response = await fetch('/error-explainer/explain', {
        method: 'POST',
        credentials: "include",
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify({
        error: errorText,
        code: codeText || null,
        }),
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return response.json();
    }

  /* ── Basic syntax highlighting for the code block ── */
  function highlight(code) {
    const escaped = code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    return escaped
      .replace(/(\/\/.*$)/gm, '<span class="tok-cmt">$1</span>')
      .replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="tok-str">$1</span>')
      .replace(
        /\b(const|let|var|function|return|if|else|throw|new|await|async|for|while|import|export|class|null|undefined|true|false)\b/g,
        '<span class="tok-kw">$1</span>'
      )
      .replace(/\b(\d+)\b/g, '<span class="tok-num">$1</span>');
  }

  /* ── Submit flow ── */
  let isSubmitting = false;

  async function handleExplain() {
    if (isSubmitting) return;

    const errorText = errorInput.value.trim();
    const codeText = codeInput.value.trim();

    if (!errorText) {
      errorInput.focus();
      errorInput.classList.add('shake');
      showToast('Please paste an error to explain', 'fa-triangle-exclamation');
      setTimeout(() => errorInput.classList.remove('shake'), 400);
      return;
    }

    isSubmitting = true;
    setLoadingState(true);

    try {
      const response = await simulateExplainRequest(errorText, codeText);
      renderResult(response);
    } catch (err) {
      showToast('Something went wrong. Please try again.', 'fa-circle-exclamation');
    } finally {
      isSubmitting = false;
      setLoadingState(false);
    }
  }

  function setLoadingState(loading) {
    [explainBtn, explainBtnMobile].forEach((btn) => {
      btn.classList.toggle('is-loading', loading);
      btn.disabled = loading;
    });
    errorInput.disabled = loading;
    codeInput.disabled = loading;
  }

  function renderResult(data) {
    resultTitle.textContent = data.title;
    resultExplanation.textContent = data.explanation;

    if (data.code) {
      resultCode.innerHTML = highlight(data.code);
      codeCard.hidden = false;
    } else {
      codeCard.hidden = true;
    }

    emptyState.hidden = true;
    resultSection.hidden = false;

    // Restart reveal animations
    resultSection.querySelectorAll('.result-card').forEach((card, i) => {
      card.style.animation = 'none';
      // Force reflow so the animation restarts
      void card.offsetWidth;
      card.style.animation = '';
    });

    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    showToast('Diagnosis ready', 'fa-circle-check');
  }

  /* ── Copy code ── */
  copyCodeBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(resultCode.textContent);
      copyCodeBtn.classList.add('copied');
      copyCodeBtn.innerHTML = '<i class="fa-solid fa-check"></i><span>Copied</span>';
      setTimeout(() => {
        copyCodeBtn.classList.remove('copied');
        copyCodeBtn.innerHTML = '<i class="fa-regular fa-copy"></i><span>Copy</span>';
      }, 1600);
    } catch (err) {
      showToast('Could not copy to clipboard', 'fa-circle-exclamation');
    }
  });

  /* ── Buttons ── */
  explainBtn.addEventListener('click', handleExplain);
  explainBtnMobile.addEventListener('click', handleExplain);

  /* ── Keyboard shortcuts ── */
  document.addEventListener('keydown', (e) => {
    const isCtrlEnter = (e.ctrlKey || e.metaKey) && e.key === 'Enter';
    if (isCtrlEnter) {
      e.preventDefault();
      handleExplain();
    }
    if (e.key === 'Escape') {
      shortcutsModal.classList.add('hidden');
    }
  });

  /* ── Shortcuts modal ── */
  shortcutsBtn.addEventListener('click', () => shortcutsModal.classList.remove('hidden'));
  closeShortcuts.addEventListener('click', () => shortcutsModal.classList.add('hidden'));
  shortcutsModal.addEventListener('click', (e) => {
    if (e.target === shortcutsModal) shortcutsModal.classList.add('hidden');
  });

  /* ── Mouse glow ── */
  window.addEventListener('mousemove', (e) => {
    mouseGlow.style.opacity = '1';
    mouseGlow.style.left = e.clientX + 'px';
    mouseGlow.style.top = e.clientY + 'px';
  });
  window.addEventListener('mouseleave', () => {
    mouseGlow.style.opacity = '0';
  });

  /* ── Header scroll shadow ── */
  const header = document.querySelector('.app-header');
  window.addEventListener('scroll', () => {
    header.style.boxShadow = window.scrollY > 8 ? '0 8px 24px rgba(0,0,0,0.3)' : 'none';
  });

  /* ── Ambient particle field ── */
  (function initParticles() {
    const canvas = document.getElementById('particleCanvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    let width, height;

    function resize() {
      width = canvas.width = canvas.offsetWidth;
      height = canvas.height = canvas.offsetHeight;
    }

    function createParticles() {
      const count = Math.min(50, Math.floor((width * height) / 26000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 1.6 + 0.4,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        hue: [59, 139, 34][Math.floor(Math.random() * 3)],
        alpha: Math.random() * 0.35 + 0.08,
      }));
    }

    function tick() {
      ctx.clearRect(0, 0, width, height);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.hue === 59 ? '96,165,250' : p.hue === 139 ? '167,139,250' : '103,232,249'}, ${p.alpha})`;
        ctx.fill();
      });
      requestAnimationFrame(tick);
    }

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) return;

    window.addEventListener('resize', () => {
      resize();
      createParticles();
    });

    resize();
    createParticles();
    tick();
  })();

  /* ── Shake animation (added dynamically to avoid unused CSS bloat) ── */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fieldShake {
      0%, 100% { transform: translateX(0); }
      20%, 60% { transform: translateX(-6px); }
      40%, 80% { transform: translateX(6px); }
    }
    .shake { animation: fieldShake 340ms ease-in-out; border-color: var(--error) !important; }
  `;
  document.head.appendChild(style);
})();