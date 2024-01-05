function confirmReservation() {
    if (confirm("Bạn chắc chắn xác nhận không?") == true) {
        let spinner = document.getElementById("my-spinner")
        spinner.classList.remove("d-none")
        fetch('/api/confirm').then(res => res.json()).then((data) => {
            if(data["status"] == 204) {
                alert("Đặt phòng thành công")
                spinner.classList.add("d-none")
                window.location="/booking"
            }
            else {
                alert("Đã có lỗi xảy ra xin vui lòng thử lại")
                spinner.classList.add("d-none")
                window.location="/booking"
            }
        })
    }
}