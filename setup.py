
from os import path
from setuptools import setup, find_packages

base_dir = path.abspath(path.dirname(__file__))

with open(path.join(base_dir, "DESCRIPTION.md")) as f:
    long_description = f.read()

setup(
    name="django_ginger",
    description="Set of django utilities",
    long_description=long_description,
    version="0.3.6",
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
        "django>=1.7",
        "jinja2",
        "django_jinja>=1",
        "pillow",
        "django_nose",
        "mock",
    ],
    packages=[
        "ginger",
    ],
)
