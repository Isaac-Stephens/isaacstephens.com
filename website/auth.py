# ======================================================================= #
#                           GYMMAN: AUTH PATHS                            #
#                         Author: Isaac Stephens                          #
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
#         Junior, Computer Science, CS Department, Missouri S&T           #
#             issq3r@mst.edu || isaac.stephens1529@gmail.com              #
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
# This file (auth.py) contains the majority of the backend functionality  #
# for the GymMan Demo site. All routes and verifications happen here.     #
#                                                                         #
#  A live web demo can be found @ https://isaacstephens.com/gymman-login. #
# ======================================================================= #

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from .models import *

auth = Blueprint('auth', __name__)
auth.permanent_session_lifetime = timedelta(minutes=30)

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
            if user["role_id"] == 1:
                session["role"] = "owner"
            elif user["role_id"] == 2:
                session["role"] = "staff"
            elif user["role_id"] == 4:
                session["role"] = "trainer"
            else:
                session["role"] = "member"
            session["name"] = user["first_name"] + ' ' +user["last_name"]           
            role = session["role"]
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
            INSERT INTO users (first_name, last_name, email, username, password_hash, role_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, username, hashed_pw, 3))
        db.commit()
        # add user to members list, birth date, membership start date, and sex should all be added from either the member's profile view or the owner/staff's memberships view
        cursor.execute("""
            INSERT INTO Members (first_name, last_name, email)
            VALUES (%s, %s, %s)
        """, (first_name, last_name, email)) 
        db.commit()     
        cursor.close()
        db.close()
        flash('Account created successfully! You can now log in.')
        return redirect(url_for('auth.login'))
    return render_template("gymman_templates/sign_up.html")

def checkin():
    if not (is_logged_in("Owner") or is_logged_in("Staff")):
        return redirect(url_for("auth.login"))
    member_search = request.form.get("member_search", "").strip()
    # No input provided
    if not member_search:
        flash("Please enter a member ID or name.", "error")
        return redirect(request.referrer)
    # Lookup member
    member = db_findMember(member_search)
    # Member not found
    if not member:
        flash("Member not found.", "error")
        return redirect(request.referrer)
    # Log check-in
    db_logCheckin(member)
    flash(f"{member['first_name']} {member['last_name']} checked in successfully!", "success")
    return redirect(request.referrer)

@auth.route("/members/<int:member_id>/modify", methods=['GET', 'POST'])
def modify_member_form(member_id):
    # Allow Owners, Staff, or Members (but members can only access themselves)
    if not (is_logged_in("Owner") or is_logged_in("Staff") or is_logged_in("Member")):
        flash("You do not have permission to modify this member.")
        return redirect(url_for("auth.login"))

    # Member role cannot modify others
    if is_logged_in("Member") and session.get("member_id") != member_id:
        flash("You do not have permission to modify this member.")
        return redirect(url_for("auth.login"))

    info = db_findMember(member_id)
    phone_numbers = db_getMemberPhone(member_id)
    emergency_contacts = db_getMemberEmergencyContacts(member_id)

    if request.method == 'POST':
        if 'new_phone' in request.form:
            new_phone_num = request.form.get("new_phone_num")
            new_phone_num_type = request.form.get("new_phone_num_type")
            db_addMemberPhone(member_id, new_phone_num, new_phone_num_type)
            flash("Phone Number Added Successfully!")
            return redirect(request.referrer)
        elif 'delete_phone' in request.form:
            phone_id = request.form.get("delete_phone")
            db_deletePhoneNum(phone_id)
            flash("Phone Number Deleted Successfully.")
            return redirect(request.referrer)
        elif 'delete_contact' in request.form:
            contact_id = request.form.get("delete_contact")
            db_deleteEmergencyContact(contact_id)
            flash("Emergency Contact Deleted Successfully.")
            return redirect(request.referrer)
        elif 'new_contact' in request.form:
            fname = request.form.get("new_contact_fname")
            lname = request.form.get("new_contact_lname")
            rel = request.form.get("new_contact_relationship")
            phone = request.form.get("new_contact_phone")
            email = request.form.get("new_contact_email")
            db_addMemberEmergencyContact(member_id, fname, lname, rel, phone, email)
            flash("New Emergency Contact Added Successfully!")
            return redirect(request.referrer)
        elif 'new_email' in request.form:
            email = request.form.get("new_email")
            db_updateMemberEmail(member_id, email)
            flash("Email Updated Successfully!")
            return redirect(request.referrer)

    return render_template(
        "/gymman_templates/modify_member.html", 
        info=info, 
        member_id=member_id,
        phone_numbers=phone_numbers,
        emergency_contacts=emergency_contacts)

