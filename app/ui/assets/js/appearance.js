// =======================================================
// Sandbox Appearance
// =======================================================

const STORAGE_KEY = "sandbox-theme";

function applyTheme(theme) {

    if (theme === "system") {

        const prefersDark = window.matchMedia(
            "(prefers-color-scheme: dark)"
        ).matches;

        document.documentElement.setAttribute(
            "data-theme",
            prefersDark ? "dark" : "light"
        );

        return;
    }

    document.documentElement.setAttribute(
        "data-theme",
        theme
    );
}

export function setTheme(theme) {

    localStorage.setItem(
        STORAGE_KEY,
        theme
    );

    applyTheme(theme);

}

export function loadTheme() {

    const theme =
        localStorage.getItem(STORAGE_KEY)
        || "dark";

    applyTheme(theme);

}

window.setTheme = setTheme;

window.addEventListener(
    "DOMContentLoaded",
    loadTheme
);

window.matchMedia(
    "(prefers-color-scheme: dark)"
).addEventListener(
    "change",
    () => {

        const theme = localStorage.getItem(STORAGE_KEY);

        if (theme === "system") {

            applyTheme("system");

        }

    }
);