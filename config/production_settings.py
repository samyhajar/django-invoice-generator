"""
Production settings for Railway deployment.
Import this in settings.py when deploying to production.
"""
import os
from decouple import config, Csv

# Security settings
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

# Database - Railway PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PGDATABASE', default=''),
        'USER': config('PGUSER', default=''),
        'PASSWORD': config('PGPASSWORD', default=''),
        'HOST': config('PGHOST', default=''),
        'PORT': config('PGPORT', default=5432, cast=int),
    }
}

# Static files with WhiteNoise
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
