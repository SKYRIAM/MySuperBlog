from flask_wtf import FlaskForm
from wtforms import StringField,BooleanField,PasswordField,SubmitField
from wtforms import  ValidationError
from wtforms.validators import DataRequired,Length,Email,EqualTo,Regexp

from Myambumy.models import User

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Length(1,254),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    remember_me = BooleanField('Remeber me')
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired(),Length(1,30)])
    email =StringField('Email',validators=[DataRequired,Length(1,254),Email()])
    username = StringField('Username',validators=[DataRequired,Length(1,30), Regexp('^[a-zA-Z0-9]*$',
                                                          message='The username should contain only a-z, A-Z and 0-9.')])
    password = StringField('Password',validators=[DataRequired(),Length(8,128),EqualTo('password2')])
    password2 = StringField('Confirmed password',validators=[DataRequired()])

    submit = SubmitField()

    def vaildate_email(self,field):
        if User.query.filter_by(email=field.date).first():
            raise ValidationError('The email is already in use.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already in use.')