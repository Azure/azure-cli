# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO Move this to a package shared by CLI and SDK
from enum import Enum
from functools import total_ordering
from importlib import import_module

from knack.log import get_logger


logger = get_logger(__name__)


class APIVersionException(Exception):
    def __init__(self, type_name, api_profile):
        super(APIVersionException, self).__init__(type_name, api_profile)
        self.type_name = type_name
        self.api_profile = api_profile

    def __str__(self):
        return "Unable to get API version for type '{}' in profile '{}'".format(
            self.type_name, self.api_profile)


# Sentinel value for profile
PROFILE_TYPE = object()


class CustomResourceType:  # pylint: disable=too-few-public-methods
    def __init__(self, import_prefix, client_name):
        self.import_prefix = import_prefix
        self.client_name = client_name


class ResourceType(Enum):  # pylint: disable=too-few-public-methods

    MGMT_APIMANAGEMENT = ('azure.mgmt.apimanagement', 'ApiManagementClient')
    MGMT_KUSTO = ('azure.mgmt.kusto', 'KustoManagementClient')
    MGMT_KEYVAULT = ('azure.mgmt.keyvault', 'KeyVaultManagementClient')
    MGMT_STORAGE = ('azure.mgmt.storage', 'StorageManagementClient')
    MGMT_COMPUTE = ('azure.mgmt.compute', 'ComputeManagementClient')
    MGMT_NETWORK = ('azure.mgmt.network', 'NetworkManagementClient')
    MGMT_NETWORK_DNS = ('azure.mgmt.dns', 'DnsManagementClient')
    MGMT_AUTHORIZATION = ('azure.mgmt.authorization', 'AuthorizationManagementClient')
    MGMT_CONTAINERREGISTRY = ('azure.mgmt.containerregistry', 'ContainerRegistryManagementClient')
    MGMT_RESOURCE_FEATURES = ('azure.mgmt.resource.features', 'FeatureClient')
    MGMT_RESOURCE_LINKS = ('azure.mgmt.resource.links', 'ManagementLinkClient')
    MGMT_RESOURCE_LOCKS = ('azure.mgmt.resource.locks', 'ManagementLockClient')
    MGMT_RESOURCE_POLICY = ('azure.mgmt.resource.policy', 'PolicyClient')
    MGMT_RESOURCE_RESOURCES = ('azure.mgmt.resource.resources', 'ResourceManagementClient')
    MGMT_RESOURCE_SUBSCRIPTIONS = ('azure.mgmt.resource.subscriptions', 'SubscriptionClient')
    MGMT_RESOURCE_DEPLOYMENTSCRIPTS = ('azure.mgmt.resource.deploymentscripts', 'DeploymentScriptsClient')
    MGMT_RESOURCE_TEMPLATESPECS = ('azure.mgmt.resource.templatespecs', 'TemplateSpecsClient')
    MGMT_RESOURCE_PRIVATELINKS = ('azure.mgmt.resource.privatelinks', 'ResourcePrivateLinkClient')
    MGMT_MONITOR = ('azure.mgmt.monitor', 'MonitorManagementClient')
    MGMT_MSI = ('azure.mgmt.msi', 'ManagedServiceIdentityClient')
    DATA_KEYVAULT = ('azure.keyvault', 'KeyVaultClient')
    DATA_KEYVAULT_KEYS = ('azure.keyvault.keys', 'KeyClient')
    DATA_PRIVATE_KEYVAULT = ('azure.cli.command_modules.keyvault.vendored_sdks.azure_keyvault_t1', 'KeyVaultClient')
    DATA_KEYVAULT_ADMINISTRATION_BACKUP = ('azure.keyvault.administration', 'KeyVaultBackupClient')
    DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL = ('azure.keyvault.administration', 'KeyVaultAccessControlClient')
    MGMT_EVENTHUB = ('azure.mgmt.eventhub', 'EventHubManagementClient')
    MGMT_SERVICEBUS = ('azure.mgmt.servicebus', 'ServiceBusManagementClient')
    MGMT_APPSERVICE = ('azure.mgmt.web', 'WebSiteManagementClient')
    MGMT_IOTCENTRAL = ('azure.mgmt.iotcentral', 'IotCentralClient')
    MGMT_IOTHUB = ('azure.mgmt.iothub', 'IotHubClient')
    MGMT_IOTDPS = ('azure.mgmt.iothubprovisioningservices', 'IotDpsClient')
    MGMT_ARO = ('azure.mgmt.redhatopenshift', 'AzureRedHatOpenShiftClient')
    MGMT_DATABOXEDGE = ('azure.mgmt.databoxedge', 'DataBoxEdgeManagementClient')
    MGMT_CUSTOMLOCATION = ('azure.mgmt.extendedlocation', 'CustomLocations')
    MGMT_CONTAINERSERVICE = ('azure.mgmt.containerservice', 'ContainerServiceClient')
    # the "None" below will stay till a command module fills in the type so "get_mgmt_service_client"
    # can be provided with "ResourceType.XXX" to initialize the client object. This usually happens
    # when related commands start to support Multi-API

    DATA_COSMOS_TABLE = ('azure.multiapi.cosmosdb', None)
    MGMT_ADVISOR = ('azure.mgmt.advisor', None)
    MGMT_MEDIA = ('azure.mgmt.media', None)
    MGMT_BACKUP = ('azure.mgmt.recoveryservicesbackup', None)
    MGMT_BATCH = ('azure.mgmt.batch', None)
    MGMT_BATCHAI = ('azure.mgmt.batchai', None)
    MGMT_BILLING = ('azure.mgmt.billing', None)
    MGMT_BOTSERVICE = ('azure.mgmt.botservice', None)
    MGMT_CDN = ('azure.mgmt.cdn', None)
    MGMT_COGNITIVESERVICES = ('azure.mgmt.cognitiveservices', None)
    MGMT_CONSUMPTION = ('azure.mgmt.consumption', None)
    MGMT_CONTAINERINSTANCE = ('azure.mgmt.containerinstance', None)
    MGMT_COSMOSDB = ('azure.mgmt.cosmosdb', None)
    MGMT_DEPLOYMENTMANAGER = ('azure.mgmt.deploymentmanager', None)
    MGMT_DATALAKE_ANALYTICS = ('azure.mgmt.datalake.analytics', None)
    MGMT_DATALAKE_STORE = ('azure.mgmt.datalake.store', None)
    MGMT_DATAMIGRATION = ('azure.mgmt.datamigration', None)
    MGMT_EVENTGRID = ('azure.mgmt.eventgrid', None)
    MGMT_DEVTESTLABS = ('azure.mgmt.devtestlabs', None)
    MGMT_MAPS = ('azure.mgmt.maps', None)
    MGMT_POLICYINSIGHTS = ('azure.mgmt.policyinsights', None)
    MGMT_RDBMS = ('azure.mgmt.rdbms', None)
    MGMT_REDIS = ('azure.mgmt.redis', None)
    MGMT_RELAY = ('azure.mgmt.relay', None)
    MGMT_RESERVATIONS = ('azure.mgmt.reservations', None)
    MGMT_SEARCH = ('azure.mgmt.search', None)
    MGMT_SERVICEFABRIC = ('azure.mgmt.servicefabric', None)
    MGMT_SIGNALR = ('azure.mgmt.signalr', None)
    MGMT_SQL = ('azure.mgmt.sql', None)
    MGMT_SQLVM = ('azure.mgmt.sqlvirtualmachine', None)
    MGMT_MANAGEDSERVICES = ('azure.mgmt.managedservices', None)
    MGMT_NETAPPFILES = ('azure.mgmt.netappfiles', None)
    DATA_STORAGE = ('azure.multiapi.storage', None)
    DATA_STORAGE_BLOB = ('azure.multiapi.storagev2.blob', None)
    DATA_STORAGE_FILEDATALAKE = ('azure.multiapi.storagev2.filedatalake', None)
    DATA_STORAGE_FILESHARE = ('azure.multiapi.storagev2.fileshare', None)
    DATA_STORAGE_QUEUE = ('azure.multiapi.storagev2.queue', None)
    DATA_STORAGE_TABLE = ('azure.data.tables', None)

    def __init__(self, import_prefix, client_name):
        """Constructor.

        :param import_prefix: Path to the (unversioned) module.
        :type import_prefix: str.
        :param client_name: Name the client for this resource type.
        :type client_name: str.
        """
        self.import_prefix = import_prefix
        self.client_name = client_name


