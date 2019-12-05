import os

# init SQLAlchemy so we can use it later in our models

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required
try:
    from blueprints import resources, about, maps
except ModuleNotFoundError:
    from .blueprints import resources, about, maps


db = SQLAlchemy()


basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(test_config=None):
    # create and configure the app
    app = Flask(
        __name__,
        static_folder='static',
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'app.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register blueprints (like views in django)
    app.register_blueprint(resources.bp)
    app.register_blueprint(maps.bp)
    app.register_blueprint(about.bp)
    import auth
    app.register_blueprint(auth.bp)

    @app.route('/')
    @login_required
    def landing():
        return render_template('landing/index.html')

    @app.route('/termsofservice')
    def termsofservice():
        return render_template('termsofservice.html')

    @app.route('/privacypolicy')
    def privacypolicy():
        return render_template('privacypolicy.html')

    return app
