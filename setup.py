#!/usr/bin/env python
import setuptools

setuptools.setup(
    name='spacetraders-py',
    version='0.0.1',
    description='Python Client for Spacetraders',
    author='jath03',
    url='https://www.python.org/sigs/distutils-sig/',
    packages=setuptools.find_packages(),
    python_requires='>=3.11',
    install_requires=['urllib3', "xdg-base-dirs"]
)
