from setuptools import setup

setup(
    name='apitree',
    version='0.3.3',
    author='Josh Matthias',
    author_email='python.apitree@gmail.com',
    packages=['apitree'],
    scripts=[],
    include_package_data=True,
    url='https://github.com/jmatthias/apitree',
    license='LICENSE.txt',
    description=('Build an orderly web service API backend.'),
    long_description=open('README_pypi.txt').read(),
    install_requires=[
        'iomanager>=0.4.0',
        'mako',
        'pyramid>=1.3.4',
        ],
    )