class SDKProfile:  # pylint: disable=too-few-public-methods

    def __init__(self, default_api_version, profile=None):
        """Constructor.

        :param str default_api_version: Default API version if not overridden by a profile. Nullable.
        :param profile: A dict operation group name to API version.
        :type profile: dict[str, str]
        """
        self.profile = profile if profile is not None else {}
        self.profile[None] = default_api_version

    @property
    def default_api_version(self):
        return self.profile[None]


AZURE_API_PROFILES = {
    'latest': {
        ResourceType.MGMT_STORAGE: '2021-09-01',
        ResourceType.MGMT_NETWORK: '2021-08-01',
        ResourceType.MGMT_COMPUTE: SDKProfile('2022-03-01', {
            'resource_skus': '2019-04-01',
            'disks': '2022-03-02',
            'disk_encryption_sets': '2022-03-02',
            'disk_accesses': '2020-05-01',
            'snapshots': '2021-12-01',
            'galleries': '2021-10-01',
            'gallery_images': '2021-10-01',
            'gallery_image_versions': '2021-10-01',
            'gallery_applications': '2021-07-01',
            'gallery_application_versions': '2022-01-03',
            'shared_galleries': '2022-01-03',
            'virtual_machine_scale_sets': '2022-03-01',
        }),
        ResourceType.MGMT_RESOURCE_FEATURES: '2021-07-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2021-06-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2021-04-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2019-11-01',
        ResourceType.MGMT_RESOURCE_DEPLOYMENTSCRIPTS: '2020-10-01',
        ResourceType.MGMT_RESOURCE_TEMPLATESPECS: '2021-05-01',
        ResourceType.MGMT_RESOURCE_PRIVATELINKS: '2020-05-01',
        ResourceType.MGMT_NETWORK_DNS: '2018-05-01',
        ResourceType.MGMT_KEYVAULT: SDKProfile('2021-04-01-preview', {
            'vaults': '2021-06-01-preview'
        }),
        ResourceType.MGMT_AUTHORIZATION: SDKProfile('2020-04-01-preview', {
            'classic_administrators': '2015-06-01',
            'role_definitions': '2018-01-01-preview',
            'provider_operations_metadata': '2018-01-01-preview'
        }),
        ResourceType.MGMT_CONTAINERREGISTRY: SDKProfile('2021-08-01-preview', {
            'agent_pools': '2019-06-01-preview',
            'tasks': '2019-06-01-preview',
            'task_runs': '2019-06-01-preview',
            'runs': '2019-06-01-preview',
        }),
        # The order does make things different.
        # Please keep ResourceType.DATA_KEYVAULT_KEYS before ResourceType.DATA_KEYVAULT
        ResourceType.DATA_KEYVAULT_KEYS: None,
        ResourceType.DATA_KEYVAULT: '7.0',
        ResourceType.DATA_PRIVATE_KEYVAULT: '7.2',
        ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP: '7.2-preview',
        ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL: '7.2-preview',
        ResourceType.DATA_STORAGE: '2018-11-09',
        ResourceType.DATA_STORAGE_BLOB: '2021-06-08',
        ResourceType.DATA_STORAGE_FILEDATALAKE: '2021-06-08',
        ResourceType.DATA_STORAGE_FILESHARE: '2021-06-08',
        ResourceType.DATA_STORAGE_QUEUE: '2018-03-28',
        ResourceType.DATA_COSMOS_TABLE: '2017-04-17',
        ResourceType.MGMT_SERVICEBUS: '2021-06-01-preview',
        ResourceType.MGMT_EVENTHUB: '2022-01-01-preview',
        ResourceType.MGMT_MONITOR: SDKProfile('2019-06-01', {
            'action_groups': '2021-09-01',
            'activity_log_alerts': '2017-04-01',
            'activity_logs': '2015-04-01',
            'alert_rule_incidents': '2016-03-01',
            'alert_rules': '2016-03-01',
            'autoscale_settings': '2015-04-01',
            'baseline': '2018-09-01',
            'baselines': '2019-03-01',
            'diagnostic_settings': '2017-05-01-preview',
            'diagnostic_settings_category': '2017-05-01-preview',
            'event_categories': '2015-04-01',
            'guest_diagnostics_settings': '2018-06-01-preview',
            'guest_diagnostics_settings_association': '2018-06-01-preview',
            'log_profiles': '2016-03-01',
            'metric_alerts': '2018-03-01',
            'metric_alerts_status': '2018-03-01',
            'metric_baseline': '2018-09-01',
            'metric_definitions': '2018-01-01',
            'metric_namespaces': '2017-12-01-preview',
            'metrics': '2018-01-01',
            'operations': '2015-04-01',
            'scheduled_query_rules': '2018-04-16',
            'service_diagnostic_settings': '2016-09-01',
            'tenant_activity_logs': '2015-04-01',
            'vm_insights': '2018-11-27-preview',
            'private_link_resources': '2019-10-17-preview',
            'private_link_scoped_resources': '2019-10-17-preview',
            'private_link_scope_operation_status': '2019-10-17-preview',
            'private_link_scopes': '2019-10-17-preview',
            'private_endpoint_connections': '2019-10-17-preview',
            'subscription_diagnostic_settings': '2017-05-01-preview'
        }),
        ResourceType.MGMT_MSI: '2021-09-30-preview',
        ResourceType.MGMT_APPSERVICE: '2022-03-01',
        ResourceType.MGMT_IOTHUB: '2021-07-02',
        ResourceType.MGMT_IOTDPS: '2021-10-15',
        ResourceType.MGMT_IOTCENTRAL: '2021-11-01-preview',
        ResourceType.MGMT_ARO: '2022-04-01',
        ResourceType.MGMT_DATABOXEDGE: '2021-02-01-preview',
        ResourceType.MGMT_CUSTOMLOCATION: '2021-03-15-preview',
        ResourceType.MGMT_CONTAINERSERVICE: SDKProfile('2022-04-01', {
            'container_services': '2017-07-01',
            'open_shift_managed_clusters': '2019-09-30-preview'
        })
    },
    '2020-09-01-hybrid': {
        ResourceType.MGMT_STORAGE: '2019-06-01',
        ResourceType.MGMT_NETWORK: '2018-11-01',
        ResourceType.MGMT_COMPUTE: SDKProfile('2020-06-01', {
            'resource_skus': '2019-04-01',
            'disks': '2019-07-01',
            'disk_encryption_sets': '2019-07-01',
            'disk_accesses': '2020-05-01',
            'snapshots': '2019-07-01',
            'galleries': '2019-12-01',
            'gallery_images': '2019-12-01',
            'gallery_image_versions': '2019-12-01',
            'virtual_machine_scale_sets': '2020-06-01'
        }),
        ResourceType.MGMT_KEYVAULT: '2016-10-01',
        ResourceType.MGMT_MSI: '2018-11-30',
        ResourceType.MGMT_RESOURCE_FEATURES: '2021-07-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-12-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2019-10-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.MGMT_RESOURCE_TEMPLATESPECS: '2015-01-01',
        ResourceType.MGMT_RESOURCE_PRIVATELINKS: '2020-05-01',
        ResourceType.MGMT_NETWORK_DNS: '2016-04-01',
        ResourceType.MGMT_AUTHORIZATION: SDKProfile('2015-07-01', {
            'classic_administrators': '2015-06-01',
            'policy_assignments': '2016-12-01',
            'policy_definitions': '2016-12-01'
        }),
        # The order does make things different.
        # Please keep ResourceType.DATA_KEYVAULT_KEYS before ResourceType.DATA_KEYVAULT
        ResourceType.DATA_KEYVAULT_KEYS: None,
        ResourceType.DATA_KEYVAULT: '2016-10-01',
        ResourceType.DATA_STORAGE: '2018-11-09',
        ResourceType.DATA_STORAGE_BLOB: '2019-07-07',
        ResourceType.DATA_STORAGE_FILEDATALAKE: '2019-07-07',
        ResourceType.DATA_STORAGE_FILESHARE: '2019-07-07',
        ResourceType.DATA_STORAGE_QUEUE: '2019-07-07',
        ResourceType.DATA_COSMOS_TABLE: '2017-04-17',
        ResourceType.MGMT_APPSERVICE: '2018-02-01',
        ResourceType.MGMT_EVENTHUB: '2022-01-01-preview',
        ResourceType.MGMT_SERVICEBUS: '2021-06-01-preview',
        ResourceType.MGMT_IOTHUB: '2019-07-01-preview',
        ResourceType.MGMT_DATABOXEDGE: '2019-08-01',
        ResourceType.MGMT_CONTAINERREGISTRY: '2019-05-01',
        ResourceType.MGMT_CONTAINERSERVICE: SDKProfile('2020-11-01', {
            'container_services': '2017-07-01',
            'open_shift_managed_clusters': '2019-09-30-preview'
        })
    },
    '2019-03-01-hybrid': {
        ResourceType.MGMT_STORAGE: '2017-10-01',
        ResourceType.MGMT_NETWORK: '2017-10-01',
        ResourceType.MGMT_COMPUTE: SDKProfile('2017-12-01', {
            'resource_skus': '2017-09-01',
            'disks': '2017-03-30',
            'snapshots': '2017-03-30'
        }),
        ResourceType.MGMT_MSI: '2018-11-30',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-12-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2018-05-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.MGMT_RESOURCE_TEMPLATESPECS: '2015-01-01',
        ResourceType.MGMT_RESOURCE_PRIVATELINKS: '2020-05-01',
        ResourceType.MGMT_NETWORK_DNS: '2016-04-01',
        ResourceType.MGMT_KEYVAULT: '2016-10-01',
        ResourceType.MGMT_AUTHORIZATION: SDKProfile('2015-07-01', {
            'classic_administrators': '2015-06-01',
            'policy_assignments': '2016-12-01',
            'policy_definitions': '2016-12-01'
        }),
        # The order does make things different.
        # Please keep ResourceType.DATA_KEYVAULT_KEYS before ResourceType.DATA_KEYVAULT
        ResourceType.DATA_KEYVAULT_KEYS: None,
        ResourceType.DATA_KEYVAULT: '2016-10-01',
        ResourceType.DATA_STORAGE: '2017-11-09',
        ResourceType.DATA_STORAGE_BLOB: '2017-11-09',
        ResourceType.DATA_STORAGE_FILEDATALAKE: '2017-11-09',
        ResourceType.DATA_STORAGE_FILESHARE: '2017-11-09',
        ResourceType.DATA_STORAGE_QUEUE: '2017-11-09',
        ResourceType.DATA_COSMOS_TABLE: '2017-04-17',
        # Full MultiAPI support is not done in AppService, the line below is merely
        # to have commands show up in the hybrid profile which happens to have the latest
        # API versions
        ResourceType.MGMT_APPSERVICE: '2018-02-01',
        ResourceType.MGMT_EVENTHUB: '2022-01-01-preview',
        ResourceType.MGMT_SERVICEBUS: '2021-06-01-preview',
        ResourceType.MGMT_IOTHUB: '2019-03-22',
        ResourceType.MGMT_DATABOXEDGE: '2019-08-01'
    },
    '2018-03-01-hybrid': {
        ResourceType.MGMT_STORAGE: '2016-01-01',
        ResourceType.MGMT_NETWORK: '2017-10-01',
        ResourceType.MGMT_COMPUTE: SDKProfile('2017-03-30'),
        ResourceType.MGMT_MSI: '2018-11-30',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-12-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2018-02-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.MGMT_RESOURCE_TEMPLATESPECS: '2015-01-01',
        ResourceType.MGMT_RESOURCE_PRIVATELINKS: '2020-05-01',
        ResourceType.MGMT_NETWORK_DNS: '2016-04-01',
        ResourceType.MGMT_KEYVAULT: '2016-10-01',
        ResourceType.MGMT_AUTHORIZATION: SDKProfile('2015-07-01', {
            'classic_administrators': '2015-06-01'
        }),
        # The order does make things different.
        # Please keep ResourceType.DATA_KEYVAULT_KEYS before ResourceType.DATA_KEYVAULT
        ResourceType.DATA_KEYVAULT_KEYS: None,
        ResourceType.DATA_KEYVAULT: '2016-10-01',
        ResourceType.DATA_STORAGE: '2017-04-17',
        ResourceType.DATA_STORAGE_BLOB: '2017-04-17',
        ResourceType.DATA_STORAGE_FILEDATALAKE: '2017-04-17',
        ResourceType.DATA_STORAGE_FILESHARE: '2017-04-17',
        ResourceType.DATA_STORAGE_QUEUE: '2017-04-17',
        ResourceType.DATA_COSMOS_TABLE: '2017-04-17'
    },
    '2017-03-09-profile': {
        ResourceType.MGMT_STORAGE: '2016-01-01',
        ResourceType.MGMT_NETWORK: '2015-06-15',
        ResourceType.MGMT_COMPUTE: SDKProfile('2016-03-30'),
        ResourceType.MGMT_MSI: '2018-11-30',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2015-01-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2015-10-01-preview',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2016-02-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.MGMT_RESOURCE_PRIVATELINKS: '2020-05-01',
        ResourceType.MGMT_RESOURCE_TEMPLATESPECS: '2015-01-01',
        ResourceType.MGMT_NETWORK_DNS: '2016-04-01',
        ResourceType.MGMT_KEYVAULT: '2016-10-01',
        ResourceType.MGMT_AUTHORIZATION: SDKProfile('2015-07-01', {
            'classic_administrators': '2015-06-01'
        }),
        # The order does make things different.
        # Please keep ResourceType.DATA_KEYVAULT_KEYS before ResourceType.DATA_KEYVAULT
        ResourceType.DATA_KEYVAULT_KEYS: None,
        ResourceType.DATA_KEYVAULT: '2016-10-01',
        ResourceType.DATA_STORAGE: '2015-04-05',
        ResourceType.DATA_STORAGE_BLOB: '2015-04-05',
        ResourceType.DATA_STORAGE_FILEDATALAKE: '2015-04-05',
        ResourceType.DATA_STORAGE_FILESHARE: '2015-04-05',
        ResourceType.DATA_STORAGE_QUEUE: '2015-04-05'
    }
}


