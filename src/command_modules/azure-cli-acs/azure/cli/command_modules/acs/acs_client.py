# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import socket
import threading
from time import sleep
from os.path import expanduser, join, isfile
import os

import paramiko
import paramiko.agent
from sshtunnel import SSHTunnelForwarder
from scp import SCPClient

from knack.prompting import prompt_pass
from knack.util import CLIError


def _load_key(key_filename):
    pkey = None
    try:
        pkey = paramiko.RSAKey.from_private_key_file(key_filename, None)
    except paramiko.PasswordRequiredException:
        key_pass = prompt_pass('Password for private key:')
        pkey = paramiko.RSAKey.from_private_key_file(key_filename, key_pass)
    if pkey is None:
        raise CLIError('failed to load key: {}'.format(key_filename))
    return pkey


def _load_keys(key_filename=None, allow_agent=True):
    keys = []
    default_key_path = join(expanduser("~"), '.ssh', 'id_rsa')
    if key_filename is not None:
        key = _load_key(key_filename)
        keys.append(key)

    if allow_agent:
        agent = paramiko.agent.Agent()
        for key in agent.get_keys():
            keys.append(key)

    if not keys and isfile(default_key_path):
        key = _load_key(default_key_path)
        keys.append(key)

    if not keys:
        raise CLIError('No keys available in ssh agent or no key in {}. '
                       'Do you need to add keys to your ssh agent via '
                       'ssh-add or specify a --ssh-key-file?'.format(default_key_path))

    return keys


def secure_copy(user, host, src, dest, key_filename=None, allow_agent=True):
    keys = _load_keys(key_filename, allow_agent)
    pkey = keys[0]
    ssh = paramiko.SSHClient()
    proxy = None
    ssh_config_file = os.path.expanduser("~/.ssh/config")
    if os.path.isfile(ssh_config_file):
        conf = paramiko.SSHConfig()
        with open(ssh_config_file) as f:
            conf.parse(f)
        host_config = conf.lookup(host)
        if 'proxycommand' in host_config:
            proxy = paramiko.ProxyCommand(host_config['proxycommand'])
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, pkey=pkey, sock=proxy)
    scp = SCPClient(ssh.get_transport())
    scp.get(src, dest)
    scp.close()


class ACSClient(object):
    def __init__(self, client=None):
        self.client = client
        self.transport = None
        self.tunnel_server = None
        self.host = None
        self.username = None
        self.port = None

    def __del__(self):
        if self.transport is not None:
            self.transport.close()
        if self.client is not None:
            self.client.close()
        if self.tunnel_server is not None:
            self.tunnel_server.close_tunnel()

    def connect(self, host, username, port=2200,
                key_filename=None):
        """
        Creates a connection to the remote server.

        :param host: Remote host
        :type host: String
        :param username: User name to connect to the remote host
        :type username: String
        :param port: Remote host port
        :type port: Number
        """

        if not host:
            raise ValueError('Host is missing')

        if not username:
            raise ValueError('Username is missing')

        if not port:
            raise ValueError('Missing port')

        self.host = host
        self.username = username
        self.port = port

        if self.client is None:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            pkey = None
            if key_filename is not None:
                pkey = _load_key(key_filename)
            self.client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=pkey)

        self.transport = self.client.get_transport()
        return self.transport is not None

    def run(self, command, background=False):
        """
        Runs a command on the remote host

        :param command: Command to run on the remote host
        :type command: String
        :param background: True to run it in a separate thread,
               False should be run in the foreground
        :type command: Boolean
        """
        if background:
            t = threading.Thread(target=ACSClient._run_cmd, args=(self, command))
            t.daemon = True
            t.start()
            return None

        return self._run_cmd(command)

    def _run_cmd(self, command):
        """
        Runs a command on the remote host

        :param command: Command to run on the remote host
        :type command: String
        """
        if not command:
            raise ValueError('Command is missing')

        _, stdout, stderr = self.client.exec_command(command)

        return stdout, stderr

    def file_exists(self, file_path):
        """
        Checks if file on the remote exists

        :param file_path: Full path to the file on remote machine
        :type file_path: String
        """
        if not file_path:
            raise ValueError('Missing file path')

        if self.transport is None:
            raise TypeError('Transport cannot be none')

        sftp = self.transport.open_sftp_client()
        result = None
        try:
            sftp.stat(file_path)
            result = True
        except IOError:
            result = False
        finally:
            sftp.close()
        return result

    def create_tunnel(self, remote_host, remote_port, local_port=0):
        """
        Creates a tunnel to the remote host

        :param remote_host: Remote host to tunnel to
        :type remote_host: String
        :param remote_port: Remote port to tunnel to
        :type remote_port: Number
        :param local_port: Local port. If set to 0, random local port is selected
        :type local_port: Number
        """
        if local_port is 0:
            local_port = self.get_available_local_port()

        with SSHTunnelForwarder((self.host, self.port),
                                ssh_username=self.username,
                                remote_bind_address=(remote_host, remote_port),
                                local_bind_address=('0.0.0.0', local_port)):
            try:
                while True:
                    sleep(1)
            except KeyboardInterrupt:
                pass

    @staticmethod
    def get_available_local_port():
        """
        Gets a random, available local port
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # pylint: disable=no-member
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port
