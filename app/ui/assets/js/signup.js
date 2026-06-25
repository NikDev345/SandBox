document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("signup-form");
    if (!form) return;

    const alertBox = document.querySelector(".auth-alert");
    const submitBtn = form.querySelector('button[type="submit"]');

    // OAuth Buttons
    const googleBtn = document.querySelector('[data-oauth-provider="google"]');
    const githubBtn = document.querySelector('[data-oauth-provider="github"]');

    // Backend URL
    const API_BASE_URL = "";

    // ----------------------------
    // Alerts
    // ----------------------------

    function showAlert(message, type = "error") {
        alertBox.textContent = message;
        alertBox.className = `auth-alert ${type}`;
        alertBox.style.display = "block";
    }

    function clearAlert() {
        alertBox.textContent = "";
        alertBox.className = "auth-alert";
        alertBox.style.display = "none";
    }

    // ----------------------------
    // Loading State
    // ----------------------------

    function setLoading(loading) {

        submitBtn.disabled = loading;

        const span = submitBtn.querySelector("span");

        if (loading) {

            submitBtn.dataset.originalText = span.textContent;
            span.textContent = "Creating...";

        } else {

            span.textContent =
                submitBtn.dataset.originalText || "Create Account";

        }
    }

    // ----------------------------
    // OAuth
    // ----------------------------

    if (googleBtn) {

        googleBtn.addEventListener("click", () => {

            window.location.href = "/auth/google";

        });

    }

    if (githubBtn) {

        githubBtn.addEventListener("click", () => {

            window.location.href = "/auth/github";

        });

    }

    // ----------------------------
    // Signup
    // ----------------------------

    form.addEventListener("submit", async (e) => {

        e.preventDefault();

        clearAlert();

        const payload = {

            name: document.getElementById("full_name").value.trim(),
            email: document.getElementById("email").value.trim(),
            password: document.getElementById("password").value

        };

        if (!payload.name) {
            return showAlert("Name is required");
        }

        if (!payload.email) {
            return showAlert("Email is required");
        }

        if (payload.password.length < 6) {
            return showAlert("Password must be at least 6 characters");
        }

        try {

            setLoading(true);

            const response = await fetch(
                `${API_BASE_URL}/auth/signup`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            let data = {};

            try {
                data = await response.json();
            } catch {
                throw new Error("Invalid server response");
            }

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    data.message ||
                    "Signup failed"
                );
            }

            showAlert(
                data.message || "Account created successfully!",
                "success"
            );

            form.reset();

            setTimeout(() => {

                window.location.href = "/login";

            }, 1200);

        } catch (err) {

            console.error(err);

            showAlert(
                err.message || "Something went wrong."
            );

        } finally {

            setLoading(false);

        }

    });

});