# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import os
import sys

from ctypes import *
from ctypes.wintypes import *
import functools

from uuid import UUID

import win32file
import win32gui
import win32process
import win32api
import win32event
import win32pipe
import win32con

from pywintypes import error as WinError

import locale

from win32com.shell import shell, shellcon

from winerror import ERROR_ALREADY_EXISTS

ntdll = WinDLL('ntdll')
kernel32 = WinDLL('kernel32')
psapi = WinDLL('psapi.dll')

PVOID       = c_void_p
PULONG      = POINTER(ULONG)
ULONG_PTR   = WPARAM
ACCESS_MASK = DWORD

SW_SHOWNORMAL = 1
MAX_PATH = 260

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

SYNCHRONIZE = DWORD(0x00100000)
PROCESS_DUP_HANDLE = DWORD(0x0040)
PROCESS_QUERY_INFORMATION = DWORD(0x0400)
PROCESS_QUERY_LIMITED_INFORMATION = DWORD(0x1000)
PROCESS_VM_READ = DWORD(0x0010)

INFINITE = DWORD(0xFFFFFFFF)

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
    DWORD)  # ProcessId


kernel32.WaitForSingleObject.restype = DWORD
kernel32.WaitForSingleObject.argtypes = (
    HANDLE, # hHandle
    DWORD)  # dwMilliseconds

kernel32.GetLastError.restype = DWORD
kernel32.GetCurrentProcess.restype = HANDLE
kernel32.CloseHandle.restype = BOOL


class GUID(Structure):   # [1]
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8)
    ]

    def __init__(self, uuid_):
        Structure.__init__(self)
        self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1], rest = uuid_.fields
        for i in range(2, 8):
            self.Data4[i] = rest>>(8 - i - 1)*8 & 0xff

