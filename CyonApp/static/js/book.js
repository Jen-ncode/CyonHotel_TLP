function getSample(roomtype) {
    var sample = document.createElement('div');
    sample.classList.add("p-3", "border-bottom")
    sample.id = `cart-room-${roomtype.id}`
    sample.innerHTML = `
        <h6 class="font-title fw-bold d-flex justify-content-between"> ${roomtype.name}
            <a href="javascript:;" class="text-decoration-none" style="color: var(--base-color-darker)"
               onclick="deleteCart(${roomtype.id})">
                <i class="fa-solid fa-xmark"></i>
            </a>
        </h6>
        <div class="my-2">
             <button type="button" class="decrease-amount text-dark"
                     onclick="decreaseAmount(${roomtype.id}, this)"> -
             </button>
             <input type="number" value=${roomtype.quantity} min=1 max=3
                    class="ip-simple text-center text-dark hide-arrow" readonly>
             <button type="button" class="increase-amount text-dark"
                     onclick="increaseAmount(${roomtype.id}, this)"> +
             </button>
        </div>
        <div>
             <span class="price">${roomtype.price.toLocaleString("en-US")} VNĐ</span>
        </div>
    `;
    return sample;
}





//////////////////////////////

function bookRoom(id, name, price, maxPeople) {
    fetch('/api/cart/book', {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price,
            "max_people": maxPeople
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        if (data) {
            if (data.quantity == 1) {
                var sample = getSample(data)
                document.getElementById("list-cart").appendChild(sample)
            }
            else {
                var c = document.getElementById(`cart-room-${data.id}`).querySelector("input")
                var p = document.getElementById(`cart-room-${data.id}`).querySelector(".price")

                var value = c.value
                p.innerHTML = (data.price*data.quantity).toLocaleString("en-US") + " VNĐ"
                c.value = value*1 + 1
            }
        }
        else {
            alert("Không còn phòng")
        }

    }).then(update => total())
}

function total() {
    fetch('/api/cart/total').then(res => res.json()).then((data) => {
        var totalAmount = document.querySelector(".total-amount")
        totalAmount.innerHTML = data.total_amount.toLocaleString("en-US") + " VNĐ"

        var totalQuantity = document.querySelector(".total-quantity")
        totalQuantity.innerHTML = data.total_quantity + " phòng"

    }).catch(err => console.error(err))
}


function increaseAmount(roomType_id, obj) {
    var ipObj = obj.parentElement.querySelector("input")

    ipObj.value = ipObj.value*1 + 1
    updateCart(roomType_id, ipObj)
}


function decreaseAmount(roomType_id, obj) {
    var ipObj = obj.parentElement.querySelector("input")
    if (ipObj.value*1 <= 1)
        deleteCart(roomType_id)
    else {
        ipObj.value = ipObj.value*1 - 1
        updateCart(roomType_id, ipObj)
    }
}


function updateCart(roomType_id, obj) {
    fetch(`/api/cart/${roomType_id}`, {
        method: "put",
        body: JSON.stringify({
            "quantity": obj.value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        if(data) {
            var p = document.getElementById(`cart-room-${roomType_id}`).querySelector(".price")
            p.innerHTML = (data.price*data.quantity).toLocaleString("en-US") + " VNĐ"
        }
        else {
            obj.value -= 1
            alert("Không còn phòng")
        }
    }).catch(err => console.error(err)).then(update => total())
}


function deleteCart(roomType_id) {
    if (confirm("Bạn chắc chắn xóa không?") == true) {
        fetch(`/api/cart/${roomType_id}`, {
            method: "delete"
        }).then(res => res.json()).then((data) => {
            let e = document.getElementById(`cart-room-${roomType_id}`)
            e.remove()
        }).catch(err => console.error(err)).then(update => total())
    }

}


function continueBook() {
    fetch('/api/get-cart').then(res => res.json()).then((data) => {
        if (Object.keys(data).length == 0)
            alert("Bạn không thể tiếp tục khi chưa chọn phòng")
        else {
            window.location="/booking/details";
        }
    })
}


function setDate() {
    var checkIn = document.getElementById("check-in");
    var checkOut = document.getElementById("check-out");
    fetch('/api/cart/date', {
        method: "post",
        body: JSON.stringify({
            "check-in": checkIn.value,
            "check-out": checkOut.value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        document.querySelector("form").submit()
    })
}

window.onscroll = function() {
    if (window.innerWidth >= 768) {
        if (window.scrollY >= 333)
            document.querySelector(".my-bill").classList.add("position-fixed", "top-0", "w-25")
        else
            document.querySelector(".my-bill").classList.remove("position-fixed", "top-0", "w-25")
    }
}