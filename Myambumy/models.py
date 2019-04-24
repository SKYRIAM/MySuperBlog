from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from Myambumy.extensions import db
from datetime import datetime

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),unique=True,index=True) #index设为True建立索引
    email = db.Column(db.String(254),index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(30))
    website = db.Column(db.String(50))
    location = db.Column(db.String(50))
    member_since = db.Column(db.DateTime,default=datetime.utcnow)

    confirmed = db.Column(db.Boolean,default=False)

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def vaildate_password(self,password):
        return check_password_hash(self.password_hash,password)