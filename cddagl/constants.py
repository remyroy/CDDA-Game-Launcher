MAX_LOG_SIZE = 1024 * 1024
MAX_LOG_FILES = 5

SAVES_WARNING_SIZE = 150 * 1024 * 1024

READ_BUFFER_SIZE = 16 * 1024

MAX_GAME_DIRECTORIES = 6

GITHUB_REST_API_URL = 'https://api.github.com'
GITHUB_API_VERSION = b'application/vnd.github.v3+json'

GITHUB_XRL_REMAINING = b'X-RateLimit-Remaining'
GITHUB_XRL_RESET = b'X-RateLimit-Reset'

CDDA_RELEASES = '/repos/CleverRaven/Cataclysm-DDA/releases'
CDDAGL_LATEST_RELEASE = '/repos/remyroy/CDDA-Game-Launcher/releases/latest'

NEW_ISSUE_URL = 'https://github.com/remyroy/CDDA-Game-Launcher/issues/new'

CHANGELOG_URL = 'http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/api/xml?tree=builds[number,timestamp,building,result,changeSet[items[msg]],runs[result,fullDisplayName]]&xpath=//build&wrapper=builds'
CDDA_ISSUE_URL_ROOT = 'https://github.com/CleverRaven/Cataclysm-DDA/issues/'
CDDAGL_ISSUE_URL_ROOT = 'https://github.com/remyroy/CDDA-Game-Launcher/issues/'

BUILD_CHANGES_URL = lambda bn: f'http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/{bn}/changes'

WORLD_FILES = set(('worldoptions.json', 'worldoptions.txt', 'master.gsav'))

FAKE_USER_AGENT = (b'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    b'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36')

TEMP_PREFIX = 'cddagl'

BASE_ASSETS = {
    'Tiles': {
        'x64': {
            'Platform': 'Windows_x64',
            'Graphics': 'Tiles'
        },
        'x86': {
            'Platform': 'Windows',
            'Graphics': 'Tiles'
        }
    },
    'Console': {
        'x64': {
            'Platform': 'Windows_x64',
            'Graphics': 'Curses'
        },
        'x86': {
            'Platform': 'Windows',
            'Graphics': 'Curses'
        },
    }
}

STABLE_ASSETS = {
    '0.D': {
        'name': '0.D Danny',
        'number': '8574',
        'date': '2019-03-08T04:22:54Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.D',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.D/cataclysmdda-0.D-8574-Win64-Tiles.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.D/cataclysmdda-0.D-8574-Win-Tiles.zip'
        }
    },
    '0.C': {
        'name': '0.C Cooper',
        'number': '2834',
        'date': '2015-03-09T16:21:48Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.C',
        'Tiles': {
            'x64': 'https://dev.narc.ro/cataclysm/jenkins-promoted/Windows_x64/Tiles/cataclysmdda-0.C-2834.zip',
            'x86': 'https://dev.narc.ro/cataclysm/jenkins-promoted/Windows_x64/Tiles/cataclysmdda-0.C-2834.zip'
        }
    }
}

STABLE_SHA256 = {
    '2d7bbf426572e2b21aede324c8d89c9ad84529a05a4ac99a914f22b2b1e1405e': '0.C',
    '0454ed2bbc4a6c1c8cca5c360533513eb2a1d975816816d7c13ff60e276d431b': '0.D',
    '7f914145248cebfd4d1a6d4b1ff932a478504b1e7e4c689aab97b8700e079f61': '0.D'
}


### Path to Dirs and Files used in CDDAGL
### TODO: (kurzed) centralize here and then move to a better place?
import sys
import os


def get_cddagl_path(*subpaths):
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        basedir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(basedir, *subpaths)


def get_resource_path(*subpaths):
    return os.path.join(get_cddagl_path(), 'cddagl', 'resources', *subpaths)


def get_locale_path(*subpaths):
    return os.path.join(get_cddagl_path(), 'cddagl', 'locale', *subpaths)


def get_data_path(*subpaths):
    return os.path.join(get_cddagl_path(), 'data', *subpaths)

def get_cdda_uld_path(*subpaths):
    """Returns path used for CDDA when 'Use the launcher directory as game directory' is set."""
    return os.path.join(get_cddagl_path(), 'cdda', *subpaths)
