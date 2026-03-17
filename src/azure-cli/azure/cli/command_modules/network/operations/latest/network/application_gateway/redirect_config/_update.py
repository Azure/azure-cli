# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.redirect_config._update import Update as _RedirectConfigUpdate


class RedirectConfigUpdate(_RedirectConfigUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/httpListeners/{}",
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.target_listener.id):
            instance.properties.target_listener = None
        if has_value(instance.properties.target_listener):
            instance.properties.target_url = None
        if has_value(instance.properties.target_url):
            instance.properties.target_listener = None
