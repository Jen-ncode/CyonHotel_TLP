import re
from datetime import datetime, timedelta, date

import requests
from flask import render_template, session, request, redirect, jsonify
from flask_login import login_user, current_user, logout_user
from pdfkit import from_url

from CyonApp import app, utils, dao, send_mail
from CyonApp.models import UserRole


def index():
    check_in = datetime.now()
    check_out = check_in + timedelta(1)
    return render_template('index.html', d1=check_in.strftime('%Y-%m-%d'), d2=check_out.strftime('%Y-%m-%d'))

#Hiển thị trang thông tin các phòng cần tìm
def step1():
    key = app.config['CART_KEY']
    key_date = app.config['DATE_KEY']

    if key not in session: #kiểm tra key có trong session không, nếu không => tạo tạo ds từ điển trong session vs key
        session[key] = {}

    today = datetime.now()
    if key_date not in session: #nếu key_date không có trong session => kiểm tra 2 tham số checkin checkout có được truyền vào request kh
        check_in = request.args.get('check-in')
        check_out = request.args.get('check-out')

        if check_in == "" or check_in is None:
            check_in = today.strftime('%Y-%m-%d')
        if check_out == "" or check_out is None:
            check_out = (today + timedelta(1)).strftime('%Y-%m-%d') #ngày hiện tại + 1 ngày => chuyển đổi thành chuỗi vơi định dạng ngày tháng năm
        #lưu thông tin checkin checkout vào session với khóa key_date
        session[key_date] = {
            "check-in": check_in,
            "check-out": check_out
        }
    #nếu key_date đã tồn tại trong sesstion, lấy thông tin checkin checkout từ session
    else:
        check_in = session[key_date]["check-in"]
        check_out = session[key_date]["check-out"]

    #ngày sau check-in
    min_check_out = datetime.strptime(check_in, '%Y-%m-%d') #chuyển đổi giá trị checkin thành đối tượng datetime bằng cách sd strptime
    min_check_out += timedelta(1) #cộng thêm 1 ngày = cách sd timedelta
    min_check_out = min_check_out.strftime('%Y-%m-%d') #chuyển đổi kết quả thành chuỗi với định dạng ngày tháng năm

    min_check_in = today.strftime('%Y-%m-%d') #lấy ngày hiện tại và chuyển đổi thành chuỗi vs định dạng ngày tháng năm
    days = utils.get_num_of_days(session[key_date]) #lấy số ngày giữa ngày hiện tại và ngày checkout

    #Lấy giá trị truyền vào => giá tiền min max / 1 ngày, từ khóa tìm phòng, số khách
    min_price = int(request.args.get('min-price')) / days if request.args.get('min-price') else None
    max_price = int(request.args.get('max-price')) / days if request.args.get('max-price') else None
    kw = request.args.get('keyword') if request.args.get('keyword') else ""
    num_of_guests = request.args.get('num-of-guests')
    room_types = dao.load_room_types(kw=kw, min_price=min_price, max_price=max_price, num_of_guests=num_of_guests)

    #duyệt qua các phòng trong 1 loại phòng
    for rt in room_types:
        rt.available = dao.get_available_room(check_in, check_out, rt.id).count() #lấy ds phòng có sẵn từ dao trong khoảng tgian checkin-out và đếm số lượng phòng có sẵn
    info_cart = utils.cart_stats(session[key]) # lấy thông tin thống kê về giỏ hàng từ session hiện tại
    total_quantity = info_cart["total_quantity"]
    total_amount = info_cart["total_amount"]

    return render_template('booking/book.html', check_in=check_in, check_out=check_out, min_check_out=min_check_out,
                           min_check_in=min_check_in, rt=room_types,
                           total_quantity=total_quantity, total_amount=total_amount, days=days, min_price=min_price,
                           max_price=max_price, kw=kw, num_of_guests=num_of_guests)

