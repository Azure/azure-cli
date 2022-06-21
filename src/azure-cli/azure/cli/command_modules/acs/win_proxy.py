# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ctypes import POINTER, Structure, Union, byref, c_ulong, create_unicode_buffer, sizeof, windll
from ctypes.wintypes import BOOL, DWORD, FILETIME, LPVOID, WCHAR

from .proxy import Proxy

LPWSTR = POINTER(WCHAR)
HINTERNET = LPVOID

# TODO: this file is deprecated, will remove this after container service commands (acs) are removed during
# the next breaking change window.


class WinProxy(Proxy):
    INTERNET_PER_CONN_PROXY_SERVER = 2
    INTERNET_OPTION_REFRESH = 37
    INTERNET_OPTION_SETTINGS_CHANGED = 39
    INTERNET_OPTION_PER_CONNECTION_OPTION = 75
    INTERNET_PER_CONN_PROXY_BYPASS = 3
    INTERNET_PER_CONN_FLAGS = 1

    def set_http_proxy(self, host, port):
        """
        Sets the HTTP proxy on Windows
        """
        setting = create_unicode_buffer(host + ':' + str(port))
        self._set_internet_options(setting)

    def disable_http_proxy(self):
        """
        Disables the HTTP proxy on Windows
        """
        self._set_internet_options(None, False)

    def _set_internet_options(self, setting, on=True):
        """
        Sets internet options with the wininet API
        """
        internet_set_option = windll.wininet.InternetSetOptionW
        internet_set_option.argtypes = [LPVOID, DWORD, LPVOID, DWORD]
        internet_set_option.restype = BOOL

        option_list = InternetPerConnOptionList()
        option = (InternetPerConnOption * 3)()
        size = c_ulong(sizeof(InternetPerConnOptionList))

        option[0].dwOption = self.INTERNET_PER_CONN_FLAGS
        option[0].Value.dwValue = (2 if on else 1)
        option[1].dwOption = self.INTERNET_PER_CONN_PROXY_SERVER
        option[1].Value.pszValue = setting
        option[2].dwOption = self.INTERNET_PER_CONN_PROXY_BYPASS
        option[2].Value.pszValue = create_unicode_buffer('<-loopback>')

        option_list.dwSize = sizeof(InternetPerConnOptionList)
        option_list.pszConnection = None
        option_list.dwOptionCount = 3
        option_list.dwOptionError = 0
        option_list.pOptions = option

        internet_set_option(None, self.INTERNET_OPTION_PER_CONNECTION_OPTION, byref(option_list), size)
        internet_set_option(None, self.INTERNET_OPTION_SETTINGS_CHANGED, None, 0)
        internet_set_option(None, self.INTERNET_OPTION_REFRESH, None, 0)


# pylint: disable=too-few-public-methods
class InternetPerConnOption(Structure):
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


class InternetPerConnOptionList(Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('pszConnection', LPWSTR),
        ('dwOptionCount', DWORD),
        ('dwOptionError', DWORD),
        ('pOptions', POINTER(InternetPerConnOption)),
    ]

    dwSize = None
    pszConnection = None
    dwOptionCount = None
    dwOptionError = None
    pOptions = None
