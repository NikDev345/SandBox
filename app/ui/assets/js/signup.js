document.addEventListener("DOMContentLoaded", () => {
const form = document.getElementById("signup-form");
const alertBox = document.querySelector(".auth-alert");
const submitBtn = form.querySelector('button[type="submit"]');


const API_BASE_URL = ""; // change if needed

function showAlert(message, type = "error") {
    alertBox.textContent = message;
    alertBox.classList.remove("success", "error");
    alertBox.classList.add(type);
    alertBox.style.display = "block";
}

function clearAlert() {
    alertBox.textContent = "";
    alertBox.classList.remove("success", "error");
    alertBox.style.display = "none";
}

function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.dataset.originalText =
            submitBtn.querySelector("span").textContent;

        submitBtn.querySelector("span").textContent =
            submitBtn.dataset.loadingText || "Loading...";
    } else {
        submitBtn.disabled = false;
        submitBtn.querySelector("span").textContent =
            submitBtn.dataset.originalText;
    }
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    clearAlert();
    const name = document.getElementById("full_name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!name) {
        showAlert("Name is required");
        return;
    }

    if (!email) {
        showAlert("Email is required");
        return;
    }

    if (password.length < 6) {
        showAlert("Password must be at least 6 characters");
        return;
    }

    try {
        setLoading(true);

        const response = await fetch(
            `${API_BASE_URL}/auth/signup`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name,
                    email,
                    password,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to create account"
            );
        }

        showAlert(
            data.message || "Account created successfully",
            "success"
        );

        form.reset();

        setTimeout(() => {
            window.location.href = "/login";
        }, 1500);

    } catch (error) {
        console.error(error);
        showAlert(error.message);
    } finally {
        setLoading(false);
    }
});


});