# +++++++++++++++++++++++++++++++++++
# =========== Owner Views ===========
# +++++++++++++++++++++++++++++++++++
@auth.route("/owner/dashboard")
def owner_dashboard():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    
    total_members = db_getNumTotalMembers()
    pending_payments = db_getNumPendingPayments()
    total_active_trainers = db_getNumActiveTrainers()
    total_revenue = db_aggregatePayments()

    return render_template(
        "/gymman_templates/dashboard_owner.html", 
        username=session["username"], 
        name=session["name"],
        total_members=total_members,
        pending_payments=pending_payments,
        total_active_trainers=total_active_trainers,
        total_revenue=total_revenue
    )

@auth.route("/owner/memberships", methods=['GET','POST'])
def owner_memberships():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    
    member_lookup = None
    num_shown = session.get("num_checkins_shown", 15)

    if request.method == 'POST':
        # If "Load More" is pressed, increment by 5
        if 'load_more' in request.form:
            num_shown += 5
            session["num_checkins_shown"] = num_shown
        elif 'lookup' in request.form:
            member_lookup = db_memberLookUp(request.form.get('member_search', '').strip())
            if not member_lookup:
                flash("Member not found :(")
        elif 'checkin' in request.form:
            # If this POST was for a check-in action
            return checkin()
        elif 'new_member' in request.form:
            fname = request.form.get("new_fname")
            lname = request.form.get("new_lname")
            bd = request.form.get("new_birthdate")
            email = request.form.get("new_email")
            sex = request.form.get("new_sex")
            username = request.form.get("new_username")
            pw = request.form.get("new_password")
            pw_repeat = request.form.get("repeat_new_password")

            # validation
            if pw != pw_repeat:
                flash('Passwords do not match.')
                return redirect(request.referrer)      
            db = get_db()
            cursor = db.cursor(dictionary=True)
            # check if username OR email already exists
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Username or email already exists.')
                cursor.close()
                db.close()
                return redirect(request.referrer)
            cursor.close()
            db.close()
            if not all([fname, lname, email, username, pw, pw_repeat]):
                flash("Missing required fields.")
                return redirect(request.referrer)

            db_createMemberUser(fname, lname, bd, email, sex, username, pw)
            flash("New member created!")
            return redirect(request.referrer)
        elif 'modify_member' in request.form:
            member_id = request.form['modify_member']
            return redirect(url_for('auth.modify_member_form', member_id=member_id))

        elif 'delete_member' in request.form:
            member_id = request.form['delete_member']
            db_deleteMember(member_id)
            flash("Member deleted successfully.")
            return redirect(request.referrer)
        elif 'add_payment' in request.form:
            member_id = request.form.get("add_payment")  # button value = member_id
            amount_raw = request.form.get("payment_amount")
            status = request.form.get("payment_status", "pending")
            payment_type = request.form.get("payment_type", "membership")

            if not member_id or not amount_raw:
                flash("Member and amount are required to add a payment.")
                return redirect(request.referrer)

            try:
                amount = float(amount_raw)
            except ValueError:
                flash("Invalid amount for payment.")
                return redirect(request.referrer)

            db_addPayment(member_id, amount, status=status, payment_type=payment_type)
            flash("Payment added for member.")
            return redirect(request.referrer)
        else:
            return redirect(request.referrer)

    # Fetch Member List
    member_list = db_showAllMembers()

    # Fetch recent check-ins
    recent_checkins = db_showRecentCheckIns(num_shown)
    
    return render_template(
        "/gymman_templates/owner_view/memberships.html", 
        username=session["username"], 
        name=session["name"],
        recent_checkins=recent_checkins,
        num_shown=num_shown,
        member_lookup=member_lookup,
        member_list=member_list
    )

