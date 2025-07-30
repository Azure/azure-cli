# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

DOTNET_TARGET_FRAMEWORK_REGEX = r"^net\d+\.\d+$"
NETCORE_RUNTIME_NAME = "dotnetcore"
ASPDOTNET_RUNTIME_NAME = "aspnet"
DOTNET_RUNTIME_NAME = "dotnet"
NODE_RUNTIME_NAME = "node"
PYTHON_RUNTIME_NAME = "python"
OS_DEFAULT = "Windows"
LINUX_OS_NAME = "linux"
WINDOWS_OS_NAME = "windows"
STATIC_RUNTIME_NAME = "static"  # not an official supported runtime but used for CLI logic
LINUX_SKU_DEFAULT = "P1V2"
FUNCTIONS_VERSIONS = ['4']
LOGICAPPS_NODE_RUNTIME_VERSIONS = ['~14', '~16', '~18']
FUNCTIONS_LINUX_RUNTIME_VERSION_REGEX = r"^.*\|(.*)$"
FUNCTIONS_WINDOWS_RUNTIME_VERSION_REGEX = r"^~(.*)$"
FUNCTIONS_NO_V2_REGIONS = {
    "USNat West",
    "USNat East",
    "USSec West",
    "USSec East"
}
GITHUB_OAUTH_CLIENT_ID = "8d8e1f6000648c575489"
GITHUB_OAUTH_SCOPES = [
    "admin:repo_hook",
    "repo",
    "workflow"
]
LOGICAPP_KIND = "workflowapp"
FUNCTIONAPP_KIND = "functionapp"
LINUXAPP_KIND = "linux"
DOTNET_REFERENCES_DIR_IN_ZIP = ".az-references"


class FUNCTIONS_STACKS_API_KEYS:
    # pylint:disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        self.NAME = 'name'
        self.VALUE = 'value'
        self.DISPLAY = 'display'
        self.PROPERTIES = 'properties'
        self.MAJOR_VERSIONS = 'majorVersions'
        self.DISPLAY_VERSION = 'displayVersion'
        self.RUNTIME_VERSION = 'runtimeVersion'
        self.IS_HIDDEN = 'isHidden'
        self.IS_PREVIEW = 'isPreview'
        self.IS_DEPRECATED = 'isDeprecated'
        self.IS_DEFAULT = 'isDefault'
        self.SITE_CONFIG_DICT = 'siteConfigPropertiesDictionary'
        self.APP_SETTINGS_DICT = 'appSettingsDictionary'
        self.LINUX_FX_VERSION = 'linuxFxVersion'
        self.APPLICATION_INSIGHTS = 'applicationInsights'
        self.SUPPORTED_EXTENSION_VERSIONS = 'supportedFunctionsExtensionVersions'
        self.USE_32_BIT_WORKER_PROC = 'use32BitWorkerProcess'
        self.FUNCTIONS_WORKER_RUNTIME = 'FUNCTIONS_WORKER_RUNTIME'
        self.GIT_HUB_ACTION_SETTINGS = 'git_hub_action_settings'
        self.END_OF_LIFE_DATE = 'endOfLifeDate'


GENERATE_RANDOM_APP_NAMES = os.path.abspath(os.path.join(os.path.abspath(__file__),
                                                         '../resources/GenerateRandomAppNames.json'))

PUBLIC_CLOUD = "AzureCloud"

VERSION_2022_09_01 = "2022-09-01"

LINUX_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH = {
    'node': 'AppService/linux/nodejs-webapp-on-azure.yml',
    'python': 'AppService/linux/python-webapp-on-azure.yml',
    'dotnetcore': 'AppService/linux/aspnet-core-webapp-on-azure.yml',
    'java': 'AppService/linux/java-jar-webapp-on-azure.yml',
    'tomcat': 'AppService/linux/java-war-webapp-on-azure.yml'
}

