import re
from datetime import datetime, timedelta, date

import requests
from flask import render_template, session, request, redirect, jsonify
from flask_login import login_user, current_user, logout_user
from pdfkit import from_url

from CyonApp import app, utils, dao, send_mail
from CyonApp.models import UserRole


def index(): # Hiển thị ngày hiện tại và ngày tiếp theo
    check_in = datetime.now()
    check_out = check_in + timedelta(1)
    return render_template('index.html', d1=check_in.strftime('%Y-%m-%d'),
                           d2=check_out.strftime('%Y-%m-%d'))


def guests():
    data = request.json # Lấy dl từ yc JSON.
    data = data['data'] # Lấy dl từ 'data' của yc JSON.

    key_orderer = app.config['ORDERER_KEY']
    key_details = app.config['DETAILS_KEY']
    key = app.config['CART_KEY']
    session[key_orderer] = data["contactInfo"]
    session[key_details] = data["rooms"]

    policy = dao.load_policy() # Tải policy từ CSDL.
    for r in session[key_details]: # Duyệt qua từng phòng trong session.
        room_type_id = session[key_details][r]["room_type_id"] # Lấy ID LP.
        price = session[key][room_type_id]['price'] # Lấy giá của LP từ giỏ hàng.
        session[key_details][r]["price"] = price # Lưu giá vào session..
        session[key_details][r]["name"] = r.replace("-", " ") # Chuyển tên phòng từ có gạch ngang sang ko gạch ngang.

        for g in session[key_details][r]["guests"].values(): # Duyệt qua từng khách trong ds khách của phòng.
            g['name'] = re.sub(' +', ' ', g['name']).capitalize() # Chỉnh tên của khách kh trắng và chữ hoa
            if g["type"] == '2': # Nếu khách là nc ngoài,
                session[key_details][r]["foreigner"] = float(policy["foreigner_factor"]) # App hệ số cho nc ngoai.

        if len(session[key_details][r]["guests"]) >= 3: # Nếu sl khách >= 3,
            session[key_details][r]["surcharge"] = price * float(policy["surcharge"]) # áp dụng phụ phí.

        if "foreigner" in session[key_details][r]: # Nếu có khách là người nước ngoài,
            price = price * float(policy["foreigner_factor"]) # tăng giá theo hệ số cho người nước ngoài.

        if "surcharge" in session[key_details][r]: # Nếu có phụ phí,
            price += price * float(policy["surcharge"]) # tăng giá theo phụ phí.

        session[key_details][r]["total"] = price # Lưu tổng giá vào chi tiết phòng.

    return jsonify() # Cuối cùng, trả về JSON trống.


def signin_admin(): # Xử lý đăng nhập của Admin
    if request.method.__eq__('POST'): # Ktr yc có phải POST ko
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


def staff_login():  # Xử lý đăng nhập của Staff
    err_msg = ''  # Ktr 1 thông báo lỗi rỗng
    if request.method.__eq__('POST'):  # Ktr yc có phải POST ko
        username = request.form.get('username')
        password = request.form.get('password')
        # Ktr tt login là Staff = hàm check_login từ utils.py
        user = utils.check_login(username=username, password=password, role=UserRole.Staff)
        if user:
            login_user(user=user)
            return redirect('/staff')
        else:
            err_msg = 'Tài khoản hoặc mật khẩu của bạn không chính xác, vui lòng nhập lại'

    return render_template("staff/login.html", err_msg=err_msg)


def staff():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff:
        return render_template('staff/staff.html')  # Xác thực là Staff thì chuyển đến trang staff
    else:
        return redirect('/login')  # Chưa xác thực là Staff thì chuyển đến trang login


def staff_logoff():
    logout_user()
    return jsonify()


def staff_booking():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff: #Nếu xác thực là nhân viên,
        key_i = app.config['S_INFO_KEY']
        key_d = app.config['S_DETAILS_KEY']
        if key_i in session: # Nếu khóa cho thông tin tồn tại
            del session[key_i] # xóa thông tin
        if key_d in session: # Nếu khóa cho chi tiết tồn tại
            del session[key_d] # xóa chi tiết khỏi phiên làm việc.
        return render_template("staff/booking.html") # Trả về trang 'staff/booking.html'.
    else: # Nếu không là nhân viên,
        return redirect('/login')


