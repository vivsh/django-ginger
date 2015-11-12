#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os


def run_tests(**options):
    import django
    import sys
    from django.conf import settings
    from ginger.conf.settings import template_settings

    defaults = dict(
        MIDDLEWARE_CLASSES=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        TEMPLATE_DEBUG = True,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        TEMPLATES = template_settings(dirs=[os.path.join(os.path.dirname(__file__), 'test_templates'),])
    )
    defaults.update(options)
    settings.configure(**defaults)
    django.setup()

    # Run the test suite, including the extra validation tests.
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)

    test_runner = TestRunner(verbosity=1, interactive=False, failfast=False)
    failures = test_runner.run_tests(sys.argv[1:] or settings.INSTALLED_APPS)
    return failures


urlpatterns = []

ROOT_URLCONF = 'runtests'

INSTALLED_APPS = [
    # 'django_nose',
    'ginger',
    'ginger.contrib.staging',
]


def main():
    failures = run_tests(
        INSTALLED_APPS=INSTALLED_APPS,
        ROOT_URLCONF=ROOT_URLCONF,
        # TEST_RUNNER='django_nose.NoseTestSuiteRunner'
    )
    sys.exit(failures)


if __name__ == "__main__":
    main()