#Nhập, lấy thông tin đặt phòng của khách hàng với số lượng khách thuê(chi tiết đặt phòng)
def step2():
    key = app.config['CART_KEY']
    cart = session[key]
    if key in session:
        max_guests = 0

        for c in cart:
            max_guests += cart[c]["max_people"] * cart[c]["quantity"]

        info_cart = utils.cart_stats(session[key])
        total_quantity = info_cart["total_quantity"]
        total_amount = info_cart["total_amount"]

        min_guests = total_quantity

        if request.form.get("guest-amount") == "" or request.form.get("guest-amount") is None:
            guest_amount = min_guests
        else:
            guest_amount = request.form.get("guest-amount")

        return render_template('booking/details.html', min_guests=min_guests, max_guests=max_guests,
                               total_quantity=total_quantity, total_amount=total_amount, guest_amount=int(guest_amount))
    else:
        return redirect("/booking")

#xác nhận đặt phòng
def step3():
    key_details = app.config['DETAILS_KEY']
    if key_details in session:
        total_bill = utils.get_total(session[key_details])
        return render_template('booking/confirm.html', total=total_bill)
    else:
        return redirect("/booking")


def rooms_suites():
    rt = dao.load_room_types()
    return render_template("rooms_suites.html", rooms=rt, rooms_count=len(rt))


def rooms_suites_details(roomType_id):
    rt = dao.load_room_types(id=roomType_id)
    return render_template("rooms_details.html", rooms=rt)


def staff_login():
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = utils.check_login(username=username, password=password, role=UserRole.Staff)
        if user:
            login_user(user=user)
            return redirect('/staff')
        else:
            err_msg = 'Tài khoản hoặc mật khẩu của bạn không chính xác, vui lòng nhập lại'

    return render_template("staff/login.html", err_msg=err_msg)


def staff():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff:
        return render_template('staff/staff.html')
    else:
        return redirect('/login')


def signin_admin():
    if request.method.__eq__('POST'):
        username = request.form['username']
        password = request.form['password']
        user = utils.check_login(username=username,
                                 password=password,
                                 role=UserRole.Admin)
        if user:
            login_user(user=user)
            return redirect('/admin')
        else:
            err_msg = "Tài khoản không tồn tại, vui lòng thử lại"
    return redirect('/admin')


def change_rule():
    if request.method.__eq__('POST'):
        surcharge = request.form['surcharge']
        factor = request.form['factor']

        rule = {
            "foreigner_factor": factor,
            "surcharge": surcharge
        }

        dao.save_policy(rule)

    return redirect('/admin/rule')


def update_date():
    data = request.json

    key_date = app.config['DATE_KEY']
    if session[key_date]["check-in"] != data['check-in'] or session[key_date]["check-out"] != data['check-out']:
        if key_date in session:
            del session[key_date]
        key = app.config['CART_KEY']
        if key in session:
            del session[key]
        return jsonify(True)
    return jsonify(False)


def book_room():
    data = request.json

    key = app.config['CART_KEY']
    cart = session[key] if key in session else {}
    key_date = app.config['DATE_KEY']
    date = session.get(key_date)

    id = str(data['id'])
    name = data['name']
    price = data['price']
    max_people = data['max_people']

    room_types = dao.load_room_types()
    for rt in room_types:
        rt.available = dao.get_available_room(date["check-in"], date["check-out"], rt.id).count()
        if id in cart and cart[id]['quantity'] > rt.available:
            return jsonify()

    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "max_people": max_people,
            "quantity": 1
        }

    session[key] = cart

    return jsonify(cart[id])


def update_cart(roomType_id):
    key = app.config['CART_KEY']
    key_date = app.config['DATE_KEY']
    cart = session.get(key)
    date = session.get(key_date)
    room_types = dao.load_room_types()
    for rt in room_types:
        rt.available = dao.get_available_room(date["check-in"], date["check-out"], rt.id).count()
        if int(request.json['quantity']) > rt.available:
            return jsonify()
    if cart and roomType_id in cart:
        cart[roomType_id]['quantity'] = int(request.json['quantity'])

    session[key] = cart

    return jsonify(cart[roomType_id])


