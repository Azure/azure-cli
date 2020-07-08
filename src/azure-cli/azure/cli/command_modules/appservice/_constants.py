# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

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
        {
            "displayName": "aspnet|V4.7",
            "configs": {
                "net_framework_version": "v4.0"
            }
        },
        {
            "displayName": "aspnet|V3.5",
            "configs": {
                "net_framework_version": "v2.0"
            }
        },
        {
            "displayName": "DOTNETCORE|2.1",
            "configs": {}
        },
        {
            "displayName": "DOTNETCORE|3.1",
            "configs": {}
        },
        {
            "displayName": "node|10.0",
            "configs": {
                "WEBSITE_NODE_DEFAULT_VERSION": "10.0"
            }
        },
        {
            "displayName": "node|10.6",
            "configs": {
                "WEBSITE_NODE_DEFAULT_VERSION": "10.6"
            }
        },
        {
            "displayName": "node|10.14",
            "configs": {
                "WEBSITE_NODE_DEFAULT_VERSION": "10.14"
            }
        },
        {
            "displayName": "node|10.15",
            "configs": {
                "WEBSITE_NODE_DEFAULT_VERSION": "10.15.2"
            }
        },
        {
            "displayName": "php|7.2",
            "configs": {
                "php_version": "7.2"
            }
        },
        {
            "displayName": "php|7.3",
            "configs": {
                "php_version": "7.3"
            }
        },
        {
            "displayName": "php|7.4",
            "configs": {
                "php_version": "7.4"
            }
        },
        {
            "displayName": "python|3.6",
            "configs": {
                "python_version": "3.4.0"
            }
        },
        {
            "displayName": "java|1.7|Tomcat|7.0",
            "configs": {
                "java_version": "1.7",
                "java_container": "tomcat",
                "java_container_version": "7.0"
            }
        },
        {
            "displayName": "java|1.7|Tomcat|8.0",
            "configs": {
                "java_version": "1.7",
                "java_container": "tomcat",
                "java_container_version": "8.0"
            }
        },
        {
            "displayName": "java|1.7|Tomcat|8.5",
            "configs": {
                "java_version": "1.7",
                "java_container": "tomcat",
                "java_container_version": "8.5"
            }
        },
        {
            "displayName": "java|1.7|Tomcat|9.0",
            "configs": {
                "java_version": "1.7",
                "java_container": "tomcat",
                "java_container_version": "9.0"
            }
        },
        {
            "displayName": "java|1.7|Jetty|9.1",
            "configs": {
                "java_version": "1.7",
                "java_container": "jetty",
                "java_container_version": "9.1"
            }
        },
        {
            "displayName": "java|1.7|Jetty|9.3",
            "configs": {
                "java_version": "1.7",
                "java_container": "jetty",
                "java_container_version": "9.3"
            }
        },
        {
            "displayName": "java|1.7|Java SE|8",
            "configs": {
                "java_version": "1.7",
                "java_container": "java",
                "java_container_version": "8"
            }
        },
        {
            "displayName": "java|1.8|Tomcat|7.0",
            "configs": {
                "java_version": "1.8",
                "java_container": "tomcat",
                "java_container_version": "7.0"
            }
        },
        {
            "displayName": "java|1.8|Tomcat|8.0",
            "configs": {
                "java_version": "1.8",
                "java_container": "tomcat",
                "java_container_version": "8.0"
            }
        },
        {
            "displayName": "java|1.8|Tomcat|8.5",
            "configs": {
                "java_version": "1.8",
                "java_container": "tomcat",
                "java_container_version": "8.5"
            }
        },
        {
            "displayName": "java|1.8|Tomcat|9.0",
            "configs": {
                "java_version": "1.8",
                "java_container": "tomcat",
                "java_container_version": "9.0"
            }
        },
        {
            "displayName": "java|1.8|Jetty|9.1",
            "configs": {
                "java_version": "1.8",
                "java_container": "jetty",
                "java_container_version": "9.1"
            }
        },
        {
            "displayName": "java|1.8|Jetty|9.3",
            "configs": {
                "java_version": "1.8",
                "java_container": "jetty",
                "java_container_version": "9.3"
            }
        },
        {
            "displayName": "java|1.8|Java SE|8",
            "configs": {
                "java_version": "1.8",
                "java_container": "java",
                "java_container_version": "8"
            }
        },
        {
            "displayName": "java|11|Tomcat|7.0",
            "configs": {
                "java_version": "11",
                "java_container": "tomcat",
                "java_container_version": "7.0"
            }
        },
        {
            "displayName": "java|11|Tomcat|8.0",
            "configs": {
                "java_version": "11",
                "java_container": "tomcat",
                "java_container_version": "8.0"
            }
        },
        {
            "displayName": "java|11|Tomcat|8.5",
            "configs": {
                "java_version": "11",
                "java_container": "tomcat",
                "java_container_version": "8.5"
            }
        },
        {
            "displayName": "java|11|Tomcat|9.0",
            "configs": {
                "java_version": "11",
                "java_container": "tomcat",
                "java_container_version": "9.0"
            }
        },
        {
            "displayName": "java|11|Jetty|9.1",
            "configs": {
                "java_version": "11",
                "java_container": "jetty",
                "java_container_version": "9.1"
            }
        },
        {
            "displayName": "java|11|Jetty|9.3",
            "configs": {
                "java_version": "11",
                "java_container": "jetty",
                "java_container_version": "9.3"
            }
        },
        {
            "displayName": "java|11|Java SE|8",
            "configs": {
                "java_version": "11",
                "java_container": "java",
                "java_container_version": "8"
            }
        }
    ],
    'linux': [
        { "displayName": "DOTNETCORE|2.1" },
        { "displayName": "DOTNETCORE|3.1" },
        { "displayName": "NODE|12-lts" },
        { "displayName": "NODE|10-lts" },
        { "displayName": "NODE|10.1" },
        { "displayName": "NODE|10.10" },
        { "displayName": "NODE|10.12" },
        { "displayName": "NODE|10.14" },
        { "displayName": "NODE|10.16" },
        { "displayName": "NODE|12.9" },
        { "displayName": "JAVA|8-jre8" },
        { "displayName": "JAVA|11-java11" },
        { "displayName": "TOMCAT|8.5-jre8" },
        { "displayName": "TOMCAT|9.0-jre8" },
        { "displayName": "TOMCAT|8.5-java11" },
        { "displayName": "TOMCAT|9.0-java11" },
        { "displayName": "PHP|7.2" },
        { "displayName": "PHP|7.3" },
        { "displayName": "PYTHON|3.8" },
        { "displayName": "PYTHON|3.7" },
        { "displayName": "PYTHON|3.6" },
        { "displayName": "RUBY|2.5.5" },
        { "displayName": "RUBY|2.6.2" }
    ]
}
