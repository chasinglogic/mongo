"""MongoDB buildscripts and their utility packages."""

from setuptools import find_packages, setup

setup(
    name='buildscripts',
    version='0.1.0',
    url='https://github.com/mongodb/mongo',
    license='SSPLv2',
    author='MongoDB Inc.',
    description=__doc__,
    packages=find_packages(),
    platforms='any',
    entry_points={},
)