def delete_cart(roomType_id):
    key = app.config['CART_KEY']

    cart = session.get(key)
    if cart and roomType_id in cart:
        del cart[roomType_id]

    session[key] = cart

    return jsonify()


def total():
    key = app.config['CART_KEY']

    cart = session.get(key)

    return jsonify(utils.cart_stats(cart))


def get_cart():
    key = app.config['CART_KEY']
    if key in session:
        cart = session.get(key)
        return jsonify(cart)
    else:
        return jsonify({})


def del_cart():
    key = app.config['CART_KEY']
    key_date = app.config['DATE_KEY']

    if key in session:
        del session[key]
    if key_date in session:
        del session[key_date]
    return jsonify()


def guests():
    data = request.json
    data = data['data']

    key_orderer = app.config['ORDERER_KEY']
    key_details = app.config['DETAILS_KEY']
    key = app.config['CART_KEY']
    session[key_orderer] = data["contactInfo"]
    session[key_details] = data["rooms"]

    policy = dao.load_policy()
    for r in session[key_details]:
        room_type_id = session[key_details][r]["room_type_id"]
        price = session[key][room_type_id]['price']
        session[key_details][r]["price"] = price
        session[key_details][r]["name"] = r.replace("-", " ")

        for g in session[key_details][r]["guests"].values():
            g['name'] = re.sub(' +', ' ', g['name']).capitalize()
            if g["type"] == '2':
                session[key_details][r]["foreigner"] = float(policy["foreigner_factor"])

        if len(session[key_details][r]["guests"]) >= 3:
            session[key_details][r]["surcharge"] = price * float(policy["surcharge"])

        if "foreigner" in session[key_details][r]:
            price = price * float(policy["foreigner_factor"])

        if "surcharge" in session[key_details][r]:
            price += price * float(policy["surcharge"])

        session[key_details][r]["total"] = price

    return jsonify()


def confirm_bill():
    key_details = app.config['DETAILS_KEY']
    key_orderer = app.config['ORDERER_KEY']
    key_date = app.config['DATE_KEY']
    key = app.config['CART_KEY']

    date = session[key_date]
    cart = session[key]

    total_bill = "{:,.0f}".format(utils.get_total(session[key_details])) + " VNĐ"
    email = session[key_orderer]["email"]
    name = session[key_orderer]["name"]
    check_in = (datetime.strptime(date["check-in"], '%Y-%m-%d')).strftime('%d-%m-%Y')
    check_out = (datetime.strptime(date["check-out"], '%Y-%m-%d')).strftime('%d-%m-%Y')
    try:
        dao.save_reservation(session[key_details], session[key_date], session[key_orderer])
    except:
        return jsonify({'status': 500})

    send_mail.send(name, email, check_in, check_out, cart, total_bill)
    if key in session:
        del session[key]
    if key_date in session:
        del session[key_date]
    if key_orderer in session:
        del session[key_orderer]
    if key_details in session:
        del session[key_details]

    return jsonify({'status': 204})


def verify_email():
    data = request.json
    email = data['email']
    return jsonify(requests.get(
        "https://isitarealemail.com/api/email/validate",
        params={'email': email}).json()['status'])


def rent():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff:
        return render_template('staff/rent.html')
    else:
        return redirect('/login')


def reservations_to_rent():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff:
        check_in = request.args.get('check-in') if request.args.get('check-in') else ""
        check_out = request.args.get('check-out') if request.args.get('check-out') else ""

        orderer_name = request.args.get('orderer-name') if request.args.get('orderer-name') else ""
        orderer_email = request.args.get('orderer-email') if request.args.get('orderer-email') else ""

        reservations = dao.get_reservation(check_in=check_in, check_out=check_out, orderer_name=orderer_name,
                                           orderer_email=orderer_email, did_guests_check_in=False)
        for rs in reservations:
            t = 0
            for ds in rs.rooms:
                t += ds.price
            rs.total = t

        return render_template('staff/reservations.html', r=reservations, check_in=check_in, check_out=check_out,
                               orderer_name=orderer_name, orderer_email=orderer_email, total=total)

    else:
        return redirect('/login')


