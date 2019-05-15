import  os
import click
from flask import Flask,render_template
from Myambumy.settings import config
from Myambumy.extensions import db,mail,moment,bootstrap,login_manager,dropzone,csrf,avatars
from Myambumy.blueprints.user import user_bp
from Myambumy.blueprints.main import main_bp
from Myambumy.blueprints.auth import auth_bp
from Myambumy.blueprints.ajax import ajax_bp
from Myambumy.models import User,Role
from Myambumy.emails import  send_confirm_email
from Myambumy.utils import generate_token,vaildate_token
from flask_wtf.csrf import  CSRFError
from Myambumy.fakes import fake_admin,fake_comment,fake_photo,fake_tag,fake_user,fake_collect,fake_follow,fake_article
from Myambumy.models import Article,Photo,Tag,Collect,Collect_article

def create_app(config_name=None):
    if config_name is None:
        config_name=os.getenv('FLASK_CONFIG','development')

    app = Flask('Myambumy')
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errorhandlers(app)
    register_shell_context(app)
    register_template_context(app)
    return app


def register_extensions(app):
    db.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    dropzone.init_app(app)
    csrf.init_app(app)
    avatars.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ajax_bp,url_prefix='/ajax')

#上下文
def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db,User=User,generate_token=generate_token,Article=Article,Tag=Tag,Photo=Photo,Collect=Collect,Collect_article=Collect_article)

def register_template_context(app):
    pass

def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'),400

    #文件大小错误处理
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop',is_flag=True,help='Create after drop.')
    def initdb(drop):
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    #初始化权限和角色
    @app.cli.command()
    def init():
        """Initialize Albumy."""
        click.echo('Initializing the database...')
        db.create_all()
        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done.')
        click.echo('Done.')

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--photo', default=30, help='Quantity of photos, default is 500.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 500.')
    @click.option('--collect', default=50, help='Quantity of collects, default is 500.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 500.')
    @click.option('--follow', default=30, help='Quantity of follow, default is 50.')
    @click.option('--article', default=30, help='Quantity of follow, default is 50.')
    def forge(user, photo, tag, comment,collect,follow,article):
        """Generate fake data."""



        db.drop_all()
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()
        click.echo('Generating the administrator...')
        fake_admin()
        click.echo('Generating %d users...' % user)
        fake_user(user)
        click.echo('Generating %d tags...' % tag)
        fake_tag(tag)
        click.echo('Generating %d article...' % article)
        fake_article(article)
        click.echo('Generating %d photos...' % photo)
        fake_photo(photo)
        click.echo('Generating %d comments...' % comment)
        fake_comment(comment)
        click.echo('Generating %d collects...' % photo)
        fake_collect(collect)
        click.echo('Generating %d follows...' % follow)
        fake_follow(follow)

        click.echo('Done.')


