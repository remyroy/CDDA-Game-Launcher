#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command

from subprocess import call

class Installer(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        call(['pyinstaller', '-F', '-w', 'cddagl\launcher.py'])


setup(name='cddagl',
      version='1.0',
      description=(
        'A Cataclysm: Dark Days Ahead launcher with additional features'),
      author='Rémy Roy',
      author_email='remyroy@remyroy.com',
      url='https://github.com/remyroy/CDDA-Game-Launcher',
      packages=['cddagl'],
      cmdclass={'installer': Installer},
     )