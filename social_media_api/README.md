Social Media API 🚀

A Django REST Framework (DRF) Social Media API built with Python and Django.

🌐 Live API

Production:
https://alx-djangolearnlab-1-d0qo.onrender.com

Source Code:
https://github.com/otieno-backend/Alx_DjangoLearnLab/tree/main/social_media_api

✨ Features
User registration & Token Authentication
Custom user profiles
Follow / unfollow users
Followers & following
Create, update & delete posts
Comments
Post search & pagination
User permissions
Django Admin
CORS support
Production deployment with Render
🛠️ Tech Stack

Python · Django 4.2 · Django REST Framework · Token Authentication · SQLite/PostgreSQL · WhiteNoise · Render

🚀 Quick Start
Use the Live API

Use the API with Postman, Insomnia, cURL, or a frontend application.

https://alx-djangolearnlab-1-d0qo.onrender.com


For protected endpoints:

Authorization: Token YOUR_TOKEN

Run Locally
git clone https://github.com/otieno-backend/Alx_DjangoLearnLab.git
cd Alx_DjangoLearnLab/social_media_api

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver


Local API:

http://127.0.0.1:8000/

## Tests
The project includes automated tests using Django's test framework and Django REST Framework's APITestCase.

### Tests cover:

User authentication and permissions

Post creation, updating and deletion

Comment creation and validation

Automatic comment author assignment

Comment filtering by post

Notification creation

Preventing users from receiving notifications for their own actions

Notification listing

Unread notification count

Marking notifications as read

Preventing users from modifying other users' notifications

Follower notifications when a new post is created

Handling invalid posts in notification tasks

### Run All Tests
From the social_media_api directory:

python manage.py test

🔎 Keywords

Django Django REST Framework DRF Python REST API Social Media API Backend Authentication Token Authentication User Profiles Posts API Comments API Followers Following Search API Pagination CORS PostgreSQL SQLite Render Django Backend

👨‍💻 Author

otieno-backend

Built with Django & Django REST Framework ❤️
