import os

from flask_login import current_user

from CyonApp import app, db
from CyonApp.models import RoomType, Room, Reservation, ReservationDetails, ReservationDetailsGuest, Guest
from sqlalchemy import or_, and_, not_, func, extract
import json


def load_policy():      # Đọc tập JSON
    my_directory = os.getcwd()      # Lấy thư mục hiên tại gán cho my_directory
    json_file_path = os.path.join(my_directory, 'static/json/policy.json')      # Đường dẫn đến tập JSON
    with open(json_file_path, encoding='utf-8') as f:       # Mở tập JSON đọc và mã hóa UTF-8
        return json.load(f)     #Trả về đt PY


def save_policy(data):      # Lưu tập JSON
    my_directory = os.getcwd()
    json_file_path = os.path.join(my_directory, 'static/json/policy.json')
    with open(json_file_path, mode='w', encoding='utf-8') as f:  # Mở tập JSON ghi và mã hóa UTF-8
        return json.dump(data, f, ensure_ascii=False, indent=4)


def load_room_types(kw=None, min_price=None, max_price=None, num_of_guests=None, id=None):
    room_types = RoomType.query     # Lấy phòng từ CSDL
    if kw:
        room_types = room_types.filter(RoomType.name.contains(kw))      # Lọc các loại phòng có tên kw
    if min_price:
        room_types = room_types.filter(RoomType.price >= float(min_price))      # Lọc các loại phòng >= min_price
    if max_price:
        room_types = room_types.filter(RoomType.price <= float(max_price))      # Lọc các loại phòng =< max_price
    if num_of_guests:
        room_types = room_types.filter(RoomType.max_people >= float(num_of_guests))#Lọc LP có sl ng tối đa >= num_of_guest
    if id:
        room_types = room_types.filter(RoomType.id.__eq__(id))  # Lọc các loại phòng có cùng id

    return room_types.all()


def get_roomtype_by_id(roomtype_id):        # Lấy danh sách các loại phòng từ CSDL dựa vào id
    return RoomType.query.filter_by(id=roomtype_id).all()


# Kiểm tra xem thông tin chi tiết đặt phòng, ngày đặt và thông tin người đặt có tồn tại hay không
def save_reservation(details, date, orderer, rent=None):
    if details and date and orderer:
        if rent:
            r = Reservation(check_in=date["check-in"], check_out=date["check-out"],
                            orderer_name=orderer["name"], orderer_email=orderer["email"], did_guests_check_in=True)
        else:
            r = Reservation(check_in=date["check-in"], check_out=date["check-out"],
                            orderer_name=orderer["name"], orderer_email=orderer["email"], did_guests_check_in=False)
        db.session.add(r)
        for d in details.values():
            room = get_available_room(date["check-in"], date["check-out"], d['room_type_id']).first()
            rd = ReservationDetails(reservation=r, room_id=room.id, price=d['total'])
            db.session.add(rd)
            for g in d['guests'].values():
                gst = get_guest(g["name"], g["identity_number"], int(g["type"]))
                if gst:
                    rdg = ReservationDetailsGuest(reservation_details=rd, guest_id=gst.id)
                else:
                    gst = Guest(name=g["name"], gender=g["gender"], identity_number=g["identity_number"],
                                address=g["address"], guest_type=g["type"])
                    db.session.add(gst)
                    rdg = ReservationDetailsGuest(reservation_details=rd, guest=gst)
                db.session.add(rdg)
        db.session.commit()


def get_available_room(start, end, room_type_id): # Lọc phòng chưa được đặt (phòng trống) trog time check_in - check_out
    subquery = db.session.query(ReservationDetails.room_id) \
        .join(Reservation, Reservation.id.__eq__(ReservationDetails.reservation_id)) \
        .filter(or_(and_(Reservation.check_in >= start, Reservation.check_in <= end),
                    and_(Reservation.check_out >= start, Reservation.check_out <= end),
                    and_(Reservation.check_in <= start, Reservation.check_out >= end)))
    query = db.session.query(Room.id) \
        .filter(Room.room_type_id.__eq__(room_type_id)) \
        .filter(Room.id.notin_(subquery))
    return query


def get_unavailable_room(start, end, room_type_id):# Lọc phòng đã đc đặt (phòng đặt) có trog time check_in - check_out
    subquery = db.session.query(ReservationDetails.room_id) \
        .join(Reservation, Reservation.id.__eq__(ReservationDetails.reservation_id)) \
        .filter(or_(and_(Reservation.check_in >= start, Reservation.check_in <= end),
                    and_(Reservation.check_out >= start, Reservation.check_out <= end),
                    and_(Reservation.check_in <= start, Reservation.check_out >= end)))
    query = db.session.query(Room.id) \
        .filter(Room.room_type_id.__eq__(room_type_id)) \
        .filter(Room.id.in_(subquery))
    return query


