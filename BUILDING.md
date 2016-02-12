# Building guide

CDDA Game Launcher is developed using Python. In order to run or build the launcher, you will need to download a recent version of Python and install all the requirements.

## Requirements

The full list of requirements is available in [requirements.txt](requirements.txt). Most of these requirements are Python packages that can be installed using [pip](https://en.wikipedia.org/wiki/Pip_%28package_manager%29). Unfortunately, there is no easy to use and easy to install build tools on Windows to compile and install a few of these requirements:

* PyQt5
* lxml

I suggest you download and install already compiled binaries for these. At this time of writing, [the PyQt5 binaries](https://www.riverbankcomputing.com/software/pyqt/download5) are only available for Python 3.4 which means you should be using that version of Python as well.

Compiled binaries for lxml can be found on [Christoph Gohlke Unofficial Windows Binaries](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml).

## Running the launcher

Once you have Python installed and all the requirements, you can run the launcher by going into the project directory and running `python cddagl\launcher.py`.

## Building the launcher executable for distribution

Once you have Python installed and all the requirements, you can build the launcher executable for distribution by going into the project directory and running `python setup.py installer`. This will use the PyInstaller package to create a frozen stand-alone executable with all the dependencies bundled. If you want the executable to support RAR archives, you will also need to have the [UnRAR command line tool](http://www.rarlab.com/rar_add.htm) in your PATH.

The resulting launcher executable should be in the `dist` directory.

## Step by step guide to run and build the launcher executable

Will be available later.