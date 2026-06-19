// ==========================================
// TOOLBOX DASHBOARD
// ==========================================

document.addEventListener('DOMContentLoaded', () => {

    initializeCounters();
    initializeToolCards();
    initializeCommandPalette();
    initializeSearch();
    initializeSidebar();

});

// ==========================================
// COUNTER ANIMATION
// ==========================================

function initializeCounters() {

    const counters = document.querySelectorAll('.stat-card h3');

    counters.forEach(counter => {

        const text = counter.innerText;

        const target = parseFloat(
            text.replace(/,/g, '')
                .replace('%', '')
        );

        if (isNaN(target)) return;

        let current = 0;

        const increment = target / 50;

        const timer = setInterval(() => {

            current += increment;

            if (current >= target) {

                current = target;

                clearInterval(timer);
            }

            if (text.includes('%')) {

                counter.innerText =
                    current.toFixed(1) + '%';

            } else {

                counter.innerText =
                    Math.floor(current).toLocaleString();
            }

        }, 20);

    });

}

// ==========================================
// TOOL CARD HOVER
// ==========================================

function initializeToolCards() {

    const cards =
        document.querySelectorAll('.tool-card');

    cards.forEach(card => {

        card.addEventListener('mouseenter', () => {

            card.style.transform =
                'translateY(-4px)';

        });

        card.addEventListener('mouseleave', () => {

            card.style.transform =
                'translateY(0px)';

        });

    });

}

// ==========================================
// SEARCH
// ==========================================

function initializeSearch() {

    const search =
        document.querySelector('.search');

    if (!search) return;

    search.addEventListener('keyup', e => {

        const value =
            e.target.value.toLowerCase();

        const cards =
            document.querySelectorAll('.tool-card');

        cards.forEach(card => {

            const title =
                card.querySelector('h3')
                    .innerText
                    .toLowerCase();

            if (title.includes(value)) {

                card.style.display = 'block';

            } else {

                card.style.display = 'none';
            }

        });

    });

}

// ==========================================
// SIDEBAR ACTIVE STATE
// ==========================================

function initializeSidebar() {

    const items =
        document.querySelectorAll('.nav-item');

    items.forEach(item => {

        item.addEventListener('click', () => {

            items.forEach(i =>
                i.classList.remove('active')
            );

            item.classList.add('active');

        });

    });

}

// ==========================================
// COMMAND PALETTE
// CTRL + K
// ==========================================

function initializeCommandPalette() {

    document.addEventListener(
        'keydown',
        function (e) {

            if (
                e.ctrlKey &&
                e.key.toLowerCase() === 'k'
            ) {

                e.preventDefault();

                openCommandPalette();
            }
        }
    );

}

function openCommandPalette() {

    let existing =
        document.querySelector('.command-modal');

    if (existing) {

        existing.remove();
        return;
    }

    const modal =
        document.createElement('div');

    modal.className =
        'command-modal';

    modal.innerHTML = `
        <div class="command-box">

            <input
                autofocus
                placeholder="Search tools..."
                class="command-input"
            />

            <div class="command-item">
                SQL Generator
            </div>

            <div class="command-item">
                Regex Generator
            </div>

            <div class="command-item">
                JSON Fixer
            </div>

            <div class="command-item">
                Code Reviewer
            </div>

        </div>
    `;

    document.body.appendChild(modal);

    modal.addEventListener('click', e => {

        if (e.target === modal) {

            modal.remove();
        }

    });

}

// ==========================================
// ESC CLOSE
// ==========================================

document.addEventListener(
    'keydown',
    function (e) {

        if (e.key === 'Escape') {

            const modal =
                document.querySelector(
                    '.command-modal'
                );

            if (modal) {

                modal.remove();
            }

        }

    }
);