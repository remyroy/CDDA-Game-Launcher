# Building guide

CDDA Game Launcher is developed using Python. In order to run or build the launcher, you will need to download a recent version of Python and install all the requirements.

## Requirements

The full list of requirements is available in [requirements.txt](requirements.txt). Most of these requirements are Python packages that can be installed using [pip](https://en.wikipedia.org/wiki/Pip_%28package_manager%29). Unfortunately, there is no easy to use and easy to install build tools on Windows to compile and install a few of these requirements:

* PyQt5
* scandir
* lxml

I suggest you download and install already compiled binaries for these. At this time of writing, [the PyQt5 binaries](https://www.riverbankcomputing.com/software/pyqt/download5) are only available for Python 3.4 which means you should be using that version of Python as well.

Compiled binaries for lxml and scandir can be found on [Christoph Gohlke's Unofficial Windows Binaries](http://www.lfd.uci.edu/~gohlke/pythonlibs/). If you are using Python 3.5+, scandir should already be included.

## Running the launcher

Once you have Python installed and all the requirements, you can run the launcher by going into the project directory and by running `python cddagl\launcher.py`.

## Building the launcher executable for distribution

Once you have Python installed and all the requirements, you can build the launcher executable for distribution by going into the project directory and running `python setup.py installer`. This will use the PyInstaller package to create a frozen stand-alone executable with all the dependencies bundled. If you want the executable to support RAR archives, you will also need to have the [UnRAR command line tool](http://www.rarlab.com/rar_add.htm) in your PATH.

The resulting launcher executable should be in the `dist` directory.

## Step by step guide to run and build the launcher executable

1. Download and install Python 3.4 from [https://www.python.org/downloads/release/python-344/](https://www.python.org/downloads/release/python-344/). Take note of whether you get the 32-bit (x86) or the 64-bit version (x86-64). Both version should work fine but they will have different binary dependencies.
2. Open a command line window and make sure the Python directory and Scripts subdirectory are in your PATH.
    * Press `⊞ Win`+`R`, type `cmd` and press `↵ Enter` to open a command line window.
    * By default, Python 3.4 is installed in `C:\Python34`. To setup your PATH, type `set PATH=%PATH%;C:\Python34;C:\Python34\Scripts` in your command line window and press `↵ Enter`.
3. Install most requirements by typing the following `pip` command in your command line window: `pip install SQLAlchemy alembic PyInstaller html5lib cssselect arrow rarfile` and press `↵ Enter`.
4. Download and install the PyQt5 binaries from [Riverbank Computing's website](https://www.riverbankcomputing.com/software/pyqt/download5). Make sure to download the same platform version (either 32-bit or 64-bit). It should match the same platform version you got in Step 1.
5. Download and install the scandir and lxml packages from [Christoph Gohlke's Unofficial Windows Binaries](http://www.lfd.uci.edu/~gohlke/pythonlibs/). It should match the same Python version and platform version you got in Step 1. `cp34` means CPython 3.4, `win32` means 32-bit and `win_amd64` means 64-bit in Christoph Gohlke's packages naming convention. To install `.whl` packages from Christoph Gohlke's Unofficial Windows Binaries page, you can using pip. In your command line window, type: `pip install [path to .whl]` and press `↵ Enter`.
6. Download the CDDA Game Launcher source code. If you have git installed, you can type the following command in your command line window: `git clone https://github.com/remyroy/CDDA-Game-Launcher.git`. You can also download the source code from [https://github.com/remyroy/CDDA-Game-Launcher/archive/master.zip](https://github.com/remyroy/CDDA-Game-Launcher/archive/master.zip). Make sure to extract the zip file somewhere before trying to run the code.
7. In your command line window, change directory to the source code directory. Type `cd [path to source code]` and press `↵ Enter`.
8. See if you can run the launcher by typing the following command in your command line window: `python cddagl\launcher.py` and press `↵ Enter`. If you have everything setuped correctly, you should see the launcher running.
9. Download the [UnRAR command line tool](http://www.rarlab.com/rar/unrarw32.exe) and extract it to `C:\Python34\Scripts`.
9. To build the launcher executable, type the following command in your command line window: `python setup.py installer` and press `↵ Enter`. The resulting launcher executable should be in the `dist` subdirectory.