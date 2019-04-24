try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import  current_app,request,redirect,url_for
from itsdangerous import  BadSignature,SignatureExpired
from Myambumy.settings import Operations
from Myambumy.extensions import db

def generate_token(user, operation, expire_in=None, **kwargs):
    s = Serializer(current_app.config['SECRET_KEY'], expire_in)
    data = {'id': user.id, 'operation': operation}
    data.update(**kwargs)
    return s.dumps(data)


def vaildate_token(user,token,operation,new_password=None):
    s = Serializer(current_app.config['SECRET_KEY'])
    token = token[2:-1]   #不然会添加多余的引号，导致无法解析
    try:
        data = s.loads(token)
        print('bbbbbbbbbbbbbbbbbbbbb  ',operation)
    except (BadSignature,SignatureExpired):   #签名错误和超时
        print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        return False

    if operation != data.get('operation') or user.id != data.get('id'):
        print('aaaaaaaaaaaaaaaaaaaaaaaaaa')
        return False

    if operation == Operations.CONFIRM:
        print('confirm ppppppppppppppppppppp')
        user.confirmed = True

    elif operation == Operations.RESET_PASSWORD:  #重设密码
        user.set_password(new_password)

    elif operation ==Operations.CHANGE_EMAIL: #重设邮箱
        user.email = data.get('new_email')

    elif operation == Operations.CHANGE_PASSWORD:
        print("hashhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        user.password_hash = data.get('password_hash')
    else:
        print('ffffffffffffffffffffffffff')
        return False

    db.session.commit()
    return True

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def redirect_back(default='main.index', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))