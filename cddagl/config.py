import os
import sys

from alembic.config import Config
from alembic import command

def init_config(basedir):
    config_path = get_config_path()

    alembic_dir = os.path.join(basedir, 'alembic')
    
    alembic_cfg = Config()
    alembic_cfg.set_main_option('sqlalchemy.url',
        'sqlite:///{0}'.format(config_path))
    alembic_cfg.set_main_option('script_location', alembic_dir)
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