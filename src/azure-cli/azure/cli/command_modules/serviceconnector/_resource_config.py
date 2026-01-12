# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from .action import (
    AddSecretAuthInfo,
    AddSecretAuthInfoAuto,
    AddUserAssignedIdentityAuthInfo,
    AddSystemAssignedIdentityAuthInfo,
    AddServicePrincipalAuthInfo,
    AddUserAccountAuthInfo,
    AddWorkloadIdentityAuthInfo
)
# pylint: disable=line-too-long


# The dict defines the resource types, including both source resources and target resources.
# The enum value will be used in command name
class RESOURCE(Enum):
    Local = 'connection'
    WebApp = 'webapp'
    FunctionApp = 'functionapp'
    # `az spring-cloud` migrated to `az spring`
    SpringCloud = 'spring'
    SpringCloudDeprecated = 'spring-cloud'
    KubernetesCluster = 'aks'
    ContainerApp = 'containerapp'
    CosmosCassandra = 'cosmos-cassandra'
    CosmosGremlin = 'cosmos-gremlin'
    CosmosMongo = 'cosmos-mongo'
    CosmosSql = 'cosmos-sql'
    CosmosTable = 'cosmos-table'
    StorageBlob = 'storage-blob'
    StorageQueue = 'storage-queue'
    StorageFile = 'storage-file'
    StorageTable = 'storage-table'
    Postgres = 'postgres'
    PostgresFlexible = 'postgres-flexible'
    Mysql = 'mysql'
    MysqlFlexible = 'mysql-flexible'
    Sql = 'sql'
    Redis = 'redis'
    RedisEnterprise = 'redis-enterprise'
    KeyVault = 'keyvault'
    EventHub = 'eventhub'
    AppConfig = 'appconfig'
    ServiceBus = 'servicebus'
    SignalR = 'signalr'
    WebPubSub = 'webpubsub'
    ConfluentKafka = 'confluent-cloud'
    FabricSql = 'fabric-sql'
    AppInsights = 'app-insights'
    CognitiveServices = 'cognitiveservices'
    NeonPostgres = 'neon-postgres'
    MongoDbAtlas = 'mongodb-atlas'

    @classmethod
    def value_of(cls, value):
        for _, v in cls.__members__.items():
            if v.value == value:
                return v

        raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")


# The dict defines the auth types
class AUTH_TYPE(Enum):
    Secret = 'secret'
    SecretAuto = 'secret(auto)'  # secret which don't need user provide name & password
    SystemIdentity = 'system-managed-identity'
    UserIdentity = 'user-managed-identity'
    WorkloadIdentity = 'workload-identity'
    ServicePrincipalSecret = 'service-principal'
    UserAccount = 'user-account'
    Null = 'null'


# The dict defines the client types
class CLIENT_TYPE(Enum):
    Dotnet = 'dotnet'
    DotnetConnectionString = 'dotnet-connectionString'
    DotnetInternal = 'dotnet-internal'
    Java = 'java'
    Nodejs = 'nodejs'
    Python = 'python'
    Go = 'go'
    Php = 'php'
    Ruby = 'ruby'
    SpringBoot = 'springBoot'
    KafkaSpringBoot = 'kafka-springBoot'
    Django = 'django'
    Blank = 'none'


# The source resources released as CLI extensions
SOURCE_RESOURCES_IN_EXTENSION = [RESOURCE.SpringCloud, RESOURCE.SpringCloudDeprecated]

# The source resources using user token
SOURCE_RESOURCES_USERTOKEN = [RESOURCE.KubernetesCluster]

# The target resources using user token
TARGET_RESOURCES_USERTOKEN = [RESOURCE.PostgresFlexible, RESOURCE.MysqlFlexible, RESOURCE.KeyVault]

# The target resources could be set to connection string
TARGET_RESOURCES_CONNECTION_STRING = [RESOURCE.Sql, RESOURCE.Mysql, RESOURCE.MysqlFlexible, RESOURCE.Postgres, RESOURCE.PostgresFlexible]

