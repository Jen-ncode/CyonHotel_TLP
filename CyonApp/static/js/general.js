function goToBook() {

    fetch('/api/get-cart').then(res => res.json()).then((data) => {
        if (Object.keys(data).length == 0) {
            return renew()
        }
        else {
            if (confirm("Bạn có đơn đặt hàng chưa hoàn thành, có muốn tiếp tục không?") == false) {
                return renew()
            }
            else
                window.location="/booking";

        }
    })
}


function goToBook2() {

    fetch('/api/get-cart').then(res => res.json()).then((data) => {
        if (Object.keys(data).length == 0) {
            return renew2()
        }
        else {
            if (confirm("Bạn có đơn đặt hàng chưa hoàn thành, có muốn tiếp tục không?") == false) {
                return renew2()
            }
            else
                window.location="/booking";

        }
    })
}

function renew() {
    fetch('/api/renew').then(res => res.json()).then((data) => {
        document.querySelector("form").action = "/booking"
        document.querySelector("form").submit()
    }).catch(err => console.error(err))
}

function renew2() {
    fetch('/api/renew').then(res => res.json()).then((data) => {
            window.location="/booking"
    }).catch(err => console.error(err))
}

function verify(obj) {
    fetch('/api/verify-email', {
        method: "post",
        body: JSON.stringify({
            "email": obj.value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        if(data != "valid") {
            alert("email không hợp lệ hoặc không tồn tại vui lòng nhập lại")
            obj.value = ""
            obj.classList.add("border", "border-danger")
        }
        else {
            obj.classList.remove("border", "border-danger")
        }
    })
}

function checkIdentityNum(guest_amount, index) {
    obj = document.getElementById(`identity-number-${index}`)
    for (let i = 0; i < guest_amount; i++) {
        if ((i + 1) != index) {
            ipIdentityNum = document.getElementById(`identity-number-${i+1}`)
            if (obj.value == ipIdentityNum.value) {
                alert("Số CMMD/CCCD này đã được sử dụng")
                obj.value = ""
            }
        }
    }
}