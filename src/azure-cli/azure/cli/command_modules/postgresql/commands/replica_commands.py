# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError, RequiredArgumentMissingError, ValidationError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id, resource_id
from ..utils._flexible_server_location_capabilities_util import get_postgres_location_capability_info
from ..utils._flexible_server_util import _is_resource_name, build_identity_and_data_encryption
from ..utils.validators import (
    is_citus_cluster,
    pg_byok_validator,
    validate_citus_cluster,
    validate_postgres_replica,
    validate_resource_group,
    validate_server_name)
from .._client_factory import (
    cf_postgres_flexible_firewall_rules,
    cf_postgres_flexible_db,
    cf_postgres_check_resource_availability,
    cf_postgres_flexible_private_dns_zone_suffix_operations)
from .._db_context import DbContext
from .network_commands import flexible_server_provision_network_resource


# pylint: disable=too-many-locals
def flexible_replica_create(cmd, client, resource_group_name, source_server, replica_name=None, name=None, zone=None,
                            location=None, vnet=None, vnet_address_prefix=None, subnet=None,
                            subnet_address_prefix=None, private_dns_zone_arguments=None, no_wait=False,
                            byok_identity=None, byok_key=None,
                            sku_name=None, tier=None, storage_type=None,
                            storage_gb=None, performance_tier=None, yes=False, tags=None):
    validate_resource_group(resource_group_name)

    if replica_name is None and name is None:
        raise RequiredArgumentMissingError('the following arguments are required: --name')
    if replica_name is not None and name is not None:
        raise MutuallyExclusiveArgumentError('usage error: --name and --replica-name cannot be used together. Please use --name.')
    replica_name = replica_name.lower() if name is None else name.lower()

    if not is_valid_resource_id(source_server):
        if _is_resource_name(source_server):
            source_server_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                           resource_group=resource_group_name,
                                           namespace='Microsoft.DBforPostgreSQL',
                                           type='flexibleServers',
                                           name=source_server)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server_id)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except Exception as e:
        raise ResourceNotFoundError(e)

    if not location:
        location = source_server_object.location
    location = ''.join(location.lower().split())

    list_location_capability_info = get_postgres_location_capability_info(cmd, location)

    if tier is None and source_server_object is not None:
        tier = source_server_object.sku.tier
    if sku_name is None and source_server_object is not None:
        sku_name = source_server_object.sku.name
    if storage_gb is None and source_server_object is not None:
        storage_gb = source_server_object.storage.storage_size_gb
    validate_postgres_replica(cmd, tier, location, source_server_object,
                              sku_name, storage_gb, performance_tier, list_location_capability_info)

    if not zone:
        zone = _get_pg_replica_zone(list_location_capability_info['zones'],
                                    source_server_object.availability_zone,
                                    zone)

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)
    validate_server_name(db_context, replica_name, 'Microsoft.DBforPostgreSQL/flexibleServers')

    pg_byok_validator(byok_identity, byok_key)

    parameters = postgresql_flexibleservers.models.Server(
        tags=tags,
        source_server_resource_id=source_server_id,
        location=location,
        availability_zone=zone,
        create_mode="Replica")

    if source_server_object.network.public_network_access == 'Disabled' and any((vnet, subnet)):
        parameters.network, _, _ = flexible_server_provision_network_resource(cmd=cmd,
                                                                              resource_group_name=resource_group_name,
                                                                              server_name=replica_name,
                                                                              location=location,
                                                                              db_context=db_context,
                                                                              private_dns_zone_arguments=private_dns_zone_arguments,
                                                                              public_access='Disabled',
                                                                              vnet=vnet,
                                                                              subnet=subnet,
                                                                              vnet_address_prefix=vnet_address_prefix,
                                                                              subnet_address_prefix=subnet_address_prefix,
                                                                              yes=yes)
    else:
        parameters.network = source_server_object.network

    parameters.identity, parameters.data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                                         byok_identity=byok_identity,
                                                                                         byok_key=byok_key)

    parameters.sku = postgresql_flexibleservers.models.Sku(name=sku_name, tier=tier)

    parameters.storage = postgresql_flexibleservers.models.Storage(storage_size_gb=storage_gb, auto_grow=source_server_object.storage.auto_grow, tier=performance_tier, type=storage_type)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, replica_name, parameters)


def _get_pg_replica_zone(availabilityZones, sourceServerZone, replicaZone):
    preferredZone = 'none'
    for _index, zone in enumerate(availabilityZones):
        if zone != sourceServerZone and zone != 'none':
            preferredZone = zone

    if not preferredZone:
        preferredZone = 'none'

    selectZone = preferredZone if not replicaZone else replicaZone

    selectZoneSupported = False
    for _index, zone in enumerate(availabilityZones):
        if zone == selectZone:
            selectZoneSupported = True

    pg_replica_zone = None
    if len(availabilityZones) > 1 and selectZone and selectZoneSupported:
        pg_replica_zone = selectZone if selectZone != 'none' else None
    else:
        sourceZoneSupported = False
        for _index, zone in enumerate(availabilityZones):
            if zone == sourceServerZone:
                sourceZoneSupported = True
        if sourceZoneSupported:
            pg_replica_zone = sourceServerZone
        else:
            pg_replica_zone = None

    return pg_replica_zone


def flexible_replica_promote(cmd, client, resource_group_name, replica_name, promote_mode='standalone', promote_option='planned'):
    validate_resource_group(resource_group_name)
    if is_citus_cluster(cmd, resource_group_name, replica_name):
        # some settings validation
        if promote_mode.lower() == 'standalone':
            raise ValidationError("Standalone replica promotion on elastic cluster isn't currently supported. Please use 'switchover' instead.")
        if promote_option.lower() == 'planned':
            raise ValidationError("Planned replica promotion on elastic cluster isn't currently supported. Please use 'forced' instead.")

    try:
        server_object = client.get(resource_group_name, replica_name)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if server_object.replica.role is not None and "replica" not in server_object.replica.role.lower():
        raise CLIError('Server {} is not a replica server.'.format(replica_name))

    if promote_mode == "standalone":
        params = postgresql_flexibleservers.models.ServerForPatch(
            replica=postgresql_flexibleservers.models.Replica(
                role='None',
                promote_mode=promote_mode,
                promote_option=promote_option
            )
        )
    else:
        params = postgresql_flexibleservers.models.ServerForPatch(
            replica=postgresql_flexibleservers.models.Replica(
                role='Primary',
                promote_mode=promote_mode,
                promote_option=promote_option
            )
        )

    return client.begin_update(resource_group_name, replica_name, params)


def flexible_replica_list_by_server(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)
    return client.list_by_server(resource_group_name, server_name)
