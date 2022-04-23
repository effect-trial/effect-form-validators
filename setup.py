# -*- coding: utf-8 -*-
import os
from os.path import abspath, dirname, join, normpath

from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(normpath(join(abspath(__file__), os.pardir)))

with open(join(dirname(__file__), "README.rst")) as f:
    README = f.read()

# with open(join(dirname(__file__), "VERSION")) as f:
#     VERSION = f.read()


setup(
    name="effect-form-validators",
    # version=VERSION,
    author="Erik van Widenfelt",
    author_email="ew2789@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/clinicedc/effect-form-validators",
    license="GPL license, see LICENSE",
    description="Classes for effect model forms validation",
    long_description=README,
    long_description_content_type="text/x-rst",
    zip_safe=False,
    keywords="django edc vitals",
    install_requires=[],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.9",
)
