document
.getElementById('login-form')
?.addEventListener(
    'submit',
    async function(e){

        e.preventDefault();

        const email =
            document.getElementById('email').value;

        const password =
            document.getElementById('password').value;

        const response =
            await fetch(
                '/auth/login',
                {
                    method:'POST',

                    headers:{
                        'Content-Type':
                        'application/json'
                    },

                    body:JSON.stringify({
                        email,
                        password
                    })
                }
            );

        const data =
            await response.json();

        console.log(data);

    }
);

document
.getElementById('guest-login')
?.addEventListener(
    'click',
    async ()=>{

        const response =
            await fetch(
                '/auth/guest',
                {
                    method:'POST'
                }
            );

        const data =
            await response.json();

        console.log(data);

    }
);