def change_reservation(reservation_id):
    dao.change_reservation(reservation_id)

    return jsonify()


def paypal():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff:
        check_in = request.args.get('check-in') if request.args.get('check-in') else ""
        check_out = request.args.get('check-out') if request.args.get('check-out') else ""

        orderer_name = request.args.get('orderer-name') if request.args.get('orderer-name') else ""
        orderer_email = request.args.get('orderer-email') if request.args.get('orderer-email') else ""

        reservations = dao.get_reservation(check_in=check_in, check_out=check_out, orderer_name=orderer_name,
                                           orderer_email=orderer_email, did_guests_check_in=True, is_pay=False)
        for rs in reservations:
            t = 0
            for ds in rs.rooms:
                t += ds.price
            rs.total = t

        return render_template('staff/paypal.html', r=reservations, check_in=check_in, check_out=check_out,
                               orderer_name=orderer_name, orderer_email=orderer_email, total=total)

    else:
        return redirect('/login')


def pay_reservation(reservation_id):
    dao.paypal_reservation(reservation_id)
    return jsonify()


def staff_logoff():
    logout_user()
    return jsonify()


def hash_pass():
    import hashlib
    data = request.json
    password = data['password']
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return jsonify(password)


def staff_booking():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff:
        key_i = app.config['S_INFO_KEY']
        key_d = app.config['S_DETAILS_KEY']
        if key_i in session:
            del session[key_i]
        if key_d in session:
            del session[key_d]
        return render_template("staff/booking.html")
    else:
        return redirect('/login')



def input_info():
    data = request.json

    key_i = app.config['S_INFO_KEY']
    session[key_i] = data['data']

    return jsonify()


def info_rooms():
    key_i = app.config['S_INFO_KEY']
    if key_i not in session:
        return redirect("/staff/booking")
    else:
        info = session[key_i]
        amount = int(info['amount_rooms'])
        key_d = app.config['S_DETAILS_KEY']
        if key_d not in session:
            session[key_d] = {}

        d = session[key_d]
        for i in range(amount):
            if str(i + 1) not in session[key_d]:
                d[str(i + 1)] = {}
        session[key_d] = d
        return render_template("staff/booking_rooms.html", amount=amount)


def add_room():
    key_i = app.config['S_INFO_KEY']
    if key_i not in session:
        return jsonify()

    temp = session[key_i]
    a = int(temp['amount_rooms']) + 1
    temp['amount_rooms'] = a
    session[key_i] = temp

    key_d = app.config['S_DETAILS_KEY']
    temp2 = session[key_d]
    temp2[str(a)] = {}
    session[key_d] = temp2
    print(session[key_d])
    return jsonify(a)


def staff_room_details(room_index):
    key_i = app.config['S_INFO_KEY']
    if key_i not in session:
        return redirect("/staff/booking")

    check_in = session[key_i]["check-in"]
    check_out = session[key_i]["check-out"]
    days = utils.get_num_of_days(session[key_i])
    kw = request.args.get("keyword") if request.args.get("keyword") else ""
    min_price = int(request.args.get('min-price')) / days if request.args.get('min-price') else None
    max_price = int(request.args.get('max-price')) / days if request.args.get('max-price') else None
    num_of_guests = request.args.get('num-of-guests')
    room_types = dao.load_room_types(kw=kw, min_price=min_price, max_price=max_price, num_of_guests=num_of_guests)

    for rt in room_types:
        rt.available = dao.get_available_room(check_in, check_out, rt.id).count()
    return render_template("staff/details_room.html", index=room_index, rt=room_types, kw=kw, min_price=min_price,
                           max_price=max_price, num_of_guests=num_of_guests, days=days)


