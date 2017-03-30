import paramiko
from scp import SCPClient
import azure.cli.command_modules.project.utils as utils
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name


class SSHConnect(object):
    """
    Deals with SSHClient and SCPClient functionality
    """

    # pylint: disable=line-too-long, too-many-arguments
    def __init__(self, dns_prefix, location, user_name, password=None, ssh_private_key=None, port=22):
        self._ssh = self.__get_ssh_client(
            dns_prefix, location, port, user_name, password, ssh_private_key)

        # SCPCLient takes a paramiko transport as its only argument
        self._scp = SCPClient(self._ssh.get_transport())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __get_ssh_client(self, dns_prefix, location, port, user_name, password, ssh_private_key):
        """
        Gets SSHClient
        """
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if password and ssh_private_key:
            raise NotImplementedError(
                'Protected SSH keys are not supported yet')

        if password:
            ssh.connect(utils.get_remote_host(dns_prefix, location),
                        port,
                        username=user_name,
                        password=password)

        if ssh_private_key:
            pkey = paramiko.RSAKey.from_private_key_file(ssh_private_key)
            ssh.connect(utils.get_remote_host(dns_prefix, location),
                        port,
                        username=user_name,
                        pkey=pkey)
        return ssh

    def get(self, remote_file, local_file):
        """
        Get remote file using SCPClient
        """
        self._scp.get(remote_file, local_file)

    def put(self, local_file, remote_file):
        """
        Put local file to remote using SCPClient
        """
        self._scp.put(local_file, remote_file)

    def run_command(self, command, async_call=False):
        """
        Runs a command on remote machine
        """
        if async_call:
            transport = self._ssh.get_transport()
            channel = transport.open_session()
            channel.exec_command(
                '{} > /dev/null 2>&1 &'.format(command))
        else:
            _, stdout, stderr = self._ssh.exec_command(command)
            for line in stdout:
                logger.info(line)
            for line in stderr:
                logger.debug(line)
            return stdout, stderr

    def close(self):
        """
        Close SSHClient and SCPClient
        """
        if self._ssh:
            self._ssh.close()
        if self._scp:
            self._scp.close()
