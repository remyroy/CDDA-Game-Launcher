import gettext
import logging


logger = logging.getLogger(__name__)


def load_gettext_locale(locale_dir, locale, domain='cddagl'):
    """Load specified locale file into gettext for the application.

    Fallback to default untranslated strings if locale file is not found.
    """
    try:
        translation = gettext.translation(domain, localedir=locale_dir, languages=[locale])
    except FileNotFoundError as err:
        logger.warning(
            'Could not get translations for {locale} in {locale_dir}. Error: {info}'
            .format(locale=locale, locale_dir=locale_dir, info=str(err))
        )
        ### fallback translation
        translation = gettext.NullTranslations()

    translation.install(('gettext', 'ngettext'))
    return translation