# The target resources to be deprecated
TARGET_RESOURCES_DEPRECATED = [RESOURCE.Mysql, RESOURCE.Postgres]

# The dict defines the resource id pattern of source resources.
SOURCE_RESOURCES = {
    RESOURCE.WebApp: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.Web/sites/{site}',
    RESOURCE.FunctionApp: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.Web/sites/{site}',
    RESOURCE.SpringCloud: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.AppPlatform/Spring/{spring}/apps/{app}',
    RESOURCE.SpringCloudDeprecated: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.AppPlatform/Spring/{spring}/apps/{app}/deployments/{deployment}',
    RESOURCE.KubernetesCluster: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.ContainerService/managedClusters/{cluster}',
    RESOURCE.ContainerApp: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.App/containerApps/{app}'
}

WEB_APP_SLOT_RESOURCE = '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.Web/sites/{site}/slots/{slot}'
SPRING_APP_DEPLOYMENT_RESOURCE = '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.AppPlatform/Spring/{spring}/apps/{app}/deployments/{deployment}'
LOCAL_CONNECTION_RESOURCE = '/subscriptions/{subscriptionId}/resourceGroups/{resource_group}/providers/Microsoft.ServiceLinker/locations/{location}/connectors/{connection_name}'

# The dict defines the resource id pattern of target resources.
TARGET_RESOURCES = {
    RESOURCE.Postgres: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBforPostgreSQL/servers/{server}/databases/{database}',
    RESOURCE.PostgresFlexible: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server}/databases/{database}',
    RESOURCE.MysqlFlexible: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBforMySQL/flexibleServers/{server}/databases/{database}',
    RESOURCE.Mysql: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBForMySQL/servers/{server}/databases/{database}',
    RESOURCE.Sql: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Sql/servers/{server}/databases/{database}',
    RESOURCE.Redis: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Cache/redis/{server}/databases/{database}',
    RESOURCE.RedisEnterprise: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Cache/redisEnterprise/{server}/databases/{database}',

    RESOURCE.CosmosCassandra: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/cassandraKeyspaces/{key_space}',
    RESOURCE.CosmosGremlin: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/gremlinDatabases/{database}/graphs/{graph}',
    RESOURCE.CosmosMongo: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/mongodbDatabases/{database}',
    RESOURCE.CosmosSql: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/sqlDatabases/{database}',
    RESOURCE.CosmosTable: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/tables/{table}',

    RESOURCE.StorageBlob: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/blobServices/default',
    RESOURCE.StorageQueue: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/queueServices/default',
    RESOURCE.StorageFile: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/fileServices/default',
    RESOURCE.StorageTable: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/tableServices/default',

    RESOURCE.KeyVault: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.KeyVault/vaults/{vault}',
    RESOURCE.AppConfig: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.AppConfiguration/configurationStores/{config_store}',
    RESOURCE.EventHub: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.EventHub/namespaces/{namespace}',
    RESOURCE.ServiceBus: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.ServiceBus/namespaces/{namespace}',
    RESOURCE.SignalR: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.SignalRService/SignalR/{signalr}',
    RESOURCE.WebPubSub: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.SignalRService/WebPubSub/{webpubsub}',
    RESOURCE.ConfluentKafka: '#',  # special target resource, no arm resource id
    RESOURCE.AppInsights: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/microsoft.insights/components/{appinsights}',

    RESOURCE.CognitiveServices: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.CognitiveServices/accounts/{account}',

    RESOURCE.ContainerApp: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.App/containerApps/{target_app_name}',

    RESOURCE.FabricSql: 'https://api.fabric.microsoft.com/v1/workspaces/{fabric_workspace_uuid}/SqlDatabases/{fabric_sql_db_uuid}',
    RESOURCE.NeonPostgres: '/subscriptions/aaaabbbb-0000-cccc-1111-dddd2222eeee/resourceGroups/testrg/providers/Neon.Postgres/organizations/neontest',
    RESOURCE.MongoDbAtlas: '/subscriptions/aaaabbbb-0000-cccc-1111-dddd2222eeee/resourceGroups/{target_resource_group}/providers/MongoDB.Atlas/organizations/{server}'

}