def staff_room_details(room_index):
    key_i = app.config['S_INFO_KEY'] # Lấy khóa
    if key_i not in session:
        return redirect("/staff/booking") # chuyển hướng 'staff/booking'.

    check_in = session[key_i]["check-in"] # Lấy ngày nhận phòng
    check_out = session[key_i]["check-out"] # Lấy ngày trả phòng
    days = utils.get_num_of_days(session[key_i]) # Tính số ngày ở
    kw = request.args.get("keyword") if request.args.get("keyword") else "" # Lấy từ khóa từ yêu cầu
    min_price = int(request.args.get('min-price')) / days if request.args.get('min-price') else None # Lấy giá tối thiểu
    max_price = int(request.args.get('max-price')) / days if request.args.get('max-price') else None # Lấy giá tối đa
    num_of_guests = request.args.get('num-of-guests') # Lấy số lượng khách
    room_types = dao.load_room_types(kw=kw, min_price=min_price, max_price=max_price, num_of_guests=num_of_guests)
    # Tải loại phòng từ CSDL

    for rt in room_types: # Duyệt qua từng LP
        rt.available = dao.get_available_room(check_in, check_out, rt.id).count() # Tính số lượng phòng còn trống.

    # Trả về trang 'staff/details_room.html' với thông tin về phòng.
    return render_template("staff/details_room.html",
                           index=room_index,
                           rt=room_types,
                           kw=kw,
                           min_price=min_price,
                           max_price=max_price,
                           num_of_guests=num_of_guests,
                           days=days)


def staff_choose_room(room_index):
    data = request.json # Lấy dữ liệu từ  JSON.
    key_d = app.config['S_DETAILS_KEY'] # Lấy khóa
    if key_d not in session or room_index not in session[key_d]:
        return jsonify() # trả về một phản hồi JSON trống.

    d = session[key_d] # Lấy chi tiết
    d[room_index] = data['data'] # Cập nhật thông tin phòng trong chi tiết dựa trên dữ liệu.
    session[key_d] = d # Cập nhật chi tiết

    return jsonify(True) # Trả về JSON với True.


def staff_confirm_room(room_index):
    data = request.json # Lấy dữ liệu từ  JSON.
    key_d = app.config['S_DETAILS_KEY'] # Lấy khóa cho chi tiết.
    if key_d not in session or room_index not in session[key_d]:
        return jsonify() # trả về JSON trống.

    details = session[key_d] # Lấy chi tiết
    details[room_index]['guests'] = data['data'] # Cập nhật thông tin khách trong chi tiết dựa trên dữ liệu.

    price = details[room_index]['price'] # Lấy giá của phòng

    policy = dao.load_policy() # Tải chính sách từ CSDL.
    details[room_index]["foreigner"] = 1 # Đặt hệ số cho người nước ngoài là 1.
    details[room_index]["surcharge"] = 0 # Đặt phụ phí là 0.

    for g in details[room_index]['guests'].values(): # Duyệt qua từng khách trong danh sách khách của phòng.
        g['name'] = re.sub(' +', ' ', g['name']).title() # Chỉnh sửa tên của khách
        if g["type"] == '2': # Nếu khách là người nước ngoài,
            details[room_index]["foreigner"] = float(policy["foreigner_factor"]) # áp dụng hệ số cho người nước ngoài.

    if len(details[room_index]["guests"]) >= 3: # Nếu số lượng khách lớn hơn hoặc bằng 3,
        details[room_index]["surcharge"] = price * float(policy["surcharge"]) # áp dụng phụ phí.

    if "foreigner" in details[room_index]: # Nếu có khách là người nước ngoài,
        price = price * float(details[room_index]["foreigner"])# tăng giá theo hệ số cho người nước ngoài.

    if "surcharge" in details[room_index]: # Nếu có phụ phí,
        price += float(details[room_index]["surcharge"]) # tăng giá theo phụ phí.

    details[room_index]["total"] = price # Lưu tổng giá
    details[room_index]["amount-guests"] = len(details[room_index]["guests"]) # Lưu số lượng khách
    session[key_d] = details # Cập nhật chi tiết

    return jsonify(session[key_d])


