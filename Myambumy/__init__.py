import  os
import click
from flask import Flask
from Myambumy.settings import config
from Myambumy.extensions import db,mail,moment,bootstrap,login_manager
from Myambumy.blueprints.user import user_bp
from Myambumy.blueprints.main import main_bp
from Myambumy.blueprints.auth import auth_bp
from Myambumy.models import User
from Myambumy.emails import  send_confirm_email
from Myambumy.utils import generate_token,vaildate_token


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


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')

#上下文
def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db,User=User,generate_token=generate_token)

def register_template_context(app):
    pass

def register_errorhandlers(app):
    pass

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

    def init():
        """Initialize Albumy."""
        click.echo('Initializing the database...')
        db.create_all()

        click.echo('Done.')


