# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum

DOTNET_FILE = "local:///usr/hdp/current/spark2-client/jars/microsoft-spark.jar"
DOTNET_CLASS = "org.apache.spark.deploy.dotnet.DotnetRunner"
EXECUTOR_SIZE = {'Small': {'Cores': 4, 'Memory': '28g'}, 'Medium': {'Cores': 8, 'Memory': '56g'},
                 'Large': {'Cores': 16, 'Memory': '112g'}}
SPARK_DOTNET_ASSEMBLY_SEARCH_PATHS_KEY = 'spark.yarn.appMasterEnv.DOTNET_ASSEMBLY_SEARCH_PATHS'
SPARK_DOTNET_UDFS_FOLDER_NAME = 'udfs'
SPARK_SERVICE_ENDPOINT_API_VERSION = '2019-11-01-priview'
AdministratorType = "activeDirectory"
ITEM_NAME_MAPPING = {'bigDataPools': '{bigDataPoolName}', 'integrationRuntimes': '{integrationRuntimeName}',
                     'linkedServices': '{linkedServiceName}', 'credentials': '{credentialName}'}


class SynapseSqlCreateMode(str, Enum):
    Default = 'Default'
    Recovery = 'Recovery'
    Restore = 'Restore'
    PointInTimeRestore = 'PointInTimeRestore'


class SparkBatchLanguage(str, Enum):
    Spark = 'Spark'
    Scala = 'Scala'
    PySpark = 'PySpark'
    Python = 'Python'
    SparkDotNet = 'SparkDotNet'
    CSharp = 'CSharp'


class SparkStatementLanguage(str, Enum):
    Spark = 'Spark'
    Scala = 'Scala'
    PySpark = 'PySpark'
    Python = 'Python'
    SparkDotNet = 'SparkDotNet'
    CSharp = 'CSharp'
    SQL = 'SQL'


# pylint: disable=too-few-public-methods
class SqlPoolConnectionClientType(str, Enum):
    '''
    Types of SQL clients whose connection strings we can generate.
    '''

    AdoDotNet = 'ado.net'
    Jdbc = 'jdbc'
    Php = 'php'
    Odbc = 'odbc'
    PhpPdo = 'php_pdo'


class SqlPoolConnectionClientAuthenticationType(str, Enum):
    '''
    Types of SQL client authentication mechanisms for connection strings
    that we can generate.
    '''

    SqlPassword = 'SqlPassword'
    ActiveDirectoryPassword = 'ADPassword'
    ActiveDirectoryIntegrated = 'ADIntegrated'


class PrincipalType(str, Enum):
    user = "User"
    group = "Group"
    service_principal = "ServicePrincipal"


class ItemType(str, Enum):
    bigDataPools = "bigDataPools"
    integrationRuntimes = "integrationRuntimes"
    credentials = "credentials"
    linkedServices = "linkedServices"
