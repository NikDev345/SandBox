// ------------------------------------------------------------------
// Mock data — this is what the real tool would generate from the
// uploaded PDF / TEXT / DOCX after extraction.
// ------------------------------------------------------------------
const MOCK_CARDS = [
  {
    question: "What is the time complexity of binary search on a sorted array?",
    answer: "O(log n) — because the search space is halved on every comparison."
  },
  {
    question: "What does the CSS property `backdrop-filter: blur()` do?",
    answer: "It blurs whatever is behind an element, creating a frosted-glass effect while keeping the element itself transparent."
  },
  {
    question: "In React, what hook lets you run side effects after render?",
    answer: "useEffect — it runs after the DOM has updated and can optionally clean up between renders."
  },
  {
    question: "What HTTP status code means 'Created'?",
    answer: "201 Created — returned when a request has successfully created a new resource."
  },
  {
    question: "What is the difference between `let` and `const` in JavaScript?",
    answer: "`let` allows reassignment; `const` binds a variable to a value that cannot be reassigned (though objects/arrays it holds can still be mutated)."
  }
];

// ------------------------------------------------------------------
// State
// ------------------------------------------------------------------
let currentIndex = 0;
let isFlipped = false;
let isAnimating = false;

const deck = document.getElementById('deck');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const dotsWrap = document.getElementById('dots');
const progressLabel = document.getElementById('progressLabel');

// ------------------------------------------------------------------
// Build DOM
// ------------------------------------------------------------------
function buildCard(cardData, index){
  const card = document.createElement('div');
  card.className = 'card';
  card.dataset.index = index;

  card.innerHTML = `
    <div class="card-inner">
      <div class="card-face card-face--front">
        <div class="face-kicker">
          <span>Question</span>
          <span class="tag">Card ${index + 1}</span>
        </div>
        <div class="face-body"><p>${cardData.question}</p></div>
        <div class="face-footer">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 15v.01M12 7a3 3 0 013 3c0 2-3 2.5-3 4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          <span>Drag or tap to reveal answer</span>
        </div>
      </div>
      <div class="card-face card-face--back">
        <div class="face-kicker">
          <span>Answer</span>
          <span class="tag">Card ${index + 1}</span>
        </div>
        <div class="face-body"><p>${cardData.answer}</p></div>
        <div class="face-footer">
          <svg viewBox="0 0 24 24" fill="none"><path d="M21 12a9 9 0 11-3.2-6.9M21 4v5h-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>Drag or tap to flip back</span>
        </div>
      </div>
    </div>
  `;

  attachFlipGestures(card);
  return card;
}

function getInner(card){
  return card.querySelector('.card-inner');
}

// current live rotation angle (degrees) per card index, so re-render keeps state
const flipAngle = {};

function currentAngle(index){
  if (flipAngle[index] != null) return flipAngle[index];
  return isFlippedState(index) ? 180 : 0;
}

function isFlippedState(index){
  return index === currentIndex ? isFlipped : false;
}

function setAngle(card, angle, withTransition){
  const inner = getInner(card);
  if (!inner) return;
  inner.style.transition = withTransition
    ? 'transform 0.5s cubic-bezier(.2,.85,.32,1.15)'
    : 'none';
  inner.style.transform = `rotateY(${angle}deg)`;

  // Don't rely on native backface-visibility — it gets silently defeated by
  // box-shadow/filter on the faces in some Chromium builds, letting both
  // sides render at once mid-rotation. Decide which face is "forward"
  // purely from the angle and hide the other explicitly, every frame.
  const normalized = ((angle % 360) + 360) % 360;
  const frontIsForward = normalized <= 90 || normalized >= 270;
  const front = card.querySelector('.card-face--front');
  const back = card.querySelector('.card-face--back');
  if (front){
    front.style.transition = 'opacity 0.08s linear';
    front.style.opacity = frontIsForward ? '1' : '0';
    front.style.visibility = frontIsForward ? 'visible' : 'hidden';
  }
  if (back){
    back.style.transition = 'opacity 0.08s linear';
    back.style.opacity = frontIsForward ? '0' : '1';
    back.style.visibility = frontIsForward ? 'hidden' : 'visible';
  }
}