LOCAL_CONNECTION_PARAMS = {
    'connection_name': {
        'options': ['--connection'],
        'type': str,
        'help': 'Name of the connection.',
    },
    'resource_group_name': {
        'options': ['--resource-group', '-g'],
        'help': 'The resource group which contains the connection.'
    },
    'location': {
    }
}
# The dict defines the parameters used to position the source resources.
# The parmaters should include all variables defined in source resource id expect
# for 'subscription', which will be dealt by CLI core as a default parameter.
SOURCE_RESOURCES_PARAMS = {
    RESOURCE.WebApp: {
        'source_resource_group': {
            'configured_default': 'group',
            'options': ['--resource-group', '-g'],
            'help': 'The resource group which contains the webapp',
            'placeholder': 'WebAppRG'
        },
        'site': {
            'configured_default': 'web',
            'options': ['--name', '-n'],
            'help': 'Name of the webapp',
            'placeholder': 'MyWebApp'
        }
    },
    RESOURCE.FunctionApp: {
        'source_resource_group': {
            'configured_default': 'group',
            'options': ['--resource-group', '-g'],
            'help': 'The resource group which contains the function app',
            'placeholder': 'FuncAppRG'
        },
        'site': {
            'configured_default': 'web',
            'options': ['--name', '-n'],
            'help': 'Name of the function app',
            'placeholder': 'MyFunctionApp'
        }
    },
    RESOURCE.SpringCloud: {
        'source_resource_group': {
            'options': ['--resource-group', '-g'],
            'help': 'The resource group which contains app in the Azure Spring Apps',
            'placeholder': 'SpringCloudRG'
        },
        'spring': {
            'options': ['--service'],
            'help': 'Name of the the Azure Spring Apps resource',
            'placeholder': 'MySpringService'
        },
        'app': {
            'options': ['--app'],
            'help': 'Name of the app in the Azure Spring Apps',
            'placeholder': 'MyApp'
        },
    },
    RESOURCE.SpringCloudDeprecated: {
        'source_resource_group': {
            'options': ['--resource-group', '-g'],
            'help': 'The resource group which contains the spring-cloud',
            'placeholder': 'SpringCloudRG'
        },
        'spring': {
            'options': ['--service'],
            'help': 'Name of the spring-cloud service',
            'placeholder': 'MySpringService'
        },
        'app': {
            'options': ['--app'],
            'help': 'Name of the spring-cloud app',
            'placeholder': 'MyApp'
        },
        'deployment': {
            'options': ['--deployment'],
            'help': 'The deployment name of the app',
            'placeholder': 'MyDeployment',
        }
    },
    RESOURCE.KubernetesCluster: {
        'source_resource_group': {
            'options': ['--resource-group', '-g'],
            'help': 'The resource group which contains the managed cluster',
            'placeholder': 'ClusterRG'
        },
        'cluster': {
            'options': ['--name', '-n'],
            'help': 'Name of the managed cluster',
            'placeholder': 'MyCluster'
        }
    },
    RESOURCE.ContainerApp: {
        'source_resource_group': {
            'options': ['--resource-group', '-g'],
            'help': 'The resource group which contains the container app',
            'placeholder': 'ContainerAppRG'
        },
        'app': {
            'options': ['--name', '-n'],
            'help': 'Name of the container app',
            'placeholder': 'MyContainerApp'
        }
    }
}


# The dict defines the required parameters used in the source resources for creation.
SOURCE_RESOURCES_CREATE_PARAMS = {
    RESOURCE.ContainerApp: {
        'scope': {
            'options': ['--container', '-c'],
            'help': 'The container where the connection information will be saved (as environment variables).',
            'placeholder': 'MyContainer'
        },
    },
}

