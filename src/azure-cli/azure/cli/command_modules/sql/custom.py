# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=C0302
from enum import Enum

from azure.cli.core.util import (
    CLIError,
    sdk_no_wait,
)

from azure.mgmt.sql.models import (
    BlobAuditingPolicyState,
    CapabilityGroup,
    CapabilityStatus,
    CreateMode,
    DatabaseEdition,
    FailoverGroup,
    FailoverGroupReadOnlyEndpoint,
    FailoverGroupReadWriteEndpoint,
    IdentityType,
    PartnerInfo,
    PerformanceLevelUnit,
    ReplicationRole,
    ResourceIdentity,
    SecurityAlertPolicyState,
    SensitivityLabel,
    SensitivityLabelSource,
    ServerKey,
    ServerKeyType,
    ServiceObjectiveName,
    Sku,
    StorageKeyType,
    InstanceFailoverGroup,
    ManagedInstancePairInfo,
    PartnerRegionInfo,
    InstanceFailoverGroupReadOnlyEndpoint,
    InstanceFailoverGroupReadWriteEndpoint,
    ServerPublicNetworkAccess
)

from knack.log import get_logger

from ._util import (
    get_sql_capabilities_operations,
    get_sql_servers_operations,
    get_sql_managed_instances_operations,
    get_sql_restorable_dropped_database_managed_backup_short_term_retention_policies_operations,
)

from datetime import datetime
from dateutil.parser import parse
import calendar

logger = get_logger(__name__)

###############################################
#                Common funcs                 #
###############################################


def _get_server_location(cli_ctx, server_name, resource_group_name):
    '''
    Returns the location (i.e. Azure region) that the specified server is in.
    '''

    server_client = get_sql_servers_operations(cli_ctx, None)
    # pylint: disable=no-member
    return server_client.get(
        server_name=server_name,
        resource_group_name=resource_group_name).location


def _get_managed_restorable_dropped_database_backup_short_term_retention_client(cli_ctx):
    '''
    Returns client for managed restorable dropped databases.
    '''

    server_client = \
        get_sql_restorable_dropped_database_managed_backup_short_term_retention_policies_operations(cli_ctx, None)

    # pylint: disable=no-member
    return server_client


def _get_managed_instance_location(cli_ctx, managed_instance_name, resource_group_name):
    '''
    Returns the location (i.e. Azure region) that the specified managed instance is in.
    '''

    managed_instance_client = get_sql_managed_instances_operations(cli_ctx, None)
    # pylint: disable=no-member
    return managed_instance_client.get(
        managed_instance_name=managed_instance_name,
        resource_group_name=resource_group_name).location


def _get_location_capability(cli_ctx, location, group):
    '''
    Gets the location capability for a location and verifies that it is available.
    '''

    capabilities_client = get_sql_capabilities_operations(cli_ctx, None)
    location_capability = capabilities_client.list_by_location(location, group)
    _assert_capability_available(location_capability)
    return location_capability


def _any_sku_values_specified(sku):
    '''
    Returns True if the sku object has any properties that are specified
    (i.e. not None).
    '''

    return any(val for key, val in sku.__dict__.items())


def _compute_model_matches(sku_name, compute_model):
    '''
    Returns True if sku name matches the compute model.
    Please update is function if compute_model has more than 2 enums.
    '''

    if (_is_serverless_slo(sku_name) and compute_model == ComputeModelType.serverless):
        return True
    if (not _is_serverless_slo(sku_name) and compute_model != ComputeModelType.serverless):
        return True
    return False


def _is_serverless_slo(sku_name):
    '''
    Returns True if the sku name is a serverless sku.
    '''

    return "_S_" in sku_name


def _get_default_server_version(location_capabilities):
    '''
    Gets the default server version capability from the full location
    capabilities response.

    If none have 'default' status, gets the first capability that has
    'available' status.

    If there is no default or available server version, falls back to
    server version 12.0 in order to maintain compatibility with older
    Azure CLI releases (2.0.25 and earlier).
    '''
    server_versions = location_capabilities.supported_server_versions

    def is_v12(capability):
        return capability.name == "12.0"

    return _get_default_capability(server_versions, fallback_predicate=is_v12)


def _get_default_capability(capabilities, fallback_predicate=None):
    '''
    Gets the first capability in the collection that has 'default' status.
    If none have 'default' status, gets the first capability that has 'available' status.
    '''
    logger.debug('_get_default_capability: %s', capabilities)

    # Get default capability
    r = next((c for c in capabilities if c.status == CapabilityStatus.default), None)
    if r:
        logger.debug('_get_default_capability found default: %s', r)
        return r

    # No default capability, so fallback to first available capability
    r = next((c for c in capabilities if c.status == CapabilityStatus.available), None)
    if r:
        logger.debug('_get_default_capability found available: %s', r)
        return r

    # No available capability, so use custom fallback
    if fallback_predicate:
        logger.debug('_get_default_capability using fallback')
        r = next((c for c in capabilities if fallback_predicate(c)), None)
        if r:
            logger.debug('_get_default_capability found fallback: %s', r)
            return r

    # No custom fallback, so we have to throw an error.
    logger.debug('_get_default_capability failed')
    raise CLIError('Provisioning is restricted in this region. Please choose a different region.')


def _assert_capability_available(capability):
    '''
    Asserts that the capability is available (or default). Throws CLIError if the
    capability is unavailable.
    '''
    logger.debug('_assert_capability_available: %s', capability)

    if not is_available(capability.status):
        raise CLIError(capability.reason)


def is_available(status):
    '''
    Returns True if the capability status is available (including default).
    '''

    return status not in (CapabilityStatus.visible, CapabilityStatus.visible.value)


def _filter_available(capabilities):
    '''
    Filters out the capabilities by removing values that are not available.
    '''

    return [c for c in capabilities if is_available(c.status)]


def _find_edition_capability(sku, supported_editions):
    '''
    Finds the DB edition capability in the collection of supported editions
    that matches the requested sku.

    If the sku has no edition specified, returns the default edition.

    (Note: tier and edition mean the same thing.)
    '''
    logger.debug('_find_edition_capability: %s; %s', sku, supported_editions)

    if sku.tier:
        # Find requested edition capability
        try:
            return next(e for e in supported_editions if e.name == sku.tier)
        except StopIteration:
            candidate_editions = [e.name for e in supported_editions]
            raise CLIError('Could not find tier ''{}''. Supported tiers are: {}'.format(
                sku.tier, candidate_editions
            ))
    else:
        # Find default edition capability
        return _get_default_capability(supported_editions)


def _find_family_capability(sku, supported_families):
    '''
    Finds the family capability in the collection of supported families
    that matches the requested sku.

    If the edition has no family specified, returns the default family.
    '''
    logger.debug('_find_family_capability: %s; %s', sku, supported_families)

    if sku.family:
        # Find requested family capability
        try:
            return next(f for f in supported_families if f.name == sku.family)
        except StopIteration:
            candidate_families = [e.name for e in supported_families]
            raise CLIError('Could not find family ''{}''. Supported families are: {}'.format(
                sku.family, candidate_families
            ))
    else:
        # Find default family capability
        return _get_default_capability(supported_families)


def _find_performance_level_capability(sku, supported_service_level_objectives, allow_reset_family, compute_model=None):
    '''
    Finds the DB or elastic pool performance level (i.e. service objective) in the
    collection of supported service objectives that matches the requested sku's
    family and capacity.

    If the sku has no capacity or family specified, returns the default service
    objective.
    '''

    logger.debug('_find_performance_level_capability: %s, %s, allow_reset_family: %s, compute_model: %s',
                 sku, supported_service_level_objectives, allow_reset_family, compute_model)

    if sku.capacity:
        try:
            # Find requested service objective based on capacity & family.
            # Note that for non-vcore editions, family is None.
            return next(slo for slo in supported_service_level_objectives
                        if ((slo.sku.family == sku.family) or
                            (slo.sku.family is None and allow_reset_family)) and
                        int(slo.sku.capacity) == int(sku.capacity) and
                        _compute_model_matches(slo.sku.name, compute_model))
        except StopIteration:
            if allow_reset_family:
                raise CLIError(
                    "Could not find sku in tier '{tier}' with capacity {capacity}."
                    " Supported capacities for '{tier}' are: {capacities}."
                    " Please specify one of these supported values for capacity.".format(
                        tier=sku.tier,
                        capacity=sku.capacity,
                        capacities=[slo.sku.capacity for slo in supported_service_level_objectives]
                    ))
            raise CLIError(
                "Could not find sku in tier '{tier}' with family '{family}', capacity {capacity}."
                " Supported families & capacities for '{tier}' are: {skus}. Please specify one of these"
                " supported combinations of family and capacity.".format(
                    tier=sku.tier,
                    family=sku.family,
                    capacity=sku.capacity,
                    skus=[(slo.sku.family, slo.sku.capacity)
                          for slo in supported_service_level_objectives]
                ))
    elif sku.family:
        # Error - cannot find based on family alone.
        raise CLIError('If --family is specified, --capacity must also be specified.')
    else:
        # Find default service objective
        return _get_default_capability(supported_service_level_objectives)


def _db_elastic_pool_update_sku(
        cmd,
        instance,
        service_objective,
        tier,
        family,
        capacity,
        find_sku_from_capabilities_func,
        compute_model=None):
    '''
    Updates the sku of a DB or elastic pool.
    '''

    # Set sku name
    if service_objective:
        instance.sku = Sku(name=service_objective)

    # Set tier
    allow_reset_family = False
    if tier:
        if not service_objective:
            # Wipe out old sku name so that it does not conflict with new tier
            instance.sku.name = None

        instance.sku.tier = tier

        if instance.sku.family and not family:
            # If we are changing tier and old sku has family but
            # new family is unspecified, allow sku search to wipe out family.
            #
            # This is needed so that tier can be successfully changed from
            # a tier that has family (e.g. GeneralPurpose) to a tier that has
            # no family (e.g. Standard).
            allow_reset_family = True

    # Set family
    if family:
        if not service_objective:
            # Wipe out old sku name so that it does not conflict with new family
            instance.sku.name = None
        instance.sku.family = family

    # Set capacity
    if capacity:
        instance.sku.capacity = capacity

    # Wipe out sku name if serverless vs provisioned db offerings changed,
    # only if sku name has not be wiped by earlier logic, and new compute model has been requested.
    if instance.sku.name and compute_model:
        if not _compute_model_matches(instance.sku.name, compute_model):
            instance.sku.name = None

    # If sku name was wiped out by any of the above, resolve the requested sku name
    # using capabilities.
    if not instance.sku.name:
        instance.sku = find_sku_from_capabilities_func(
            cmd.cli_ctx, instance.location, instance.sku,
            allow_reset_family=allow_reset_family, compute_model=compute_model)


