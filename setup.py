import os
from shutil import copyfile

try:
    from setuptools import setup
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install

from suricate.paths import (
    suricate_dir,
    config_dir,
    config_file,
    log_dir,
    template_dir,
)


try:
    os.mkdir(suricate_dir)
except OSError:
    pass  # The directory already exists
try:
    os.mkdir(config_dir)
except OSError:
    pass  # The directory already exists
try:
    os.mkdir(log_dir)
except OSError:
    pass  # The directory already exists
try:
    os.mkdir(template_dir)
except OSError:
    pass  # The directory already exists

for file_name in os.listdir('templates'):
    source_file = os.path.join('templates', file_name)
    dest_file = os.path.join(template_dir, file_name)
    copyfile(source_file, dest_file)


setup(
    name='suricate',
    version='0.1',
    description='ACS property publisher',
    packages=['suricate'],
    py_modules=[],
    author='Marco Buttu',
    author_email="marco.buttu@inaf.it",
    license='GPL',
    url='https://github.com/marco-buttu/suricate/',
    keywords='Alma Common Software property publisher',
    scripts=['scripts/suricate-server', 'scripts/suricate-config'],
    platforms='all',
    install_requires=[
        'redis==3.3.8',
        'apscheduler==3.6.1',
        'flask==1.1.1',
        'pyyaml',
    ],
    classifiers=[
        'Intended Audience :: Alma Common Software users',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
)
