from flask import Blueprint,flash,redirect,render_template,url_for
from Myambumy.extensions import db
from Myambumy.models import User
from Myambumy.forms.auth import RegisterForm
from flask_login import current_user,login_required,login_user,logout_user

auth_bp  = Blueprint('auth',__name__)

@auth_bp.route('/register',methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        username = form.username.data
        user = User(name=name,email=email,username=username)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('craete user','success')
        return redirect(url_for('main.index'))
    return  render_template('auth/register.html',form=form)


@auth_bp.route('/login',methods=['GET','POST'])
def login():
    return render_template('/main/index.html')

@auth_bp.route('/logout',methods=['GET','POST'])
def logout():
    return render_template('/main/index.html')


