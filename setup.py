#!/usr/bin/env python

# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import os
import sys
import os.path
import pathlib
import winreg

from pathlib import Path
import shutil
import httpx
from zipfile import ZipFile
import subprocess

from distutils.cmd import Command
from distutils.core import setup
from os import scandir
from subprocess import call, check_output, CalledProcessError, DEVNULL

try:
    import txclib.commands
    import txclib.utils
except ImportError:
    print('Transifex client not found. Consider installing it (`pip install transifex-client`) '
        'if you need to interact with Transifex.', file=sys.stderr)

from babel.messages import frontend as babel


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
    with open(get_setup_dir() / 'cddagl' / 'VERSION') as version_file:
        return version_file.read().strip()


def log(msg):
    print(msg)


class ExtendedCommand(Command):
    def run_other_command(self, command_name, **kwargs):
        """Runs another command with specified parameters."""
        command = self.reinitialize_command(command_name)

        vars(command).update(**kwargs)
        command.ensure_finalized()

        self.announce(f'running {command_name}', 2)
        command.run()

        return command

def include_requirements(target_path):
    # Install packages from requirements.txt file into build dir
    requirements_path = Path('requirements.txt')
    subprocess.run([
        'python', '-m', 'pip', 'install', '--upgrade', "pip"
    ])
    subprocess.run([
        'python', '-m', 'pip', 'install', '-r', requirements_path,
        '--target', target_path
    ])

    # Clean __pycache__ directories
    dir_list = []
    dir_list.append(target_path)
    while len(dir_list) > 0:
        next_dir = dir_list.pop()
        with os.scandir(next_dir) as it:
            for entry in it:
                if entry.name.startswith('.'):
                    continue
                if entry.is_dir():
                    if entry.name == '__pycache__':
                        shutil.rmtree(entry.path)
                    else:
                        dir_list.append(entry.path)

    # Clean .dist-info directories
    with os.scandir(target_path) as dir_it:
        for entry in dir_it:
            if entry.name.startswith('.') or not entry.is_dir():
                continue
            
            if entry.name.endswith('.dist-info'):
                shutil.rmtree(entry.path)

class Bundle(ExtendedCommand):
    description = 'Bundle CDDAGL with Python'
    user_options = []

    def initialize_options(self):
        self.locale_dir = os.path.join('cddagl', 'locale')

    def finalize_options(self):
        pass

    def run(self):
        print('Bundling with Python for Windows')

        src_package_path = Path('cddagl')

        build_path = Path('build')
        if build_path.is_dir():
            shutil.rmtree(build_path)
        build_path.mkdir(parents=True, exist_ok=True)

        download_path = build_path.joinpath('downloads')
        download_path.mkdir(parents=True, exist_ok=True)

        # Download Python embeddable package
        python_embed_url = 'https://www.python.org/ftp/python/3.9.7/python-3.9.7-embed-amd64.zip'
        python_embed_name = 'python-3.9.7-embed-amd64.zip'

        python_embed_archive = download_path.joinpath(python_embed_name)
        try:
            with open(python_embed_archive, 'wb') as binary_file:
                print(f'Downloading python archive {python_embed_name}...')
                with httpx.stream('GET', python_embed_url) as http_stream:
                    if http_stream.status_code != 200:
                        print(f'Cannot download python archive {python_embed_name}.\n'
                            f'Unexpected status code {http_stream.status_code}')
                        return False
                    for data in http_stream.iter_bytes():
                        binary_file.write(data)
        except httpx.RequestError as exception:
            print(f'Exception while downloading python archive. Exception: {exception}')
            return False

        archive_dir_path = build_path.joinpath('archive')
        archive_dir_path.mkdir(parents=True, exist_ok=True)

        # Extracting Python embeddable package
        print(f'Extracting python archive {python_embed_name}...')
        with ZipFile(python_embed_archive, 'r') as zip_file:
            zip_file.extractall(archive_dir_path)
        
        # Add mo files for localization
        self.run_other_command('compile_catalog')

        # Copy package into archive dir
        archive_package_path = archive_dir_path.joinpath('cddagl')
        shutil.copytree(src_package_path, archive_package_path)

        # Additional directories
        src_data_path = Path('data')
        target_data_path = archive_dir_path.joinpath('data')
        shutil.copytree(src_data_path, target_data_path)

        src_alembicrepo_path = Path('alembicrepo')
        target_alembicrepo_path = archive_dir_path.joinpath('alembicrepo')
        shutil.copytree(src_alembicrepo_path, target_alembicrepo_path)

        include_requirements(archive_dir_path)

        # Move pywin32_system32 dlls into archive root
        pywin32_system32_path = archive_dir_path.joinpath('pywin32_system32')
        with os.scandir(pywin32_system32_path) as it:
            for entry in it:
                if entry.is_file():
                    shutil.move(entry.path, archive_dir_path)
        
        shutil.rmtree(pywin32_system32_path)

        # Let's find and add unrar if available
        try:
            unrar_path = r'.\third-party\unrar-command-line-tool\UnRAR.exe'
            shutil.copy(unrar_path, archive_dir_path)
        except CalledProcessError:
            log("'unrar.exe' couldn't be found.")
        
        # Remove unneeded files in archive
        paths_to_remove = [
            ['bin'],
            ['adodbapi'],
            ['pythonwin'],
            ['PyQt5', 'Qt5', 'qml']
        ]
        for path in paths_to_remove:
            target_path = archive_dir_path.joinpath(*path)
            if target_path.is_dir():
                shutil.rmtree(target_path)
        
        # Create batch file for starting the launcher easily
        batch_file_path = archive_dir_path.joinpath('Launcher.bat')
        with open(batch_file_path, 'w', encoding='utf8') as batch_file:
            batch_file.write(
                '''
                @echo off
                start /realtime python.exe -m cddagl
                '''
            )

        # zip finished file
        print('Writing portable zip file...')

        zip_file_src = archive_dir_path

        zip_file_dest = Path(f'dist')
        zip_file_dest.mkdir(parents=True, exist_ok=True)
        zip_file_dest = f'dist/cddagl_portable_v{get_version()}'

        shutil.make_archive(
            base_name=zip_file_dest,
            format='zip',
            root_dir=zip_file_src,
            verbose=True
        )

