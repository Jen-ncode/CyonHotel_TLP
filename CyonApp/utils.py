import hashlib
from datetime import datetime
from CyonApp import db
from CyonApp.models import User, UserRole

#tính toán thống kê về giỏ hàng và trả về một ds chứa tổng số lượng và tổng giá trị của các mục trong giỏ hàng
def cart_stats(cart):
    total_amount, total_quantity = 0, 0
    if cart:
        for c in cart.values():
            total_quantity += c['quantity'] #cộng dồn số lượng
            total_amount += c['quantity'] * c['price'] #cộng dồn giá mỗi mục

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }

#Hàm trả về số ngày dựa vào ngày checkin - checkout truyền vào
def get_num_of_days(date):
    num_of_days = 0
    if date:
        start = datetime.strptime(date["check-in"], '%Y-%m-%d')
        end = datetime.strptime(date["check-out"], '%Y-%m-%d')
        num_of_days = (end - start).days

    return num_of_days

#tính tổng giá tiền đơn đặt phòng
def get_total(details):
    total = 0
    if details:
        for r in details.values():
            total += r['total']

    return total


def add_user(name, username, password, **kwargs):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name.strip(),
                username=username.strip(),
                password=password,
                email=kwargs.get('email'),
                avatar=kwargs.get('avatar'))
    db.session.add(user)
    db.session.commit()

#xác thực, kiểm tra người dùng
def check_login(username, password, role=UserRole):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        return User.query.filter(User.username.__eq__(username.strip()), User.password.__eq__(password),
                                 User.user_role.__eq__(role)).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)



if __name__ == '__main__':
    from CyonApp import app
    with app.app_context():
        pass