WINDOWS_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH = {
    'node': 'AppService/windows/nodejs-webapp-on-azure.yml',
    'python': 'AppService/windows/python-webapp-on-azure.yml',
    'dotnetcore': 'AppService/windows/aspnet-core-webapp-on-azure.yml',
    'java': 'AppService/windows/java-jar-webapp-on-azure.yml',
    'tomcat': 'AppService/windows/java-war-webapp-on-azure.yml'
}

LINUX_FUNCTIONAPP_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH = {
    'node': 'FunctionApp/linux-node.js-functionapp-on-azure.yml',
    'python': 'FunctionApp/linux-python-functionapp-on-azure.yml',
    'dotnet': 'FunctionApp/linux-dotnet-functionapp-on-azure.yml',
    'java': 'FunctionApp/linux-java-functionapp-on-azure.yml',
    'powershell': 'FunctionApp/linux-powershell-functionapp-on-azure.yml',
}

WINDOWS_FUNCTIONAPP_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH = {
    'node': 'FunctionApp/windows-node.js-functionapp-on-azure.yml',
    'dotnet': 'FunctionApp/windows-dotnet-functionapp-on-azure.yml',
    'java': 'FunctionApp/windows-java-functionapp-on-azure.yml',
    'powershell': 'FunctionApp/windows-powershell-functionapp-on-azure.yml',
}

DEFAULT_CENTAURI_IMAGE = 'mcr.microsoft.com/azure-functions/dotnet8-quickstart-demo:1.0'
ACR_IMAGE_SUFFIX = ".azurecr.io"

RUNTIME_STATUS_TEXT_MAP = {
    "BuildRequestReceived": "Received build request...",
    "BuildInProgress": "Building the app...",
    "BuildSuccessful": "Build successful.",
    "BuildFailed": "Build failed.",
    "RuntimeStarting": "Starting the site...",
    "RuntimeSuccessful": "Site started successfully.",
    "RuntimeFailed": "Site failed to start."
}

LANGUAGE_EOL_DEPRECATION_NOTICES = {
    "dotnet|3.1": "https://azure.microsoft.com/en-us/updates/extended-support-for-"
                  "microsoft-net-core-31-will-end-on-3-december-2022/",
    "dotnet|6": "https://azure.microsoft.com/en-us/updates/dotnet6support/",
    "dotnet-isolated|6": "https://azure.microsoft.com/en-us/updates/dotnet6support/",
    "dotnet-isolated|7": "https://azure.microsoft.com/en-us/updates/dotnet7support/",
    "python|3.6": "https://azure.microsoft.com/en-us/updates/azure-functions-support-"
                  "for-python-36-is-ending-on-30-september-2022/",
    "python|3.7": "https://azure.microsoft.com/en-us/updates/community-support-for-"
                  "python-37-is-ending-on-27-june-2023/",
    "python|3.8": "https://azure.microsoft.com/en-us/updates/azure-functions-support-"
                  "for-python-38-is-ending-on-14-october-2023-6/",
    "powershell|6.2": "https://azure.microsoft.com/en-us/updates/azure-functions-support-"
                      "for-powershell-6-is-ending-on-30-september-2022/",
    "node|6": "https://azure.microsoft.com/en-us/updates/azure-functions-support-for-"
              "node-6-is-ending-on-28-february-2022/",
    "node|8": "https://azure.microsoft.com/en-us/updates/azure-functions-support-for-"
              "node-8-is-ending-on-28-february-2022/",
    "node|10": "https://azure.microsoft.com/en-us/updates/azure-functions-support-"
               "for-node-10-is-ending-on-30-september-2022/",
    "node|12": "https://azure.microsoft.com/en-us/updates/node12/",
    "node|14": "https://azure.microsoft.com/en-us/updates/community-support-for-node-"
               "14-lts-is-ending-on-30-april-2023/",
    "node|16": "https://azure.microsoft.com/en-us/updates/node16support/"
}

FLEX_SUBNET_DELEGATION = "Microsoft.App/environments"

DEPLOYMENT_STORAGE_AUTH_TYPES = ['SystemAssignedIdentity', 'UserAssignedIdentity', 'StorageAccountConnectionString']

STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
