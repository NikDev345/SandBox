document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("login-form");
    if (!form) return;

    const alertBox = document.querySelector(".auth-alert");
    const submitBtn = form.querySelector('button[type="submit"]');

    // OAuth Buttons
    const googleBtn = document.querySelector('[data-oauth-provider="google"]');
    const githubBtn = document.querySelector('[data-oauth-provider="github"]');

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
            span.textContent = "Signing in...";

        } else {

            span.textContent =
                submitBtn.dataset.originalText || "Sign In";

        }
    }

    // ----------------------------
    // Google OAuth
    // ----------------------------

    if (googleBtn) {

        googleBtn.addEventListener("click", () => {

            window.location.href = "/auth/google";

        });

    }

    // ----------------------------
    // GitHub OAuth
    // ----------------------------

    if (githubBtn) {

        githubBtn.addEventListener("click", () => {

            window.location.href = "/auth/github";

        });

    }

    // ----------------------------
    // Login
    // ----------------------------

    form.addEventListener("submit", async (e) => {

        e.preventDefault();

        clearAlert();

        const payload = {

            email: document.getElementById("email").value.trim(),
            password: document.getElementById("password").value

        };

        if (!payload.email) {
            return showAlert("Email is required");
        }

        if (!payload.password) {
            return showAlert("Password is required");
        }

        try {

            setLoading(true);

            const response = await fetch(
                "/auth/login",
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
                    "Invalid credentials"
                );

            }

            // Save Session
            localStorage.setItem(
                "access_token",
                data.access_token
            );

            localStorage.setItem(
                "user_id",
                data.user_id
            );

            if (data.role) {

                localStorage.setItem(
                    "role",
                    data.role
                );

            }

            showAlert(
                "Login successful!",
                "success"
            );

            setTimeout(() => {

                window.location.href = "/";

            }, 1000);

        } catch (err) {

            console.error(err);

            showAlert(
                err.message || "Login failed."
            );

        } finally {

            setLoading(false);

        }

    });

});
