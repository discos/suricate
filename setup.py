from __future__ import print_function

import os
from shutil import copyfile
from setuptools import setup, find_packages
from setuptools.command.install import install

from suricate.paths import (
    suricate_dir,
    config_dir,
    log_dir,
    template_dir,
    database_dir,
)

directories = (
    suricate_dir,
    config_dir,
    log_dir,
    template_dir,
    database_dir,
)

for d in directories:
    try:
        os.mkdir(d)
        print('Directory %s created' % d)
    except OSError, ex:
        pass # Directory already exists


for file_name in os.listdir('templates'):
    source_file = os.path.join('templates', file_name)
    dest_file = os.path.join(template_dir, file_name)
    copyfile(source_file, dest_file)


setup(
    name='suricate',
    version='0.1',
    description='DISCOS monitor and API',
    packages=find_packages(include=['suricate', 'suricate.*']),
    py_modules=[],
    author='Marco Buttu',
    author_email="marco.buttu@inaf.it",
    license='GPL',
    url='https://github.com/discos/suricate/',
    keywords='Alma Common Software property publisher',
    scripts=['scripts/suricate-server', 'scripts/suricate-config'],
    platforms='all',
    install_requires=[
        'redis==3.3.8',
        'apscheduler==3.6.1',
        'MarkupSafe==1.1.1',
        'Jinja2==2.11.3',
        'Flask==1.1.1',
        'itsdangerous==1.1.0',
        'Flask-SQLAlchemy==2.4.3',
        'Flask-Migrate==2.5.3',
        'pyyaml==5.1',
        'rq==1.3.0',
        'python-dotenv',
        'requests',
    ],
    classifiers=[
        'Intended Audience :: Alma Common Software users',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
)
