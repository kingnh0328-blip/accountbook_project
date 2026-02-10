from pathlib import Path
import os
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv()


SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = ["accountbook-project.fly.dev", "localhost", "127.0.0.1"]
BASE_DIR = Path(__file__).resolve().parent.parent
# DEBUG = os.getenv('DEBUG', 'False') == 'True'
DEBUG = False


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'django.contrib.humanize', #숫자에,찍어주는app (예시 1,000원)
    
    # 앱
    'accounts',
    'transactions',
    'dashboard',
    'report',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'accountbook_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'accountbook_project.wsgi.application'


# DATABASES = {
# "default": {
# "ENGINE":"django.db.backends.postgresql",
# "NAME": os.getenv("DB_NAME"),
# "USER": os.getenv("DB_USER"),
# "PASSWORD": os.getenv("DB_PASSWORD"),
# "HOST": os.getenv("DB_HOST"),
# "PORT": os.getenv("DB_PORT"),
#     }
# }

# Fly.io의 DATABASE_URL 환경변수를 자동으로 읽어온다냐!
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}





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


LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_URL = '/login/'

CSRF_TRUSTED_ORIGINS = ["https://accountbook-project.fly.dev",
                        "https://*.fly.dev",  # 아예 fly.dev로 끝나는 모든 주소를 허용한다냐!
                        ]