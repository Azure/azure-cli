# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from knack.util import CLIError
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.commands.parameters import get_resources_in_subscription
from .util import get_resource_id_by_name

VALIDATION_TIME_OUT = 20


def validate_component_version(namespace):
    if namespace.component_version:
        import re
        invalid_component_versions = [cv for cv in namespace.component_version if not re.match('^[^=]+=[^=]+$', cv)]
        if any(invalid_component_versions):
            raise ValueError('Component verions must be in the form component=version. '
                             'Invalid component version(s): {}'.format(', '.join(invalid_component_versions)))


# Validate storage account.
def validate_storage_account(cmd, namespace):
    namespace.storage_account = HDInsightValidator(
        resource_type='Microsoft.Storage/storageAccounts',
        resource_name=namespace.storage_account).validate(cmd, namespace)


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    subnet = namespace.subnet
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        vnet = HDInsightValidator(
            resource_type='Microsoft.Network/virtualNetworks',
            resource_name=vnet).validate(cmd, namespace)
        namespace.subnet = '/'.join([vnet, 'subnets', subnet])
    else:
        raise CLIError('usage error: [--subnet ID | --subnet NAME --vnet-name NAME]')
    delattr(namespace, 'vnet_name')


# Validate managed identity.
def validate_msi(cmd, namespace):
    if namespace.assign_identity is None:
        namespace.assign_identity = []
    elif isinstance(namespace.assign_identity, str):
        namespace.assign_identity = [namespace.assign_identity]

    validated_identities = []
    for identity in namespace.assign_identity:
        validated_identity = HDInsightValidator(
            resource_type='Microsoft.ManagedIdentity/userAssignedIdentities',
            resource_name=identity).validate(cmd, namespace)
        validated_identities.append(validated_identity)

    namespace.assign_identity = validated_identities


# Validate managed identity to access storage account v2.
def validate_storage_msi(cmd, namespace):
    namespace.storage_account_managed_identity = HDInsightValidator(
        resource_type='Microsoft.ManagedIdentity/userAssignedIdentities',
        resource_name=namespace.storage_account_managed_identity).validate(cmd, namespace)


# Validate domain service.
def validate_domain_service(cmd, namespace):
    if namespace.esp and not namespace.domain:
        domain = next(iter(get_resources_in_subscription(cmd.cli_ctx, 'Microsoft.AAD/domainServices')), None)
        if domain:
            namespace.domain = domain.id
    namespace.domain = HDInsightValidator(
        resource_type='Microsoft.AAD/domainServices',
        resource_name=namespace.domain).validate(cmd, namespace)


# Validate workspace.
def validate_workspace(cmd, namespace):
    from uuid import UUID

    try:
        # check if the given workspace is a valid UUID
        UUID(namespace.workspace, version=4)
        namespace.workspace_type = 'workspace_id'

        # A workspace name can also be in type of GUID
        # if we can find the workspace by name,
        # we will use the input value as workspace name
        try:
            namespace.workspace = HDInsightValidator(
                resource_type='Microsoft.OperationalInsights/workspaces',
                resource_name=namespace.workspace).validate(cmd, namespace)
            namespace.workspace_type = 'resource_id'
        except CLIError:
            # This indicates the input is not a valid UUID.
            # So we just ignore the error and treat it as workspace id
            pass
        return
    except ValueError:
        pass

    namespace.workspace = HDInsightValidator(
        resource_type='Microsoft.OperationalInsights/workspaces',
        resource_name=namespace.workspace).validate(cmd, namespace)


class HDInsightValidator:

    def __init__(self,
                 worker=None,
                 timeout=VALIDATION_TIME_OUT,
                 resource_type=None,
                 resource_name=None):
        self.worker = worker
        self.timeout = timeout
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.resource_id = resource_name
        self.exception = None

    def validate(self, cmd, namespace):
        if not self.worker:
            self.worker = self.validate_worker
        thread = threading.Thread(target=self.worker, args=[cmd, namespace])
        thread.daemon = True
        thread.start()
        if getattr(namespace, 'no_validation_timeout', None):
            thread.join()
        else:
            thread.join(timeout=self.timeout)
        if thread.is_alive():
            raise CLIError('Failed to transform name {} into resource ID within {} second(s). '
                           'Please specify resource ID explicitly.'.format(self.resource_name, self.timeout))

        if self.exception:
            raise self.exception  # pylint: disable=raising-bad-type

        return self.resource_id

    def validate_worker(self, cmd, namespace):  # pylint: disable=unused-argument
        try:
            if self.resource_name:
                if not is_valid_resource_id(self.resource_name):
                    self.resource_id = get_resource_id_by_name(
                        cmd.cli_ctx,
                        self.resource_type,
                        self.resource_name)
        except CLIError as e:
            self.exception = e


def validate_timezone_name(namespace):
    if namespace.timezone:
        from .util import AUTOSCALE_TIMEZONES
        zone = next((x for x in AUTOSCALE_TIMEZONES if x.lower() == namespace.timezone.lower()), None)
        if not zone:
            raise CLIError(
                "Invalid time zone: '{}'. Run 'az hdinsight autoscale list-timezones' for values.".format(
                    namespace.timezone))
        namespace.timezone = zone
        return zone
    return None


def validate_time(namespace):
    if namespace.time:
        message = 'The time is 24-hour time and exactly in the form of xx:xx. ' \
                  'For example it should be 09:00 instead of 9:00.'
        if ':' not in namespace.time:
            raise CLIError(message)
        hour, minute = namespace.time.split(':')
        if len(hour) != 2 or len(minute) != 2:
            raise CLIError(message)
        if not hour.isdigit() or not minute.isdigit():
            raise CLIError('The hour part or minute part is not digit.')
        if int(hour) > 23 or int(hour) < 0:
            raise CLIError('The hour of time should be 00-23.')
        if int(minute) > 59 or int(minute) < 0:
            raise CLIError('The minute of time should be 00-59.')
