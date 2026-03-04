# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
from knack.log import get_logger

from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.zone._create import (
    Create as _PrivateDNSZoneCreate
)

logger = get_logger(__name__)


class PrivateDNSZoneCreate(_PrivateDNSZoneCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.if_none_match._registered = False
        args_schema.location._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.name.to_serialized_data().endswith(".local"):
            logger.warning(
                "Please be aware that DNS names ending with `.local` are reserved for use with multicast DNS and "
                "may not work as expected with some operating systems. "
                "For details refer to your operating systems documentation."
            )
        args.location = "global"
        args.if_none_match = "*"
