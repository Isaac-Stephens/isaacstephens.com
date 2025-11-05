# --------------------------------------------
# Views for isaacstephens.com
# --------------------------------------------

from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html")

@views.route('/about-me')
def about_me():
    return render_template("resume.html")

@views.route('/my-homelab')
def lab():
    return render_template("homelab.html")