def _get_tenant_id():
    '''
    Gets tenantId from current subscription.
    '''
    from azure.cli.core._profile import Profile

    profile = Profile()
    sub = profile.get_subscription()
    return sub['tenantId']


_DEFAULT_SERVER_VERSION = "12.0"


def failover_group_update_common(
        instance,
        failover_policy=None,
        grace_period=None,):
    '''
    Updates the failover group grace period and failover policy. Common logic for both Sterling and Managed Instance
    '''

    if failover_policy is not None:
        instance.read_write_endpoint.failover_policy = failover_policy

    if instance.read_write_endpoint.failover_policy == FailoverPolicyType.manual.value:
        grace_period = None
        instance.read_write_endpoint.failover_with_data_loss_grace_period_minutes = grace_period

    if grace_period is not None:
        grace_period = int(grace_period) * 60
        instance.read_write_endpoint.failover_with_data_loss_grace_period_minutes = grace_period

###############################################
#                sql db                       #
###############################################


# pylint: disable=too-few-public-methods
class ClientType(Enum):
    '''
    Types of SQL clients whose connection strings we can generate.
    '''

    ado_net = 'ado.net'
    sqlcmd = 'sqlcmd'
    jdbc = 'jdbc'
    php_pdo = 'php_pdo'
    php = 'php'
    odbc = 'odbc'


class ClientAuthenticationType(Enum):
    '''
    Types of SQL client authentication mechanisms for connection strings
    that we can generate.
    '''

    sql_password = 'SqlPassword'
    active_directory_password = 'ADPassword'
    active_directory_integrated = 'ADIntegrated'


class FailoverPolicyType(Enum):
    automatic = 'Automatic'
    manual = 'Manual'


class SqlServerMinimalTlsVersionType(Enum):
    tls_1_0 = "1.0"
    tls_1_1 = "1.1"
    tls_1_2 = "1.2"


class SqlManagedInstanceMinimalTlsVersionType(Enum):
    no_tls = "None"
    tls_1_0 = "1.0"
    tls_1_1 = "1.1"
    tls_1_2 = "1.2"


class ComputeModelType(str, Enum):

    provisioned = "Provisioned"
    serverless = "Serverless"


def _get_server_dns_suffx(cli_ctx):
    '''
    Gets the DNS suffix for servers in this Azure environment.
    '''

    # Allow dns suffix to be overridden by environment variable for testing purposes
    from os import getenv
    return getenv('_AZURE_CLI_SQL_DNS_SUFFIX', default=cli_ctx.cloud.suffixes.sql_server_hostname)


