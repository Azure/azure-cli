# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import secrets
import shlex
import time
from contextlib import ExitStack

from azure.core.exceptions import HttpResponseError
from knack.log import get_logger

from azure.cli.testsdk.preparers import AbstractPreparer
from azure.cli.testsdk.scenario_tests import RecordingProcessor


logger = get_logger(__name__)


class SqlInstancePasswordReplacer(RecordingProcessor):
    def __init__(self, password):
        self.password = password

    def process_request(self, request):
        if isinstance(request.body, bytes):
            request.body = request.body.replace(self.password.encode(), b'REDACTED')
        elif isinstance(request.body, str):
            request.body = request.body.replace(self.password, 'REDACTED')
        return request


class SqlInstanceSnapshotPreparer(AbstractPreparer):
    def __init__(self):
        super().__init__('sqlsnap', 24)
        self.cleanup = None

    @property
    def moniker(self):
        # This preparer owns no named Azure resource; only its environment allocates resource names.
        return self.name_prefix

    def create_resource(self, name, **kwargs):
        with ExitStack() as cleanup:
            environment = SqlInstanceSnapshotEnvironment(self.test_class_instance)
            cleanup.callback(environment.close)
            environment.create()
            self.cleanup = cleanup.pop_all()
            return {'snapshot_environment': environment}

    def remove_resource(self, name, **kwargs):
        self.cleanup.close()


