import logging
import os
import re
import traceback
from io import StringIO

import winutils
from pywintypes import com_error

import cddagl
from cddagl.i18n import proxy_gettext as _
from cddagl.sql.functions import get_config_value, config_true

version = cddagl.__version__
logger = logging.getLogger('cddagl')


def log_exception(extype, value, tb):
    tb_io = StringIO()
    traceback.print_tb(tb, file=tb_io)

    logger.critical(_('Global error:\nLauncher version: {version}\nType: '
                      '{extype}\nValue: {value}\nTraceback:\n{traceback}').format(
        version=cddagl.__version__, extype=str(extype), value=str(value),
        traceback=tb_io.getvalue()))

def ensure_slash(path):
    """Return path making sure it has a trailing slash at the end."""
    return os.path.join(path, '')

def unique(seq):
    """Return unique entries in a unordered sequence while original order."""
    seen = set()
    for x in seq:
        if x not in seen:
            seen.add(x)
            yield x

def clean_qt_path(path):
    return path.replace('/', '\\')

def safe_filename(filename):
    keepcharacters = (' ', '.', '_', '-')
    return ''.join(c for c in filename if c.isalnum() or c in keepcharacters
        ).strip()

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return arstrip([tryint(c) for c in re.split('([0-9]+)', s)])

def arstrip(value):
    while len(value) > 1 and value[-1:] == ['']:
        value = value[:-1]
    return value

def is_64_windows():
    return 'PROGRAMFILES(X86)' in os.environ

def bitness():
    if is_64_windows():
        return _('64-bit')
    else:
        return _('32-bit')

def sizeof_fmt(num, suffix=None):
    if suffix is None:
        suffix = _('B')
    for unit in ['', _('Ki'), _('Mi'), _('Gi'), _('Ti'), _('Pi'), _('Ei'),
        _('Zi')]:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, _('Yi'), suffix)

def delete_path(path):
    ''' Move directory or file in the recycle bin (or permanently delete it
    depending on the settings used) using the built in Windows File
    operations dialog
    '''

    # Make sure we have an absolute path first
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    shellcon = winutils.shellcon

    permanently_delete_files = config_true(
        get_config_value('permanently_delete_files', 'False'))

    if permanently_delete_files:
        flags = 0
    else:
        flags = shellcon.FOF_ALLOWUNDO

    flags = (flags |
        shellcon.FOF_SILENT |
        shellcon.FOF_NOCONFIRMATION |
        shellcon.FOF_WANTNUKEWARNING
        )

    try:
        return winutils.delete(path, flags)
    except com_error:
        return False

def move_path(srcpath, dstpath):
    ''' Move srcpath to dstpath using using the built in Windows File
    operations dialog
    '''

    # Make sure we have absolute paths first
    if not os.path.isabs(srcpath):
        srcpath = os.path.abspath(srcpath)
    if not os.path.isabs(dstpath):
        dstpath = os.path.abspath(dstpath)

    shellcon = winutils.shellcon

    flags = (
        shellcon.FOF_ALLOWUNDO |
        shellcon.FOF_SILENT |
        shellcon.FOF_NOCONFIRMMKDIR |
        shellcon.FOF_NOCONFIRMATION |
        shellcon.FOF_WANTNUKEWARNING
        )

    try:
        return winutils.move(srcpath, dstpath, flags)
    except com_error:
        return False

def safe_humanize(arrow_date, other=None, locale='en_us', only_distance=False, granularity='auto'):
    try:
        # Can we use the normal humanize method?
        return arrow_date.humanize(other=other, locale=locale, only_distance=only_distance,
            granularity=granularity)
    except ValueError:
        # On first fail, let's try with day granularity
        try:
            return arrow_date.humanize(other=other, locale=locale, only_distance=only_distance,
                granularity='day')
        except ValueError:
            # On final fail, use en_us locale which should be translated
            return arrow_date.humanize(other=other, locale='en_us', only_distance=only_distance,
                granularity='auto')