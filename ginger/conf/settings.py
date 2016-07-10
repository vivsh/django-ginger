
from . import env

__all__ = ['STATIC_URL',
           'MEDIA_URL',
            'CELERY_ALWAYS_EAGER',
            'CELERY_EAGER_PROPAGATES_EXCEPTIONS',
            'env',
            'MESSAGE_TAGS',
            'JINJA2_EXCLUDED_FOLDERS',
            'JINJA2_AUTOESCAPE',
            'STAGING_SECRET',
            'TEMPLATES',
            'template_settings',
            'GINGER_TEMPLATE_CONTEXT_PROCESSORS'
]


STATIC_URL = '/static/'

MEDIA_URL = '/media/'

JINJA2_EXCLUDED_FOLDERS = ["sitemaps", "admin", "debug_toolbar", "suit", 'rest_framework', 'rest_framework_swagger']

JINJA2_AUTOESCAPE = False

# TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

#Celery config
CELERY_ALWAYS_EAGER = True

CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

STAGING_SECRET = "curry-rice"

from django.contrib.messages import constants
MESSAGE_TAGS = {
    constants.ERROR: "danger"
}


GINGER_TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'django.template.context_processors.request'
)


def template_settings(dirs=(), debug=False, context_processors=GINGER_TEMPLATE_CONTEXT_PROCESSORS):
    return [
        {
            "BACKEND": "ginger.template.backend.Jinja2",
            "APP_DIRS": True,
            "DIRS": dirs,
            "NAME": "GINGER",
            "OPTIONS": {
            "context_processors": context_processors,
                "newstyle_gettext": True,
                "autoescape": False,
                "auto_reload": debug,
                # "translation_engine": "django.utils.translation",
            }
        },
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": dirs,
            "APP_DIRS": True,
            'OPTIONS':{
                'context_processors': context_processors,
            }
        },
    ]


TEMPLATES = template_settings()