def _get_managed_db_resource_id(cli_ctx, resource_group_name, managed_instance_name, database_name):
    '''
    Gets the Managed db resource id in this Azure environment.
    '''

    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import resource_id

    return resource_id(
        subscription=get_subscription_id(cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Sql', type='managedInstances',
        name=managed_instance_name,
        child_type_1='databases',
        child_name_1=database_name)


def _to_filetimeutc(dateTime):
    '''
    Changes given datetime to filetimeutc string
    '''

    NET_epoch = datetime(1601, 1, 1)
    UNIX_epoch = datetime(1970, 1, 1)

    epoch_delta = (UNIX_epoch - NET_epoch)

    log_time = parse(dateTime)

    net_ts = calendar.timegm((log_time + epoch_delta).timetuple())

    # units of seconds since NET epoch
    filetime_utc_ts = net_ts * (10**7) + log_time.microsecond * 10

    return filetime_utc_ts


def _get_managed_dropped_db_resource_id(
        cli_ctx,
        resource_group_name,
        managed_instance_name,
        database_name,
        deleted_time):
    '''
    Gets the Managed db resource id in this Azure environment.
    '''

    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from six.moves.urllib.parse import quote  # pylint: disable=import-error
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import resource_id

    return (resource_id(
        subscription=get_subscription_id(cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Sql', type='managedInstances',
        name=managed_instance_name,
        child_type_1='restorableDroppedDatabases',
        child_name_1='{},{}'.format(
            quote(database_name),
            _to_filetimeutc(deleted_time))))


def db_show_conn_str(
        cmd,
        client_provider,
        database_name='<databasename>',
        server_name='<servername>',
        auth_type=ClientAuthenticationType.sql_password.value):
    '''
    Builds a SQL connection string for a specified client provider.
    '''

    server_suffix = _get_server_dns_suffx(cmd.cli_ctx)

    conn_str_props = {
        'server': server_name,
        'server_fqdn': '{}{}'.format(server_name, server_suffix),
        'server_suffix': server_suffix,
        'db': database_name
    }

    formats = {
        ClientType.ado_net.value: {
            ClientAuthenticationType.sql_password.value:
                'Server=tcp:{server_fqdn},1433;Database={db};User ID=<username>;'
                'Password=<password>;Encrypt=true;Connection Timeout=30;',
            ClientAuthenticationType.active_directory_password.value:
                'Server=tcp:{server_fqdn},1433;Database={db};User ID=<username>;'
                'Password=<password>;Encrypt=true;Connection Timeout=30;'
                'Authentication="Active Directory Password"',
            ClientAuthenticationType.active_directory_integrated.value:
                'Server=tcp:{server_fqdn},1433;Database={db};Encrypt=true;'
                'Connection Timeout=30;Authentication="Active Directory Integrated"'
        },
        ClientType.sqlcmd.value: {
            ClientAuthenticationType.sql_password.value:
                'sqlcmd -S tcp:{server_fqdn},1433 -d {db} -U <username> -P <password> -N -l 30',
            ClientAuthenticationType.active_directory_password.value:
                'sqlcmd -S tcp:{server_fqdn},1433 -d {db} -U <username> -P <password> -G -N -l 30',
            ClientAuthenticationType.active_directory_integrated.value:
                'sqlcmd -S tcp:{server_fqdn},1433 -d {db} -G -N -l 30',
        },
        ClientType.jdbc.value: {
            ClientAuthenticationType.sql_password.value:
                'jdbc:sqlserver://{server_fqdn}:1433;database={db};user=<username>@{server};'
                'password=<password>;encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{server_suffix};loginTimeout=30',
            ClientAuthenticationType.active_directory_password.value:
                'jdbc:sqlserver://{server_fqdn}:1433;database={db};user=<username>;'
                'password=<password>;encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{server_suffix};loginTimeout=30;'
                'authentication=ActiveDirectoryPassword',
            ClientAuthenticationType.active_directory_integrated.value:
                'jdbc:sqlserver://{server_fqdn}:1433;database={db};'
                'encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{server_suffix};loginTimeout=30;'
                'authentication=ActiveDirectoryIntegrated',
        },
        ClientType.php_pdo.value: {
            # pylint: disable=line-too-long
            ClientAuthenticationType.sql_password.value:
                '$conn = new PDO("sqlsrv:server = tcp:{server_fqdn},1433; Database = {db}; LoginTimeout = 30; Encrypt = 1; TrustServerCertificate = 0;", "<username>", "<password>");',
            ClientAuthenticationType.active_directory_password.value:
                CLIError('PHP Data Object (PDO) driver only supports SQL Password authentication.'),
            ClientAuthenticationType.active_directory_integrated.value:
                CLIError('PHP Data Object (PDO) driver only supports SQL Password authentication.'),
        },
        ClientType.php.value: {
            # pylint: disable=line-too-long
            ClientAuthenticationType.sql_password.value:
                '$connectionOptions = array("UID"=>"<username>@{server}", "PWD"=>"<password>", "Database"=>{db}, "LoginTimeout" => 30, "Encrypt" => 1, "TrustServerCertificate" => 0); $serverName = "tcp:{server_fqdn},1433"; $conn = sqlsrv_connect($serverName, $connectionOptions);',
            ClientAuthenticationType.active_directory_password.value:
                CLIError('PHP sqlsrv driver only supports SQL Password authentication.'),
            ClientAuthenticationType.active_directory_integrated.value:
                CLIError('PHP sqlsrv driver only supports SQL Password authentication.'),
        },
        ClientType.odbc.value: {
            ClientAuthenticationType.sql_password.value:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{server_fqdn},1433;'
                'Database={db};Uid=<username>@{server};Pwd=<password>;Encrypt=yes;'
                'TrustServerCertificate=no;',
            ClientAuthenticationType.active_directory_password.value:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{server_fqdn},1433;'
                'Database={db};Uid=<username>@{server};Pwd=<password>;Encrypt=yes;'
                'TrustServerCertificate=no;Authentication=ActiveDirectoryPassword',
            ClientAuthenticationType.active_directory_integrated.value:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{server_fqdn},1433;'
                'Database={db};Encrypt=yes;TrustServerCertificate=no;'
                'Authentication=ActiveDirectoryIntegrated',
        }
    }

    f = formats[client_provider][auth_type]

    if isinstance(f, Exception):
        # Error
        raise f

    # Success
    return f.format(**conn_str_props)


class DatabaseIdentity():  # pylint: disable=too-few-public-methods
    '''
    Helper class to bundle up database identity properties and generate
    database resource id.
    '''

    def __init__(self, cli_ctx, database_name, server_name, resource_group_name):

        self.database_name = database_name
        self.server_name = server_name
        self.resource_group_name = resource_group_name
        self.cli_ctx = cli_ctx

    def id(self):
        # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
        from six.moves.urllib.parse import quote  # pylint: disable=import-error
        from azure.cli.core.commands.client_factory import get_subscription_id

        return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/databases/{}'.format(
            quote(get_subscription_id(self.cli_ctx)),
            quote(self.resource_group_name),
            quote(self.server_name),
            quote(self.database_name))


def _find_db_sku_from_capabilities(cli_ctx, location, sku, allow_reset_family=False, compute_model=None):
    '''
    Given a requested sku which may have some properties filled in
    (e.g. tier and capacity), finds the canonical matching sku
    from the given location's capabilities.
    '''

    logger.debug('_find_db_sku_from_capabilities input: %s', sku)

    if sku.name:
        # User specified sku.name, so nothing else needs to be resolved.
        logger.debug('_find_db_sku_from_capabilities return sku as is')
        return sku

    if not _any_sku_values_specified(sku):
        # User did not request any properties of sku, so just wipe it out.
        # Server side will pick a default.
        logger.debug('_find_db_sku_from_capabilities return None')
        return None

    # Some properties of sku are specified, but not name. Use the requested properties
    # to find a matching capability and copy the sku from there.

    # Get location capability
    loc_capability = _get_location_capability(cli_ctx, location, CapabilityGroup.supported_editions)

    # Get default server version capability
    server_version_capability = _get_default_server_version(loc_capability)

    # Find edition capability, based on requested sku properties
    edition_capability = _find_edition_capability(
        sku, server_version_capability.supported_editions)

    # Find performance level capability, based on requested sku properties
    performance_level_capability = _find_performance_level_capability(
        sku, edition_capability.supported_service_level_objectives,
        allow_reset_family=allow_reset_family,
        compute_model=compute_model)

    # Ideally, we would return the sku object from capability (`return performance_level_capability.sku`).
    # However not all db create modes support using `capacity` to find slo, so instead we put
    # the slo name into the sku name property.
    result = Sku(name=performance_level_capability.name)
    logger.debug('_find_db_sku_from_capabilities return: %s', result)
    return result


def _validate_elastic_pool_id(
        cli_ctx,
        elastic_pool_id,
        server_name,
        resource_group_name):
    '''
    Validates elastic_pool_id is either None or a valid resource id.

    If elastic_pool_id has a value but it is not a valid resource id,
    then assume that user specified elastic pool name which we need to
    convert to elastic pool id using the provided server & resource group
    name.

    Returns the elastic_pool_id, which may have been updated and may be None.
    '''

    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    if elastic_pool_id and not is_valid_resource_id(elastic_pool_id):
        return resource_id(
            subscription=get_subscription_id(cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Sql',
            type='servers',
            name=server_name,
            child_type_1='elasticPools',
            child_name_1=elastic_pool_id)

    return elastic_pool_id


def _db_dw_create(
        cli_ctx,
        client,
        source_db,
        dest_db,
        no_wait,
        sku=None,
        **kwargs):
    '''
    Creates a DB (with any create mode) or DW.
    Handles common concerns such as setting location and sku properties.
    '''

    # This check needs to be here, because server side logic of
    # finding a default sku for Serverless is not yet implemented.
    if kwargs['compute_model'] == ComputeModelType.serverless:
        if not sku or not sku.tier or not sku.family or not sku.capacity:
            raise CLIError('When creating a severless database, please pass in edition, '
                           'family, and capacity parameters through -e -f -c')

    # Determine server location
    kwargs['location'] = _get_server_location(
        cli_ctx,
        server_name=dest_db.server_name,
        resource_group_name=dest_db.resource_group_name)

    # Set create mode properties
    if source_db:
        kwargs['source_database_id'] = source_db.id()

    # If sku.name is not specified, resolve the requested sku name
    # using capabilities.
    kwargs['sku'] = _find_db_sku_from_capabilities(
        cli_ctx,
        kwargs['location'],
        sku,
        compute_model=kwargs['compute_model'])

    # Validate elastic pool id
    kwargs['elastic_pool_id'] = _validate_elastic_pool_id(
        cli_ctx,
        kwargs['elastic_pool_id'],
        dest_db.server_name,
        dest_db.resource_group_name)

    # Create
    return sdk_no_wait(no_wait, client.create_or_update,
                       server_name=dest_db.server_name,
                       resource_group_name=dest_db.resource_group_name,
                       database_name=dest_db.database_name,
                       parameters=kwargs)


def db_create(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        no_wait=False,
        **kwargs):
    '''
    Creates a DB (with 'Default' create mode.)
    '''

    return _db_dw_create(
        cmd.cli_ctx,
        client,
        None,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        no_wait,
        **kwargs)


def _use_source_db_tier(
        client,
        database_name,
        server_name,
        resource_group_name,
        kwargs):
    '''
    Gets the specified db and copies its sku tier into kwargs.
    '''

    if _any_sku_values_specified(kwargs['sku']):
        source = client.get(resource_group_name, server_name, database_name)
        kwargs['sku'].tier = source.sku.tier


def db_copy(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        dest_name,
        dest_server_name=None,
        dest_resource_group_name=None,
        no_wait=False,
        **kwargs):
    '''
    Copies a DB (i.e. create with 'Copy' create mode.)
    '''

    # Determine optional values
    dest_server_name = dest_server_name or server_name
    dest_resource_group_name = dest_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = 'Copy'

    # Some sku properties may be filled in from the command line. However
    # the sku tier must be the same as the source tier, so it is grabbed
    # from the source db instead of from command line.
    _use_source_db_tier(
        client,
        database_name,
        server_name,
        resource_group_name,
        kwargs)

    return _db_dw_create(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        DatabaseIdentity(cmd.cli_ctx, dest_name, dest_server_name, dest_resource_group_name),
        no_wait,
        **kwargs)


def db_create_replica(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        # Replica must have the same database name as the source db
        partner_server_name,
        partner_resource_group_name=None,
        no_wait=False,
        **kwargs):
    '''
    Creates a secondary replica DB (i.e. create with 'Secondary' create mode.)

    Custom function makes create mode more convenient.
    '''

    # Determine optional values
    partner_resource_group_name = partner_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = CreateMode.secondary.value

    # Some sku properties may be filled in from the command line. However
    # the sku tier must be the same as the source tier, so it is grabbed
    # from the source db instead of from command line.
    _use_source_db_tier(
        client,
        database_name,
        server_name,
        resource_group_name,
        kwargs)

    # Replica must have the same database name as the source db
    return _db_dw_create(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        DatabaseIdentity(cmd.cli_ctx, database_name, partner_server_name, partner_resource_group_name),
        no_wait,
        **kwargs)


# Renames a database.
def db_rename(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        new_name):
    '''
    Renames a DB.
    '''

    client.rename(
        resource_group_name,
        server_name,
        database_name,
        id=DatabaseIdentity(
            cmd.cli_ctx,
            new_name,
            server_name,
            resource_group_name
        ).id())

    return client.get(
        resource_group_name,
        server_name,
        new_name)


def db_restore(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        dest_name,
        restore_point_in_time=None,
        source_database_deletion_date=None,
        no_wait=False,
        **kwargs):
    '''
    Restores an existing or deleted DB (i.e. create with 'Restore'
    or 'PointInTimeRestore' create mode.)

    Custom function makes create mode more convenient.
    '''

    if not (restore_point_in_time or source_database_deletion_date):
        raise CLIError('Either --time or --deleted-time must be specified.')

    # Set create mode properties
    is_deleted = source_database_deletion_date is not None

    kwargs['restore_point_in_time'] = restore_point_in_time
    kwargs['source_database_deletion_date'] = source_database_deletion_date
    kwargs['create_mode'] = CreateMode.restore.value if is_deleted else CreateMode.point_in_time_restore.value

    return _db_dw_create(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        # Cross-server restore is not supported. So dest server/group must be the same as source.
        DatabaseIdentity(cmd.cli_ctx, dest_name, server_name, resource_group_name),
        no_wait,
        **kwargs)


# pylint: disable=inconsistent-return-statements
def db_failover(
        client,
        database_name,
        server_name,
        resource_group_name,
        allow_data_loss=False):
    '''
    Fails over a database by setting the specified database as the new primary.

    Wrapper function which uses the server location so that the user doesn't
    need to specify replication link id.
    '''

    # List replication links
    links = list(client.list_by_database(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name))

    if not links:
        raise CLIError('The specified database has no replication links.')

    # If a replica is primary, then it has 1 or more links (to its secondaries).
    # If a replica is secondary, then it has exactly 1 link (to its primary).
    primary_link = next((link for link in links if link.partner_role == ReplicationRole.primary), None)
    if not primary_link:
        # No link to a primary, so this must already be a primary. Do nothing.
        return

    # Choose which failover method to use
    if allow_data_loss:
        failover_func = client.failover_allow_data_loss
    else:
        failover_func = client.failover

    # Execute failover from the primary to this database
    return failover_func(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        link_id=primary_link.name)


class DatabaseCapabilitiesAdditionalDetails(Enum):  # pylint: disable=too-few-public-methods
    '''
    Additional details that may be optionally included when getting db capabilities.
    '''

    max_size = 'max-size'


def db_list_capabilities(
        client,
        location,
        edition=None,
        service_objective=None,
        dtu=None,
        vcores=None,
        show_details=None,
        available=False):
    '''
    Gets database capabilities and optionally applies the specified filters.
    '''

    # Fixup parameters
    if not show_details:
        show_details = []

    # Get capabilities tree from server
    capabilities = client.list_by_location(location, CapabilityGroup.supported_editions)

    # Get subtree related to databases
    editions = _get_default_server_version(capabilities).supported_editions

    # Filter by edition
    if edition:
        editions = [e for e in editions if e.name.lower() == edition.lower()]

    # Filter by service objective
    if service_objective:
        for e in editions:
            e.supported_service_level_objectives = [
                slo for slo in e.supported_service_level_objectives
                if slo.name.lower() == service_objective.lower()]

    # Filter by dtu
    if dtu:
        for e in editions:
            e.supported_service_level_objectives = [
                slo for slo in e.supported_service_level_objectives
                if slo.performance_level.value == int(dtu) and
                slo.performance_level.unit == PerformanceLevelUnit.dtu.value]

    # Filter by vcores
    if vcores:
        for e in editions:
            e.supported_service_level_objectives = [
                slo for slo in e.supported_service_level_objectives
                if slo.performance_level.value == int(vcores) and
                slo.performance_level.unit == PerformanceLevelUnit.vcores.value]

    # Filter by availability
    if available:
        editions = _filter_available(editions)
        for e in editions:
            e.supported_service_level_objectives = _filter_available(e.supported_service_level_objectives)
            for slo in e.supported_service_level_objectives:
                if slo.supported_max_sizes:
                    slo.supported_max_sizes = _filter_available(slo.supported_max_sizes)

    # Remove editions with no service objectives (due to filters)
    editions = [e for e in editions if e.supported_service_level_objectives]

    # Optionally hide supported max sizes
    if DatabaseCapabilitiesAdditionalDetails.max_size.value not in show_details:
        for e in editions:
            for slo in e.supported_service_level_objectives:
                if slo.supported_max_sizes:
                    slo.supported_max_sizes = []

    return editions


# pylint: disable=inconsistent-return-statements
def db_delete_replica_link(
        client,
        database_name,
        server_name,
        resource_group_name,
        # Partner dbs must have the same name as one another
        partner_server_name,
        partner_resource_group_name=None,
        # Base command code handles confirmation, but it passes '--yes' parameter to us if
        # provided. We don't care about this parameter and it gets handled weirdly if we
        # expliclty specify it with default value here (e.g. `yes=None` or `yes=True`), receiving
        # it in kwargs seems to work.
        **kwargs):  # pylint: disable=unused-argument
    '''
    Deletes a replication link.
    '''

    # Determine optional values
    partner_resource_group_name = partner_resource_group_name or resource_group_name

    # Find the replication link
    links = list(client.list_by_database(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name))

    # The link doesn't tell us the partner resource group name, so we just have to count on
    # partner server name being unique
    link = next((link for link in links if link.partner_server == partner_server_name), None)
    if not link:
        # No link exists, nothing to be done
        return

    return client.delete(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        link_id=link.name)


def db_export(
        client,
        database_name,
        server_name,
        resource_group_name,
        storage_key_type,
        storage_key,
        **kwargs):
    '''
    Exports a database to a bacpac file.
    '''

    storage_key = _pad_sas_key(storage_key_type, storage_key)

    kwargs['storage_key_type'] = storage_key_type
    kwargs['storage_key'] = storage_key

    return client.export(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        storage_key_type=storage_key_type,
        storage_key=storage_key,
        parameters=kwargs)


def db_import(
        client,
        database_name,
        server_name,
        resource_group_name,
        storage_key_type,
        storage_key,
        **kwargs):
    '''
    Imports a bacpac file into an existing database.
    '''

    storage_key = _pad_sas_key(storage_key_type, storage_key)

    kwargs['storage_key_type'] = storage_key_type
    kwargs['storage_key'] = storage_key

    return client.create_import_operation(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        storage_key_type=storage_key_type,
        storage_key=storage_key,
        parameters=kwargs)


def _pad_sas_key(
        storage_key_type,
        storage_key):
    '''
    Import/Export API requires that "?" precede SAS key as an argument.
    Adds ? prefix if it wasn't included.
    '''

    if storage_key_type.lower() == StorageKeyType.shared_access_key.value.lower():  # pylint: disable=no-member
        if storage_key[0] != '?':
            storage_key = '?' + storage_key
    return storage_key


def db_list(
        client,
        server_name,
        resource_group_name,
        elastic_pool_name=None):
    '''
    Lists databases in a server or elastic pool.
    '''

    if elastic_pool_name:
        # List all databases in the elastic pool
        return client.list_by_elastic_pool(
            server_name=server_name,
            resource_group_name=resource_group_name,
            elastic_pool_name=elastic_pool_name)

        # List all databases in the server
    return client.list_by_server(resource_group_name=resource_group_name, server_name=server_name)


def db_update(
        cmd,
        instance,
        server_name,
        resource_group_name,
        elastic_pool_id=None,
        max_size_bytes=None,
        service_objective=None,
        zone_redundant=None,
        tier=None,
        family=None,
        capacity=None,
        read_scale=None,
        read_replica_count=None,
        min_capacity=None,
        auto_pause_delay=None,
        compute_model=None):
    '''
    Applies requested parameters to a db resource instance for a DB update.
    '''
    # Verify edition
    if instance.sku.tier.lower() == DatabaseEdition.data_warehouse.value.lower():  # pylint: disable=no-member
        raise CLIError('Azure SQL Data Warehouse can be updated with the command'
                       ' `az sql dw update`.')

    #####
    # Set sku-related properties
    #####

    # Verify that elastic_pool_name and requested_service_objective_name param values are not
    # totally inconsistent. If elastic pool and service objective name are both specified, and
    # they are inconsistent (i.e. service objective is not 'ElasticPool'), then the service
    # actually ignores the value of service objective name (!!). We are trying to protect the CLI
    # user from this unintuitive behavior.
    if (elastic_pool_id and service_objective and
            service_objective != ServiceObjectiveName.elastic_pool.value):
        raise CLIError('If elastic pool is specified, service objective must be'
                       ' unspecified or equal \'{}\'.'.format(
                           ServiceObjectiveName.elastic_pool.value))

    # Update both elastic pool and sku. The service treats elastic pool and sku properties like PATCH,
    # so if either of these properties is null then the service will keep the property unchanged -
    # except if pool is null/empty and service objective is a standalone SLO value (e.g. 'S0',
    # 'S1', etc), in which case the pool being null/empty is meaningful - it means remove from
    # pool.

    # Validate elastic pool id
    instance.elastic_pool_id = _validate_elastic_pool_id(
        cmd.cli_ctx,
        elastic_pool_id,
        server_name,
        resource_group_name)

    # Finding out requesting compute_model
    if not compute_model:
        compute_model = (
            ComputeModelType.serverless if _is_serverless_slo(instance.sku.name)
            else ComputeModelType.provisioned)

    # Update sku
    _db_elastic_pool_update_sku(
        cmd,
        instance,
        service_objective,
        tier,
        family,
        capacity,
        find_sku_from_capabilities_func=_find_db_sku_from_capabilities,
        compute_model=compute_model)

    # TODO Temporary workaround for elastic pool sku name issue
    if instance.elastic_pool_id:
        instance.sku = None

    #####
    # Set other (non-sku related) properties
    #####

    if max_size_bytes:
        instance.max_size_bytes = max_size_bytes

    if zone_redundant is not None:
        instance.zone_redundant = zone_redundant

    if read_scale is not None:
        instance.read_scale = read_scale

    if read_replica_count is not None:
        instance.read_replica_count = read_replica_count

    #####
    # Set other (serverless related) properties
    #####
    if min_capacity:
        instance.min_capacity = min_capacity

    if auto_pause_delay:
        instance.auto_pause_delay = auto_pause_delay

    return instance


#####
#           sql db audit-policy & threat-policy
#####


def _find_storage_account_resource_group(cli_ctx, name):
    '''
    Finds a storage account's resource group by querying ARM resource cache.

    Why do we have to do this: so we know the resource group in order to later query the storage API
    to determine the account's keys and endpoint. Why isn't this just a command line parameter:
    because if it was a command line parameter then the customer would need to specify storage
    resource group just to update some unrelated property, which is annoying and makes no sense to
    the customer.
    '''
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    storage_type = 'Microsoft.Storage/storageAccounts'
    classic_storage_type = 'Microsoft.ClassicStorage/storageAccounts'

    query = "name eq '{}' and (resourceType eq '{}' or resourceType eq '{}')".format(
        name, storage_type, classic_storage_type)

    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    resources = list(client.resources.list(filter=query))

    if not resources:
        raise CLIError("No storage account with name '{}' was found.".format(name))

    if len(resources) > 1:
        raise CLIError("Multiple storage accounts with name '{}' were found.".format(name))

    if resources[0].type == classic_storage_type:
        raise CLIError("The storage account with name '{}' is a classic storage account which is"
                       " not supported by this command. Use a non-classic storage account or"
                       " specify storage endpoint and key instead.".format(name))

    # Split the uri and return just the resource group
    return resources[0].id.split('/')[4]


def _get_storage_account_name(storage_endpoint):
    '''
    Determines storage account name from endpoint url string.
    e.g. 'https://mystorage.blob.core.windows.net' -> 'mystorage'
    '''
    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

    return urlparse(storage_endpoint).netloc.split('.')[0]


def _get_storage_endpoint(
        cli_ctx,
        storage_account,
        resource_group_name):
    '''
    Gets storage account endpoint by querying storage ARM API.
    '''
    from azure.mgmt.storage import StorageManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    # Get storage account
    client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    account = client.storage_accounts.get_properties(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Get endpoint
    # pylint: disable=no-member
    endpoints = account.primary_endpoints
    try:
        return endpoints.blob
    except AttributeError:
        raise CLIError("The storage account with name '{}' (id '{}') has no blob endpoint. Use a"
                       " different storage account.".format(account.name, account.id))


def _get_storage_key(
        cli_ctx,
        storage_account,
        resource_group_name,
        use_secondary_key):
    '''
    Gets storage account key by querying storage ARM API.
    '''
    from azure.mgmt.storage import StorageManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    # Get storage keys
    client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    keys = client.storage_accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Choose storage key
    index = 1 if use_secondary_key else 0
    return keys.keys[index].value  # pylint: disable=no-member


def _db_security_policy_update(
        cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        use_secondary_key):
    '''
    Common code for updating audit and threat detection policy.
    '''

    # Validate storage endpoint arguments
    if storage_endpoint and storage_account:
        raise CLIError('--storage-endpoint and --storage-account cannot both be specified.')

    # Set storage endpoint
    if storage_endpoint:
        instance.storage_endpoint = storage_endpoint
    if storage_account:
        storage_resource_group = _find_storage_account_resource_group(cli_ctx, storage_account)
        instance.storage_endpoint = _get_storage_endpoint(cli_ctx, storage_account, storage_resource_group)

    # Set storage access key
    if storage_account_access_key:
        # Access key is specified
        instance.storage_account_access_key = storage_account_access_key
    elif enabled:
        # Access key is not specified, but state is Enabled.
        # If state is Enabled, then access key property is required in PUT. However access key is
        # readonly (GET returns empty string for access key), so we need to determine the value
        # and then PUT it back. (We don't want the user to be force to specify this, because that
        # would be very annoying when updating non-storage-related properties).
        # This doesn't work if the user used generic update args, i.e. `--set state=Enabled`
        # instead of `--state Enabled`, since the generic update args are applied after this custom
        # function, but at least we tried.
        if not storage_account:
            storage_account = _get_storage_account_name(instance.storage_endpoint)
            storage_resource_group = _find_storage_account_resource_group(cli_ctx, storage_account)

        instance.storage_account_access_key = _get_storage_key(
            cli_ctx,
            storage_account,
            storage_resource_group,
            use_secondary_key)


def db_audit_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        audit_actions_and_groups=None,
        retention_days=None):
    '''
    Updates an audit policy. Custom update function to apply parameters to instance.
    '''

    # Apply state
    if state:
        instance.state = BlobAuditingPolicyState[state.lower()]
    enabled = instance.state.value.lower() == BlobAuditingPolicyState.enabled.value.lower()  # pylint: disable=no-member

    # Set storage-related properties
    _db_security_policy_update(
        cmd.cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        instance.is_storage_secondary_key_in_use)

    # Set other properties
    if audit_actions_and_groups:
        instance.audit_actions_and_groups = audit_actions_and_groups

    # If auditing is enabled, make sure that the actions and groups are set to default
    # value in case they were removed previously (When disabling auditing)
    if enabled and (not instance.audit_actions_and_groups or instance.audit_actions_and_groups == []):
        instance.audit_actions_and_groups = [
            "SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP",
            "FAILED_DATABASE_AUTHENTICATION_GROUP",
            "BATCH_COMPLETED_GROUP"]

    if retention_days:
        instance.retention_days = retention_days

    return instance


def db_threat_detection_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        retention_days=None,
        email_addresses=None,
        disabled_alerts=None,
        email_account_admins=None):
    '''
    Updates a threat detection policy. Custom update function to apply parameters to instance.
    '''

    # Apply state
    if state:
        instance.state = SecurityAlertPolicyState[state.lower()]
    enabled = instance.state.value.lower() == SecurityAlertPolicyState.enabled.value.lower()  # pylint: disable=no-member

    # Set storage-related properties
    _db_security_policy_update(
        cmd.cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        False)

    # Set other properties
    if retention_days:
        instance.retention_days = retention_days

    if email_addresses:
        instance.email_addresses = ";".join(email_addresses)

    if disabled_alerts:
        instance.disabled_alerts = ";".join(disabled_alerts)

    if email_account_admins:
        instance.email_account_admins = email_account_admins

    return instance


def db_sensitivity_label_show(
        client,
        database_name,
        server_name,
        schema_name,
        table_name,
        column_name,
        resource_group_name):

    return client.get(
        resource_group_name,
        server_name,
        database_name,
        schema_name,
        table_name,
        column_name,
        SensitivityLabelSource.current)


def db_sensitivity_label_update(
        cmd,
        client,
        database_name,
        server_name,
        schema_name,
        table_name,
        column_name,
        resource_group_name,
        label_name=None,
        information_type=None):
    '''
    Updates a sensitivity label. Custom update function to apply parameters to instance.
    '''

    # Get the information protection policy
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.security import SecurityCenter
    from msrestazure.azure_exceptions import CloudError

    security_center_client = get_mgmt_service_client(cmd.cli_ctx, SecurityCenter, asc_location="centralus")

    information_protection_policy = security_center_client.information_protection_policies.get(
        scope='/providers/Microsoft.Management/managementGroups/{}'.format(_get_tenant_id()),
        information_protection_policy_name="effective")

    sensitivity_label = SensitivityLabel()

    # Get the current label
    try:
        current_label = client.get(
            resource_group_name,
            server_name,
            database_name,
            schema_name,
            table_name,
            column_name,
            SensitivityLabelSource.current)
        # Initialize with existing values
        sensitivity_label.label_name = current_label.label_name
        sensitivity_label.label_id = current_label.label_id
        sensitivity_label.information_type = current_label.information_type
        sensitivity_label.information_type_id = current_label.information_type_id

    except CloudError as ex:
        if not(ex.error and ex.error.error and 'SensitivityLabelsLabelNotFound' in ex.error.error):
            raise ex

    # Find the label id and information type id in the policy by the label name provided
    label_id = None
    if label_name:
        label_id = next((id for id in information_protection_policy.labels
                         if information_protection_policy.labels[id].display_name.lower() ==
                         label_name.lower()),
                        None)
        if label_id is None:
            raise CLIError('The provided label name was not found in the information protection policy.')
        sensitivity_label.label_id = label_id
        sensitivity_label.label_name = label_name
    information_type_id = None
    if information_type:
        information_type_id = next((id for id in information_protection_policy.information_types
                                    if information_protection_policy.information_types[id].display_name.lower() ==
                                    information_type.lower()),
                                   None)
        if information_type_id is None:
            raise CLIError('The provided information type was not found in the information protection policy.')
        sensitivity_label.information_type_id = information_type_id
        sensitivity_label.information_type = information_type

    return client.create_or_update(
        resource_group_name, server_name, database_name, schema_name, table_name, column_name, sensitivity_label)


###############################################
#                sql dw                       #
###############################################


def dw_create(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        no_wait=False,
        **kwargs):
    '''
    Creates a datawarehouse.
    '''

    # Set edition
    kwargs['sku'].tier = DatabaseEdition.data_warehouse.value

    # Create
    return _db_dw_create(
        cmd.cli_ctx,
        client,
        None,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        no_wait,
        **kwargs)


def dw_list(
        client,
        server_name,
        resource_group_name):
    '''
    Lists data warehouses in a server or elastic pool.
    '''

    dbs = client.list_by_server(
        resource_group_name=resource_group_name,
        server_name=server_name)

    # Include only DW's
    return [db for db in dbs if db.sku.tier == DatabaseEdition.data_warehouse.value]


def dw_update(
        instance,
        max_size_bytes=None,
        service_objective=None):
    '''
    Updates a data warehouse. Custom update function to apply parameters to instance.
    '''

    # Apply param values to instance
    if max_size_bytes:
        instance.max_size_bytes = max_size_bytes

    if service_objective:
        instance.sku = Sku(name=service_objective)

    return instance


def dw_pause(
        client,
        database_name,
        server_name,
        resource_group_name):
    '''
    Pauses a datawarehouse.
    '''

    # Pause, but DO NOT return the result. Long-running POST operation
    # results are not returned correctly by SDK.
    client.pause(
        server_name=server_name,
        resource_group_name=resource_group_name,
        database_name=database_name).wait()


def dw_resume(
        client,
        database_name,
        server_name,
        resource_group_name):
    '''
    Resumes a datawarehouse.
    '''

    # Resume, but DO NOT return the result. Long-running POST operation
    # results are not returned correctly by SDK.
    client.resume(
        server_name=server_name,
        resource_group_name=resource_group_name,
        database_name=database_name).wait()


###############################################
#                sql elastic-pool             #
###############################################


def _find_elastic_pool_sku_from_capabilities(cli_ctx, location, sku, allow_reset_family=False, compute_model=None):
    '''
    Given a requested sku which may have some properties filled in
    (e.g. tier and capacity), finds the canonical matching sku
    from the given location's capabilities.
    '''

    logger.debug('_find_elastic_pool_sku_from_capabilities input: %s', sku)

    if sku.name:
        # User specified sku.name, so nothing else needs to be resolved.
        logger.debug('_find_elastic_pool_sku_from_capabilities return sku as is')
        return sku

    if not _any_sku_values_specified(sku):
        # User did not request any properties of sku, so just wipe it out.
        # Server side will pick a default.
        logger.debug('_find_elastic_pool_sku_from_capabilities return None')
        return None

    # Some properties of sku are specified, but not name. Use the requested properties
    # to find a matching capability and copy the sku from there.

    # Get location capability
    loc_capability = _get_location_capability(cli_ctx, location, CapabilityGroup.supported_elastic_pool_editions)

    # Get default server version capability
    server_version_capability = _get_default_server_version(loc_capability)

    # Find edition capability, based on requested sku properties
    edition_capability = _find_edition_capability(sku, server_version_capability.supported_elastic_pool_editions)

    # Find performance level capability, based on requested sku properties
    performance_level_capability = _find_performance_level_capability(
        sku, edition_capability.supported_elastic_pool_performance_levels,
        allow_reset_family=allow_reset_family,
        compute_model=compute_model)

    # Copy sku object from capability
    result = performance_level_capability.sku
    logger.debug('_find_elastic_pool_sku_from_capabilities return: %s', result)
    return result


def elastic_pool_create(
        cmd,
        client,
        server_name,
        resource_group_name,
        elastic_pool_name,
        sku=None,
        **kwargs):
    '''
    Creates an elastic pool.
    '''

    # Determine server location
    kwargs['location'] = _get_server_location(
        cmd.cli_ctx,
        server_name=server_name,
        resource_group_name=resource_group_name)

    # If sku.name is not specified, resolve the requested sku name
    # using capabilities.
    kwargs['sku'] = _find_elastic_pool_sku_from_capabilities(cmd.cli_ctx, kwargs['location'], sku)

    # Create
    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        elastic_pool_name=elastic_pool_name,
        parameters=kwargs)


