
import ast
import re
from os import path
from setuptools import setup, find_packages

base_dir = path.abspath(path.dirname(__file__))

with open(path.join(base_dir, "DESCRIPTION.md")) as f:
    long_description = f.read()

with file(path.join(base_dir, "ginger/__init__.py")) as f:
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
    url="https://github.com/vivsh/django-ginger",
    author="Vivek Sharma",
    author_email="vivek@17thstep.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4"
    ],
    keywords="django utilities",
    install_requires=[
        "django-jsonfield",
        "django-pods>=1.1",
        "django_jinja>=1.1",
        "django_nose>=1.3",
        "django>=1.7.4",
        "jinja2>=2.7.3",
        "mock",
    ],
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ginger_bootstrap_project = ginger.scripts.bootstrap:main"
        ]
    }
)
