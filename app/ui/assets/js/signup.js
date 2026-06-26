document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("signup-form");
    if (!form) return;

    const submitBtn = form.querySelector('button[type="submit"]');

    // OAuth Buttons
    const googleBtn = document.querySelector('[data-oauth-provider="google"]');
    const githubBtn = document.querySelector('[data-oauth-provider="github"]');

    // Backend URL
    const API_BASE_URL = "";
    let signupEmail = "";

    const otpBoxes = document.querySelectorAll(".otp-box");

    otpBoxes.forEach((box, index) => {

        box.addEventListener("input", () => {

            box.value = box.value.replace(/\D/g, "");

            if (
                box.value &&
                index < otpBoxes.length - 1
            ) {
                otpBoxes[index + 1].focus();
            }

        });

        box.addEventListener("keydown", e => {

            if (
                e.key === "Backspace" &&
                !box.value &&
                index > 0
            ) {
                otpBoxes[index - 1].focus();
            }

        });

    });
    // ----------------------------
    // Alerts
    // ----------------------------

    function showSignupAlert(message, type = "error") {
        const alert = document.getElementById("signup-alert");
        alert.textContent = message;
        alert.className = `auth-alert ${type}`;
        alert.style.display = "block";
    }

    function showOtpAlert(message, type = "error") {
        const alert = document.getElementById("otp-alert");
        alert.textContent = message;
        alert.className = `auth-alert ${type}`;
        alert.style.display = "block";
    }

    function clearAlert() {
        const signupAlert = document.getElementById("signup-alert");
        if (signupAlert) {
            signupAlert.textContent = "";
            signupAlert.className = "auth-alert";
            signupAlert.style.display = "none";
        }

        const otpAlert = document.getElementById("otp-alert");
        if (otpAlert) {
            otpAlert.textContent = "";
            otpAlert.className = "auth-alert";
            otpAlert.style.display = "none";
        }
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
            return showSignupAlert("Name is required");
        }

        if (!payload.email) {
            return showSignupAlert("Email is required");
        }

        if (payload.password.length < 6) {
            return showSignupAlert("Password must be at least 6 characters");
        }

        try {

            setLoading(true);

            const response = await fetch(
                `${API_BASE_URL}/auth/send-otp`,
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
            signupEmail = payload.email;

            document
            .querySelectorAll(".otp-box")
            .forEach(box => box.value = "");

            document.querySelector(".otp-box").focus();

            document.getElementById("otp-email").textContent =
                signupEmail;

            document.getElementById("otp-modal").hidden = false;

            showSignupAlert(
                data.message,
                "success"
            );

        } catch (err) {

            console.error(err);

            showSignupAlert(
                err.message || "Something went wrong."
            );

        } finally {

            setLoading(false);

        }

    });
    // ----------------------------
    // Verify OTP
    // ----------------------------


    // ----------------------------
    // Verify OTP
    // ----------------------------

    document
    .getElementById("verify-otp-btn")
    .addEventListener("click", async () => {

        const otp = [...document.querySelectorAll(".otp-box")]
            .map(box => box.value)
            .join("");

        // Select the OTP card element so we can add the red glow to it
        const otpCard = document.querySelector(".otp-card");

        if (otp.length !== 6) {
            otpCard.classList.add("error-state");
            setTimeout(() => otpCard.classList.remove("error-state"), 1500);

            showOtpAlert("Please enter the 6-digit OTP.");
            return;
        }

        try {

            const response = await fetch(
                `${API_BASE_URL}/auth/verify-otp`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: signupEmail,
                        otp: otp
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    data.message ||
                    "OTP verification failed."
                );
            }

            showOtpAlert(
                "Account created successfully!",
                "success"
            );
            document.getElementById("otp-modal").hidden = true;

            setTimeout(() => {
                window.location.href = "/login";
            }, 1000);

        } catch (err) {

            console.error(err);

            showOtpAlert(
                err.message ||
                "OTP verification failed."
            );

            // NEW: Add the red glassmorphism effect when the backend says OTP is wrong
            // 1. Select the card
            const otpCard = document.querySelector('.otp-card');

            // 2. Add the red glassmorphism class
            otpCard.classList.add('error-state');
            
            // Remove the effect after 1.5 seconds (1500ms)
            setTimeout(() => {
                otpCard.classList.remove("error-state");
            }, 1500);

            // OPTIONAL BUT RECOMMENDED: Clear the wrong OTP inputs automatically
            document.querySelectorAll(".otp-box").forEach(box => box.value = "");
            document.querySelector(".otp-box").focus(); 

        }

    });

    document
    .getElementById("resend-otp-btn")
    .addEventListener("click", async () => {

        try {

            const response = await fetch(
                `${API_BASE_URL}/auth/resend-otp`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: signupEmail
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "Failed to resend OTP."
                );
            }

            showOtpAlert(
                data.message,
                "success"
            );

        } catch (err) {

            showOtpAlert(
                err.message
            );

        }

    });

});