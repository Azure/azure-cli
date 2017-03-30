import paramiko
from scp import SCPClient
import azure.cli.command_modules.project.utils as utils
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
logger = azlogging.get_az_logger(__name__) # pylint: disable=invalid-name

class SSHConnect(object):
    """
    Deals with SSHClient and SCPClient functionality
    """

    def __init__(self, user_name, dns_prefix, location, port, ssh_private_key):
        self._ssh = self.__get_ssh_client(user_name, dns_prefix, location, port, ssh_private_key)

        # SCPCLient takes a paramiko transport as its only argument
        self._scp = SCPClient(self._ssh.get_transport())

    def __get_ssh_client(self, user_name, dns_prefix, location, port, ssh_private_key):
        """
        Gets SSHClient
        """
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        # TODO: Remove the below command when we support protected SSH Keys
        pkey = paramiko.RSAKey.from_private_key_file(ssh_private_key)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
