from setuptools import setup

setup(
    name='pyramid_apitree',
    version='0.1.0a',
    author='Josh Matthias',
    author_email='pyramid.apitree@gmail.com',
    packages=['pyramid_apitree'],
    scripts=[],
    url='https://github.com/jmatthias/pyramid_apitree',
    license='LICENSE.txt',
    description=('Unstable beta release.'),
    long_description=open('README.md').read(),
    install_requires=[
        'iomanager>=0.3.4',
        'mako',
        'pyramid>=1.3.4',
        ],
    )