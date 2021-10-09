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
    AddServicePrincipalAuthInfo
)
# pylint: disable=line-too-long


# The dict defines the resource types, including both source resources and target resources.
# The enum value will be used in command name
class RESOURCE(Enum):
    WebApp = 'webapp'
    SpringCloud = 'spring-cloud'
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
    KeyVault = 'keyvault'
    EventHub = 'eventhub'
    AppConfig = 'appconfig'
    ServiceBus = 'servicebus'


# The dict defines the auth types
class AUTH_TYPE(Enum):
    Secret = 'secret'
    SecretAuto = 'secret(auto)'  # secret which don't need user provide name & password
    SystemIdentity = 'system-managed-identity'
    UserIdentity = 'user-managed-identity'
    ServicePrincipalSecret = 'service-principal'


# The dict defines the client types
class CLIENT_TYPE(Enum):
    Dotnet = 'dotnet'
    Java = 'java'
    Nodejs = 'nodejs'
    Python = 'python'
    Go = 'go'
    Php = 'php'
    Ruby = 'ruby'
    SpringBoot = 'springBoot'
    Django = 'django'
    Blank = 'none'


# The source resources released as CLI extensions
SOURCE_RESOURCES_IN_EXTENSION = [RESOURCE.SpringCloud]


# The dict defines the resource id pattern of source resources.
SOURCE_RESOURCES = {
    RESOURCE.WebApp: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.Web/sites/{site}',
    RESOURCE.SpringCloud: '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.AppPlatform/Spring/{spring}/apps/{app}/deployments/{deployment}'
}


# The dict defines the resource id pattern of target resources.
TARGET_RESOURCES = {
    RESOURCE.Postgres: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBforPostgreSQL/servers/{server}/databases/{database}',
    RESOURCE.PostgresFlexible: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server}/databases/{database}',
    RESOURCE.MysqlFlexible: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBforMySQL/flexibleServers/{server}/databases/{database}',
    RESOURCE.Mysql: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DBForMySQL/servers/{server}/databases/{database}',
    RESOURCE.Sql: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Sql/servers/{server}/databases/{database}',

    RESOURCE.CosmosCassandra: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/cassandraKeyspaces/{key_space}',
    RESOURCE.CosmosGremlin: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/gremlinDatabases/{database}/graphs/{graph}',
    RESOURCE.CosmosMongo: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/mongodbDatabases/{database}',
    RESOURCE.CosmosSql: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/sqlDatabases/{database}',
    RESOURCE.CosmosTable: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/{account}/tables/{table}',

    RESOURCE.StorageBlob: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/blobServices/default',
    RESOURCE.StorageQueue: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/fileServices/default',
    RESOURCE.StorageFile: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/queueServices/default',
    RESOURCE.StorageTable: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.Storage/storageAccounts/{account}/tableServices/default',

    RESOURCE.KeyVault: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.KeyVault/vaults/{vault}',
    RESOURCE.AppConfig: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.AppConfiguration/configurationStores/{config_store}',
    RESOURCE.EventHub: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.EventHub/namespaces/{namespace}',
    RESOURCE.ServiceBus: '/subscriptions/{subscription}/resourceGroups/{target_resource_group}/providers/Microsoft.ServiceBus/namespaces/{namespace}'
}


# The dict defines the parameters used to position the source resources.
# The parmaters should include all variables defined in source resource id expect
# for 'subscription', which will be dealt by CLI core as a default parameter.
SOURCE_RESOURCES_PARAMS = {
    RESOURCE.WebApp: {
        'source_resource_group': {
            'options': ['--source-resource-group', '-sg'],
            'help': 'The resource group which contains the webapp'
        },
        'site': {
            'options': ['--webapp'],
            'help': 'Name of the webapp'
        }
    },
    RESOURCE.SpringCloud: {
        'source_resource_group': {
            'options': ['--source-resource-group', '-sg'],
            'help': 'The resource group which contains the spring-cloud'
        },
        'spring': {
            'options': ['--service', '-s'],
            'help': 'Name of the spring-cloud service'
        },
        'app': {
            'options': ['--app'],
            'help': 'Name of the spring-cloud app'
        },
        'deployment': {
            'options': ['--deployment'],
            'help': 'The deployment name of the app'
        }
    }
}


