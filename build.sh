#!/usr/bin/env bash

set -o errexit # exit on error

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate


# Safely create superuser
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.getenv("admin")
email = os.getenv("admin@gmail.com")
password = os.getenv("admin123abc")
if username and email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print("Superuser created.")
    else:
        print("Superuser already exists.")
EOF