# We should avoid using ad hoc API versions,
# use the version in a profile as much as possible.
AD_HOC_API_VERSIONS = {
    ResourceType.MGMT_NETWORK: {
        'vm_default_target_network': '2018-01-01',
        'nw_connection_monitor': '2019-06-01',
        'container_network': '2018-08-01',
        'appservice_network': '2020-04-01',
        'appservice_ensure_subnet': '2019-02-01'
    }
}


class _ApiVersions:  # pylint: disable=too-few-public-methods
    def __init__(self, client_type, sdk_profile, post_process):
        self._client_type = client_type
        self._sdk_profile = sdk_profile
        self._post_process = post_process
        self._operations_groups_value = None
        self._resolved = False

    def _resolve(self):
        if self._resolved:
            return

        self._operations_groups_value = {}
        for operation_group_name, operation_type in self._client_type.__dict__.items():
            if not isinstance(operation_type, property):
                continue

            value_to_save = self._sdk_profile.profile.get(
                operation_group_name,
                self._sdk_profile.default_api_version
            )
            self._operations_groups_value[operation_group_name] = self._post_process(value_to_save)
        self._resolved = True

    def __getattr__(self, item):
        try:
            self._resolve()
            return self._operations_groups_value[item]
        except KeyError:
            raise AttributeError('Attribute {} does not exist.'.format(item))


