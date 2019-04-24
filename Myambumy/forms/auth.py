from flask_wtf import FlaskForm
from wtforms import StringField,BooleanField,PasswordField,SubmitField,HiddenField
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
    email =StringField('Email',validators=[DataRequired(),Length(1,254),Email()])
    username = StringField('Username',validators=[DataRequired(),Length(1,30), Regexp('^[a-zA-Z0-9]*$',
                                                          message='The username should contain only a-z, A-Z and 0-9.')])
    password = PasswordField('Password',validators=[DataRequired(),Length(8,128),EqualTo('password2')])
    password2 = PasswordField('Confirmed password',validators=[DataRequired()])

    submit = SubmitField()

    def vaildate_email(self,field):
        if User.query.filter_by(email=field.date).first():
            raise ValidationError('The email is already in use.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already in use.')
#忘记密码的表单
class ResetPassword(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email(),Length(1,128)])
    password = PasswordField('Password',validators=[DataRequired(),Length(8,128),EqualTo('password2')])
    password2 = PasswordField('Password2',validators=[DataRequired(),Length(8,128)])
    submit = SubmitField()
#更改密码的表单
class ChangePassword(ResetPassword):
    email = HiddenField()

class ForgetPassword(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()

class ChangeEmail(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()
