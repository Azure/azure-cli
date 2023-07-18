# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404

from ._client_factory import (
    cf_signalr,
    cf_custom_domains,
    cf_custom_certificates)


def load_command_table(self, _):

    signalr_custom_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.custom#{}',
        client_factory=cf_signalr
    )

    signalr_key_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.key#{}',
        client_factory=cf_signalr
    )

    signalr_cors_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.cors#{}',
        client_factory=cf_signalr
    )

    signalr_network_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.network#{}',
        client_factory=cf_signalr
    )

    signalr_upstream_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.upstream#{}',
        client_factory=cf_signalr
    )

    signalr_msi_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.msi#{}',
        client_factory=cf_signalr
    )

    signalr_custom_domain_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.customdomain#{}',
        client_factory=cf_custom_domains
    )

    signalr_custom_certificate_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.signalr.customcertificate#{}',
        client_factory=cf_custom_certificates
    )

    with self.command_group('signalr', signalr_custom_utils) as g:
        g.command('create', 'signalr_create')
        g.command('delete', 'signalr_delete')
        g.command('list', 'signalr_list')
        g.show_command('show', 'signalr_show', exception_handler=empty_on_404)
        g.command('restart', 'signalr_restart', exception_handler=empty_on_404)
        g.generic_update_command('update', getter_name='signalr_update_get',
                                 setter_name='signalr_update_set', custom_func_name='signalr_update_custom',
                                 custom_func_type=signalr_custom_utils)

    with self.command_group('signalr key', signalr_key_utils) as g:
        g.command('list', 'signalr_key_list')
        g.command('renew', 'signalr_key_renew')

    with self.command_group('signalr cors', signalr_cors_utils) as g:
        g.command('add', 'signalr_cors_add')
        g.command('remove', 'signalr_cors_remove')
        g.command('list', 'signalr_cors_list')
        g.command('update', 'signalr_cors_update')

    with self.command_group('signalr network-rule', signalr_network_utils) as g:
        g.command('list', 'list_network_rules')
        g.command('update', 'update_network_rules')

    with self.command_group('signalr upstream', signalr_upstream_utils) as g:
        g.command('list', 'signalr_upstream_list')
        g.command('update', 'signalr_upstream_update')
        g.command('clear', 'signalr_upstream_clear')

    with self.command_group('signalr identity', signalr_msi_utils) as g:
        g.command('assign', 'signalr_msi_assign')
        g.command('remove', 'signalr_msi_remove')
        g.show_command('show', 'signalr_msi_show')

    with self.command_group('signalr custom-domain', signalr_custom_domain_utils) as g:
        g.show_command('show', 'custom_domain_show', exception_handler=empty_on_404)
        g.command('create', 'custom_domain_create')
        g.command('delete', 'custom_domain_delete')
        g.generic_update_command('update', getter_name='get_custom_domain', setter_name='set_custom_domain', custom_func_name='update', custom_func_type=signalr_custom_domain_utils)
        g.command('list', 'custom_domain_list')

    with self.command_group('signalr custom-certificate', signalr_custom_certificate_utils) as g:
        g.show_command('show', 'custom_certificate_show', exception_handler=empty_on_404)
        g.command('create', 'custom_certificate_create')
        g.command('delete', 'custom_certificate_delete')
        g.generic_update_command('update', getter_name='get_custom_certificate', setter_name='set_custom_certificate', custom_func_name='update', custom_func_type=signalr_custom_certificate_utils)
        g.command('list', 'custom_certificate_list')
