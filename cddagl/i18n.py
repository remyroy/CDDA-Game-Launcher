# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import builtins
import gettext
import logging
import os

logger = logging.getLogger(__name__)

default_names_to_install = ('gettext', 'ngettext')


def proxy_gettext(*args, **kwargs):
    """Proxy calls this function to the real built-in gettext() function.

    This is not required for normal operation of the application, could be not imported at all,
    but will help development.
    """
    ### this would load gettext in case it wasn't done before use, but could hide an app bug.
    #if 'gettext' not in builtins.__dict__:
    #    load_gettext_no_locale()
    return builtins.__dict__['gettext'](*args, **kwargs)


def proxy_ngettext(*args, **kwargs):
    """Proxy calls to this function to the real built-in ngettext() function.

    This is not required for normal operation of the application, could be not imported at all,
    but will help development.
    """
    ### this would load gettext in case it wasn't done before use, but could hide an app bug.
    #if 'ngettext' not in builtins.__dict__:
    #    load_gettext_no_locale()
    return builtins.__dict__['ngettext'](*args, **kwargs)


def get_available_locales(locale_dir):
    """Return a list of available locales in the specified directory."""
    available_locales = {'en'}
    if os.path.isdir(locale_dir):
        entries = os.scandir(locale_dir)
        for entry in entries:
            if entry.is_dir():
                available_locales.add(entry.name)

    return sorted(available_locales, key=lambda x: 0 if x == 'en' else 1)


def load_gettext_no_locale():
    """Load gettext into the application using base strings (no translations)."""
    translation = gettext.NullTranslations()
    translation.install(default_names_to_install)
    return translation


def load_gettext_locale(locale_dir, locale, domain='cddagl'):
    """Load gettext into the application with specified locale file.

    Fallback to default untranslated strings if locale file is not found.
    """
    if locale == 'en':
        return load_gettext_no_locale()

    try:
        translation = gettext.translation(domain, localedir=locale_dir, languages=[locale])
    except FileNotFoundError as err:
        logger.warning(
            'Could not get translations for {locale} in {locale_dir}. Error: {info}'
            .format(locale=locale, locale_dir=locale_dir, info=str(err))
        )
        return load_gettext_no_locale()

    translation.install(default_names_to_install)
    return translation
