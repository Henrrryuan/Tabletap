import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

DEBUG = True

ALLOWED_HOSTS = [
    "infs3202-183b16dd.uqcloud.net",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

# Support for running under a subpath
FORCE_SCRIPT_NAME = '/tabletap'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'core.apps.CoreConfig',
    
    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = 'menu_welcome'
ACCOUNT_LOGOUT_REDIRECT_URL = 'index'
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': ['user', 'user:email'],
        'APP': {
            'client_id': 'Ov23liaJKxjj5cgIptBA',
            'secret': '28777bdd050b282907ce8a9efd70bb834beb2d4a',
            'key': ''
        }
    }
}

ROOT_URLCONF = 'tabletap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # 移除额外的模板目录，只使用应用内的模板
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# allauth template overrides
ACCOUNT_TEMPLATE_EXTENSION = 'html'
ACCOUNT_LOGIN_TEMPLATE = 'core/login.html'

WSGI_APPLICATION = 'tabletap.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Security Settings
CSRF_TRUSTED_ORIGINS = [
    "https://infs3202-183b16dd.uqcloud.net",
    "http://infs3202-183b16dd.uqcloud.net",
    "http://localhost:8001",
    "http://127.0.0.1:8001"
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Australia/Brisbane'
USE_I18N = True
USE_TZ = True

# Session Settings
SESSION_COOKIE_SECURE = False  # 本地开发设置为 False
CSRF_COOKIE_SECURE = False    # 本地开发设置为 False
SESSION_COOKIE_DOMAIN = None  # 本地开发设置为 None
CSRF_COOKIE_DOMAIN = None    # 本地开发设置为 None
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_LOGOUT_ON_GET = True

# Additional django-allauth settings
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
