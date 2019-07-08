# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json


def test_backup_wl_container(self, container_name1, container_name2, resource_group, vault_name, workload_type, subscription, id):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'rg': resource_group,
        'wt': workload_type,
        'sub': subscription,
        'id': id
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    container_json = self.cmd('backup container show -n {name} -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fname}'),
        self.check('properties.healthStatus', 'Healthy'),
        self.check('properties.registrationStatus', 'Registered'),
        self.check('resourceGroup', '{rg}')
    ]).get_output_in_json()

    self.kwargs['container_name'] = container_json['name']

    self.cmd('backup container show -n {container_name} -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fname}'),
        self.check('properties.healthStatus', 'Healthy'),
        self.check('properties.registrationStatus', 'Registered'),
        self.check('name', '{container_name}'),
        self.check('resourceGroup', '{rg}')
    ]).get_output_in_json()

    self.assertIn(vault_name.lower(), container_json['id'].lower())
    self.assertIn(container_name1.lower(), container_json['name'].lower())

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?properties.friendlyName == '{fname}'])", 1)])

    self.cmd('backup container re-register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -y -n{name}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])


def test_backup_wl_policy(self, container_name1, container_name2, resource_group, vault_name, policy_name, workload_type, subscription, item, id, item_type, item_id, policy_new):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'default': 'HourlyLogBackup',
        'rg': resource_group,
        'item': item,
        'id': id,
        'item_id': item_id,
        'pit': item_type,
        'policy_new': self.create_random_name('clitest-policy', 24)
    })

    self.kwargs['policy1_json'] = self.cmd('backup policy show -g {rg} -v {vault} -n {policy} -bmt AzureWorkload', checks=[
        self.check('[].name', '[\'{policy}\']'),
        self.check('[].resourceGroup', '[\'{rg}\']')
    ]).get_output_in_json()[0]

    self.kwargs['policy_json'] = json.dumps(self.kwargs['policy1_json'], separators=(',', ':')).replace('\'', '\\\'').replace('"', '\\"')

    self.cmd("backup policy new -g {rg} -v {vault} --policy {policy_json} -bmt AzureWorkload -wt {wt} -n {policy_new}", checks=[
        self.check('name', '{policy_new}'),
        self.check('resourceGroup', '{rg}')
    ])

    self.cmd('backup policy list -g {rg} -v {vault}', checks=[
        self.check("length([?name == '{default}'])", 1),
        self.check("length([?name == '{policy}'])", 1),
        self.check("length([?name == '{policy_new}'])", 1)
    ])

    self.kwargs['policy1_json']['properties']['settings']['isCompression'] = 'true'
    self.kwargs['policy1_json']['properties']['settings']['issqlcompression'] = 'true'
    self.kwargs['policy1_json'] = json.dumps(self.kwargs['policy1_json'], separators=(',', ':')).replace('\'', '\\\'').replace('"', '\\"')

    if workload_type == 'MSSQL':
        self.cmd("backup policy set -g {rg} -v {vault} --policy {policy1_json} -n {policy_new}", checks=[
            self.check('name', '{policy_new}'),
            self.check('resourceGroup', '{rg}')
        ])

    self.cmd('backup policy show -g {rg} -v {vault} -n {policy_new} -bmt AzureWorkload', checks=[
        self.check('[].name', '[\'{policy_new}\']'),
        self.check('[].resourceGroup', '[\'{rg}\']')
    ])

    self.cmd('backup policy delete -g {rg} -v {vault} -n {policy_new}')

    self.cmd('backup policy list -g {rg} -v {vault}', checks=[
        self.check("length([?name == '{default}'])", 1),
        self.check("length([?name == '{policy}'])", 1),
        self.check("length([?name == '{policy_new}'])", 0)
    ])


