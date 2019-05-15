from flask import Blueprint,render_template,request,current_app,send_from_directory,flash,redirect,url_for,abort
from Myambumy.models import User,Photo,Comment,Tag,Collect,Article,Collect_article,Notification
from Myambumy.decorations import confirm_required,permission_required
from flask_login import  login_required,current_user
from Myambumy.utils import resize_image,rename_image,flash_errors
import os
from Myambumy.forms.main import CommentForm
from Myambumy.extensions import db
from Myambumy.forms.main import DescriptionForm,TagForm,ArticleForm
from Myambumy.notifications import push_comment_notification,push_collect_notification,push_comment_notification_article
main_bp  = Blueprint('main',__name__)

@main_bp.route('/')
def index():
    return render_template('/main/index.html')

@main_bp.route('/expplore')
def explore():
    return render_template('/main/index.html')



@login_required
@confirm_required
@permission_required('UPLOAD')
@main_bp.route('/upload',methods=['GET','POST'])
def upload():
    if request.method == 'POST' and 'file' in request.files:
        f = request.files.get('file')
        filename = rename_image(f.filename)
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))
        filename_s = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small'])
        filename_m = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium'])
        photo = Photo(
            filename=filename,
            filename_s=filename_s,
            filename_m=filename_m,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')

#返回对于的头像图片文件
@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

#用来返回图片
@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)

#收藏图片
@main_bp.route('/collect/<int:photo_id>',methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    current_user.collect(photo)
    flash('Photo collected ','info')
    if current_user != photo.author:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return redirect(url_for('.show_photo', photo_id=photo_id))

#收藏文章
@main_bp.route('/collect/article/<int:article_id>',methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect_article(article_id):
    article = Article.query.get_or_404(article_id)
    print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq",article.id)
    if current_user.is_collecting_articles(article):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))
    current_user.collect_article(article)
    flash('Article collected ','info')
    return redirect(url_for('.show_article', article_id=article_id))


#取消收藏的图片
#下一步在photo_sider添加按钮
@main_bp.route('/uncollect/<int:photo_id>',methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash('Not collect yet.', 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))

#取消收藏文章
@main_bp.route('/uncollect/article/<int:article_id>',methods=['POST'])
@login_required
def uncollect_article(article_id):
    article = Article.query.get_or_404(article_id)
    if not current_user.is_collecting_articles(article):
        flash('Not collect yet.', 'info')
        return redirect(url_for('main.show_article', article_id=article_id))

    current_user.uncollect_article(article)
    flash('Article uncollected.', 'info')
    return redirect(url_for('.show_article', article_id=article_id))

#删除照片
@main_bp.route('/delete/photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo delete','info')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.timestamp < photo.timestamp).order_by(Photo.timestamp.desc()).first()
    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.timestamp > photo.timestamp).order_by(
            Photo.timestamp.asc()).first()

        if photo_p is None:
            return redirect(url_for('user.index',username=photo.author.username))
        return redirect(url_for('.show_photo',photo_id = photo_p.id))
    return redirect(url_for('.show_photo',photo_id = photo_n.id))


#展示收藏图片的界面
@main_bp.route('/photo/<int:photo_id>/collectors')
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', collects=collects, photo=photo, pagination=pagination)

#展示文章收藏者界面
@main_bp.route('/photo/<int:article_id>/article/collectors')
def show_collectors_article(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect_article.query.with_parent(article).order_by(Collect_article.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors_article.html', collects=collects, article=article, pagination=pagination)

@main_bp.route('/report/photo/<int:photo_id>',methods=['POST'])
@login_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag+=1
    db.session.commit()
    flash('Photo reported ','success')
    return redirect(url_for('.show_photo',photo_id=photo_id))
#图片向前翻页
@main_bp.route('/photo_previous/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.timestamp > photo.timestamp).order_by(Photo.timestamp.asc()).first()
    if photo_p is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_p.id))

#图片向后翻页，按显示界面顺序
@main_bp.route('/photo_next/<int:photo_id>')
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    #photo_n  = Photo.query.with_parent(photo.author).filter(Photo.id < photo.id).order_by(Photo.id.desc()).first()
    #按时间排序更符合实际
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.timestamp < photo.timestamp).order_by(Photo.timestamp.desc()).first()
    if photo_n is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo',photo_id = photo_n.id))

