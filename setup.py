"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

import os
from setuptools import setup, find_packages
from simgame import VERSION
APP = ['simgame/main.py']
APP_NAME = 'simgame'
DATA_FILES = []
for (path, directories, filenames) in os.walk("simgame/assets"):
    for filename in filenames:
        DATA_FILES.append(os.path.join(path, filename))
OPTIONS = {'force_system_tk': True,
 'packages': 'numpy==1.14.1,panda3d>=1.10.0,pudb==2017.1.4,Pygments==2.2.0,urwid==2.0.1,Pmw>=2.0.1,astropy>=3.0.1,jplephem>=2.7,pysolar>=0.7,',
 'report_missing_from_imports': True}

setup(
    name             = APP_NAME,
    app              = APP,
    version          = VERSION,
    data_files       = DATA_FILES,
    options          = {'py2app': OPTIONS},
    setup_requires   = ['py2app'],
    packages         = find_packages(),
    install_requires = [
        'numpy>=1.14.1',
        'panda3d>=1.10.0',
        'Pmw>=2.0.1',
        'astropy>=3.0.1',
        'jplephem>=2.7',
        'pysolar>=0.7',
        'neovim>=0.2',
        'Flask-Bootstrap>=3.3.5',
        'webassets>=0.1',
        'Flask-Session>=0.3',
        'Flask-WTF>=0.12',
        'Flask-Login>=0.4',
        'flask-nav>=0.6',
        'requests>=2.18',
        'Flask-Cache>=0.13.1',
        'pyperclip>=1.6.0',
    ],
    entry_points      = {
        'console_scripts': [
                'simgame=simgame.main',
            ]
        },
)
