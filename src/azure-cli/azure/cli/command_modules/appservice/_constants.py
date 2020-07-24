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
