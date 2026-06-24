document.addEventListener("DOMContentLoaded", () => {


const form = document.getElementById("login-form");

if (!form) return;

const alertBox = document.querySelector(".auth-alert");
const submitBtn = form.querySelector('button[type="submit"]');

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
            submitBtn.dataset.loadingText || "Signing in...";
    } else {
        submitBtn.disabled = false;

        submitBtn.querySelector("span").textContent =
            submitBtn.dataset.originalText;
    }
}

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    clearAlert();

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    if (!email) {
        showAlert("Email is required");
        return;
    }

    if (!password) {
        showAlert("Password is required");
        return;
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
                body: JSON.stringify({
                    email,
                    password
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Invalid credentials"
            );
        }

        localStorage.setItem(
            "access_token",
            data.access_token
        );

        localStorage.setItem(
            "user_id",
            data.user_id
        );

        showAlert(
            "Login successful",
            "success"
        );

        setTimeout(() => {
            window.location.href = "/";
        }, 1000);

    } catch (error) {

        console.error(error);

        showAlert(
            error.message || "Login failed"
        );

    } finally {

        setLoading(false);

    }

});


});
