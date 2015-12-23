import sys
import os

if getattr(sys, 'frozen', False):
    # we are running in a bundle
    basedir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(basedir)

from cddagl.config import init_config
from cddagl.ui import start_ui

if __name__ == '__main__':

    init_config(basedir)

    start_ui()
