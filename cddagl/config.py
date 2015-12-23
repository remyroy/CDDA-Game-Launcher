import os
import sys

from alembic.config import Config
from alembic import command

def init_config():
    config_path = get_config_path()

    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    alembic_ini = os.path.join(project_dir, 'alembic.ini')
    
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url",
        "sqlite:///{0}".format(config_path))
    command.upgrade(alembic_cfg, "head")

def get_config_path():
    local_app_data = os.environ['LOCALAPPDATA']
    if not os.path.isdir(local_app_data):
        local_app_data = sys.path

    config_dir = os.path.join(local_app_data, 'CDDA Game Launcher')

    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    return os.path.join(config_dir, 'configs.db')

def get_config():
    if _config_values is None:
        config_path = getConfigPath()

    #return _config_values

def save_config():
    pass