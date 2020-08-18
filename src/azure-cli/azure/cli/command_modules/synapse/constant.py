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
