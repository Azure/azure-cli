# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.express_route.port.link._update import Update as _ExpressRoutePortLinkUpdate


class ExpressRoutePortLinkUpdate(_ExpressRoutePortLinkUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.admin_state._blank = "Enabled"

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # TODO https://github.com/Azure/azure-rest-api-specs/issues/7569
        # need to remove this conversion when the issue is fixed.
        if has_value(args.macsec_cipher):
            macsec_cipher = args.macsec_cipher.to_serialized_data()
            macsec_ciphers_tmp = {'gcm-aes-128': 'GcmAes128', 'gcm-aes-256': 'GcmAes256'}
            macsec_cipher = macsec_ciphers_tmp.get(macsec_cipher, macsec_cipher)
            args.macsec_cipher = macsec_cipher
