# ======================================================================= #
#                           GYMMAN: QUERY MODELS                          #
#                          Author: Isaac Stephens                         #
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
#          Junior, Computer Science, CS Department, Missouri S&T          #
#              issq3r@mst.edu || isaac.stephens1529@gmail.com             #
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
# This file (models.py) contains the majority of the SQL query models for #
# auth.py, which was becoming increasingly hard to read with all the SQL  #
# in the routes.                                                          #
#                                                                         #
# A live web demo can be found @ https://isaacstephens.com/gymman-login.  #
# ======================================================================= #

from werkzeug.security import generate_password_hash
import mysql.connector
import os
from dotenv import load_dotenv

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

# find a member's information
# [only the row from the Member's table, for accompanying 
# inforation (ie. PhoneNumber, EmergencyContact, etc...)
# use db_memberLookup.] (owner/staff/trainer)
def db_findMember(member_search):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Try to find member by ID or name
    cursor.execute(
        """
        SELECT * FROM Members
        WHERE member_id = %s OR CONCAT(first_name, ' ', last_name) LIKE %s
        """,
        (member_search, f"%{member_search}%")
    )
    row = cursor.fetchone()
    cursor.close()
    return row

# log member in checkin table (owner/staff)
def db_logCheckin(member):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        INSERT INTO Checkins (member_id, checkin_datetime)
        VALUES (%s, NOW())
        """,
        (member["member_id"],)
    )
    db.commit()
    cursor.close()
    db.close()

# return total member count (owner/staff)
def db_getNumTotalMembers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM Members")
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["count"] if row and row["count"] is not None else 0

# return num pending payments (owner)
def db_getNumPendingPayments():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM Payments WHERE LOWER(status) = 'pending'")
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["count"] if row and row["count"] is not None else 0

# return num active trainers (owner/staff)
def db_getNumActiveTrainers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM Trainers WHERE active = 1")
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["count"] if row and row["count"] is not None else 0

# returns num_shown most recent checkins (owner/staff)
def db_showRecentCheckIns(num_shown=15):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = f"""
        SELECT 
            c.checkin_id,
            c.member_id,
            m.first_name,
            m.last_name,
            c.checkin_datetime
        FROM Checkins AS c
        JOIN Members AS m ON c.member_id = m.member_id
        ORDER BY c.checkin_id DESC
        LIMIT {int(num_shown)}
    """
    cursor.execute(query)
    checkins = cursor.fetchall()
    cursor.close()
    db.close()
    return checkins

# member lookup function (owner/staff/trainer)
def db_memberLookUp(member):
    db = get_db()
    cursor = db.cursor(dictionary=True)
  
    cursor.execute(""" 
        SELECT m.member_id, m.first_name, m.last_name, m.email, m.birth_date,
               m.membership_start_date, p.phone_number,
               CONCAT(e.first_name, ' ', e.last_name) AS emergency_contact_name,
               e.phone_number AS emergency_contact_phone
        FROM Members m
        LEFT JOIN PhoneNumbers p ON m.member_id = p.member_id
        LEFT JOIN EmergencyContacts e ON m.member_id = e.member_id
        WHERE m.member_id = %s OR m.first_name LIKE %s OR m.last_name LIKE %s 
                               OR CONCAT(m.first_name, ' ', m.last_name) LIKE %s 
                               OR CONCAT(m.last_name, ' ', m.first_name) LIKE %s
    """, (member, f"%{member}%", f"%{member}%", f"%{member}%", f"%{member}%"))
    lookup = cursor.fetchall()
    cursor.close()
    db.close()
    return lookup

# returns a table of all memberships (owner/staff)
def db_showAllMembers():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT m.member_id, CONCAT(m.first_name, ' ', m.last_name) AS name, 
               p.phone_number, m.email, m.birth_date, m.membership_start_date
        FROM Members m
        LEFT JOIN PhoneNumbers p ON m.member_id = p.member_id
    """)
    members = cursor.fetchall()
    cursor.close()
    db.close()
    return members

