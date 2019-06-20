import gettext
import logging


logger = logging.getLogger(__name__)

default_names_to_install = ('gettext', 'ngettext')


def load_gettext_no_locale():
    """Load gettext into the application using base strings (no translations)."""
    translation = gettext.NullTranslations()
    translation.install(default_names_to_install)
    return translation


def load_gettext_locale(locale_dir, locale, domain='cddagl'):
    """Load gettext into the application with specified locale file.

    Fallback to default untranslated strings if locale file is not found.
    """
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
