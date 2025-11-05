from flask import Flask
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), "passwords.env")
load_dotenv(env_path)

def create_app():
    app = Flask(__name__)
    app.secret_key = "SECRET_KEY"

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app

