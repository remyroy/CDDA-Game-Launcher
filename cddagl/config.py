import os
import sys

from alembic.config import Config
from alembic import command

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import joinedload, joinedload_all

from cddagl.configmodel import ConfigValue, GameVersion, GameBuild

_session = None

def get_db_url():
    return 'sqlite:///{0}'.format(get_config_path())

def init_config(basedir):
    alembic_dir = os.path.join(basedir, 'alembic')
    
    alembic_cfg = Config()
    alembic_cfg.set_main_option('sqlalchemy.url', get_db_url())
    alembic_cfg.set_main_option('script_location', alembic_dir)
    command.upgrade(alembic_cfg, "head")

def get_config_path():
    local_app_data = os.environ['LOCALAPPDATA']    
    
    if os.path.exists(os.path.join(basedir, 'configs.db')):
        return os.path.join(basedir, 'configs.db')

    if not os.path.isdir(local_app_data):
        local_app_data = sys.path

    config_dir = os.path.join(local_app_data, 'CDDA Game Launcher')

    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    return os.path.join(config_dir, 'configs.db')

def get_session():
    global _session

    if _session is None:
        db_engine = create_engine(get_db_url())
        Session = sessionmaker(bind=db_engine)
        _session = Session()

    return _session

def get_config_value(name, default=None):
    session = get_session()

    db_value = session.query(ConfigValue).filter_by(name=name).first()

    if db_value is None:
        return default
    
    return db_value.value

def set_config_value(name, value):
    session = get_session()

    db_value = session.query(ConfigValue).filter_by(name=name).first()

    if db_value is None:
        db_value = ConfigValue()
        db_value.name = name

    db_value.value = value
    session.add(db_value)
    session.commit()

def new_version(version, sha256):
    session = get_session()

    game_version = session.query(GameVersion).filter_by(sha256=sha256).first()

    if game_version is None:
        game_version = GameVersion()
        game_version.sha256 = sha256
        game_version.version = version

        session.add(game_version)
        session.commit()

def new_build(version, sha256, number, release_date):
    session = get_session()

    game_version = session.query(GameVersion).filter_by(sha256=sha256
        ).options(joinedload('game_build')
        ).first()

    if game_version is None:
        game_version = GameVersion()
        game_version.sha256 = sha256
        game_version.version = version

        session.add(game_version)

    if game_version.game_build is None:
        game_build = GameBuild()
        game_build.build = number
        game_build.released_on = release_date

        game_version.game_build = game_build

        session.commit()

def get_build_from_sha256(sha256):
    session = get_session()
    
    game_version = session.query(GameVersion).filter_by(sha256=sha256
        ).options(joinedload('game_build')
        ).first()

    if game_version is not None and game_version.game_build is not None:
        game_build = game_version.game_build
        return {
            'build': game_build.build,
            'released_on': game_build.released_on
        }

    return None
