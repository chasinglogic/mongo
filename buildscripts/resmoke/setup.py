"""Test runner for MongoDB JS, unit, and integration tests."""

from setuptools import find_packages, setup

with open('requirements.txt') as req_txt:
    requirements = req_txt.read()

setup(
    name='resmoke',
    version='1.0.0',
    url='https://github.com/mongodb/mongo',
    license='SSPLv2',
    author='MongoDB Inc.',
    description=__doc__,
    packages=find_packages(),
    platforms='any',
    install_requires=requirements.splitlines(),
    entry_points={
        'console_scripts': [
            'resmoke = resmokelib.cli:main',
        ],
    },
)
