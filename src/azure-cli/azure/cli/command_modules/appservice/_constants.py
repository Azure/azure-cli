# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

NODE_VERSION_DEFAULT = "10.14"
NODE_VERSION_NEWER = "12-lts"
NODE_EXACT_VERSION_DEFAULT = "10.14.1"
NETCORE_VERSION_DEFAULT = "3.1"
ASPDOTNET_VERSION_DEFAULT = "4.8"
DOTNET_VERSION_DEFAULT = "5.0"
DOTNET_TARGET_FRAMEWORK_REGEX = r"^net\d+\.\d+$"
PYTHON_VERSION_DEFAULT = "3.7"
NETCORE_RUNTIME_NAME = "dotnetcore"
ASPDOTNET_RUNTIME_NAME = "aspnet"
DOTNET_RUNTIME_NAME = "dotnet"
NODE_RUNTIME_NAME = "node"
PYTHON_RUNTIME_NAME = "python"
OS_DEFAULT = "Windows"
STATIC_RUNTIME_NAME = "static"  # not an official supported runtime but used for CLI logic
NODE_VERSIONS = ['10.6', '10.14']
PYTHON_VERSIONS = ['3.9', '3.8', '3.7', '3.6']
NETCORE_VERSIONS = ['2.1', '3.1']
DOTNET_VERSIONS = ['5.0', '6.0']
ASPDOTNET_VERSIONS = ['3.5', '4.8']
LINUX_SKU_DEFAULT = "P1V2"
FUNCTIONS_VERSIONS = ['2', '3', '4']
FUNCTIONS_STACKS_API_JSON_PATHS = {
    'windows': os.path.abspath(os.path.join(os.path.abspath(__file__), '../resources/WindowsFunctionsStacks.json')),
    'linux': os.path.abspath(os.path.join(os.path.abspath(__file__), '../resources/LinuxFunctionsStacks.json'))
}
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


class FUNCTIONS_STACKS_API_KEYS():
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


RUNTIME_STACKS = os.path.abspath(os.path.join(os.path.abspath(__file__),
                                              '../resources/WebappRuntimeStacks.json'))

GENERATE_RANDOM_APP_NAMES = os.path.abspath(os.path.join(os.path.abspath(__file__),
                                                         '../resources/GenerateRandomAppNames.json'))

PUBLIC_CLOUD = "AzureCloud"

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
