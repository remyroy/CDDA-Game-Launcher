import os
import sys

from ctypes import *
from ctypes.wintypes import *
import functools

import win32file
from pywintypes import error as WinError

ntdll = WinDLL('ntdll')
kernel32 = WinDLL('kernel32')

PVOID       = c_void_p
PULONG      = POINTER(ULONG)
ULONG_PTR   = WPARAM
ACCESS_MASK = DWORD

VISTA_OR_LATER = sys.getwindowsversion()[0] >= 6

class EnumerationType(type(c_uint)):
    def __new__(metacls, name, bases, dict):
        if not "_members_" in dict:
            _members_ = {}
            for key,value in dict.items():
                if not key.startswith("_"):
                    _members_[key] = value
            dict["_members_"] = _members_
        cls = type(c_uint).__new__(metacls, name, bases, dict)
        for key,value in cls._members_.items():
            globals()[key] = value
        return cls

    def __contains__(self, value):
        return value in self._members_.values()

    def __repr__(self):
        return "<Enumeration %s>" % self.__name__


class Enumeration(c_uint):
    __metaclass__ = EnumerationType
    _members_ = {}
    def __init__(self, value):
        for k,v in self._members_.items():
            if v == value:
                self.name = k
                break
        else:
            raise ValueError("No enumeration member with value %r" % value)
        c_uint.__init__(self, value)
        

    @classmethod
    def from_param(cls, param):
        if isinstance(param, Enumeration):
            if param.__class__ != cls:
                raise ValueError("Cannot mix enumeration members")
            else:
                return param
        else:
            return cls(param)

    def __repr__(self):
        return "<member %s=%d of %r>" % (self.name, self.value, self.__class__)


@functools.total_ordering
class NTSTATUS(c_long):
    def __eq__(self, other):
        if hasattr(other, 'value'):
            other = other.value
        return self.value == other
    def __ne__(self, other):
        if hasattr(other, 'value'):
            other = other.value
        return self.value != other
    def __lt__(self, other):
        if hasattr(other, 'value'):
            other = other.value
        return self.value < other
    def __bool__(self):
        return self.value >= 0
    def __repr__(self):
        value = c_ulong.from_buffer(self).value
        return 'NTSTATUS(%08x)' % value

STATUS_SUCCESS = NTSTATUS(0x0)
STATUS_INVALID_HANDLE = NTSTATUS(0xC0000008)
STATUS_OBJECT_TYPE_MISMATCH = NTSTATUS(0xC0000024)
STATUS_INFO_LENGTH_MISMATCH = NTSTATUS(0xC0000004)
STATUS_ACCESS_DENIED = NTSTATUS(0xC0000022)

PROCESS_DUP_HANDLE = DWORD(0x0040)
PROCESS_QUERY_INFORMATION = DWORD(0x0400)
PROCESS_QUERY_LIMITED_INFORMATION = DWORD(0x1000)

def WinErrorFromNtStatus(status):
    last_error = ntdll.RtlNtStatusToDosError(status)
    return WinError(last_error)


class UNICODE_STRING(Structure):
    _fields_ = (('Length',          USHORT),
                ('MaximumLength',   USHORT),
                ('Buffer',          LPWSTR))


class GENERIC_MAPPING(Structure):
    _fields_ = (('GenericRead',     ACCESS_MASK),
                ('GenericWrite',    ACCESS_MASK),
                ('GenericExecute',  ACCESS_MASK),
                ('GenericAll',      ACCESS_MASK))


class SYSTEM_INFORMATION_CLASS(c_ulong):
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.value)

SystemExtendedHandleInformation = SYSTEM_INFORMATION_CLASS(64)


class  OBJECT_INFORMATION_CLASS(ULONG):
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.value)

ObjectBasicInformation = OBJECT_INFORMATION_CLASS(0)
ObjectNameInformation = OBJECT_INFORMATION_CLASS(1)
ObjectTypeInformation = OBJECT_INFORMATION_CLASS(2)


class SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX(Structure):
    _fields_ = (('Object',                PVOID),
                ('UniqueProcessId',       HANDLE),
                ('HandleValue',           HANDLE),
                ('GrantedAccess',         ACCESS_MASK),
                ('CreatorBackTraceIndex', USHORT),
                ('ObjectTypeIndex',       USHORT),
                ('HandleAttributes',      ULONG),
                ('Reserved',              ULONG))


class SYSTEM_INFORMATION(Structure):
    pass

PSYSTEM_INFORMATION = POINTER(SYSTEM_INFORMATION)


