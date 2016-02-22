#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command

from babel.messages import frontend as babel

from subprocess import call, check_output, CalledProcessError


class Installer(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        call(['pyi-makespec', '-F', '-w', '--noupx',
            '--hidden-import=lxml.cssselect', 'cddagl\launcher.py'])

        added_files = [('alembic', 'alembic'), ('bin/updated.bat', '.'),
            ('data', 'data'), ('cddagl/resources', 'cddagl/resources')]

        # Let's find and add unrar if available
        try:
            unrar_path = check_output(['where', 'unrar.exe']).strip().decode(
                'utf8')
            added_files.append((unrar_path, '.'))
        except CalledProcessError:
            pass

        spec_content = None
        with open('launcher.spec', 'r') as f:
            spec_content = f.read()

        spec_content = spec_content.replace('datas=None', 'datas=added_files')
        spec_content = ('added_files = ' + repr(added_files) + '\n' +
            spec_content)

        with open('launcher.spec', 'w') as f:
            f.write(spec_content)

        call(['pyinstaller', 'launcher.spec'])


class ExtractUpdateMessages(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        call('python setup.py extract_messages -o cddagl\locale\messages.pot '
            '-F cddagl\locale\mapping.cfg')

        call('python setup.py update_catalog -i cddagl\locale\messages.pot -d '
            'cddagl\locale -D cddagl')


setup(name='cddagl',
      version='0.8.5',
      description=(
          'A Cataclysm: Dark Days Ahead launcher with additional features'),
      author='Rémy Roy',
      author_email='remyroy@remyroy.com',
      url='https://github.com/remyroy/CDDA-Game-Launcher',
      packages=['cddagl'],
      cmdclass={'installer': Installer,
        'exup_messages': ExtractUpdateMessages,
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog},
)