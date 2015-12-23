from datetime import datetime

import sqlalchemy as sa

from sqlalchemy.ext.declarative import declarative_base

metadata = sa.MetaData()

Base = declarative_base(metadata=metadata)


class ConfigValue(Base):
    __tablename__ = 'config_value'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(32), nullable=False)
    value = sa.Column(sa.Text(), nullable=False)


class GameVersion(Base):
    __tablename__ = 'game_version'

    id = sa.Column(sa.Integer, primary_key=True)
    sha256 = sa.Column(sa.String(64), nullable=False)
    version = sa.Column(sa.String(32), nullable=False)