# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.private_link_service.connection._update import Update as _PrivateEndpointConnectionUpdate


class PrivateEndpointConnectionUpdate(_PrivateEndpointConnectionUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.connection_status._required = True
        args_schema.connection_status.enum = AAZArgEnum({"Approved": "Approved", "Rejected": "Rejected", "Removed": "Removed"})
        return args_schema
