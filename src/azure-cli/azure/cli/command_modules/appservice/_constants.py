# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

NODE_VERSION_DEFAULT = "10.14"
NETCORE_VERSION_DEFAULT = "3.1"
DOTNET_VERSION_DEFAULT = "4.7"
PYTHON_VERSION_DEFAULT = "3.7"
NETCORE_RUNTIME_NAME = "dotnetcore"
DOTNET_RUNTIME_NAME = "aspnet"
NODE_RUNTIME_NAME = "node"
PYTHON_RUNTIME_NAME = "python"
OS_DEFAULT = "Windows"
STATIC_RUNTIME_NAME = "static"  # not an official supported runtime but used for CLI logic
NODE_VERSIONS = ['10.1', '10.10', '10.12', '10.14', '10.16']
PYTHON_VERSIONS = ['3.8', '3.7', '3.6']
NETCORE_VERSIONS = ['2.1', '3.1']
DOTNET_VERSIONS = ['3.5', '4.7']
LINUX_SKU_DEFAULT = "P1V2"
FUNCTIONS_VERSIONS = ['2', '3']
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


class FUNCTIONS_STACKS_API_KEYS():
    # pylint:disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        self.NAME = 'name'
        self.VALUE = 'value'
        self.PROPERTIES = 'properties'
        self.MAJOR_VERSIONS = 'majorVersions'
        self.DISPLAY_VERSION = 'displayVersion'
        self.RUNTIME_VERSION = 'runtimeVersion'
        self.IS_HIDDEN = 'isHidden'
        self.IS_PREVIEW = 'isPreview'
        self.IS_DEFAULT = 'isDefault'
        self.SITE_CONFIG_DICT = 'siteConfigPropertiesDictionary'
        self.APP_SETTINGS_DICT = 'appSettingsDictionary'
        self.LINUX_FX_VERSION = 'linuxFxVersion'
        self.APPLICATION_INSIGHTS = 'applicationInsights'
        self.SUPPORTED_EXTENSION_VERSIONS = 'supportedFunctionsExtensionVersions'


RUNTIME_STACKS = os.path.abspath(os.path.join(os.path.abspath(__file__), '../resources/WebappRuntimeStacks.json'))