#修改描述
@main_bp.route('/photo/<int:photo_id>/description',methods=['POST'])
def edit_description(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('Description updated','success')
    flash_errors(form)
    return redirect(url_for('.show_photo',photo_id=photo_id))

    return render_template('main/index.html')

#显示TAG下的图片
@main_bp.route('/tag/<int:tag_id>',defaults={'order':'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
@login_required
def show_tag(tag_id,order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page',1,type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    order_rule = 'time'

    if request.args.get('type') == 'article':
        print("11111111111111111111111111111111111111111111111")
        pagination = Article.query.with_parent(tag).order_by(Article.timestamp.desc()).paginate(page, per_page)
        articles = pagination.items
        if order == 'by_collects':
            articles.sort(key=lambda x: len(x.collectors), reverse=True)
            order_rule = 'collects'
        return render_template('main/show_tag_article.html', tag=tag, pagination=pagination, articles=articles,order_rule=order_rule)
    else:
        pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
        photos = pagination.items
        if order == 'by_collects':
            photos.sort(key=lambda x: len(x.collectors), reverse=True)
            order_rule = 'collects'
        return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)

#每次都会需要不同的TAG
@main_bp.route('/photo/<int:photo_id>/tag/new',methods=['POST'])
@login_required
def new_tag(photo_id):
    form = TagForm()
    if request.args.get('type') == 'article':

        blog = Article.query.get_or_404(photo_id)
    else:
        blog = Photo.query.get_or_404(photo_id)

    if current_user != blog.author:
        abort(403)
    if form.validate_on_submit():
        name = form.tag.data
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        if tag not in blog.tags:
            blog.tags.append(tag)
            db.session.commit()
    flash_errors(form)
    if request.args.get('type') == 'article':
        article_id = photo_id
        return redirect(url_for('.show_article',article_id=article_id))
    else:
        return redirect(url_for('.show_photo', photo_id=photo_id))


#先查询有没有已存在TAG再创建
@main_bp.route('/photo/<int:photo_id>/tag/new2',methods=['POST'])
@login_required
def new_tag2(photo_id):
    form = TagForm()
    if request.args.get('type') == 'article':

        blog = Article.query.get_or_404(photo_id)
    else:
        blog = Photo.query.get_or_404(photo_id)

    if current_user != blog.author:
        abort(403)
    if form.validate_on_submit():
        name = form.tag.data
        tag = Tag.query.filter_by(name=name).first()
        if tag:
            blog.tags.append(tag)
            db.session.commit()
        else:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.commit()

            if tag not in blog.tags:
                blog.tags.append(tag)
                db.session.commit()
    flash_errors(form)
    if request.args.get('type') == 'article':
        article_id = photo_id
        return redirect(url_for('.show_article',article_id=article_id))
    else:
        return redirect(url_for('.show_photo', photo_id=photo_id))


#删除标签，顺便删除图片里的该标签
@main_bp.route('/delete/tag/<int:photo_id>/<int:tag_id>',methods=['POST'])
@login_required
def delete_tag(photo_id,tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag Delete','success')
    return redirect(url_for('.show_photo',photo_id = photo_id))

#只是删除图片标签，不删除原本的标签
@main_bp.route('/delete2/tag/<int:photo_id>/<int:tag_id>',methods=['POST'])
@login_required
def delete2_tag(photo_id,tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if request.args.get('type') == 'article':
        blog = Article.query.get_or_404(photo_id)
    else:
        blog = Photo.query.get_or_404(photo_id)

    if current_user != blog.author:
        abort(403)
    blog.tags.remove(tag)
    db.session.commit()

    flash('Delete Tag','success')
    if request.args.get('type') == 'article':
        article_id = photo_id
        return redirect(url_for('.show_article', article_id=article_id))
    else:
        return redirect(url_for('.show_photo', photo_id=photo_id))

#删除评论
@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if request.args.get('type') == 'article':
        if current_user != comment.author and current_user != comment.article.author:
            abort(403)
    else:
        if current_user != comment.author and current_user != comment.photo.author:
            abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    if request.args.get('type') == 'article':
        return redirect(url_for('.show_article', article_id=comment.article_id))
    else:
        return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/comment/<int:comment_id>',methods=['POST'])
@login_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag+=1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_photo',photo_id = comment.photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    if request.args.get('type') == 'article':
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        article = Article.query.get_or_404(photo_id)
    else:
        photo = Photo.query.get_or_404(photo_id)

    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        if request.args.get('type') == 'article':
            comment = Comment(body=body, author=author, article=article)
        else:
            comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        #print("pppppppppppppppppppppppppppppppppp",replied_id)
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if request.args.get('type') == 'article':
                push_comment_notification_article(article_id=photo_id,receiver=comment.replied.author)
            else:
                push_comment_notification(photo_id=photo.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if request.args.get('type') == 'article':
            if current_user != article.author:
                push_comment_notification_article(photo_id, receiver=article.author, page=page)
        else:
            if current_user != photo.author:
                push_comment_notification(photo_id, receiver=photo.author, page=page)

    flash_errors(form)

    if request.args.get('type') == 'article':
        return redirect(url_for('.show_article', article_id=photo_id, page=page))
    else:
        return redirect(url_for('.show_photo', photo_id=photo_id, page=page))

#设置评论的开启，还是给管理员用吧
@main_bp.route('/set-comment/<int:photo_id>', methods=['POST','GET'])
@login_required
def set_comment(photo_id):
    #如果是文章
    if request.args.get('type') == 'article':
        article = Article.query.get_or_404(photo_id)
        if current_user != article.author and current_user.role.name != 'Administrator':
            abort(403)
        if article.can_comment:
            article.can_comment = False
            flash('Comment disabled', 'info')
        else:
            article.can_comment = True
            flash('Comment enabled', 'info')
        db.session.commit()
        return redirect(url_for('.show_article', article_id=photo_id))
    #如果是照片
    else:
        photo = Photo.query.get_or_404(photo_id)
        if current_user != photo.author :
            abort(403)
        if photo.can_comment:
            photo.can_comment=False
            flash('Comment disabled','info')
        else:
            photo.can_comment = True
            flash('Comment enabled','info')
        db.session.commit()
        return redirect(url_for('.show_photo',photo_id=photo_id))

#图片评论回复
@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_photo', photo_id=comment.photo_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')

#文章评论回复
@main_bp.route('/reply/article/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment_article(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_article', article_id=comment.article_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


#显示图片的详情页
@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page',1,type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page,per_page)
    comments = pagination.items
    comment_form = CommentForm()
    description_form = DescriptionForm()
    description_form.description.data = photo.description
    tag_form = TagForm()

    return render_template('main/photo.html',photo=photo,pagination=pagination,comments=comments,comment_form=comment_form,description_form=description_form,tag_form=tag_form)

#创建文章
@main_bp.route('/article/create',methods=['GET','POST'])
@login_required
@confirm_required
def create_article( ):
    form = ArticleForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        tags = form.tags.data.split('#') #标签用#分隔
        article = Article(title=title,content=content,author=current_user._get_current_object())

        for t in tags:
            tag = Tag.query.filter_by(name = t).first()
            if  not tag:

                new_tag = Tag(name=t)
                tag = new_tag
                db.session.add(new_tag)
                db.session.commit()

            article.tags.append(tag)
            db.session.add(article)
        db.session.commit()
        flash('Article create','success')
        return redirect(url_for('main.show_article',article_id=article.id))
    return render_template('main/create_article.html',form=form)






#显示文章
@main_bp.route('/article/<int:article_id>')
def show_article(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(article).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items
    comment_form = CommentForm()
    tag_form = TagForm()
    return render_template('main/article.html',article=article,comment_form=comment_form,comments=comments,tag_form=tag_form,pagination=pagination)

#删除文章
@main_bp.route('/article/delete/<int:article_id>',methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user != article.author:
        abort(403)
    db.session.delete(article)
    db.session.commit()
    flash('article delete', 'info')
    return redirect(url_for('user.index',username = article.author.username))

#举报文章
@main_bp.route('/article/report/<int:article_id>',methods=['POST'])
@login_required
def report_article(article_id):
    article = Article.query.get_or_404(article_id)
    article.flag += 1
    db.session.commit()
    flash('Article reported ', 'success')
    return redirect(url_for('.show_article', article_id=article_id))
#消息界面
@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('Notification archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications archived.', 'success')
    return redirect(url_for('.show_notifications'))
