# --------------------------------------------
# Views for isaacstephens.com
# --------------------------------------------

from flask import Blueprint, render_template
from datetime import datetime
views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html")

# date for copyright
def inject_now():
    return {"now": datetime.now(datetime.timezone.utc)}

# ++++++++++++++++++++++++
# ======= Articles =======
# ++++++++++++++++++++++++
@views.route('/about-me')
def about_me():
    return render_template("resume.html")

@views.route('/my-homelab')
def lab():
    return render_template("homelab.html")

@views.route('/comparative-analysis-of-linux-scheduling')
def cs3800finalpaper():
    return render_template("articles/CS3800_FinalProject.html")

@views.route('/real-time-containers')
def cpe5170finalpaper():
    return render_template("articles/RTOS_Paper.html")

@views.route('/bsu_mc')
def bsu_mc():
    return render_template("bsu_mc.html")