#!/bin/bash
sudo apt update
sudo apt install python3-flask python3-flask-login python3-flask-sqlalchemy python3-mysql.connector python3-werkzeug python3-dotenv

# For a .venv environment uncomment bellow
# python3 -m venv venv
# source venv/bin/activate
# pip install gunicorn flask mysql-connector-python python-dotenv
# gunicorn --bind 127.0.0.1:5000 main:app
