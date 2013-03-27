from setuptools import setup

setup(
    name='pyramid_apitree',
    version='0.0.1',
    author='Josh Matthias',
    author_email='pyramid.apitree@gmail.com',
    packages=['pyramid_apitree'],
    scripts=[],
    url='https://github.com/jmatthias/pyramid_apitree',
    license='LICENSE.txt',
    description=('Make an orderly API from Pyramid views.'),
    long_description=open('README.txt').read(),
    install_requires=[
        'ioprocess',
        ],
    )