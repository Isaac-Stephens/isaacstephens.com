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
    trainerClients = cursor.fetchall
    cursor.close()
    db.close()
    return trainerClients

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
def db_updateMember(member_id):
    return

# delete a member (owner)
def db_deleteMember(member_id):
    return

# add a payment for a member (owner/staff/member)
def db_addPayment(member_id):
    return

# register staff / trainer (owner)

# assign trainer to a member (owner/staff/trainer)

# log an exercise for a member (owner/trainer/member)

# modify an exercise record (owner/trainer/member)

# delete an exercise (owner/trainer/member)

# get exercises for a specific member (owner/trainer/member)

# aggregate total payments / revenue (owner/staff/member)

# aggregate average RPE (owner/trainer/member)

# aggregate max weigh lifted by a member (owner/traiiner/member)

# aggregate average run distance (owner/trainer/member)

# get error logs (owner/staff)