def staff_del_room(room_index):
    key_d = app.config['S_DETAILS_KEY']
    if key_d not in session or room_index not in session[key_d]:
        return jsonify() # trả về JSON trống.

    details = session[key_d] # Lấy chi tiết
    for i in range(int(room_index), len(details)): # Duyệt qua từng pt trong chi tiết từ room_index đến cuối chi tiết.
        details[str(i)] = details[str(i + 1)] # Cập nhật phần tử thứ i bằng phần tử thứ i + 1.

    del details[str(len(details))] # Xóa phần tử cuối cùng

    session[key_d] = details # Cập nhật chi tiết

    key_i = app.config['S_INFO_KEY'] # Lấy khóa
    if key_i not in session: # Nếu khóa cho thông tin không tồn tại
        return jsonify() # trả về  JSON trống.

    temp = session[key_i] # Lấy thông tin từ phiên làm việc.
    temp['amount_rooms'] = len(details) # Cập nhật sl phòng trong thông tin bằng sl phần tử trong chi tiết.

    return jsonify(True) # Trả về JSON với True.


def staff_confirm_book():
    key_d = app.config['S_DETAILS_KEY']
    key_i = app.config['S_INFO_KEY']
    key_date = app.config['DATE_KEY']

    if key_i not in session or key_d not in session: # Nếu khóa cho thông tin hoặc chi tiết không tồn tại
        return jsonify({'status': 'error'}) # trả về  JSON với 'error'.

    details = session[key_d] # Lấy chi tiết
    for d in details: # Duyệt qua từng phần tử
        if 'guests' not in details[d]: # Nếu 'guests' không tồn tại
            return jsonify({'status': 'not yet'}) # trả về  JSON với 'not yet'.
    info = session[key_i] # Lấy thông tin từ phiên làm việc.

    info['name'] = info['orderer_name'] # Cập nhật tên .
    info['email'] = info['orderer_email'] # Cập nhật email.
    session[key_i] = info # Cập nhật thông tin
    try:
        dao.save_reservation(session[key_d], session[key_i], session[key_i]) # Lưu đặt phòng vào CSDL
    except:
        return jsonify({'status': 'error'}) # Nếu có lỗi, trả về JSON với'error'.

    total_bill = "{:,.0f}".format(utils.get_total(details)) + " VNĐ"
    send_mail.send2(info['name'], info['email'], info['check-in'], info['check-out'], details, total_bill) # Gửi email
    del session[key_d] # Xóa chi tiết
    del session[key_i] # Xóa thông tin

    return jsonify({'status': 'success'}) # Trả về JSON với  'success'.


def staff_confirm_rent():
    key_d = app.config['S_DETAILS_KEY']
    key_i = app.config['S_INFO_KEY']

    if key_i not in session or key_d not in session: # Nếu khóa cho thông tin hoặc chi tiết không tồn tại
        return jsonify({'status': 'error'}) # trả về JSON với 'error'.

    details = session[key_d] # Lấy chi tiết
    for d in details: # Duyệt qua từng phần tử
        if 'guests' not in details[d]: # Nếu 'guests' không tồn tại
            return jsonify({'status': 'not yet'}) # trả về JSON với 'not yet'.
    info = session[key_i] # Lấy thông tin

    info['name'] = info['orderer_name'] # Cập nhật tên
    info['email'] = info['orderer_email'] # Cập nhật email
    session[key_i] = info # Cập nhật thông tin
    try:
        dao.save_reservation(session[key_d], session[key_i], session[key_i], rent=True) # Lưu đặt phòng vào CSDL
    except:
        return jsonify({'status': 'error'}) # Nếu có lỗi, trả vềJSON với 'error'.

    total_bill = "{:,.0f}".format(utils.get_total(details)) + " VNĐ" # Tính tổng hóa đơn.
    send_mail.send2(info['name'], info['email'], info['check-in'], info['check-out'], details, total_bill) # Gửi email.
    del session[key_d] # Xóa chi tiết
    del session[key_i] # Xóa thông tin

    return jsonify({'status': 'success'}) # Trả về JSON với 'success'.


def staff_cancel():
    key_d = app.config['S_DETAILS_KEY']
    key_i = app.config['S_INFO_KEY']

    if key_d in session: # Nếu khóa cho chi tiết tồn tại
        del session[key_d] # xóa chi tiết

    if key_i in session: # Nếu khóa cho thông tin tồn tại
        del session[key_i] # xóa thông tin

    return jsonify()


