<!--
SPDX-FileCopyrightText: 2015-2021 Rémy Roy

SPDX-License-Identifier: MIT
-->

# Building guide

> This guide is **outdated**. A updated version should soon be added to replace this one.

CDDA Game Launcher is developed using Python. In order to run or build the launcher, you will need to download a recent version of Python and install all the requirements.

## Requirements

The full list of requirements is available in [requirements.txt](requirements.txt). Most of these requirements are Python packages that can be installed using [pip](https://en.wikipedia.org/wiki/Pip_%28package_manager%29). Unfortunately, some of these requirements need build tools which are not easy to use nor easy to install on Windows. Here are those special requirements:

* pylzma
* Microsoft C++ Build Tools
* Windows 10 SDK
* Inno Setup

Compiled binaries for lxml and pylzma can be found on [Christoph Gohlke's Unofficial Windows Binaries](http://www.lfd.uci.edu/~gohlke/pythonlibs/). If you are using Python >= 3.5, scandir should already be included. If you are using Python <= 3.4, you can also find compiled binaries for scandir on that website.

## Running the launcher

Once you have Python installed and all the requirements, you can run the launcher by going into the project directory and by running `python -m cddagl`.

## Building the launcher installer for distribution

Once you have Python installed and all the requirements, you can build the launcher installer for distribution by going into the project directory and running `python setup.py create_installer`. This will use the PyInstaller package to create a frozen stand-alone executable with all the dependencies alongside. Afterwards, it will build the installer using Inno Setup. If you want the executable to support RAR archives, you will also need to have the [UnRAR command line tool](http://www.rarlab.com/rar_add.htm) in your PATH (note: a local copy of this utility is already provided in `./third-party/unrar-command-line-tool`)

The resulting launcher installer should be in the `dist\innosetup` directory.

## Step by step guide to run and build the launcher executable

1. Download and install Python 3.9 from [python.org](https://www.python.org/downloads/release/python-3910/). The rest of this guide will assume that you are using the 64-bit (x64) version of Python 3.9.
   1. **_Optional but thoroughly recommended_**: Setup a [virtual environment](https://docs.python.org/3.9/library/venv.html). It will make your development experience immensely easier. 
2. Install most requirements by typing the following `pip` command in your command line window: `pip install SQLAlchemy alembic PyQt5 PyInstaller html5lib cssselect arrow rarfile Babel pypiwin32 pywinutils Markdown Werkzeug` and press `↵ Enter`.
3. Install the `pylzma` package from [Christoph Gohlke's Unofficial Windows Binaries](http://www.lfd.uci.edu/~gohlke/pythonlibs/). `cp39` means CPython 3.9 and `amd64` means 64-bit and in Christoph Gohlke's packages naming convention. The package name you are looking for should be similar to `pylzma-0.5.0-cp39-cp39-win_amd64.whl`. To install `.whl` packages from Christoph Gohlke's Unofficial Windows Binaries page, you can use pip. In your command line window, type: `pip install [path to .whl]` and press `↵ Enter`.
   1. A local copy of a usable pylzma package can be found in `./third-party/pylzma/pylzma-0.5.0-cp39-cp39-win_amd64.whl`, so you can go ahead and `pip install` that one if you have Python 3.9 and a 64-bit Windows installation.
4. Download the CDDA Game Launcher source code. If you have git installed, you can type the following command in your command line window: `git clone https://github.com/DazedNConfused-/CDDA-Game-Launcher.git`. You can also download the source code from [https://github.com/DazedNConfused-/CDDA-Game-Launcher/archive/master.zip](https://github.com/DazedNConfused-/CDDA-Game-Launcher/archive/master.zip). Make sure to extract the zip file somewhere before trying to run the code.
5. In your command line window, change directory to the source code directory. Type `cd [path to source code]` and press `↵ Enter`.
6. See if you can run the launcher by typing the following command in your command line window: `python -m cddagl` and press `↵ Enter`. If you have everything installed correctly, you should see the launcher running.
7. A local copy of [Inno Setup](http://www.jrsoftware.org/isinfo.php) is already provided in `./third-party/inno-setup/`. It will get automatically picked up during the build process. 
   1. If you do not use the default installation provided (ie: you want to use your own local version of Inno Setup), you will have to use the `--compiler=[path to Compil32.exe]` option with the `create_installer` command.
8. Install the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/es/visual-cpp-build-tools/), they are required for `pylzma`'s compilation during the build process.
   1. A local offline copy of the Build Tools' installer is already provided in `./third-party/vs-build-tools/vs_BuildTools.exe`. You should mark the [Visual C++ Build Tools](https://stackoverflow.com/a/55370133) and the [Windows 10 SDK](https://developer.microsoft.com/en-US/windows/downloads/windows-10-sdk) (listed in the optional components) for installation. 
      1. Alternatively, you can import the needed configuration already exported as `./third-party/vs-build-tools/.vsconfig` and the Build Tools' installer shall take care of the rest without further user input.
10. To build the launcher installer, type the following command in your command line window: `python setup.py create_installer` and press `↵ Enter`. The resulting launcher installer should be in the `dist\innosetup` subdirectory.
