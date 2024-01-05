
window.onload = function() {
    let ipPass = document.getElementById("password")
    ipPass.onchange = function() {
        console.log(ipPass.value)
        fetch('/api/hash-password', {
            method: "post",
            body: JSON.stringify({
                "password": ipPass.value
            }),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => res.json()).then((data) => {
                ipPass.value = data
        })
    }
}