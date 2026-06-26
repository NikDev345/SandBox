document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("forgot-form");

    const alertBox = document.querySelector(".auth-alert");

    const API_BASE_URL = "";

    function showAlert(message, type = "error") {

        alertBox.textContent = message;

        alertBox.className =
            `auth-alert ${type}`;

        alertBox.style.display = "block";

    }

    form.addEventListener("submit", async (e) => {

        e.preventDefault();

        const email =
            document.getElementById("email").value.trim();

        try {

            const response = await fetch(

                `${API_BASE_URL}/auth/forgot-password`,

                {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email
                    })

                }

            );

            const data = await response.json();

            if (!response.ok) {

                throw new Error(

                    data.detail ||
                    "Unable to send email."

                );

            }

            showAlert(

                data.message,

                "success"

            );

        }

        catch (err) {

            showAlert(

                err.message

            );

        }

    });

});