@auth.route("/owner/payments", methods=['GET', 'POST'])
def owner_payments():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    
    pending_payments = []
    search_results = None
    aggregate_total = None

    db = get_db()
    cursor = db.cursor(dictionary=True)
    pending_payments = db_loadPendingPayments()

    if request.method == 'POST':
        # Search payments by member and/or date range and status
        if 'search_payment' in request.form:
            member_query = request.form.get("search_member", "").strip()
            date_from = request.form.get("date_from")  # yyyy-mm-dd
            date_to = request.form.get("date_to")      # yyyy-mm-dd
            status_filter = request.form.get("status_filter", "").strip().lower()

            where = []
            params = []

            if member_query:
                where.append("(p.member_id = %s OR CONCAT(m.first_name, ' ', m.last_name) LIKE %s)")
                params.append(member_query)
                params.append(f"%{member_query}%")

            if date_from:
                where.append("p.payment_date >= %s")
                params.append(date_from)
            if date_to:
                where.append("p.payment_date <= %s")
                params.append(date_to)

            if status_filter in ("pending", "complete", "failed", "paid"):
                where.append("LOWER(p.status) = %s")
                params.append(status_filter)

            sql = """
                SELECT 
                    p.payment_id,
                    p.member_id,
                    CONCAT(m.first_name, ' ', m.last_name) AS member_name,
                    p.amount,
                    p.payment_date,
                    p.status,
                    p.type
                FROM Payments AS p
                JOIN Members AS m ON p.member_id = m.member_id
            """
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY p.payment_date DESC"

            cursor.execute(sql, tuple(params))
            search_results = cursor.fetchall()

        # Aggregate complete payments for last N days
        elif 'aggregate_over_n' in request.form:
            n_days_raw = request.form.get("n_days")
            try:
                n_days = int(n_days_raw)
            except (TypeError, ValueError):
                flash("Invalid number of days.")
                cursor.close()
                db.close()
                return redirect(request.referrer)

            cursor.execute("""
                SELECT SUM(amount) AS total
                FROM Payments
                WHERE LOWER(status) = 'complete'
                  AND payment_date >= (CURDATE() - INTERVAL %s DAY)
            """, (n_days,))
            row = cursor.fetchone()
            aggregate_total = row["total"] or 0.0

    cursor.close()
    db.close()

    return render_template(
        "/gymman_templates/owner_view/payments.html", 
        username=session["username"], 
        name=session["name"],
        pending_payments=pending_payments,
        search_results=search_results,
        aggregate_total=aggregate_total
    )

