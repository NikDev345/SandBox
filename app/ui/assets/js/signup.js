const signupForm = document.getElementById("signup-form");
const authAlert = document.querySelector(".auth-alert");

function showAlert(message, type = "error") {
    if (!authAlert) return;
    authAlert.textContent = message;
    authAlert.className = `auth-alert show ${type}`;
}

function setButtonLoading(button, loading) {
    if (!button) return;
    const label = button.querySelector("[data-button-label]") || button.querySelector("span") || button;
    if (!button.dataset.defaultText) {
        button.dataset.defaultText = label.textContent;
    }
    label.textContent = loading ? button.dataset.loadingText : button.dataset.defaultText;
    button.disabled = loading;
}

function setFieldError(input, message) {
    const field = input.closest(".field");
    const note = field?.querySelector("small");
    field?.classList.toggle("invalid", Boolean(message));
    if (note) note.textContent = message || "";
}

function validateSignup() {
    const name = document.getElementById("name");
    const email = document.getElementById("email");
    const password = document.getElementById("password");
    let valid = true;

    if (!name.value.trim() || name.value.trim().length < 2) {
        setFieldError(name, "Enter your full name.");
        valid = false;
    } else {
        setFieldError(name, "");
    }

    if (!email.value.trim() || !email.validity.valid) {
        setFieldError(email, "Enter a valid email address.");
        valid = false;
    } else {
        setFieldError(email, "");
    }

    if (!password.value || password.value.length < 6) {
        setFieldError(password, "Use at least 6 characters.");
        valid = false;
    } else {
        setFieldError(password, "");
    }

    return valid;
}

document.querySelectorAll(".field input").forEach(input => {
    input.addEventListener("input", () => setFieldError(input, ""));
});

document.querySelectorAll("[data-oauth-provider]").forEach(button => {
    button.addEventListener("click", () => {
        window.location.href = `/auth/oauth/${button.dataset.oauthProvider}/login`;
    });
});

signupForm?.addEventListener("submit", async event => {
    event.preventDefault();

    if (!validateSignup()) return;

    const submitButton = signupForm.querySelector("button[type='submit']");
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    setButtonLoading(submitButton, true);

    try {
        const response = await fetch("/auth/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to create account.");
        }

        showAlert("Account created. Taking you to sign in...", "success");
        window.setTimeout(() => {
            window.location.href = "/login";
        }, 700);
    } catch (error) {
        showAlert(error.message);
    } finally {
        setButtonLoading(submitButton, false);
    }
});
