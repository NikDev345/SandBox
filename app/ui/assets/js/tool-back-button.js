(function () {
    "use strict";

    function addToolBackButton() {
        if (document.querySelector(".tool-back-button")) {
            return;
        }

        const button = document.createElement("button");

        button.type = "button";
        button.className = "tool-back-button";
        button.setAttribute("aria-label", "Back to Tools");

        button.innerHTML = `
            <svg
                viewBox="0 0 24 24"
                aria-hidden="true"
                focusable="false"
            >
                <path d="M19 12H5"></path>
                <path d="M12 19L5 12L12 5"></path>
            </svg>

            <span>Back to Tools</span>
        `;

        /*
         * Use capture phase so tool-specific JavaScript
         * cannot prevent the navigation.
         */
        button.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();

                window.location.href = "/#tools";
            },
            true
        );

        document.body.prepend(button);
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            addToolBackButton
        );
    } else {
        addToolBackButton();
    }
})();