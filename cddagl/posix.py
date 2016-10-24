import os
import sys
import tempfile
import locale
import psutil

import posix_ipc
from posix_ipc import *

class PathNotFoundException(Exception): pass

def get_downloads_directory():
    return os.path.join(os.path.expanduser("~"), 'Downloads')

def list_handles():
    info = SYSTEM_HANDLE_INFORMATION_EX()
    length = ULONG()
    while True:
        status = ntdll.NtQuerySystemInformation(
            SystemExtendedHandleInformation,
            byref(info),
            sizeof(info),
            byref(length))
        if status != STATUS_INFO_LENGTH_MISMATCH:
            break
        resize(info, length.value)
    if status < 0:
        raise WinErrorFromNtStatus(status)
    return info.Handles

def process_id_from_path(path):
    lower_path = path.lower()

    for proc in psutil.process_iter():
        try:
            if proc.name() == lower_path:
                return proc
        except psutil.Error:
            pass

    return None

def wait_for_pid(pid):
    waitpid(pid, 0)

    return True

# Find the process which is using the file handle
def find_process_with_file_handle(path):
    for proc in psutil.process_iter():
        for open_file in proc.open_files():
            if open_file.path == path:
                return {
                    'pid': proc.pid,
                    'image_file_name': open_file.path
                }

    return None

def get_ui_locale():
    return locale.getdefaultlocale()[0]

def activate_window(pid):
    return True

def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


class SingleInstance:
    def __init__(self):
        # cddagl_{64394E79-7931-49CB-B8CF-3F4ECAE16B6C}
        self.mutexname = 'cddagl_{64394E79-7931}'
        self.lasterror = 0
        self.mutex = 0
        try:
            self.mutex = posix_ipc.Semaphore(self.mutexname, O_CREX)
        except ExistentialError:
            self.lasterror = 666
    
    def aleradyrunning(self):
        return (self.lasterror == 666)
    
    def close(self):
        if self.mutex:
            self.mutex.unlink()
            self.mutex = None

    def __del__(self):
        self.close()


class SimpleNamedPipe:
    def __init__(self, name):
        self.name = name
        self.filename = os.path.join(tempfile.gettempdir(), name)
        self.pipe = None
        self.create_pipe()

    def create_pipe(self):
        filename = self.filename;
        try:
            os.mkfifo(filename)
        except OSError as e:
            pass


    def connect(self):
        self.pipe = os.open(self.filename, os.O_RDONLY)
        return True
        
    def read(self, size):
        return os.read(self.pipe, size)

    def close(self):
        if self.pipe:
            self.pipe.close()
            os.remove(self.filename)
            self.pipe = None

    def __del__(self):
        self.close()

def write_named_pipe(name, value):
    pipe = None
    filename = os.path.join(tempfile.gettempdir(), name)
    try:
        os.mkfifo(filename)
        pipe = os.open(filename, os.O_WRONLY)
        os.write(pipe, value)
    except OSError as e:
        pass
    finally:
        if pipe:
            pipe.close()