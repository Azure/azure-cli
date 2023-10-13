# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

LINUX_RUNTIMES = ['dotnet', 'node', 'python', 'java']
WINDOWS_RUNTIMES = ['dotnet', 'node', 'java', 'powershell']

DEFAULT_LOGICAPP_RUNTIME = 'node'
DEFAULT_LOGICAPP_FUNCTION_VERSION = '4'

# functions version -> runtime : default runtime version
FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION = {
    '2': {
        'node': '~8',
        'dotnet': '2'
    },
    '3': {
        'node': '~16',
        'dotnet': '3'
    },
    '4': {
        'node': '~16',
        'dotnet': '6'
    }
}
# functions version -> runtime : runtime versions
FUNCTIONS_VERSION_TO_SUPPORTED_RUNTIME_VERSIONS = {
    '2': {
        'node': ['~8', '~10'],
        'dotnet': ['2']
    },
    '3': {
        'node': ['~14', '~16', '~18'],
        'dotnet': ['3']
    },
    '4': {
        'node': ['~16', '~18'],
        'dotnet': ['3', '6']
    }
}
# dotnet runtime version : dotnet linuxFxVersion
DOTNET_RUNTIME_VERSION_TO_DOTNET_LINUX_FX_VERSION = {
    '2': '2.2',
    '3': '3.1'
}

OS_TYPES = ['Windows', 'Linux']

CONTAINER_APPSETTING_NAMES = ['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                              'DOCKER_REGISTRY_SERVER_PASSWORD', "WEBSITES_ENABLE_APP_SERVICE_STORAGE"]
APPSETTINGS_TO_MASK = ['DOCKER_REGISTRY_SERVER_PASSWORD']

SCALE_VALID_PARAMS = {
    "runtimeScaleMonitoringEnabled": "siteConfig.functionsRuntimeScaleMonitoringEnabled",
    "logicAppScaleLimit": "siteConfig.functionAppScaleLimit",
    "minimumElasticInstanceCount": "siteConfig.minimumElasticInstanceCount"
}
