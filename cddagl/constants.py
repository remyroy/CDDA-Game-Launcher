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
CDDA_RELEASE_BY_TAG = lambda tag: f'/repos/CleverRaven/Cataclysm-DDA/releases/tags/{tag}'
CDDAGL_LATEST_RELEASE = '/repos/remyroy/CDDA-Game-Launcher/releases/latest'

NEW_ISSUE_URL = 'https://github.com/remyroy/CDDA-Game-Launcher/issues/new'

CDDA_ISSUE_URL_ROOT = 'https://github.com/CleverRaven/Cataclysm-DDA/issues/'
CDDA_COMMIT_URL_ROOT = 'https://github.com/CleverRaven/Cataclysm-DDA/commit/'
CDDAGL_ISSUE_URL_ROOT = 'https://github.com/remyroy/CDDA-Game-Launcher/issues/'

GAME_ISSUE_URL = 'https://cataclysmdda.org/#ive-found-a-bug--i-would-like-to-make-a-suggestion-what-should-i-do'

BUILD_TAG = lambda bn: f'cdda-jenkins-b{bn}'
NEW_BUILD_TAG = lambda bn: f'experimental-{bn}'

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

NEW_BASE_ASSETS = {
    'Tiles': {
        'x64': {
            'Platform': 'x64',
            'Graphics': 'tiles'
        },
        'x86': {
            'Platform': 'x32',
            'Graphics': 'tiles'
        }
    }
}

STABLE_ASSETS = {
    '0.F': {
        'name': '0.F Frank',
        'number': '2021-07-03-0512',
        'released_on': '2021-07-03T05:12:43Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.F/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F/cdda-windows-tiles-x64-2021-07-03-0512.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F/cdda-windows-tiles-x32-2021-07-03-0512.zip'
        }
    },
    '0.E-3': {
        'name': '0.E-3 Ellison-3',
        'number': '10478',
        'released_on': '2020-12-09T22:52:49Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.E-3/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E-3/cataclysmdda-0.E-Windows_x64-Tiles-0.E-3.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E-3/cataclysmdda-0.E-Windows-Tiles-0.E-3.zip'
        }
    },
    '0.E-2': {
        'name': '0.E-2 Ellison-2',
        'number': '10478',
        'released_on': '2020-05-20T12:21:59Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.E-2/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E-2/cataclysmdda-0.E-Windows_x64-Tiles-0.E-2.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E-2/cataclysmdda-0.E-Windows-Tiles-0.E-2.zip'
        }
    },
    '0.E-1': {
        'name': '0.E-1 Ellison-1',
        'number': '10478',
        'released_on': '2020-05-16T09:16:41Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.E-1/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E-1/cataclysmdda-0.E-Windows_x64-Tiles-0.E-1.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E-1/cataclysmdda-0.E-Windows-Tiles-0.E-1.zip'
        }
    },
    '0.E': {
        'name': '0.E Ellison',
        'number': '10478',
        'released_on': '2020-04-01T12:48:28Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.E',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E/cataclysmdda-0.E-Windows_x64-Tiles-10478.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.E/cataclysmdda-0.E-Windows-Tiles-10478.zip'
        }
    },
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
<h3>0.F Frank</h3>

<p>After a long and anticlimactic buildup, we are pleased to announce the release of stable version 0.F “Frank” of Cataclysm: Dark Days Ahead! Like our previous stable versions, this release features an expansive range of bugfixes, code and content additions, and new features. 4,500 new game entities were added, 123,162 lines of source code were inserted, and 77,727 lines were deleted.</p>

<p>The goal was to have a smaller and more manageable release this cycle, which was an utter failure, as it took well over a year and by several measures was even larger than the 0.E cycle.</p>

