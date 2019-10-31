try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='suricate',
    version='0.1',
    description='ACS property publisher',
    packages=[
        'suricate',
    ],
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
