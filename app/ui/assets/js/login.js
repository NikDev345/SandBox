const loginForm = document.getElementById("login-form");
const guestButton = document.getElementById("guest-login");
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

function validateLogin() {
    const email = document.getElementById("email");
    const password = document.getElementById("password");
    let valid = true;

    if (!email.value.trim() || !email.validity.valid) {
        setFieldError(email, "Enter a valid email address.");
        valid = false;
    } else {
        setFieldError(email, "");
    }

    if (!password.value || password.value.length < 6) {
        setFieldError(password, "Password must be at least 6 characters.");
        valid = false;
    } else {
        setFieldError(password, "");
    }

    return valid;
}

document.querySelectorAll(".field input").forEach(input => {
    input.addEventListener("input", () => setFieldError(input, ""));
});

function persistAuthSession(data) {
    localStorage.setItem("user_id", data.user_id);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("toolbox_user", JSON.stringify(data.user));
}

document.querySelectorAll("[data-oauth-provider]").forEach(button => {
    button.addEventListener("click", () => {
        window.location.href = `/auth/oauth/${button.dataset.oauthProvider}/login`;
    });
});

guestButton?.addEventListener("click", async () => {
    setButtonLoading(guestButton, true);

    try {
        const response = await fetch("/auth/guest", {
            method: "POST"
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to continue as guest.");
        }

        persistAuthSession(data);
        window.location.href = "/";
    } catch (error) {
        showAlert(error.message);
    } finally {
        setButtonLoading(guestButton, false);
    }
});

loginForm?.addEventListener("submit", async event => {
    event.preventDefault();

    if (!validateLogin()) return;

    const submitButton = loginForm.querySelector("button[type='submit']");
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    setButtonLoading(submitButton, true);

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to sign in.");
        }

        persistAuthSession(data);

        showAlert("Signed in. Redirecting to your workspace...", "success");
        window.location.href = "/";
    } catch (error) {
        showAlert(error.message);
    } finally {
        setButtonLoading(submitButton, false);
    }
});
