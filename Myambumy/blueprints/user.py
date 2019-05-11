from flask import Blueprint,render_template,request,current_app
from Myambumy.models import User,Photo
user_bp  = Blueprint('user',__name__)

@user_bp.route('/<username>')
def index(username):
    print('qwqw',username)
    user = User.query.filter_by(username=username).first_or_404()
    print(user.username)
    page = request.args.get('page',1,type=int)
    print('lll')
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']

    pagination = Photo.query.with_parent(user).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    print(pagination,'asasas')
    photos = pagination.items
    print('vavavav')
    return render_template('user/index.html', user=user,pagination=pagination,photos=photos)

