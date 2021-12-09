# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import pkgutil


__version__ = pkgutil.get_data('cddagl', 'VERSION').decode("utf8").strip()