# The dict defines the parameters used to position the target resources.
# The parmaters should include all variables defined in target resource id expect
# for 'subscription', which will be dealt by CLI core as a default parameter.
TARGET_RESOURCES_PARAMS = {
    RESOURCE.Postgres: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the postgres service'
        },
        'server': {
            'options': ['--postgres'],
            'help': 'Name of postgres server'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of database'
        }
    },
    RESOURCE.PostgresFlexible: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the flexible postgres service'
        },
        'server': {
            'options': ['--postgres'],
            'help': 'Name of flexible postgres server'
        },
        'database': {
            'options': ['--database'],
            'help': 'Name of database'
        }
    },
    RESOURCE.MysqlFlexible: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the mysql flexible server'
        },
        'server': {
            'options': ['--server-name', '-s'],
            'help': 'Name of the server'
        },
        'database': {
            'options': ['--database-name', '-d'],
            'help': 'Name of the database'
        }
    },
    RESOURCE.Mysql: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the mysql server'
        },
        'server': {
            'options': ['--server-name', '-s'],
            'help': 'Name of the server'
        },
        'database': {
            'options': ['--database-name', '-d'],
            'help': 'Name of the database'
        }
    },
    RESOURCE.Sql: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the sql server'
        },
        'server': {
            'options': ['--server-name', '-s'],
            'help': 'Name of the server'
        },
        'database': {
            'options': ['--database-name', '-d'],
            'help': 'Name of the database'
        }
    },
    RESOURCE.CosmosCassandra: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the cosmos database account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the cosmos database account'
        },
        'key_space': {
            'options': ['--key-space'],
            'help': 'Name of the keyspace'
        }
    },
    RESOURCE.CosmosGremlin: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the cosmos database account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the cosmos database account'
        },
        'database': {
            'options': ['--database-name', '-d'],
            'help': 'Name of the database'
        },
        'graph': {
            'options': ['--graph-name'],
            'help': 'Name of the graph'
        }
    },
    RESOURCE.CosmosMongo: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the cosmos database account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the cosmos database account'
        },
        'database': {
            'options': ['--database-name', '-d'],
            'help': 'Name of the database'
        }
    },
    RESOURCE.CosmosSql: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the cosmos database account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the cosmos database account'
        },
        'database': {
            'options': ['--database-name', '-d'],
            'help': 'Name of the database'
        }
    },
    RESOURCE.CosmosTable: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the cosmos database account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the cosmos database account'
        },
        'table': {
            'options': ['--table-name'],
            'help': 'Name of the table'
        }
    },
    RESOURCE.StorageBlob: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the storage account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the storage account'
        },
    },
    RESOURCE.StorageQueue: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the storage account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the storage account'
        },
    },
    RESOURCE.StorageFile: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the storage account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the storage account'
        },
    },
    RESOURCE.StorageTable: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the storage account'
        },
        'account': {
            'options': ['--account-name', '-a'],
            'help': 'Name of the storage account'
        },
    },
    RESOURCE.KeyVault: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the keyvault'
        },
        'vault': {
            'options': ['--vault-name'],
            'help': 'Name of the keyvault'
        }
    },
    RESOURCE.AppConfig: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the app configuration'
        },
        'config_store': {
            'options': ['--app-config'],
            'help': 'Name of the app configuration'
        }
    },
    RESOURCE.EventHub: {
        'target_resource_group': {
            'options': ['--target-resource-group', '-tg'],
            'help': 'The resource group which contains the eventhub'
        },
        'namespace': {
            'options': ['--namespace'],
            'help': 'Name of the eventhub namespace'
        }
    },
}


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
    AUTH_TYPE.ServicePrincipalSecret: {
        'service_principal_auth_info_secret': {
            'options': ['--service-principal'],
            'help': 'The service principal auth info',
            'action': AddServicePrincipalAuthInfo
        }
    }
}


# The dict defines the supported auth type of each source-target resource pair
# The first one will be used as the default auth type
SUPPORTED_AUTH_TYPE = {
    RESOURCE.WebApp: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret],
        RESOURCE.Sql: [AUTH_TYPE.Secret],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.SecretAuto],

        RESOURCE.KeyVault: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
    },
    RESOURCE.SpringCloud: {
        RESOURCE.Postgres: [AUTH_TYPE.Secret],
        RESOURCE.PostgresFlexible: [AUTH_TYPE.Secret],
        RESOURCE.Mysql: [AUTH_TYPE.Secret],
        RESOURCE.MysqlFlexible: [AUTH_TYPE.Secret],
        RESOURCE.Sql: [AUTH_TYPE.Secret],

        RESOURCE.CosmosCassandra: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosGremlin: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosMongo: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosTable: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.CosmosSql: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],

        RESOURCE.StorageBlob: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageQueue: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.StorageFile: [AUTH_TYPE.SecretAuto],
        RESOURCE.StorageTable: [AUTH_TYPE.SecretAuto],

        RESOURCE.KeyVault: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.AppConfig: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.EventHub: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
        RESOURCE.ServiceBus: [AUTH_TYPE.SystemIdentity, AUTH_TYPE.SecretAuto, AUTH_TYPE.UserIdentity, AUTH_TYPE.ServicePrincipalSecret],
    }
}


# The dict defines the supported client types of each source-target resource pair
# The first one will be used as the default client type
SUPPORTED_CLIENT_TYPE = {
    RESOURCE.WebApp: {
        RESOURCE.Postgres: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.PostgresFlexible: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.Mysql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.MysqlFlexible: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.Sql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.Django,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosCassandra: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosGremlin: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Php
        ],
        RESOURCE.CosmosMongo: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosTable: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosSql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs
        ],
        RESOURCE.StorageBlob: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.StorageQueue: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.StorageFile: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Php,
            CLIENT_TYPE.Ruby,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.StorageTable: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs
        ],
        RESOURCE.KeyVault: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.AppConfig: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs
        ],
        RESOURCE.EventHub: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.ServiceBus: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.Python,
            CLIENT_TYPE.Nodejs,
            CLIENT_TYPE.Go,
            CLIENT_TYPE.SpringBoot
        ],
    },
    RESOURCE.SpringCloud: {
        RESOURCE.Postgres: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.PostgresFlexible: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.Mysql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.MysqlFlexible: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.Sql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosCassandra: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosGremlin: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
        ],
        RESOURCE.CosmosMongo: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosTable: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.CosmosSql: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
        ],
        RESOURCE.StorageBlob: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.StorageQueue: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.StorageFile: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.StorageTable: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
        ],
        RESOURCE.KeyVault: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.AppConfig: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
        ],
        RESOURCE.EventHub: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ],
        RESOURCE.ServiceBus: [
            CLIENT_TYPE.Dotnet,
            CLIENT_TYPE.Java,
            CLIENT_TYPE.SpringBoot
        ]
    }
}