<p>We’d overall characterize 0.F as a release with a lot of content and polish. Compared to 0.E, you may find it a little more difficult (the pendulum swings ever back and forth), but we think also more rewarding. The most obvious feature of 0.F is the addition of nested inventory, the ability to store items in containers and have them behave as you’d expect. This is probably the most long awaited and highly requested feature of the past five years of development. Besides pockets, 0.F features the addition of achievements for fun and bragging rights, a proficiency system to represent more refined skill knowledge, blood loss mechanics for you and your enemies, weariness that builds as you push yourself to your limits, vehicles that can drive up and down z-levels (and bridges that are above rivers, enabling more navigable rivers, as a result), and a vast host of new content from new monsters and evolutions to new quests and items. On the mod side, Magiclysm, Aftershock, and Dinomod have all grown expansively, including new artifact and enchantment systems that have impacted content in the main game. And much more, too much to list here.</p>

<p>Players coming from the last stable will notice a switch towards encouraging looting over crafting, especially in the early game, and will have to be cautious about overextending themselves in the beginning of their survival effort. As usual, you’ll want to avoid getting into combat with multiple zombies in an open area. However, you can also have ‘grab bags’ of useful gear and tools, allowing you to toss your loot sack to the floor to engage in an unencumbered melee battle with zombies! All in all, as usual, we’re deeply excited about this new version, and look forward to continuing to make your survival difficult in the months to come.</p>

<p>Highlights</p>
<ul>
  <li>Nested Containers rationalize inventory management and enable dropping and retrieving go-bags during fights.</li>
  <li>Achievements track your deeds and misdeeds across games.</li>
  <li>Proficiencies better represent deeper knowledge required for various endeavors, mostly crafting.</li>
  <li>Bleeding added to both the player and monsters as the first step toward a more comprehensive wound and wound treatment system.</li>
  <li>Weariness tracking added to represent longer-term physical exhaustion.</li>
  <li>Elevated bridges over navigable rivers added, allowing better navigability while using boats.</li>
  <li>Large-scale audit of weapon and armor values for better representativeness and consistency.</li>
  <li>Improved armor handling by separating ballistic damage into its own damage type.</li>
  <li>Pervasive performance enhancements throughout the game.</li>
  <li>Tileset vehicle support for more cohesive vehicle rendering.</li>
  <li>Aftershock changes direction to a total conversion mod with a new far-future setting on a frozen world.</li>
  <li>Dinomod added 238 dinosaurs, pterosaurs, mosasaurs, and dino-related NPCs with missions and dino locations.</li>
  <li>Added many dino features, including zombie, fungal, evolved, bionic, baby, and mutant dino variants.</li>
  <li>Dinomod added many dino interactions, including farming, riding, butchering, cooking, and special attacks.</li>
  <li>Magiclysm added a huge content update including many new traits called Attunements that switch up gameplay at the endgame.</li>
</ul>

<p>For a larger, but still incomplete listing of features, see <a href="https://github.com/CleverRaven/Cataclysm-DDA/blob/0.F/data/changelog.txt">https://github.com/CleverRaven/Cataclysm-DDA/blob/0.F/data/changelog.txt</a></p>

<h3>0.E-3 Ellison-3</h3>
<p>Point release Ellison-3 includes following important bugfixes to original Ellison release:</p>
<ul>
  <li>fixed compilation under clang;
  <li>fixes for several errors and crashes;
  <li>fixed hardware keyboard issue in Android builds.
</ul>
<p>See differences between current point release and original release here - <a href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.E…0.E-3">0.E…0.E-3</a></p>

<h3>0.E-2 Ellison-2</h3>
<p>Point release Ellison-2 includes following important bugfixes to original Ellison release:</p>
<ul>
  <li>fixed virtual keyboard issue in Android builds.</li>
</ul>
<p>See differences between current point release and original release here - <a href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.E...0.E-2">0.E…0.E-2</a></p>

<h3>0.E-1 Ellison-1</h3>
<p>Point release Ellison-1 includes a number of following important bugfixes to original Ellison release:</p>
<ul>
  <li>fixes for several errors and crashes;</li>
  <li>savegame migration for obsolete items, recipes and overmap terrains;</li>
  <li>enhanced Android builds.</li>