class FOLDERID:     # [2]
    AccountPictures         = UUID('{008ca0b1-55b4-4c56-b8a8-4de4b299d3be}')
    AdminTools              = UUID('{724EF170-A42D-4FEF-9F26-B60E846FBA4F}')
    ApplicationShortcuts    = UUID('{A3918781-E5F2-4890-B3D9-A7E54332328C}')
    CameraRoll              = UUID('{AB5FB87B-7CE2-4F83-915D-550846C9537B}')
    CDBurning               = UUID('{9E52AB10-F80D-49DF-ACB8-4330F5687855}')
    CommonAdminTools        = UUID('{D0384E7D-BAC3-4797-8F14-CBA229B392B5}')
    CommonOEMLinks          = UUID('{C1BAE2D0-10DF-4334-BEDD-7AA20B227A9D}')
    CommonPrograms          = UUID('{0139D44E-6AFE-49F2-8690-3DAFCAE6FFB8}')
    CommonStartMenu         = UUID('{A4115719-D62E-491D-AA7C-E74B8BE3B067}')
    CommonStartup           = UUID('{82A5EA35-D9CD-47C5-9629-E15D2F714E6E}')
    CommonTemplates         = UUID('{B94237E7-57AC-4347-9151-B08C6C32D1F7}')
    Contacts                = UUID('{56784854-C6CB-462b-8169-88E350ACB882}')
    Cookies                 = UUID('{2B0F765D-C0E9-4171-908E-08A611B84FF6}')
    Desktop                 = UUID('{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}')
    DeviceMetadataStore     = UUID('{5CE4A5E9-E4EB-479D-B89F-130C02886155}')
    Documents               = UUID('{FDD39AD0-238F-46AF-ADB4-6C85480369C7}')
    DocumentsLibrary        = UUID('{7B0DB17D-9CD2-4A93-9733-46CC89022E7C}')
    Downloads               = UUID('{374DE290-123F-4565-9164-39C4925E467B}')
    Favorites               = UUID('{1777F761-68AD-4D8A-87BD-30B759FA33DD}')
    Fonts                   = UUID('{FD228CB7-AE11-4AE3-864C-16F3910AB8FE}')
    GameTasks               = UUID('{054FAE61-4DD8-4787-80B6-090220C4B700}')
    History                 = UUID('{D9DC8A3B-B784-432E-A781-5A1130A75963}')
    ImplicitAppShortcuts    = UUID('{BCB5256F-79F6-4CEE-B725-DC34E402FD46}')
    InternetCache           = UUID('{352481E8-33BE-4251-BA85-6007CAEDCF9D}')
    Libraries               = UUID('{1B3EA5DC-B587-4786-B4EF-BD1DC332AEAE}')
    Links                   = UUID('{bfb9d5e0-c6a9-404c-b2b2-ae6db6af4968}')
    LocalAppData            = UUID('{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}')
    LocalAppDataLow         = UUID('{A520A1A4-1780-4FF6-BD18-167343C5AF16}')
    LocalizedResourcesDir   = UUID('{2A00375E-224C-49DE-B8D1-440DF7EF3DDC}')
    Music                   = UUID('{4BD8D571-6D19-48D3-BE97-422220080E43}')
    MusicLibrary            = UUID('{2112AB0A-C86A-4FFE-A368-0DE96E47012E}')
    NetHood                 = UUID('{C5ABBF53-E17F-4121-8900-86626FC2C973}')
    OriginalImages          = UUID('{2C36C0AA-5812-4b87-BFD0-4CD0DFB19B39}')
    PhotoAlbums             = UUID('{69D2CF90-FC33-4FB7-9A0C-EBB0F0FCB43C}')
    PicturesLibrary         = UUID('{A990AE9F-A03B-4E80-94BC-9912D7504104}')
    Pictures                = UUID('{33E28130-4E1E-4676-835A-98395C3BC3BB}')
    Playlists               = UUID('{DE92C1C7-837F-4F69-A3BB-86E631204A23}')
    PrintHood               = UUID('{9274BD8D-CFD1-41C3-B35E-B13F55A758F4}')
    Profile                 = UUID('{5E6C858F-0E22-4760-9AFE-EA3317B67173}')
    ProgramData             = UUID('{62AB5D82-FDC1-4DC3-A9DD-070D1D495D97}')
    ProgramFiles            = UUID('{905e63b6-c1bf-494e-b29c-65b732d3d21a}')
    ProgramFilesX64         = UUID('{6D809377-6AF0-444b-8957-A3773F02200E}')
    ProgramFilesX86         = UUID('{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}')
    ProgramFilesCommon      = UUID('{F7F1ED05-9F6D-47A2-AAAE-29D317C6F066}')
    ProgramFilesCommonX64   = UUID('{6365D5A7-0F0D-45E5-87F6-0DA56B6A4F7D}')
    ProgramFilesCommonX86   = UUID('{DE974D24-D9C6-4D3E-BF91-F4455120B917}')
    Programs                = UUID('{A77F5D77-2E2B-44C3-A6A2-ABA601054A51}')
    Public                  = UUID('{DFDF76A2-C82A-4D63-906A-5644AC457385}')
    PublicDesktop           = UUID('{C4AA340D-F20F-4863-AFEF-F87EF2E6BA25}')
    PublicDocuments         = UUID('{ED4824AF-DCE4-45A8-81E2-FC7965083634}')
    PublicDownloads         = UUID('{3D644C9B-1FB8-4f30-9B45-F670235F79C0}')
    PublicGameTasks         = UUID('{DEBF2536-E1A8-4c59-B6A2-414586476AEA}')
    PublicLibraries         = UUID('{48DAF80B-E6CF-4F4E-B800-0E69D84EE384}')
    PublicMusic             = UUID('{3214FAB5-9757-4298-BB61-92A9DEAA44FF}')
    PublicPictures          = UUID('{B6EBFB86-6907-413C-9AF7-4FC2ABF07CC5}')
    PublicRingtones         = UUID('{E555AB60-153B-4D17-9F04-A5FE99FC15EC}')
    PublicUserTiles         = UUID('{0482af6c-08f1-4c34-8c90-e17ec98b1e17}')
    PublicVideos            = UUID('{2400183A-6185-49FB-A2D8-4A392A602BA3}')
    QuickLaunch             = UUID('{52a4f021-7b75-48a9-9f6b-4b87a210bc8f}')
    Recent                  = UUID('{AE50C081-EBD2-438A-8655-8A092E34987A}')
    RecordedTVLibrary       = UUID('{1A6FDBA2-F42D-4358-A798-B74D745926C5}')
    ResourceDir             = UUID('{8AD10C31-2ADB-4296-A8F7-E4701232C972}')
    Ringtones               = UUID('{C870044B-F49E-4126-A9C3-B52A1FF411E8}')
    RoamingAppData          = UUID('{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}')
    RoamedTileImages        = UUID('{AAA8D5A5-F1D6-4259-BAA8-78E7EF60835E}')
    RoamingTiles            = UUID('{00BCFC5A-ED94-4e48-96A1-3F6217F21990}')
    SampleMusic             = UUID('{B250C668-F57D-4EE1-A63C-290EE7D1AA1F}')
    SamplePictures          = UUID('{C4900540-2379-4C75-844B-64E6FAF8716B}')
    SamplePlaylists         = UUID('{15CA69B3-30EE-49C1-ACE1-6B5EC372AFB5}')
    SampleVideos            = UUID('{859EAD94-2E85-48AD-A71A-0969CB56A6CD}')
    SavedGames              = UUID('{4C5C32FF-BB9D-43b0-B5B4-2D72E54EAAA4}')
    SavedSearches           = UUID('{7d1d3a04-debb-4115-95cf-2f29da2920da}')
    Screenshots             = UUID('{b7bede81-df94-4682-a7d8-57a52620b86f}')
    SearchHistory           = UUID('{0D4C3DB6-03A3-462F-A0E6-08924C41B5D4}')
    SearchTemplates         = UUID('{7E636BFE-DFA9-4D5E-B456-D7B39851D8A9}')
    SendTo                  = UUID('{8983036C-27C0-404B-8F08-102D10DCFD74}')
    SidebarDefaultParts     = UUID('{7B396E54-9EC5-4300-BE0A-2482EBAE1A26}')
    SidebarParts            = UUID('{A75D362E-50FC-4fb7-AC2C-A8BEAA314493}')
    SkyDrive                = UUID('{A52BBA46-E9E1-435f-B3D9-28DAA648C0F6}')
    SkyDriveCameraRoll      = UUID('{767E6811-49CB-4273-87C2-20F355E1085B}')
    SkyDriveDocuments       = UUID('{24D89E24-2F19-4534-9DDE-6A6671FBB8FE}')
    SkyDrivePictures        = UUID('{339719B5-8C47-4894-94C2-D8F77ADD44A6}')
    StartMenu               = UUID('{625B53C3-AB48-4EC1-BA1F-A1EF4146FC19}')
    Startup                 = UUID('{B97D20BB-F46A-4C97-BA10-5E3608430854}')
    System                  = UUID('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}')
    SystemX86               = UUID('{D65231B0-B2F1-4857-A4CE-A8E7C6EA7D27}')
    Templates               = UUID('{A63293E8-664E-48DB-A079-DF759E0509F7}')
    UserPinned              = UUID('{9E3995AB-1F9C-4F13-B827-48B24B6C7174}')
    UserProfiles            = UUID('{0762D272-C50A-4BB0-A382-697DCD729B80}')
    UserProgramFiles        = UUID('{5CD7AEE2-2219-4A67-B85D-6C9CE15660CB}')
    UserProgramFilesCommon  = UUID('{BCBD3057-CA5C-4622-B42D-BC56DB0AE516}')
    Videos                  = UUID('{18989B1D-99B5-455B-841C-AB7C74E4DDFC}')
    VideosLibrary           = UUID('{491E922F-5643-4AF4-A7EB-4E7A138D8174}')
    Windows                 = UUID('{F38BF404-1D43-42F2-9305-67DE0B28FC23}')


