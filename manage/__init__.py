from os.path import join, dirname, realpath

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from O365 import Account


app = Flask(__name__)

''' DB connection and configuration'''
app.config['SECRET_KEY'] = '49397af3a1821e12d96707d5dc322c8a'
#app.config['SQLALCHEMY_DATABASE_URI'] ='mysql://root:''@localhost:3306/management'         #mysql config
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///site.db'              #sqlite config
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

''' end DB '''

credentials = ('9fc03a66-fa26-472f-81ec-acdbef0ff289','Rw5D9U=3IovPWriMl0u[bWwgTOlznT?[')
account = Account(credentials)

bcrypt = Bcrypt(app)
TOKEN_EXPIRED = 36000       #verify link expired time
PASSWORD_TOKEN_EXPIRED = 60       #password reset expired time
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
UPLOADS_PATH = join(dirname(realpath(__file__)), 'static\\uploads\\')

app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['UPLOADS_PATH'] = UPLOADS_PATH


''' Login Manager '''
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

'''--------------'''

from manage import routes
from manage.models import User, Country
db.create_all()
user = User.query.filter_by(email="admin@admin.com").first()
if user == None:
    hashed = bcrypt.generate_password_hash("admin").decode('utf-8')
    new_user = User(email="admin@admin.com",name="admin",password=hashed,verified=True,role=1)
    db.session.add(new_user)
    db.session.commit()
    print("admin user created !!!")