# returns a table of ALL trainer client relationships (owner)
def db_showTrainerClientRel():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            CONCAT(s.first_name, ' ', s.last_name) AS trainer,
            CONCAT(m.first_name, ' ', m.last_name) AS client,
            tc.notes, tc.client_start_date, tc.client_end_date
        FROM
            TrainerClients AS tc
            LEFT JOIN Staff AS s ON tc.trainer_id = s.staff_id
            LEFT JOIN Members AS m ON tc.member_id = m.member_id
    """)
    trainerClients = cursor.fetchall()
    cursor.close()
    db.close()
    return trainerClients

# returns a table of clients from a SPECIFIC trainer (trainer)
def db_showTrainerClients(trainerID):
    if trainerID is None:
        return []
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            CONCAT(m.first_name, ' ', m.last_name) AS client,
            tc.notes, tc.client_start_date, tc.client_end_date
        FROM
            TrainerClients AS tc
            LEFT JOIN Members AS m ON tc.member_id = m.member_id
        WHERE 
            tc.trainer_id = %s
    """, (trainerID))
    trainerClients = cursor.fetchall()
    cursor.close()
    db.close()
    return trainerClients

def db_getMemberPhone(memberID):
    if memberID is None:
        return []
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT phone_number_id, phone_number, phone_number_type
        FROM PhoneNumbers
        WHERE member_id = %s
    """,(memberID,))
    phoneNumbers = cursor.fetchall()

    cursor.close()
    db.close()
    return phoneNumbers

def db_getMemberEmergencyContacts(memberID):
    if memberID is None:
        return []
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT emergency_contact_id, CONCAT(first_name, ' ', last_name) AS name, email, phone_number, relationship
        FROM EmergencyContacts
        WHERE member_id = %s
    """, (memberID,))
    emergency_contacts = cursor.fetchall()
    cursor.close()
    db.close()
    return emergency_contacts


# add a new member and create their user (owner/staff)
def db_createMemberUser(fname, lname, bd, email, sex, username, pw):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        INSERT INTO Members(first_name, last_name, birth_date, membership_start_date, email, sex)
        VALUES (%s, %s, %s, CURDATE(), %s, %s)
    """, (fname, lname, bd, email, sex))
    member_id = cursor.lastrowid
    pw_hash = generate_password_hash(pw)
    cursor.execute("""
        INSERT INTO users (username, password_hash, role_id, first_name, last_name, email)
        VALUES (%s, %s, 3, %s, %s, %s)
    """,(username, pw_hash, fname, lname, email))
    user_id = cursor.lastrowid
    db.commit()
    cursor.close()
    db.close()
    return member_id, user_id

# update a member's information (owner/staff/member(self))
def db_updateMemberEmail(member_id, new_email):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT email FROM Members WHERE member_id = %s", (member_id,))
    row = cursor.fetchone()
    old_email = row['email']
    cursor.execute("""
        UPDATE users
        SET email = %s
        WHERE email = %s
    """,(new_email, old_email))
    db.commit()
    cursor.execute("""
        UPDATE Members
        SET email = %s
        WHERE member_id = %s
    """, (new_email, member_id))
    db.commit()
    cursor.close()
    db.close()

def db_addMemberPhone(member_id, phone_number, phone_type):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO PhoneNumbers (member_id, phone_number, phone_number_type)
        VALUES (%s, %s, %s)
    """, (member_id, phone_number, phone_type))

    db.commit()
    cursor.close()
    db.close()

