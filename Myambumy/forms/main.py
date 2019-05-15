from flask_wtf import  FlaskForm
from wtforms import StringField,SubmitField,TextAreaField
from wtforms.validators import DataRequired,Length,Optional,Regexp
from flask_ckeditor import CKEditorField

#评论表单
class CommentForm(FlaskForm):
    body = TextAreaField('',validators=[DataRequired()])
    submit = SubmitField()

class DescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    submit = SubmitField()


class TagForm(FlaskForm):
    tag = StringField('Add Tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()

class ArticleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 60)])
    tags = StringField('Category',validators=[DataRequired(), Length(1, 60),Regexp('^[\u4e00-\u9fa5#a-zA-Z0-9]+$',
                                                          message='The tag can contain only 字母 数字 汉字 #.')])
    content = CKEditorField('Content',validators=[DataRequired()])
    submit = SubmitField()
