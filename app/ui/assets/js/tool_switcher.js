document.addEventListener("DOMContentLoaded", () => {
    const tools = window.TOOLS || [];

    // 🔹 Icon map
    const ICONS = {
        code: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-width="2" d="M16 18l6-6-6-6M8 6l-6 6 6 6"/>
        </svg>`,

        text: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-width="2" d="M4 6h16M4 12h10M4 18h7"/>
        </svg>`,

        ai: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="3" stroke-width="2"/>
            <path stroke-width="2" d="M19.4 15a7.5 7.5 0 0 0 0-6M4.6 9a7.5 7.5 0 0 0 0 6"/>
        </svg>`,

        doc: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-width="2" d="M6 2h9l5 5v15H6z"/>
        </svg>`,

        default: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="2"/>
        </svg>`
    };

    function getIcon(type) {
        return ICONS[type] || ICONS.default;
    }

    // 🔹 Container
    const container = document.createElement("div");
    container.className = "tool-dropdown-container";

    // 🔹 Button
    const button = document.createElement("button");
    button.className = "tool-toggle-btn";
    button.innerHTML = `
        ${ICONS.default}
        Tools <span class="arrow">⌄</span>
    `;

    // 🔹 Dropdown
    const dropdown = document.createElement("div");
    dropdown.className = "tool-dropdown";

    const currentPath = window.location.pathname;

    tools.forEach(tool => {
        const item = document.createElement("div");
        item.className = "tool-item";

        item.innerHTML = `
            ${getIcon(tool.icon)}
            <span>${tool.name}</span>
        `;

        // ✅ Correct active check
        if (currentPath === tool.route) {
            item.classList.add("active");
        }

        // ✅ Correct navigation
        item.onclick = () => {
            window.location.href = tool.route;
        };

        dropdown.appendChild(item);
    });

    // Toggle dropdown
    button.onclick = (e) => {
        e.stopPropagation();
        dropdown.classList.toggle("open");
        button.classList.toggle("active");
    };

    // Close on outside click
    document.addEventListener("click", (e) => {
        if (!container.contains(e.target)) {
            dropdown.classList.remove("open");
        }
    });

    container.appendChild(button);
    container.appendChild(dropdown);
    document.body.appendChild(container);
});