def step1():
    key = app.config['CART_KEY']
    key_date = app.config['DATE_KEY']

    if key not in session: # KT session cho gh và ngày DP nếu chưa có
        session[key] = {}

    # Lấy ngày nhận và trả phòng từ yêu cầu. Nếu ko có thì lấy ngày HT và TT
    today = datetime.now()
    if key_date not in session:
        check_in = request.args.get('check-in')
        check_out = request.args.get('check-out')

        if check_in == "" or check_in is None:
            check_in = today.strftime('%Y-%m-%d')
        if check_out == "" or check_out is None:
            check_out = (today + timedelta(1)).strftime('%Y-%m-%d')

            # Lưu vào Session
        session[key_date] = {
            "check-in": check_in,
            "check-out": check_out
        }

    else:
        check_in = session[key_date]["check-in"]
        check_out = session[key_date]["check-out"]

    min_check_out = datetime.strptime(check_in, '%Y-%m-%d')
    min_check_out += timedelta(1)
    min_check_out = min_check_out.strftime('%Y-%m-%d')

    min_check_in = today.strftime('%Y-%m-%d')
    days = utils.get_num_of_days(session[key_date])

    # Lấy từ khóa và số lượng khách từ yêu cầu
    min_price = int(request.args.get('min-price')) / days if request.args.get('min-price') else None
    max_price = int(request.args.get('max-price')) / days if request.args.get('max-price') else None
    kw = request.args.get('keyword') if request.args.get('keyword') else ""
    num_of_guests = request.args.get('num-of-guests')
    room_types = dao.load_room_types(kw=kw, min_price=min_price, max_price=max_price, num_of_guests=num_of_guests)

    # Tính số lượng phòng còn trống cho mỗi loại phòng
    # Tính tổng số lượng và tổng giá tiền trong giỏ hàng
    for rt in room_types:
        rt.available = dao.get_available_room(check_in, check_out, rt.id).count()
    info_cart = utils.cart_stats(session[key])
    total_quantity = info_cart["total_quantity"]
    total_amount = info_cart["total_amount"]

    return render_template('booking/book.html', check_in=check_in, check_out=check_out, min_check_out=min_check_out,
                           min_check_in=min_check_in, rt=room_types,
                           total_quantity=total_quantity, total_amount=total_amount, days=days, min_price=min_price,
                           max_price=max_price, kw=kw, num_of_guests=num_of_guests)


def step2():
    key = app.config['CART_KEY']
    cart = session[key]
    # Kiểm tra giỏ hàng có tồn tại trong session không
    # Nếu có thì
    if key in session:
        max_guests = 0
        # Tính sl khách tối đa dụa vào sl phòng và sl khách
        # Tính tổng sl và tổng gt trong giỏ hàng
        for c in cart:
            max_guests += cart[c]["max_people"] * cart[c]["quantity"]
        info_cart = utils.cart_stats(session[key])
        total_quantity = info_cart["total_quantity"]
        total_amount = info_cart["total_amount"]

        # Lấy số lượng khách từ form. Nếu ko có thì sd sl khách tối thiểu
        min_guests = total_quantity
        if request.form.get("guest-amount") == "" or request.form.get("guest-amount") is None:
            guest_amount = min_guests
        else:
            guest_amount = request.form.get("guest-amount")

        return render_template('booking/details.html', min_guests=min_guests, max_guests=max_guests,
                               total_quantity=total_quantity, total_amount=total_amount, guest_amount=int(guest_amount))
    else:
        return redirect("/booking")


def step3(): # Ktr xem  CT đặt phòngcosos trong session không
    key_details = app.config['DETAILS_KEY']
    key_date = app.config['DATE_KEY']
    #Nếu CT ĐP có thì
    if key_details in session: # Tính tổng hóa đơn = tổng tiền * số ngày ở
        total_bill = utils.get_total(session[key_details])*utils.get_num_of_days(session[key_date])
        return render_template('booking/confirm.html', total=total_bill)
    else:
        return redirect("/booking")


def rooms_suites(): # Tải các loại phòng trong dao.py và gán cho rt
    rt = dao.load_room_types()
    return render_template("rooms_suites.html", rooms=rt, rooms_count=len(rt))


def rooms_suites_details(roomType_id):# Tải loại phòng có id là roomType_id trong dao.py và gán cho rt
    rt = dao.load_room_types(id=roomType_id)
    return render_template("rooms_details.html", rooms=rt)


