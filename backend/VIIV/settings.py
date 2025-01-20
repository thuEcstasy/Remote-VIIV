"""
Django settings for VIIV project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 这意味着如果你上传了一个名为example.jpg的文件到avatars子文件夹下，那么这个文件将可以通过http://yourdomain.com/media/avatars/example.jpg访问。


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-xvv16d@^4vu6-_^8w73_wt+xqf-wfppqevn)_zgye!#7l^6=p$'

# SECURITY WARNING: don't run with debug turned on in production!
# Disable debug mode in production
DEBUG = not os.getenv("DEPLOY")

#AUTH_USER_MODEL = 'author.User'


ALLOWED_HOSTS = [
    '*'  # Insecure
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520
# Application definition

INSTALLED_APPS = [
    'group',
    'daphne',
    'communication',
    'author',
    'friends',
    'main',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders', # enable CORS
    'channels', # enable channels
]

CORS_ALLOW_ALL_ORIGINS = True
# channel settings
ASGI_APPLICATION = 'VIIV.asgi.application'

# settings.py

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# 邮件发送的设置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'infiniteqgl@gmail.com'
EMAIL_HOST_PASSWORD = 'uspj ubbi asfj mtyw'
EMAIL_USE_SSL = False

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 必须放在最前面
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Remove CSRF middleware for teaching purpose, although insecure :(
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.token_middleware.RefreshTokenMiddleware',
    'middleware.reset_status_middleware.ResetUserStatusMiddleware'
]

ROOT_URLCONF = 'VIIV.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'VIIV.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

BASE_DIR = Path(__file__).resolve().parent.parent

# DATABASES={
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': '7encent',
#         'USER': 'root',
#         'PASSWORD': 'kyrie0925',
#         'HOST': '127.0.0.1',  # 通常是'localhost'或者是数据库服务器的IP 地址
#         'PORT': '3306',  # MySQL的默认端口是3306
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',  # 替换为你创建的数据库名
        'USER': 'your_user',          # 替换为你设置的 MySQL 用户名
        'PASSWORD': 'your_password',  # 替换为对应的密码
        'HOST': '127.0.0.1',          # WSL 中通常使用本地地址
        'PORT': '3306',               # MySQL 默认端口
        'OPTIONS': {
            'charset': 'utf8mb4',     # 推荐使用 utf8mb4 字符集
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

APPEND_SLASH = False