class UserHandle:
    current = HANDLE(0)
    common  = HANDLE(-1)

_CoTaskMemFree = windll.ole32.CoTaskMemFree
_CoTaskMemFree.restype = None
_CoTaskMemFree.argtypes = (c_void_p, )

if VISTA_OR_LATER:
    _SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
    _SHGetKnownFolderPath.argtypes = (
        POINTER(GUID), DWORD, HANDLE, POINTER(c_wchar_p)
    )

    QueryFullProcessImageName = kernel32.QueryFullProcessImageNameW
    QueryFullProcessImageName.restype = BOOL
    QueryFullProcessImageName.argtypes = (
        HANDLE,     # hProcess
        DWORD,      # dwFlags
        LPWSTR,     # lpExeName
        PDWORD)      # lpdwSize

GetModuleFileNameEx = psapi.GetModuleFileNameExW
GetModuleFileNameEx.restype = DWORD
GetModuleFileNameEx.argtypes = (
    HANDLE,     # hProcess
    HMODULE,    # hModule
    LPWSTR,     # lpFilename
    DWORD)      # nSize


class PathNotFoundException(Exception): pass

def get_path(folderid, user_handle=UserHandle.common):
    fid = GUID(folderid)
    pPath = ctypes.c_wchar_p()
    S_OK = 0
    if _SHGetKnownFolderPath(ctypes.byref(fid), 0, user_handle,
        ctypes.byref(pPath)) != S_OK:
        raise PathNotFoundException()
    path = pPath.value
    _CoTaskMemFree(pPath)
    return path

