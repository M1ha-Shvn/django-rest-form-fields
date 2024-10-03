"""
This file contains django settings to run tests with runtests.py
"""

SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    "src",
    "tests",
]

DATABASES = {}

USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'