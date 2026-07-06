document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("reset-form");

    const alertBox = document.querySelector(".auth-alert");

    const API_BASE_URL = "";

    const token =
        new URLSearchParams(
            window.location.search
        ).get("token");




        
    function showAlert(message, type = "error") {

        alertBox.textContent = message;

        alertBox.className =
            `auth-alert ${type}`;

        alertBox.style.display = "block";

    }


    form.addEventListener("submit", async (e) => {

        e.preventDefault();

        const password =
            document.getElementById("password").value;

        const confirm =
            document.getElementById("confirm_password").value;

        if (password !== confirm) {

            return showAlert(
                "Passwords do not match."
            );

        }

        try {

            const response = await fetch(

                `${API_BASE_URL}/auth/reset-password`,

                {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({

                        token: token,

                        password: password

                    })

                }

            );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(

                    data.detail ||
                    "Password reset failed."

                );

            }

            showAlert(

                data.message,

                "success"

            );

            setTimeout(() => {

                window.location.href =
                    "/login";

            }, 1500);

        }

        catch (err) {

            showAlert(

                err.message

            );

        }

    });

});