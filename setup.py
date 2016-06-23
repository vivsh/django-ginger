
import ast
import re
from os import path
from setuptools import setup, find_packages

base_dir = path.abspath(path.dirname(__file__))

with open(path.join(base_dir, "DESCRIPTION.md")) as f:
    long_description = f.read()

with open(path.join(base_dir, "ginger/__init__.py")) as f:
    for line in f:
        matches = re.findall(r'^__version__\s*=\s*(.+)$', line)
        if matches:
            version = ast.literal_eval(matches[0])
            break

setup(
    name="django_ginger",
    description="Set of django utilities",
    long_description=long_description,
    version=version,
    # url="https://github.com/vivsh/django-ginger",
    license="BSD",
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    keywords="django utilities",
    install_requires=[
        "django-jsonfield",
        "django-imagekit",
        "python-dateutil",
        "webtest",
        "django-webtest",
        "jinja2>=2.7.3",
        "mock>=1.0.1",
        "django>=1.9.2",
        'pillow',
        "geopy",
        'bleach',
        "pytz"
    ],
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ginger_bootstrap_project = ginger.scripts.bootstrap:main"
        ]
    }
)
