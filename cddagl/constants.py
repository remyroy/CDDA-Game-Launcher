# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

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
CDDAGL_LATEST_RELEASE = '/repos/DazedNConfused-/CDDA-Game-Launcher/releases/latest'

NEW_ISSUE_URL = 'https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/new'

CDDA_ISSUE_URL_ROOT = 'https://github.com/CleverRaven/Cataclysm-DDA/issues/'
CDDA_COMMIT_URL_ROOT = 'https://github.com/CleverRaven/Cataclysm-DDA/commit/'
CDDAGL_ISSUE_URL_ROOT = 'https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/'

GAME_ISSUE_URL = 'https://cataclysmdda.org/#ive-found-a-bug--i-would-like-to-make-a-suggestion-what-should-i-do'

BUILD_TAG = lambda bn: f'cdda-jenkins-b{bn}'
NEW_BUILD_TAG = lambda bn: f'cdda-experimental-{bn}'

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
    '0.F-3': {
        'name': '0.F Frank-3',
        'number': '2021-11-27-1534',
        'released_on': '2021-11-27T15:34:00Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.F-3/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F-3/cataclysmdda-0.F-Windows_x64-Tiles-0.F-3.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F-3/cataclysmdda-0.F-Windows-Tiles-0.F-3.zip'
        }
    },
    '0.F-2': {
        'name': '0.F Frank-2',
        'number': '2021-08-31-2315',
        'released_on': '2021-08-31T13:36:46Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.F-2/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F-2/cataclysmdda-0.F-Windows_x64-Tiles-0.F-2.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F-2/cataclysmdda-0.F-Windows-Tiles-0.F-2.zip'
        }
    },
    '0.F-1': {
        'name': '0.F Frank-1',
        'number': '2021-08-14-0132',
        'released_on': '2021-08-14T01:32:00Z',
        'github_release': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/0.F-1/',
        'Tiles': {
            'x64': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F-1/cataclysmdda-0.F-Windows_x64-Tiles-0.F-1.zip',
            'x86': 'https://github.com/CleverRaven/Cataclysm-DDA/releases/download/0.F-1/cataclysmdda-0.F-Windows-Tiles-0.F-1.zip'
        }
    },
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
<h3>0.F-3 Frank-3</h3>

