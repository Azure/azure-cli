# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):
    from azure.cli.command_modules.relay.action import AlertAddIpRule

    # Region Namespace NetworkRuleSet
    with self.argument_context('relay namespace network-rule-set') as c:
        c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None,
                   help='Name of the Namespace')

    for scope in ['relay namespace network-rule-set ip-rule add', 'relay namespace network-rule-set ip-rule remove']:
        with self.argument_context(scope) as c:
            c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None,
                       help='Name of the Namespace')
            c.argument('ip_rule', action=AlertAddIpRule, nargs='+', help='List of IP rules.')
