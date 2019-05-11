from flask import Blueprint,render_template,request,current_app,send_from_directory,flash,redirect,url_for,abort
from Myambumy.models import User,Photo,Comment,Tag,Collect
from Myambumy.decorations import confirm_required,permission_required
from flask_login import  login_required,current_user
from Myambumy.utils import resize_image,rename_image,flash_errors
import os
from Myambumy.forms.main import CommentForm
from Myambumy.extensions import db
from Myambumy.forms.main import DescriptionForm,TagForm
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
    return redirect(url_for('.show_photo', photo_id=photo_id))

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
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    if form.validate_on_submit():
        name = form.tag.data
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        if tag not in photo.tags:
            photo.tags.append(tag)
            db.session.commit()
    flash_errors(form)
    return redirect(url_for('.show_photo',photo_id=photo_id))

#先查询有没有已存在TAG再创建
@main_bp.route('/photo/<int:photo_id>/tag/new2',methods=['POST'])
@login_required
def new_tag2(photo_id):
    form = TagForm()
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    if form.validate_on_submit():
        name = form.tag.data
        tag = Tag.query.filter_by(name=name).first()
        if tag:
            photo.tags.append(tag)
            db.session.commit()
        else:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.commit()

            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
    flash_errors(form)
    return redirect(url_for('.show_photo',photo_id=photo_id))

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
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    flash('Delete Tag','success')
    return redirect(url_for('.show_photo',photo_id=photo_id))

#删除评论
@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/comment/<int:comment_id>',methods=['POST'])
@login_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag+=1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_photo',photo_id = comment.photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new',methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id, page=page))

#设置评论的开启，还是给管理员用吧
@main_bp.route('/set-comment/<int:photo_id>', methods=['POST','GET'])
@login_required
def set_comment(photo_id):
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

#评论回复
@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_photo', photo_id=comment.photo_id, reply=comment_id,
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