<p>Point release <strong>Frank-3</strong> includes following features and bugfixes backported to <a href="https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.F">original Frank release</a>:</p>
<ul>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="957276533" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50360" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50360/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50360">#50360</a> Handle window events during long operations</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="802539356" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/47253" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/47253/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/47253">#47253</a> Unlimited map memory</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="942749323" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/49906" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/49906/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49906">#49906</a> Return an invalid mm_submap if the map_memory is not prepared</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="940521528" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/49772" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/49772/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49772">#49772</a> Autodrive v2</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="964279857" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50637" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50637/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50637">#50637</a> Offroad autodrive</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="967665752" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50695" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50695/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50695">#50695</a> Overmap path fixes</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="966027636" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50670" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50670/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50670">#50670</a> Make autowalk more like autodrive</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="971055467" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50803" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50803/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50803">#50803</a> Render one frame per turn during autodrive</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="971559153" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50835" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50835/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50835">#50835</a> Improved overmap pathfinding in 3D</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="986335515" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51312" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51312/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51312">#51312</a> Update 0.F translations</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1000837265" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51742" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51742/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51742">#51742</a> Update 0.F translations</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1064260888" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/53037" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/53037/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/53037">#53037</a> Update 0.F translations</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="941333977" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/49828" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/49828/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49828">#49828</a> Fix health test</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="946978047" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50021" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50021/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50021">#50021</a> Translate monster death function messages</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="970766593" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50760" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50760/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50760">#50760</a> Fix for WEBWALK flag</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="971493914" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50834" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50834/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50834">#50834</a> Added fruit as a material in fruit wine</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="974099850" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50881" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50881/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50881">#50881</a> Silence warnings reported from inside SDL header</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="975902117" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50933" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/50933/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50933">#50933</a> Fix siphon from and fill to the same tank</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="979749987" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51086" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51086/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51086">#51086</a> In crafting every tool is displayed only once</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="979915909" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51096" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51096/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51096">#51096</a> Prevent inserting an item with NO_UNWIELD into a container</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="980193181" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51100" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51100/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51100">#51100</a> Fix clerical errors about Demihuman</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="981301861" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51124" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51124/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51124">#51124</a> Street facing churches</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="981495700" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51129" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51129/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51129">#51129</a> Fix infinitely falling vehicle</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="981521778" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51131" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51131/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51131">#51131</a> Adds missing knives to the Krav Maga list</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="981624737" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51136" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51136/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51136">#51136</a> Fix spammy warning in string_formatter.h when using clang on Windows</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="982056973" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51199" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51199/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51199">#51199</a> Fix horde indicators showing in elements outside of sidebar overmap</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="982133675" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51205" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51205/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51205">#51205</a> A few microoptimizations</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="982275409" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51220" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51220/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51220">#51220</a> Ice cream is edible frozen</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="982384501" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51226" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51226/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51226">#51226</a> Fix choppy vehicle animation</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="982409512" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51227" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51227/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51227">#51227</a> Fix: inedible MELTS while FROZEN (milkshake)</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="983368021" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51250" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51250/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51250">#51250</a> Capping shakes duration to prevent month-long shakes after withdrawal is gone</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="983653532" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51257" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51257/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51257">#51257</a> Allow multitile sprites to be animated</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="983922675" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51262" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51262/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51262">#51262</a> Fix sealed containers being targets for pickup actions</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="984462530" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51275" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51275/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51275">#51275</a> Iridescent cats now visible at night</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="984909638" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51282" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51282/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51282">#51282</a> Invalidate weight carried cache</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="985151290" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51287" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51287/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51287">#51287</a> Animated background</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="985511239" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51295" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51295/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51295">#51295</a> Limit zombie_fuse, other size change to within tiny-huge</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="987184242" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51319" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51319/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51319">#51319</a> Fixed Filter Paper Always Hitting</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="988332037" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51362" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51362/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51362">#51362</a> Add DESTROYS, PUSH_MON to albertosaurus</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="988410424" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51381" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51381/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51381">#51381</a> Fix NC_JUNK_SHOPKEEP item list</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="988424134" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51385" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51385/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51385">#51385</a> Fix bug when grabbing a vehicle</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="988608201" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51406" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51406/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51406">#51406</a> Make Gozu and Amigara yield demihuman meat</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="988608930" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51407" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51407/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51407">#51407</a> Workaround for heavy slowdown caused by eager evaluation of debug message strings</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="988626107" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51411" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51411/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51411">#51411</a> Adjust cannibal trait cost</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="989450214" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51439" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51439/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51439">#51439</a> Display name of loaded ammo instead of ammo type</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="989472188" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51441" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51441/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51441">#51441</a> If want successful test output, include messages</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="989523932" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51447" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51447/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51447">#51447</a> Change item list highlight color to white</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="990322608" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51458" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51458/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51458">#51458</a> Add the "mayfail" flag to the fire spreading test</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="990461952" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51460" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51460/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51460">#51460</a> Actually throttle monster thinking</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="992808518" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51498" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51498/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51498">#51498</a> Make paper soft so it will fit in small pockets</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="993737529" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51519" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51519/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51519">#51519</a> Fix poppies unharvestable in Dark Skies mod</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="993854453" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51524" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51524/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51524">#51524</a> Fix eating demihuman not affecting morale</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="993890958" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51529" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51529/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51529">#51529</a> Make monster::power_rating() use is_ranged_attacker()</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="994475319" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51580" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51580/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51580">#51580</a> Fix stair navigation</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1000269514" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51710" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51710/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51710">#51710</a> Reset whitelist flag on scenario blacklist reset</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1000274815" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51711" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51711/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51711">#51711</a> Reset scenarios unconditionally</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1001657043" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51754" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51754/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51754">#51754</a> Fix: Force stereo when opening audio device</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1007525086" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/51911" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/51911/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51911">#51911</a> Don't allow swapping places with NPC while grabbing something</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1012629397" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52010" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52010/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52010">#52010</a> Fix insect flesh vitamins</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1014251053" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52063" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52063/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52063">#52063</a> Fix NPCs cannot climb chickenwire fences but players can</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1017414553" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52133" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52133/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52133">#52133</a> Verify font can be rendered successfully at runtime</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1021755900" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52197" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52197/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52197">#52197</a> Fix crash when getting related recipes with no components and results for current recipe</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1022442055" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52243" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52243/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52243">#52243</a> Add missing translation in aiming UI</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1022601311" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52247" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52247/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52247">#52247</a> Fix compile errors on LLVM/Clang 13</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1023698930" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52257" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52257/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52257">#52257</a> Fragile television</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1026521662" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52289" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52289/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52289">#52289</a> Add omitted translation calls</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1029839291" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52356" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52356/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52356">#52356</a> Add more missing translations</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1034240117" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52413" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52413/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52413">#52413</a> Fix tabbing in character creation saving info</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1040984542" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52580" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52580/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52580">#52580</a> Fix an untranslated message in ATM deposit menu</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1043681227" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52612" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52612/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52612">#52612</a> Fix more untranslated messages</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1046070650" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52656" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52656/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52656">#52656</a> Fix compile error on LLVM/Clang 13</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1054417195" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/52847" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/52847/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/52847">#52847</a> Remove duplicate ATM spawn from movie theater palette</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1063232270" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/53019" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/53019/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/53019">#53019</a> Fix pathfinding hash functions for 32-bit systems</li>
<li><a class="issue-link js-issue-link" data-error-text="Failed to load title" data-id="1064950063" data-permission-text="Title is private" data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/53056" data-hovercard-type="pull_request" data-hovercard-url="/CleverRaven/Cataclysm-DDA/pull/53056/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/pull/53056">#53056</a> backporting tilesets from I-am-Erk/CDDA-Tilesets to 0.F</li>
</ul>
<p>Two major features were backported - unlimited map memory and autodrive v2.</p>
<p>There is also significant update of translations:</p>
<ul>
<li><strong>Japanese [100% translated]</strong> (<em>+172 lines</em>);</li>
<li><strong>Russian [100% translated]</strong> (<em>+297 lines</em>);</li>
<li><strong>Simplified Chinese [100% translated]</strong> (<em>+191 lines</em>);</li>
<li><strong>Spanish (Argentina) [100% translated]</strong> (<em>+180 lines</em>);</li>
<li><strong>Spanish (Spain) [100% translated]</strong> (<em>+185 lines</em>);</li>
<li>Polish (<em>+7,475 lines</em>) - most noticeable progress (up from 53% translated in <code>0.F-2</code> to 82% translated in <code>0.F-3</code>);</li>
<li>Hungarian (<em>+4,084 lines</em>);</li>
<li>Italian (Italy) (<em>+2,190 lines</em>);</li>
<li>Traditional Chinese (<em>+1,020 lines</em>);</li>
<li>Czech (<em>+952 lines</em>);</li>
</ul>
<p>And there are also some minor updates in translations to Indonesian, German, Ukrainian (Ukraine), French, Portuguese (Brazil), Danish, Dutch, Icelandic, Korean, Norwegian and Turkish.</p>
<p>Tilesets were also updated to latest available versions.</p>
<p>See differences between current point release and original release here - <a class="commit-link" href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F...0.F-3"><tt>0.F...0.F-3</tt></a></p>
<p>See differences between current point release and previous point release here - <a class="commit-link" href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F-2...0.F-3"><tt>0.F-2...0.F-3</tt></a></p>