# The dict defines the optional parameters used in the source resources for WebApp creation.
SOURCE_RESOURCES_OPTIONAL_PARAMS = {
    RESOURCE.WebApp: {
        'slot': {
            'options': ['--slot'],
            'help': 'The name of the slot. Default to the production slot if not specified.',
            'placeholder': 'WebAppSlot'
        },
    },
    RESOURCE.SpringCloud: {
        'deployment': {
            'options': ['--deployment'],
            'help': 'The deployment name of the app.',
            'placeholder': 'MyDeployment',
        },
    }
}

# The dict defines the parameters used to position the target resources.
# The parmaters should include all variables defined in target resource id expect
# for 'subscription', which will be dealt by CLI core as a default parameter.
TARGET_RESOURCES_PARAMS = {
    RESOURCE.Postgres: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the postgres service',
            'placeholder': 'PostgresRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of postgres server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of postgres database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.PostgresFlexible: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the flexible postgres service',
            'placeholder': 'PostgresRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of postgres flexible server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of postgres flexible database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.MysqlFlexible: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the mysql flexible server',
            'placeholder': 'MysqlRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of the mysql flexible server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the mysql flexible database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.Mysql: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the mysql server',
            'placeholder': 'MysqlRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of the mysql server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the mysql database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.Sql: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the sql server',
            'placeholder': 'SqlRG'
        },
        'server': {
            'configured_default': 'sql-server',
            'options': ['--server'],
            'help': 'Name of the sql server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the sql database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.Redis: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the redis server',
            'placeholder': 'RedisRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of the redis server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the redis database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.RedisEnterprise: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the redis server',
            'placeholder': 'RedisRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of the redis enterprise server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the redis enterprise database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.CosmosCassandra: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the cosmos database account',
            'placeholder': 'CosmosRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the cosmos database account',
            'placeholder': 'MyAccount'
        },
        'key_space': {
            'options': ['--key-space'],
            'help': 'Name of the keyspace',
            'placeholder': 'MyKeySpace'
        }
    },
    RESOURCE.CosmosGremlin: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the cosmos database account',
            'placeholder': 'CosmosRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the cosmos database account',
            'placeholder': 'MyAccount'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the database',
            'placeholder': 'MyDB'
        },
        'graph': {
            'options': ['--graph'],
            'help': 'Name of the graph',
            'placeholder': 'MyGraph'
        }
    },
    RESOURCE.CosmosMongo: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the cosmos database account',
            'placeholder': 'CosmosRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the cosmos database account',
            'placeholder': 'MyAccount'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.CosmosSql: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the cosmos database account',
            'placeholder': 'CosmosRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the cosmos database account',
            'placeholder': 'MyAccount'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.CosmosTable: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the cosmos database account',
            'placeholder': 'CosmosRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the cosmos database account',
            'placeholder': 'MyAccount'
        },
        'table': {
            'options': ['--table'],
            'help': 'Name of the table',
            'placeholder': 'MyTable'
        }
    },
    RESOURCE.StorageBlob: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the storage account',
            'placeholder': 'StorageRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the storage account',
            'placeholder': 'MyAccount'
        },
    },
    RESOURCE.StorageQueue: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the storage account',
            'placeholder': 'StorageRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the storage account',
            'placeholder': 'MyAccount'
        },
    },
    RESOURCE.StorageFile: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the storage account',
            'placeholder': 'StorageRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the storage account',
            'placeholder': 'MyAccount'
        },
    },
    RESOURCE.StorageTable: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the storage account',
            'placeholder': 'StorageRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the storage account',
            'placeholder': 'MyAccount'
        },
    },
    RESOURCE.KeyVault: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the keyvault',
            'placeholder': 'KeyvaultRG'
        },
        'vault': {
            'options': ['--vault'],
            'help': 'Name of the keyvault',
            'placeholder': 'MyVault'
        }
    },
    RESOURCE.AppConfig: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the app configuration',
            'placeholder': 'AppconfigRG'
        },
        'config_store': {
            'options': ['--app-config'],
            'help': 'Name of the app configuration',
            'placeholder': 'MyConfigStore'
        }
    },
    RESOURCE.EventHub: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the eventhub',
            'placeholder': 'EventhubRG'
        },
        'namespace': {
            'options': ['--namespace'],
            'help': 'Name of the eventhub namespace',
            'placeholder': 'MyNamespace'
        }
    },
    RESOURCE.ServiceBus: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the servicebus',
            'placeholder': 'ServicebusRG'
        },
        'namespace': {
            'options': ['--namespace'],
            'help': 'Name of the servicebus namespace',
            'placeholder': 'MyNamespace'
        }
    },
    RESOURCE.SignalR: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the signalr',
            'placeholder': 'SignalrRG'
        },
        'signalr': {
            'options': ['--signalr'],
            'help': 'Name of the signalr service',
            'placeholder': 'MySignalR'
        }
    },
    RESOURCE.WebPubSub: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the webpubsub',
            'placeholder': 'WebpubsubRG'
        },
        'webpubsub': {
            'options': ['--webpubsub'],
            'help': 'Name of the webpubsub service',
            'placeholder': 'MyWebPubSub'
        }
    },
    RESOURCE.AppInsights: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the app insights',
            'placeholder': 'AppInsightsRG'
        },
        'appinsights': {
            'options': ['--app-insights'],
            'help': 'Name of the app insights',
            'placeholder': 'MyAppInsights'
        }
    },
    RESOURCE.CognitiveServices: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the cognitive services',
            'placeholder': 'CognitiveServicesRG'
        },
        'account': {
            'options': ['--account'],
            'help': 'Name of the cognitive services account',
            'placeholder': 'MyAccount'
        }
    },
    RESOURCE.ContainerApp: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the target container app',
            'placeholder': 'TargetContainerAppRG'
        },
        'target_app_name': {
            'options': ['--target-app-name'],
            'help': 'Name of the target container app',
            'placeholder': 'MyTargetContainerApp'
        }
    },
    RESOURCE.FabricSql: {
        'fabric_workspace_uuid': {
            'options': ['--fabric-workspace-uuid'],
            'help': 'UUID of Fabric workspace which contains the target SQL database',
            'placeholder': 'TargetFabricWorkspaceUUID'
        },
        'fabric_sql_db_uuid': {
            'options': ['--fabric-sql-db-uuid'],
            'help': 'UUID of the target Fabric SQL database',
            'placeholder': 'TargetFabricSQLDatabaseUUID'
        },
    },
    RESOURCE.NeonPostgres: {
        'server': {
            'configured_default': 'sql-server',
            'options': ['--server'],
            'help': 'Name of the sql server',
            'placeholder': 'MyServer'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of the sql database',
            'placeholder': 'MyDB'
        }
    },
    RESOURCE.MongoDbAtlas: {
        'target_resource_group': {
            'options': ['--target-resource-group', '--tg'],
            'help': 'The resource group which contains the MongoDB Atlas',
            'placeholder': 'MongoDBAtlasRG'
        },
        'server': {
            'options': ['--server'],
            'help': 'Name of the MongoDB Atlas server',
            'placeholder': 'MongoDBAtlasServer'
        }
    }
}