def get_documents_directory():
    if VISTA_OR_LATER:
        try:
            return get_path(FOLDERID.Documents, UserHandle.current)
        except PathNotFoundException:
            return os.path.join(os.path.expanduser('~'))
    else:
        return shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)

def get_downloads_directory():
    if VISTA_OR_LATER:
        try:
            return get_path(FOLDERID.Downloads, UserHandle.current)
        except PathNotFoundException:
            return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:
        return os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL,
            None, 0), 'Downloads')

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

    pids = win32process.EnumProcesses()

    for pid in pids:
        if VISTA_OR_LATER:
            desired_access = PROCESS_QUERY_LIMITED_INFORMATION
            phandle = kernel32.OpenProcess(desired_access, BOOL(False), pid)

            if phandle is None:
                continue

            path = ctypes.create_unicode_buffer(MAX_PATH)
            length = DWORD(MAX_PATH)
            flags = DWORD(0)
            ret = QueryFullProcessImageName(phandle, flags, path, byref(length))

            if ret != 0:
                found_path = path.value.lower()

                if found_path == lower_path:
                    kernel32.CloseHandle(phandle)

                    return pid
        else:
            desired_access = DWORD(PROCESS_VM_READ.value |
                PROCESS_QUERY_INFORMATION.value)
            phandle = kernel32.OpenProcess(desired_access, BOOL(False), pid)

            if phandle is None:
                continue

            path = ctypes.create_unicode_buffer(MAX_PATH)
            length = DWORD(MAX_PATH)
            ret = GetModuleFileNameEx(phandle, None, path, length)

            if ret > 0:
                found_path = path.value.lower()

                if found_path == lower_path:
                    kernel32.CloseHandle(phandle)

                    return pid

        kernel32.CloseHandle(phandle)

    return None

def wait_for_pid(pid):
    desired_access = SYNCHRONIZE
    phandle = kernel32.OpenProcess(desired_access, BOOL(False), pid)

    if phandle is None:
        return False

    kernel32.WaitForSingleObject(phandle, INFINITE)

    kernel32.CloseHandle(phandle)

    return True

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

def get_ui_locale():
    return locale.windows_locale.get(kernel32.GetUserDefaultUILanguage(), None)

def activate_window(pid):
    handles = get_hwnds_for_pid(pid)
    if len(handles) > 0:
        wnd_handle = handles[0]
        win32gui.ShowWindow(wnd_handle, SW_SHOWNORMAL)
        win32gui.SetForegroundWindow(wnd_handle)
        return True
    return False

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
        self.mutexname = 'cddagl_{64394E79-7931-49CB-B8CF-3F4ECAE16B6C}'
        self.mutex = win32event.CreateMutex(None, False, self.mutexname)
        self.lasterror = win32api.GetLastError()

    def aleradyrunning(self):
        return (self.lasterror == ERROR_ALREADY_EXISTS)

    def close(self):
        if self.mutex:
            win32api.CloseHandle(self.mutex)
            self.mutex = None

    def __del__(self):
        self.close()


class SimpleNamedPipe:
    def __init__(self, name):
        self.name = name
        self.create_pipe()

    def create_pipe(self):
        self.pipe = win32pipe.CreateNamedPipe(r'\\.\pipe\{name}'.format(
            name=self.name),
            win32pipe.PIPE_ACCESS_INBOUND,
            (win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE
                | win32pipe.PIPE_WAIT),
            1,
            1024,
            1024,
            0,
            None)
        if self.pipe == win32file.INVALID_HANDLE_VALUE:
            last_error = win32api.GetLastError()
            raise OSError(last_error)

    def connect(self):
        try:
            return win32pipe.ConnectNamedPipe(self.pipe, None) == 0
        except WinError as e:
            win32api.CloseHandle(self.pipe)
            self.create_pipe()
            return win32pipe.ConnectNamedPipe(self.pipe, None) == 0

    def read(self, size):
        code, value = win32file.ReadFile(self.pipe, size)
        if code != 0:
            raise IOError(win32api.FormatMessage(code))

        return value

    def close(self):
        if self.pipe:
            win32api.CloseHandle(self.pipe)
            self.pipe = None

    def __del__(self):
        self.close()

def write_named_pipe(name, value):
    fileh = None
    try:
        fileh = win32file.CreateFile(r'\\.\pipe\{name}'.format(name=name),
            win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
        win32file.WriteFile(fileh, value)
    except WinError:
        pass
    finally:
        if fileh is not None:
            win32api.CloseHandle(fileh)
