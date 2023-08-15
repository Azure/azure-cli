# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger

from ._util import import_aaz_by_profile

logger = get_logger(__name__)


_VpnConnSharedKey = import_aaz_by_profile("network.vpn_connection.shared_key")


class VpnConnSharedKeyUpdate(_VpnConnSharedKey.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.value._required = True
        return args_schema
