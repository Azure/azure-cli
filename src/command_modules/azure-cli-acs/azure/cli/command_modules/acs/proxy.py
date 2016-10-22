#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import platform
import subprocess

try:
    from azure.cli.command_modules.acs import win_proxy
except ImportError:
    pass

# TODO (peterj, 10/11/2016): task 275567 - implement this for Linux
def unset_http_proxy():
    """
    Unsets/disables the HTTP proxy
    """
    os_platform = platform.system()
    if os_platform == 'Darwin':
        subprocess.call('sudo networksetup -setwebproxystate wi-fi off', shell=True)
    elif os_platform == 'Windows':
        win_proxy.set_http_proxy(None, None, False)
    else:
        raise NotImplementedError('Not implemented yet for {}'.format(os_platform))

def set_http_proxy(host, port):
    """
    Sets the HTTP proxy to host:port
    """
    if not host:
        raise ValueError('Missing host')

    if not port:
        raise ValueError('Missing port')

    os_platform = platform.system()

    if os_platform == 'Darwin':
        cmd = 'sudo networksetup -setwebproxy wi-fi {} {}'.format(host, port)
        subprocess.call(cmd, shell=True)
    elif os_platform == 'Windows':
        win_proxy.set_http_proxy(host, port)
    else:
        raise NotImplementedError('Not implemented yet for {}'.format(os_platform))
