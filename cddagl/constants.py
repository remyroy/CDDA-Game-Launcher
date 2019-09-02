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
        'released_on': '2019-03-08T04:22:54Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.D',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.D/cataclysmdda-0.D-8574-Win64-Tiles.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.D/cataclysmdda-0.D-8574-Win-Tiles.zip'
        }
    },
    '0.C': {
        'name': '0.C Cooper',
        'number': '2834',
        'released_on': '2015-03-09T16:21:48Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.C',
        'Tiles': {
            'x64': 'https://dev.narc.ro/cataclysm/jenkins-promoted/Windows_x64/Tiles/cataclysmdda-0.C-2834.zip',
            'x86': 'https://dev.narc.ro/cataclysm/jenkins-promoted/Windows_x64/Tiles/cataclysmdda-0.C-2834.zip'
        }
    }
}

STABLE_CHANGELOG = '''
<h3>0.D Danny</h3>
<p>The Danny release is characterized by MORE. More UI polish, more features, more content, more long-asked-for changes. It’s the longest-lived and largest in every way release we’ve ever done, and we hope to never do it again. Future releases are planned for roughly 6-month intervals. This release is made up of 37,604 commits authored by over 700 contributors, and it roughly doubled the number of everything in the game, items, monsters, map buildings, you name it, we doubled it.</p>
<p>It’s honestly way too huge to summarize in any meaningful way, but here are the absolute biggest changes, and you’ll just have to dig into the <a href="https://github.com/CleverRaven/Cataclysm-DDA/blob/de1858337072bf1af0bc89cbe1d9df7796a773af/data/changelog.txt">changelog</a> or the game itself for more detail.</p>
<ul>
  <li>Many quality of life enhancements such as auto-pulp, autopickup, batch actions, interacting with adjacent items and improved long-action handling.</li>
  <li>Pixel minimap for tiles mode.</li>
  <li>Guns accept magazines when appropriate.</li>
  <li>Player stamina stat that is burned by running and other physical exertion.</li>
  <li>Player faction base that allows incremental growth and autonomous work by NPCs.</li>
  <li>The player remembers terrain and furniture they have seen.</li>
  <li>Carrying racks for small vehicles.</li>
  <li>Vehicle system (speed, fuel consumption, terrain effects) overhaul.</li>
  <li>Overhauled nutrition, food spoilage and food state changes (freezing).</li>
  <li>Overhauled bomb fragment handling.</li>
  <li>NPC dialogue support, group commands, tactical instructions and backstories.</li>
  <li>Dynamic Lighting.</li>
  <li>Roughly DOUBLED the amount of in-game content.</li>
  <li>Unheard-of levels of bugfixing.</li>
  <li>Full translations for Chinese, German, Japanese, Polish and Russian.</li>
</ul>
<h3>0.C Cooper</h3>
<p>The Cooper release is named in honor of the new monster infighting system. Now you can sit back and watch as your enemies tear each other to pieces! Don’t get too close though, they’re still out for your blood.</p>
<ul>
  <li>This release also brings the long-requested DeathCam system, which lets you see the aftermath of the glorious fireball or atrocious train wreck that was your demise.</li>
  <li>Gun users will notice a new aiming menu: you can now spend time to steady your aim. Do you take the shot now, or wait until the zombie gets a little closer?</li>
  <li>Tailoring-oriented survivors (and who isn’t?) will note the new tailor’s kit item, which lets you add insulation or protective patches to your clothes.</li>
  <li>Survivors with gigantic death-mobiles may appreciate the new turret options, including being able to enable/disable individual turrets, and being able to fire some turrets manually.</li>
  <li>Finally, for survivors with, shall we say, “well-stocked” bases, there are massive improvements to performance when there are many thousands of items nearby.</li>
</ul>
'''

STABLE_SHA256 = {
    '2d7bbf426572e2b21aede324c8d89c9ad84529a05a4ac99a914f22b2b1e1405e': '0.C',
    '0454ed2bbc4a6c1c8cca5c360533513eb2a1d975816816d7c13ff60e276d431b': '0.D',
    '7f914145248cebfd4d1a6d4b1ff932a478504b1e7e4c689aab97b8700e079f61': '0.D'
}

CONFIG_BRANCH_KEY = 'branch'
CONFIG_BRANCH_STABLE = 'stable'
CONFIG_BRANCH_EXPERIMENTAL = 'experimental'


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
