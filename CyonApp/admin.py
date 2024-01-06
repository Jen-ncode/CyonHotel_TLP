from flask import redirect
from flask_login import logout_user

from CyonApp import app, db, dao
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from CyonApp.models import User, UserRole, RoomType, Room
from flask_login import current_user
from flask import request


class AdminModelView(ModelView): # Xác thực Admin

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.Admin


class StaffView(AdminModelView):  # Xem nhân viên
    column_exclude_list = ['password', 'avatar', 'reservations']   #Danh sách các cột sẽ không được hiển thị
    form_edit_rules = ('name', 'username', 'password', 'email', 'avatar', 'joined_date', 'user_role')
    form_create_rules = ('name', 'username', 'password', 'email', 'avatar', 'joined_date', 'user_role')    #Các quy tắc cho việc chỉnh sửa và tạo mới
    can_create = True

    def get_query(self):
        return self.session.query(self.model).filter(self.model.user_role == UserRole.Staff)


class RuleView(BaseView):  # Xem quy định
    @expose('/')
    def index(self):
        policy = dao.load_policy()
        room_type = dao.load_room_types()

        return self.render('admin/rule.html', surcharge=policy['surcharge'], factor=policy['foreigner_factor'],
                           room_type=room_type)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.Admin


class LogOutView(BaseView):  #Xem đăng xuất
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        from datetime import datetime
        month = request.args.get("month")
        if not month:
            month = datetime.now().month
        stats = dao.revenue_stats_by_month(month)
        total = dao.total_by_month(month)[0]

        fre = dao.frequency_room_type(month)
        total_fre = dao.total_reservation_details(month)
        if not total:
            total = 0
        return self.render('admin/index.html', month=int(month), stats=stats, total=total, fre=fre, total_fre=total_fre)


class RoomTypeView(AdminModelView):
    column_list = ['id', 'name', 'price', 'max_people', 'rooms']
    form_edit_rules = ('name', 'price', 'max_people', 'image', 'description')
    can_create = True
    can_edit = True
    can_export = True
    column_searchable_list = ['name']
    column_filters = ['name', 'price', 'max_people']


class RoomView(AdminModelView):
    can_create = True
    can_edit = True
    can_export = True
    column_list = ['room_number', 'floor', 'available', 'room_type_id']
    form_edit_rules = ('room_number', 'floor', 'room_type', 'available')
    form_create_rules = ('room_number', 'floor', 'room_type', 'available')

    column_searchable_list = ['room_number']
    column_filters = ['room_number', 'floor', 'available', 'room_type_id']


admin = Admin(app=app, name="Cyon Hotel Administration", template_mode="bootstrap4", index_view=MyAdminIndex())

admin.add_view(RuleView(name='Quy định'))
admin.add_view(RoomTypeView(RoomType, db.session, name='Loại phòng'))
admin.add_view(RoomView(Room, db.session, name='Phòng'))
admin.add_view(StaffView(User, db.session, name='Nhân viên'))
admin.add_view(LogOutView(name='Đăng xuất'))