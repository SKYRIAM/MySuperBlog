from flask import Blueprint,flash,redirect,render_template,url_for
from Myambumy.extensions import db
from Myambumy.models import User
from Myambumy.forms.auth import RegisterForm,LoginForm,ForgetPassword,ResetPassword,ChangeEmail,ChangePassword
from flask_login import current_user,login_required,login_user,logout_user
from Myambumy.emails import send_confirm_email,send_reset_password_email,send_change_email_email,send_change_password
from Myambumy.utils import generate_token,vaildate_token,redirect_back
from Myambumy.settings import Operations
from Myambumy.decorations import confirm_required

auth_bp  = Blueprint('auth',__name__)

#注册并发送确认邮件
@auth_bp.route('/register',methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower() #规定在数据库中存储小写邮箱
        name = form.name.data
        username = form.username.data
        user = User(name=name,email=email,username=username)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user=user,operation=Operations.CONFIRM)
        print('token ',token)
        send_confirm_email(user=user,token=token) #发送验证邮件
        flash('Confirm email sent,check your inbox ','info')
        return redirect(url_for('.login'))
    return  render_template('auth/register.html',form=form)

#验证邮箱
@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if vaildate_token(user=current_user, token=token, operation=Operations.CONFIRM):
        flash('Account confirmed.', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('main.index'))#修改redirect(url_for('.resend_confirm_email'))


#重新发送邮件
@auth_bp.route('/resend_confirm_email')
def resend_confirm_email():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    token = generate_token(current_user,operation=Operations.CONFIRM)
    send_confirm_email(current_user,token)
    flash('New email sent, check your inbox.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.vaildate_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('Login success.', 'info')
            return redirect_back()
        flash('Invalid email or password.', 'warning')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout',methods=['GET','POST'])
def logout():
    logout_user()
    flash('Logout success','info')
    return redirect(url_for('main.index'))

#忘记密码
@auth_bp.route('/forget_password',methods=['GET','POST'])
def forget_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ForgetPassword()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data.lower()).first()
        if user:
            token = generate_token(user=user,operation=Operations.RESET_PASSWORD)
            send_reset_password_email(token=token,user=user) #发送重设密码文件
            flash('Password reset email sent,check your inbox','info')
            return redirect(url_for('.login'))
        flash('aaainvaild email','warning')
        return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)

#验证忘记密码的token
@auth_bp.route('/reset-password/<token>',methods=['GET','POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPassword()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data.lower()).first()
        if user is None:
            flash('invailed email')
            return redirect(url_for('main.index'))
        if vaildate_token(token=token,user=user,operation=Operations.RESET_PASSWORD,new_password=form.password.data):
            flash('Password updated.', 'success')
            return redirect(url_for('.login'))
        else:
            flash('Invalid or expired link.', 'danger')
            return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)

#修改邮箱
@auth_bp.route('/change_email',methods=['GET','POST'])
@login_required
@confirm_required
def change_email():
    form = ChangeEmail()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('email had been register ', 'warning')
            return redirect(url_for('.login'))
        email = form.email.data
        user = current_user
        token = generate_token(user=user,operation=Operations.CHANGE_EMAIL,new_email=email) #向新邮箱发送邮件
        send_change_email_email(user=user,token=token,to=email)
        flash('change email email send to your inbox','info')
        return redirect(url_for('main.index'))
    return render_template('auth/change_email.html',form=form)

#验证修改的邮箱
@login_required
@confirm_required
@auth_bp.route('/change_email_confirm/<token>',methods=['GET','POST'])
def change_email_confirm(token):
    if vaildate_token(token=token,user=current_user,operation=Operations.CHANGE_EMAIL):
        flash('email change ','success')
        logout_user() #用户重新登录
        return  redirect(url_for('.login'))

    return redirect(url_for('main.index'))

#修改密码 发送邮件
@login_required
@confirm_required
@auth_bp.route('/change_password',methods=['GET','POST'])
def change_password():
    form = ChangePassword()

    if form.validate_on_submit():
        password = form.password.data
        print("ppppppppppppassword ",password)
        print("currenttttttttttt ",current_user.id)
        current_user.set_password(password)  #只是赋值，并没有返回值
        password_hash = current_user.password_hash
        print("ppppppppppppppppppppp ",password_hash)
        token = generate_token(user=current_user,operation=Operations.CHANGE_PASSWORD,password_hash=password_hash)
        send_change_password(user=current_user,token=token)
        flash('change password email send to your inbox','info')
        return redirect(url_for('main.index'))
    return  render_template('auth/change_password.html',form=form)

@login_required
@confirm_required
@auth_bp.route('/change_password_confirm/<token>')
def change_password_confirm(token):
    print("changeeeeeeeeeeeeeeeeeeee",current_user.id)
    if vaildate_token(token=token,user=current_user,operation=Operations.CHANGE_PASSWORD):
        flash('change password,please login ','success')
        logout_user()
        redirect(url_for('.login'))
    return redirect(url_for('main.index'))




@auth_bp.route('/test')
@confirm_required
def test():
    return render_template('auth/text.html')

