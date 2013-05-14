from setuptools import setup

setup(
    name='pyramid_apitree',
    version='0.3.1',
    author='Josh Matthias',
    author_email='pyramid.apitree@gmail.com',
    packages=['pyramid_apitree'],
    scripts=[],
    include_package_data=True,
    url='https://github.com/jmatthias/pyramid_apitree',
    license='LICENSE.txt',
    description=('Build an orderly web service API from Pyramid views.'),
    long_description=open('README_pypi.txt').read(),
    install_requires=[
        'iomanager>=0.4.0',
        'mako',
        'pyramid>=1.3.4',
        ],
    )