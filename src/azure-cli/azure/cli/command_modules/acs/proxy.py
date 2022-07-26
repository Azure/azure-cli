# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import platform
import subprocess
from abc import abstractmethod

# TODO: this file is deprecated, will remove this after container service commands (acs) are removed during
# the next breaking change window.


def disable_http_proxy():
    """
    Disables the HTTP proxy
    """
    _get_proxy_instance().disable_http_proxy()


def set_http_proxy(host, port):
    """
    Sets the HTTP proxy to host:port
    """
    if not host:
        raise ValueError('Missing host')

    if not port:
        raise ValueError('Missing port')

    _get_proxy_instance().set_http_proxy(host, port)


def _get_proxy_instance():
    """
    Gets the proxy class instance based on the OS
    """
    os_platform = platform.system()
    if os_platform == 'Darwin':
        return MacProxy()
    if os_platform == 'Windows':
        from azure.cli.command_modules.acs.win_proxy import WinProxy
        return WinProxy()
    if os_platform == 'Linux':
        return LinuxProxy()
    raise NotImplementedError('Not implemented yet for {}'.format(os_platform))


class Proxy:
    """
    Base proxy class
    """

    def __init__(self):
        pass

    @abstractmethod
    def set_http_proxy(self, host, port):
        """
        Sets the HTTP proxy
        """

    @abstractmethod
    def disable_http_proxy(self):
        """
        Disables the HTTP proxy
        """


class LinuxProxy(Proxy):
    def set_http_proxy(self, host, port):
        """
        Sets the HTTP proxy on Linux
        """
        subprocess.call('sudo gsettings set org.gnome.system.proxy mode \'manual\'', shell=True)
        subprocess.call(
            'sudo gsettings set org.gnome.system.proxy.http host \'{}\''.format(host), shell=True)
        subprocess.call(
            'sudo gsettings set org.gnome.system.proxy.http port {}'.format(port), shell=True)

    def disable_http_proxy(self):
        """
        Disables the HTTP proxy on Linux
        """
        subprocess.call('sudo gsettings set org.gnome.system.proxy mode \'none\'', shell=True)


class MacProxy(Proxy):
    def set_http_proxy(self, host, port):
        """
        Sets the HTTP proxy on macOS
        """
        cmd = 'sudo networksetup -setwebproxy wi-fi {} {}'.format(host, port)
        subprocess.call(cmd, shell=True)

    def disable_http_proxy(self):
        """
        Disables the HTTP proxy on macOS
        """
        subprocess.call('sudo networksetup -setwebproxystate wi-fi off', shell=True)