def book_room():
    data = request.json # Lấy dl yc dưới dạng JSON và gán cho biến data

    key = app.config['CART_KEY']
    cart = session[key] if key in session else {}
    key_date = app.config['DATE_KEY']
    date = session.get(key_date)    # Lấy giỏ hàng và day DP từ session

    id = str(data['id'])
    name = data['name']
    price = data['price']
    max_people = data['max_people']

    room_types = dao.load_room_types()  # Tải các LP từ dao.py và tính sl phòng còn trống cho mỗi LP
    # Ktr sl phòng trong giỏ hàng > sl phòng còn trống trả về 1 JSON rỗng
    for rt in room_types:
        rt.available = dao.get_available_room(date["check-in"], date["check-out"], rt.id).count()
        if id in cart and cart[id]['quantity'] > rt.available:
            return jsonify()

    if id in cart:  # Nếu id của SP trong giỏ hàng đã có thì tăng sl của SP lên 1
        cart[id]['quantity'] += 1
    else: # Tự thêm SP vào giỏi hàng với TT từ data
        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "max_people": max_people,
            "quantity": 1
        }

    session[key] = cart # Cập nhật giỏ hàng

    return jsonify(cart[id]) # Trả về TT SP ở dạng JSON


def change_rule(): # Xử lý thay đổi các quy định
    if request.method.__eq__('POST'): # Ktr yc có phải POST ko
        surcharge = request.form['surcharge']
        factor = request.form['factor']
            # Lưu rule vào dao.py bằng sd hàm save_policy
        rule = {
            "foreigner_factor": factor,
            "surcharge": surcharge
        }

        dao.save_policy(rule)

    return redirect('admin/rule.html')


def update_date():
    data = request.json # Lấy dl yc dưới dạng JSON và gán cho biến data

    key_date = app.config['DATE_KEY']
    # Ktr ngay nhan va ngay tra phog
    # Nếu có sự khác của check_in và check_out sẽ xóa. Nếu đúng hay không đúng thì cũng trả về dạng JSON
    if session[key_date]["check-in"] != data['check-in'] or session[key_date]["check-out"] != data['check-out']:
        if key_date in session:
            del session[key_date]
        key = app.config['CART_KEY']
        if key in session:
            del session[key]
        return jsonify(True)
    return jsonify(False)


def update_cart(roomType_id): # Lấy giỏ hàng và ngày từ phiên làm việc.
    key = app.config['CART_KEY']
    key_date = app.config['DATE_KEY']
    cart = session.get(key) # Lấy giỏ hàng từ session
    date = session.get(key_date) # Lấy ngày từ session
    room_types = dao.load_room_types() # Tải all các LP từ CSDL.
    for rt in room_types:
        rt.available = dao.get_available_room(date["check-in"], date["check-out"], rt.id).count() # Tính sl phòng trống
        if int(request.json['quantity']) > rt.available: # Nếu sl yc > số phòng trống, trả về JSON trống.
            return jsonify()
    if cart and roomType_id in cart: # Nếu giỏ hàng tồn tại và LP đã có trong giỏ hàng, cập nhật sl LP đó.
        cart[roomType_id]['quantity'] = int(request.json['quantity'])

    session[key] = cart # Cập nhật giỏ hàng trong session

    return jsonify(cart[roomType_id]) # Trả về mục giỏ hàng đã cập nhật dưới dạng phản hồi JSON.


def delete_cart(roomType_id): # Hàm này nhận vào một tham số là roomType_id.
    key = app.config['CART_KEY'] # Lấy khóa cho giỏ hàng.

    cart = session.get(key) # Lấy giỏ hàng trong session
    if cart and roomType_id in cart: # Nếu giỏ hàng tồn tại và LP nằm trong giỏ hàng,
        del cart[roomType_id] # xóa LP đó khỏi giỏ hàng.

    session[key] = cart # Cập nhật giỏ hàng trong session

    return jsonify() # Trả về một phản hồi JSON trống.


def get_cart(): # Hàm này không nhận tham số nào.
    key = app.config['CART_KEY'] # Lấy khóa cho giỏ hàng.

    if key in session: # Nếu khóa tồn tại trong session
        cart = session.get(key) # lấy giỏ hàng từ session và trả về dưới dạng phản hồi JSON.
        return jsonify(cart)
    else:
        return jsonify({}) # Nếu không, trả về một phản hồi JSON trống.


