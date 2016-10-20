
import getpass
import os
import select
import socket
import sys
import threading
import webbrowser
from time import sleep

import paramiko
import requests
from sshtunnel import SSHTunnelForwarder

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

class ACSClient(object):
    def __init__(self, client = None):
        self.client = client
        self.transport = None
        self.tunnel_server = None

    def __del__(self):
        if self.transport is not None:
            self.transport.close()
        if self.client is not None:
            self.client.close()
        if self.tunnel_server is not None:
            self.close_tunnel()

    def connect(self, host, username, port=2200):
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
            self.client.connect(hostname = host, 
                                port = port,
                                username = username)

        self.transport = self.client.get_transport()
        return self.transport is not None
    
    def run(self, command, background = False):
        """
        Runs a command on the remote host

        :param command: Command to run on the remote host
        :type command: String
        :param background: True if command should be run in the foreground, false to run it in a separate thread
        :type command: Boolean
        """
        if background:
            t = threading.Thread(target=ACSClient._run_cmd, 
                                 args=(self, command))
            t.daemon = True
            t.start()
            return
        else:
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
            sftp.close
        return result

    def copy_file(self, local_file, remote_file):
        """
        Copies a local file to the remote host
        
        :param local_file: Full path to the file on the local machine
        :type local_file: String
        :param remote_file: Full path to the file on the remote host
        :type remote_file: String
        """
        if (not os.path.isfile(local_file)):
            raise OSError('Local file "{}"" was not found'.format(local_file))

        if not local_file:
            raise ValueError('Missing local file')

        if not remote_file:
            raise ValueError('Missing remote file')

        if self.transport is None:
            raise TypeError('Transport cannot be none')
        
        sftp = self.transport.open_sftp_client()
        sftp.put(local_file, remote_file)
        sftp.close()
    
    def chmod(self, remote_file, mode):
        """
        Runs a chmod command on a remote file
        
        :param remote_file: Full path to the file on the remote host
        :type remote_file: String
        :param mode: File mode to set on the file
        :type mode: Number
        """
        if self.transport is None:
            # TODO (peter, 08/26/2016): 258186 We should not use generic exceptions in our code 
            raise Exception('Transport cannot be none')

        if not remote_file:
            raise ValueError('Missing remote file')
        
        if not mode:
            raise ValueError('Missing mode')

        sftp = self.transport.open_sftp_client()
        try:
            sftp.lstat(remote_file)
            sftp.chmod(remote_file, mode)
        except OSError as e:
            import errno
            if e.errno == errno.ENOENT:
                raise Exception('Remote file "{}" does not exist'.format(remote_file))
            else:
                assert False, 'Error accessing remote_file {}'.format(remote_file)
        finally:
            sftp.close()
    # TODO (peterj, 09/06/2016): This should be in a separate class (Marathon?)
    def get_request(self, path):
        """
        Makes a GET request to Marathon endpoint (localhost:8080 on the cluster)
        
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        local_port = self.get_available_local_port()
        server = SSHTunnelForwarder(
            (self.host, self.port),
            ssh_username=self.username,
            remote_bind_address=('localhost', 8080),
            local_bind_address=('0.0.0.0', local_port))
        
        server.start()
        url = 'http://localhost:' + str(local_port) + '/' + path
        response = requests.get(url).json()
        server.stop()
        return response

    def create_tunnel(self, remote_host, remote_port, local_port = 0, open_url = None):
        """
        Creates a tunnel to the remote host

        :param remote_host: Remote host to tunnel to
        :type remote_host: String
        :param remote_port: Remote port to tunnel to
        :type remote_port: Number
        :param local_port: Local port. If set to 0, random local port is selected
        :type local_port: Number
        :param open_url: URL to open after tunnel is created
        :type open_url: String
        """
        if local_port is 0:
            local_port = self.get_available_local_port()

        with SSHTunnelForwarder(
            (self.host, self.port),
            ssh_username=self.username,
            remote_bind_address=(remote_host, remote_port),
            local_bind_address=('0.0.0.0', local_port)) as server:
            try:
                if open_url: 
                    webbrowser.open(open_url)
                while True:
                    sleep(1)
            except KeyboardInterrupt:
                pass

    def get_available_local_port(self):
        """
        Gets a random, available local port
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port