def elastic_pool_update(
        cmd,
        instance,
        max_capacity=None,
        min_capacity=None,
        max_size_bytes=None,
        zone_redundant=None,
        tier=None,
        family=None,
        capacity=None):
    '''
    Updates an elastic pool. Custom update function to apply parameters to instance.
    '''

    #####
    # Set sku-related properties
    #####

    # Update sku
    _db_elastic_pool_update_sku(
        cmd,
        instance,
        None,  # service_objective
        tier,
        family,
        capacity,
        find_sku_from_capabilities_func=_find_elastic_pool_sku_from_capabilities)

    #####
    # Set other properties
    #####

    if max_capacity:
        instance.per_database_settings.max_capacity = max_capacity

    if min_capacity:
        instance.per_database_settings.min_capacity = min_capacity

    if max_size_bytes:
        instance.max_size_bytes = max_size_bytes

    if zone_redundant is not None:
        instance.zone_redundant = zone_redundant

    return instance


class ElasticPoolCapabilitiesAdditionalDetails(Enum):  # pylint: disable=too-few-public-methods
    '''
    Additional details that may be optionally included when getting elastic pool capabilities.
    '''

    max_size = 'max-size'
    db_min_dtu = 'db-min-dtu'
    db_max_dtu = 'db-max-dtu'
    db_max_size = 'db-max-size'