def del_cart():
    key = app.config['CART_KEY'] # Lấy khóa cho giỏ hàng.
    key_date = app.config['DATE_KEY'] # Lấy khóa cho ngày.

    if key in session: # Nếu khóa cho giỏ hàng tồn tại trong session
        del session[key] # xóa giỏ hàng khỏi session.
    if key_date in session: # Nếu khóa cho ngày tồn tại trong session,
        del session[key_date] # xóa ngày khỏi session.

    return jsonify() # Trả về  JSON trống.


def total(): #Tính tổng
    key = app.config['CART_KEY'] # Lấy khóa cho giỏ hàng.
    cart = session.get(key) # Lấy giỏ hàng

    return jsonify(utils.cart_stats(cart)) # Trả về thống kê giỏ hàng dưới dạng phản hồi JSON.


def confirm_bill():
    key_details = app.config['DETAILS_KEY'] # Lấy khóa cho chi tiết phòng.
    key_orderer = app.config['ORDERER_KEY'] # Lấy khóa cho thông tin liên hệ.
    key_date = app.config['DATE_KEY'] # Lấy khóa cho ngày.
    key = app.config['CART_KEY'] # Lấy khóa cho giỏ hàng.

    date = session[key_date] # Lấy ngày
    cart = session[key] # Lấy giỏ hàng
    # Tính tổng hóa đơn.
    total_bill = "{:,.0f}".format(utils.get_total(session[key_details])) + " VNĐ"
    email = session[key_orderer]["email"] # Lấy email từ thông tin liên hệ.
    name = session[key_orderer]["name"] # Lấy tên từ thông tin liên hệ.
    check_in = (datetime.strptime(date["check-in"], '%Y-%m-%d')).strftime('%d-%m-%Y')
    check_out = (datetime.strptime(date["check-out"], '%Y-%m-%d')).strftime('%d-%m-%Y')
    try:
        dao.save_reservation(session[key_details], session[key_date], session[key_orderer]) # Lưu DP vào CSDL.
    except:
        return jsonify({'status': 500}) # Nếu có lỗi, trả về mã lỗi 500.

    send_mail.send(name, email, check_in, check_out, cart, total_bill) # Gửi email xác nhận đặt phòng.
    if key in session: # Nếu giỏ hàng
        del session[key] # xóa giỏ hàng
    if key_date in session: # Nếu ngày
        del session[key_date] # xóa ngày
    if key_orderer in session: # Nếu thông tin liên hệ
        del session[key_orderer] # xóa thông tin liên hệ
    if key_details in session: # Nếu chi tiết phòng
        del session[key_details] # xóa chi tiết phòng

    return jsonify({'status': 204}) # Cuối cùng, trả về mã thành công 204.


def verify_email():
    data = request.json # Lấy dữ liệu
    email = data['email'] # Lấy email

    # Gửi một yêu cầu GET đến API "isitarealemail" để kiểm tra tính hợp lệ của email.
    # Trả về email dưới dạng JSON.
    return jsonify(requests.get(
        "https://isitarealemail.com/api/email/validate",
        params={'email': email}).json()['status'])


def rent():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff: # Xác thực Staff
        return render_template('staff/rent.html') # trả về trang 'rent' dành cho Staff.
    else: # Nếu người dùng chưa xác thực hoặc không là staff,
        return redirect('/login') # chuyển đến login.


def reservations_to_rent():
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff: # Nếu người xác thực Staff
        # Lấy thông tin từ yc, nếu không có thì để trống.
        check_in = request.args.get('check-in') if request.args.get('check-in') else ""
        check_out = request.args.get('check-out') if request.args.get('check-out') else ""
        orderer_name = request.args.get('orderer-name') if request.args.get('orderer-name') else ""
        orderer_email = request.args.get('orderer-email') if request.args.get('orderer-email') else ""

        # Lấy ds DP từ CSDL.
        reservations = dao.get_reservation(check_in=check_in, check_out=check_out, orderer_name=orderer_name,
                                           orderer_email=orderer_email, did_guests_check_in=False)
        for rs in reservations: # Duyệt qua từng đặt phòng trong ds.
            t = 0
            for ds in rs.rooms: # Duyệt qua từng phòng trong DP.
                t += ds.price # Tính tổng giá của các phòng.
            rs.total = t # Lưu tổng giá vào đặt phòng.

        # Trả về trang 'reservations' dành cho nhân viên với thông tin về đặt phòng.
        return render_template('staff/reservations.html',
                               r=reservations,
                               check_in=check_in,
                               check_out=check_out,
                               orderer_name=orderer_name,
                               orderer_email=orderer_email,
                               total=total)

    else: # ko là nhân viên,
        return redirect('/login')


