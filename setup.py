

import os
from shutil import copyfile
from setuptools import setup, find_packages

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
        print(f'Directory {d} created')
    except OSError:
        pass  # Directory already exists


for file_name in os.listdir('templates'):
    source_file = os.path.join('templates', file_name)
    dest_file = os.path.join(template_dir, file_name)
    copyfile(source_file, dest_file)

# Read requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

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
    install_requires=requirements,
    classifiers=[
        'Intended Audience :: Alma Common Software users',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
    ],
)