# The dict defines the targets which supports service endpoint
TARGET_SUPPORT_SERVICE_ENDPOINT = [
    RESOURCE.Postgres,
    RESOURCE.Mysql,
    RESOURCE.Sql,
    RESOURCE.StorageBlob,
    RESOURCE.StorageQueue,
    RESOURCE.StorageFile,
    RESOURCE.StorageTable,
    RESOURCE.KeyVault,
    RESOURCE.CosmosSql,
    RESOURCE.CosmosCassandra,
    RESOURCE.CosmosGremlin,
    RESOURCE.CosmosMongo,
    RESOURCE.CosmosTable,
    RESOURCE.ServiceBus,
    RESOURCE.EventHub,
]


TARGET_SUPPORT_PRIVATE_ENDPOINT = [
    RESOURCE.AppConfig,
    RESOURCE.CosmosSql,
    RESOURCE.CosmosCassandra,
    RESOURCE.CosmosGremlin,
    RESOURCE.CosmosMongo,
    RESOURCE.CosmosTable,
    RESOURCE.Redis,
    RESOURCE.Postgres,
    RESOURCE.Mysql,
    RESOURCE.MysqlFlexible,
    RESOURCE.EventHub,
    RESOURCE.KeyVault,
    RESOURCE.SignalR,
    RESOURCE.WebPubSub,
    RESOURCE.Sql,
    RESOURCE.StorageBlob,
    RESOURCE.StorageQueue,
    RESOURCE.StorageFile,
    RESOURCE.StorageTable,
    RESOURCE.ServiceBus,
]


