document
.getElementById("login-form")
.addEventListener(
    "submit",
    async function(e){

        e.preventDefault();

        const email =
            document.getElementById("email").value;

        const password =
            document.getElementById("password").value;

        const response =
            await fetch(
                "/auth/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                        "application/json"
                    },

                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );

        const data =
            await response.json();

        if(response.ok){

            alert("Login Successful");

            window.location.href = "/";

        }else{

            alert(data.detail);
        }

    }
);