class SYSTEM_HANDLE_INFORMATION_EX(SYSTEM_INFORMATION):
    _fields_ = (('NumberOfHandles', ULONG_PTR),
                ('Reserved',        ULONG_PTR),
                ('_Handles', SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX * 1))
    @property
    def Handles(self):
        arr_t = (SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX *
                 self.NumberOfHandles)
        return POINTER(arr_t)(self._Handles)[0]


class POOL_TYPE(Enumeration):
    _members_ = {'NonPagedPool': 0,
                 'PagedPool': 1,
                 'NonPagedPoolMustSucceed': 2,
                 'DontUseThisType': 3,
                 'NonPagedPoolCacheAligned': 4,
                 'PagedPoolCacheAligned': 5,
                 'NonPagedPoolCacheAlignedMustS': 6}


class OBJECT_INFORMATION(Structure):
    pass

POBJECT_INFORMATION = POINTER(OBJECT_INFORMATION)


class OBJECT_TYPE_INFORMATION(OBJECT_INFORMATION):
    _fields_ = (('Name',                        UNICODE_STRING),
                ('TotalNumberOfObjects',        ULONG),
                ('TotalNumberOfHandles',        ULONG),
                ('TotalPagedPoolUsage',         ULONG),
                ('TotalNonPagedPoolUsage',      ULONG),
                ('TotalNamePoolUsage',          ULONG),
                ('TotalHandleTableUsage',       ULONG),
                ('HighWaterNumberOfObjects',    ULONG),
                ('HighWaterNumberOfHandles',    ULONG),
                ('HighWaterPagedPoolUsage',     ULONG),
                ('HighWaterNonPagedPoolUsage',  ULONG),
                ('HighWaterNamePoolUsage',      ULONG),
                ('HighWaterHandleTableUsage',   ULONG),
                ('InvalidAttributes',           ULONG),
                ('GenericMapping',              GENERIC_MAPPING),
                ('ValidAccess',                 ULONG),
                ('SecurityRequired',            BOOLEAN),
                ('MaintainHandleCount',         BOOLEAN),
                ('MaintainTypeList',            USHORT),
                ('PoolType',                    POOL_TYPE),
                ('PagedPoolUsage',              ULONG),
                ('NonPagedPoolUsage',           ULONG))


class PROCESS_INFO_CLASS(Enumeration):
    _members_ = {'ProcessBasicInformation': 0,
                 'ProcessDebugPort': 7,
                 'ProcessWow64Information': 26,
                 'ProcessImageFileName': 27,
                 'ProcessBreakOnTermination': 29}

ProcessImageFileName = PROCESS_INFO_CLASS(27)

ntdll.NtQuerySystemInformation.restype = NTSTATUS
ntdll.NtQuerySystemInformation.argtypes = (
    SYSTEM_INFORMATION_CLASS, # SystemInformationClass
    PSYSTEM_INFORMATION,      # SystemInformation
    ULONG,                    # SystemInformationLength
    PULONG)                   # ReturnLength

ntdll.NtDuplicateObject.restype = NTSTATUS
ntdll.NtDuplicateObject.argtypes = (
    HANDLE,         # SourceProcessHandle
    HANDLE,         # SourceHandle
    HANDLE,         # TargetProcessHandle
    PHANDLE,        # TargetHandle
    ACCESS_MASK,    # DesiredAccess
    ULONG,          # Attributes
    ULONG)          # Options

ntdll.NtQueryObject.restype = NTSTATUS
ntdll.NtQueryObject.argtypes = (
    HANDLE,                     # ObjectHandle,
    OBJECT_INFORMATION_CLASS,   # ObjectInformationClass,
    PVOID,                      # ObjectInformation,
    ULONG,                      # ObjectInformationLength,
    PULONG)                     # ReturnLength

ntdll.NtQueryInformationProcess.restype = NTSTATUS
ntdll.NtQueryInformationProcess.argtypes = (
    HANDLE,             # ProcessHandle
    PROCESS_INFO_CLASS, # ProcessInformationClass
    PVOID,              # ProcessInformation
    ULONG,              # ProcessInformationLength
    PULONG)             # ReturnLength

kernel32.OpenProcess.restype = HANDLE
kernel32.OpenProcess.argtypes = (
    DWORD,  # DesiredAccess
    BOOL,   # InheritHandle
    DWORD   # ProcessId
    )

kernel32.GetLastError.restype = DWORD
kernel32.GetCurrentProcess.restype = HANDLE
kernel32.CloseHandle.restype = BOOL

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

