
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS, TEMPLATE_LOADERS
from . import env

__all__ = ['STATIC_URL',
           'TEMPLATE_CONTEXT_PROCESSORS',
           'TEMPLATE_LOADERS',
           'TEST_RUNNER',
            'CELERY_ALWAYS_EAGER',
            'CELERY_EAGER_PROPAGATES_EXCEPTIONS', 'env']


STATIC_URL = '/static/'


TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)

JINJA2_EXCLUDE_FOLDERS = ["admin", "debug_toolbar", "suit"]

JINJA2_AUTOESCAPE = False

TEMPLATE_LOADERS = (
    'ginger.templates.FileSystemLoader',
    'ginger.templates.AppLoader',
) + TEMPLATE_LOADERS

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

#Celery config
CELERY_ALWAYS_EAGER = True

CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

STAGING_SECRET = "curry-rice"

from django.contrib.messages import constants
MESSAGE_TAGS = {
    constants.ERROR: "danger"
}