def db_updateMemberPhone(member_id, phone_number_id, new_phone_number, new_type):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE PhoneNumbers
        SET phone_number = %s,
            phone_number_type = %s
        WHERE phone_number_id = %s AND member_id = %s
    """, (new_phone_number, new_type, phone_number_id, member_id))

    db.commit()
    cursor.close()
    db.close()

def db_deletePhoneNum(phoneID):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM PhoneNumbers WHERE phone_number_id = %s", (phoneID,))
    db.commit()
    cursor.close()
    db.close()

def db_addMemberEmergencyContact(member_id, fname, lname, relationship, phone, email):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO EmergencyContacts (member_id, first_name, last_name, relationship, phone_number, email)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (member_id, fname, lname, relationship, phone, email))

    db.commit()
    cursor.close()
    db.close()

def db_updateMemberEmergencyContact(member_id, ec_id, fname, lname, relationship, phone, email):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE EmergencyContacts
        SET first_name = %s,
            last_name = %s,
            relationship = %s,
            phone_number = %s,
            email = %s
        WHERE emergency_contact_id = %s AND member_id = %s
    """, (fname, lname, relationship, phone, email, ec_id, member_id))

    db.commit()
    cursor.close()
    db.close()

def db_deleteEmergencyContact(ecID):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM EmergencyContacts WHERE emergency_contact_id = %s", (ecID,))
    db.commit()
    cursor.close()
    db.close()

# delete a member (owner)
def db_deleteMember(member_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT email FROM Members WHERE member_id = %s", (member_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        db.close()
        return False
    email = row["email"]

    cursor.execute("DELETE FROM Checkins WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM PhoneNumbers WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM EmergencyContacts WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM Payments WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM TrainerClients WHERE member_id = %s OR trainer_id = %s", (member_id, member_id))

    cursor.execute("DELETE FROM users WHERE email = %s", (email,))
    cursor.execute("DELETE FROM Members WHERE member_id = %s", (member_id,))

    db.commit()
    cursor.close()
    db.close()
    return True

# add a payment for a member (owner/staff/member)
def db_addPayment(member_id, amount, status="pending", payment_type="membership"):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Payments (member_id, amount, payment_date, status, type)
        VALUES (%s, %s, CURDATE(), %s, %s)
    """, (member_id, amount, status, payment_type))

    db.commit()
    cursor.close()
    db.close()

# register staff / trainer (owner)
def db_registerStaff(ssn, fname, lname, emp_date, birth_date, address,
                     staff_type, hourly_rate=None, annual_salary=None,
                     contract_type=None, contract_details=None,
                     shift_managed=None):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Staff (ssn, first_name, last_name, employment_date, birth_date, staff_address)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (ssn, fname, lname, emp_date, birth_date, address))

    staff_id = cursor.lastrowid

    if staff_type == "hourly":
        cursor.execute("INSERT INTO Hourly_Employees VALUES (%s, %s)",
                       (staff_id, hourly_rate))
    elif staff_type == "salary":
        cursor.execute("INSERT INTO Salary_Employees VALUES (%s, %s)",
                       (staff_id, annual_salary))
    elif staff_type == "maintenance":
        cursor.execute("INSERT INTO Maintainence VALUES (%s)", (staff_id,))
    elif staff_type == "manager":
        cursor.execute("INSERT INTO Managers VALUES (%s, %s)",
                       (staff_id, shift_managed))
    elif staff_type == "contractor":
        cursor.execute("INSERT INTO Contractors VALUES (%s, %s, %s)",
                       (staff_id, contract_type, contract_details))

    db.commit()
    cursor.close()
    db.close()
    return staff_id

def db_registerTrainer(staff_id, speciality, active=1):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Trainers (staff_id, speciality, active)
        VALUES (%s, %s, %s)
    """, (staff_id, speciality, active))

    db.commit()
    cursor.close()
    db.close()

def db_getAllTrainers():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.staff_id, t.speciality, t.active,
               CONCAT(s.first_name, ' ', s.last_name) AS trainer_name
        FROM Trainers t
        JOIN Staff s ON t.staff_id = s.staff_id
        ORDER BY trainer_name
    """)
    all_trainers = cursor.fetchall()

    cursor.close()
    db.close()
    return all_trainers

# assign trainer to a member (owner/staff/trainer)
def db_assignTrainer(trainer_id, member_id, notes=None):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO TrainerClients (trainer_id, member_id, client_start_date, notes)
        VALUES (%s, %s, CURDATE(), %s)
        ON DUPLICATE KEY UPDATE
            client_end_date = NULL,
            notes = VALUES(notes)
    """, (trainer_id, member_id, notes))

    db.commit()
    cursor.close()
    db.close()

