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
        call(['pyi-makespec', '-F', '-w', '--noupx',
          '--hidden-import=lxml.cssselect', 'cddagl\launcher.py'])

        added_files = [('alembic', 'alembic')]

        spec_content = None
        with open('launcher.spec', 'r') as f:
            spec_content = f.read()

        spec_content = spec_content.replace('datas=None', 'datas=added_files')
        spec_content = ('added_files = ' + repr(added_files) + '\n' +
            spec_content)

        with open('launcher.spec', 'w') as f:
            f.write(spec_content)

        call(['pyinstaller', 'launcher.spec'])


setup(name='cddagl',
      version='0.3',
      description=(
          'A Cataclysm: Dark Days Ahead launcher with additional features'),
      author='Rémy Roy',
      author_email='remyroy@remyroy.com',
      url='https://github.com/remyroy/CDDA-Game-Launcher',
      packages=['cddagl'],
      cmdclass={'installer': Installer},
     )