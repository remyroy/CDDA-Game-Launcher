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


def get_locale_path(*subpaths):
    return os.path.join(get_cddagl_path(), 'cddagl', 'locale', *subpaths)

def get_data_path(*subpaths):
    return os.path.join(get_cddagl_path(), 'data', *subpaths)