# log an exercise for a member (owner/trainer/member)
def db_logExercise(member_id, name, rpe, date,
                   strength_data=None, cardio_data=None):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Exercises (member_id, exercise_name, rpe, exercise_date)
        VALUES (%s, %s, %s, %s)
    """, (member_id, name, rpe, date))

    exercise_id = cursor.lastrowid

    if strength_data:
        cursor.execute("""
            INSERT INTO Strength_Exercises
            (exercise_id, strength_id, exercise_weight, weight_unit,
             num_sets, num_repetitions, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (exercise_id, *strength_data))

    if cardio_data:
        cursor.execute("""
            INSERT INTO Cardio_Exercises
            (exercise_id, avg_hr, time_taken)
            VALUES (%s, %s, %s)
        """, (exercise_id, *cardio_data))

    db.commit()
    cursor.close()
    db.close()

# modify an exercise record (owner/trainer/member)
def db_modifyExercise(exercise_id, rpe=None, date=None):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE Exercises
        SET rpe = COALESCE(%s, rpe),
            exercise_date = COALESCE(%s, exercise_date)
        WHERE exercise_id = %s
    """, (rpe, date, exercise_id))

    db.commit()
    cursor.close()
    db.close()

# delete an exercise (owner/trainer/member)
def db_deleteExercise(exercise_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM Exercises WHERE exercise_id = %s", (exercise_id,))

    db.commit()
    cursor.close()
    db.close()

# get exercises for a specific member (owner/trainer/member)
def db_getExercise(member_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM Exercises
        WHERE member_id = %s
        ORDER BY exercise_date DESC
    """, (member_id,))

    exercises = cursor.fetchall()
    cursor.close()
    db.close()
    return exercises

# aggregate total payments / revenue (owner/staff/member)
def db_aggregatePayments(member=False, member_id=None):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if member == False:
        cursor.execute("""
            SELECT SUM(amount) AS total_revenue
            FROM Payments
            WHERE LOWER(status) = 'Complete' OR LOWER(status) = 'Paid'
        """)
    else:
        cursor.execute("""
            SELECT SUM(amount) AS total_revenue
            FROM Payments
            WHERE LOWER(status) = 'completed'
            AND member_id = %s
        """, (member_id))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["total_revenue"] or 0

# aggregate average RPE (owner/trainer/member)
def db_aggregateRPE(member_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT AVG(rpe) AS avg_rpe
        FROM Exercises
        WHERE member_id = %s
    """, (member_id,))

    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["avg_rpe"] or 0

# aggregate max weight lifted by a member (owner/traiiner/member)
def db_aggregateMaxWeight(member_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT MAX(exercise_weight) AS max_weight
        FROM Strength_Exercises se
        JOIN Exercises e ON se.exercise_id = e.exercise_id
        WHERE e.member_id = %s
    """, (member_id,))

    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["max_weight"] or 0

# load pending payments
def db_loadPendingPayments():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
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
        WHERE LOWER(p.status) = 'pending'
        ORDER BY p.payment_date DESC
    """)
    pending_payments = cursor.fetchall()
    cursor.close()
    db.close()
    return pending_payments

# aggregate average run distance (owner/trainer/member)
def db_aggregateAvgRunDist(member_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT AVG(r.distance) AS avg_distance
        FROM Runs r
        JOIN Cardio_Exercises c ON r.cardio_id = c.cardio_id
        JOIN Exercises e ON c.exercise_id = e.exercise_id
        WHERE e.member_id = %s
    """, (member_id,))

    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["avg_distance"] or 0

# get error logs (owner/staff)
# TODO: set up error logging 
def db_getErrorLog():
    return
