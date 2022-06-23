# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.acs.acs_client import ACSClient


# TODO: deprecated, will remove this after container service commands (acs) are removed during
# the next breaking change window.
class AcsClientTest(unittest.TestCase):
    def test_create_acs_client(self):
        a = ACSClient()
        self.assertIsNotNone(a)

    @mock.patch('paramiko.SSHClient')
    def test_connect_success(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        res = a.connect('myhostname', 'myuser')
        self.assertTrue(res)

    @mock.patch('paramiko.SSHClient')
    def test_connect_fails(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = None
        a = ACSClient(mock_ssh_client)
        res = a.connect('myhostname', 'myuser')
        self.assertFalse(res)

    @mock.patch('paramiko.SSHClient')
    def test_connect_default_port(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        a.connect('myhostname', 'myuser')
        self.assertEqual(a.port, 2200)

    @mock.patch('paramiko.SSHClient')
    def test_connect_set_port(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        a.connect('myhostname', 'myuser', 1234)
        self.assertEqual(a.port, 1234)

    @mock.patch('paramiko.SSHClient')
    def test_connect_hostname_username_set(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        a.connect('myhostname', 'myuser')
        self.assertEqual(a.host, 'myhostname')
        self.assertEqual(a.username, 'myuser')

    @mock.patch('paramiko.SSHClient')
    def test_connect_missing_hostname(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        self.assertRaises(ValueError, a.connect, '', 'someuser')

    @mock.patch('paramiko.SSHClient')
    def test_connect_missing_username(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        self.assertRaises(ValueError, a.connect, 'somehost', '')

    @mock.patch('paramiko.SSHClient')
    def test_connect_missing_port(self, mock_ssh_client):
        mock_ssh_client.get_transport.return_value = mock.Mock()
        a = ACSClient(mock_ssh_client)
        self.assertRaises(ValueError, a.connect, 'somehost', 'someuser', '')

    @mock.patch('paramiko.SSHClient')
    def test_run(self, mock_ssh_client):
        mock_ssh_client.exec_command.return_value = (None, 'stdout', 'stderr')
        a = ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        stdout, stderr = a.run('somecommand')
        self.assertEqual(stdout, 'stdout')
        self.assertEqual(stderr, 'stderr')

    @mock.patch('paramiko.SSHClient')
    def test_run_empty_command(self, mock_ssh_client):
        a = ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')
        self.assertRaises(ValueError, a.run, '')

    @mock.patch('paramiko.SSHClient')
    def test_file_exists_no_file(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        sftp_mock.stat.side_effect = IOError()
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        actual = a.file_exists('somefile')
        self.assertEqual(actual, False)

    @mock.patch('paramiko.SSHClient')
    def test_file_exists_positive(self, mock_ssh_client):
        sftp_mock = mock.Mock()
        sftp_mock.stat.side_efect = 'filexists'
        transport_mock = mock.Mock()
        transport_mock.open_sftp_client.return_value = sftp_mock
        mock_ssh_client.get_transport.return_value = transport_mock
        a = ACSClient(mock_ssh_client)
        a.connect('somehost', 'someusername')

        actual = a.file_exists('somefile')
        self.assertEqual(actual, True)