def staff_choose_room(room_index):
    data = request.json
    key_d = app.config['S_DETAILS_KEY']
    if key_d not in session or room_index not in session[key_d]:
        return jsonify()

    d = session[key_d]
    d[room_index] = data['data']
    session[key_d] = d
    return jsonify(True)


def staff_confirm_room(room_index):
    data = request.json
    key_d = app.config['S_DETAILS_KEY']
    if key_d not in session or room_index not in session[key_d]:
        return jsonify()

    details = session[key_d]
    details[room_index]['guests'] = data['data']

    price = details[room_index]['price']

    policy = dao.load_policy()
    details[room_index]["foreigner"] = 1
    details[room_index]["surcharge"] = 0

    for g in details[room_index]['guests'].values():
        g['name'] = re.sub(' +', ' ', g['name']).title()
        if g["type"] == '2':
            details[room_index]["foreigner"] = float(policy["foreigner_factor"])

    if len(details[room_index]["guests"]) >= 3:
        details[room_index]["surcharge"] = price * float(policy["surcharge"])

    if "foreigner" in details[room_index]:
        price = price * float(details[room_index]["foreigner"])

    if "surcharge" in details[room_index]:
        price += float(details[room_index]["surcharge"])

    details[room_index]["total"] = price
    details[room_index]["amount-guests"] = len(details[room_index]["guests"])
    session[key_d] = details

    return jsonify(session[key_d])


def staff_del_room(room_index):
    key_d = app.config['S_DETAILS_KEY']
    if key_d not in session or room_index not in session[key_d]:
        return jsonify()

    details = session[key_d]
    for i in range(int(room_index), len(details)):
        details[str(i)] = details[str(i + 1)]

    del details[str(len(details))]

    session[key_d] = details

    key_i = app.config['S_INFO_KEY']
    if key_i not in session:
        return jsonify()

    temp = session[key_i]
    temp['amount_rooms'] = len(details)

    return jsonify(True)


def staff_confirm_book():
    key_d = app.config['S_DETAILS_KEY']
    key_i = app.config['S_INFO_KEY']

    if key_i not in session or key_d not in session:
        return jsonify({'status': 'error'})

    details = session[key_d]
    for d in details:
        if 'guests' not in details[d]:
            return jsonify({'status': 'not yet'})
    info = session[key_i]

    info['name'] = info['orderer_name']
    info['email'] = info['orderer_email']
    session[key_i] = info
    try:
        dao.save_reservation(session[key_d], session[key_i], session[key_i])
    except:
        return jsonify({'status': 'error'})

    total_bill = "{:,.0f}".format(utils.get_total(details)) + " VNĐ"
    send_mail.send2(info['name'], info['email'], info['check-in'], info['check-out'], details, total_bill)
    del session[key_d]
    del session[key_i]

    return jsonify({'status': 'success'})


def staff_confirm_rent():
    key_d = app.config['S_DETAILS_KEY']
    key_i = app.config['S_INFO_KEY']

    if key_i not in session or key_d not in session:
        return jsonify({'status': 'error'})

    details = session[key_d]
    for d in details:
        if 'guests' not in details[d]:
            return jsonify({'status': 'not yet'})
    info = session[key_i]

    info['name'] = info['orderer_name']
    info['email'] = info['orderer_email']
    session[key_i] = info
    try:
        dao.save_reservation(session[key_d], session[key_i], session[key_i], rent=True)
    except:
        return jsonify({'status': 'error'})

    total_bill = "{:,.0f}".format(utils.get_total(details)) + " VNĐ"
    send_mail.send2(info['name'], info['email'], info['check-in'], info['check-out'], details, total_bill)
    del session[key_d]
    del session[key_i]

    return jsonify({'status': 'success'})


def staff_cancel():
    key_d = app.config['S_DETAILS_KEY']
    key_i = app.config['S_INFO_KEY']

    if key_d in session:
        del session[key_d]

    if key_i in session:
        del session[key_i]

    return jsonify()