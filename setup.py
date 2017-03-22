"""Setup script for packaging pystatsmpg
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


setup(
    name='pystatsmpg',
    version='0.0.0',
    description='A Python library to read football stats',
    long_description="",
    url='https://github.com/cpind/mystatsmpg',
    # Author details
    author='cpind',
    author_email='cyprien.pindat@gmail.com',
    # Choose your license
    license='MIT',
    keywords='openpyxl stats football',
    packages=['pystatsmpg'],
)
