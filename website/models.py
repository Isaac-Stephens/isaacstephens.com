# --------------------------------------------
# Database models for gymman web demo. auth.py
# was getting wayyyy too long lol
# --------------------------------------------

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

# find member for checkin
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
    return cursor.fetchone()

# log member in checkin table
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

# return total member count
def db_getNumTotalMembers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM Members")
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["count"] if row and row["count"] is not None else 0

# return num pending payments
def db_getNumPendingPayments():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM Payments WHERE LOWER(status) = 'pending'")
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["count"] if row and row["count"] is not None else 0

# return num active trainers
def db_getNumActiveTrainers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM Trainers WHERE active = 1")
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row["count"] if row and row["count"] is not None else 0

# returns num_shown most recent checkins 
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
        ORDER BY c.checkin_datetime DESC
        LIMIT {int(num_shown)}
    """
    cursor.execute(query)
    checkins = cursor.fetchall()
    cursor.close()
    db.close()
    return checkins

#
