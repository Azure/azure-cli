from ctypes import *
from ctypes.wintypes import *

LPWSTR = POINTER(WCHAR)
HINTERNET = LPVOID

INTERNET_PER_CONN_PROXY_SERVER = 2
INTERNET_OPTION_REFRESH = 37
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_PER_CONNECTION_OPTION = 75
INTERNET_PER_CONN_PROXY_BYPASS = 3
INTERNET_PER_CONN_FLAGS = 1

class INTERNET_PER_CONN_OPTION(Structure):
    class Value(Union):
        _fields_ = [
            ('dwValue', DWORD),
            ('pszValue', LPWSTR),
            ('ftValue', FILETIME),
        ]

    _fields_ = [
        ('dwOption', DWORD),
        ('Value', Value),
    ]

class INTERNET_PER_CONN_OPTION_LIST(Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('pszConnection', LPWSTR),
        ('dwOptionCount', DWORD),
        ('dwOptionError', DWORD),
        ('pOptions', POINTER(INTERNET_PER_CONN_OPTION)),
    ]

def set_http_proxy(host, port, on = True):
    """
    Sets the HTTP proxy on Windows
    """
    if on:
        setting = create_unicode_buffer(host+":"+str(port))
    else:
        setting = None

    InternetSetOption = windll.wininet.InternetSetOptionW
    InternetSetOption.argtypes = [HINTERNET, DWORD, LPVOID, DWORD]
    InternetSetOption.restype  = BOOL

    List = INTERNET_PER_CONN_OPTION_LIST()
    Option = (INTERNET_PER_CONN_OPTION * 3)()
    nSize = c_ulong(sizeof(INTERNET_PER_CONN_OPTION_LIST))

    Option[0].dwOption = INTERNET_PER_CONN_FLAGS
    Option[0].Value.dwValue = (2 if on else 1)
    Option[1].dwOption = INTERNET_PER_CONN_PROXY_SERVER
    Option[1].Value.pszValue = setting
    Option[2].dwOption = INTERNET_PER_CONN_PROXY_BYPASS
    Option[2].Value.pszValue = create_unicode_buffer("localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;172.32.*;192.168.*")

    List.dwSize = sizeof(INTERNET_PER_CONN_OPTION_LIST)
    List.pszConnection = None
    List.dwOptionCount = 3
    List.dwOptionError = 0
    List.pOptions = Option

    InternetSetOption(None, INTERNET_OPTION_PER_CONNECTION_OPTION, byref(List), nSize)
    InternetSetOption(None, INTERNET_OPTION_SETTINGS_CHANGED, None, 0)
    InternetSetOption(None, INTERNET_OPTION_REFRESH, None, 0)