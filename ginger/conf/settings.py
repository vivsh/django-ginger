
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS, TEMPLATE_LOADERS
from . import env

__all__ = ['STATIC_URL',
           'MEDIA_URL',
           'TEMPLATE_CONTEXT_PROCESSORS',
           # 'TEMPLATE_LOADERS',
           'TEST_RUNNER',
            'CELERY_ALWAYS_EAGER',
            'CELERY_EAGER_PROPAGATES_EXCEPTIONS',
            'env',
            'MESSAGE_TAGS',
            'JINJA2_EXCLUDED_FOLDERS',
            'JINJA2_AUTOESCAPE',
            'STAGING_SECRET',
            'TEMPLATES'
]


STATIC_URL = '/static/'

MEDIA_URL = '/media/'


TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)

JINJA2_EXCLUDED_FOLDERS = ["admin", "debug_toolbar", "suit"]

JINJA2_AUTOESCAPE = False

# TEMPLATE_LOADERS = (
#     'ginger.templates.FileSystemLoader',
#     'ginger.templates.AppLoader',
# ) + TEMPLATE_LOADERS

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

#Celery config
CELERY_ALWAYS_EAGER = True

CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

STAGING_SECRET = "curry-rice"

from django.contrib.messages import constants
MESSAGE_TAGS = {
    constants.ERROR: "danger"
}

TEMPLATES = [
    {
        "BACKEND": "ginger.template.backend.Jinja2",
        "APP_DIRS": True,
        "DIRS": [],
        "NAME": "GINGER",
        "OPTIONS": {
        "context_processors": [
            "django.contrib.auth.context_processors.auth",
            "django.template.context_processors.debug",
            "django.template.context_processors.i18n",
            "django.template.context_processors.media",
            "django.template.context_processors.static",
            "django.template.context_processors.tz",
            "django.contrib.messages.context_processors.messages",
            'django.core.context_processors.request'
        ],
            "newstyle_gettext": True,
            "autoescape": False,
            "auto_reload": False,
            # "translation_engine": "django.utils.translation",
        }
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        'OPTIONS':{
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.request'
            ],
        }
    },
]
