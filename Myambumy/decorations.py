from flask import Markup,url_for,flash,redirect,render_template,abort
from functools import wraps
from flask_login import  current_user

#保证用户经过邮箱认证的装饰器
def confirm_required(func):
    @wraps(func) #避免修改函数名和特殊属性
    def decoration_function(*args,**kwargs):
        if  not current_user.confirmed:
            #避免JINJIA的转义，防止其他人纂改保证安全
            message = Markup(
                'Please confirm your account first.'
                'Not receive the email?'
                '<a class="alert-link" href="%s">Resend Confirm Email</a>' %
                url_for('auth.resend_confirm_email'))
            flash(message,'warning')
            return redirect(url_for('main.index'))
        return func(*args,**kwargs)
    return decoration_function


#保证用户有某权限的装饰器
def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator

#验证是否有管理员权限
def admin_required(func):
    return permission_required('ADMINISTER')(func)