@auth.route("/owner/staff", methods=['GET', 'POST'])
def owner_staff():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))

    # Handle staff registration
    if request.method == 'POST' and 'register_staff' in request.form:
        ssn = request.form.get("ssn")
        fname = request.form.get("first_name")
        lname = request.form.get("last_name")
        emp_date = request.form.get("employment_date")  # yyyy-mm-dd
        birth_date = request.form.get("birth_date")     # yyyy-mm-dd
        address = request.form.get("address")

        staff_type = request.form.get("staff_type")  # hourly, salary, maintenance, manager, contractor

        hourly_rate = request.form.get("hourly_rate") or None
        annual_salary = request.form.get("annual_salary") or None
        contract_type = request.form.get("contract_type") or None
        contract_details = request.form.get("contract_details") or None
        shift_managed = request.form.get("shift_managed") or None

        # Basic validation
        if not all([ssn, fname, lname, emp_date, birth_date, address, staff_type]):
            flash("Missing required staff fields.")
            return redirect(request.referrer)

        try:
            if hourly_rate is not None:
                hourly_rate = float(hourly_rate)
            if annual_salary is not None:
                annual_salary = float(annual_salary)
        except ValueError:
            flash("Invalid pay values.")
            return redirect(request.referrer)

        staff_id = db_registerStaff(
            ssn, fname, lname, emp_date, birth_date, address,
            staff_type,
            hourly_rate=hourly_rate,
            annual_salary=annual_salary,
            contract_type=contract_type,
            contract_details=contract_details,
            shift_managed=shift_managed
        )
        flash(f"Staff member registered with ID {staff_id}.")
        return redirect(request.referrer)

    # Show staff listing
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT staff_id, first_name, last_name, employment_date, birth_date, staff_address
        FROM Staff
        ORDER BY last_name, first_name
    """)
    staff_list = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template(
        "/gymman_templates/owner_view/staff.html",
        username=session["username"],
        name=session["name"],
        staff_list=staff_list
    )

@auth.route("/owner/trainers", methods=['GET', 'POST'])
def owner_trainers():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))

    # Load all trainer-client relationships
    trainer_clients = db_showTrainerClientRel()
    search_term = None

    if request.method == 'POST':
        # Register a trainer from existing staff
        if 'register_trainer' in request.form:
            staff_id = request.form.get("staff_id")
            speciality = request.form.get("speciality")
            active_raw = request.form.get("active", "1")

            if not staff_id or not speciality:
                flash("Staff ID and speciality are required to register a trainer.")
                return redirect(request.referrer)

            try:
                active = int(active_raw)
            except ValueError:
                active = 1

            db_registerTrainer(staff_id, speciality, active=active)
            flash("Trainer registered.")
            return redirect(request.referrer)

        # Assign trainer to a member
        elif 'assign_trainer' in request.form:
            trainer_id = request.form.get("trainer_id")
            member_id = request.form.get("member_id")
            notes = request.form.get("notes")

            if not trainer_id or not member_id:
                flash("Trainer and member IDs are required to assign a trainer.")
                return redirect(request.referrer)

            db_assignTrainer(trainer_id, member_id, notes=notes)
            flash("Trainer assigned to member.")
            return redirect(request.referrer)

        # Filter trainer-client relationships
        elif 'search_relationships' in request.form:
            search_term = request.form.get("search_term", "").strip().lower()
            if search_term:
                filtered = []
                for rel in trainer_clients:
                    trainer_name = (rel.get("trainer") or "").lower()
                    client_name = (rel.get("client") or "").lower()
                    if search_term in trainer_name or search_term in client_name:
                        filtered.append(rel)
                trainer_clients = filtered

    # Also provide list of trainers and members for dropdowns
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT staff_id, CONCAT(first_name, ' ', last_name) AS staff_name
        FROM Staff
        ORDER BY staff_name
    """)
    all_staff = cursor.fetchall()

    all_trainers = db_getAllTrainers()

    cursor.execute("""
        SELECT member_id, CONCAT(first_name, ' ', last_name) AS member_name
        FROM Members
        ORDER BY member_name
    """)
    all_members = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "/gymman_templates/owner_view/trainers.html", 
        username=session["username"], 
        name=session["name"],
        trainer_clients=trainer_clients,
        all_trainers=all_trainers,
        all_members=all_members,
        all_staff=all_staff,
        search_term=search_term
    )

