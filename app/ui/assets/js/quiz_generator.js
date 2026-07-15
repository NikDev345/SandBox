/**
 * quiz_generator.js
 * Production-grade Quiz Generator for SandBox AI SaaS Platform
 * ─────────────────────────────────────────────────────────────
 * Works with: quiz_generator.html + quiz_generator.css + FastAPI backend
 * API: POST /quiz/generate  (multipart/form-data)
 */

(() => {
  'use strict';

  // ─────────────────────────────────────────────────────────────
  // CONSTANTS
  // ─────────────────────────────────────────────────────────────

  const API_ENDPOINT = '/quiz/generate';
  const MAX_FILE_BYTES = 20 * 1024 * 1024; // 20 MB
  const ACCEPTED_EXTS = ['.pdf', '.docx', '.pptx', '.txt', '.md'];
  const LOADING_STEP_INTERVAL_MS = 1800;
  const SCORE_ARC_CIRCUMFERENCE = 2 * Math.PI * 52; // r=52

  const SKILL_LEVELS = [
    { min: 90, label: 'Expert' },
    { min: 75, label: 'Advanced' },
    { min: 60, label: 'Proficient' },
    { min: 40, label: 'Learning' },
    { min: 0,  label: 'Beginner' },
  ];

  const QUESTION_TYPE_LABELS = {
    mcq:          'Multiple Choice',
    truefalse:    'True / False',
    fill_blank:   'Fill in the Blank',
    short_answer: 'Short Answer',
  };

  // ─────────────────────────────────────────────────────────────
  // STATE
  // ─────────────────────────────────────────────────────────────

  const state = {
    mode: 'document',         // 'document' | 'prompt'
    file: null,               // File object
    config: {
      question_count: 10,
      difficulty: 'medium',
      language: 'english',
      audience: 'school',
      include_explanations: true,
      include_hints: true,
      question_types: ['mcq'],
    },
    quiz: null,               // full backend response
    currentIndex: 0,
    answers: {},              // { questionIndex: 'A' | 'B' | 'C' | 'D' | string }
    startTime: null,          // Date.now() when quiz starts
    endTime: null,            // Date.now() when quiz submitted
    loadingStepTimer: null,
    rotatorTimer: null,
    rotatorIndex: 0,
  };

  // ─────────────────────────────────────────────────────────────
  // DOM CACHE
  // ─────────────────────────────────────────────────────────────

  let dom = {};

  const cacheDOM = () => {
    dom = {
      // Phases
      phaseInput:   document.getElementById('qg-phase-input'),
      phaseConfig:  document.getElementById('qg-phase-config'),
      phaseQuiz:    document.getElementById('qg-phase-quiz'),
      phaseResults: document.getElementById('qg-phase-results'),
      loadingOverlay: document.getElementById('qg-loading-overlay'),

      // Hero rotator
      rotatorTrack: document.getElementById('qg-rotator-track'),

      // Mode selector
      modeDoc:    document.getElementById('qg-mode-doc'),
      modePrompt: document.getElementById('qg-mode-prompt'),
      modePill:   document.getElementById('qg-mode-pill'),
      panelDoc:   document.getElementById('qg-panel-doc'),
      panelPrompt:document.getElementById('qg-panel-prompt'),

      // Upload zone
      uploadZone: document.getElementById('qg-upload-zone'),
      fileInput:  document.getElementById('qg-file-input'),
      uploadIdle: document.getElementById('qg-upload-idle'),
      uploadFile: document.getElementById('qg-upload-file'),
      fileName:   document.getElementById('qg-file-name'),
      fileSize:   document.getElementById('qg-file-size'),
      fileRemove: document.getElementById('qg-file-remove'),

      // Prompt
      promptInput: document.getElementById('qg-prompt-input'),
      charCount:   document.getElementById('qg-char-count'),

      // Input actions
      continueBtn: document.getElementById('qg-continue-btn'),

      // Config
      backBtn:       document.getElementById('qg-back-btn'),
      countSlider:   document.getElementById('qg-count-slider'),
      countValue:    document.getElementById('qg-count-value'),
      languageSelect:document.getElementById('qg-language-select'),
      generateBtn:   document.getElementById('qg-generate-btn'),
      loadingSteps:  document.getElementById('qg-loading-steps'),

      // Quiz
      quizCounter:     document.getElementById('qg-quiz-counter'),
      progressFill:    document.getElementById('qg-progress-fill'),
      progressBar:     document.querySelector('.qg-progress-bar'),
      questionCard:    document.getElementById('qg-question-card'),
      questionTypeBadge: document.getElementById('qg-question-type-badge'),
      questionText:    document.getElementById('qg-question-text'),
      optionsContainer:document.getElementById('qg-options'),
      prevBtn:         document.getElementById('qg-prev-btn'),
      skipBtn:         document.getElementById('qg-skip-btn'),
      nextBtn:         document.getElementById('qg-next-btn'),
      quitBtn:         document.getElementById('qg-quit-btn'),

      // Results
      scorePct:    document.getElementById('qg-score-pct'),
      scoreArc:    document.getElementById('qg-score-arc'),
      resultTitle: document.getElementById('qg-result-title'),
      resultSubtitle: document.getElementById('qg-result-subtitle'),
      statCorrect: document.getElementById('qg-stat-correct'),
      statWrong:   document.getElementById('qg-stat-wrong'),
      statSkip:    document.getElementById('qg-stat-skip'),
      statTime:    document.getElementById('qg-stat-time'),
      statAvg:     document.getElementById('qg-stat-avg'),
      statSkill:   document.getElementById('qg-stat-skill'),
      reviewList:  document.getElementById('qg-review-list'),
      retakeBtn:   document.getElementById('qg-retake-btn'),
      newQuizBtn:  document.getElementById('qg-new-quiz-btn'),
    };
  };

  // ─────────────────────────────────────────────────────────────
  // PHASE NAVIGATION
  // ─────────────────────────────────────────────────────────────

  const allPhases = () => [
    dom.phaseInput,
    dom.phaseConfig,
    dom.phaseQuiz,
    dom.phaseResults,
  ];

  const showPhase = (phase) => {
    allPhases().forEach(p => {
      const isTarget = p === phase;
      p.classList.toggle('qg-phase--hidden', !isTarget);
      p.removeAttribute('aria-hidden');
      if (!isTarget) p.setAttribute('aria-hidden', 'true');
    });
    phase.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // ─────────────────────────────────────────────────────────────
  // HERO ROTATOR
  // ─────────────────────────────────────────────────────────────

  const initRotator = () => {

    const track = dom.rotatorTrack;
    if (!track) return;

    const words = track.querySelectorAll(".qg-rotator-word");
    if (!words.length) return;

    let index = 0;

    words[0].classList.add("qg-rotator-word--active");

    state.rotatorTimer = setInterval(() => {

        words[index].classList.remove("qg-rotator-word--active");

        index = (index + 1) % words.length;

        track.style.transform = `translateY(-${index * 1.2}em)`;

        words[index].classList.add("qg-rotator-word--active");

    }, 1400);

};
  // ─────────────────────────────────────────────────────────────
  // MODE SWITCH
  // ─────────────────────────────────────────────────────────────

  const setMode = (mode) => {
    state.mode = mode;

    const isDoc = mode === 'document';

    dom.modeDoc.classList.toggle('qg-mode-btn--active', isDoc);
    dom.modePrompt.classList.toggle('qg-mode-btn--active', !isDoc);
    dom.modeDoc.setAttribute('aria-selected', String(isDoc));
    dom.modePrompt.setAttribute('aria-selected', String(!isDoc));

    dom.panelDoc.classList.toggle('qg-panel--hidden', !isDoc);
    dom.panelPrompt.classList.toggle('qg-panel--hidden', isDoc);

    // Animate pill
    const activeBtn = isDoc ? dom.modeDoc : dom.modePrompt;
    const pill = dom.modePill;
    pill.style.width  = `${activeBtn.offsetWidth}px`;
    pill.style.left   = `${activeBtn.offsetLeft}px`;

    updateContinueBtn();
  };

  // ─────────────────────────────────────────────────────────────
  // UPLOAD HANDLER
  // ─────────────────────────────────────────────────────────────

  const uploadHandler = (file) => {
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_EXTS.includes(ext)) {
      toast(`Unsupported file type. Please upload: ${ACCEPTED_EXTS.join(', ')}`, 'error');
      return;
    }

    if (file.size > MAX_FILE_BYTES) {
      toast('File too large. Maximum size is 20 MB.', 'error');
      return;
    }

    state.file = file;
    dom.fileName.textContent = file.name;
    dom.fileSize.textContent = formatBytes(file.size);
    dom.uploadIdle.hidden = true;
    dom.uploadFile.hidden = false;
    dom.uploadZone.classList.add('qg-upload-zone--has-file');
    updateContinueBtn();
  };

  const clearUpload = () => {
    state.file = null;
    dom.fileInput.value = '';
    dom.uploadIdle.hidden = false;
    dom.uploadFile.hidden = true;
    dom.uploadZone.classList.remove('qg-upload-zone--has-file');
    updateContinueBtn();
  };

  // ─────────────────────────────────────────────────────────────
  // CONTINUE BUTTON STATE
  // ─────────────────────────────────────────────────────────────

  const updateContinueBtn = () => {
    const ready = state.mode === 'document'
      ? !!state.file
      : dom.promptInput.value.trim().length > 0;

    dom.continueBtn.disabled = !ready;
    dom.continueBtn.setAttribute('aria-disabled', String(!ready));
  };

  // ─────────────────────────────────────────────────────────────
  // LOADING OVERLAY
  // ─────────────────────────────────────────────────────────────

  const showLoading = () => {
    dom.loadingOverlay.hidden = false;
    dom.loadingOverlay.removeAttribute('aria-hidden');

    // Reset steps
    const steps = dom.loadingSteps.querySelectorAll('.qg-step');
    steps.forEach(s => {
      s.classList.remove('qg-step--active', 'qg-step--done');
    });

    let currentStep = 0;
    steps[0]?.classList.add('qg-step--active');

    state.loadingStepTimer = setInterval(() => {
      steps[currentStep]?.classList.replace('qg-step--active', 'qg-step--done');
      currentStep++;
      if (currentStep < steps.length) {
        steps[currentStep].classList.add('qg-step--active');
      } else {
        clearInterval(state.loadingStepTimer);
      }
    }, LOADING_STEP_INTERVAL_MS);
  };

  const hideLoading = () => {
    clearInterval(state.loadingStepTimer);
    dom.loadingOverlay.hidden = true;
    dom.loadingOverlay.setAttribute('aria-hidden', 'true');
  };

  // ─────────────────────────────────────────────────────────────
  // GENERATE QUIZ — API CALL
  // ─────────────────────────────────────────────────────────────

  const generateQuiz = async () => {
    const formData = buildFormData();
    if (!formData) return;

    showLoading();
    dom.generateBtn.disabled = true;

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data?.detail || data?.message || `Server error ${response.status}`);
      }

      state.quiz = data;
      state.currentIndex = 0;
      state.answers = {};
      state.startTime = Date.now();
      state.endTime = null;

      hideLoading();
      showPhase(dom.phaseQuiz);
      renderQuestion(0);

    } catch (err) {
      hideLoading();
      console.error('[QuizGenerator] API error:', err);
      toast(err.message || 'Failed to generate quiz. Please try again.', 'error');
    } finally {
      dom.generateBtn.disabled = false;
    }
  };

  const buildFormData = () => {
    const fd = new FormData();
    const cfg = state.config;

    if (state.mode === 'document') {
      if (!state.file) {
        toast('Please upload a document first.', 'error');
        return null;
      }
      fd.append('input_type', 'document');
      fd.append('file', state.file);
    } else {
      const prompt = dom.promptInput.value.trim();
      if (!prompt) {
        toast('Please enter a prompt.', 'error');
        return null;
      }
      fd.append('input_type', 'prompt');
      fd.append('prompt', prompt);
    }

    fd.append('question_count',        String(cfg.question_count));
    fd.append('difficulty',            cfg.difficulty);
    fd.append('language',              cfg.language);
    fd.append('audience',              cfg.audience);
    fd.append('include_explanations',  String(cfg.include_explanations));
    fd.append('include_hints',         String(cfg.include_hints));

    // question_types as repeated field
    cfg.question_types.forEach(t => fd.append('question_types', t));

    return fd;
  };

  // ─────────────────────────────────────────────────────────────
  // QUIZ RENDERING
  // ─────────────────────────────────────────────────────────────

  const questions = () => state.quiz?.questions ?? [];
  const total = () => questions().length;

  const renderQuestion = (index) => {
    const q = questions()[index];
    if (!q) return;

    state.currentIndex = index;

    const pct = ((index + 1) / total()) * 100;
    dom.progressFill.style.width = `${pct}%`;
    dom.progressBar.setAttribute('aria-valuenow', String(Math.round(pct)));

    dom.quizCounter.textContent = `Question ${index + 1} of ${total()}`;
    dom.questionTypeBadge.textContent = QUESTION_TYPE_LABELS[q.question_type] ?? q.question_type;
    dom.questionText.textContent = q.question;

    // Animate card in
    dom.questionCard.classList.remove('qg-question-card--enter');
    void dom.questionCard.offsetWidth; // reflow
    dom.questionCard.classList.add('qg-question-card--enter');

    renderOptions(q, index);
    updateNavButtons(index);
  };

  const renderOptions = (question, index) => {
    dom.optionsContainer.innerHTML = '';

    const selectedId = state.answers[index] ?? null;

    const renderers = {
      mcq:          renderMCQOptions,
      truefalse:    renderTrueFalseOptions,
      fill_blank:   renderFillBlankOption,
      short_answer: renderShortAnswerOption,
    };

    const renderer = renderers[question.question_type] ?? renderMCQOptions;
    renderer(question, index, selectedId);
  };

  // MCQ
  const renderMCQOptions = (question, index, selectedId) => {
    question.options?.forEach((option) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'qg-option';
      btn.dataset.optionId = option.id;
      btn.setAttribute('role', 'radio');
      btn.setAttribute('aria-checked', String(option.id === selectedId));
      btn.setAttribute('aria-label', `Option ${option.id}: ${option.text}`);

      if (option.id === selectedId) btn.classList.add('qg-option--selected');

      btn.innerHTML = `
        <span class="qg-option-key" aria-hidden="true">${option.id}</span>
        <span class="qg-option-text">${escapeHTML(option.text)}</span>
      `;

      btn.addEventListener('click', () => selectOption(option.id, index));
      dom.optionsContainer.appendChild(btn);
    });
  };

  // True / False
  const renderTrueFalseOptions = (question, index, selectedId) => {
    const tfOptions = question.options?.length
      ? question.options
      : [{ id: 'A', text: 'True' }, { id: 'B', text: 'False' }];

    renderMCQOptions({ ...question, options: tfOptions }, index, selectedId);
  };

  // Fill in the blank
  const renderFillBlankOption = (question, index, selectedId) => {
    const wrap = document.createElement('div');
    wrap.className = 'qg-text-answer-wrap';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'qg-text-input';
    input.placeholder = 'Type your answer…';
    input.setAttribute('aria-label', 'Fill in the blank answer');
    input.value = selectedId ?? '';

    input.addEventListener('input', () => {
      state.answers[index] = input.value.trim();
      updateNavButtons(index);
    });

    wrap.appendChild(input);
    dom.optionsContainer.appendChild(wrap);
  };

  // Short Answer
  const renderShortAnswerOption = (question, index, selectedId) => {
    const wrap = document.createElement('div');
    wrap.className = 'qg-text-answer-wrap';

    const textarea = document.createElement('textarea');
    textarea.className = 'qg-text-input qg-text-input--area';
    textarea.placeholder = 'Write your answer here…';
    textarea.rows = 4;
    textarea.setAttribute('aria-label', 'Short answer');
    textarea.value = selectedId ?? '';

    textarea.addEventListener('input', () => {
      state.answers[index] = textarea.value.trim();
      updateNavButtons(index);
    });

    wrap.appendChild(textarea);
    dom.optionsContainer.appendChild(wrap);
  };

  // ─────────────────────────────────────────────────────────────
  // OPTION SELECTION
  // ─────────────────────────────────────────────────────────────

  const selectOption = (optionId, index) => {
    state.answers[index] = optionId;

    dom.optionsContainer.querySelectorAll('.qg-option').forEach(btn => {
      const isSelected = btn.dataset.optionId === optionId;
      btn.classList.toggle('qg-option--selected', isSelected);
      btn.setAttribute('aria-checked', String(isSelected));
    });

    updateNavButtons(index);
  };

  // ─────────────────────────────────────────────────────────────
  // NAVIGATION
  // ─────────────────────────────────────────────────────────────

  const updateNavButtons = (index) => {
    const hasAnswer = state.answers[index] != null && state.answers[index] !== '';
    const isFirst   = index === 0;
    const isLast    = index === total() - 1;

    dom.prevBtn.disabled = isFirst;
    dom.nextBtn.disabled = !hasAnswer;
    dom.nextBtn.textContent = isLast ? 'Submit' : 'Next';
    dom.nextBtn.innerHTML = isLast
      ? 'Submit <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4"/></svg>'
      : 'Next <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3l5 5-5 5"/></svg>';
    dom.skipBtn.style.display = hasAnswer ? 'none' : '';
  };

  const goNext = () => {
    const index = state.currentIndex;
    const isLast = index === total() - 1;

    if (isLast) {
      submitQuiz();
      return;
    }

    renderQuestion(index + 1);
  };

  const goPrevious = () => {
    if (state.currentIndex === 0) return;
    renderQuestion(state.currentIndex - 1);
  };

  const skipQuestion = () => {
    // Leave answer as undefined (skipped)
    const isLast = state.currentIndex === total() - 1;
    if (isLast) {
      submitQuiz();
      return;
    }
    renderQuestion(state.currentIndex + 1);
  };

  // ─────────────────────────────────────────────────────────────
  // SUBMIT
  // ─────────────────────────────────────────────────────────────

  const submitQuiz = () => {
    state.endTime = Date.now();
    const results = calculateResults();
    showPhase(dom.phaseResults);
    renderResults(results);
    renderReview(results);
  };

  // ─────────────────────────────────────────────────────────────
  // CALCULATE RESULTS
  // ─────────────────────────────────────────────────────────────

  const calculateResults = () => {
    const qs = questions();
    let correct = 0;
    let wrong   = 0;
    let skipped = 0;

    const reviewed = qs.map((q, i) => {
      const userAnswerId = state.answers[i] ?? null;
      const isSkipped = userAnswerId === null || userAnswerId === '';

      // For MCQ / T-F: compare option id
      // For text types: compare trimmed strings (case-insensitive)
      let isCorrect = false;
      if (!isSkipped) {
        if (q.question_type === 'mcq' || q.question_type === 'truefalse') {
          isCorrect = q.correct_answers?.includes(userAnswerId) ?? false;
        } else {
          // Short answer / fill blank: lenient match
          const normalized = (str) => str?.toLowerCase().trim() ?? '';
          isCorrect = q.correct_answers?.some(
            ans => normalized(ans) === normalized(userAnswerId)
          ) ?? false;
        }
      }

      if (isSkipped) skipped++;
      else if (isCorrect) correct++;
      else wrong++;

      return { question: q, index: i, userAnswerId, isCorrect, isSkipped };
    });

    const totalQ    = qs.length;
    const score     = totalQ > 0 ? Math.round((correct / totalQ) * 100) : 0;
    const elapsed   = Math.round(((state.endTime - state.startTime) / 1000));
    const avgPerQ   = totalQ > 0 ? Math.round(elapsed / totalQ) : 0;
    const skillLevel = SKILL_LEVELS.find(s => score >= s.min)?.label ?? '—';

    return { correct, wrong, skipped, score, elapsed, avgPerQ, skillLevel, reviewed, totalQ };
  };

  // ─────────────────────────────────────────────────────────────
  // RENDER RESULTS
  // ─────────────────────────────────────────────────────────────

  const renderResults = (results) => {
    const { correct, wrong, skipped, score, elapsed, avgPerQ, skillLevel } = results;

    // Score ring
    const dashOffset = SCORE_ARC_CIRCUMFERENCE * (1 - score / 100);
    dom.scoreArc.style.strokeDasharray  = SCORE_ARC_CIRCUMFERENCE;
    dom.scoreArc.style.strokeDashoffset = SCORE_ARC_CIRCUMFERENCE;

    // Counter animations
    animateCounter(dom.scorePct,    0, score,   '%',  1200);
    animateCounter(dom.statCorrect, 0, correct, '',   900);
    animateCounter(dom.statWrong,   0, wrong,   '',   900);
    animateCounter(dom.statSkip,    0, skipped, '',   900);

    // After a brief pause, animate the arc
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        dom.scoreArc.style.transition = 'stroke-dashoffset 1.2s ease';
        dom.scoreArc.style.strokeDashoffset = dashOffset;
      });
    });

    dom.statTime.textContent  = formatTime(elapsed);
    dom.statAvg.textContent   = formatTime(avgPerQ);
    dom.statSkill.textContent = skillLevel;

    dom.resultTitle.textContent    = score >= 60 ? '🎉 Well Done!' : '📝 Keep Practising!';
    dom.resultSubtitle.textContent =
      `You scored ${correct} out of ${results.totalQ} — ${score}%`;
  };

  // ─────────────────────────────────────────────────────────────
  // RENDER REVIEW
  // ─────────────────────────────────────────────────────────────

  const renderReview = ({ reviewed }) => {
    dom.reviewList.innerHTML = '';

    reviewed.forEach(({ question: q, index, userAnswerId, isCorrect, isSkipped }) => {
      const li = document.createElement('li');
      li.className = [
        'qg-review-item',
        'metric-card',
        isSkipped  ? 'qg-review-item--skipped'
        : isCorrect ? 'qg-review-item--correct'
        :             'qg-review-item--wrong',
      ].join(' ');

      const correctOption = q.options?.find(o => q.correct_answers?.includes(o.id));
      const userOption    = q.options?.find(o => o.id === userAnswerId);

      const correctText = correctOption?.text ?? q.correct_answers?.join(', ') ?? '—';
      const userText    = isSkipped
        ? '<em>Skipped</em>'
        : (userOption?.text ?? escapeHTML(userAnswerId ?? '—'));

      const statusIcon  = isSkipped ? '—' : isCorrect ? '✓' : '✕';
      const statusClass = isSkipped ? 'skip' : isCorrect ? 'correct' : 'wrong';

      li.innerHTML = `
        <div class="qg-review-top">
          <span class="qg-review-num">${index + 1}</span>
          <span class="qg-review-status qg-review-status--${statusClass}" aria-label="${statusClass}">
            ${statusIcon}
          </span>
        </div>
        <p class="qg-review-question">${escapeHTML(q.question)}</p>
        <div class="qg-review-answers">
          <div class="qg-review-answer qg-review-answer--user">
            <span class="qg-review-answer-label">Your Answer</span>
            <span class="qg-review-answer-val">${userText}</span>
          </div>
          ${!isCorrect && !isSkipped ? `
          <div class="qg-review-answer qg-review-answer--correct">
            <span class="qg-review-answer-label">Correct Answer</span>
            <span class="qg-review-answer-val">${escapeHTML(correctText)}</span>
          </div>` : ''}
        </div>
        ${q.hint ? `
        <div class="qg-review-hint">
          <span class="qg-review-hint-label">💡 Hint</span>
          <span>${escapeHTML(q.hint)}</span>
        </div>` : ''}
        ${q.explanation ? `
        <div class="qg-review-explanation">
          <span class="qg-review-explanation-label">📖 Explanation</span>
          <p>${escapeHTML(q.explanation)}</p>
        </div>` : ''}
      `;

      dom.reviewList.appendChild(li);
    });
  };

  // ─────────────────────────────────────────────────────────────
  // RESET
  // ─────────────────────────────────────────────────────────────

  const resetQuiz = () => {
    state.quiz = null;
    state.currentIndex = 0;
    state.answers = {};
    state.startTime = null;
    state.endTime = null;

    // Reset score ring
    dom.scoreArc.style.transition = 'none';
    dom.scoreArc.style.strokeDashoffset = SCORE_ARC_CIRCUMFERENCE;
    dom.scoreArc.style.strokeDasharray  = SCORE_ARC_CIRCUMFERENCE;

    showPhase(dom.phaseInput);
  };

  const retakeQuiz = () => {
    if (!state.quiz) return;
    state.currentIndex = 0;
    state.answers = {};
    state.startTime = Date.now();
    state.endTime = null;

    // Reset score ring
    dom.scoreArc.style.transition = 'none';
    dom.scoreArc.style.strokeDashoffset = SCORE_ARC_CIRCUMFERENCE;
    dom.scoreArc.style.strokeDasharray  = SCORE_ARC_CIRCUMFERENCE;

    showPhase(dom.phaseQuiz);
    renderQuestion(0);
  };

  // ─────────────────────────────────────────────────────────────
  // KEYBOARD NAVIGATION
  // ─────────────────────────────────────────────────────────────

  const handleKeydown = (e) => {
    // Only active during quiz phase
    if (dom.phaseQuiz.classList.contains('qg-phase--hidden')) return;

    const q = questions()[state.currentIndex];
    if (!q) return;

    switch (e.key) {
      case 'ArrowRight':
      case 'Enter':
        if (!dom.nextBtn.disabled) goNext();
        break;
      case 'ArrowLeft':
        if (!dom.prevBtn.disabled) goPrevious();
        break;
      default:
        handleAlphaKey(e.key, q);
    }
  };

  const handleAlphaKey = (key, question) => {
    const num = parseInt(key, 10);
    const isMCQ = question.question_type === 'mcq' || question.question_type === 'truefalse';
    if (!isMCQ || isNaN(num)) return;

    const options = question.options ?? [];
    const option  = options[num - 1];
    if (option) selectOption(option.id, state.currentIndex);
  };

  // ─────────────────────────────────────────────────────────────
  // TOAST NOTIFICATIONS
  // ─────────────────────────────────────────────────────────────

  const toast = (message, type = 'info') => {
    const existing = document.getElementById('qg-toast-container');
    const container = existing ?? (() => {
      const el = document.createElement('div');
      el.id = 'qg-toast-container';
      el.className = 'qg-toast-container';
      el.setAttribute('role', 'alert');
      el.setAttribute('aria-live', 'assertive');
      document.body.appendChild(el);
      return el;
    })();

    const t = document.createElement('div');
    t.className = `qg-toast qg-toast--${type}`;
    t.textContent = message;
    container.appendChild(t);

    requestAnimationFrame(() => t.classList.add('qg-toast--visible'));

    setTimeout(() => {
      t.classList.remove('qg-toast--visible');
      t.addEventListener('transitionend', () => t.remove(), { once: true });
    }, 4000);
  };

  // ─────────────────────────────────────────────────────────────
  // HELPERS
  // ─────────────────────────────────────────────────────────────

  const formatBytes = (bytes) => {
    if (bytes < 1024)       return `${bytes} B`;
    if (bytes < 1024 ** 2)  return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return s === 0 ? `${m}m` : `${m}m ${s}s`;
  };

  const escapeHTML = (str) => {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  const animateCounter = (el, from, to, suffix = '', duration = 1000) => {
    const start = performance.now();
    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
      el.textContent = `${Math.round(from + (to - from) * ease)}${suffix}`;
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  // ─────────────────────────────────────────────────────────────
  // CONFIG CHIP / CARD GROUPS
  // ─────────────────────────────────────────────────────────────

  const initChipGroups = () => {
    // Single-select chip groups: difficulty
    document.querySelectorAll('.qg-chip[data-group]').forEach(btn => {
      btn.addEventListener('click', () => {
        const group = btn.dataset.group;
        document.querySelectorAll(`.qg-chip[data-group="${group}"]`).forEach(b => {
          b.classList.remove('qg-chip--active');
        });
        btn.classList.add('qg-chip--active');
        state.config[group] = btn.dataset.value;
      });
    });

    // Single-select audience cards
    document.querySelectorAll('.qg-audience-card[data-group]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.qg-audience-card').forEach(b =>
          b.classList.remove('qg-audience-card--active')
        );
        btn.classList.add('qg-audience-card--active');
        state.config.audience = btn.dataset.value;
      });
    });

    // Multi-select question type cards
    document.querySelectorAll('.qg-type-card[data-group="types"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const value = btn.dataset.value;
        const isActive = btn.classList.contains('qg-type-card--active');

        // Must keep at least one selected
        const activeCount = document.querySelectorAll('.qg-type-card--active').length;
        if (isActive && activeCount === 1) {
          toast('At least one question type must be selected.', 'info');
          return;
        }

        btn.classList.toggle('qg-type-card--active', !isActive);
        btn.setAttribute('aria-pressed', String(!isActive));

        state.config.question_types = [...document.querySelectorAll('.qg-type-card--active')]
          .map(b => b.dataset.value);
      });
    });
  };

  // ─────────────────────────────────────────────────────────────
  // EXTRA TOGGLES (Hints / Explanations)
  // ─────────────────────────────────────────────────────────────

  const initToggles = () => {
    const toggles = document.querySelectorAll('[data-toggle]');
    toggles.forEach(toggle => {
      toggle.addEventListener('change', () => {
        const key = toggle.dataset.toggle;
        if (key in state.config) {
          state.config[key] = toggle.checked;
        }
      });
    });
  };

  // ─────────────────────────────────────────────────────────────
  // BIND EVENTS
  // ─────────────────────────────────────────────────────────────

  const bindEvents = () => {

    // Mode buttons
    dom.modeDoc.addEventListener('click',    () => setMode('document'));
    dom.modePrompt.addEventListener('click', () => setMode('prompt'));

    // File upload — click zone
    dom.uploadZone.addEventListener('click', (e) => {
      if (e.target === dom.uploadZone || e.target.closest('.qg-upload-idle')) {
        dom.fileInput.click();
      }
    });

    dom.fileInput.addEventListener('change', () => {
      if (dom.fileInput.files[0]) uploadHandler(dom.fileInput.files[0]);
    });

    // Drag and drop
    dom.uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dom.uploadZone.classList.add('qg-upload-zone--drag');
    });

    dom.uploadZone.addEventListener('dragleave', (e) => {
      if (!dom.uploadZone.contains(e.relatedTarget)) {
        dom.uploadZone.classList.remove('qg-upload-zone--drag');
      }
    });

    dom.uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dom.uploadZone.classList.remove('qg-upload-zone--drag');
      const file = e.dataTransfer?.files[0];
      if (file) uploadHandler(file);
    });

    // Remove file
    dom.fileRemove.addEventListener('click', (e) => {
      e.stopPropagation();
      clearUpload();
    });

    // Prompt input — char count
    dom.promptInput.addEventListener('input', () => {
      const len = dom.promptInput.value.length;
      dom.charCount.textContent = `${len} / 5000`;
      updateContinueBtn();
    });

    // Continue → config
    dom.continueBtn.addEventListener('click', () => showPhase(dom.phaseConfig));

    // Back → input
    dom.backBtn.addEventListener('click', () => showPhase(dom.phaseInput));

    // Question count slider
    dom.countSlider.addEventListener('input', () => {
      const val = Number(dom.countSlider.value);
      dom.countValue.textContent = val;
      dom.countSlider.setAttribute('aria-valuenow', val);
      state.config.question_count = val;
    });

    // Language select
    dom.languageSelect.addEventListener('change', () => {
      state.config.language = dom.languageSelect.value;
    });

    // Generate button
    dom.generateBtn.addEventListener('click', generateQuiz);

    // Quiz navigation
    dom.nextBtn.addEventListener('click',   goNext);
    dom.prevBtn.addEventListener('click',   goPrevious);
    dom.skipBtn.addEventListener('click',   skipQuestion);
    dom.quitBtn.addEventListener('click',   () => {
      if (confirm('Exit the quiz? Your progress will be lost.')) resetQuiz();
    });

    // Results actions
    dom.retakeBtn.addEventListener('click',  retakeQuiz);
    dom.newQuizBtn.addEventListener('click', resetQuiz);

    // Keyboard
    document.addEventListener('keydown', handleKeydown);

    // Chip / card groups
    initChipGroups();
    initToggles();
  };

  // ─────────────────────────────────────────────────────────────
  // PILL INIT (size the pill to match the active mode button)
  // ─────────────────────────────────────────────────────────────

  const initModePill = () => {
    const activeBtn = dom.modeDoc;
    dom.modePill.style.width  = `${activeBtn.offsetWidth}px`;
    dom.modePill.style.left   = `${activeBtn.offsetLeft}px`;
  };

  // ─────────────────────────────────────────────────────────────
  // INIT
  // ─────────────────────────────────────────────────────────────

  const init = () => {
    cacheDOM();
    bindEvents();
    initModePill();
    initRotator();
    setMode('document');
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();