def test_backup_wl_item(self, container_name1, container_name2, resource_group, vault_name, policy_name, workload_type, subscription, item, id, item_type, item_id):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'default': 'HourlyLogBackup',
        'rg': resource_group,
        'item': item,
        'fitem': item.split(';')[-1],
        'id': id,
        'item_id': item_id,
        'pit': item_type
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.kwargs['protectable_item'] = json.dumps(self.cmd('backup protectable-item show -v {vault} -g {rg} -pit {pit} -s {fname} -n {item} -wt {wt}').get_output_in_json(), separators=(',', ':')).replace('"', '\\"')

    self.cmd('backup protection enable-for-AzureWL -v {vault} -g {rg} -p {policy} -pi {protectable_item}')

    self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} -bmt AzureWorkload --query name').get_output_in_json()

    item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fitem}'),
        self.check('properties.protectedItemHealthStatus', 'IRPending'),
        self.check('properties.protectionState', 'IRPending'),
        self.check('properties.protectionStatus', 'Healthy'),
        self.check('resourceGroup', '{rg}')
    ]).get_output_in_json()

    self.assertIn(vault_name.lower(), item1_json['id'].lower())
    self.assertIn(container_name2.lower(), item1_json['properties']['containerName'].lower())
    self.assertIn(container_name2.lower(), item1_json['properties']['sourceResourceId'].lower())
    self.assertIn(self.kwargs['default'].lower(), item1_json['properties']['policyId'].lower())

    self.kwargs['container1_fullname'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} -bmt AzureWorkload --query name').get_output_in_json()

    self.cmd('backup item show -g {rg} -v {vault} -c {container1_fullname} -n {item} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fitem}'),
        self.check('properties.protectedItemHealthStatus', 'IRPending'),
        self.check('properties.protectionState', 'IRPending'),
        self.check('properties.protectionStatus', 'Healthy'),
        self.check('resourceGroup', '{rg}')
    ])

    self.kwargs['item1_fullname'] = item1_json['name']

    self.cmd('backup item show -g {rg} -v {vault} -c {container1_fullname} -n {item1_fullname} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fitem}'),
        self.check('properties.protectedItemHealthStatus', 'IRPending'),
        self.check('properties.protectionState', 'IRPending'),
        self.check('properties.protectionStatus', 'Healthy'),
        self.check('resourceGroup', '{rg}')
    ])

    self.cmd('backup item list -g {rg} -v {vault} -c {container1} -bmt AzureWorkload -wt {wt}', checks=[
        self.check("length(@)", 1),
        self.check("length([?properties.friendlyName == '{fitem}'])", 1)
    ])

    self.cmd('backup item list -g {rg} -v {vault} -c {container1_fullname} -bmt AzureWorkload -wt {wt}', checks=[
        self.check("length(@)", 1),
        self.check("length([?properties.friendlyName == '{fitem}'])", 1)
    ])

    self.cmd('backup item list -g {rg} -v {vault} -bmt AzureWorkload -wt {wt}', checks=[
        self.check("length(@)", 1),
        self.check("length([?properties.friendlyName == '{fitem}'])", 1)
    ])

    self.cmd('backup item set-policy -g {rg} -v {vault} -c {container1} -n {item1_fullname} -p {policy} -bmt AzureWorkload', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "ConfigureBackup"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} -bmt AzureWorkload').get_output_in_json()
    self.assertIn(policy_name.lower(), item1_json['properties']['policyId'].lower())

    self.cmd('backup protection disable -v {vault} -g {rg} -i {item_id} -y --delete-backup-data true')

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])


def test_backup_wl_rp(self, container_name, resource_group, vault_name, item_name, workload_type, subscription, item_type, container_name2, policy_name, id, item_id):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name,
        'rg': resource_group,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'item': item_name,
        'pit': item_type,
        'item_id': item_id,
        'id': id
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.kwargs['protectable_item'] = json.dumps(self.cmd('backup protectable-item show -v {vault} -g {rg} -pit {pit} -s {fname} -n {item} -wt {wt}').get_output_in_json(), separators=(',', ':')).replace('"', '\\"')

    self.cmd('backup protection enable-for-AzureWL -v {vault} -g {rg} -p {policy} -pi {protectable_item}')

    self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} -wt {wt} --query [].name', checks=[
        self.check("length(@)", 1)
    ])

    rp1_json = self.cmd('backup recoverypoint logchain show -g {rg} -v {vault} -c {name} -i {item} -wt {wt}', checks=[
        self.check('[].resourceGroup', '[\'{rg}\']')
    ]).get_output_in_json()
    self.assertIn(vault_name.lower(), rp1_json[0]['id'].lower())
    self.assertIn(container_name.lower(), rp1_json[0]['id'].lower())

    rp2_json = self.cmd('backup recoverypoint logchain show -g {rg} -v {vault} -c {name} -i {item} -wt {wt}', checks=[
        self.check('[].resourceGroup', '[\'{rg}\']')
    ]).get_output_in_json()
    self.assertIn(vault_name.lower(), rp2_json[0]['id'].lower())
    self.assertIn(container_name.lower(), rp2_json[0]['id'].lower())

    self.cmd('backup protection disable -v {vault} -g {rg} -i {item_id} -y --delete-backup-data true')

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])


