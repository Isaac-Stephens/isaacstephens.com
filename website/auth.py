# --------------------------------------------
# Views for gymman web demo
# --------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
import os
from dotenv import load_dotenv


auth = Blueprint('auth', __name__)
auth.permanent_session_lifetime = timedelta(minutes=30)

env_path = os.path.join(os.path.dirname(__file__), "db.env")
load_dotenv(env_path)


# database conn
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

def is_logged_in(required_role=None):
    """Verify user session and optional role."""

    if "user_id" not in session:
        return False
    if required_role and session.get("role", "").lower() != required_role.lower():
        return False
    return True

@auth.route('/gymman-login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.permanent = True

            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role_name"]
            session["name"] = user["first_name"] + ' ' +user["last_name"]

            role = user["role_name"].lower()

            # Redirect the user to their role-specific dashboard
            if role == "owner":
                cursor.close()
                db.close()
                return redirect(url_for("auth.owner_dashboard"))
            elif role == "staff":
                cursor.close()
                db.close()
                return redirect(url_for("auth.staff_dashboard"))
            elif role == "trainer":
                cursor.close()
                db.close()
                return redirect(url_for("auth.trainer_dashboard"))
            elif role == "member":
                cursor.close()
                db.close()
                return redirect(url_for("auth.member_dashboard"))
            else:
                flash("Unknown role.")
                cursor.close()
                db.close()
                return redirect(url_for("auth.login"))
            
        else:
            cursor.close()
            db.close()
            flash("Invalid credentials. Username or Password is incorrect.")
            return redirect(url_for("auth.login"))
        
    #if request was GET, load
    return render_template("gymman_templates/login.html")

@auth.route('/gymman-logout')
def logout():
    session.clear()
    flash("Succesfully Logged Out!")
    resp = redirect(url_for("auth.login"))
    resp.set_cookie('session', '', expires=0)
    return resp

@auth.route('/gymman-sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_repeat = request.form['password_repeat']

        # validation
        if password != password_repeat:
            flash('Passwords do not match.')
            return redirect(url_for('auth.sign_up'))
        
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # check if username OR email already exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username or email already exists.')
            cursor.close()
            db.close()
            return redirect(url_for('auth.sign_up'))
        
        # insert new user
        hashed_pw = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (first_name, last_name, email, username, password_hash, role_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, username, hashed_pw, 'Member'))
        db.commit()

        # add user to members list, birth date, membership start date, and sex should all be added from either the member's profile view or the owner/staff's memberships view
        cursor.execute("""
            INSERT INTO Members (first_name, last_name, email)
            VALUES (%s, %s, %s)
        """, (first_name, last_name, email)) 

        cursor.close()
        db.close()
        flash('Account created successfully! You can now log in.')
        return redirect(url_for('auth.login'))

    return render_template("gymman_templates/sign_up.html")


# ========================================================= Owner View ==========================================================
@auth.route("/owner/dashboard")
def owner_dashboard():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/dashboard_owner.html", username=session["username"], name=session["name"])

@auth.route("/owner/memberships")
def owner_memberships():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/memberships.html", username=session["username"], name=session["name"])

@auth.route("/owner/payments")
def owner_payments():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/payments.html", username=session["username"], name=session["name"])

@auth.route("/owner/staff")
def owner_staff():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/staff.html", username=session["username"], name=session["name"])

@auth.route("/owner/trainers")
def owner_trainers():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/trainers.html", username=session["username"], name=session["name"])

@auth.route("/owner/exercise_logs")
def owner_exercise_logs():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/exercise_logs.html", username=session["username"], name=session["name"])

@auth.route("/owner/error_logs")
def owner_errors():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/error_logs.html", username=session["username"], name=session["name"])

# ========================================================= Staff View =========================================================
@auth.route("/staff/dashboard")
def staff_dashboard():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/dashboard_staff.html", username=session["username"], name=session["name"])

@auth.route("/staff/checkins")
def staff_checkins():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/staff_view/checkins.html", username=session["username"], name=session["name"])

@auth.route("/staff/payments")
def staff_payments():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/staff_view/payments.html", username=session["username"], name=session["name"])

@auth.route("/staff/memberships")
def staff_memberships():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/staff_view/memberships.html", username=session["username"], name=session["name"])

@auth.route("/staff/error_logs")
def staff_error_logs():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/staff_view/error_logs.html", username=session["username"], name=session["name"])

# ========================================================= Trainer View =========================================================
@auth.route("/trainer/dashboard")
def trainer_dashboard():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/dashboard_trainer.html", username=session["username"], name=session["name"])

@auth.route("/trainer/clients")
def trainer_clients():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/trainer_view/clients.html", username=session["username"], name=session["name"])

@auth.route("/trainer/workouts")
def trainer_workouts():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/trainer_view/workouts.html", username=session["username"], name=session["name"])

@auth.route("/trainer/logs")
def trainer_logs():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/trainer_view/logs.html", username=session["username"], name=session["name"])

@auth.route("/trainer/reports")
def trainer_reports():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/trainer_view/reports.html", username=session["username"], name=session["name"])

# ========================================================= Member View =========================================================
@auth.route("/member/dashboard")
def member_dashboard():
    if not is_logged_in("Member"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/dashboard_member.html", username=session["username"], name=session["name"])

@auth.route("/member/profile")
def member_profile():
    if not is_logged_in("Member"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/member_view/profile.html", username=session["username"], name=session["name"])

@auth.route("/member/membership")
def member_membership():
    if not is_logged_in("Member"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/member_view/membership.html", username=session["username"], name=session["name"])

@auth.route("/member/workouts")
def member_workouts():
    if not is_logged_in("Member"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/member_view/workouts.html", username=session["username"], name=session["name"])

@auth.route("/member/payments")
def member_payments():
    if not is_logged_in("Member"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/member_view/payments.html", username=session["username"], name=session["name"])

@auth.route("/member/support")
def member_support():
    if not is_logged_in("Member"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/member_view/support.html", username=session["username"], name=session["name"])