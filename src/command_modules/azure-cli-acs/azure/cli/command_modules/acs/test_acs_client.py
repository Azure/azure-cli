import unittest

import mock
import paramiko

import acs_client


class AcsClientTest(unittest.TestCase):
    def test_create_acs_Client(self):
        a = acs_client.ACSClient()
        self.assertIsNotNone(a)
    
    @mock.patch('paramiko.SSHClient')
    def test_connect_success(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        res = a.connect('myhostname', 'myuser')
        self.assertTrue(res)

    @mock.patch('paramiko.SSHClient')
    def test_connect_fails(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = None 
        a = acs_client.ACSClient(mock_ssh_client)
        res = a.connect('myhostname', 'myuser')
        self.assertFalse(res)

    @mock.patch('paramiko.SSHClient')
    def test_connect_default_port(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('myhostname', 'myuser')
        self.assertEqual(a.port, 2200)

    @mock.patch('paramiko.SSHClient')
    def test_connect_set_port(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('myhostname', 'myuser', 1234)
        self.assertEqual(a.port, 1234)

    @mock.patch('paramiko.SSHClient')
    def test_connect_hostname_username_set(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('myhostname', 'myuser')
        self.assertEqual(a.host, 'myhostname')
        self.assertEqual(a.username, 'myuser')

    @mock.patch('paramiko.SSHClient')
    def test_connect_missing_hostname(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        self.assertRaises(ValueError, a.connect, '', 'someuser')

    @mock.patch('paramiko.SSHClient')
    def test_connect_missing_username(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        self.assertRaises(ValueError, a.connect, 'somehost', '')

    @mock.patch('paramiko.SSHClient')
    def test_connect_missing_port(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = acs_client.ACSClient(mock_ssh_client)
        self.assertRaises(ValueError, a.connect, 'somehost', 'someuser', '')

    @mock.patch('paramiko.SSHClient')
    def test_run(self, mock_ssh_client):
        exec_command_mock = mock.Mock()
        mock_ssh_client.exec_command.return_value = (None, 'stdout', 'stderr')
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        stdout, stderr = a.run('somecommand')
        self.assertEquals(stdout, 'stdout')
        self.assertEqual(stderr, 'stderr')

    @mock.patch('paramiko.SSHClient')
    def test_run_empty_command(self, mock_ssh_client):
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        self.assertRaises(ValueError, a.run, '')

    @mock.patch('paramiko.SSHClient')
    def test_copy_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        with mock.patch('os.path.isfile', return_value=True):
            a.copy_file('localfile', 'remotefile')
            self.assertTrue(sftp_mock.put.called)
            self.assertTrue(sftp_mock.close.called)

    @mock.patch('paramiko.SSHClient')
    def test_copy_file_no_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        with mock.patch('os.path.isfile', return_value=False):
            self.assertRaises(OSError, a.copy_file, '', 'remotefile')

    @mock.patch('paramiko.SSHClient')
    def test_copy_file_empty_local_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        with mock.patch('os.path.isfile', return_value=True):
            self.assertRaises(ValueError, a.copy_file, '', 'remotefile')

    @mock.patch('paramiko.SSHClient')
    def test_copy_file_empty_remote_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        with mock.patch('os.path.isfile', return_value=True):
            self.assertRaises(ValueError, a.copy_file, 'localfile', '')

    @mock.patch('paramiko.SSHClient')
    def test_chmod(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        a.chmod('somefile', 1234)

        self.assertTrue(sftp_mock.lstat.called)
        self.assertTrue(sftp_mock.chmod.called)
        self.assertTrue(sftp_mock.close.called)

    @mock.patch('paramiko.SSHClient')
    def test_file_exists_no_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        sftp_mock.stat.side_effect = IOError()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        actual = a.file_exists('somefile')
        self.assertEquals(actual, False)

    @mock.patch('paramiko.SSHClient')
    def test_file_exists_positive(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        sftp_mock.stat.side_efect = 'filexists'
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        actual = a.file_exists('somefile')
        self.assertEquals(actual, True)

    @mock.patch('paramiko.SSHClient')
    def test_chmod_empty_remote_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        self.assertRaises(ValueError, a.chmod, '', 1234)

    @mock.patch('paramiko.SSHClient')
    def test_chmod_empty_mode(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        self.assertRaises(ValueError, a.chmod, 'remotefile', '')

    @mock.patch('paramiko.SSHClient')
    def test_chmod_empty_transport(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        self.assertRaises(Exception, a.chmod, 'remotefile', 1234)

    @mock.patch('paramiko.SSHClient')
    def test_chmod_missing_remote_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        sftp_mock.lstat.side_effect = OSError('Some OS error')

        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = acs_client.ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        self.assertRaises(Exception, a.chmod, 'remotefile', 1234)
        self.assertTrue(sftp_mock.close.called)