# The dict defines the parameters used to provide auth info
AUTH_TYPE_PARAMS = {
    AUTH_TYPE.Secret: {
        'secret_auth_info': {
            'options': ['--secret'],
            'help': 'The secret auth info',
            'action': AddSecretAuthInfo
        }
    },
    AUTH_TYPE.SecretAuto: {
        'secret_auth_info_auto': {
            'options': ['--secret'],
            'help': 'The secret auth info',
            'action': AddSecretAuthInfoAuto
        }
    },
    AUTH_TYPE.SystemIdentity: {
        'system_identity_auth_info': {
            'options': ['--system-identity'],
            'help': 'The system assigned identity auth info',
            'action': AddSystemAssignedIdentityAuthInfo
        }
    },
    AUTH_TYPE.UserIdentity: {
        'user_identity_auth_info': {
            'options': ['--user-identity'],
            'help': 'The user assigned identity auth info',
            'action': AddUserAssignedIdentityAuthInfo
        }
    },
    # used only as argument, same action as user identity
    AUTH_TYPE.WorkloadIdentity: {
        'workload_identity_auth_info': {
            'options': ['--workload-identity'],
            'help': 'The workload identity auth info',
            'action': AddWorkloadIdentityAuthInfo
        }
    },
    AUTH_TYPE.ServicePrincipalSecret: {
        'service_principal_auth_info_secret': {
            'options': ['--service-principal'],
            'help': 'The service principal auth info',
            'action': AddServicePrincipalAuthInfo
        }
    },
    AUTH_TYPE.UserAccount: {
        'user_account_auth_info': {
            'options': ['--user-account'],
            'help': 'The local user account auth info',
            'action': AddUserAccountAuthInfo
        }
    }
}


# The dict defines the supported auth type of each source-target resource pair
# The first one will be used as the default auth type
SUPPORTED_AUTH_TYPE = {
    RESOURCE.Local: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret, AUTH_TYPE.UserAccount],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.UserAccount],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.UserAccount],
        RESOURCE.Sql: [AUTH_TYPE.Secret, AUTH_TYPE.UserAccount],
        RESOURCE.Redis: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.RedisEnterprise: [AUTH_TYPE.SecretAuto],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.KeyVault: [AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.SignalR: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.WebPubSub: [AUTH_TYPE.SecretAuto, AUTH_TYPE.UserAccount, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ConfluentKafka: [AUTH_TYPE.Secret],
        RESOURCE.AppInsights: [AUTH_TYPE.SecretAuto]
    },
    RESOURCE.WebApp: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Sql: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Redis: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.RedisEnterprise: [AUTH_TYPE.SecretAuto],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.KeyVault: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.SignalR: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.WebPubSub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ConfluentKafka: [AUTH_TYPE.Secret],
        RESOURCE.FabricSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity],
        RESOURCE.AppInsights: [AUTH_TYPE.SecretAuto],

        RESOURCE.CognitiveServices: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.NeonPostgres: [AUTH_TYPE.Secret],
        RESOURCE.MongoDbAtlas: [AUTH_TYPE.Secret]
    },
    RESOURCE.SpringCloud: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Sql: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Redis: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.RedisEnterprise: [AUTH_TYPE.SecretAuto],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.KeyVault: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.SignalR: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.WebPubSub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ConfluentKafka: [AUTH_TYPE.Secret],
        RESOURCE.FabricSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity],
        RESOURCE.AppInsights: [AUTH_TYPE.SecretAuto],

        RESOURCE.CognitiveServices: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.NeonPostgres: [AUTH_TYPE.Secret],
        RESOURCE.MongoDbAtlas: [AUTH_TYPE.Secret]
    },
    RESOURCE.KubernetesCluster: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret],
        RESOURCE.Sql: [AUTH_TYPE.Secret],
        RESOURCE.Redis: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.RedisEnterprise: [AUTH_TYPE.SecretAuto],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.KeyVault: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.SignalR: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.WebPubSub: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ConfluentKafka: [AUTH_TYPE.Secret],
        RESOURCE.AppInsights: [AUTH_TYPE.SecretAuto],

        RESOURCE.CognitiveServices: [AUTH_TYPE.WorkloadIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.NeonPostgres: [AUTH_TYPE.Secret],
        RESOURCE.MongoDbAtlas: [AUTH_TYPE.Secret]
    },
    RESOURCE.ContainerApp: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Sql: [AUTH_TYPE.Secret, AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.Redis: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.RedisEnterprise: [AUTH_TYPE.SecretAuto],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.KeyVault: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.SignalR: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.WebPubSub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ConfluentKafka: [AUTH_TYPE.Secret],
        RESOURCE.FabricSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity],
        RESOURCE.AppInsights: [AUTH_TYPE.SecretAuto],

        RESOURCE.CognitiveServices: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.NeonPostgres: [AUTH_TYPE.Secret],
        RESOURCE.MongoDbAtlas: [AUTH_TYPE.Secret],
        RESOURCE.ContainerApp: [AUTH_TYPE.Null]
    },
}
SUPPORTED_AUTH_TYPE[RESOURCE.SpringCloudDeprecated] = SUPPORTED_AUTH_TYPE[RESOURCE.SpringCloud]
SUPPORTED_AUTH_TYPE[RESOURCE.FunctionApp] = SUPPORTED_AUTH_TYPE[RESOURCE.WebApp]


