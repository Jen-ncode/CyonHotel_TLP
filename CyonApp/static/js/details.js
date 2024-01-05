function continueBook2(guest_amount) {
    var form = document.getElementById("guests-info-form")
    if (form.checkValidity()) {
        data = {}

        data["contactInfo"] = {}
        data["contactInfo"]["name"] = document.getElementById("name").value
        data["contactInfo"]["email"] = document.getElementById("email").value

        data["rooms"] = {}

        var rooms = document.querySelectorAll(".info-box")
        rooms.forEach(r => {
            let roomName = r.getAttribute("alt")
            let roomTypeId = r.getAttribute("rel")
            data["rooms"][roomName] = {
                "room_type_id": roomTypeId
            }
        })

        for (let i = 0; i < guest_amount; i++) {
            let room = document.getElementById(`room-${i+1}`).value

            if (!data["rooms"][room]["guests"])
                data["rooms"][room]["guests"] = {}

            let name = document.getElementById(`name-${i+1}`).value
            let gender = document.getElementById(`gender-${i+1}`).value
            let type = document.getElementById(`guest-type-${i+1}`).value
            let identity_number = document.getElementById(`identity-number-${i+1}`).value
            let address = document.getElementById(`address-${i+1}`).value

            data["rooms"][room]["guests"][i + ""] = {
                "name": name,
                "gender": gender,
                "type": type,
                "identity_number": identity_number,
                "address": address
            }

        }

        //check empty
        let haveEmptyRoom = false
        rooms.forEach(r => {
            let roomName = r.getAttribute("alt")
            let g = data["rooms"][roomName]["guests"]

            if (typeof g == 'undefined') {
                haveEmptyRoom = true
            }
        })

        if (haveEmptyRoom) {
            alert("Tồn tại phòng chưa có khách ở")
            return
        }

        console.log(data)
        fetch('/api/guests', {
            method: "post",
            body: JSON.stringify({
                data
            }),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => res.json()).then((data) => {
            window.location="/booking/confirm";
        })
    }
    else
        alert("Vui lòng điền đầy đủ thông tin")
}


var available = `<i class="fa-regular fa-user"></i>`
var unavailable = `<i class="fa-solid fa-user"></i>`
var a = document.querySelector(".select-room")
var b = a.children
var dict = {}
for (let i = 1; i < b.length; i++) {
    dict[b[i].value] = {}
    dict[b[i].value]["max"] = b[i].getAttribute("rel")*1
    dict[b[i].value]["current"] = 0
}

function resetCurrent(){
    for (let i = 1; i < b.length; i++) {
        dict[b[i].value]["current"] = 0
    }
}

function updateAvailable(obj) {
    //check
    if (obj.value != "") {
        let val = obj.value
        let cur = dict[val]["current"]
        let max = dict[val]["max"]
        if (cur == max) {
            obj.value = ""
            alert("Phòng bạn vừa chọn đã hết chổ trống")
        }

    }


    resetCurrent()
    console.log(dict)
    var ipSelect = document.querySelectorAll(".select-room")

    for(let i = 0; i < ipSelect.length; i++) {
        if (ipSelect[i].value != "") {

            let val = ipSelect[i].value
            dict[val]["current"]++
        }
    }

    var infoBox = document.querySelectorAll(".info-box")
    for(let i = 0; i < infoBox.length; i++) {
        var name = infoBox[i].getAttribute("alt")
        var current = dict[name]["current"]
        var max =  dict[name]["max"]
        var peopleAmount = infoBox[i].querySelector(".people-amount")
        var innerPeopleAmount = ``
        for (let j = 0; j < current; j++)
            innerPeopleAmount += unavailable
        for (let j = 0; j < max-current; j++)
            innerPeopleAmount += available
        peopleAmount.innerHTML = `${innerPeopleAmount}`
    }
}

window.onscroll = function() {
    if (window.innerWidth >= 768) {
        if (window.scrollY >= 90)
            document.querySelector(".my-bill").classList.add("position-fixed", "top-0", "w-25")
        else
            document.querySelector(".my-bill").classList.remove("position-fixed", "top-0", "w-25")
    }
}