def change_reservation(reservation_id):
    dao.change_reservation(reservation_id) # Thay đổi đặt phòng trong CSDL dựa trên reservation_id.

    return jsonify() # Trả về JSON trống.


def paypal(): # Hàm này không nhận tham số nào.
    if current_user.is_authenticated and current_user.user_role == UserRole.Staff: # Nếu người dùng hiện tại đã được xác thực và là nhân viên,
        # Lấy thông tin từ yêu cầu, nếu không có thì để trống.
        check_in = request.args.get('check-in') if request.args.get('check-in') else ""
        check_out = request.args.get('check-out') if request.args.get('check-out') else ""
        orderer_name = request.args.get('orderer-name') if request.args.get('orderer-name') else ""
        orderer_email = request.args.get('orderer-email') if request.args.get('orderer-email') else ""

        # Lấy danh sách đặt phòng từ cơ sở dữ liệu.
        reservations = dao.get_reservation(check_in=check_in, check_out=check_out, orderer_name=orderer_name,
                                           orderer_email=orderer_email, did_guests_check_in=True, is_pay=False)
        for rs in reservations: # Duyệt qua từng đặt phòng trong danh sách.
            t = 0
            for ds in rs.rooms: # Duyệt qua từng phòng trong đặt phòng.
                t += ds.price # Tính tổng giá của các phòng.
            rs.total = t # Lưu tổng giá vào đặt phòng.

        # Trả về trang 'paypal' dành cho nhân viên với thông tin về đặt phòng.
        return render_template('staff/paypal.html', r=reservations, check_in=check_in, check_out=check_out,
                               orderer_name=orderer_name, orderer_email=orderer_email, total=total)

    else: # Nếu ko là nhân viên,
        return redirect('/login') # chuyển đến trang login


def pay_reservation(reservation_id):
    dao.paypal_reservation(reservation_id) # Thanh toán DP thông qua PayPal dựa trên reservation_id.

    return jsonify()


def hash_pass():
    import hashlib # Nhập module hashlib để sử dụng thuật toán băm.
    data = request.json # Lấy dl từ JSON.
    password = data['password'] # Lấy mật khẩu từ dữ liệu.

    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return jsonify(password)


def input_info():
    data = request.json # Lấy dữ liệu từ yêu cầu JSON.

    key_i = app.config['S_INFO_KEY'] # Lấy khóa cho thông tin.
    session[key_i] = data['data'] # Lưu dữ liệu vào session dựa trên khóa.

    return jsonify()


def info_rooms():
    key_i = app.config['S_INFO_KEY']
    if key_i not in session: # Nếu khóa không tồn tại
        return redirect("/staff/booking") # chuyển trang 'staff/booking'.
    else: # Nếu khóa tồn tại
        info = session[key_i] # lấy thông tin
        amount = int(info['amount_rooms']) # Lấy số lượng phòng
        key_d = app.config['S_DETAILS_KEY'] # Lấy khóa
        if key_d not in session: # Nếu khóa cho chi tiết không tồn tại
            session[key_d] = {} # tạo một từ điển mới

        d = session[key_d] # Lấy chi tiết
        for i in range(amount): # Duyệt qua từng phòng.
            if str(i + 1) not in session[key_d]: # Nếu phòng chưa tồn tại
                d[str(i + 1)] = {} # thêm phòng
        session[key_d] = d # Cập nhật chi tiết

        # Trả về trang 'staff/booking_rooms.html' với số lượng phòng.
        return render_template("staff/booking_rooms.html", amount=amount)


def add_room():
    key_i = app.config['S_INFO_KEY']
    if key_i not in session: # Nếu khóa không tồn tại
        return jsonify()

    temp = session[key_i] # Lấy thông tin
    a = int(temp['amount_rooms']) + 1 # Tăng số lượng phòng lên 1.
    temp['amount_rooms'] = a # Cập nhật sl phòng
    session[key_i] = temp # Cập nhật thông tin

    key_d = app.config['S_DETAILS_KEY'] # Lấy khóa
    temp2 = session[key_d] # Lấy chi tiết
    temp2[str(a)] = {} # Thêm một phòng mới
    session[key_d] = temp2 # Cập nhật chi tiết
    print(session[key_d]) # In chi tiết ra console.

    return jsonify(a) # Trả về sl phòng mới dưới dạng  JSON.


