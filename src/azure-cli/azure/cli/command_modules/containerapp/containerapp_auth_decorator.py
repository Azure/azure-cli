# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, broad-exception-caught, bare-except, too-many-boolean-expressions, useless-parent-delegation, expression-not-assigned
from typing import Any, Dict

from azure.cli.core.commands import AzCliCommand
from azure.cli.core.azclierror import ArgumentUsageError

from ._client_factory import handle_raw_exception
from ._constants import BLOB_STORAGE_TOKEN_STORE_SECRET_SETTING_NAME
from ._utils import safe_set
from .base_resource import BaseResource


class ContainerAppAuthDecorator(BaseResource):
    def __init__(self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str):
        super().__init__(cmd, client, raw_parameters, models)
        self.existing_auth = {}

    def show(self):
        auth_settings = {}
        try:
            auth_settings = self.client.get(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), container_app_name=self.get_argument_name(), auth_config_name="current")["properties"]
        except:
            pass
        return auth_settings

    def construct_payload(self):
        from ._utils import set_field_in_auth_settings, update_http_settings_in_auth_settings
        self.existing_auth = {}
        try:
            self.existing_auth = self.client.get(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), container_app_name=self.get_argument_name(), auth_config_name="current")["properties"]
        except:
            self.existing_auth["platform"] = {}
            self.existing_auth["platform"]["enabled"] = True
            self.existing_auth["globalValidation"] = {}
            self.existing_auth["login"] = {}

        self.existing_auth = set_field_in_auth_settings(self.existing_auth, self.get_argument_set_string())

        if self.get_argument_enabled() is not None:
            if "platform" not in self.existing_auth:
                self.existing_auth["platform"] = {}
            self.existing_auth["platform"]["enabled"] = self.get_argument_enabled()

        if self.get_argument_runtime_version() is not None:
            if "platform" not in self.existing_auth:
                self.existing_auth["platform"] = {}
            self.existing_auth["platform"]["runtimeVersion"] = self.get_argument_runtime_version()

        if self.get_argument_config_file_path() is not None:
            if "platform" not in self.existing_auth:
                self.existing_auth["platform"] = {}
            self.existing_auth["platform"]["configFilePath"] = self.get_argument_config_file_path()

        if self.get_argument_unauthenticated_client_action() is not None:
            if "globalValidation" not in self.existing_auth:
                self.existing_auth["globalValidation"] = {}
            self.existing_auth["globalValidation"]["unauthenticatedClientAction"] = self.get_argument_unauthenticated_client_action()

        if self.get_argument_redirect_provider() is not None:
            if "globalValidation" not in self.existing_auth:
                self.existing_auth["globalValidation"] = {}
            self.existing_auth["globalValidation"]["redirectToProvider"] = self.get_argument_redirect_provider()

        if self.get_argument_excluded_paths() is not None:
            if "globalValidation" not in self.existing_auth:
                self.existing_auth["globalValidation"] = {}
            self.existing_auth["globalValidation"]["excludedPaths"] = self.get_argument_excluded_paths().split(",")

        self.existing_auth = update_http_settings_in_auth_settings(self.existing_auth, self.get_argument_require_https(),
                                                                   self.get_argument_proxy_convention(), self.get_argument_proxy_custom_host_header(),
                                                                   self.get_argument_proxy_custom_proto_header())

        if self.get_argument_token_store() is None:
            return

        if self.get_argument_token_store() is False:
            safe_set(self.existing_auth, "login", "tokenStore", "enabled", value=False)
            return

        safe_set(self.existing_auth, "login", "tokenStore", "enabled", value=True)

        if self.get_argument_sas_url_secret() is None and self.get_argument_sas_url_secret_name() is None:
            raise ArgumentUsageError(
                'Usage Error: only blob storage token store is supported. --sas-url-secret and --sas-url-secret-name should provide exactly one when token store is enabled')
        if self.get_argument_sas_url_secret() is not None and self.get_argument_sas_url_secret_name() is not None:
            raise ArgumentUsageError('Usage Error: --sas-url-secret and --sas-url-secret-name cannot both be set')

        sas_url_setting_name = BLOB_STORAGE_TOKEN_STORE_SECRET_SETTING_NAME
        if self.get_argument_sas_url_secret_name() is not None:
            sas_url_setting_name = self.get_argument_sas_url_secret_name()
        safe_set(self.existing_auth, "login", "tokenStore", "azureBlobStorage", "sasUrlSettingName",
                 value=sas_url_setting_name)

    def create_or_update(self):
        try:
            return self.client.create_or_update(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(),
                                                container_app_name=self.get_argument_name(), auth_config_name="current",
                                                auth_config_envelope=self.existing_auth)
        except Exception as e:
            handle_raw_exception(e)

    def get_argument_set_string(self):
        return self.get_param("set_string")

    def get_argument_enabled(self):
        return self.get_param("enabled")

    def get_argument_runtime_version(self):
        return self.get_param("runtime_version")

    def get_argument_config_file_path(self):
        return self.get_param("config_file_path")

    def get_argument_unauthenticated_client_action(self):
        return self.get_param("unauthenticated_client_action")

    def get_argument_redirect_provider(self):
        return self.get_param("redirect_provider")

    def get_argument_require_https(self):
        return self.get_param("require_https")

    def get_argument_proxy_convention(self):
        return self.get_param("proxy_convention")

    def get_argument_proxy_custom_host_header(self):
        return self.get_param("proxy_custom_host_header")

    def get_argument_proxy_custom_proto_header(self):
        return self.get_param("proxy_custom_proto_header")

    def get_argument_excluded_paths(self):
        return self.get_param("excluded_paths")

    def get_argument_token_store(self):
        return self.get_param("token_store")

    def get_argument_sas_url_secret(self):
        return self.get_param("sas_url_secret")

    def get_argument_sas_url_secret_name(self):
        return self.get_param("sas_url_secret_name")

    def get_argument_yes(self):
        return self.get_param("yes")
