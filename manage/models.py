from datetime import datetime
from manage import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), unique=True, nullable = False,default='')
    email = db.Column(db.String(120), unique=True, nullable = False)
    company = db.Column(db.String(120), unique=False, nullable = False,default='')
    tel = db.Column(db.String(120), unique=False, nullable = False,default='')
    address1 = db.Column(db.String(255), unique=False, nullable = True,default='')
    address2 = db.Column(db.String(255), unique=False, nullable = True,default='')
    city = db.Column(db.String(50), unique=False, nullable = True,default='')
    state = db.Column(db.String(50), unique=False, nullable = True,default='')
    zip = db.Column(db.String(50), unique=False, nullable = True,default='')
    country = db.Column(db.String(50), unique=False, nullable = True,default='')
    password = db.Column(db.String(60), nullable=False)
    verified = db.Column(db.Boolean,default=False,nullable=True)
    role=db.Column(db.Integer,nullable=False,default=0)     # 0: client, 1: admin
    date_registered = db.Column(db.DateTime, nullable=False, default = datetime.utcnow)
    user_services =db.relationship('UserService', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.email}')"

################################################################### prototype ###################################

class Service(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), unique=True, nullable = False,default='')
    description = db.Column(db.String(255), nullable = True,default='')
    admin_items = db.relationship('AdminItem',backref='service', lazy=True)
    client_items = db.relationship('ClientItem',backref='service', lazy=True)
    user_services = db.relationship("UserService", backref='service', lazy=True)

'''
Upload | Download 	0
Simple Date Picker | Display Date Picked | Accept Date: Confirm or Select Date	1
Check Box Only	2
'''
    
class AdminItem(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False,default='')
    item_type = db.Column(db.Boolean,default=False,nullable=True)   # If True ,pre assessment.  If False, post assessment
    matched_item = db.Column(db.Integer, nullable=False, default=0)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    function = db.Column(db.Integer, nullable = False, default=0)

class ClientItem(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False,default='')
    item_type = db.Column(db.Boolean,default=False,nullable=True)   # If True ,pre assessment.  If False, post assessment
    matched_item = db.Column(db.Integer, nullable=False, default=0)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    function = db.Column(db.Integer, nullable = False, default=0)

###############################################################################################################################

class UserService(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    name = db.Column(db.String(100), nullable = False, default='')
    project_name = db.Column(db.String(100), nullable = False, default='')
    a_items = db.relationship('AItem',backref='user_service', lazy=True)
    c_items = db.relationship('CItem',backref='user_service', lazy=True)


class AItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='')
    item_type = db.Column(db.Boolean, default=False,
                          nullable=True)  # If True ,pre assessment.  If False, post assessment
    form_text = db.Column(db.String(255), nullable=True)
    user_service_id = db.Column(db.Integer, db.ForeignKey('user_service.id'), nullable=False)

    function = db.Column(db.Integer, nullable=False, default=0)
    filename = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=True)
    checked = db.Column(db.Boolean, default=False, nullable=True)
    updated = db.Column(db.DateTime, nullable=True)
    finished = db.Column(db.Boolean, default=False, nullable=True)
    finished_time = db.Column(db.DateTime, nullable=True)


class CItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='')
    item_type = db.Column(db.Boolean, default=False,
                          nullable=True)  # If True ,pre assessment.  If False, post assessment
    form_text = db.Column(db.String(255), nullable=True)
    user_service_id = db.Column(db.Integer, db.ForeignKey('user_service.id'), nullable=False)

    function = db.Column(db.Integer, nullable=False, default=0)
    filename = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=True)
    checked = db.Column(db.Boolean, default=False, nullable=True)
    updated = db.Column(db.DateTime, nullable=True)
    finished = db.Column(db.Boolean, default=False, nullable=True)
    finished_time = db.Column(db.DateTime, nullable=True)

class Country(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, default='')