class FreezeWithPyInstaller(ExtendedCommand):
    description = 'Build CDDAGL with PyInstaller'
    user_options = [
        ('debug=', None, 'Specify if we are using a debug build with PyInstaller.')
    ]

    def initialize_options(self):
        self.debug = None
        self.locale_dir = os.path.join('cddagl', 'locale')

    def finalize_options(self):
        pass

    def run(self):
        # -w for no console and -c for console
        window_mode = '-c' if bool(self.debug) else '-w'

        makespec_call = [
            'pyi-makespec', '-D', window_mode, '--noupx',
            '--hidden-import=lxml.cssselect',
            '--hidden-import=babel.numbers',
            '--hidden-import=pkg_resources.py2_warn',
            'cddagl\launcher.py',
            '-i', r'cddagl\resources\launcher.ico'
        ]

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
            pass

        if windowskit_path is not None:
            ucrt_path = windowskit_path + 'Redist\\ucrt\\DLLs\\x86\\'
            makespec_call.extend(('-p', ucrt_path))

        # Additional files
        added_files = [
            ('alembic', 'alembic'),
            ('alembicrepo', 'alembicrepo'),
            ('data', 'data'),
            ('cddagl/resources', 'cddagl/resources'),
            ('cddagl/VERSION', 'cddagl')
        ]

        added_binaries = []

        # Let's find and add unrar if available
        try:
            unrar_path = check_output(['where', 'unrar.exe'], stderr=DEVNULL)
            unrar_path = unrar_path.strip().decode('cp437')
            added_files.append((unrar_path, '.'))
        except CalledProcessError:
            log("'unrar.exe' couldn't be found.")

        # Add mo files for localization
        self.run_other_command('compile_catalog')

        if os.path.isdir(self.locale_dir):
            for entry in scandir(self.locale_dir):
                if entry.is_dir():
                    mo_path = os.path.join(entry.path, 'LC_MESSAGES', 'cddagl.mo')
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
            makespec_call.extend(('-d', 'all'))

        # Call the makespec util
        log(f'executing {makespec_call}')
        call(makespec_call)

        # Call pyinstaller
        pyinstaller_call = ['pyinstaller']

        # Add debug info for PyInstaller
        if bool(self.debug):
            pyinstaller_call.append('--clean')
            pyinstaller_call.extend(('--log-level', 'DEBUG'))

        pyinstaller_call.append('--noconfirm')
        pyinstaller_call.append('launcher.spec')

        log(f'executing {pyinstaller_call}')
        call(pyinstaller_call)