def test_backup_wl_protection(self, container_name1, container_name2, resource_group, vault_name, policy_name, workload_type, subscription, item, id, item_type, item_id, backup_entity_friendly_name):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'default': 'HourlyLogBackup',
        'rg': resource_group,
        'item': item,
        'fitem': item.split(';')[-1],
        'id': id,
        'item_id': item_id,
        'pit': item_type,
        'entityFriendlyName': backup_entity_friendly_name
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.kwargs['protectable_item'] = json.dumps(self.cmd('backup protectable-item show -v {vault} -g {rg} -pit {pit} -s {fname} -n {item} -wt {wt}').get_output_in_json(), separators=(',', ':')).replace('"', '\\"')

    self.cmd('backup protection enable-for-AzureWL -v {vault} -g {rg} -p {policy} -pi {protectable_item}', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "ConfigureBackup"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} -bmt AzureWorkload --query name').get_output_in_json()

    self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item_id} -bt Full -rt 1-7-2020 -ec false', checks=[
        self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
        self.check("properties.operation", "Backup"),
        self.check("properties.status", "InProgress"),
        self.check("resourceGroup", '{rg}')
    ]).get_output_in_json()

    self.kwargs['job'] = self.kwargs['backup_job']['name']

    self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

    self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fitem}'),
        self.check('properties.protectedItemHealthStatus', 'Healthy'),
        self.check('properties.protectionState', 'Protected'),
        self.check('properties.protectionStatus', 'Healthy'),
        self.check('resourceGroup', '{rg}')
    ])

    self.cmd('backup protection disable -v {vault} -g {rg} -i {item_id} -y', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "DisableBackup"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} -bmt AzureWorkload', checks=[
        self.check("properties.friendlyName", '{fitem}'),
        self.check("properties.protectionState", "ProtectionStopped"),
        self.check("resourceGroup", '{rg}')
    ])

    self.cmd('backup protection disable -v {vault} -g {rg} -i {item_id} -y --delete-backup-data true', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "DeleteBackupData"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])


def test_backup_wl_auto_protection(self, container_name1, container_name2, resource_group, vault_name, policy_name, workload_type, subscription, item, id, item_type, item_id, backup_entity_friendly_name):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'default': 'HourlyLogBackup',
        'rg': resource_group,
        'item': item,
        'fitem': item.split(';')[-1],
        'id': id,
        'item_id': item_id,
        'pit': item_type,
        'entityFriendlyName': backup_entity_friendly_name
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.kwargs['protectable_item'] = self.cmd('backup protectable-item show -v {vault} -g {rg} -pit {pit} -s {fname} -n {item} -wt {wt}').get_output_in_json()

    self.kwargs['protectable_item_name'] = self.kwargs['protectable_item']['name']

    self.kwargs['protectable_item'] = json.dumps(self.kwargs['protectable_item'], separators=(',', ':')).replace('"', '\\"')

    self.cmd('backup protection auto-enable-for-AzureWL -v {vault} -g {rg} -p {policy} -pi {protectable_item}', checks=[
        self.check("status", "True")
    ])

    self.cmd('backup protection disable auto-for-AzureWL -v {vault} -g {rg} -i {protectable_item_name}', checks=[
        self.check("status", "True")
    ])

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])


def test_backup_wl_protectable_item(self, container_name1, container_name2, resource_group, vault_name, policy_name, workload_type, subscription, item, id, item_type, item_id):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'default': 'HourlyLogBackup',
        'rg': resource_group,
        'item': item,
        'id': id,
        'item_id': item_id,
        'pit': item_type,
        'protectable_item_name': 'NEWDB' if workload_type == 'SAPHANA' else 'newdb',
        'pit_hana': 'SAPHanaDatabase'
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --query properties.friendlyName -bmt AzureWorkload').get_output_in_json()

    self.cmd('backup protectable-item list -g {rg} -v {vault} -wt {wt}', checks=[
        self.check("length([?properties.friendlyName == '{protectable_item_name}'])", 0)
    ])

    self.cmd('backup protectable-item initialize -g {rg} -v {vault} -wt {wt} -c {name}')

    self.cmd('backup protectable-item list -g {rg} -v {vault} -wt {wt}', checks=[
        self.check("length([?properties.friendlyName == '{protectable_item_name}'])", 1)
    ])

    item1_json = self.cmd('backup protectable-item show -g {rg} -v {vault} -n {protectable_item_name} -wt {wt} -pit {pit} -s {fname}', checks=[
        self.check('properties.friendlyName', '{protectable_item_name}'),
        self.check('properties.protectableItemType', '{pit}' if workload_type == 'MSSQL' else '{pit_hana}'),
        self.check('properties.serverName', '{fname}'),
        self.check('resourceGroup', '{rg}')
    ]).get_output_in_json()

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])


