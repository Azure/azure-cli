# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait


logger = get_logger(__name__)


def create_cluster(cmd, client, cluster_name, resource_group_name, location=None, tags=None, no_wait=False,
                   cluster_version='default', cluster_type='hadoop', cluster_tier=None, cluster_configurations=None, component_version=None,
                   headnode_size='large', workernode_size='large', zookeepernode_size=None, edgenode_size=None,
                   workernode_count=3, workernode_data_disk_groups=None,
                   http_username=None, http_password=None, ssh_username=None, ssh_password=None, ssh_public_key=None,
                   storage_account=None, storage_account_key=None, storage_default_container=None, additional_storage_accounts=None,
                   virtual_network=None, subnet_name=None, security_profile=None):
    from azure.mgmt.hdinsight.models import ClusterCreateParametersExtended, ClusterCreateProperties, OSType, Tier, \
        ClusterDefinition, ComputeProfile, HardwareProfile, Role, OsProfile, LinuxOperatingSystemProfile, \
        StorageProfile, StorageAccount, VirtualNetworkProfile, DataDisksGroups

    # Update optional parameters with defaults
    additional_storage_accounts = additional_storage_accounts or []
    location = location or _get_rg_location(cmd.cli_ctx, resource_group_name)

    # Format dictionary and free-form arguments
    if cluster_configurations:
        import json
        try:
            cluster_configurations = json.loads(cluster_configurations)
        except Exception as ex:
            raise CLIError('The cluster_configurations argument must be valid JSON. Error: {}'.format(ex.message))
    if component_version:
        import json
        try:
            component_version = json.loads(component_version)
        except Exception as ex:
            raise CLIError('The component_version argument must be valid JSON. Error: {}'.format(ex.message))

    # Validate whether HTTP credentials were provided
    is_cluster_config_defined = cluster_configurations and 'gateway' in cluster_configurations and cluster_configurations['gateway']
    is_username_in_cluster_config = is_cluster_config_defined and 'restAuthCredential.username' in cluster_configurations['gateway']
    is_password_in_cluster_config = is_cluster_config_defined and 'restAuthCredential.password' in cluster_configurations['gateway']
    if not (http_username or is_username_in_cluster_config):
        raise CLIError('An HTTP username is required.')
    if not (http_password or is_password_in_cluster_config):
        raise CLIError('An HTTP password is required.')
    if http_username and is_username_in_cluster_config:
        raise CLIError('An HTTP username must be specified either as a command-line parameter or in the cluster configuration, but not both.')
    if http_password and is_password_in_cluster_config:
        raise CLIError('An HTTP password must be specified either as a command-line parameter or in the cluster configuration, but not both.')

    # Update the cluster config with the HTTP credentials
    if not cluster_configurations:
        cluster_configurations = dict()
    if 'gateway' not in cluster_configurations:
        cluster_configurations['gateway'] = dict()
    if not is_username_in_cluster_config:
        cluster_configurations['gateway']['restAuthCredential.username'] = http_username
    if not is_password_in_cluster_config:
        cluster_configurations['gateway']['restAuthCredential.password'] = http_password

    # Validate whether SSH credentials were provided
    if not ssh_username:
        raise CLIError('An SSH username is required.')
    if not (ssh_password or ssh_public_key):
        raise CLIError('An SSH password or public key is required.')

    # Validate storage info
    wasb_param_set = {
        'storage_account': storage_account,
        'storage_account_key': storage_account_key,
        'storage_default_container': storage_default_container
    }
    _validate_parameter_set('WASB', wasb_param_set)

    virtual_network_profile = (virtual_network or subnet_name) and VirtualNetworkProfile(
                                  id=virtual_network,
                                  subnet=subnet_name
                              )
    os_profile = OsProfile(
                     linux_operating_system_profile=LinuxOperatingSystemProfile(
                         username=ssh_username,
                         password=ssh_password,
                         ssh_public_key=ssh_public_key
                     )
                 )

    create_params = ClusterCreateParametersExtended(
        location=location,
        tags=tags,
        properties=ClusterCreateProperties(
            cluster_version=cluster_version,
            os_type=OSType.linux,
            tier=cluster_tier,
            cluster_definition=ClusterDefinition(
                kind=cluster_type,
                configurations=cluster_configurations,
                component_version=component_version
            ),
            compute_profile=ComputeProfile(
                roles=[
                    # Required roles
                    Role(
                        name="headnode",
                        target_instance_count=2,
                        hardware_profile=HardwareProfile(vm_size=headnode_size),
                        os_profile=os_profile,
                        virtual_network_profile=virtual_network_profile
                    ),
                    Role(
                        name="workernode",
                        target_instance_count=workernode_count,
                        hardware_profile=HardwareProfile(vm_size=workernode_size),
                        os_profile=os_profile,
                        virtual_network_profile=virtual_network_profile,
                        data_disks_groups=workernode_data_disk_groups
                    )
                ]
                + (
                    [
                        # Specify a zookeeper role only if the zookeeper size is specified
                        Role(
                            name="zookeepernode",
                            target_instance_count=3,
                            hardware_profile=HardwareProfile(vm_size=zookeepernode_size),
                            os_profile=os_profile,
                            virtual_network_profile=virtual_network_profile
                        )
                    ] if zookeepernode_size else []
                )
                + (
                    [
                        # Specify an edgenode role only if the edgenode size is specified
                        Role(
                            name="edgenode",
                            target_instance_count=1,
                            hardware_profile=HardwareProfile(vm_size=edgenode_size),
                            os_profile=os_profile,
                            virtual_network_profile=virtual_network_profile
                        )
                    ] if edgenode_size else []
                )
            ),
            security_profile=security_profile,
            storage_profile=StorageProfile(
                storageaccounts=[
                    StorageAccount(
                        name=storage_account,
                        key=storage_account_key,
                        container=storage_default_container,
                        is_default=True
                    )
                ]
                + [
                    StorageAccount(
                        name=s.storage_account,
                        key=s.storage_account_key,
                        container=s.container,
                        is_default=False
                    )
                    for s in additional_storage_accounts
                ]
            )
        )
    )

    if no_wait:
        return sdk_no_wait(no_wait, client.create,
                           resource_group_name, cluster_name, create_params)

    return client.create(resource_group_name, cluster_name, create_params)


def _validate_parameter_set(param_set_name, param_set):
    """
    Validates that if any parameter in the set is provided, all parameters are.
    :param param_set_name: Name of the parameter set for error message purposes.
    :param param_set: Dictionary where the key as parameter name and value as parameter value.
    """
    if any(param_set.values()) and not all(param_set.values()):
        raise CLIError('Missing parameters in argument group "{}": {}'
                       .format(param_set_name, [k for k, v in param_set.items() if not v]))


def _get_rg_location(ctx, resource_group_name, subscription_id=None):
    from ._client_factory import cf_resource_groups
    groups = cf_resource_groups(ctx, subscription_id=subscription_id)
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    return rg.location