function attachFlipGestures(card){
  const inner = getInner(card);
  if (!inner) return;

  let dragging = false;
  let startX = 0;
  let startAngle = 0;
  let moved = false;
  let wheelSettleTimer = null;

  const isActiveCard = () => parseInt(card.dataset.index, 10) === currentIndex && !isAnimating;

  function pointerDown(e){
    if (!isActiveCard()) return;
    dragging = true;
    moved = false;
    startX = e.clientX;
    startAngle = currentAngle(currentIndex);
    inner.setPointerCapture && inner.setPointerCapture(e.pointerId);
    setAngle(card, startAngle, false);
  }

  function pointerMove(e){
    if (!dragging) return;
    const dx = e.clientX - startX;
    if (Math.abs(dx) > 4) moved = true;
    // 260px drag = a full 180deg flip
    let angle = startAngle - (dx / 260) * 180;
    angle = Math.max(-20, Math.min(200, angle)); // slight overshoot allowed, then snap corrects it
    flipAngle[currentIndex] = angle;
    setAngle(card, angle, false);
  }

  function pointerUp(){
    if (!dragging) return;
    dragging = false;
    if (!moved){
      // treat as a plain tap: toggle fully
      flipCard();
      return;
    }
    snapToNearest();
  }

  function snapToNearest(){
    const angle = flipAngle[currentIndex] != null ? flipAngle[currentIndex] : currentAngle(currentIndex);
    const normalized = ((angle % 360) + 360) % 360;
    const snapped = normalized > 90 && normalized < 270 ? 180 : 0;
    isFlipped = snapped === 180;
    flipAngle[currentIndex] = snapped;
    setAngle(card, snapped, true);
    const activeCard = deck.querySelector(`.card[data-index="${currentIndex}"]`);
    if (activeCard) activeCard.classList.toggle('is-flipped', isFlipped);
  }

  inner.addEventListener('pointerdown', pointerDown);
  inner.addEventListener('pointermove', pointerMove);
  inner.addEventListener('pointerup', pointerUp);
  inner.addEventListener('pointercancel', pointerUp);

  // Scroll wheel nudges the flip like a dial — vertical scroll rotates the card
  inner.addEventListener('wheel', (e) => {
    if (!isActiveCard()) return;
    e.preventDefault();
    const base = flipAngle[currentIndex] != null ? flipAngle[currentIndex] : currentAngle(currentIndex);
    let angle = base + e.deltaY * 0.6;
    angle = Math.max(-20, Math.min(200, angle));
    flipAngle[currentIndex] = angle;
    setAngle(card, angle, false);

    clearTimeout(wheelSettleTimer);
    wheelSettleTimer = setTimeout(snapToNearest, 140);
  }, { passive: false });
}

function buildDots(){
  dotsWrap.innerHTML = '';
  MOCK_CARDS.forEach((_, i) => {
    const dot = document.createElement('div');
    dot.className = 'dot' + (i === currentIndex ? ' is-active' : '');
    dotsWrap.appendChild(dot);
  });
}

function renderDeck(withIntro){
  deck.innerHTML = '';
  MOCK_CARDS.forEach((data, i) => {
    const card = buildCard(data, i);
    deck.appendChild(card);
  });
  positionCards(withIntro);
  updateProgress();
}

function positionCards(withIntro){
  const cards = Array.from(deck.children);
  cards.forEach((card, i) => {
    card.classList.remove('is-flipped');
    setAngle(card, 0, false);
    let pos = 'hidden';
    if (i === currentIndex) pos = 'active';
    else if (i === currentIndex + 1) pos = 'next1';
    else if (i === currentIndex - 1) pos = 'prev1';
    else if (i === currentIndex + 2) pos = 'next2';
    else if (i === currentIndex - 2) pos = 'prev2';
    card.dataset.pos = pos;
  });

  if (withIntro){
    const active = cards[currentIndex];
    if (active){
      active.classList.add('intro');
      setTimeout(() => active.classList.remove('intro'), 650);
    }
  }
}

function updateProgress(){
  progressLabel.textContent = `Card ${currentIndex + 1} of ${MOCK_CARDS.length}`;
  prevBtn.disabled = currentIndex === 0;
  nextBtn.disabled = currentIndex === MOCK_CARDS.length - 1;
  buildDots();
}

function flipCard(){
  const activeCard = deck.querySelector(`.card[data-index="${currentIndex}"]`);
  if (!activeCard) return;
  isFlipped = !isFlipped;
  const angle = isFlipped ? 180 : 0;
  flipAngle[currentIndex] = angle;
  setAngle(activeCard, angle, true);
  activeCard.classList.toggle('is-flipped', isFlipped);
}

function goNext(){
  if (isAnimating || currentIndex >= MOCK_CARDS.length - 1) return;
  isAnimating = true;
  isFlipped = false;
  delete flipAngle[currentIndex];
  currentIndex++;
  positionCards(true);
  updateProgress();
  setTimeout(() => { isAnimating = false; }, 400);
}

function goPrev(){
  if (isAnimating || currentIndex <= 0) return;
  isAnimating = true;
  isFlipped = false;
  delete flipAngle[currentIndex];
  currentIndex--;
  positionCards(true);
  updateProgress();
  setTimeout(() => { isAnimating = false; }, 400);
}

// ------------------------------------------------------------------
// Events
// ------------------------------------------------------------------
nextBtn.addEventListener('click', goNext);
prevBtn.addEventListener('click', goPrev);

document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight') goNext();
  if (e.key === 'ArrowLeft') goPrev();
  if (e.key === ' ' || e.key === 'Enter'){
    e.preventDefault();
    if (!isAnimating) flipCard();
  }
});

// ------------------------------------------------------------------
// Init
// ------------------------------------------------------------------
renderDeck(true);