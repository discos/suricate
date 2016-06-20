try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='Suricate',
    version='0.1',
    description='ACS property publisher',
    packages=[
        'suricate',
    ],
    py_modules=[],
    author='Marco Buttu',
    author_email="mbuttu@oa-cagliari.inaf.it",
    license='GPL',
    url='https://github.com/marco-buttu/suricate/',
    keywords='Alma Common Software property publisher',
    scripts=['scripts/suricate-server', 'scripts/suricate-config'],
    platforms='all',
    install_requires=[
        'redis>=2.10.3',
        'apscheduler>=3.0.3',
        'Flask',
    ],
    classifiers=[
        'Intended Audience :: Alma Common Software users',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
   ],
)
