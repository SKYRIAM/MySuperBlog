from flask_sqlalchemy import SQLAlchemy
from flask_mail import  Mail
from flask_moment import  Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager


db = SQLAlchemy()
mail = Mail()
moment = Moment()
bootstrap = Bootstrap()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from Myambumy.models import User
    user = User.query.get(int(user_id))
    print('opopop'+user_id)
    return user

login_manager.login_view = 'auth.login'
# login_manager.login_message = 'Your custom message'
login_manager.login_message_category = 'warning'

