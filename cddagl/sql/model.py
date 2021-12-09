# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

from datetime import datetime

import sqlalchemy as sa

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

metadata = sa.MetaData()

Base = declarative_base(metadata=metadata)


class ConfigValue(Base):
    __tablename__ = 'config_value'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(32), nullable=False)
    value = sa.Column(sa.Text(), nullable=False)
    created_on = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)


class GameVersion(Base):
    __tablename__ = 'game_version'

    id = sa.Column(sa.Integer, primary_key=True)
    sha256 = sa.Column(sa.String(64), nullable=False)
    version = sa.Column(sa.String(32), nullable=False)
    stable = sa.Column(sa.Boolean, nullable=False)

    game_build = relationship('GameBuild', uselist=False)

    discovered_on = sa.Column(sa.DateTime, nullable=False,
        default=datetime.utcnow)


class GameBuild(Base):
    __tablename__ = 'game_build'

    id = sa.Column(sa.Integer, primary_key=True)
    version = sa.Column(sa.Integer, sa.ForeignKey(GameVersion.id),
        nullable=False)
    build = sa.Column(sa.String(16), nullable=False)
    released_on = sa.Column(sa.DateTime, nullable=False)
    discovered_on = sa.Column(sa.DateTime, nullable=False,
        default=datetime.utcnow)
