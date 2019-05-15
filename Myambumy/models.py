from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from Myambumy.extensions import db
from datetime import datetime
from flask import  current_app
from flask_avatars import Identicon
import  os

#标签和图片间是多对多的关系
tagging = db.Table('tagging',
                   db.Column('article_id',db.Integer,db.ForeignKey('article.id')),
                   db.Column('photo_id', db.Integer, db.ForeignKey('photo.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                   )
#标签
class Tag(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),unique=True,index=True)
    articles = db.relationship('Article', secondary=tagging, back_populates='tags')
    photos = db.relationship('Photo', secondary=tagging, back_populates='tags')

class Photo(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    description = db.Column(db.String(500))
    filename = db.Column(db.String(64))
    filename_s = db.Column(db.String(64))  # 存储小型尺寸图片名称
    filename_m = db.Column(db.String(64))  #
    timestamp = db.Column(db.DateTime,default=datetime.utcnow,index=True)
    can_comment = db.Column(db.Boolean,default=True)
    flag = db.Column(db.Integer,default=0)#举报
    #设置和用户的外键
    author_id = db.Column(db.Integer,db.ForeignKey('user.id'))#创建者ID
    author = db.relationship('User',back_populates='photos')
    #设置图片与评论间的关系
    comments = db.relationship('Comment',back_populates='photo',cascade='all')
    #设置与标签之间的关系
    tags = db.relationship('Tag', secondary=tagging, back_populates='photos')
    #收藏
    collectors = db.relationship('Collect', back_populates='collected', cascade='all')

class Article(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(60),index=True)
    content = db.Column(db.Text)
    flag = db.Column(db.Integer,default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    can_comment = db.Column(db.Boolean,default=True)
    #作者
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 创建者ID
    author = db.relationship('User', back_populates='articles')
    #标签
    tags = db.relationship('Tag', secondary=tagging, back_populates='articles')
    #评论
    comments = db.relationship('Comment', back_populates='article', cascade='all')
    #收藏
    collectors = db.relationship('Collect_article', back_populates='collected_article', cascade='all')



class Comment(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,default=datetime.utcnow,index=True)
    flag = db.Column(db.Integer,default=0)
    #建立和用户的关系
    author_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    author = db.relationship('User',back_populates='comments')
    #建立自身的临界列表关系
    replied_id = db.Column(db.Integer,db.ForeignKey('comment.id'))
    replies = db.relationship('Comment', back_populates='replied', cascade='all')
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])
    #建立与图片的双向关系
    photo_id = db.Column(db.Integer,db.ForeignKey('photo.id'))
    photo = db.relationship('Photo',back_populates='comments')
    # 建立与文章的双向关系
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    article = db.relationship('Article', back_populates='comments')

class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')






class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),unique=True,index=True) #index设为True建立索引
    email = db.Column(db.String(254),index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(30))
    website = db.Column(db.String(50))
    location = db.Column(db.String(50))
    bio = db.Column(db.String(120))#自我介绍
    member_since = db.Column(db.DateTime,default=datetime.utcnow)
    #建立和article一对多的关系
    articles = db.relationship('Article',back_populates='author',cascade='all')#设立外键和级联
    #建立和photo一对多的关系
    photos = db.relationship('Photo',back_populates='author',cascade='all')#设立外键和级联
    #建立和角色的关系,设立外键
    role = db.relationship('Role',back_populates='users')
    role_id = db.Column(db.Integer,db.ForeignKey('role.id'))
    confirmed = db.Column(db.Boolean,default=False)
    #建立和评论一对多的关系
    comments = db.relationship('Comment',back_populates='author',cascade='all')
    # 头像文件
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    #收藏
    collections = db.relationship('Collect', back_populates='collector', cascade='all')
    collections_article = db.relationship('Collect_article', back_populates='collector', cascade='all')
    #关注
    following = db.relationship('Follow', foreign_keys=[Follow.follower_id], back_populates='follower',
                                lazy='dynamic', cascade='all')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], back_populates='followed',
                                lazy='dynamic', cascade='all')

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def vaildate_password(self,password):
        return check_password_hash(self.password_hash,password)
    #构造函数
    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        self.follow(self)  # 关注自己，可以用同种方法获取自己的动态
        self.set_role()
        self.generate_avatar()

    #初始化权限
    def set_role(self):
        if self.role is None:
            if self.email ==current_app.config['ALBUMY_ADMIN_EMAIL'] :
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()
    #初始化随机头像
    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()


    #为已存在用户赋值权限
    @staticmethod
    def init_role_permissions( ):
        users = User.query.all()
        for user in users:
            if user.role is None:
                if user.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
                    user.role = Role.query.filter_by(name='Administrator').first()
                else:
                    user.role = Role.query.filter_by(name='User').first()
                db.session.commit()

    #权限认证
    def can(self,permission_name):

        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not  None and self.role is not None and permission in self.role.permissions
    #设为属性 判断是否为管理员
    @property
    def id_admin(self):
        return self.role.name == 'Administrator'

    #判断图片是否已经收藏
    def is_collecting(self, photo):
        return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first() is not None

    def is_collecting_articles(self, article):
        print("wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww",type(article))
        return Collect_article.query.with_parent(self).filter_by(collected_article_id = article.id).first() is not None

    #收藏图片
    def collect(self,photo):
        if not self.is_collecting(photo):
            print(photo.id)
            collect = Collect(collector = self,collected=photo)
            db.session.add(collect)
            db.session.commit()

    def collect_article(self,article):
        if not self.is_collecting_articles(article):
            #print("ppppppppppppppppppppppppppaaaaaaaaaaaaaaaaaa"+article.id)
            collect = Collect_article(collector=self,collected_article=article)
            db.session.add(article)
            db.session.commit()

    #取消收藏图片
    def uncollect(self,photo):
        collect = Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    #取消收藏文章
    def uncollect_article(self,article):
        collect = Collect_article.query.with_parent(self).filter_by(collected_article_id=article.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()
    #关注用户
    def follow(self,user):
        if not self.is_following(user) :
            follow = Follow(follower=self,followed=user)
            db.session.add(follow)
            db.session.commit()

    #解除关注
    def unfollow(self,user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow :
            db.session.delete(follow)
            db.session.commit()

    #查询是否被某个用户关注
    def is_followed_by(self,user):
        return self.followers.filter_by(follower_id = user.id).first() is not None


    #插叙是否以及关注过该用户
    def is_following(self, user):
        if user.id is None:  # when follow self, user.id will be None
            print("as")
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None


class Collect(db.Model):
    collector_id = db.Column(db.Integer,db.ForeignKey('user.id'),primary_key=True)
    #与图片建立外键
    collected_id = db.Column(db.Integer,db.ForeignKey('photo.id'),primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    #建立关系
    collector = db.relationship('User', back_populates='collections', lazy='joined')#joined预加载，对两侧的表进行联结操作，减少一次查询
    #photo
    collected = db.relationship('Photo', back_populates='collectors', lazy='joined')


class Collect_article(db.Model):
    collector_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    # 与文章建立外键
    collected_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # article
    collected_article = db.relationship('Article', back_populates='collectors', lazy='joined')
    #建立和用户的关系
    collector = db.relationship('User', back_populates='collections_article', lazy='joined')  # joined预加载，对两侧的表进行联结操作，减少一次查询

#权限    权限和角色：多对多
roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
                             )

class Permission(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(30),unique=True)
    roles = db.relationship('Role',secondary = roles_permissions,back_populates='permissions')

#角色
class Role(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(30),unique=True)
    permissions = db.relationship('Permission',secondary = roles_permissions,back_populates='roles')
    #和User建立1对多的双向关系
    users = db.relationship('User',back_populates='role')

    #初始化角色和权限
    @staticmethod#静态方法，跟普通函数没什么区别，与类和实例都没有所谓的绑定关系，它只不过是碰巧存在类中的一个函数而已。不论是通过类还是实例都可以引用该方法。
    def init_role():
        roles_permissions_map = {
            'Locked': ['FOLLOW', 'COLLECT'],
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER']
        }
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name = role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions=[]
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name = permission_name).first()

                if permission is None:
                    permission = Permission(name = permission_name)
                    db.session.add(permission)
                role.permissions.append(permission) #为角色添加权限
        db.session.commit()


@db.event.listens_for(Photo, 'after_delete', named=True)
def delete_photos(**kwargs):
    target = kwargs['target']
    for filename in [target.filename, target.filename_s, target.filename_m]:
        path = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
        if os.path.exists(path):  # not every filename map a unique file
            os.remove(path)




