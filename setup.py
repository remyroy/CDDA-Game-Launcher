#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command

from babel.messages import frontend as babel

from subprocess import call, check_output, CalledProcessError

import os
import pathlib
import winreg

import os.path

try:
    from os import scandir
except ImportError:
    from scandir import scandir


def get_setup_dir():
    """Return an absolute path to setup.py directory
    Useful to find project files no matter where setup.py is invoked.
    """
    try:
        return get_setup_dir.setup_base_dir
    except AttributeError:
        get_setup_dir.setup_base_dir = pathlib.Path(__file__).absolute().parent
    return get_setup_dir.setup_base_dir


def get_version():
    with open(get_setup_dir() / 'VERSION') as version_file:
        return version_file.read().strip()


class CompileWithPyInstaller(Command):
    description = 'Build CDDAGL with PyInstaller'
    user_options = [
        ('debug=', None,
            'Specify if we are using a debug build with PyInstaller.'),
    ]

    def initialize_options(self):
        self.debug = None

    def finalize_options(self):
        pass

    def run(self):
        window_mode = '-w' # -w for no console and -c for console

        if bool(self.debug):
            window_mode = '-c'

        makespec_call = ['pyi-makespec', '-D', window_mode, '--noupx',
            '--hidden-import=lxml.cssselect', '--hidden-import=babel.numbers',
            'cddagl\launcher.py', '-i', r'cddagl\resources\launcher.ico']

        # Check if we have Windows Kits 10 path and add ucrt path
        windowskit_path = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows Kits\Installed Roots',
                access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
            value = winreg.QueryValueEx(key, 'KitsRoot10')
            windowskit_path = value[0]
            winreg.CloseKey(key)
        except OSError:
            windowskit_path = None

        if windowskit_path is not None:
            ucrt_path = windowskit_path + 'Redist\\ucrt\\DLLs\\x86\\'
            makespec_call.extend(('-p', ucrt_path))

        # Additional files
        added_files = [('alembic', 'alembic'), ('bin/updated.bat', '.'),
            ('data', 'data'), ('cddagl/resources', 'cddagl/resources')]

        added_binaries = []

        # Let's find and add unrar if available
        try:
            unrar_path = check_output(['where', 'unrar.exe']).strip().decode(
                'utf8')
            added_files.append((unrar_path, '.'))
        except CalledProcessError:
            pass

        # Add mo files for localization
        locale_dir = os.path.join('cddagl', 'locale')

        call('python setup.py compile_catalog -D cddagl -d {locale_dir}'.format(
            locale_dir=locale_dir))

        if os.path.isdir(locale_dir):
            for entry in scandir(locale_dir):
                if entry.is_dir():
                    mo_path = os.path.join(entry.path, 'LC_MESSAGES',
                        'cddagl.mo')
                    if os.path.isfile(mo_path):
                        mo_dir = os.path.dirname(mo_path).replace('\\', '/')
                        mo_path = mo_path.replace('\\', '/')
                        added_files.append((mo_path, mo_dir))

        # Include additional files
        for src, dest in added_files:
            src_dest = src + ';' + dest
            makespec_call.extend(('--add-data', src_dest))

        for src, dest in added_binaries:
            src_dest = src + ';' + dest
            makespec_call.extend(('--add-binary', src_dest))

        # Add debug build
        if bool(self.debug):
            makespec_call.append('-d')

        # Call the makespec util
        call(makespec_call)

        # Call pyinstaller
        pyinstaller_call = ['pyinstaller']

        # Add debug info for PyInstaller
        if bool(self.debug):
            pyinstaller_call.append('--clean')
            pyinstaller_call.extend(('--log-level', 'DEBUG'))

        pyinstaller_call.append('launcher.spec')

        call(pyinstaller_call)


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
      version=get_version(),
      description=(
          'A Cataclysm: Dark Days Ahead launcher with additional features'),
      author='Rémy Roy',
      author_email='remyroy@remyroy.com',
      url='https://github.com/remyroy/CDDA-Game-Launcher',
      packages=['cddagl'],
      cmdclass={'installer': CompileWithPyInstaller,
        'exup_messages': ExtractUpdateMessages,
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog},
)