def _get_api_version_tuple(resource_type, sdk_profile, post_process=lambda x: x):
    """Return a _ApiVersion instance where key are operation group and value are api version."""
    return _ApiVersions(client_type=get_client_class(resource_type),
                        sdk_profile=sdk_profile,
                        post_process=post_process)


def get_api_version(api_profile, resource_type, as_sdk_profile=False):
    """Get the API version of a resource type given an API profile.

    :param api_profile: The name of the API profile.
    :type api_profile: str.
    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :returns:  str -- the API version.
    :raises: APIVersionException
    """
    try:
        api_version = AZURE_API_PROFILES[api_profile][resource_type]
        if as_sdk_profile:
            return api_version  # Could be SDKProfile or string
        if isinstance(api_version, SDKProfile):
            api_version = _get_api_version_tuple(resource_type, api_version)
        return api_version
    except KeyError:
        raise APIVersionException(resource_type, api_profile)


@total_ordering
class _SemVerAPIFormat:
    """Basic semver x.y.z API format.
    Supports x, or x.y, or x.y.z
    """

    def __init__(self, api_version_str):
        try:
            parts = api_version_str.split('.')
            parts += [0, 0]  # At worst never read, at best minor/patch
            self.major = int(parts[0])
            self.minor = int(parts[1])
            self.patch = int(parts[2])
        except (ValueError, TypeError):
            raise ValueError('The API version {} is not in a '
                             'semver format'.format(api_version_str))

    def __eq__(self, other):
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other):
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


