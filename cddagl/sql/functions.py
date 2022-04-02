# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import os
import threading

from alembic import command
from alembic.config import Config

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, joinedload

from cddagl.sql.model import ConfigValue, GameVersion, GameBuild


class ThreadSafeSessionManager():
    def __init__(self):
        self._lock = threading.Lock()
        self.sessions = {}

    def has_session(self, thread_id):
        return thread_id in self.sessions

    def get_session(self, thread_id):
        return self.sessions[thread_id]

    def save_session(self, thread_id, session):
        self._lock.acquire()
        self.sessions[thread_id] = session
        self._lock.release()


def get_db_url():
    return 'sqlite:///{0}'.format(get_config_path())


def init_config(basedir):
    alembic_dir = os.path.join(basedir, 'alembicrepo')

    alembic_cfg = Config()
    alembic_cfg.set_main_option('sqlalchemy.url', get_db_url())
    alembic_cfg.set_main_option('script_location', alembic_dir)

    try:
        command.upgrade(alembic_cfg, "head")
    except OperationalError:
        # If we cannot upgrade the database, we remove it and try again
        os.remove(get_config_path())
        command.upgrade(alembic_cfg, "head")


def get_config_path():
    local_app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA'))
    if local_app_data is None or not os.path.isdir(local_app_data):
        local_app_data = ''

    config_dir = os.path.join(local_app_data, 'CDDA Game Launcher')

    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    return os.path.join(config_dir, 'configs.db')


def get_session():
    global _session_manager
    try:
        _session_manager
    except NameError:
        _session_manager = ThreadSafeSessionManager()

    thread_id = threading.current_thread().ident
    if not _session_manager.has_session(thread_id):
        db_engine = create_engine(get_db_url())
        Session = sessionmaker(bind=db_engine)
        _session_manager.save_session(thread_id, Session())

    return _session_manager.get_session(thread_id)


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


def new_version(version, sha256, stable):
    session = get_session()

    game_version = session.query(GameVersion).filter_by(sha256=sha256).first()

    if game_version is None:
        game_version = GameVersion()
        game_version.sha256 = sha256
        game_version.version = version
        game_version.stable = stable

        session.add(game_version)
        session.commit()
    elif game_version.version != version or game_version.stable != stable:
        # if info doesn't match, update it
        game_version.version = version
        game_version.stable = stable

        session.add(game_version)
        session.commit()


def new_build(version, sha256, stable, number, release_date):
    session = get_session()

    game_version = (session
                    .query(GameVersion)
                    .filter_by(sha256=sha256)
                    .options(joinedload('game_build'))
                    .first())

    if game_version is None:
        game_version = GameVersion()
        game_version.sha256 = sha256
        game_version.version = version
        game_version.stable = stable

        session.add(game_version)

    if game_version.game_build is None:
        game_build = GameBuild()
        game_build.build = number
        game_build.released_on = release_date

        game_version.game_build = game_build

        session.commit()


def get_build_from_sha256(sha256):
    session = get_session()

    game_version = (session
                    .query(GameVersion)
                    .filter_by(sha256=sha256)
                    .options(joinedload('game_build'))
                    .first())

    if game_version is not None and game_version.game_build is not None:
        game_build = game_version.game_build
        return {
            'build': game_build.build,
            'released_on': game_build.released_on
        }

    return None


def config_true(value):
    return value == 'True' or value == '1'