def elastic_pool_list_capabilities(
        client,
        location,
        edition=None,
        dtu=None,
        vcores=None,
        show_details=None,
        available=False):
    '''
    Gets elastic pool capabilities and optionally applies the specified filters.
    '''

    # Fixup parameters
    if not show_details:
        show_details = []
    if dtu:
        dtu = int(dtu)

    # Get capabilities tree from server
    capabilities = client.list_by_location(location, CapabilityGroup.supported_elastic_pool_editions)

    # Get subtree related to elastic pools
    editions = _get_default_server_version(capabilities).supported_elastic_pool_editions

    # Filter by edition
    if edition:
        editions = [e for e in editions if e.name.lower() == edition.lower()]

    # Filter by dtu
    if dtu:
        for e in editions:
            e.supported_elastic_pool_performance_levels = [
                pl for pl in e.supported_elastic_pool_performance_levels
                if pl.performance_level.value == int(dtu) and
                pl.performance_level.unit == PerformanceLevelUnit.dtu.value]

    # Filter by vcores
    if vcores:
        for e in editions:
            e.supported_elastic_pool_performance_levels = [
                pl for pl in e.supported_elastic_pool_performance_levels
                if pl.performance_level.value == int(vcores) and
                pl.performance_level.unit == PerformanceLevelUnit.vcores.value]

    # Filter by availability
    if available:
        editions = _filter_available(editions)
        for e in editions:
            e.supported_elastic_pool_performance_levels = _filter_available(e.supported_elastic_pool_performance_levels)
            for slo in e.supported_service_level_objectives:
                slo.supported_max_sizes = _filter_available(slo.supported_max_sizes)

    # Remove editions with no service objectives (due to filters)
    editions = [e for e in editions if e.supported_elastic_pool_performance_levels]

    for e in editions:
        for d in e.supported_elastic_pool_performance_levels:
            # Optionally hide supported max sizes
            if ElasticPoolCapabilitiesAdditionalDetails.max_size.value not in show_details:
                d.supported_max_sizes = []

            # Optionally hide per database min & max dtus. min dtus are nested inside max dtus,
            # so only hide max dtus if both min and max should be hidden.
            if ElasticPoolCapabilitiesAdditionalDetails.db_min_dtu.value not in show_details:
                if ElasticPoolCapabilitiesAdditionalDetails.db_max_dtu.value not in show_details:
                    d.supported_per_database_max_performance_levels = []

                for md in d.supported_per_database_max_performance_levels:
                    md.supported_per_database_min_performance_levels = []

            # Optionally hide supported per db max sizes
            if ElasticPoolCapabilitiesAdditionalDetails.db_max_size.value not in show_details:
                d.supported_per_database_max_sizes = []

    return editions

