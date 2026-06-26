document.addEventListener("DOMContentLoaded", () => {

    const savedTheme =
        localStorage.getItem("sandbox-theme") || "dark";

    applyTheme(savedTheme);

});

function applyTheme(theme) {

    document.documentElement.setAttribute(
        "data-theme",
        theme
    );

    localStorage.setItem(
        "sandbox-theme",
        theme
    );

}

window.setTheme = function(theme) {

    applyTheme(theme);

};