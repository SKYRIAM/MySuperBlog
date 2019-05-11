import os
import random
from flask import current_app
from faker import Faker
from Myambumy.models import User,Comment,Tag,Photo,Collect
from Myambumy.extensions import db
from PIL import Image
from sqlalchemy.exc import IntegrityError

fake = Faker()
#创建管理员
def fake_admin():
    admin = User(
        name='Steave',
        username='Buck',
        email='putdowncat@163.com',
        bio=fake.sentence(),
        website='http://123456.com',
        confirmed=True
        )
    admin.set_password('12345678')
    db.session.add(admin)
    db.session.commit()
#创建用户

def fake_users(count=10):
    for i in range(count):
        user = User(
            name=fake.name(),
            confirmed=True,
            username=fake.user_name(),
            bio=fake.sentence(),
            location=fake.city(),
            website=fake.url(),
            member_since=fake.date_this_decade(),
            email=fake.email())
        user.set_password('123456')
        db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

#创建标签
def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name = fake.word())
        db.session.add(tag)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
#创建图片
def fake_photo(count=30):
    upload_path = current_app.config['ALBUMY_UPLOAD_PATH']
    for i in range(count):
        print(i)

        filename = 'random_%d.jpg' % i
        r = lambda: random.randint(128, 255)
        img = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))
        img.save(os.path.join(upload_path, filename))

        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year()
        )

        # tags
        for j in range(random.randint(1, 5)):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in photo.tags:
                photo.tags.append(tag)

        db.session.add(photo)
    db.session.commit()


def fake_comment(count=30):
    for i in range(count):
        comment = Comment(
            author=User.query.get(random.randint(1,User.query.count())),
            body = fake.sentence(),
            timestamp=fake.date_time_this_year(),
            photo=Photo.query.get(random.randint(1, Photo.query.count()))
        )
        db.session.add(comment)
    db.session.commit()

def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        photo = Photo.query.get(random.randint(1, Photo.query.count()))
        user.collect(photo)

    db.session.commit()