###############################################
#                sql instance-pool            #
###############################################


def instance_pool_list(
        client,
        resource_group_name=None):
    '''
    Lists servers in a resource group or subscription
    '''

    if resource_group_name:
        # List all instance pools in the resource group
        return client.list_by_resource_group(
            resource_group_name=resource_group_name)

    # List all instance pools in the subscription
    return client.list()


def instance_pool_create(
        cmd,
        client,
        instance_pool_name,
        resource_group_name,
        no_wait=False,
        sku=None,
        **kwargs):
    '''
    Creates a new instance pool
    '''

    kwargs['sku'] = _find_instance_pool_sku_from_capabilities(
        cmd.cli_ctx, kwargs['location'], sku)

    return sdk_no_wait(no_wait, client.create_or_update,
                       instance_pool_name=instance_pool_name,
                       resource_group_name=resource_group_name,
                       parameters=kwargs)


def _find_instance_pool_sku_from_capabilities(cli_ctx, location, sku):
    '''
    Validate if the sku family and edition input by user are permissible in the region using
    capabilities API and get the SKU name
    '''

    logger.debug('_find_instance_pool_sku_from_capabilities input: %s', sku)

    # Get location capability
    loc_capability = _get_location_capability(
        cli_ctx, location, CapabilityGroup.supported_managed_instance_versions)

    # Get default server version capability
    managed_instance_version_capability = _get_default_capability(
        loc_capability.supported_managed_instance_versions)

    # Find edition capability, based on requested sku properties
    edition_capability = _find_edition_capability(
        sku, managed_instance_version_capability.supported_instance_pool_editions)

    # Find family level capability, based on requested sku properties
    _find_family_capability(
        sku, edition_capability.supported_families)

    result = Sku(
        name="instance-pool",
        tier=sku.tier,
        family=sku.family)

    logger.debug(
        '_find_instance_pool_sku_from_capabilities return: %s',
        result)
    return result


###############################################
#                sql server                   #
###############################################

def server_create(
        client,
        resource_group_name,
        server_name,
        assign_identity=False,
        no_wait=False,
        enable_public_network=None,
        **kwargs):
    '''
    Creates a server.
    '''

    if assign_identity:
        kwargs['identity'] = ResourceIdentity(type=IdentityType.system_assigned.value)

    if enable_public_network is not None:
        kwargs['public_network_access'] = (
            ServerPublicNetworkAccess.enabled if enable_public_network
            else ServerPublicNetworkAccess.disabled)

    # Create
    return sdk_no_wait(no_wait, client.create_or_update,
                       server_name=server_name,
                       resource_group_name=resource_group_name,
                       parameters=kwargs)


def server_list(
        client,
        resource_group_name=None):
    '''
    Lists servers in a resource group or subscription
    '''

    if resource_group_name:
        # List all servers in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all servers in the subscription
    return client.list()


def server_update(
        instance,
        administrator_login_password=None,
        assign_identity=False,
        minimal_tls_version=None,
        enable_public_network=None):
    '''
    Updates a server. Custom update function to apply parameters to instance.
    '''

    # Once assigned, the identity cannot be removed
    if instance.identity is None and assign_identity:
        instance.identity = ResourceIdentity(type=IdentityType.system_assigned.value)

    # Apply params to instance
    instance.administrator_login_password = (
        administrator_login_password or instance.administrator_login_password)
    instance.minimal_tls_version = (
        minimal_tls_version or instance.minimal_tls_version)

    if enable_public_network is not None:
        instance.public_network_access = (
            ServerPublicNetworkAccess.enabled if enable_public_network
            else ServerPublicNetworkAccess.disabled)

    return instance


#####
#           sql server ad-admin
#####


def server_ad_admin_set(
        client,
        resource_group_name,
        server_name,
        **kwargs):
    '''
    Sets a server's AD admin.
    '''

    kwargs['tenant_id'] = _get_tenant_id()

    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        parameters=kwargs)


def server_ad_admin_update(
        instance,
        login=None,
        sid=None,
        tenant_id=None):
    '''
    Updates a server' AD admin.
    '''

    # Apply params to instance
    instance.login = login or instance.login
    instance.sid = sid or instance.sid
    instance.tenant_id = tenant_id or instance.tenant_id

    return instance

#####
#           sql server firewall-rule
#####


def firewall_rule_allow_all_azure_ips(
        client,
        server_name,
        resource_group_name):
    '''
    Creates a firewall rule with special start/end ip address value
    that represents all azure ips.
    '''

    # Name of the rule that will be created
    rule_name = 'AllowAllAzureIPs'

    # Special start/end IP that represents allowing all azure ips
    azure_ip_addr = '0.0.0.0'

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name=rule_name,
        start_ip_address=azure_ip_addr,
        end_ip_address=azure_ip_addr)


def firewall_rule_update(
        client,
        firewall_rule_name,
        server_name,
        resource_group_name,
        start_ip_address=None,
        end_ip_address=None):
    '''
    Updates a firewall rule.
    '''

    # Get existing instance
    instance = client.get(
        firewall_rule_name=firewall_rule_name,
        server_name=server_name,
        resource_group_name=resource_group_name)

    # Send update
    return client.create_or_update(
        firewall_rule_name=firewall_rule_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        start_ip_address=start_ip_address or instance.start_ip_address,
        end_ip_address=end_ip_address or instance.end_ip_address)


#####
#           sql server key
#####


def server_key_create(
        client,
        resource_group_name,
        server_name,
        kid=None):
    '''
    Creates a server key.
    '''

    key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name,
        parameters=ServerKey(
            server_key_type=ServerKeyType.azure_key_vault.value,
            uri=kid
        )
    )


def server_key_get(
        client,
        resource_group_name,
        server_name,
        kid):
    '''
    Gets a server key.
    '''

    key_name = _get_server_key_name_from_uri(kid)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def server_key_delete(
        client,
        resource_group_name,
        server_name,
        kid):
    '''
    Deletes a server key.
    '''

    key_name = _get_server_key_name_from_uri(kid)

    return client.delete(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def _get_server_key_name_from_uri(uri):
    '''
    Gets the key's name to use as a SQL server key.

    The SQL server key API requires that the server key has a specific name
    based on the vault, key and key version.
    '''
    import re

    match = re.match(r'^https(.)+\.vault(.)+\/keys\/[^\/]+\/[0-9a-zA-Z]+$', uri)

    if match is None:
        raise CLIError('The provided uri is invalid. Please provide a valid Azure Key Vault key id.  For example: '
                       '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

    vault = uri.split('.')[0].split('/')[-1]
    key = uri.split('/')[-2]
    version = uri.split('/')[-1]
    return '{}_{}_{}'.format(vault, key, version)


#####
#           sql server dns-alias
#####


def server_dns_alias_set(
        cmd,
        client,
        resource_group_name,
        server_name,
        dns_alias_name,
        original_server_name,
        original_subscription_id=None,
        original_resource_group_name=None):
    '''
    Sets a server DNS alias.
    '''
    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from six.moves.urllib.parse import quote  # pylint: disable=import-error
    from azure.cli.core.commands.client_factory import get_subscription_id

    # Build the old alias id
    old_alias_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/dnsAliases/{}".format(
        quote(original_subscription_id or get_subscription_id(cmd.cli_ctx)),
        quote(original_resource_group_name or resource_group_name),
        quote(original_server_name),
        quote(dns_alias_name))

    return client.acquire(
        resource_group_name=resource_group_name,
        server_name=server_name,
        dns_alias_name=dns_alias_name,
        old_server_dns_alias_id=old_alias_id
    )

#####
#           sql server encryption-protector
#####


def encryption_protector_update(
        client,
        resource_group_name,
        server_name,
        server_key_type,
        kid=None):
    '''
    Updates a server encryption protector.
    '''

    if server_key_type == ServerKeyType.service_managed.value:
        key_name = 'ServiceManaged'
    else:
        if kid is None:
            raise CLIError('A uri must be provided if the server_key_type is AzureKeyVault.')
        key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        server_key_type=server_key_type,
        server_key_name=key_name
    )

###############################################
#                sql managed instance         #
###############################################


def _find_managed_instance_sku_from_capabilities(
        cli_ctx,
        location,
        sku):
    '''
    Given a requested sku which may have some properties filled in
    (e.g. tier and family), finds the canonical matching sku
    from the given location's capabilities.
    '''

    logger.debug('_find_managed_instance_sku_from_capabilities input: %s', sku)

    if not _any_sku_values_specified(sku):
        # User did not request any properties of sku, so just wipe it out.
        # Server side will pick a default.
        logger.debug('_find_managed_instance_sku_from_capabilities return None')
        return None

    # Some properties of sku are specified, but not name. Use the requested properties
    # to find a matching capability and copy the sku from there.

    # Get location capability
    loc_capability = _get_location_capability(cli_ctx, location, CapabilityGroup.supported_managed_instance_versions)

    # Get default server version capability
    managed_instance_version_capability = _get_default_capability(loc_capability.supported_managed_instance_versions)

    # Find edition capability, based on requested sku properties
    edition_capability = _find_edition_capability(sku, managed_instance_version_capability.supported_editions)

    # Find family level capability, based on requested sku properties
    family_capability = _find_family_capability(sku, edition_capability.supported_families)

    result = Sku(name=family_capability.sku)
    logger.debug('_find_managed_instance_sku_from_capabilities return: %s', result)
    return result


def managed_instance_create(
        cmd,
        client,
        managed_instance_name,
        resource_group_name,
        location,
        virtual_network_subnet_id,
        assign_identity=False,
        sku=None,
        **kwargs):
    '''
    Creates a managed instance.
    '''

    if assign_identity:
        kwargs['identity'] = ResourceIdentity(type=IdentityType.system_assigned.value)

    kwargs['location'] = location
    kwargs['sku'] = _find_managed_instance_sku_from_capabilities(cmd.cli_ctx, kwargs['location'], sku)
    kwargs['subnet_id'] = virtual_network_subnet_id

    # Create
    return client.create_or_update(
        managed_instance_name=managed_instance_name,
        resource_group_name=resource_group_name,
        parameters=kwargs)


def managed_instance_list(
        client,
        resource_group_name=None):
    '''
    Lists managed instances in a resource group or subscription
    '''

    if resource_group_name:
        # List all managed instances in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all managed instances in the subscription
    return client.list()


