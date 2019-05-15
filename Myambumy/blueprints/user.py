from flask import Blueprint,render_template,request,current_app,flash,redirect,url_for
from Myambumy.models import User,Photo,Collect,Article,Collect_article
from flask_login import current_user,login_required
from Myambumy.decorations import confirm_required,permission_required
from Myambumy.utils import redirect_back
from Myambumy.notifications import push_follow_notification,push_collect_notification,push_comment_notification
user_bp  = Blueprint('user',__name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    print(user.username)

    page = request.args.get('page',1,type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Photo.query.with_parent(user).order_by(Photo.timestamp.desc()).paginate(page, per_page)

    photos = pagination.items
    print('vavavav')
    return render_template('user/index.html', user=user,pagination=pagination,photos=photos)

@user_bp.route('/<username>/article')
def article_index(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Article.query.with_parent(user).order_by(Article.timestamp.desc()).paginate(page, per_page)
    articles = pagination.items
    return render_template('user/article_index.html',user=user,pagination=pagination,articles=articles)


@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('Already followed.', 'info')
        return redirect(url_for('.index', username=username))

    current_user.follow(user)
    flash('User followed.', 'success')
    push_follow_notification(follower=current_user, receiver=user)
    return redirect_back()


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('Not follow yet.', 'info')
        return redirect(url_for('.index', username=username))

    current_user.unfollow(user)
    flash('User unfollowed.', 'info')
    return redirect_back()

#关注自己的人
@user_bp.route('/<username>/followers')
def  show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = user.followers.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/followers.html', user=user, pagination=pagination, follows=follows)

#关注别人
@user_bp.route('/<username>/following')
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = user.following.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/following.html', user=user, pagination=pagination, follows=follows)

#显示图片收藏列表
@user_bp.route('/<username>/collections')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    collects_article = Collect_article.query.with_parent(user).count()
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects,collects_article=collects_article)

#显示文章收藏列表
@user_bp.route('/<username>/article/collections')
def show_collections_article(username):
    user = User.query.filter_by(username=username).first_or_404()
    count_photo = Collect.query.with_parent(user).count()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Collect_article.query.with_parent(user).order_by(Collect_article.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/article_collections.html', user=user, pagination=pagination, collects=collects,count_photo=count_photo)


