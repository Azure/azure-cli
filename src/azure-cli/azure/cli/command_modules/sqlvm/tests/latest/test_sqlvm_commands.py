# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import os
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from azure.cli.core.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckGreaterThan,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StorageAccountPreparer,
    LiveScenarioTest,
    record_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from datetime import datetime, timedelta
from time import sleep


# Constants
sqlvm_name_prefix = 'clisqlvm'
sqlvm_domain_prefix = 'domainvm'
sqlvm_group_prefix = 'sqlgroup'
sqlvm_max_length = 15


class SqlVirtualMachinePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix=sqlvm_name_prefix, location='westus',
                 vm_user='admin123', vm_password='SecretPassword123', parameter_name='sqlvm',
                 resource_group_parameter_name='resource_group', skip_delete=True):
        super(SqlVirtualMachinePreparer, self).__init__(name_prefix, sqlvm_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.vm_user = vm_user
        self.vm_password = vm_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = ('az vm create -l {} -g {} -n {} --admin-username {} --admin-password {} --image MicrosoftSQLServer:SQL2017-WS2016:Enterprise:latest'
                    ' --size Standard_DS2_v2 --nsg-rule NONE')
        execute(DummyCli(), template.format(self.location, group, name, self.vm_user, self.vm_password))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute(DummyCli(), 'az vm delete -g {} -n {} --yes --no-wait'.format(group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a virtual machine a resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class DomainPreparer(AbstractPreparer, SingleValueReplacer):
    import string

    def __init__(self, name_prefix=sqlvm_domain_prefix, location='westus',
                 vm_user='admin123', vm_password='SecretPassword123', parameter_name='domainvm',
                 resource_group_parameter_name='resource_group', skip_delete=True):
        super(DomainPreparer, self).__init__(name_prefix, sqlvm_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.vm_user = vm_user
        self.vm_password = vm_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def id_generator(self, size=6, chars=string.ascii_lowercase + string.digits):
        import random
        return ''.join(random.choice(chars) for _ in range(size))

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        dns_name = self.id_generator()
        parameters = ('adminUsername=admin123 adminPassword=SecretPassword123 location=westus '
                      'domainName=domain.com dnsPrefix={}').format(dns_name)
        template = 'az deployment group create --name {} -g {} --template-uri {} --parameters {}'
        execute(DummyCli(), template.format('domaintemplate', group,
                                            'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/application-workloads/active-directory/active-directory-new-domain/azuredeploy.json',
                                            parameters))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute(DummyCli(), 'az group delete -g {}'.format(group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a virtual machine a resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class SqlVmScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlVirtualMachinePreparer()
    @StorageAccountPreparer()
    def test_sqlvm_mgmt(self, resource_group, resource_group_location, sqlvm, storage_account):

        loc = 'westus'
        self.cmd('storage account update -n {} -g {} --set kind=StorageV2'.format(storage_account, resource_group))

        sa = self.cmd('storage account show -n {} -g {}'
                      .format(storage_account, resource_group)).get_output_in_json()

        key = self.cmd('storage account keys list -n {} -g {}'
                       .format(storage_account, resource_group)).get_output_in_json()

        # Assert customer cannot create a SQL vm with no agent and do not provide offer and sku
        with self.assertRaisesRegex(CLIError, "usage error: --sql-mgmt-type NoAgent --image-sku NAME --image-offer NAME"):
            self.cmd('sql vm create -n {} -g {} -l {} --license-type {} --sql-mgmt-type {}'
                     .format(sqlvm, resource_group, loc, 'PAYG', 'NoAgent'))

        # test create sqlvm with minimal required parameters
        sqlvm_1 = self.cmd('sql vm create -n {} -g {} -l {} --license-type {}'
                           .format(sqlvm, resource_group, loc, 'PAYG'),
                           checks=[
                               JMESPathCheck('name', sqlvm),
                               JMESPathCheck('location', loc),
                               JMESPathCheck('sqlServerLicenseType', 'PAYG'),
                               JMESPathCheck('sqlManagement', 'LightWeight')
                           ]).get_output_in_json()

        # test list sqlvm should be 1
        self.cmd('sql vm list -g {}'.format(resource_group), checks=[JMESPathCheck('length(@)', 1)])

        # test show of vm
        self.cmd('sql vm show -n {} -g {}'
                 .format(sqlvm, resource_group),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('id', sqlvm_1['id'])
                 ])

        # Check the id of the vm is correct in show
        self.cmd('sql vm show -n {} -g {}'
                 .format(sqlvm, resource_group),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('id', sqlvm_1['id'])
                 ])

        # test update sqlvm with management mode to make sure it updates to full.
        self.cmd('sql vm update -n {} -g {} --sql-mgmt-type {} --yes'
                 .format(sqlvm, resource_group, 'Full'),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('sqlManagement', 'Full')
                 ]).get_output_in_json()

        # test expand parameter: * - all settings exist
        expand_all = self.cmd('sql vm show -n {} -g {} --expand {}'
                              .format(sqlvm, resource_group, '*')
                              ).get_output_in_json()
        assert 'autoBackupSettings' in expand_all
        assert 'autoPatchingSettings' in expand_all
        assert 'keyVaultCredentialSettings' in expand_all
        assert 'serverConfigurationsManagementSettings' in expand_all

        # test expand parameter: single value - only specified setting exists
        expand_one = self.cmd('sql vm show -n {} -g {} --expand {}'
                              .format(sqlvm, resource_group, 'AutoBackupSettings')
                              ).get_output_in_json()
        assert 'autoBackupSettings' in expand_one
        assert 'autoPatchingSettings' not in expand_one
        assert 'keyVaultCredentialSettings' not in expand_one
        assert 'serverConfigurationsManagementSettings' not in expand_one

        # test expand parameter: comma-separated values - all specificed settings exist
        expand_comma = self.cmd('sql vm show -n {} -g {} --expand {}'
                                .format(sqlvm, resource_group, 'AutoPatchingSettings AutoBackupSettings')
                                ).get_output_in_json()
        assert 'autoBackupSettings' in expand_comma
        assert 'autoPatchingSettings' in expand_comma
        assert 'keyVaultCredentialSettings' not in expand_comma
        assert 'serverConfigurationsManagementSettings' not in expand_comma

        # test expand parameter: comma-separated values with * - all settings exist
        expand_comma_all = self.cmd('sql vm show -n {} -g {} --expand {}'
                                    .format(sqlvm, resource_group, 'AutoPatchingSettings * AutoBackupSettings')
                                    ).get_output_in_json()
        assert 'autoBackupSettings' in expand_comma_all
        assert 'autoPatchingSettings' in expand_comma_all
        assert 'keyVaultCredentialSettings' in expand_comma_all
        assert 'serverConfigurationsManagementSettings' in expand_comma_all

        # test license change
        self.cmd('sql vm update -n {} -g {} --license-type {}'
                 .format(sqlvm, resource_group, 'AHUB'),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('id', sqlvm_1['id']),
                     JMESPathCheck('sqlServerLicenseType', 'AHUB')
                 ])

        # test enabling R services
        self.cmd('sql vm update -n {} -g {} --enable-r-services {}'
                 .format(sqlvm, resource_group, True),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('id', sqlvm_1['id'])
                 ])

        # test autopatching enabling succeeds
        self.cmd('sql vm update -n {} -g {} --day-of-week {} --maintenance-window-duration {} --maintenance-window-start-hour {}'
                 .format(sqlvm, resource_group, 'Monday', 60, 22),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('id', sqlvm_1['id'])
                 ])

        # test autopatching disabling succeeds
        self.cmd('sql vm update -n {} -g {} --enable-auto-patching {}'
                 .format(sqlvm, resource_group, False),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('id', sqlvm_1['id'])
                 ])

        # test backup enabling works
        self.cmd('sql vm update -n {} -g {} --backup-schedule-type {} --full-backup-frequency {} --full-backup-start-hour {} --full-backup-duration {} '
                 '--sa-key {} --storage-account {} --retention-period {} --log-backup-frequency {}'
                 .format(sqlvm, resource_group, 'Manual', 'Weekly', 2, 2, key[0]['value'], sa['primaryEndpoints']['blob'], 30, 60),
                 checks=[
                     JMESPathCheck('name', sqlvm),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('id', sqlvm_1['id'])
                 ])

        # test delete vm
        self.cmd('sql vm delete -n {} -g {} --yes'
                 .format(sqlvm, resource_group),
                 checks=NoneCheck())

        # test list sql vm should be empty
        self.cmd('sql vm list -g {}'.format(resource_group), checks=[NoneCheck()])

    @ResourceGroupPreparer(name_prefix='sqlvm_cli_test_create')
    @SqlVirtualMachinePreparer(parameter_name='sqlvm1')
    @SqlVirtualMachinePreparer(parameter_name='sqlvm2')
    @SqlVirtualMachinePreparer(parameter_name='sqlvm3')
    @StorageAccountPreparer()
    def test_sqlvm_create_and_delete(self, resource_group, resource_group_location, sqlvm1, sqlvm2, sqlvm3, storage_account):

        # test create sqlvm1 with minimal required parameters
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {}'
                 .format(sqlvm1, resource_group, resource_group_location, 'PAYG'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG')
                 ])

        # test create sqlvm2 with AHUB changes inmediately
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {}'
                 .format(sqlvm2, resource_group, resource_group_location, 'AHUB'),
                 checks=[
                     JMESPathCheck('name', sqlvm2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'AHUB')
                 ])

        # test create sqlvm with sql connectivity settings
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {} --sql-mgmt-type {} --connectivity-type {} --port {} --sql-auth-update-username {} --sql-auth-update-pwd {}'
                 .format(sqlvm3, resource_group, resource_group_location, 'PAYG', 'Full', 'PUBLIC', 1433, 'sqladmin123', 'SecretPassword123'),
                 checks=[
                     JMESPathCheck('name', sqlvm3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG'),
                     JMESPathCheck('sqlManagement', 'Full')
                 ])

        # For allocation purposes, will delete the vms and re create them with different settings.
        # delete sqlvm1
        self.cmd('sql vm delete -n {} -g {} --yes'
                 .format(sqlvm1, resource_group),
                 checks=NoneCheck())

        # delete sqlvm2
        self.cmd('sql vm delete -n {} -g {} --yes'
                 .format(sqlvm2, resource_group),
                 checks=NoneCheck())

        # delete sqlvm3
        self.cmd('sql vm delete -n {} -g {} --yes'
                 .format(sqlvm3, resource_group),
                 checks=NoneCheck())

        # test create sqlvm1 with auto patching
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {} --sql-mgmt-type {} --day-of-week {} --maintenance-window-duration {} --maintenance-window-start-hour {}'
                 .format(sqlvm1, resource_group, resource_group_location, 'PAYG', 'Full', 'Monday', 60, 22),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG'),
                     JMESPathCheck('sqlManagement', 'Full')
                 ])

        # test create sqlvm1 with auto backup
        self.cmd('storage account update -n {} -g {} --set kind=StorageV2'.format(storage_account, resource_group))

        sa = self.cmd('storage account show -n {} -g {}'
                      .format(storage_account, resource_group)).get_output_in_json()

        key = self.cmd('storage account keys list -n {} -g {}'
                       .format(storage_account, resource_group)).get_output_in_json()

        self.cmd('sql vm create -n {} -g {} -l {} --license-type {} --backup-schedule-type {} --full-backup-frequency {} --full-backup-start-hour {} --full-backup-duration {} '
                 '--sa-key {} --storage-account {} --retention-period {} --log-backup-frequency {} --sql-mgmt-type {}'
                 .format(sqlvm2, resource_group, resource_group_location, 'PAYG', 'Manual', 'Weekly', 2, 2, key[0]['value'], sa['primaryEndpoints']['blob'], 30, 60, 'Full'),
                 checks=[
                     JMESPathCheck('name', sqlvm2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG'),
                     JMESPathCheck('sqlManagement', 'Full')
                 ])

        # test create sqlvm1 with R services on
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {} --enable-r-services {} --sql-mgmt-type {}'
                 .format(sqlvm3, resource_group, resource_group_location, 'PAYG', True, 'Full'),
                 checks=[
                     JMESPathCheck('name', sqlvm3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG'),
                     JMESPathCheck('sqlManagement', 'Full')
                 ])

    @ResourceGroupPreparer(name_prefix='sqlvm_cli_test_license')
    @SqlVirtualMachinePreparer(parameter_name='sqlvm1')
    def test_sqlvm_update_license_and_sku(self, resource_group, resource_group_location, sqlvm1):

        # test create sqlvm with sql license type and sku type.
        self.cmd('sql vm create -n {} -g {} -l {} --image-sku {} --license-type {}'
                 .format(sqlvm1, resource_group, resource_group_location, 'Enterprise', 'AHUB'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'AHUB'),
                     JMESPathCheck('sqlImageSku', 'Enterprise'),
                 ])

        # test sku change with license change.
        self.cmd('sql vm update -n {} -g {} --image-sku {} --license-type {}'
                 .format(sqlvm1, resource_group, 'Enterprise', 'PAYG'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlImageSku', 'Enterprise'),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG')
                 ])

        # delete sqlvm
        self.cmd('sql vm delete -n {} -g {} --yes'
                 .format(sqlvm1, resource_group),
                 checks=NoneCheck())

        # test create sqlvm with sql license type PAYG and sku type.
        self.cmd('sql vm create -n {} -g {} -l {} --image-sku {} --license-type {}'
                 .format(sqlvm1, resource_group, resource_group_location, 'Enterprise', 'PAYG'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG'),
                     JMESPathCheck('sqlImageSku', 'Enterprise'),
                 ])

        # test sku change without license change.
        self.cmd('sql vm update -n {} -g {} --image-sku {}'
                 .format(sqlvm1, resource_group, 'Enterprise'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlImageSku', 'Enterprise'),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG')
                 ])

        # test sku change with license change.
        self.cmd('sql vm update -n {} -g {} --image-sku {} --license-type {}'
                 .format(sqlvm1, resource_group, 'Enterprise', 'AHUB'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlImageSku', 'Enterprise'),
                     JMESPathCheck('sqlServerLicenseType', 'AHUB')
                 ])

        # test license change for DR only.
        self.cmd('sql vm update -n {} -g {} --license-type {}'
                 .format(sqlvm1, resource_group, 'DR'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlImageSku', 'Enterprise'),
                     JMESPathCheck('sqlServerLicenseType', 'DR')
                 ])

        # delete sqlvm
        self.cmd('sql vm delete -n {} -g {} --yes'
                 .format(sqlvm1, resource_group),
                 checks=NoneCheck())

        # test create sqlvm with sql license type DR.
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {}'
                 .format(sqlvm1, resource_group, resource_group_location, 'DR'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlServerLicenseType', 'DR'),
                 ])


class SqlVmGroupScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account1', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='storage_account2', kind='StorageV2')
    def test_sqlvm_group_mgmt(self, resource_group, resource_group_location, storage_account1, storage_account2):

        name = 'sqlvmgroup'
        image_offer = 'SQL2017-WS2016'
        image_sku = 'Enterprise'
        domain = 'domain.com'
        operator_acc = 'myvmadmin'
        sql_service_acc = 'sqlservice'

        sa_1 = self.cmd('storage account show -n {} -g {}'
                        .format(storage_account1, resource_group)).get_output_in_json()

        key_1 = self.cmd('storage account keys list -n {} -g {}'
                         .format(storage_account1, resource_group)).get_output_in_json()

        sa_2 = self.cmd('storage account show -n {} -g {}'
                        .format(storage_account2, resource_group)).get_output_in_json()

        key_2 = self.cmd('storage account keys list -n {} -g {}'
                         .format(storage_account2, resource_group)).get_output_in_json()

        # create sql vm group
        sqlvmgroup = self.cmd('sql vm group create -n {} -g {} -l {} -i {} -s {} -f {} -p {} -k {} -e {} -u {}'
                              .format(name, resource_group, resource_group_location, image_offer, image_sku,
                                      domain, operator_acc, key_1[0]['value'], sql_service_acc, sa_1['primaryEndpoints']['blob']),
                              checks=[
                                  JMESPathCheck('name', name),
                                  JMESPathCheck('location', resource_group_location),
                                  JMESPathCheck('provisioningState', "Succeeded")
                              ]).get_output_in_json()

        # test list sqlvm should be 1
        self.cmd('sql vm group list -g {}'.format(resource_group), checks=[JMESPathCheck('length(@)', 1)])

        # test show of the group
        self.cmd('sql vm group show -n {} -g {}'
                 .format(name, resource_group),
                 checks=[
                     JMESPathCheck('name', name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheck('sqlImageOffer', image_offer),
                     JMESPathCheck('sqlImageSku', image_sku),
                     JMESPathCheck('id', sqlvmgroup['id'])
                 ])

        # Change the storage account url and key
        self.cmd('sql vm group update -n {} -g {} -u {} -k {}'
                 .format(name, resource_group, sa_2['primaryEndpoints']['blob'], key_2[0]['value']),
                 checks=[
                     JMESPathCheck('name', name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('wsfcDomainProfile.storageAccountUrl', sa_2['primaryEndpoints']['blob'])
                 ])

        # change the domain
        self.cmd('sql vm group update -n {} -g {} -f {} -k {}'
                 .format(name, resource_group, 'my' + domain, key_2[0]['value']),
                 checks=[
                     JMESPathCheck('name', name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('wsfcDomainProfile.domainFqdn', 'my' + domain)
                 ])

        # change the operator account
        self.cmd('sql vm group update -n {} -g {} -p {} -k {}'
                 .format(name, resource_group, 'my' + operator_acc, key_2[0]['value']),
                 checks=[
                     JMESPathCheck('name', name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('wsfcDomainProfile.clusterOperatorAccount', 'my' + operator_acc)
                 ])

        # test delete vm
        self.cmd('sql vm group delete -n {} -g {} --yes'
                 .format(name, resource_group),
                 checks=NoneCheck())

        # test list sql vm should be empty
        self.cmd('sql vm group list -g {}'.format(resource_group), checks=[NoneCheck()])


class SqlVmAndGroupScenarioTest(ScenarioTest):
    """
    This is a very lengthy test, it may take more than 45 minutes to run.
    """
    @ResourceGroupPreparer()
    @DomainPreparer()
    @SqlVirtualMachinePreparer(parameter_name='sqlvm1')
    @StorageAccountPreparer(kind='StorageV2')
    def test_sqlvm_add_and_remove(self, resource_group, resource_group_location, domainvm, sqlvm1, storage_account):

        add_account_script = '\"Set-AdUser -UserPrincipalName admin123@domain.com -Identity admin123 -PasswordNeverExpires $true\"'

        # add account to domain controller
        self.cmd('vm run-command invoke -n {} -g {} --command-id RunPowerShellScript --scripts {}'
                 .format('adVM', resource_group, add_account_script))

        parameters_string = ('location={} domainJoinUserName=domain\\\\admin123 domainJoinUserPassword=SecretPassword123 '
                             'domainFQDN=domain.com vmList={}').format(resource_group_location, sqlvm1)

        # join vms to the domain
        self.cmd('deployment group create --name {} -g {} --template-uri {} --parameters {}'
                 .format('joinvms',
                         resource_group,
                         'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/quickstarts/microsoft.compute/vm-domain-join-existing/azuredeploy.json',
                         parameters_string))

        # Create the sqlvm group
        sa = self.cmd('storage account show -n {} -g {}'
                      .format(storage_account, resource_group)).get_output_in_json()

        key = self.cmd('storage account keys list -n {} -g {}'
                       .format(storage_account, resource_group)).get_output_in_json()

        sqlvmgroup = self.cmd('sql vm group create -n {} -g {} -l {} -i {} -s {} -f {} -p {} -k {} -e {} -u {} --bootstrap-acc {}'
                              .format('cligroup', resource_group, resource_group_location, 'SQL2017-WS2016', 'Enterprise',
                                      'domain.com', 'admin123', key[0]['value'], 'admin123', sa['primaryEndpoints']['blob'], 'admin123')).get_output_in_json()

        # test create sqlvm1
        self.cmd('sql vm create -n {} -g {} -l {} --license-type {} --connectivity-type {} --port {} --sql-auth-update-pwd {} --sql-auth-update-username {} --sql-mgmt-type {}'
                 .format(sqlvm1, resource_group, resource_group_location, 'PAYG', 'PRIVATE', 1433, 'admin123', 'SecretPassword123', 'Full'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('sqlServerLicenseType', 'PAYG')
                 ]).get_output_in_json()

        self.cmd('sql vm add-to-group -n {} -g {} -r {} -p {} -s {} -b {}'
                 .format(sqlvm1, resource_group, sqlvmgroup['id'], 'SecretPassword123', 'SecretPassword123', 'SecretPassword123'),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded"),
                     JMESPathCheckExists('sqlVirtualMachineGroupResourceId')
                 ])

        # Remove from group
        self.cmd('sql vm remove-from-group -n {} -g {}'
                 .format(sqlvm1, resource_group),
                 checks=[
                     JMESPathCheck('name', sqlvm1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', "Succeeded")
                 ])