@auth.route("/owner/exercise_logs", methods=['GET', 'POST'])
def owner_exercise_logs(): # TODO: actually add the strenght / cardio tables
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))

    selected_member_id = None
    exercises = []

    if request.method == 'POST':
        # search / load exercises for a member
        if 'search_member' in request.form:
            selected_member_id = request.form.get("member_id")
            if selected_member_id:
                exercises = db_getExercise(selected_member_id)
            else:
                flash("Please choose a member to view exercises.")

        # log a new exercise
        elif 'log_exercise' in request.form:
            member_id = request.form.get("log_member_id")
            name = request.form.get("exercise_name")
            rpe_raw = request.form.get("rpe")
            date = request.form.get("exercise_date")  # yyyy-mm-dd

            if not all([member_id, name, rpe_raw, date]):
                flash("Member, exercise name, RPE, and date are required to log an exercise.")
                return redirect(request.referrer)

            try:
                rpe = int(rpe_raw)
            except ValueError:
                flash("RPE must be an integer.")
                return redirect(request.referrer)

            # not using strength/cardio extra tables for now
            db_logExercise(member_id, name, rpe, date)
            flash("Exercise logged.")
            selected_member_id = member_id
            exercises = db_getExercise(member_id)

        elif 'modify_exercise' in request.form:
            exercise_id = request.form.get("exercise_id")
            new_rpe = request.form.get("new_rpe")
            new_date = request.form.get("new_date")
            selected_member_id = request.form.get("member_id_for_refresh")

            if not exercise_id:
                flash("Exercise ID required to modify.")
                return redirect(request.referrer)

            rpe_val = None
            if new_rpe:
                try:
                    rpe_val = int(new_rpe)
                except ValueError:
                    flash("Invalid RPE value.")
                    return redirect(request.referrer)

            db_modifyExercise(exercise_id, rpe=rpe_val, date=new_date)
            flash("Exercise updated.")

            if selected_member_id:
                exercises = db_getExercise(selected_member_id)

        elif 'delete_exercise' in request.form:
            exercise_id = request.form.get("delete_exercise")
            selected_member_id = request.form.get("member_id_for_refresh")

            if not exercise_id:
                flash("Exercise ID required to delete.")
                return redirect(request.referrer)

            db_deleteExercise(exercise_id)
            flash("Exercise deleted.")

            if selected_member_id:
                exercises = db_getExercise(selected_member_id)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT member_id, CONCAT(first_name, ' ', last_name) AS member_name
        FROM Members
        ORDER BY member_name
    """)
    all_members = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template(
        "/gymman_templates/owner_view/exercise_logs.html",
        username=session["username"],
        name=session["name"],
        all_members=all_members,
        selected_member_id=selected_member_id,
        exercises=exercises
    )

@auth.route("/owner/error_logs")
def owner_errors():
    if not is_logged_in("Owner"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/owner_view/error_logs.html", username=session["username"], name=session["name"])

# +++++++++++++++++++++++++++++++++++
# =========== Staff Views ===========
# +++++++++++++++++++++++++++++++++++
@auth.route("/staff/dashboard", methods=['GET','POST'])
def staff_dashboard():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    
    # checkin member
    if request.method == 'POST':
        return checkin()

    return render_template("/gymman_templates/dashboard_staff.html", username=session["username"], name=session["name"])

@auth.route("/staff/checkins", methods=['GET','POST'])
def staff_checkins():
    if not is_logged_in("Staff"):
        return redirect(url_for("auth.login"))
    
    num_shown = session.get("num_checkins_shown", 15)

    if request.method == 'POST':
        # If "Load More" is pressed, increment by 5
        if 'load_more' in request.form:
            num_shown += 5
            session["num_checkins_shown"] = num_shown
        else:
            # If this POST was for a check-in action
            return checkin()

    # Fetch recent check-ins
    recent_checkins = db_showRecentCheckIns(num_shown)

    return render_template(
        "/gymman_templates/staff_view/checkins.html",
        username=session["username"],
        name=session["name"],
        recent_checkins=recent_checkins,
        num_shown=num_shown)

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

# +++++++++++++++++++++++++++++++++++++
# =========== Trainer Views ===========
# +++++++++++++++++++++++++++++++++++++
@auth.route("/trainer/dashboard")
def trainer_dashboard():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    return render_template("/gymman_templates/dashboard_trainer.html", username=session["username"], name=session["name"])

@auth.route("/trainer/clients")
def trainer_clients():
    if not is_logged_in("Trainer"):
        return redirect(url_for("auth.login"))
    name = session['name'].lower()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT tc.trainer_id FROM TrainerClients AS tc 
        JOIN Staff AS s ON tc.trainer_id = s.staff_id 
        WHERE CONCAT(s.first_name, ' ', s.last_name) LIKE %s
    """, (f"%{name}%",))
    row = cursor.fetchone()
    trainer_id = row["trainer_id"] if row else None
    trainer_clients = db_showTrainerClients(trainer_id)
    
    cursor.close()
    db.close()
    return render_template(
        "/gymman_templates/trainer_view/clients.html", 
        username=session["username"], 
        name=name, 
        trainer_clients=trainer_clients)

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

# ++++++++++++++++++++++++++++++++++++
# =========== Member Views ===========
# ++++++++++++++++++++++++++++++++++++
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

# --o-o- EOF