def test_backup_wl_restore(self, container_name1, container_name2, resource_group, vault_name, policy_name, workload_type, subscription, item, id, item_type, item_id, backup_entity_friendly_name, target_type, target_item):

    self.kwargs.update({
        'vault': vault_name,
        'name': container_name1,
        'fname': container_name2,
        'policy': policy_name,
        'wt': workload_type,
        'sub': subscription,
        'default': 'HourlyLogBackup',
        'rg': resource_group,
        'item': item,
        'fitem': item.split(';')[-1],
        'id': id,
        'item_id': item_id,
        'pit': item_type,
        'entityFriendlyName': backup_entity_friendly_name,
        'tpit': target_type,
        'titem': target_item
    })

    self.cmd('backup container register -v {vault} -g {rg} -bmt AzureWorkload -wt {wt} -id {id}')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 1)])

    self.kwargs['protectable_item'] = json.dumps(self.cmd('backup protectable-item show -v {vault} -g {rg} -pit {pit} -s {fname} -n {item} -wt {wt}').get_output_in_json(), separators=(',', ':')).replace('"', '\\"')

    self.cmd('backup protection enable-for-AzureWL -v {vault} -g {rg} -p {policy} -pi {protectable_item}', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "ConfigureBackup"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} -bmt AzureWorkload --query name').get_output_in_json()

    self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item_id} -bt Full -rt 1-7-2020 -ec false', checks=[
        self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
        self.check("properties.operation", "Backup"),
        self.check("properties.status", "InProgress"),
        self.check("resourceGroup", '{rg}')
    ]).get_output_in_json()

    self.kwargs['job'] = self.kwargs['backup_job']['name']

    self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

    self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} -bmt AzureWorkload', checks=[
        self.check('properties.friendlyName', '{fitem}'),
        self.check('properties.protectedItemHealthStatus', 'Healthy'),
        self.check('properties.protectionState', 'Protected'),
        self.check('properties.protectionStatus', 'Healthy'),
        self.check('resourceGroup', '{rg}')
    ])

    self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} -wt {wt} --query [0]').get_output_in_json()

    self.kwargs['rp'] = self.kwargs['rp']['name']

    self.kwargs['ti'] = json.dumps(self.cmd('backup protectable-item show -v {vault} -g {rg} -pit {tpit} -s {fname} -n {titem} -wt {wt}').get_output_in_json(), separators=(',', ':')).replace('"', '\\"')

    self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show -v {vault} -g {rg} -m AlternateWorkloadRestore -r {rp} -i {item} -c {container1} -ti {ti}').get_output_in_json(), separators=(',', ':'))

    self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl -v {vault} -g {rg} -rc {rc}', checks=[
        self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
        self.check("properties.operation", "Restore"),
        self.check("properties.status", "InProgress"),
        self.check("resourceGroup", '{rg}')
    ]).get_output_in_json()

    self.kwargs['job'] = self.kwargs['backup_job']['name']

    self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

    self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show -v {vault} -g {rg} -m OriginalWorkloadRestore -i {item} -c {container1} -r {rp}').get_output_in_json(), separators=(',', ':'))

    self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl -v {vault} -g {rg} -rc {rc}', checks=[
        self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
        self.check("properties.operation", "Restore"),
        self.check("properties.status", "InProgress"),
        self.check("resourceGroup", '{rg}')
    ]).get_output_in_json()

    self.kwargs['job'] = self.kwargs['backup_job']['name']

    self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

    self.cmd('backup protection disable -v {vault} -g {rg} -i {item_id} -y', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "DisableBackup"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} -bmt AzureWorkload', checks=[
        self.check("properties.friendlyName", '{fitem}'),
        self.check("properties.protectionState", "ProtectionStopped"),
        self.check("resourceGroup", '{rg}')
    ])

    self.cmd('backup protection disable -v {vault} -g {rg} -i {item_id} -y --delete-backup-data true', checks=[
        self.check("properties.entityFriendlyName", '{fitem}'),
        self.check("properties.operation", "DeleteBackupData"),
        self.check("properties.status", "Completed"),
        self.check("resourceGroup", '{rg}')
    ])

    self.cmd('backup container unregister -v {vault} -g {rg} -n {name} -y')

    self.cmd('backup container list -v {vault} -g {rg} -bmt AzureWorkload', checks=[
        self.check("length([?name == '{name}'])", 0)])