# The dict defines the supported client types of each source-target resource pair
# The first one will be used as the default client type
SUPPORTED_CLIENT_TYPE = {
    RESOURCE.WebApp: {
        RESOURCE.Postgres: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.PostgresFlexible: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.NeonPostgres: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.MongoDbAtlas: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.Mysql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.MysqlFlexible: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.Sql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.Redis: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.RedisEnterprise: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.CosmosCassandra: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.CosmosGremlin: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.CosmosMongo: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.CosmosTable: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.CosmosSql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.StorageBlob: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.StorageQueue: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.StorageFile: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.StorageTable: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.KeyVault: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.AppConfig: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.EventHub: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.KafkaSpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.ServiceBus: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.SignalR: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.WebPubSub: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.ConfluentKafka: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.FabricSql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.AppInsights: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.CognitiveServices: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Blank
        ],
        RESOURCE.ContainerApp: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.DotnetInternal,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot,
            CLIENT_TYPE.Blank
        ]
    }
}

SUPPORTED_CLIENT_TYPE[RESOURCE.SpringCloud] = SUPPORTED_CLIENT_TYPE[RESOURCE.WebApp]
SUPPORTED_CLIENT_TYPE[RESOURCE.SpringCloudDeprecated] = SUPPORTED_CLIENT_TYPE[RESOURCE.WebApp]
SUPPORTED_CLIENT_TYPE[RESOURCE.KubernetesCluster] = SUPPORTED_CLIENT_TYPE[RESOURCE.WebApp]
SUPPORTED_CLIENT_TYPE[RESOURCE.ContainerApp] = SUPPORTED_CLIENT_TYPE[RESOURCE.WebApp]
SUPPORTED_CLIENT_TYPE[RESOURCE.Local] = SUPPORTED_CLIENT_TYPE[RESOURCE.WebApp]
SUPPORTED_CLIENT_TYPE[RESOURCE.FunctionApp] = SUPPORTED_CLIENT_TYPE[RESOURCE.WebApp]


# The dict defines the options for opt-out
class OPT_OUT_OPTION(Enum):
    PUBLIC_NETWORK = 'publicnetwork'
    CONFIGURATION_INFO = 'configinfo'
    AUTHENTICATION = 'auth'