</ul>
<p>See differences between current point release and original release here - <a href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.E…0.E-1">0.E…0.E-1</a></p>

<h3>0.E Ellison</h3>
<p>The Ellison release adds a huge number of features and content that make the world feel more alive. From being able to climb onto building rooftops or hide behind cars, to building a camp for your followers in the wilderness, to exploring the new river and lake systems on a boat or raft, everything is more immersive and consistent. Also more STUFF. I didn’t think we would ever double the number of game entities with a release again, but we did.</p>
<p>We aimed at a 6 month release cycle, and ended up spending 9 months adding features at a breakneck pace and 3 months putting the brakes on and stabilizing. I can’t honestly say that’s a huge disappointment, though toward the end the rest of the development team was really chomping at the bit to get back to feature work, so we’ll need to continue to adjust.</p>
<p>We built a huge amount of infrastructure for having the game check its own consistency, which has and is going to continue to contribute to the amazing pace of feature and content additions we are experiencing. The development team is also larger and at the same time more cohesive than it has ever been before.</p>
<p>Explore all the new features with the attached release archives. Speaking of exploring, the list of available tilesets has shuffled a bit, so this is a great time to find your new favorite.</p>
<ul>
  <li>Long distance automove feature for walking, driving and boating.</li>
  <li>Extensive bugfixes to inter-level interactivity, on by default.</li>
  <li>Riding animals and animal-pulled vehicles.</li>
  <li>More flexible Basecamp construction options.</li>
  <li>Default starting date changed to mid-spring for better survivability.</li>
  <li>Time advancement is rationalized, a turn is now one second.</li>
  <li>Extensive river and lake systems, and boat support for navigating them.</li>
  <li>Expanded NPC usefulness and interactivity.</li>
  <li>Massive increases in location variety and consistency, especially rooftops.</li>
  <li>Expansion of mi-go faction with new enemies and locations.</li>
  <li>Batteries now store charge instead of being pseudo-items.</li>
  <li>Overhaul and rebalance of martial arts.</li>
  <li>Zombie grabbing and biting more manageable and predictable.</li>
  <li>Overhauled stamina and damage recovery for grittier gameplay.</li>
  <li>Crouching movement mode allows hiding.</li>
  <li>Magiclysm and Aftershock mods have first class support within the game.</li>
</ul>
<p>Finally, see the changelog for the more complete (but still not comprehensive) listing of new features and contents <a href="https://github.com/CleverRaven/Cataclysm-DDA/blob/0.E/data/changelog.txt">https://github.com/CleverRaven/Cataclysm-DDA/blob/0.E/data/changelog.txt</a></p>

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
    '7f914145248cebfd4d1a6d4b1ff932a478504b1e7e4c689aab97b8700e079f61': '0.D',
    'bdd4f539767fd970beeab271e0e3774ba3022faeff88c6186b389e6bbe84bc75': '0.E',
    '8adea7b3bc81fa9e4594b19553faeb591846295f47b67110dbd16eed8b37e62b': '0.E',
    'fb7db2b3cf101e19565ce515c012a089a75f54da541cd458144dc8483b5e59c8': '0.E-1',
    '1068867549c1a24ae241a886907651508830ccd9c091bad27bacbefabab99acc': '0.E-1',
    '0ce61cdfc299661382e30da133f7356b4faea38865ec0947139a08f40b595728': '0.E-2',
    'c9ca51bd1e7549b0820fe736c10b3e73d358700c3460a0227fade59e9754e03d': '0.E-2',
    '563bd13cff18c4271c43c18568237046d1fd18ae200f7e5cdd969b80e6992967': '0.E-3',
    'e4874bbb8e0a7b1e52b4dedb99575e2a90bfe84e74c36db58510f9973400077d': '0.E-3',
    '1f5beb8b3dcb5ca1f704b816864771e2dd8ff38ca435a4abdb9a59e4bb95d099': '0.F',
    '2794df225787174c6f5d8557d63f434a46a82f562c0395294901fb5d5d10d564': '0.F'
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
