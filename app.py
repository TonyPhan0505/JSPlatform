from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from os import path
from flask_mail import Mail, Message
from os import environ
import re

app = Flask(__name__)
app.config["SECRET_KEY"] = "a^U2YB*Lw`bH#?)0{NICKhD&yAE|vOr}+85xJos6$ZzS3QnglG<4e@>7V[j(RpPX!1c9fT~mtFq]kdiuWM_"
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
	uri = uri.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///my_database.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['MAIL_SERVER']='smtp.aol.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'juststartplatform@aol.com'
app.config['MAIL_PASSWORD'] = 'lqsahqsuozvifdaj'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['UPLOAD_FOLDER'] = 'static/files'

mail = Mail(app)
db = SQLAlchemy(app)

import routes

from models import *

if not path.exists("my_database.db"):
	db.create_all()

login = LoginManager()
login.login_view = 'login'
login.init_app(app)

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

if __name__ == "__main__":
	app.run(debug=True)
