# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ctypes import (POINTER, Structure, Union, byref, c_ulong,
                    create_unicode_buffer, sizeof, windll)
from ctypes.wintypes import BOOL, DWORD, FILETIME, LPVOID, WCHAR

from azure.cli.command_modules.acs.proxy import Proxy

LPWSTR = POINTER(WCHAR)
HINTERNET = LPVOID


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
        Disables the HTTP proxy
        """
        self._set_internet_options(None, False)

    def _set_internet_options(self, setting, on=True):
        """
        Sets the internet options
        """
        InternetSetOption = windll.wininet.InternetSetOptionW
        InternetSetOption.argtypes = [LPVOID, DWORD, LPVOID, DWORD]
        InternetSetOption.restype = BOOL

        List = INTERNET_PER_CONN_OPTION_LIST()
        Option = (INTERNET_PER_CONN_OPTION * 3)()
        nSize = c_ulong(sizeof(INTERNET_PER_CONN_OPTION_LIST))

        Option[0].dwOption = self.INTERNET_PER_CONN_FLAGS
        Option[0].Value.dwValue = (2 if on else 1)
        Option[1].dwOption = self.INTERNET_PER_CONN_PROXY_SERVER
        Option[1].Value.pszValue = setting
        Option[2].dwOption = self.INTERNET_PER_CONN_PROXY_BYPASS
        Option[2].Value.pszValue = create_unicode_buffer('<-loopback>')

        List.dwSize = sizeof(INTERNET_PER_CONN_OPTION_LIST)
        List.pszConnection = None
        List.dwOptionCount = 3
        List.dwOptionError = 0
        List.pOptions = Option

        InternetSetOption(None, self.INTERNET_OPTION_PER_CONNECTION_OPTION, byref(List), nSize)
        InternetSetOption(None, self.INTERNET_OPTION_SETTINGS_CHANGED, None, 0)
        InternetSetOption(None, self.INTERNET_OPTION_REFRESH, None, 0)


# pylint: disable=too-few-public-methods
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

    dwSize = None
    pszConnection = None
    dwOptionCount = None
    dwOptionError = None
    pOptions = None
