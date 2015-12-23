import sys
import os

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from cddagl.config import init_config
from cddagl.ui import start_ui

if __name__ == '__main__':

    init_config()

    start_ui()