def get_guest(name=None, identity_number=None, guest_type=None, id=None):   # Lọc thông tin khách hàng
    guest = Guest.query
    if name:
        guest = guest.filter(Guest.name.__eq__(name))
    if identity_number:
        guest = guest.filter(Guest.identity_number.__eq__(identity_number))
    if guest_type:
        guest = guest.filter(Guest.guest_type.__eq__(guest_type))
    if id:
        guest = guest.filter(Guest.id.__eq__(id))
    if guest.first():
        return guest.first()
    else:
        return None


def revenue_stats_by_month(month):   # Thống kê doanh thu theo từng loại phòng trong một tháng cụ thể
    query = db.session.query(RoomType.id, RoomType.name, func.sum(ReservationDetails.price)) \
        .join(Reservation, Reservation.id.__eq__(ReservationDetails.reservation_id)) \
        .join(Room, Room.id.__eq__(ReservationDetails.room_id)) \
        .join(RoomType, RoomType.id.__eq__(Room.room_type_id)) \
        .filter(Reservation.is_pay.__eq__(True)) \
        .filter(extract('month', Reservation.created_date) == month) \
        .group_by(RoomType.id, RoomType.name)

    return query.all()


def total_by_month(month): # Lấy tổng doanh thu các phòng đã đặt trong một tháng
    query = db.session.query(func.sum(ReservationDetails.price)) \
        .join(Reservation, Reservation.id.__eq__(ReservationDetails.reservation_id)) \
        .filter(Reservation.is_pay.__eq__(True)) \
        .filter(extract('month', Reservation.created_date) == month)

    return query.first()


def frequency_room_type(month):
    subquery = db.session.query(func.count(Room.room_type_id)). \
        join(ReservationDetails, ReservationDetails.room_id.__eq__(Room.id)). \
        join(Reservation, Reservation.id.__eq__(ReservationDetails.reservation_id)). \
        filter(Room.room_type_id.__eq__(RoomType.id)). \
        filter(Reservation.did_guests_check_in.__eq__(True)). \
        filter(extract('month', Reservation.created_date) == month).label('số lần xuất hiện')

    query = db.session.query(RoomType.id, RoomType.name, subquery)

    return query.all()


def total_reservation_details(month): # Tần suất sử dụng phòng trong các phòng đã đặt phòng đã nận phòng trong 1 tháng
    query = db.session.query(ReservationDetails.id). \
        join(Reservation, Reservation.id.__eq__(ReservationDetails.reservation_id)). \
        filter(Reservation.did_guests_check_in.__eq__(True)). \
        filter(extract('month', Reservation.created_date) == month)

    return query.count()


# Tìm kiếm thông tin các phòng đã đặt từ CSDL dựa trên các tiêu chí tìm kiếm
def get_reservation(check_in=None, check_out=None, orderer_name=None, orderer_email=None, is_pay=None,
                    did_guests_check_in=None, id=None):
    query = Reservation.query
    if check_in:
        query = query.filter(Reservation.check_in.__eq__(check_in))
    if check_out:
        query = query.filter(Reservation.check_out.__eq__(check_out))
    if orderer_name:
        query = query.filter(Reservation.orderer_name.contains(orderer_name))
    if orderer_email:
        query = query.filter(Reservation.orderer_email.contains(orderer_email))
    if is_pay is not None and is_pay == False:
        query = query.filter(Reservation.is_pay.__eq__(False))
    if is_pay is not None and is_pay == True:
        query = query.filter(Reservation.is_pay.__eq__(True))
    if did_guests_check_in is not None and did_guests_check_in == False:
        query = query.filter(Reservation.did_guests_check_in.__eq__(False))
    if did_guests_check_in is not None and did_guests_check_in == True:
        query = query.filter(Reservation.did_guests_check_in.__eq__(True))
    if id:
        query = query.filter(Reservation.id.__eq__(id))

    return query.all()


def get_reservation_details(reservation_id=None):  # Lấy thông tin chi tiết của các phòng đã đặt từ CSDL
    query = db.session.query(ReservationDetails, Room.id, RoomType.name).join(Room, Room.id.__eq__(
        ReservationDetails.room_id)). \
        join(RoomType, RoomType.id.__eq__(Room.room_type_id))

    if reservation_id:
        query = query.filter(ReservationDetails.reservation_id.__eq__(reservation_id))

    return query.all()


# Lấy thông tin chi tiết về KH của các phòng đã đặt phòng từ CSDL
def get_reservation_details_guests(reservation_details_id=None):
    query = ReservationDetailsGuest.query

    if reservation_details_id:
        query = query.filter(ReservationDetailsGuest.reservation_details_id.__eq__(reservation_details_id))

    return query.all()


def change_reservation(reservation_id): # Cập nhật trạng thái của 1 phòng đã đặt cụ thể
    r = Reservation.query.filter(Reservation.id.__eq__(reservation_id)).first()
    r.did_guests_check_in = True
    db.session.commit()


def paypal_reservation(reservation_id): # Cập nhật trạng thái thanh toán các phòng đã đặt
    r = Reservation.query.filter(Reservation.id.__eq__(reservation_id)).first()
    r.is_pay = True
    r.user = current_user
    db.session.commit()