def managed_instance_update(
        cmd,
        instance,
        administrator_login_password=None,
        license_type=None,
        vcores=None,
        storage_size_in_gb=None,
        assign_identity=False,
        proxy_override=None,
        public_data_endpoint_enabled=None,
        tier=None,
        family=None,
        minimal_tls_version=None):
    '''
    Updates a managed instance. Custom update function to apply parameters to instance.
    '''

    # Once assigned, the identity cannot be removed
    if instance.identity is None and assign_identity:
        instance.identity = ResourceIdentity(type=IdentityType.system_assigned.value)

    # Apply params to instance
    instance.administrator_login_password = (
        administrator_login_password or instance.administrator_login_password)
    instance.license_type = (
        license_type or instance.license_type)
    instance.v_cores = (
        vcores or instance.v_cores)
    instance.storage_size_in_gb = (
        storage_size_in_gb or instance.storage_size_in_gb)
    instance.proxy_override = (
        proxy_override or instance.proxy_override)
    instance.minimal_tls_version = (
        minimal_tls_version or instance.minimal_tls_version)

    instance.sku.name = None
    instance.sku.tier = (
        tier or instance.sku.tier)
    instance.sku.family = (
        family or instance.sku.family)
    instance.sku = _find_managed_instance_sku_from_capabilities(
        cmd.cli_ctx,
        instance.location,
        instance.sku)

    if public_data_endpoint_enabled is not None:
        instance.public_data_endpoint_enabled = public_data_endpoint_enabled

    return instance


#####
#           sql managed instance key
#####


def managed_instance_key_create(
        client,
        resource_group_name,
        managed_instance_name,
        kid=None):
    '''
    Creates a managed instance key.
    '''

    key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        managed_instance_name=managed_instance_name,
        key_name=key_name,
        server_key_type=ServerKeyType.azure_key_vault.value,
        uri=kid
    )


def managed_instance_key_get(
        client,
        resource_group_name,
        managed_instance_name,
        kid):
    '''
    Gets a managed instance key.
    '''

    key_name = _get_server_key_name_from_uri(kid)

    return client.get(
        resource_group_name=resource_group_name,
        managed_instance_name=managed_instance_name,
        key_name=key_name)


def managed_instance_key_delete(
        client,
        resource_group_name,
        managed_instance_name,
        kid):
    '''
    Deletes a managed instance key.
    '''

    key_name = _get_server_key_name_from_uri(kid)

    return client.delete(
        resource_group_name=resource_group_name,
        managed_instance_name=managed_instance_name,
        key_name=key_name)

#####
#           sql managed instance encryption-protector
#####


def managed_instance_encryption_protector_update(
        client,
        resource_group_name,
        managed_instance_name,
        server_key_type,
        kid=None):
    '''
    Updates a server encryption protector.
    '''

    if server_key_type == ServerKeyType.service_managed.value:
        key_name = 'ServiceManaged'
    else:
        if kid is None:
            raise CLIError('A uri must be provided if the server_key_type is AzureKeyVault.')
        key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        managed_instance_name=managed_instance_name,
        server_key_type=server_key_type,
        server_key_name=key_name
    )


#####
#           sql managed instance ad-admin
#####


def mi_ad_admin_set(
        client,
        resource_group_name,
        managed_instance_name,
        **kwargs):
    '''
    Creates a managed instance active directory administrator.
    '''

    kwargs['tenant_id'] = _get_tenant_id()

    return client.create_or_update(
        resource_group_name=resource_group_name,
        managed_instance_name=managed_instance_name,
        parameters=kwargs
    )


def mi_ad_admin_delete(
        client,
        resource_group_name,
        managed_instance_name):
    '''
    Deletes a managed instance active directory administrator.
    '''
    return client.delete(
        resource_group_name=resource_group_name,
        managed_instance_name=managed_instance_name
    )

###############################################
#                sql managed db               #
###############################################


def managed_db_create(
        cmd,
        client,
        database_name,
        managed_instance_name,
        resource_group_name,
        **kwargs):

    # Determine managed instance location
    kwargs['location'] = _get_managed_instance_location(
        cmd.cli_ctx,
        managed_instance_name=managed_instance_name,
        resource_group_name=resource_group_name)

    # Create
    return client.create_or_update(
        database_name=database_name,
        managed_instance_name=managed_instance_name,
        resource_group_name=resource_group_name,
        parameters=kwargs)


def managed_db_restore(
        cmd,
        client,
        database_name,
        managed_instance_name,
        resource_group_name,
        target_managed_database_name,
        target_managed_instance_name=None,
        target_resource_group_name=None,
        deleted_time=None,
        **kwargs):
    '''
    Restores an existing managed DB (i.e. create with 'PointInTimeRestore' create mode.)

    Custom function makes create mode more convenient.
    '''

    if not target_managed_instance_name:
        target_managed_instance_name = managed_instance_name

    if not target_resource_group_name:
        target_resource_group_name = resource_group_name

    kwargs['location'] = _get_managed_instance_location(
        cmd.cli_ctx,
        managed_instance_name=managed_instance_name,
        resource_group_name=resource_group_name)

    kwargs['create_mode'] = CreateMode.point_in_time_restore.value

    if deleted_time:
        kwargs['restorable_dropped_database_id'] = _get_managed_dropped_db_resource_id(
            cmd.cli_ctx,
            resource_group_name,
            managed_instance_name,
            database_name,
            deleted_time)
    else:
        kwargs['source_database_id'] = _get_managed_db_resource_id(
            cmd.cli_ctx,
            resource_group_name,
            managed_instance_name,
            database_name)

    return client.create_or_update(
        database_name=target_managed_database_name,
        managed_instance_name=target_managed_instance_name,
        resource_group_name=target_resource_group_name,
        parameters=kwargs)


def update_short_term_retention_mi(
        cmd,
        client,
        database_name,
        managed_instance_name,
        resource_group_name,
        retention_days,
        deleted_time=None):
    '''
    Updates short term retention for database
    '''

    if deleted_time:
        database_name = '{},{}'.format(
            database_name,
            _to_filetimeutc(deleted_time))

        client = \
            get_sql_restorable_dropped_database_managed_backup_short_term_retention_policies_operations(
                cmd.cli_ctx,
                None)

        policy = client.create_or_update(
            restorable_dropped_database_id=database_name,
            managed_instance_name=managed_instance_name,
            resource_group_name=resource_group_name,
            retention_days=retention_days)
    else:
        policy = client.create_or_update(
            database_name=database_name,
            managed_instance_name=managed_instance_name,
            resource_group_name=resource_group_name,
            retention_days=retention_days)

    return policy


def get_short_term_retention_mi(
        cmd,
        client,
        database_name,
        managed_instance_name,
        resource_group_name,
        deleted_time=None):
    '''
    Gets short term retention for database
    '''

    if deleted_time:
        database_name = '{},{}'.format(
            database_name,
            _to_filetimeutc(deleted_time))

        client = \
            get_sql_restorable_dropped_database_managed_backup_short_term_retention_policies_operations(
                cmd.cli_ctx,
                None)

        policy = client.get(
            restorable_dropped_database_id=database_name,
            managed_instance_name=managed_instance_name,
            resource_group_name=resource_group_name)
    else:
        policy = client.get(
            database_name=database_name,
            managed_instance_name=managed_instance_name,
            resource_group_name=resource_group_name)

    return policy


def _is_int(retention):
    try:
        int(retention)
        return True
    except ValueError:
        return False


def update_long_term_retention_mi(
        client,
        database_name,
        managed_instance_name,
        resource_group_name,
        weekly_retention=None,
        monthly_retention=None,
        yearly_retention=None,
        week_of_year=None,
        **kwargs):
    '''
    Updates long term retention for managed database
    '''

    if not (weekly_retention or monthly_retention or yearly_retention):
        raise CLIError('Please specify retention setting(s).  See \'--help\' for more details.')

    if yearly_retention and not week_of_year:
        raise CLIError('Please specify week of year for yearly retention.')

    # if an int is provided for retention, convert to ISO 8601 using days
    if (weekly_retention and _is_int(weekly_retention)):
        weekly_retention = 'P%sD' % weekly_retention
        print(weekly_retention)

    if (monthly_retention and _is_int(monthly_retention)):
        monthly_retention = 'P%sD' % monthly_retention

    if (yearly_retention and _is_int(yearly_retention)):
        yearly_retention = 'P%sD' % yearly_retention

    kwargs['weekly_retention'] = weekly_retention

    kwargs['monthly_retention'] = monthly_retention

    kwargs['yearly_retention'] = yearly_retention

    kwargs['week_of_year'] = week_of_year

    policy = client.create_or_update(
        database_name=database_name,
        managed_instance_name=managed_instance_name,
        resource_group_name=resource_group_name,
        parameters=kwargs)

    return policy


def _get_backup_id_resource_values(backup_id):
    '''
    Extract resource values from the backup id
    '''

    backup_id = backup_id.replace('\'', '')
    backup_id = backup_id.replace('"', '')

    if backup_id[0] == '/':
        # remove leading /
        backup_id = backup_id[1:]

    resources_list = backup_id.split('/')
    resources_dict = {resources_list[i]: resources_list[i + 1] for i in range(0, len(resources_list), 2)}

    if not ('locations'.casefold() in resources_dict and
            'longTermRetentionManagedInstances'.casefold() not in resources_dict and
            'longTermRetentionDatabases'.casefold() not in resources_dict and
            'longTermRetentionManagedInstanceBackups'.casefold() not in resources_dict):

        # backup ID should contain all these
        raise CLIError('Please provide a valid resource URI.  See --help for example.')

    return resources_dict


def get_long_term_retention_mi_backup(
        client,
        location_name=None,
        managed_instance_name=None,
        database_name=None,
        backup_name=None,
        backup_id=None):
    '''
    Gets the requested long term retention backup.
    '''

    if backup_id:
        resources_dict = _get_backup_id_resource_values(backup_id)

        location_name = resources_dict['locations']
        managed_instance_name = resources_dict['longTermRetentionManagedInstances']
        database_name = resources_dict['longTermRetentionDatabases']
        backup_name = resources_dict['longTermRetentionManagedInstanceBackups']

    return client.get(
        location_name=location_name,
        managed_instance_name=managed_instance_name,
        database_name=database_name,
        backup_name=backup_name)


def _list_by_database_long_term_retention_mi_backups(
        client,
        location_name,
        managed_instance_name,
        database_name,
        resource_group_name=None,
        only_latest_per_database=None,
        database_state=None):
    '''
    Gets the long term retention backups for a Managed Database
    '''

    if resource_group_name:
        backups = client.list_by_resource_group_database(
            resource_group_name=resource_group_name,
            location_name=location_name,
            managed_instance_name=managed_instance_name,
            database_name=database_name,
            only_latest_per_database=only_latest_per_database,
            database_state=database_state)
    else:
        backups = client.list_by_database(
            location_name=location_name,
            managed_instance_name=managed_instance_name,
            database_name=database_name,
            only_latest_per_database=only_latest_per_database,
            database_state=database_state)

    return backups