class SqlInstanceSnapshotEnvironment:
    location = 'eastus2'
    image = 'microsoftsqlserver:sql2022-ws2022:enterprise-gen2:latest'
    child_databases = ['clitestdb1', 'clitestdb2']
    sql_username = 'sqlsnapsetup'

    def __init__(self, test):
        self.test = test
        self.kwargs = {'sub': test.get_subscription_id()}
        self.groups = []
        self.vaults = []
        self.identities = []
        self.role_assignments = []
        self.retained_groups = set()
        self.target = None
        self.identity = None
        self.tags = {
            'product': 'azurecli', 'Workload': 'SQLInstance', 'TestType': 'CLILiveTest',
            'Purpose': 'CLI SQL instance snapshot lifecycle validation',
        }
        extra_tags = json.loads(os.environ.get('AZURE_BACKUP_SQL_TEST_TAGS', '{}'))
        if not isinstance(extra_tags, dict) or any(
                not isinstance(key, str) or not key or not isinstance(value, str) or not value
                for key, value in extra_tags.items()):
            raise ValueError('AZURE_BACKUP_SQL_TEST_TAGS must be a JSON object of nonempty string tags.')
        self.tags.update(extra_tags)
        self.kwargs['tags'] = ' '.join(shlex.quote(key + '=' + value) for key, value in self.tags.items())
        self.password = secrets.token_urlsafe(24) + 'aA1!'
        self.sql_password = secrets.token_urlsafe(24) + 'aA1!'
        test.recording_processors.insert(0, SqlInstancePasswordReplacer(self.password))
        test.recording_processors.insert(0, SqlInstancePasswordReplacer(self.sql_password))

    def _cmd(self, command, **kwargs):
        values = dict(self.kwargs, **kwargs)
        return self.test.cmd(command.format(**values) + ' --subscription "{}"'.format(values['sub']))

    def _group(self, location):
        name = self.test.create_random_name('cli-sqlsnap-rg-', 40)
        exists = self._cmd('group exists -n "{group}"', group=name).get_output_in_json()
        self.test.assertFalse(exists, 'The SQL snapshot test must never reuse an existing resource group.')
        # Track the owned name before creation so a partially successful create can also be cleaned up.
        self.groups.append(name)
        self._cmd('group create -n "{group}" -l "{location}" --tags {tags}', group=name, location=location)
        return name

    def _delete_group(self, group):
        self.test.assertIn(group, self.groups, 'Refusing to delete a resource group not created by this test.')
        if group in self.retained_groups:
            logger.warning('Retaining test resource group %s because its vault was not removed; '
                           'see the preceding soft-delete warning or cleanup error.', group)
            return
        if not self._cmd('group exists -n "{group}"', group=group).get_output_in_json():
            logger.info('Test resource group %s does not exist; no deletion is required.', group)
            return
        self._cmd('group delete -n "{group}" --yes', group=group)

    def _vault(self, group, location):
        self.test.assertIn(group, self.groups)
        name = self.test.create_random_name('cli-sqlsnap-vault-', 40)
        self._cmd('backup vault create -g "{group}" -n "{name}" -l "{location}" --tags {tags}',
                  group=group, name=name, location=location)
        self.vaults.append((group, name))
        self._cmd('backup vault update -g "{group}" -n "{name}" --backup-storage-redundancy LocallyRedundant',
                  group=group, name=name)
        properties = self._cmd(
            'backup vault backup-properties show -g "{group}" -n "{name}"',
            group=group, name=name).get_output_in_json()
        states = [entry['properties']['softDeleteFeatureState'] for entry in properties
                  if 'softDeleteFeatureState' in entry.get('properties', {})]
        self.test.assertEqual(1, len(states), 'The vault must expose its soft-delete configuration.')
        if states[0].lower() == 'enabled':
            self._cmd('backup vault backup-properties set -g "{group}" -n "{name}" '
                      '--soft-delete-feature-state Disable', group=group, name=name)
            configured = self._cmd(
                'backup vault backup-properties show -g "{group}" -n "{name}"',
                group=group, name=name).get_output_in_json()
            self.test.assertTrue(any(
                entry.get('properties', {}).get('softDeleteFeatureState', '').lower() == 'disabled'
                for entry in configured), 'Disabling soft delete did not take effect.')
        elif states[0].lower() == 'alwayson':
            logger.warning('Soft delete is AlwaysOn for test vault %s; it cannot be disabled.', name)
        else:
            self.test.assertEqual('disabled', states[0].lower())
        return name

    def _items(self, group, vault, workload):
        return self._cmd(
            'backup item list -g "{group}" -v "{vault}" --backup-management-type AzureWorkload '
            '--workload-type {workload}', group=group, vault=vault, workload=workload).get_output_in_json()

    def _disable(self, group, vault, item, workload):
        container = item['id'].split('/protectedItems/')[0].rsplit('/', 1)[1]
        self._cmd(
            'backup protection disable -g "{group}" -v "{vault}" -c "{container}" -i "{item}" '
            '--backup-management-type AzureWorkload --workload-type {workload} '
            '--delete-backup-data true --yes',
            group=group, vault=vault, container=container, item=item['name'], workload=workload)

    def delete_backup_data(self, verify=False):
        group, vault = self.kwargs['rg'], self.kwargs['vault']
        self.test.assertIn((group, vault), self.vaults, 'Refusing to change protection in an unowned vault.')
        instances = self._items(group, vault, 'SQLInstance')
        for item in instances:
            if not item['properties'].get('isScheduledForDeferredDelete'):
                self._disable(group, vault, item, 'SQLInstance')
        databases = self._items(group, vault, 'MSSQL')
        if verify:
            self.test.assertEqual(set(self.child_databases),
                                  {item['properties']['friendlyName'] for item in databases})
            for item in databases:
                self.test.assertEqual('ProtectionStopped', item['properties']['protectionState'])
                self.test.assertFalse(item['properties'].get('isScheduledForDeferredDelete', False))
        for item in databases:
            if not item['properties'].get('isScheduledForDeferredDelete'):
                self._disable(group, vault, item, 'MSSQL')

    def _delete_vault(self, group, vault):
        self.test.assertIn((group, vault), self.vaults)
        # Prevent subsequent resource-group deletion if any protection cleanup step fails.
        self.retained_groups.add(group)
        has_soft_deleted_items = False
        for workload in ('SQLInstance', 'MSSQL'):
            for item in self._items(group, vault, workload):
                if item['properties'].get('isScheduledForDeferredDelete'):
                    has_soft_deleted_items = True
                else:
                    self._disable(group, vault, item, workload)
        containers = self._cmd(
            'backup container list -g "{group}" -v "{vault}" --backup-management-type AzureWorkload',
            group=group, vault=vault).get_output_in_json()
        for container in containers:
            if container['properties']['registrationStatus'] == 'Registered':
                try:
                    self._cmd(
                        'backup container unregister -g "{group}" -v "{vault}" -c "{container}" '
                        '--backup-management-type AzureWorkload --yes',
                        group=group, vault=vault, container=container['name'])
                except HttpResponseError as error:
                    if not has_soft_deleted_items or not str(error).startswith('(CloudInternalError)'):
                        raise
                    logger.warning(
                        'Container %s returned the expected CloudInternalError during unregistration '
                        'in test vault %s with soft-deleted backup data. Retaining the vault and '
                        'continuing cleanup: %s', container['name'], vault, error)
        remaining_items = self._items(group, vault, 'SQLInstance') + self._items(group, vault, 'MSSQL')
        remaining_containers = self._cmd(
            'backup container list -g "{group}" -v "{vault}" --backup-management-type AzureWorkload',
            group=group, vault=vault).get_output_in_json()
        retained = any(item['properties'].get('isScheduledForDeferredDelete') for item in remaining_items)
        retained = retained or any(
            item['properties']['registrationStatus'] == 'SoftDeleted' for item in remaining_containers)
        if retained:
            logger.warning('Retained test vault %s in %s due to soft-deleted items/containers. '
                           'Other test-created resources will be deleted.', vault, group)
            return
        self._cmd('backup vault delete -g "{group}" -n "{vault}" --yes', group=group, vault=vault)
        self.retained_groups.remove(group)

    def close(self):
        # ExitStack runs every callback even if an earlier cleanup operation raises.
        with ExitStack() as cleanup:
            for group in self.groups:
                cleanup.callback(self._delete_group, group)
            for group, identity in self.identities:
                cleanup.callback(self._cmd, 'identity delete -g "{group}" -n "{identity}"',
                                 group=group, identity=identity)
            for assignment in self.role_assignments:
                cleanup.callback(self._cmd, 'role assignment delete --ids "{assignment}"', assignment=assignment)
            for group, vault in self.vaults:
                cleanup.callback(self._delete_vault, group, vault)

    def _identity(self, group, location, scopes):
        identity = self._cmd(
            'identity create -g "{group}" -n "{name}" -l "{location}" --tags {tags}',
            group=group, name=self.test.create_random_name('cli-sqlsnap-id-', 32),
            location=location).get_output_in_json()
        self.identities.append((group, identity['name']))
        for scope in scopes:
            self.test.assertIn(scope, self.groups)
            assignment = self._cmd(
                'role assignment create --name "{assignment}" '
                '--assignee-object-id "{principal}" --assignee-principal-type ServicePrincipal '
                '--role "Azure Backup Snapshot Contributor" '
                '--scope "/subscriptions/{sub}/resourceGroups/{scope}"',
                assignment=self.test.create_guid(), principal=identity['principalId'], scope=scope
            ).get_output_in_json()
            self.role_assignments.append(assignment['id'])
        return identity

    def _vm(self, group, location, identity, seed):
        name = self.test.create_random_name('sqlsnap', 15)
        self._cmd(
            'vm create -g "{group}" -n "{name}" -l "{location}" --image "{image}" '
            '--size {size} --admin-username sqlsnapadmin --admin-password "{password}" '
            '--public-ip-sku Standard --nsg-rule NONE --assign-identity "[system]" "{identity}"{disks} --tags {tags}',
            group=group, name=name, location=location, image=self.image, password=self.password,
            size='Standard_B2as_v2' if seed else 'Standard_B4as_v2',
            identity=identity['id'], disks=' --data-disk-sizes-gb 32 32' if seed else ''
        ).get_output_in_json()
        assigned = self._cmd('vm identity show -g "{group}" -n "{name}"',
                             group=group, name=name).get_output_in_json()
        self.test.assertTrue(assigned['principalId'], 'The SQL VM must have a system-assigned identity.')
        self.test.assertIn(identity['id'].lower(),
                           {item.lower() for item in assigned['userAssignedIdentities']})
        self._cmd(
            'sql vm create -g "{group}" -n "{name}" -l "{location}" --license-type PAYG '
            '--sql-mgmt-type Full --connectivity-type LOCAL --sql-auth-update-username "{sql_username}" '
            '--sql-auth-update-pwd "{sql_password}" --tags {tags}',
            group=group, name=name, location=location,
            sql_username=self.sql_username, sql_password=self.sql_password)
        self.run_sql(group, name, 'Seed' if seed else 'Target')
        return name

    def run_sql(self, group, vm, mode):
        self.test.assertIn(group, self.groups, 'Run Command must only target test-created VMs.')
        with open(os.path.join(os.path.dirname(__file__), 'sql_instance_test_setup.ps1'),
                  encoding='utf-8') as script_file:
            # ScenarioTest.cmd formats its string again after _cmd expands the arguments.
            script = shlex.quote(script_file.read().replace('{', '{{').replace('}', '}}'))
        name = 'sqlsnap-setup-' + mode.lower()
        self._cmd(
            'vm run-command create -g "{group}" --vm-name "{vm}" --run-command-name "{name}" '
            '--script {script} --parameters "Mode={mode}" "SqlUsername={sql_username}" '
            '--protected-parameters "SqlPassword={sql_password}" '
            '--async-execution false --timeout-in-seconds 1800 --tags {tags}',
            group=group, vm=vm, name=name, script=script, mode=mode,
            sql_username=self.sql_username, sql_password=self.sql_password)
        view = self._cmd(
            'vm run-command show -g "{group}" --vm-name "{vm}" --run-command-name "{name}" '
            '--instance-view --query instanceView',
            group=group, vm=vm, name=name).get_output_in_json()
        self.test.assertIsInstance(view, dict, 'Managed Run Command returned no guest instance view.')
        self.test.assertEqual('Succeeded', view.get('executionState'), view)
        self.test.assertEqual(0, view.get('exitCode'), view)
        self.test.assertIn('SQLSNAP-SETUP-OK:' + mode, view.get('output', ''),
                           'Managed Run Command returned no guest-script success marker: ' + str(view))

    def _register(self, vault_group, vault, vm_group, vm):
        self._cmd(
            'backup container register -g "{group}" -v "{vault}" --backup-management-type AzureWorkload '
            '--workload-type MSSQL --resource-id '
            '"/subscriptions/{sub}/resourceGroups/{vm_group}/providers/Microsoft.Compute/virtualMachines/{vm}"',
            group=vault_group, vault=vault, vm_group=vm_group, vm=vm)
        self.run_sql(vm_group, vm, 'Permissions')

        def find_container():
            containers = self._cmd(
                'backup container list -g "{group}" -v "{vault}" --backup-management-type AzureWorkload',
                group=vault_group, vault=vault).get_output_in_json()
            matches = [item for item in containers if item['properties']['friendlyName'].lower() == vm.lower()]
            if not matches:
                return None
            self.test.assertEqual(1, len(matches))
            return matches[0]['name']

        container = self.wait_for(find_container, 'SQL VM registration', attempts=60, delay=30)
        self._cmd('backup protectable-item initialize -g "{group}" -v "{vault}" '
                  '--container-name "{container}" --workload-type MSSQL',
                  group=vault_group, vault=vault, container=container)

        def find_instance():
            instances = self._cmd(
                'backup protectable-item list -g "{group}" -v "{vault}" --workload-type MSSQL '
                '--protectable-item-type SQLInstance --server-name "{vm}"',
                group=vault_group, vault=vault, vm=vm).get_output_in_json()
            selected = [item for item in instances if item['properties']['friendlyName'].lower() == 'mssqlserver']
            if not selected:
                return None
            self.test.assertEqual(1, len(selected))
            return selected[0]['name']

        return container, self.wait_for(find_instance, 'SQL instance discovery', attempts=60, delay=30)

    def wait_for(self, query, description, attempts, delay):
        for attempt in range(attempts):
            value = query()
            if value:
                return value
            if attempt + 1 < attempts and (self.test.in_recording or self.test.is_live):
                time.sleep(delay)
        self.test.fail('Timed out waiting for {} after {} attempts ({} seconds between live attempts).'.format(
            description, attempts, delay))

    def create(self):
        target_location = self.location
        vault_group = self._group(self.location)
        source_group = self._group(self.location)
        target_group = self._group(target_location)
        target_vault_group = vault_group
        vault = self._vault(vault_group, self.location)
        target_vault = vault
        self.identity = self._identity(source_group, self.location, [source_group])
        target_identity = self._identity(target_group, target_location, [source_group, target_group])
        source_vm = self._vm(source_group, self.location, self.identity, seed=True)
        target_vm = self._vm(target_group, target_location, target_identity, seed=False)
        container, item = self._register(vault_group, vault, source_group, source_vm)
        target_container, _ = self._register(target_vault_group, target_vault, target_group, target_vm)
        self.kwargs.update(
            rg=vault_group, vault=vault, policy_snapshot_rg=source_group,
            source_vm_rg=source_group, protection_server=source_vm, protection_instance='mssqlserver',
            container=container, item=item, protection_container=container,
            child_database_args=' '.join('"{}"'.format(name) for name in self.child_databases))
        self.kwargs['vault_args'] = '--subscription "{sub}" -g "{rg}" -v "{vault}"'.format(**self.kwargs)
        self.kwargs['instance_args'] = (
            '{vault_args} -c "{container}" --item-name "{item}" '
            '--backup-management-type AzureWorkload --workload-type SQLInstance'.format(**self.kwargs))
        self.test.kwargs.update(self.kwargs)
        self.target = dict(
            target_rg=target_vault_group, target_vault=target_vault, target_container=target_container,
            target_server=target_vm, target_instance='mssqlserver', target_vm_rg=target_group,
            target_item='*_' + self.test.create_random_name('cli_snap_', 24),
            restore_snapshot_rg=target_group, restore_identity_id=target_identity['id'],
            volume_mappings={'F:\\': 'X:\\', 'G:\\': 'Y:\\'})
