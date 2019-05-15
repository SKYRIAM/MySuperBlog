from flask import url_for

from Myambumy.extensions import db
from Myambumy.models import Notification,Article


def push_follow_notification(follower, receiver):
    message = 'User <a href="%s">%s</a> followed you.' % \
              (url_for('user.index', username=follower.username), follower.username)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_comment_notification(photo_id, receiver, page=1):
    message = '<a href="%s#comments">This photo</a> has new comment/reply.' % \
              (url_for('main.show_photo', photo_id=photo_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()

def push_comment_notification_article(article_id,receiver, page=1):
    article = Article.query.get_or_404(article_id)

    message = 'Your article <a href="%s#comments"> %s</a> has new comment/reply.' % \
              (url_for('main.show_article', article_id=article_id, page=page),article.title)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()

def push_collect_notification(collector, photo_id, receiver):
    message = 'User <a href="%s">%s</a> collected your <a href="%s">photo</a>' % \
              (url_for('user.index', username=collector.username),
               collector.username,
               url_for('main.show_photo', photo_id=photo_id))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()

def push_collect_notification_article(collector, article_id, receiver):
    message = 'User <a href="%s">%s</a> collected your <a href="%s">article</a>' % \
              (url_for('user.index', username=collector.username),
               collector.username,
               url_for('main.show_article', article_id=article_id))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()