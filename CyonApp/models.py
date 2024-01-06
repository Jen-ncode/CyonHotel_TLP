from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from enum import Enum as MyEnum
from CyonApp import db, app
from datetime import datetime
from flask_login import UserMixin


class GuestType(MyEnum):
    domestic = 1
    foreign = 2


class Gender(MyEnum):
    male = 1
    female = 2


class UserRole(MyEnum):
    Admin = 1
    Staff = 2


class Status(MyEnum):
    not_checked_in_yet = 1
    checked_in = 2


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)


class RoomType(BaseModel):
    name = Column(String(50), nullable=False, unique=True)
    image = Column(String(100))
    price = Column(Float, default=0)
    max_people = Column(Integer, nullable=False)
    description = Column(Text)
    rooms = relationship('Room', backref='room_type', lazy=True)

    def __str__(self):
        return self.name


class Room(BaseModel):
    room_number = Column(String(4), nullable=False, unique=True)
    floor = Column(Integer, nullable=False)
    available = Column(Boolean, nullable=False, default=True)
    room_type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    reservations = relationship('ReservationDetails', backref='room', lazy=True)

    def __str__(self):
        return self.room_number


class Guest(BaseModel):
    name = Column(String(50), nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    identity_number = Column(String(50), nullable=False)
    address = Column(String(100))
    guest_type = Column(Enum(GuestType), nullable=False)
    reservations = relationship('ReservationDetailsGuest', backref='guest', lazy=True)


class User(BaseModel, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50))
    avatar = Column(String(100))
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.now)
    user_role = Column(Enum(UserRole), default=UserRole.Staff)
    reservations = relationship('Reservation', backref='user', lazy=True)

    def __str__(self):
        return self.username


class Reservation(BaseModel):
    created_date = Column(DateTime, default=datetime.now())
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    orderer_name = Column(String(50), nullable=False)
    orderer_email = Column(String(100), nullable=False)
    did_guests_check_in = Column(Boolean, nullable=False, default=False)
    is_pay = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=True)
    rooms = relationship('ReservationDetails', backref='reservation', lazy=True)


class ReservationDetails(BaseModel):
    reservation_id = Column(Integer, ForeignKey(Reservation.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    price = Column(Float, nullable=False)
    guests = relationship('ReservationDetailsGuest', backref='reservation_details', lazy=True)


class ReservationDetailsGuest(BaseModel):
    reservation_details_id = Column(Integer, ForeignKey(ReservationDetails.id), nullable=False)
    guest_id = Column(Integer, ForeignKey(Guest.id), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        pass
        db.drop_all()
        db.create_all()
        import hashlib
        password = "cyon"
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        u = User(name="Cyon1", username="staff", password=password)
        db.session.add(u)
        db.session.commit()
        password = "cyon"
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        u2 = User(name="Cyon2", username="admin", password=password, user_role=UserRole.Admin)
        db.session.add(u2)
        db.session.commit()
        t1 = RoomType(name="SUPERIOR DOUBLE BED",
                      image="https://iconsaigonhotel.com/wp-content/uploads/2017/06/ICON-DELUXE.jpg",
                      price=750000, max_people=2)
        t2 = RoomType(name="SUPERIOR TWIN BED",
                      image="https://iconsaigonhotel.com/wp-content/uploads/2019/11/sen4.jpg",
                      price=960000, max_people=2)
        t3 = RoomType(name="DELUXE DOUBLE",
                      image="https://iconsaigonhotel.com/wp-content/uploads/2017/06/iCON-SENIOR-DELUXE.jpg",
                      price=1280000, max_people=3)
        t4 = RoomType(name="PREMIUM DOUBLE",
                      image="https://iconsaigonhotel.com/wp-content/uploads/2017/06/ICON-PREMIUM.jpg",
                      price=1950000, max_people=3)
        db.session.add_all([t1, t2, t3, t4])
        db.session.commit()

        for i in range(0, 10):
            r1 = Room(room_number=str(100 + i), floor=1, room_type_id=1)
            db.session.add(r1)
            db.session.commit()

        for i in range(0, 10):
            r2 = Room(room_number=str(200 + i), floor=2, room_type_id=2)
            db.session.add(r2)
            db.session.commit()

        for i in range(0, 10):
            r3 = Room(room_number=str(300 + i), floor=3, room_type_id=3)
            db.session.add(r3)
            db.session.commit()

        for i in range(0, 10):
            r4 = Room(room_number=str(400 + i), floor=4, room_type_id=4)
            db.session.add(r4)
            db.session.commit()