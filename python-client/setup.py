#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import re
import os
import sys


def get_version():
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    module = open('docjson.py').read()
    return re.search("version = ['\"]([^'\"]+)['\"]", module).group(1)


version = get_version()


if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()


setup(
    name='docjson',
    version=version,
    url='http://docjson.org',
    license='BSD',
    description='Simple, flexible JSON hypermedia documents.',
    author='Tom Christie',
    author_email='tom@tomchristie.com',
    py_modules=['docjson'],
    install_requires=['requests'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
