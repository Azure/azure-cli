# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from _common import (create_vm,
                     install_cli_interactive,
                     verify_basic,
                     verify_tab_complete,
                     AZURE_CLI_PACKAGE_VERSION_PREV)

## Ubuntu 14.04 LTS

class Ubuntu1404Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'Canonical:UbuntuServer:14.04.4-LTS:latest')
        cls.vm(['sudo', 'apt-get', 'update'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'libssl-dev', 'libffi-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'python-dev'])

class TestUbuntu1404_global(Ubuntu1404Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestUbuntu1404_local(Ubuntu1404Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

class TestUbuntu1404_global_tab(Ubuntu1404Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory=None, exec_directory=None, tab_completion_ans='y', sudo=True)
        verify_basic(self.vm)
        verify_tab_complete(self.vm)

class TestUbuntu1404_b2b(Ubuntu1404Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True, nightly_version=AZURE_CLI_PACKAGE_VERSION_PREV)
        verify_basic(self.vm)
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

# Ubuntu 12.04 LTS

class Ubuntu1204Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'Canonical:UbuntuServer:12.04.5-LTS:12.04.201605160')
        cls.vm(['sudo', 'apt-get', 'update'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'libssl-dev', 'libffi-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'python-dev'])

class TestUbuntu1204_global(Ubuntu1204Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestUbuntu1204_local(Ubuntu1204Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# Ubuntu 15.10

class Ubuntu1510Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'Canonical:UbuntuServer:15.10:15.10.201605160')
        cls.vm(['sudo', 'apt-get', 'update'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'libssl-dev', 'libffi-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'python-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'build-essential'])

class TestUbuntu1510_global(Ubuntu1510Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestUbuntu1510_local(Ubuntu1510Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# Ubuntu 16.04 LTS

class Ubuntu1604Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'Canonical:UbuntuServer:16.04.0-LTS:16.04.201605161')
        cls.vm(['sudo', 'apt-get', 'update'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'libssl-dev', 'libffi-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'python-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'build-essential'])

class TestUbuntu1604_global(Ubuntu1604Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestUbuntu1604_local(Ubuntu1604Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# centos 7.1

class Centos71Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'OpenLogic:CentOS:7.1:7.1.20160308')
        cls.vm(['sudo', 'yum', 'check-update'], _ok_code=[0, 100])
        cls.vm(['sudo', 'yum', 'install', '-y', 'gcc', 'libffi-devel', 'python-devel', 'openssl-devel'])

class TestCentos71_global(Centos71Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestCentos71_local(Centos71Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# centos 7.2

class Centos72Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'OpenLogic:CentOS:7.2:7.2.20160308')
        cls.vm(['sudo', 'yum', 'check-update'], _ok_code=[0, 100])
        cls.vm(['sudo', 'yum', 'install', '-y', 'gcc', 'libffi-devel', 'python-devel', 'openssl-devel'])

class TestCentos72_global(Centos72Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestCentos72_local(Centos72Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# debian 8

class Debian8Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'credativ:Debian:8:8.0.201604200')
        cls.vm(['sudo', 'apt-get', 'update'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'curl'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'libssl-dev', 'libffi-dev', 'python-dev'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'build-essential'])

class TestDebian8_global(Debian8Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestDebian8_local(Debian8Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# debian 7

class Debian7Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'credativ:Debian:7:7.0.201604200')
        cls.vm(['sudo', 'apt-get', 'update'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'curl'])
        cls.vm(['sudo', 'apt-get', 'install', '-y', 'libssl-dev', 'libffi-dev', 'python-dev'])

class TestDebian7_global(Debian7Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestDebian7_local(Debian7Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# RedHat RHEL 7.2

class RHEL72Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'RedHat:RHEL:7.2:7.2.20160302')
        cls.vm(['sudo', 'yum', 'check-update'], _ok_code=[0, 100])
        cls.vm(['sudo', 'yum', 'install', '-y', 'gcc', 'libffi-devel', 'python-devel', 'openssl-devel'])

class TestRHEL72_global(RHEL72Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestRHEL72_local(RHEL72Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

# SUSE OpenSUSE 13.2

class SUSE132Base(object):
    @classmethod
    def setUpClass(cls):
        cls.vm = create_vm(cls.__name__, 'SUSE:openSUSE:13.2:2016.03.02')
        cls.vm(['sudo', 'zypper', 'refresh'])
        cls.vm(['sudo', 'zypper', '--non-interactive', 'install', 'gcc', 'libffi-devel', 'python-devel', 'openssl-devel'])

class TestSUSE132_global(SUSE132Base):
    def test(self):
        install_cli_interactive(self.vm, sudo=True)
        verify_basic(self.vm)

class TestSUSE132_local(SUSE132Base):
    def test(self):
        install_cli_interactive(self.vm, install_directory='~/myaz', exec_directory='~/myaz', tab_completion_ans='n', sudo=False)
        verify_basic(self.vm, az='~/myaz/az')

