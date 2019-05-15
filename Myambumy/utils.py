try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin
import  os
import  uuid
import PIL
from PIL import Image
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import  current_app,request,redirect,url_for
from itsdangerous import  BadSignature,SignatureExpired
from Myambumy.settings import Operations
from Myambumy.extensions import db
from flask import flash
from Myambumy.models import User

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

#生成随机文件名
def rename_image(old_filename):
    ext = os.path.splitext(old_filename)[1]
    new_filename = uuid.uuid4().hex + ext
    return new_filename

#生成缩放图
def resize_image(image,filename,base_width):
    #用于返回文件名和扩展名元组 os.path.splitext('d:\\library\\book.txt')('d:\\library\\book', '.txt')
    filename,ext = os.path.splitext(filename)
    img = Image.open(image)
    if img.size[0] <= base_width:
        return filename+ext
    w_percent = (base_width / float(img.size[0]))
    h_size = int((float(img.size[1])*float(w_percent)))
    img = img.resize((base_width, h_size), PIL.Image.ANTIALIAS)

    filename += current_app.config['ALBUMY_PHOTO_SUFFIX'][base_width] + ext
    img.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename), optimize=True, quality=85)
    return filename

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))

def validate_token(user, token, operation, new_password=None):
    s = Serializer(current_app.config['SECRET_KEY'])

    try:
        data = s.loads(token)
    except (SignatureExpired, BadSignature):
        return False

    if operation != data.get('operation') or user.id != data.get('id'):
        return False

    if operation == Operations.CONFIRM:
        user.confirmed = True
    elif operation == Operations.RESET_PASSWORD:
        user.set_password(new_password)
    elif operation == Operations.CHANGE_EMAIL:
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.query.filter_by(email=new_email).first() is not None:
            return False
        user.email = new_email
    else:
        return False

    db.session.commit()
    return True