@total_ordering  # pylint: disable=too-few-public-methods
class _DateAPIFormat:
    """ Class to support comparisons for API versions in
        YYYY-MM-DD, YYYY-MM-DD-preview, YYYY-MM-DD-profile, YYYY-MM-DD-profile-preview
        or any string that starts with YYYY-MM-DD format. A special case is made for 'latest'.
    """

    def __init__(self, api_version_str):
        try:
            self.latest = self.preview = False
            self.yyyy = self.mm = self.dd = None
            if api_version_str == 'latest':
                self.latest = True
            else:
                if 'preview' in api_version_str:
                    self.preview = True
                parts = api_version_str.split('-')
                self.yyyy = int(parts[0])
                self.mm = int(parts[1])
                self.dd = int(parts[2])
        except (ValueError, TypeError):
            raise ValueError('The API version {} is not in a '
                             'supported format'.format(api_version_str))

    def __eq__(self, other):
        return self.latest == other.latest and self.yyyy == other.yyyy and self.mm == other.mm and \
            self.dd == other.dd and self.preview == other.preview

    def __lt__(self, other):  # pylint: disable=too-many-return-statements
        if self.latest or other.latest:
            if not self.latest and other.latest:
                return True
            if self.latest and not other.latest:
                return False
            return False
        if self.yyyy < other.yyyy:
            return True
        if self.yyyy == other.yyyy:
            if self.mm < other.mm:
                return True
            if self.mm == other.mm:
                if self.dd < other.dd:
                    return True
                if self.dd == other.dd:
                    if self.preview and not other.preview:
                        return True
        return False