<h3>0.F-2 Frank-2</h3>

<p>Point release Frank-2 includes following bugfixes backported to <a href="https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.F">original Frank release</a>:</p>

<ul>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50877">#50877</a> Catch SecurityException in SDL getSerialNumber</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50452">#50452</a> Fix dropping worn items from AIM</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50814">#50814</a> Prevent endless loop during butchering</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51035">#51035</a> Resolve a bug in partial stack dropping/using and unify ui behaviour</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/51147">#51147</a> Fix crash resulting from NPC activity migration (loading 0.F saves)</li>
</ul>

<p>See differences between current point release and original release here - <a href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F...0.F-2">https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F…0.F-2</a></p>

<p>See differences between current point release and previous point release here - <a href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F-1...0.F-2">https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F-1…0.F-2</a></p>

<h3>0.F-1 Frank-1</h3>

<p>Point release <strong>Frank-1</strong> includes following bugfixes backported to <a href="https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/0.F">original Frank release</a>:</p>
<ul>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49538">#49538</a> Fix welding requirement on some recipes</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50534">#50534</a> Fix overmap NPC names showing for NPCs out of range</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50173">#50173</a> Fix manually assigned item letter being removed on unwield</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49396">#49396</a> Fix classic zombies map extras chance values which could cause debugmsg</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49537">#49537</a> Fix incorrect conditional name of smoked wasteland sausage</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49543">#49543</a> Only apply disabled effect for main bodyparts</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48607">#48607</a> Mapgen road connections improved in the absence of overmap cities</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49211">#49211</a> Add lesser magic items to pawn and hunting itemgroups</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49565">#49565</a> Add version to debugmsg</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49568">#49568</a> Add back legacy wheel definitions</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48882">#48882</a> Fix magiclysm 1L V-Twin Engine has infinite fuel</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49589">#49589</a> Migrate legacy wheels and fix memory corruption in vehicle deserialization</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49401">#49401</a> Chitin Leg Guards and Tails</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49631">#49631</a> Add the missing door in private resort</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49597">#49597</a> Allow a region overlay to set all weights to zero</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49715">#49715</a> Update monster_attacks.json</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49628">#49628</a> Update keg description to no longer errorneously suggest they can be used for fermenting</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49741">#49741</a> Fix:Ninjutsu martial art does incorrect damage due to multiplicative …</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49690">#49690</a> Fix typo in stone.json</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49421">#49421</a> Change time to install oars from 60 m to 60 s</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49599">#49599</a> Prophylactic antivenom pills rename</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49622">#49622</a> Make Tallon Mutation allow fingerless gloves</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49577">#49577</a> Fix orc village's name</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/45787">#45787</a> Lowered encumbrance and tweaked belts</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49559">#49559</a> Add belt clip ability to webbing belt</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49534">#49534</a> Made Tea batch crafting mod equal to boiling plain water</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49513">#49513</a> Fix Cut Logs faction camp mission difficulty disp.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49318">#49318</a> Ignore pocket settings when manually inserting stackable items</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49550">#49550</a> Colt Delta Damage</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49734">#49734</a> Reduce solder in electronics control unit from 150 to 40</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49303">#49303</a> Adjust Burrowing mutation's description/effects</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48637">#48637</a> Fix fur/scales loop in Chimera</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49596">#49596</a> Roof and general improvements for orchard_apple</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48827">#48827</a> Replace MREs with itemgroups</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49512">#49512</a> Reworked brewing, now with merge conflicts resolved</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48960">#48960</a> Fix various meaty comestibles' vitamin values</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49760">#49760</a> Improve error message re armor portions</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49380">#49380</a> 10mm adheres to GAME_BALANCE.md</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49109">#49109</a> fix feints and lightly clean up some miss recovery and grab break code;</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/47986">#47986</a> Populated Bone Skewers into recipes, made Skewers millable</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49762">#49762</a> Change recipe sort to difficulty, name, crafting time</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49279">#49279</a> Remove additional spawns from Wander Hordes</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/45584">#45584</a> Balance tactical helmets</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49759">#49759</a> Fix CBM install data retrieval when installing CBM on NPC</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49778">#49778</a> Force place_special_forced to place special in forced mode</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49799">#49799</a> Fix healthy rounding bug</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49758">#49758</a> Make cooking oil unhealthy</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49794">#49794</a> Move workshop toolbox recipe to containers tab</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49751">#49751</a> Correct monster_size_capacity to creature_size_capacity</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48651">#48651</a> [Magiclysm] Can't cast if Stunned</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48078">#48078</a> [Magiclysm] Add mutations to manatouched</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49844">#49844</a> Correct the plural name of 'mana infused blood'</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48746">#48746</a> [Magiclysm] Leprechaun adjustments</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49217">#49217</a> [Magiclysm] More magical loot in wizard towers</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49729">#49729</a> Sword cane should fit in the hollow cane</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49764">#49764</a> Reordered magazine type for M17/M18</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49613">#49613</a> Changed time and energy to create a washboard.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49871">#49871</a> Makes flammable arrow components reflect the damage.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49883">#49883</a> Increased volume and length of western holster to accommodate other revolvers (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/48532" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/48532/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/48532">#48532</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49861">#49861</a> fix meatarian/vegetarian text</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49805">#49805</a> Fix weight of wild yeast</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49904">#49904</a> Fix weapons dropping without message on reload</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49934">#49934</a> Allow MISSION_FREE_MERCHANTS_HUB_DELIVERY_1 to complete after player has already met HUB-01</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49946">#49946</a> Remove TRADER_AVOID flag from mre containers</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49931">#49931</a> Hide vehicle UI when pouring on the ground</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49962">#49962</a> fixed reload times of guns</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49442">#49442</a> Change Hobo Stove to deployable furniture</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49997">#49997</a> Use positional arguments for 'It should take %d minutes to finish washing items in the %s.'</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50003">#50003</a> Chainlink fence posts now require pipe fittings to build</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48662">#48662</a> When telling NPCs to read something, include all columns in the 'choose a book' popup</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50032">#50032</a> Changed Humvee jerrycans to use JP8 fuel (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50008" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/50008/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/50008">#50008</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49995">#49995</a> Fix ammo capitalization</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49919">#49919</a> [Dinomod] Duplicate entry caused CTD</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49879">#49879</a> Dogs zombify</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49957">#49957</a> Improve chance to find hidden lab in MISSION_SCIENCE_REP_3</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48930">#48930</a> Butchering use best tool in crafting radius</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49377">#49377</a> Prevent overmap mongroups from spawning on top of faction bases</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50043">#50043</a> Hatchets aren't melee durable</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49949">#49949</a> Prevent UB passing 0 to LIGHT_RANGE</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50044">#50044</a> Change stone chopper requirement from fab (3) to fab (2) to resolve crafting bottleneck.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50061">#50061</a> Changed morphine description to naturally occurring drug (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/48710" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/48710/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/48710">#48710</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50053">#50053</a> Require hemostatic powder to require <em>powdered</em> chitin only.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50006">#50006</a> vehicles: helicopters do not have 100% load in idle()</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50086">#50086</a> Update cordage and cordage ropes crafting time.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50096">#50096</a> Added batch cook times to Granola and Cookies (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50089" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/50089/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/50089">#50089</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50046">#50046</a> Recompute overmap::safe_at_worldgen during unserialize()</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50114">#50114</a> Fix disappearance of CRIT vest on activation</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48462">#48462</a> Colorize spells in spellbooks</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/47257">#47257</a> Stand up peek</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48794">#48794</a> Ability to configure user-defined map extra symbols</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50074">#50074</a> Check skill requirements for vehicle most_repairable_part</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50165">#50165</a> Added condom to item restriction on travel wallet (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/49932" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/49932/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/49932">#49932</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50182">#50182</a> Fix wind not updating</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50134">#50134</a> Modified mass ratio of sheep wool on harvest to give similar to shearing returns (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/48962" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/48962/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/48962">#48962</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50180">#50180</a> Fix multitile variations</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50132">#50132</a> Fix armor pen from martial arts buffs not working</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49595">#49595</a> Target to Mac OS X 10.12+ in release build workflow</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49593">#49593</a> Raise the proportional AP value of handloaded 5.7mm</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50107">#50107</a> [Aftershock] Increase volume/weight of lichen, fix processing not neutralizing toxins</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50170">#50170</a> Add permeable flag to appropriate windows</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50243">#50243</a> Add Boxing to Self-Defense Classes</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49769">#49769</a> Remove CROWS turrets from irradiator overmap special</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50184">#50184</a> [DinoMod] wilderness spawn counts and fixes</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50230">#50230</a> Bondage mask layer mismatch</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50272">#50272</a> Display kicking monster name</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50222">#50222</a> Fix layer ordering of demon skin</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50216">#50216</a> ASCII tileset QoL changes</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/49953">#49953</a> Serialize moves_total</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/48864">#48864</a> Don't add magazines to all guns, don't show '(empty)' on unreloadable guns.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50100">#50100</a> Fix resuming mass disassembly not working</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50403">#50403</a> fix strong stomach granting nausea immunity</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50172">#50172</a> Reduce River weight to under 1k</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50251">#50251</a> Fix NPC claiming to eat FROZEN food without EDIBLE_FROZEN flag</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50381">#50381</a> Prevent stacking AIM windows when moving NO_UNWIELD flagged items</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50401">#50401</a> Change armored car to use JP8 (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50252" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/50252/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/50252">#50252</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50309">#50309</a> Added barred window with no glass (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/48453" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/48453/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/48453">#48453</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50174">#50174</a> Modified stained glass description to reflect the fact it is a wall with a high window, changed all external walls to stone walls for cathedral (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/49440" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/49440/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/49440">#49440</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50353">#50353</a> Fixed safe spawning on top of shrub in one of the houses</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50416">#50416</a> set number to 1 if no charges</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50240">#50240</a> Fix inconsistencies on all sleeveless dusters</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50371">#50371</a> Update Crowbars with DURABLE_MELEE</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50443">#50443</a> [DinoMod] dinos don't hear great</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50000">#50000</a> Bugfixes 'Port fix for 'phantom fuel' from Cataclysm-BN'</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50460">#50460</a> Modified the Batwing Zombie Description (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50383" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/50383/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/50383">#50383</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50536">#50536</a> Fishing spears can be stored in spear strap</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50543">#50543</a> Avoid division-by-zero in lerped_multiplier</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50525">#50525</a> Fixes crash during save due to invalid ammo_location</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50508">#50508</a> Balance 'Rebar cage breaks into concrete floor, not pit'</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50471">#50471</a> Atomic headlamp should not have DURABLE_MELEE</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50556">#50556</a> Make ironshod quarterstaff looks like quarterstaff</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50555">#50555</a> Add missing dot and the end of the sencence</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50487">#50487</a> Audit lawn mower length</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50448">#50448</a> Prevent display of martial arts traits as traits</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50550">#50550</a> Avoid placing hospitals in the woods during MISSION_SCIENCE_REP_1</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50564">#50564</a> cmake: don't use PREFIX variable</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50562">#50562</a> cmake: install core and help directories</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50528">#50528</a> random cosmetic traits respect scenario (<a data-url="https://github.com/CleverRaven/Cataclysm-DDA/issues/50224" data-hovercard-type="issue" data-hovercard-url="/CleverRaven/Cataclysm-DDA/issues/50224/hovercard" href="https://github.com/CleverRaven/Cataclysm-DDA/issues/50224">#50224</a>)</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50385">#50385</a> Spawn correct underwear for female True Foodperson</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50494">#50494</a> Fix the mission 'Visit the Isherwoods' that was impossible to complete</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50478">#50478</a> Clarify the mission descriptions in the pizzaiolo quest line</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50588">#50588</a> Fix the wooden privacy gate name</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50581">#50581</a> cmake: set RELEASE variable to generate install target</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50546">#50546</a> Avoid crashing when the player's gun is destroyed while firing.</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50607">#50607</a> Fixed density of legume products</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50598">#50598</a> Camp NPCs will refuse to eat inedible animal food</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50602">#50602</a> Add a crafting recipe for skirts</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50601">#50601</a> Fix Bathroom scale symbol</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50620">#50620</a> iwyu cuboid_rectangle.h</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50616">#50616</a> Add repairs_like to runner pack</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50618">#50618</a> Billous Soldier Zombie acid-attack description fix</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50610">#50610</a> Fix duplicate unitfont.ttf in config/fonts.json</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50609">#50609</a> Disable Terminus.ttf on Mac</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50606">#50606</a> Backport BN's MSVC sound fix</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50547">#50547</a> Do not remove vehicle label when canceling input</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50646">#50646</a> Recolor the blackjack oak</li>
<li><a href="https://github.com/CleverRaven/Cataclysm-DDA/pull/50577">#50577</a> Fixed unpack leaving containers invalid</li>
</ul>
<p>See differences between current point release and original release here - <a class="commit-link" href="https://github.com/CleverRaven/Cataclysm-DDA/compare/0.F...0.F-1"><tt>0.F...0.F-1</tt></a></p>

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

# certutil -hashfile "<main_cdda_executable_file>" SHA256
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
    '2794df225787174c6f5d8557d63f434a46a82f562c0395294901fb5d5d10d564': '0.F',
    '960140f7926267b56ef6933670b7a73d00087bd53149e9e63c48a8631cfbed53': '0.F-1',
    'c87f226d8b4e6543fbc8527d645cf4342b5e1036e94e16920381d7e5b5b9e34f': '0.F-1',
    '5da7ebd7ab07ebf755e445440210309eda0ae8f5924026d401b9eb5c52c5b6e7': '0.F-2',
    '6870353e6d142735dfd21dec1eaf6b39af088daf5eef27b02e53ebb1c9eca684': '0.F-2',
    '59404eeb88539b20c9ffbbcbe86a7e5c20267375975306245862c7fb731a5973': '0.F-3',
    '3e0b15543015389c34ad679a931186a1264dbccb010b813f63b6caef2d158dc8': '0.F-3'
}

CONFIG_BRANCH_KEY = 'branch'
CONFIG_BRANCH_STABLE = 'stable'
CONFIG_BRANCH_EXPERIMENTAL = 'experimental'

DURATION_FORMAT = '{D:02}d {H:02}h {M:02}m {S:02}s'

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
