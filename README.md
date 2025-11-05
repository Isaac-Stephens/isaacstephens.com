# isaacstephens.com

Personal website and web demo platorm for me, **Isaac Stephens**.

This repo contains the **Flask** backend and content that's served by **Nginx** on my personal home server.

## Project Structure:
```
isaacstephens.com/
│
├── main.py # Flask entry point
├── website/ # Flask app package
│ ├── init.py # App factory
│ ├── auth.py # Authentication routes
│ ├── views.py # General views
│ ├── models.py # Database models
│ ├── templates/ # HTML templates
│ └── static/ # CSS, JS, images, and documents
│ 
├── dependencies.sh # Setup dependencies on a new server
├── LICENSE
└── README.md
```

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

## License:

This project is licensed under the MIT License.

## Author:
**Isaac Stephens**

Junior, Computer Science, Missouri University of Science & Technology

isaac.stephens1529@gmail.com