# Find the process which is using the file handle
def find_process_with_file_handle(path):
    # Check for drive absolute path
    if path[1:2] != ':':
        return None

    try:
        device_prefix = win32file.QueryDosDevice(path[:2])
    except WinError:
        return None
    device_path = device_prefix[:-2] + path[2:]

    pid = os.getpid()

    pid_handle = {}
    denied_pid = set()

    cphandle = kernel32.GetCurrentProcess()

    found_process = None

    for handle in list_handles():
        # Do no query handles with 0x0012019f GrantedAccess, it may hang
        # Only name pipes should have that GrantedAccess value
        if handle.GrantedAccess == 0x0012019f:
            continue

        # Skip handles in processes previously denied
        if handle.UniqueProcessId in denied_pid:
            continue

        # Get process handle
        phandle = pid_handle.get(handle.UniqueProcessId, None)
        if phandle is None:
            if VISTA_OR_LATER:
                desired_access = DWORD(PROCESS_DUP_HANDLE.value |
                    PROCESS_QUERY_LIMITED_INFORMATION.value)
            else:
                desired_access = DWORD(PROCESS_DUP_HANDLE.value |
                    PROCESS_QUERY_INFORMATION.value)
            phandle = kernel32.OpenProcess(desired_access, BOOL(False),
                handle.UniqueProcessId)
            if phandle is None:
                denied_pid.add(handle.UniqueProcessId)
                continue

        # Get a handle duplicate
        dup_handle = HANDLE()

        status = ntdll.NtDuplicateObject(
            phandle,
            handle.HandleValue,
            cphandle,
            byref(dup_handle),
            0,
            0,
            0)

        if status != STATUS_SUCCESS:
            continue
        
        # Query the object type
        buflen = 0x1000
        pobject_type_info = cast(create_string_buffer(buflen),
            POINTER(OBJECT_TYPE_INFORMATION))
        length = ULONG()
        status = ntdll.NtQueryObject(
            dup_handle,
            ObjectTypeInformation,
            pobject_type_info,
            buflen,
            byref(length))

        if status != STATUS_SUCCESS:
            kernel32.CloseHandle(dup_handle)
            continue

        # We are only looking for file handles
        if pobject_type_info.contents.Name.Buffer != 'File':
            kernel32.CloseHandle(dup_handle)
            continue

        # Query the object name
        buflen = 0x1000
        pobject_name = cast(create_string_buffer(buflen),
            POINTER(UNICODE_STRING))
        length = ULONG()
        while True:
            status = ntdll.NtQueryObject(
                dup_handle,
                ObjectNameInformation,
                pobject_name,
                buflen,
                byref(length))
            if status != STATUS_INFO_LENGTH_MISMATCH:
                break
            buflen = length.value
            pobject_name = cast(create_string_buffer(buflen),
                POINTER(UNICODE_STRING))
        
        if status != STATUS_SUCCESS:
            kernel32.CloseHandle(dup_handle)
            continue

        # Is this handle the file we are looking for?
        if device_path == pobject_name.contents.Buffer:
            # Get process path
            buflen = 0x1000
            pimage_file_name = cast(create_string_buffer(buflen),
                POINTER(UNICODE_STRING))
            length = ULONG()
            while True:
                status = ntdll.NtQueryInformationProcess(
                    phandle,
                    ProcessImageFileName,
                    pimage_file_name,
                    buflen,
                    byref(length))
                if status != STATUS_INFO_LENGTH_MISMATCH:
                    break
                buflen = length.value
                pimage_file_name = cast(create_string_buffer(buflen),
                    POINTER(UNICODE_STRING))

            if status != STATUS_SUCCESS:
                kernel32.CloseHandle(dup_handle)
                continue

            image_file_name = pimage_file_name.contents.Buffer
            if image_file_name.startswith(device_prefix[:-2]):
                image_file_name = path[:2] + image_file_name[
                    len(device_prefix) - 2:]
            else:
                devices = win32file.QueryDosDevice(None).split('\x00')
                letters = []
                for device in devices:
                    if (len(device) == 2
                        and device[-1] == ':'
                        and device != path[:2]):
                        letters.append(device)
                for letter in letters:
                    device_prefix = win32file.QueryDosDevice(letter)
                    if image_file_name.startswith(device_prefix[:-2]):
                        image_file_name = letter + image_file_name[
                            len(device_prefix) - 2:]
                        break

            found_process = {
                'pid': handle.UniqueProcessId,
                'image_file_name': image_file_name
            }
            kernel32.CloseHandle(dup_handle)
            break

        kernel32.CloseHandle(dup_handle)

    for phandle in pid_handle.values():
        kernel32.CloseHandle(phandle)

    return found_process