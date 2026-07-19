/**
 * blog_outline_generator.js
 * Production-grade Blog Outline Generator for SandBox AI SaaS Platform
 * ─────────────────────────────────────────────────────────────
 * Works with: blog_outline_generator.html + blog_outline_generator.css
 * API: POST /blog-outline-generator/generate  (application/json)
 */

(() => {
  'use strict';

  // ─────────────────────────────────────────────────────────────
  // CONSTANTS
  // ─────────────────────────────────────────────────────────────

  const API_ENDPOINT = '/blog-outline-generator/generate';
  const MAX_TOPIC_LENGTH = 300;
  const MIN_TOPIC_LENGTH = 3;
  const ROTATOR_INTERVAL_MS = 2000;
  const LOADING_STEP_INTERVAL_MS = 1800;

  const LOADING_STEPS = [
    'Analyzing topic...',
    'Researching structure...',
    'Finding search intent...',
    'Generating outline...',
    'Optimizing SEO...',
    'Preparing final response...',
  ];

  // ─────────────────────────────────────────────────────────────
  // STATE
  // ─────────────────────────────────────────────────────────────

  const state = {
    isGenerating: false,
    rotatorTimer: null,
    loadingTimer: null,
    loadingIndex: 0,
    lastOutline: '',
  };

  // ─────────────────────────────────────────────────────────────
  // DOM CACHE
  // ─────────────────────────────────────────────────────────────

  let dom = {};

  const cacheDOM = () => {
    dom = {
      rotatorTrack: document.getElementById('bog-rotator-track'),

      topicInput: document.getElementById('bog-topic-input'),
      charCount: document.getElementById('bog-char-count'),
      errorMsg: document.getElementById('bog-error-msg'),

      generateBtn: document.getElementById('bog-generate-btn'),

      loadingBox: document.getElementById('bog-loading'),
      loadingText: document.getElementById('bog-loading-text'),

      outputCard: document.getElementById('bog-output-card'),
      outputBody: document.getElementById('bog-output-body'),
      copyBtn: document.getElementById('bog-copy-btn'),
      clearBtn: document.getElementById('bog-clear-btn'),

      examplesGrid: document.getElementById('bog-examples-grid'),
      inputCard: document.getElementById('bog-input-card'),
    };
  };

  // ─────────────────────────────────────────────────────────────
  // HERO ROTATOR
  // ─────────────────────────────────────────────────────────────

  const initRotator = () => {
    const track = dom.rotatorTrack;
    if (!track) return;

    const words = track.querySelectorAll('.bog-rotator-word');
    if (!words.length) return;

    let index = 0;
    words[0].classList.add('bog-rotator-word--active');

    state.rotatorTimer = setInterval(() => {
      words[index].classList.remove('bog-rotator-word--active');
      index = (index + 1) % words.length;
      words[index].classList.add('bog-rotator-word--active');
    }, ROTATOR_INTERVAL_MS);
  };

  // ─────────────────────────────────────────────────────────────
  // VALIDATION
  // ─────────────────────────────────────────────────────────────

  const showError = (message) => {
    dom.errorMsg.textContent = message;
    dom.errorMsg.hidden = false;
    dom.topicInput.classList.add('bog-invalid');
    dom.topicInput.setAttribute('aria-invalid', 'true');
  };

  const clearError = () => {
    dom.errorMsg.hidden = true;
    dom.errorMsg.textContent = '';
    dom.topicInput.classList.remove('bog-invalid');
    dom.topicInput.removeAttribute('aria-invalid');
  };

  const validateTopic = (value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      showError('Please enter a topic before generating an outline.');
      return null;
    }
    if (trimmed.length < MIN_TOPIC_LENGTH) {
      showError(`Topic must be at least ${MIN_TOPIC_LENGTH} characters.`);
      return null;
    }
    if (trimmed.length > MAX_TOPIC_LENGTH) {
      showError(`Topic must be under ${MAX_TOPIC_LENGTH} characters.`);
      return null;
    }
    clearError();
    return trimmed;
  };

  // ─────────────────────────────────────────────────────────────
  // LOADING STATE
  // ─────────────────────────────────────────────────────────────

  const startLoadingSteps = () => {
    state.loadingIndex = 0;
    dom.loadingText.textContent = LOADING_STEPS[0];

    state.loadingTimer = setInterval(() => {
      state.loadingIndex = (state.loadingIndex + 1) % LOADING_STEPS.length;
      dom.loadingText.style.opacity = '0';
      setTimeout(() => {
        dom.loadingText.textContent = LOADING_STEPS[state.loadingIndex];
        dom.loadingText.style.opacity = '1';
      }, 200);
    }, LOADING_STEP_INTERVAL_MS);
  };

  const stopLoadingSteps = () => {
    if (state.loadingTimer) {
      clearInterval(state.loadingTimer);
      state.loadingTimer = null;
    }
  };

  const setGeneratingState = (isGenerating) => {
    state.isGenerating = isGenerating;

    dom.generateBtn.disabled = isGenerating;
    dom.generateBtn.classList.toggle('bog-btn--loading', isGenerating);
    dom.topicInput.disabled = isGenerating;

    dom.loadingBox.hidden = !isGenerating;

    if (isGenerating) {
      startLoadingSteps();
    } else {
      stopLoadingSteps();
    }
  };

  // ─────────────────────────────────────────────────────────────
  // MARKDOWN → HTML RENDERER
  // Lightweight, dependency-free renderer tuned for the outline
  // shape returned by the backend (headings, bold labels, lists,
  // blockquotes, tables, hr, inline links/code).
  // ─────────────────────────────────────────────────────────────

  const escapeHTML = (str) => {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  // Inline-level: bold, italic, inline code, links
  const renderInline = (text) => {
    let out = escapeHTML(text);

    // inline code `code`
    out = out.replace(/`([^`]+)`/g, '<code class="bog-md-code">$1</code>');

    // links [label](url)
    out = out.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a class="bog-md-link" href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );

    // bold **text** or __text__
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong class="bog-md-strong">$1</strong>');
    out = out.replace(/__([^_]+)__/g, '<strong class="bog-md-strong">$1</strong>');

    // italic *text* or _text_ (after bold is handled)
    out = out.replace(/\*([^*]+)\*/g, '<em class="bog-md-em">$1</em>');
    out = out.replace(/(^|[^\w])_([^_]+)_(?!\w)/g, '$1<em class="bog-md-em">$2</em>');

    return out;
  };

  const isTableSeparator = (line) => /^\s*\|?[\s:|-]+\|?\s*$/.test(line) && line.includes('-');

  const parseTableBlock = (lines, startIndex) => {
    const rows = [];
    let i = startIndex;

    const splitRow = (line) =>
      line
        .trim()
        .replace(/^\|/, '')
        .replace(/\|$/, '')
        .split('|')
        .map((cell) => cell.trim());

    while (i < lines.length && lines[i].trim().includes('|')) {
      if (!(i === startIndex + 1 && isTableSeparator(lines[i]))) {
        rows.push(splitRow(lines[i]));
      }
      i += 1;
    }

    if (rows.length === 0) return null;

    const header = rows[0];
    const body = rows.slice(1);

    let html = '<div class="bog-md-table-wrap"><table class="bog-md-table"><thead><tr>';
    header.forEach((cell) => {
      html += `<th>${renderInline(cell)}</th>`;
    });
    html += '</tr></thead><tbody>';
    body.forEach((row) => {
      html += '<tr>';
      row.forEach((cell) => {
        html += `<td>${renderInline(cell)}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table></div>';

    return { html, nextIndex: i };
  };

  const renderMarkdown = (markdown) => {
    const text = (markdown || '').replace(/\r\n/g, '\n');
    const lines = text.split('\n');

    let html = '';
    let i = 0;
    let listBuffer = null; // { type: 'ul' | 'ol', items: [] }

    const flushList = () => {
      if (!listBuffer) return;
      const tag = listBuffer.type;
      const cls = tag === 'ul' ? 'bog-md-ul' : 'bog-md-ol';
      html += `<${tag} class="${cls}">`;
      listBuffer.items.forEach((item) => {
        html += `<li class="bog-md-li">${renderInline(item)}</li>`;
      });
      html += `</${tag}>`;
      listBuffer = null;
    };

    while (i < lines.length) {
      const rawLine = lines[i];
      const line = rawLine.trim();

      if (line === '') {
        flushList();
        i += 1;
        continue;
      }

      // Table block
      if (
        line.includes('|') &&
        lines[i + 1] &&
        isTableSeparator(lines[i + 1])
      ) {
        flushList();
        const table = parseTableBlock(lines, i);
        if (table) {
          html += table.html;
          i = table.nextIndex;
          continue;
        }
      }

      // Horizontal rule
      if (/^(---+|\*\*\*+|___+)$/.test(line)) {
        flushList();
        html += '<hr class="bog-md-hr">';
        i += 1;
        continue;
      }

      // Headings
      const headingMatch = line.match(/^(#{1,4})\s+(.*)$/);
      if (headingMatch) {
        flushList();
        const level = headingMatch[1].length;
        const content = headingMatch[2].replace(/#+\s*$/, '').trim();
        html += `<h${level} class="bog-md-h${level}">${renderInline(content)}</h${level}>`;
        i += 1;
        continue;
      }

      // Blockquote (collect consecutive > lines)
      if (line.startsWith('>')) {
        flushList();
        const quoteLines = [];
        while (i < lines.length && lines[i].trim().startsWith('>')) {
          quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
          i += 1;
        }
        const paras = quoteLines
          .join('\n')
          .split(/\n{2,}/)
          .filter(Boolean)
          .map((p) => `<p>${renderInline(p.trim())}</p>`)
          .join('');
        html += `<blockquote class="bog-md-blockquote">${paras}</blockquote>`;
        continue;
      }

      // Unordered list item
      const ulMatch = line.match(/^[-*+]\s+(.*)$/);
      if (ulMatch) {
        if (!listBuffer || listBuffer.type !== 'ul') {
          flushList();
          listBuffer = { type: 'ul', items: [] };
        }
        listBuffer.items.push(ulMatch[1]);
        i += 1;
        continue;
      }

      // Ordered list item
      const olMatch = line.match(/^\d+[.)]\s+(.*)$/);
      if (olMatch) {
        if (!listBuffer || listBuffer.type !== 'ol') {
          flushList();
          listBuffer = { type: 'ol', items: [] };
        }
        listBuffer.items.push(olMatch[1]);
        i += 1;
        continue;
      }

      // Default: paragraph (merge consecutive plain lines)
      flushList();
      const paraLines = [line];
      i += 1;
      while (
        i < lines.length &&
        lines[i].trim() !== '' &&
        !/^(#{1,4})\s+/.test(lines[i].trim()) &&
        !/^[-*+]\s+/.test(lines[i].trim()) &&
        !/^\d+[.)]\s+/.test(lines[i].trim()) &&
        !lines[i].trim().startsWith('>') &&
        !/^(---+|\*\*\*+|___+)$/.test(lines[i].trim()) &&
        !(lines[i].includes('|') && lines[i + 1] && isTableSeparator(lines[i + 1]))
      ) {
        paraLines.push(lines[i].trim());
        i += 1;
      }
      html += `<p class="bog-md-p">${renderInline(paraLines.join(' '))}</p>`;
    }

    flushList();
    return html;
  };

  // ─────────────────────────────────────────────────────────────
  // OUTPUT RENDERING
  // ─────────────────────────────────────────────────────────────

  const renderOutline = (outlineText) => {
    const text = (outlineText || '').trim();

    dom.outputCard.hidden = false;

    if (!text) {
      dom.outputBody.innerHTML = '';
      dom.outputBody.textContent = 'No outline generated.';
      dom.outputBody.classList.add('bog-output-empty');
      state.lastOutline = '';
    } else {
      dom.outputBody.classList.remove('bog-output-empty');
      dom.outputBody.innerHTML = renderMarkdown(text);
      state.lastOutline = text;
    }

    scrollToOutput();
  };

  const renderErrorOutput = (message) => {
    dom.outputCard.hidden = false;
    dom.outputBody.innerHTML = '';
    dom.outputBody.textContent = message;
    dom.outputBody.classList.add('bog-output-empty');
    state.lastOutline = '';
    scrollToOutput();
  };

  const scrollToOutput = () => {
    dom.outputCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // ─────────────────────────────────────────────────────────────
  // API CALL
  // ─────────────────────────────────────────────────────────────

  const generateOutline = async () => {
    if (state.isGenerating) return;

    const topic = validateTopic(dom.topicInput.value);
    if (!topic) return;

    setGeneratingState(true);

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      renderOutline(data && data.outline);
    } catch (err) {
      renderErrorOutput(
        'Something went wrong while generating your outline. Please try again in a moment.'
      );
    } finally {
      setGeneratingState(false);
    }
  };

  // ─────────────────────────────────────────────────────────────
  // COPY / CLEAR
  // ─────────────────────────────────────────────────────────────

  const copyOutline = async () => {
    if (!state.lastOutline) return;

    try {
      await navigator.clipboard.writeText(state.lastOutline);
      flashCopyButton();
    } catch (err) {
      // Fallback for environments without Clipboard API access
      const textarea = document.createElement('textarea');
      textarea.value = state.lastOutline;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        flashCopyButton();
      } catch (fallbackErr) {
        // Silently ignore — copy is a non-critical enhancement
      }
      document.body.removeChild(textarea);
    }
  };

  const flashCopyButton = () => {
    const label = dom.copyBtn.querySelector('span');
    const original = label.textContent;
    dom.copyBtn.classList.add('bog-icon-btn--success');
    label.textContent = 'Copied!';

    setTimeout(() => {
      dom.copyBtn.classList.remove('bog-icon-btn--success');
      label.textContent = original;
    }, 1600);
  };

  const clearOutline = () => {
    dom.outputCard.hidden = true;
    dom.outputBody.innerHTML = '';
    dom.outputBody.classList.remove('bog-output-empty');
    state.lastOutline = '';
    dom.topicInput.value = '';
    updateCharCount();
    dom.topicInput.focus();
  };

  // ─────────────────────────────────────────────────────────────
  // EXAMPLE TOPICS
  // ─────────────────────────────────────────────────────────────

  const useExampleTopic = (topic) => {
    if (!topic) return;
    dom.topicInput.value = topic;
    updateCharCount();
    clearError();
    dom.inputCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    dom.topicInput.focus();
  };

  const initExamples = () => {
    if (!dom.examplesGrid) return;
    dom.examplesGrid.addEventListener('click', (e) => {
      const btn = e.target.closest('.bog-example');
      if (!btn) return;
      useExampleTopic(btn.dataset.topic || btn.querySelector('.bog-example-text')?.textContent);
    });
  };

  // ─────────────────────────────────────────────────────────────
  // CHAR COUNT
  // ─────────────────────────────────────────────────────────────

  const updateCharCount = () => {
    const len = dom.topicInput.value.length;
    dom.charCount.textContent = `${len} / ${MAX_TOPIC_LENGTH}`;
  };

  // ─────────────────────────────────────────────────────────────
  // EVENT BINDING
  // ─────────────────────────────────────────────────────────────

  const bindEvents = () => {
    dom.topicInput.addEventListener('input', () => {
      updateCharCount();
      if (!dom.errorMsg.hidden) clearError();
    });

    dom.topicInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        generateOutline();
      }
    });

    dom.generateBtn.addEventListener('click', generateOutline);
    dom.copyBtn.addEventListener('click', copyOutline);
    dom.clearBtn.addEventListener('click', clearOutline);
  };

  // ─────────────────────────────────────────────────────────────
  // INIT
  // ─────────────────────────────────────────────────────────────

  const init = () => {
    cacheDOM();
    bindEvents();
    initRotator();
    initExamples();
    updateCharCount();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();