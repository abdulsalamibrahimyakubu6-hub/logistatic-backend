#!/usr/bin/env bash

set -o errexit # exit on error

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate


# Safely change user password
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.getenv("DJANGO_ADMIN_USERNAME", "admin")
new_password = os.getenv("DJANGO_ADMIN_PASSWORD", "admin123abc")

try:
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.save()
    print(f"Password updated successfully for user: {username}")
except User.DoesNotExist:
    print(f"User '{username}' does not exist. No password was changed.")
EOF