def _parse_api_version(api_version):
    """Will try to parse it as a date, and if not working
    as semver, and if still not working raise.
    """
    try:
        return _DateAPIFormat(api_version)
    except ValueError:
        return _SemVerAPIFormat(api_version)


def _cross_api_format_less_than(api_version, other):
    """LT strategy that supports if types are different.

    For now, let's assume that any Semver is higher than any DateAPI
    This fits KeyVault, if later we have a counter-example we'll update
    """
    api_version = _parse_api_version(api_version)
    other = _parse_api_version(other)

    if type(api_version) is type(other):
        return api_version < other
    return isinstance(api_version, _DateAPIFormat) and isinstance(other, _SemVerAPIFormat)


def _validate_api_version(api_version_str, min_api=None, max_api=None):
    """Validate if api_version is inside the interval min_api/max_api.
    """
    if min_api and _cross_api_format_less_than(api_version_str, min_api):
        return False
    if max_api and _cross_api_format_less_than(max_api, api_version_str):
        return False
    return True


def supported_api_version(api_profile, resource_type, min_api=None, max_api=None, operation_group=None):
    """
    Returns True if current API version for the resource type satisfies min/max range.
    To compare profile versions, set resource type to None.
    Can return a tuple<operation_group, bool> if the resource_type supports SDKProfile.
    note: Currently supports YYYY-MM-DD, YYYY-MM-DD-preview, YYYY-MM-DD-profile
    or YYYY-MM-DD-profile-preview  formatted strings.
    """
    if not isinstance(resource_type, (ResourceType, CustomResourceType)) and resource_type != PROFILE_TYPE:
        raise ValueError("'resource_type' is required.")
    if min_api is None and max_api is None:
        raise ValueError('At least a min or max version must be specified')
    api_version_obj = get_api_version(api_profile, resource_type, as_sdk_profile=True) \
        if isinstance(resource_type, (ResourceType, CustomResourceType)) else api_profile
    if isinstance(api_version_obj, SDKProfile):
        api_version_obj = api_version_obj.profile.get(operation_group or '', api_version_obj.default_api_version)
    return _validate_api_version(api_version_obj, min_api, max_api)


