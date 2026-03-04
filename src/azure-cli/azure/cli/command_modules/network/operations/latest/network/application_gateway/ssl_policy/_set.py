# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.ssl_policy._set import Set as _SSLPolicySet


class SSLPolicySet(_SSLPolicySet):
    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.name):
            args.policy_type = "Predefined"
        elif not has_value(args.policy_type) \
                and (has_value(args.cipher_suites) or has_value(args.min_protocol_version)):
            args.policy_type = "Custom"
