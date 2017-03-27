#!/usr/bin/env python

try:
    from setuptools import setup
    test_extras = {
        'test_suite': 'pythonosc.test',
    }
except ImportError:
    from distutils.core import setup
    test_extras = {}


setup(
    name='python-osc',
    version='1.6.3',
    author='attwad',
    author_email='tmusoft@gmail.com',
    description=(
        'Open Sound Control server and client implementations in pure Python'),
    long_description=open('README.rst').read(),
    url='https://github.com/attwad/python-osc',
    platforms='any',
    packages=[
        'pythonosc',
        'pythonosc.parsing',
        'pythonosc.test',
        'pythonosc.test.parsing',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: System :: Networking',
    ],
    **test_extras
)
