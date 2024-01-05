function next(){
    let form = document.getElementById("reservation")
    if (form.checkValidity()) {
        ordererName = document.getElementById("orderer-name").value
        ordererEmail = document.getElementById("orderer-email").value
        checkIn = document.getElementById("check-in").value
        checkOut = document.getElementById("check-out").value
        amountRooms = document.getElementById("amount-rooms").value
        data = {
            'orderer_name': ordererName,
            'orderer_email': ordererEmail,
            'check-in': checkIn,
            'check-out': checkOut,
            'amount_rooms': amountRooms,
        }
        fetch('/api/staff/info', {
            method: "post",
            body: JSON.stringify({
                data
            }),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => res.json()).then((data) => {
            window.location="/staff/booking/rooms";
        })
    }
    else
        alert("Vui lòng điền đầy đủ thông tin")
}

function addRoom() {
    fetch('/api/booking/rooms/add', {
        method: "put",
    }).then(res => res.json()).then((data) => {
        if (data) {
            let index= data*1
            r = `
                <div id="${index}" class="row col-12 col-md-10 mx-auto my-4 rounded-3 shadow p-4 bg-white position-relative">
                    <div class="fw-bold fs-5">Phòng <span class="index">${index}</span></div>
                    <div class="mt-3 w-75">
                        <a class="btn btn-primary w-100" href="/staff/booking/rooms/${index}">Điền thông tin</a>
                    </div>
                    <div class="mt-3 w-25">
                        <a class="btn btn-danger w-100">Xóa</a>
                    </div>
                </div>
            `
             let listRoom = document.querySelector("#list-room > div:last-child")
             if (listRoom != null)
                listRoom.insertAdjacentHTML("afterend", r)
             else
                document.getElementById("list-room").innerHTML = r
        }
        else
            alert("Có lỗi xảy ra")
    })
}

function chooseRoom(index, type_id, type_name, price, type_max_people) {
    let amountGuests = document.querySelector("#list-guests").children.length
    if (amountGuests > type_max_people) {
        alert(`Số khách nhiều hơn số lượng tối đa của phòng ${type_name}, vui lòng chọn phòng khác`)
        return
    }
    let data = {
                'room_type_id': type_id,
                'name': type_name,
                'price': price,
                'max_people': type_max_people
            }
    fetch(`/api/booking/rooms/${index}/choose`, {
        method: "post",
        body: JSON.stringify({
            data
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        if(data) {
            document.getElementById("room-type").innerHTML = type_name
            document.getElementById("choose-room-type").classList.remove("show")
            h = document.getElementById("hidden-list")
            if (h)
                h.classList.remove("d-none")

            l = document.getElementById("list-guests")
            l.setAttribute("rel", type_max_people)
        }
        else
            alert("Đã có lỗi xảy ra")
    })
}

function addGuest() {
    let order = document.querySelector("#list-guests").children.length + 1
    let max = document.getElementById("list-guests").getAttribute("rel")*1
    if (order > max) {
        alert("Đã đạt số lượng tối đa, không thể thêm")
        return
    }
    let g = `
        <div id="guest-${order}" class="input-group shadow my-3 bg-white rounded-2 p-3">
            <div class="mt-3 fw-bold">Khách hàng ${order}</div>
            <div class="form-floating m-3 w-100">
                <input required type="text" class="form-control" id="name-${order}" placeholder="Nhập họ tên"
                       name="name">
                <label for="name-${order}">Họ tên</label>
            </div>
            <select required class="form-select m-3 w-25" name="gender-${order}" id="gender-${order}" aria-label="Giới tính">
                <option value="" selected>Giới tính</option>
                <option value="1">Nam</option>
                <option value="2">Nữ</option>
            </select>
            <select required class="form-select m-3 w-25" name="guest-type-${order}" id="guest-type-${order}"
                    aria-label="Loại khách">
                <option value="" selected>Chọn loại khách</option>
                <option value="1">Nội địa</option>
                <option value="2">Nước ngoài</option>
            </select>
            <div class="form-floating m-3 w-100">
                <input required type="text" class="form-control" id="identity-number-${order}"
                       placeholder="Nhập CMND/CCCD"
                       name="identity-number-${order}">
                <label for="identity-number-${order}">CMND/CCCD</label>
            </div>
            <div class="form-floating m-3 w-100">
                <input required type="text" class="form-control" id="address-${order}" placeholder="Nhập địa chỉ"
                       name="address-${order}">
                <label for="address-${order}">Địa chỉ</label>
            </div>
            <div class="ms-auto mt-3 col-1">
                 <a onclick="removeGuests(${order})" class="btn btn-danger w-100">Xóa</a>
            </div>
        </div>
    `
    let listGuests = document.querySelector("#list-guests > div:last-child")
    if (listGuests != null)
        listGuests.insertAdjacentHTML("afterend", g)
    else
        document.getElementById("list-room").innerHTML = g
}

function removeGuests(order) {
    let length = document.querySelector("#list-guests").children.length
    if (length == 1) {
        alert("Phải có ít nhất 1 khách")
        return
    }

    replaceThisGuests(order*1, length)
    document.getElementById(`guest-${length}`).remove()
}

function replaceThisGuests(order, length) {
    if (order == length)
        return
    for (let i = order; i < length; i++) {
        document.querySelector(`#name-${i}`).value = document.querySelector(`#name-${i + 1}`).value
        document.querySelector(`#gender-${i}`).value = document.querySelector(`#gender-${i + 1}`).value
        document.querySelector(`#guest-type-${i}`).value = document.querySelector(`#guest-type-${i + 1}`).value
        document.querySelector(`#identity-number-${i}`).value = document.querySelector(`#identity-number-${i + 1}`).value
        document.querySelector(`#address-${i}`).value = document.querySelector(`#address-${i + 1}`).value
    }
}

function done(index) {
    let formGuest = document.getElementById("formGuests")
    if (formGuest.checkValidity() && confirm("Bạn chắc chắn xác nhận?") == true) {
        let length = document.querySelector("#list-guests").children.length
        let data = {}
        for (let i = 0; i < length; i++) {
            let name = document.getElementById(`name-${i+1}`).value
            let gender = document.getElementById(`gender-${i+1}`).value
            let type = document.getElementById(`guest-type-${i+1}`).value
            let identity_number = document.getElementById(`identity-number-${i+1}`).value
            let address = document.getElementById(`address-${i+1}`).value
            data[(i+1) + ""] = {
                'order': i + 1,
                'name': name,
                'gender': gender,
                'type': type,
                'identity_number': identity_number,
                'address': address
            }
        }

        fetch(`/api/booking/rooms/${index}/confirm`, {
            method: "post",
            body: JSON.stringify({
                data
            }),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => res.json()).then((data) => {
            if(data) {
                alert("Thành công")
                window.location = "/staff/booking/rooms"
            }
            else
                alert("Đã có lỗi xảy ra")
        })
    }

}


function deleteRoom(index) {
    if (confirm("Bạn chắc chắn xóa?") == true) {
        fetch(`/api/booking/rooms/${index}`, {
            method: "delete"
        }).then(res => res.json()).then((data) => {
            if(data) {
                window.location = "/staff/booking/rooms"
            }
            else
                alert("Đã có lỗi xảy ra")
        })
    }
}


function staffBook() {
    if (confirm("Bạn chắc chắn lập đơn đặt này không?") == true) {
        let spinner = document.getElementById("my-spinner")
        spinner.classList.remove("d-none")
        fetch('/api/booking/rooms/confirm-book').then(res => res.json()).then((data) => {
            spinner.classList.add("d-none")
            if(data['status'] == 'success') {
                alert("Thành công")
                window.location = "/staff/booking"
            }
            else if(data['status'] == 'not yet')
                alert("Vui lòng điền đầy đủ thông tin cho các phòng")
            else
                alert("Đã có lỗi xảy ra")
        })
    }
}

function staffRent() {
    if (confirm("Bạn chắc chắn lập đơn đặt này không?") == true) {
        let spinner = document.getElementById("my-spinner")
        spinner.classList.remove("d-none")
        fetch('/api/booking/rooms/confirm-rent').then(res => res.json()).then((data) => {
            spinner.classList.add("d-none")
            if(data['status'] == 'success') {
                alert("Thành công")
                window.location = "/staff/booking"
            }
            else if(data['status'] == 'not yet')
                alert("Vui lòng điền đầy đủ thông tin cho các phòng")
            else
                alert("Đã có lỗi xảy ra")
        })
    }
}

function staffCancel() {
    if (confirm("Bạn chắc chắn hủy đơn này không?") == true) {
        fetch('/api/booking/rooms/cancel').then(res => res.json()).then((data) => {
            window.location = "/staff/booking"
        })
    }
}