def supported_resource_type(api_profile, resource_type):
    if api_profile == 'latest' or resource_type is None:
        return True
    try:
        return bool(AZURE_API_PROFILES[api_profile][resource_type])
    except KeyError:
        return False


def _get_attr(sdk_path, mod_attr_path, checked=True):
    try:
        attr_mod, attr_path = mod_attr_path.split('#') \
            if '#' in mod_attr_path else (mod_attr_path, '')
        full_mod_path = '{}.{}'.format(sdk_path, attr_mod) if attr_mod else sdk_path
        op = import_module(full_mod_path)
        if attr_path:
            # Only load attributes if needed
            for part in attr_path.split('.'):
                op = getattr(op, part)
        return op
    except (ImportError, AttributeError) as ex:
        import traceback
        logger.debug(traceback.format_exc())
        if checked:
            return None
        raise ex


def get_client_class(resource_type):
    return _get_attr(resource_type.import_prefix, '#' + resource_type.client_name)


def get_versioned_sdk_path(api_profile, resource_type, operation_group=None):
    """ Patch the unversioned sdk path to include the appropriate API version for the
        resource type in question.
        e.g. Converts azure.mgmt.storage.operations.storage_accounts_operations to
                      azure.mgmt.storage.v2016_12_01.operations.storage_accounts_operations
                      azure.keyvault.v7_0.models.KeyVault
    """
    api_version = get_api_version(api_profile, resource_type)
    if api_version is None:
        return resource_type.import_prefix
    if isinstance(api_version, _ApiVersions):
        if operation_group is None:
            raise ValueError("operation_group is required for resource type '{}'".format(resource_type))
        api_version = getattr(api_version, operation_group)
    return '{}.v{}'.format(resource_type.import_prefix, api_version.replace('-', '_').replace('.', '_'))


def get_versioned_sdk(api_profile, resource_type, *attr_args, **kwargs):
    checked = kwargs.get('checked', True)
    sub_mod_prefix = kwargs.get('mod', None)
    operation_group = kwargs.get('operation_group', None)
    sdk_path = get_versioned_sdk_path(api_profile, resource_type, operation_group)
    if not attr_args:
        # No attributes to load. Return the versioned sdk
        return import_module(sdk_path)
    results = []
    for mod_attr_path in attr_args:
        if sub_mod_prefix and '#' not in mod_attr_path:
            mod_attr_path = '{}#{}'.format(sub_mod_prefix, mod_attr_path)
        loaded_obj = _get_attr(sdk_path, mod_attr_path, checked)
        results.append(loaded_obj)
    return results[0] if len(results) == 1 else results
