# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=broad-exception-caught, line-too-long, no-else-return
from typing import Any, Dict

from azure.cli.core.commands import AzCliCommand
from knack.util import CLIError

from ._client_factory import handle_raw_exception
from ._utils import register_provider_if_needed, _validate_subscription_registered


class BaseResource:
    def __init__(
        self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str
    ):
        self.raw_param = raw_parameters
        self.cmd = cmd
        self.client = client
        self.models = models

    def register_provider(self, *rp_name_list):
        for rp in rp_name_list:
            register_provider_if_needed(self.cmd, rp)

    def validate_subscription_registered(self, *rp_name_list):
        for rp in rp_name_list:
            _validate_subscription_registered(self.cmd, rp)

    def list(self):
        try:
            if self.get_argument_resource_group_name() is None:
                return self.client.list_by_subscription(cmd=self.cmd)
            else:
                return self.client.list_by_resource_group(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name())
        except CLIError as e:
            handle_raw_exception(e)

    def show(self):
        try:
            return self.client.show(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name())
        except CLIError as e:
            handle_raw_exception(e)

    def delete(self):
        try:
            return self.client.delete(cmd=self.cmd, name=self.get_argument_name(), resource_group_name=self.get_argument_resource_group_name(), no_wait=self.get_argument_no_wait())
        except CLIError as e:
            handle_raw_exception(e)

    def get_param(self, key) -> Any:
        return self.raw_param.get(key)

    def set_param(self, key, value):
        self.raw_param[key] = value

    def get_argument_name(self):
        return self.get_param("name")

    def get_argument_resource_group_name(self):
        return self.get_param("resource_group_name")

    def get_argument_no_wait(self):
        return self.get_param("no_wait")
