from CyonApp import app, dao, admin, utils, send_mail, login, controllers


app.add_url_rule('/', 'index', controllers.index)
app.add_url_rule('/rooms-suites', 'rooms_suites', controllers.rooms_suites)
app.add_url_rule('/rooms-suites/<roomType_id>', 'rooms_suites_details', controllers.rooms_suites_details)

app.add_url_rule('/booking', 'booking', controllers.step1, methods=["POST", "GET"])
app.add_url_rule('/booking/details', 'details', controllers.step2, methods=["POST", "GET"])
app.add_url_rule('/booking/confirm', 'confirm', controllers.step3)
app.add_url_rule('/login', 'staff_login', controllers.staff_login, methods=["POST", "GET"])
app.add_url_rule('/staff', 'staff', controllers.staff, methods=["POST", "GET"])
app.add_url_rule('/admin-login', 'signin_admin', controllers.signin_admin, methods=["POST"])
app.add_url_rule('/rule-change', 'change_rule', controllers.change_rule, methods=["PUT"])

app.add_url_rule('/api/cart/book', 'book_room', controllers.book_room, methods=['POST'])
app.add_url_rule('/api/cart/date', 'update_date', controllers.update_date, methods=['POST'])
app.add_url_rule('/api/cart/<roomType_id>', 'update_cart', controllers.update_cart, methods=['PUT'])
app.add_url_rule('/api/cart/<roomType_id>', 'delete_cart', controllers.delete_cart, methods=['DELETE'])
app.add_url_rule('/api/cart/total', 'total', controllers.total)

app.add_url_rule('/api/cart/total', 'total', controllers.total)
app.add_url_rule('/api/get-cart', 'get_cart', controllers.get_cart)
app.add_url_rule('/api/renew', 'del_cart', controllers.del_cart)
app.add_url_rule('/api/guests', 'guests', controllers.guests, methods=["POST"])
app.add_url_rule('/api/confirm', 'confirm_bill', controllers.confirm_bill)
app.add_url_rule('/api/verify-email', 'verify_email', controllers.verify_email, methods=["POST"])

app.add_url_rule('/staff/rent', 'rent', controllers.rent)
app.add_url_rule('/staff/booking', 'staff_booking', controllers.staff_booking)
app.add_url_rule('/api/staff/info', 'input_info', controllers.input_info, methods=["POST"])
app.add_url_rule('/staff/booking/rooms', 'info_rooms', controllers.info_rooms)
app.add_url_rule('/api/booking/rooms/add', 'add_room', controllers.add_room, methods=['PUT'])
app.add_url_rule('/staff/booking/rooms/<room_index>', 'staff_room_details', controllers.staff_room_details)

app.add_url_rule('/api/booking/rooms/<room_index>/choose', 'staff_choose_room', controllers.staff_choose_room,
                 methods=["POST"])
app.add_url_rule('/api/booking/rooms/<room_index>', 'staff_del_room', controllers.staff_del_room, methods=["DELETE"])
app.add_url_rule('/api/booking/rooms/confirm-book', 'staff_confirm_book', controllers.staff_confirm_book)
app.add_url_rule('/api/booking/rooms/confirm-rent', 'staff_confirm_rent', controllers.staff_confirm_rent)
app.add_url_rule('/api/booking/rooms/cancel', 'staff_cancel', controllers.staff_cancel)

app.add_url_rule('/api/booking/rooms/<room_index>/confirm', 'staff_confirm_room', controllers.staff_confirm_room,
                 methods=["POST"])

app.add_url_rule('/staff/rent/reservations', 'reservations_to_rent', controllers.reservations_to_rent,
                 methods=["GET"])
app.add_url_rule('/api/reservations/<reservation_id>', 'change_reservation', controllers.change_reservation,
                 methods=['PUT'])
app.add_url_rule('/staff/paypal', 'paypal', controllers.paypal, methods=["GET"])
app.add_url_rule('/api/reservations/paypal/<reservation_id>', 'pay_reservation', controllers.pay_reservation,
                 methods=['PUT'])
app.add_url_rule('/api/staff/logoff', 'staff_logoff', controllers.staff_logoff)

app.add_url_rule('/api/hash-password', 'hash_pass', controllers.hash_pass, methods=["POST", "GET"])


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


if __name__ == '__main__':
    from CyonApp.admin import *
    app.run(debug=True, port=5002)