def _list_by_instance_long_term_retention_mi_backups(
        client,
        location_name,
        managed_instance_name,
        resource_group_name=None,
        only_latest_per_database=None,
        database_state=None):
    '''
    Gets the long term retention backups within a Managed Instance
    '''

    if resource_group_name:
        backups = client.list_by_resource_group_instance(
            resource_group_name=resource_group_name,
            location_name=location_name,
            managed_instance_name=managed_instance_name,
            only_latest_per_database=only_latest_per_database,
            database_state=database_state)
    else:
        backups = client.list_by_instance(
            location_name=location_name,
            managed_instance_name=managed_instance_name,
            only_latest_per_database=only_latest_per_database,
            database_state=database_state)

    return backups


def _list_by_location_long_term_retention_mi_backups(
        client,
        location_name,
        resource_group_name=None,
        only_latest_per_database=None,
        database_state=None):
    '''
    Gets the long term retention backups within a specified region.
    '''

    if resource_group_name:
        backups = client.list_by_resource_group_location(
            resource_group_name=resource_group_name,
            location_name=location_name,
            only_latest_per_database=only_latest_per_database,
            database_state=database_state)
    else:
        backups = client.list_by_location(
            location_name=location_name,
            only_latest_per_database=only_latest_per_database,
            database_state=database_state)

    return backups


def list_long_term_retention_mi_backups(
        client,
        location_name,
        managed_instance_name=None,
        database_name=None,
        resource_group_name=None,
        only_latest_per_database=None,
        database_state=None):
    '''
    Lists the long term retention backups for a specified location, instance, or database.
    '''

    if managed_instance_name:
        if database_name:
            backups = _list_by_database_long_term_retention_mi_backups(
                client,
                location_name,
                managed_instance_name,
                database_name,
                resource_group_name,
                only_latest_per_database,
                database_state)

        else:
            backups = _list_by_instance_long_term_retention_mi_backups(
                client,
                location_name,
                managed_instance_name,
                resource_group_name,
                only_latest_per_database,
                database_state)
    else:
        backups = _list_by_location_long_term_retention_mi_backups(
            client,
            location_name,
            resource_group_name,
            only_latest_per_database,
            database_state)

    return backups


def delete_long_term_retention_mi_backup(
        client,
        location_name=None,
        managed_instance_name=None,
        database_name=None,
        backup_name=None,
        backup_id=None):
    '''
    Deletes the requested long term retention backup.
    '''

    if backup_id:
        resources_dict = _get_backup_id_resource_values(backup_id)

        location_name = resources_dict['locations']
        managed_instance_name = resources_dict['longTermRetentionManagedInstances']
        database_name = resources_dict['longTermRetentionDatabases']
        backup_name = resources_dict['longTermRetentionManagedInstanceBackups']

    return client.delete(
        location_name=location_name,
        managed_instance_name=managed_instance_name,
        database_name=database_name,
        backup_name=backup_name)


def restore_long_term_retention_mi_backup(
        cmd,
        client,
        long_term_retention_backup_resource_id,
        target_managed_database_name,
        target_managed_instance_name,
        target_resource_group_name,
        **kwargs):
    '''
    Restores an existing managed DB (i.e. create with 'RestoreLongTermRetentionBackup' create mode.)
    '''

    if not target_resource_group_name or not target_managed_instance_name or not target_managed_database_name:
        raise CLIError('Please specify target resource(s). '
                       'Target resource group, target instance, and target database '
                       'are all required for restore LTR backup.')

    if not long_term_retention_backup_resource_id:
        raise CLIError('Please specify a long term retention backup.')

    kwargs['location'] = _get_managed_instance_location(
        cmd.cli_ctx,
        managed_instance_name=target_managed_instance_name,
        resource_group_name=target_resource_group_name)

    kwargs['create_mode'] = CreateMode.restore_long_term_retention_backup.value
    kwargs['long_term_retention_backup_resource_id'] = long_term_retention_backup_resource_id

    return client.create_or_update(
        database_name=target_managed_database_name,
        managed_instance_name=target_managed_instance_name,
        resource_group_name=target_resource_group_name,
        parameters=kwargs)

###############################################
#              sql failover-group             #
###############################################


def failover_group_create(
        cmd,
        client,
        resource_group_name,
        server_name,
        failover_group_name,
        partner_server,
        partner_resource_group=None,
        failover_policy=FailoverPolicyType.automatic.value,
        grace_period=1,
        add_db=None):
    '''
    Creates a failover group.
    '''

    from six.moves.urllib.parse import quote  # pylint: disable=import-error
    from azure.cli.core.commands.client_factory import get_subscription_id

    # Build the partner server id
    partner_server_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}".format(
        quote(get_subscription_id(cmd.cli_ctx)),
        quote(partner_resource_group or resource_group_name),
        quote(partner_server))

    partner_server = PartnerInfo(id=partner_server_id)

    # Convert grace period from hours to minutes
    grace_period = int(grace_period) * 60

    if failover_policy == FailoverPolicyType.manual.value:
        grace_period = None

    if add_db is None:
        add_db = []

    databases = _get_list_of_databases_for_fg(
        cmd,
        resource_group_name,
        server_name,
        [],
        add_db,
        [])

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        failover_group_name=failover_group_name,
        parameters=FailoverGroup(
            partner_servers=[partner_server],
            databases=databases,
            read_write_endpoint=FailoverGroupReadWriteEndpoint(
                failover_policy=failover_policy,
                failover_with_data_loss_grace_period_minutes=grace_period),
            read_only_endpoint=FailoverGroupReadOnlyEndpoint(
                failover_policy="Disabled")))


def failover_group_update(
        cmd,
        instance,
        resource_group_name,
        server_name,
        failover_policy=None,
        grace_period=None,
        add_db=None,
        remove_db=None):
    '''
    Updates the failover group.
    '''

    failover_group_update_common(
        instance,
        failover_policy,
        grace_period)

    if add_db is None:
        add_db = []

    if remove_db is None:
        remove_db = []

    databases = _get_list_of_databases_for_fg(
        cmd,
        resource_group_name,
        server_name,
        instance.databases,
        add_db,
        remove_db)

    instance.databases = databases

    return instance


def failover_group_failover(
        client,
        resource_group_name,
        server_name,
        failover_group_name,
        allow_data_loss=False):
    '''
    Failover a failover group.
    '''

    failover_group = client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        failover_group_name=failover_group_name)

    if failover_group.replication_role == "Primary":
        return

    # Choose which failover method to use
    if allow_data_loss:
        failover_func = client.force_failover_allow_data_loss
    else:
        failover_func = client.failover

    return failover_func(
        resource_group_name=resource_group_name,
        server_name=server_name,
        failover_group_name=failover_group_name)


def _get_list_of_databases_for_fg(
        cmd,
        resource_group_name,
        server_name,
        databases_in_fg,
        add_db,
        remove_db):
    '''
    Gets a list of databases that are supposed to be part of the failover group
    after the operation finishes
    It consolidates the list of dbs to add and remove with the list of databases
    that are already part of the failover group.
    '''

    add_db_ids = [DatabaseIdentity(cmd.cli_ctx, d, server_name, resource_group_name).id() for d in add_db]

    remove_db_ids = [DatabaseIdentity(cmd.cli_ctx, d, server_name, resource_group_name).id() for d in remove_db]

    databases = list(({x.lower() for x in databases_in_fg} |
                      {x.lower() for x in add_db_ids}) - {x.lower() for x in remove_db_ids})

    return databases

###############################################
#                sql virtual cluster          #
###############################################


def virtual_cluster_list(
        client,
        resource_group_name=None):
    '''
    Lists virtual clusters in a resource group or subscription
    '''

    if resource_group_name:
        # List all virtual clusters in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all virtual clusters in the subscription
    return client.list()


###############################################
#              sql instance failover group    #
###############################################

def instance_failover_group_create(
        cmd,
        client,
        resource_group_name,
        managed_instance,
        failover_group_name,
        partner_managed_instance,
        partner_resource_group,
        failover_policy=FailoverPolicyType.automatic.value,
        grace_period=1):
    '''
    Creates a failover group.
    '''

    managed_instance_client = get_sql_managed_instances_operations(cmd.cli_ctx, None)
    # pylint: disable=no-member
    primary_server = managed_instance_client.get(
        managed_instance_name=managed_instance,
        resource_group_name=resource_group_name)

    partner_server = managed_instance_client.get(
        managed_instance_name=partner_managed_instance,
        resource_group_name=partner_resource_group)

    # Build the partner server id
    managed_server_info_pair = ManagedInstancePairInfo(
        primary_managed_instance_id=primary_server.id,
        partner_managed_instance_id=partner_server.id)
    partner_region_info = PartnerRegionInfo(location=partner_server.location)

    # Convert grace period from hours to minutes
    grace_period = int(grace_period) * 60

    if failover_policy == FailoverPolicyType.manual.value:
        grace_period = None

    return client.create_or_update(
        resource_group_name=resource_group_name,
        location_name=primary_server.location,
        failover_group_name=failover_group_name,
        parameters=InstanceFailoverGroup(
            managed_instance_pairs=[managed_server_info_pair],
            partner_regions=[partner_region_info],
            read_write_endpoint=InstanceFailoverGroupReadWriteEndpoint(
                failover_policy=failover_policy,
                failover_with_data_loss_grace_period_minutes=grace_period),
            read_only_endpoint=InstanceFailoverGroupReadOnlyEndpoint(
                failover_policy="Disabled")))


def instance_failover_group_update(
        instance,
        failover_policy=None,
        grace_period=None,):
    '''
    Updates the failover group.
    '''

    failover_group_update_common(
        instance,
        failover_policy,
        grace_period)

    return instance


def instance_failover_group_failover(
        cmd,
        client,
        resource_group_name,
        failover_group_name,
        location_name,
        allow_data_loss=False):
    '''
    Failover an instance failover group.
    '''

    from azure.cli.core.commands.client_factory import get_subscription_id

    failover_group = client.get(
        resource_group_name=resource_group_name,
        subscription_id=get_subscription_id(cmd.cli_ctx),
        failover_group_name=failover_group_name,
        location_name=location_name)

    if failover_group.replication_role == "Primary":
        return

    # Choose which failover method to use
    if allow_data_loss:
        failover_func = client.force_failover_allow_data_loss
    else:
        failover_func = client.failover

    return failover_func(
        resource_group_name=resource_group_name,
        failover_group_name=failover_group_name,
        location_name=location_name)
