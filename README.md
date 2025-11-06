# isaacstephens.com

Personal website and web demo platorm for me, **Isaac Stephens**.

This repo contains the **Flask** backend and content that's served by **Nginx** on my personal home server.

## Project Structure:

```
/isaacstephens.com/
├── dependencies.sh
├── LICENSE
├── main.py
├── README.md
├── venv/
├── website/
│   ├── auth.py
│   ├── db.env (contains DB credentials, NOT committed lol)
│   ├── __init__.py
│   ├── models.py
│   ├── passwords.env (contains secrets, NOT committed lol)
│   ├── static/
│   └── templates/
└── other project files
```

Python / Virtual Environment:
-----------------------------
### Python Interpreter:
../isaacstephens.com/venv/bin/python

Python Version: 3.13.5

### Installed Packages (pip list):
- blinker 1.9.0
- click 8.3.0
- Flask 3.1.2
- gunicorn 23.0.0
- itsdangerous 2.2.0
- Jinja2 3.1.6
- MarkupSafe 3.0.3
- mysql-connector-python 9.5.0
- packaging 25.0
- pip 25.1.1
- python-dotenv 1.2.1
- Werkzeug 3.1.3

## Cloudflare Tunnel:

This site is accessed through a Cloudflare Tunnel pointing to my home server. The tunnel automatically routes traffic from https://isaacstephens.com → Nginx → Gunicorn → Flask.

## Tech Stack:

| Component         	| Description                          	|
|-------------------	|--------------------------------------	|
| Flask             	| Python web framework                 	|
| Gunicorn          	| WSGI HTTP server for production      	|
| Nginx             	| Reverse proxy + static file handler  	|
| MariaDB           	| Backend Database                     	|
| Cloudflare Tunnel 	| Secure remote access to local server 	|

## Notes:

- Static files served via `/static/` in Nginx for performance.
- Gunicorn runs the Flask app locally, proxied by Nginx, exposed via Cloudflare Tunnel.

## License:

This project is licensed under the MIT License.

## Author:
**Isaac Stephens**

Junior, Computer Science, Missouri University of Science & Technology

isaac.stephens1529@gmail.com