class CreateInnoSetupInstaller(ExtendedCommand):
    description = 'Creates a Windows Installer for the project'
    user_options = [
        ('compiler=', None, 'Specify the path to Inno Setup Compiler (Compil32.exe).'),
    ]

    def initialize_options(self):
        self.compiler = r'.\third-party\inno-setup\6.2.0\Compil32.exe'

    def finalize_options(self):
        if not pathlib.Path(self.compiler).exists():
            raise Exception('Inno Setup Compiler (Compil32.exe) not found.')

    def run(self):
        #### Make sure we are running Inno Setup from the project directory
        os.chdir(get_setup_dir())

        self.run_other_command('bundle')
        inno_call = [self.compiler, '/cc', 'launcher.iss']
        log(f'executing {inno_call}')
        call(inno_call)


class TransifexPull(ExtendedCommand):
    description = 'Download translated strings from Transifex service.'
    user_options = [
        ('reviewed-only', None, 'Download only reviewed translations.'),
    ]

    def initialize_options(self):
        self.reviewed_only = False

    def finalize_options(self):
        pass

    def run(self):
        ### Make sure we are running the commands from project directory
        os.chdir(get_setup_dir())

        args = ['--no-interactive', '--all', '--force']
        if self.reviewed_only:
            args.extend(['--mode', 'onlyreviewed'])
        else:
            args.extend(['--mode', 'onlytranslated'])

        txclib.utils.DISABLE_COLORS = True
        txclib.commands.cmd_pull(args, get_setup_dir())
        self.run_other_command('compile_catalog')


class TransifexPush(Command):
    description = 'Push untranslated project strings to Transifex service.'
    user_options = [
        ('push-translations', None, 'Push translations too, this will try to merge translations.'),
    ]

    def initialize_options(self):
        self.push_translations = False

    def finalize_options(self):
        pass

    def run(self):
        ### Make sure we are running the commands from project directory
        os.chdir(get_setup_dir())

        args = ['--no-interactive', '--source', '--force']
        if self.push_translations:
            args.append('--translations')

        txclib.utils.DISABLE_COLORS = True
        txclib.commands.cmd_push(args, get_setup_dir())


class TransifexExtractPush(ExtendedCommand):
    description = 'Extract all translatable strings and push them to Transifex service.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        ### Make sure we are running the commands from project directory
        os.chdir(get_setup_dir())
        self.run_other_command('extract_messages')
        self.run_other_command('translation_push')


class ExtractMessagesWithDefaults(babel.extract_messages):

    def initialize_options(self):
        super().initialize_options()
        self.output_file = r'cddagl\locale\cddagl.pot'
        self.mapping_file = r'cddagl\locale\mapping.cfg'


class UpdateCatalogWithDefaults(babel.update_catalog):

    def initialize_options(self):
        super().initialize_options()
        self.input_file = r'cddagl\locale\cddagl.pot'
        self.output_dir = r'cddagl\locale'
        self.domain = 'cddagl'


class CompileCatalogWithDefauls(babel.compile_catalog):

    def initialize_options(self):
        super().initialize_options()
        self.directory = r'cddagl\locale'
        self.domain = 'cddagl'
        self.use_fuzzy = True


class ExtractUpdateMessages(ExtendedCommand):
    description = 'Extract all project strings that require translation and update catalogs.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_other_command('extract_messages')
        self.run_other_command('update_catalog')


setup(
    name='cddagl',
    version=get_version(),
    description=('A Cataclysm: Dark Days Ahead launcher with additional features'),
    author='Rémy Roy',
    author_email='remyroy@remyroy.com',
    maintainer='Gonzalo López',
    url='https://github.com/DazedNConfused-/CDDA-Game-Launcher',
    packages=['cddagl'],
    package_data={'cddagl': ['VERSION']},
    cmdclass={
        ### freeze & installer commands
        'bundle': Bundle,
        'freeze': FreezeWithPyInstaller,
        'create_installer': CreateInnoSetupInstaller,
        ### babel commands
        'extract_messages': ExtractMessagesWithDefaults,
        'compile_catalog': CompileCatalogWithDefauls,
        'init_catalog': babel.init_catalog,
        'update_catalog': UpdateCatalogWithDefaults,
        'exup_messages': ExtractUpdateMessages,
        ### transifex related commands
        'translation_push': TransifexPush,
        'translation_expush': TransifexExtractPush,
        'translation_pull': TransifexPull,
    },
)
