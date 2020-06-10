# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

NODE_VERSION_DEFAULT = "10.14"
NETCORE_VERSION_DEFAULT = "2.2"
DOTNET_VERSION_DEFAULT = "4.7"
PYTHON_VERSION_DEFAULT = "3.7"
NETCORE_RUNTIME_NAME = "dotnetcore"
DOTNET_RUNTIME_NAME = "aspnet"
NODE_RUNTIME_NAME = "node"
PYTHON_RUNTIME_NAME = "python"
OS_DEFAULT = "Windows"
STATIC_RUNTIME_NAME = "static"  # not an official supported runtime but used for CLI logic
NODE_VERSIONS = ['4.4', '4.5', '6.2', '6.6', '6.9', '6.11', '8.0', '8.1', '8.9', '8.11', '10.1', '10.10', '10.14']
PYTHON_VERSIONS = ['3.7', '3.6', '2.7']
NETCORE_VERSIONS = ['1.0', '1.1', '2.1', '2.2']
DOTNET_VERSIONS = ['3.5', '4.7']
LINUX_SKU_DEFAULT = "P1V2"
FUNCTIONS_VERSIONS = ['2', '3']
# functions version : default node version
FUNCTIONS_VERSION_TO_DEFAULT_NODE_VERSION = {
    '2': '~10',
    '3': '~12'
}
# functions version -> runtime : default runtime version
FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION = {
    '2': {
        'node': '8',
        'dotnet': '2',
        'python': '3.7',
        'java': '8'
    },
    '3': {
        'node': '12',
        'dotnet': '3',
        'python': '3.7',
        'java': '8'
    }
}
# functions version -> runtime : runtime versions
FUNCTIONS_VERSION_TO_SUPPORTED_RUNTIME_VERSIONS = {
    '2': {
        'node': ['8', '10'],
        'python': ['3.6', '3.7'],
        'dotnet': ['2'],
        'java': ['8']
    },
    '3': {
        'node': ['10', '12'],
        'python': ['3.6', '3.7', '3.8'],
        'dotnet': ['3'],
        'java': ['8']
    }
}
# dotnet runtime version : dotnet linuxFxVersion
DOTNET_RUNTIME_VERSION_TO_DOTNET_LINUX_FX_VERSION = {
    '2': '2.2',
    '3': '3.1'
}

RUNTIME_STACKS = {
    'windows': [
        "aspnet|V4.7",
        "aspnet|V3.5",
        "DOTNETCORE|2.1",
        "DOTNETCORE|3.1",
        "node|10.0",
        "node|10.6",
        "node|10.14",
        "node|10.15",
        "php|7.2",
        "php|7.3",
        "php|7.4",
        "python|3.6",
        "java|1.7|Tomcat|7.0",
        "java|1.7|Tomcat|8.0",
        "java|1.7|Tomcat|8.5",
        "java|1.7|Tomcat|9.0",
        "java|1.7|Jetty|9.1",
        "java|1.7|Jetty|9.3",
        "java|1.7|Java SE|8",
        "java|1.8|Tomcat|7.0",
        "java|1.8|Tomcat|8.0",
        "java|1.8|Tomcat|8.5",
        "java|1.8|Tomcat|9.0",
        "java|1.8|Jetty|9.1",
        "java|1.8|Jetty|9.3",
        "java|1.8|Java SE|8",
        "java|11|Tomcat|7.0",
        "java|11|Tomcat|8.0",
        "java|11|Tomcat|8.5",
        "java|11|Tomcat|9.0",
        "java|11|Jetty|9.1",
        "java|11|Jetty|9.3",
        "java|11|Java SE|8"
    ],
    'linux': [
        "DOTNETCORE|2.1",
        "DOTNETCORE|3.1",
        "NODE|12-lts",
        "NODE|10-lts",
        "NODE|10.1",
        "NODE|10.10",
        "NODE|10.12",
        "NODE|10.14",
        "NODE|10.16",
        "NODE|12.9",
        "JAVA|8-jre8",
        "JAVA|11-java11",
        "TOMCAT|8.5-jre8",
        "TOMCAT|9.0-jre8",
        "TOMCAT|8.5-java11",
        "TOMCAT|9.0-java11",
        "PHP|7.2",
        "PHP|7.3",
        "PYTHON|3.8",
        "PYTHON|3.7",
        "PYTHON|3.6",
        "RUBY|2.5.5",
        "RUBY|2.6.2",
    ]
}
