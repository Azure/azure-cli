# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apimgmt._client_factory import cf_apimgmt
def load_command_table(self, _):

    apimgmt_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimgmt.operations#ApiManagementOperations.{}',
        client_factory=cf_apimgmt)


    with self.command_group('apimgmt apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis')
        g.custom_command('update', 'update_apimgmt_apis')
        g.custom_command('delete', 'delete_apimgmt_apis')
        g.custom_command('list', 'list_apimgmt_apis')
        g.custom_command('show', 'show_apimgmt_apis')
    with self.command_group('apimgmt apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis')
        g.custom_command('list', 'list_apimgmt_apis')
    with self.command_group('apimgmt apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_apis')
    with self.command_group('apimgmt apis releases', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_releases')
        g.custom_command('update', 'update_apimgmt_apis_releases')
        g.custom_command('delete', 'delete_apimgmt_apis_releases')
        g.custom_command('list', 'list_apimgmt_apis_releases')
        g.custom_command('show', 'show_apimgmt_apis_releases')
    with self.command_group('apimgmt apis releases', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_releases')
        g.custom_command('list', 'list_apimgmt_apis_releases')
    with self.command_group('apimgmt apis operations', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_operations')
        g.custom_command('update', 'update_apimgmt_apis_operations')
        g.custom_command('delete', 'delete_apimgmt_apis_operations')
        g.custom_command('list', 'list_apimgmt_apis_operations')
        g.custom_command('show', 'show_apimgmt_apis_operations')
    with self.command_group('apimgmt apis operations', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_operations')
        g.custom_command('list', 'list_apimgmt_apis_operations')
    with self.command_group('apimgmt apis operations policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_operations_policies')
        g.custom_command('delete', 'delete_apimgmt_apis_operations_policies')
        g.custom_command('list', 'list_apimgmt_apis_operations_policies')
        g.custom_command('show', 'show_apimgmt_apis_operations_policies')
    with self.command_group('apimgmt apis operations policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_operations_policies')
        g.custom_command('list', 'list_apimgmt_apis_operations_policies')
    with self.command_group('apimgmt tags', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_tags')
        g.custom_command('update', 'update_apimgmt_tags')
        g.custom_command('delete', 'delete_apimgmt_tags')
        g.custom_command('list', 'list_apimgmt_tags')
        g.custom_command('show', 'show_apimgmt_tags')
    with self.command_group('apimgmt tags apis products operations', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_tags_apis_products_operations')
        g.custom_command('show', 'show_apimgmt_tags_apis_products_operations')
    with self.command_group('apimgmt apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_apis')
    with self.command_group('apimgmt apis policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_policies')
        g.custom_command('delete', 'delete_apimgmt_apis_policies')
        g.custom_command('list', 'list_apimgmt_apis_policies')
        g.custom_command('show', 'show_apimgmt_apis_policies')
    with self.command_group('apimgmt apis policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_policies')
        g.custom_command('list', 'list_apimgmt_apis_policies')
    with self.command_group('apimgmt apis schemas', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_schemas')
        g.custom_command('delete', 'delete_apimgmt_apis_schemas')
        g.custom_command('list', 'list_apimgmt_apis_schemas')
        g.custom_command('show', 'show_apimgmt_apis_schemas')
    with self.command_group('apimgmt apis schemas', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_schemas')
        g.custom_command('list', 'list_apimgmt_apis_schemas')
    with self.command_group('apimgmt apis diagnostics', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_diagnostics')
        g.custom_command('update', 'update_apimgmt_apis_diagnostics')
        g.custom_command('delete', 'delete_apimgmt_apis_diagnostics')
        g.custom_command('list', 'list_apimgmt_apis_diagnostics')
        g.custom_command('show', 'show_apimgmt_apis_diagnostics')
    with self.command_group('apimgmt apis diagnostics', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_diagnostics')
        g.custom_command('list', 'list_apimgmt_apis_diagnostics')
    with self.command_group('apimgmt apis issues', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_issues')
        g.custom_command('update', 'update_apimgmt_apis_issues')
        g.custom_command('delete', 'delete_apimgmt_apis_issues')
        g.custom_command('list', 'list_apimgmt_apis_issues')
        g.custom_command('show', 'show_apimgmt_apis_issues')
    with self.command_group('apimgmt apis issues', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_issues')
        g.custom_command('list', 'list_apimgmt_apis_issues')
    with self.command_group('apimgmt apis issues comments', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_issues_comments')
        g.custom_command('delete', 'delete_apimgmt_apis_issues_comments')
        g.custom_command('list', 'list_apimgmt_apis_issues_comments')
        g.custom_command('show', 'show_apimgmt_apis_issues_comments')
    with self.command_group('apimgmt apis issues comments', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_issues_comments')
        g.custom_command('list', 'list_apimgmt_apis_issues_comments')
    with self.command_group('apimgmt apis issues attachments', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_issues_attachments')
        g.custom_command('delete', 'delete_apimgmt_apis_issues_attachments')
        g.custom_command('list', 'list_apimgmt_apis_issues_attachments')
        g.custom_command('show', 'show_apimgmt_apis_issues_attachments')
    with self.command_group('apimgmt apis issues attachments', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_issues_attachments')
        g.custom_command('list', 'list_apimgmt_apis_issues_attachments')
    with self.command_group('apimgmt apis tagdescriptions', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apis_tagdescriptions')
        g.custom_command('delete', 'delete_apimgmt_apis_tagdescriptions')
        g.custom_command('list', 'list_apimgmt_apis_tagdescriptions')
        g.custom_command('show', 'show_apimgmt_apis_tagdescriptions')
    with self.command_group('apimgmt apis tagdescriptions', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis_tagdescriptions')
        g.custom_command('list', 'list_apimgmt_apis_tagdescriptions')
    with self.command_group('apimgmt apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_apis')
    with self.command_group('apimgmt apiversionsets', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apiversionsets')
        g.custom_command('update', 'update_apimgmt_apiversionsets')
        g.custom_command('delete', 'delete_apimgmt_apiversionsets')
        g.custom_command('list', 'list_apimgmt_apiversionsets')
        g.custom_command('show', 'show_apimgmt_apiversionsets')
    with self.command_group('apimgmt apiversionsets', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apiversionsets')
        g.custom_command('list', 'list_apimgmt_apiversionsets')
    with self.command_group('apimgmt authorizationservers', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_authorizationservers')
        g.custom_command('update', 'update_apimgmt_authorizationservers')
        g.custom_command('delete', 'delete_apimgmt_authorizationservers')
        g.custom_command('list', 'list_apimgmt_authorizationservers')
        g.custom_command('show', 'show_apimgmt_authorizationservers')
    with self.command_group('apimgmt authorizationservers', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_authorizationservers')
        g.custom_command('list', 'list_apimgmt_authorizationservers')
    with self.command_group('apimgmt backends', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_backends')
        g.custom_command('update', 'update_apimgmt_backends')
        g.custom_command('delete', 'delete_apimgmt_backends')
        g.custom_command('list', 'list_apimgmt_backends')
        g.custom_command('show', 'show_apimgmt_backends')
    with self.command_group('apimgmt backends', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_backends')
        g.custom_command('list', 'list_apimgmt_backends')
    with self.command_group('apimgmt caches', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_caches')
        g.custom_command('update', 'update_apimgmt_caches')
        g.custom_command('delete', 'delete_apimgmt_caches')
        g.custom_command('list', 'list_apimgmt_caches')
        g.custom_command('show', 'show_apimgmt_caches')
    with self.command_group('apimgmt caches', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_caches')
        g.custom_command('list', 'list_apimgmt_caches')
    with self.command_group('apimgmt certificates', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_certificates')
        g.custom_command('delete', 'delete_apimgmt_certificates')
        g.custom_command('list', 'list_apimgmt_certificates')
        g.custom_command('show', 'show_apimgmt_certificates')
    with self.command_group('apimgmt certificates', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_certificates')
        g.custom_command('list', 'list_apimgmt_certificates')
    with self.command_group('', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt')
        g.custom_command('update', 'update_apimgmt')
        g.custom_command('delete', 'delete_apimgmt')
        g.custom_command('list', 'list_apimgmt')
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt')
        g.custom_command('list', 'list_apimgmt')
    with self.command_group('apimgmt diagnostics', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_diagnostics')
        g.custom_command('update', 'update_apimgmt_diagnostics')
        g.custom_command('delete', 'delete_apimgmt_diagnostics')
        g.custom_command('list', 'list_apimgmt_diagnostics')
        g.custom_command('show', 'show_apimgmt_diagnostics')
    with self.command_group('apimgmt diagnostics', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_diagnostics')
        g.custom_command('list', 'list_apimgmt_diagnostics')
    with self.command_group('apimgmt templates', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_templates')
        g.custom_command('update', 'update_apimgmt_templates')
        g.custom_command('delete', 'delete_apimgmt_templates')
        g.custom_command('list', 'list_apimgmt_templates')
        g.custom_command('show', 'show_apimgmt_templates')
    with self.command_group('apimgmt templates', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_templates')
        g.custom_command('list', 'list_apimgmt_templates')
    with self.command_group('apimgmt groups', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_groups')
        g.custom_command('update', 'update_apimgmt_groups')
        g.custom_command('delete', 'delete_apimgmt_groups')
        g.custom_command('list', 'list_apimgmt_groups')
        g.custom_command('show', 'show_apimgmt_groups')
    with self.command_group('apimgmt groups', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_groups')
        g.custom_command('list', 'list_apimgmt_groups')
    with self.command_group('apimgmt groups users', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_groups_users')
        g.custom_command('delete', 'delete_apimgmt_groups_users')
        g.custom_command('list', 'list_apimgmt_groups_users')
    with self.command_group('apimgmt groups', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_groups')
    with self.command_group('apimgmt identityproviders', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_identityproviders')
        g.custom_command('update', 'update_apimgmt_identityproviders')
        g.custom_command('delete', 'delete_apimgmt_identityproviders')
        g.custom_command('list', 'list_apimgmt_identityproviders')
        g.custom_command('show', 'show_apimgmt_identityproviders')
    with self.command_group('apimgmt identityproviders', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_identityproviders')
        g.custom_command('list', 'list_apimgmt_identityproviders')
    with self.command_group('apimgmt issues', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_issues')
        g.custom_command('list', 'list_apimgmt_issues')
    with self.command_group('apimgmt loggers', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_loggers')
        g.custom_command('update', 'update_apimgmt_loggers')
        g.custom_command('delete', 'delete_apimgmt_loggers')
        g.custom_command('list', 'list_apimgmt_loggers')
        g.custom_command('show', 'show_apimgmt_loggers')
    with self.command_group('apimgmt loggers', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_loggers')
        g.custom_command('list', 'list_apimgmt_loggers')
    with self.command_group('apimgmt locations', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_locations')
    with self.command_group('apimgmt notifications', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_notifications')
        g.custom_command('list', 'list_apimgmt_notifications')
        g.custom_command('show', 'show_apimgmt_notifications')
    with self.command_group('apimgmt notifications', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_notifications')
        g.custom_command('list', 'list_apimgmt_notifications')
    with self.command_group('apimgmt notifications recipientusers', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_notifications_recipientusers')
        g.custom_command('delete', 'delete_apimgmt_notifications_recipientusers')
        g.custom_command('list', 'list_apimgmt_notifications_recipientusers')
    with self.command_group('apimgmt notifications', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_notifications')
    with self.command_group('apimgmt notifications recipientemails', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_notifications_recipientemails')
        g.custom_command('delete', 'delete_apimgmt_notifications_recipientemails')
        g.custom_command('list', 'list_apimgmt_notifications_recipientemails')
    with self.command_group('apimgmt notifications', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_notifications')
    with self.command_group('apimgmt openidconnectproviders', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_openidconnectproviders')
        g.custom_command('update', 'update_apimgmt_openidconnectproviders')
        g.custom_command('delete', 'delete_apimgmt_openidconnectproviders')
        g.custom_command('list', 'list_apimgmt_openidconnectproviders')
        g.custom_command('show', 'show_apimgmt_openidconnectproviders')
    with self.command_group('apimgmt openidconnectproviders', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_openidconnectproviders')
        g.custom_command('list', 'list_apimgmt_openidconnectproviders')
    with self.command_group('apimgmt policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_policies')
        g.custom_command('delete', 'delete_apimgmt_policies')
        g.custom_command('list', 'list_apimgmt_policies')
        g.custom_command('show', 'show_apimgmt_policies')
    with self.command_group('apimgmt policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_policies')
        g.custom_command('list', 'list_apimgmt_policies')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt')
        g.custom_command('update', 'update_apimgmt')
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt')
        g.custom_command('update', 'update_apimgmt')
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt')
        g.custom_command('update', 'update_apimgmt')
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt products', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_products')
        g.custom_command('update', 'update_apimgmt_products')
        g.custom_command('delete', 'delete_apimgmt_products')
        g.custom_command('list', 'list_apimgmt_products')
        g.custom_command('show', 'show_apimgmt_products')
    with self.command_group('apimgmt products', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_products')
        g.custom_command('list', 'list_apimgmt_products')
    with self.command_group('apimgmt products apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_products_apis')
        g.custom_command('delete', 'delete_apimgmt_products_apis')
        g.custom_command('list', 'list_apimgmt_products_apis')
    with self.command_group('apimgmt products', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_products')
    with self.command_group('apimgmt products groups', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_products_groups')
        g.custom_command('delete', 'delete_apimgmt_products_groups')
        g.custom_command('list', 'list_apimgmt_products_groups')
    with self.command_group('apimgmt products', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_products')
    with self.command_group('apimgmt products', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_products')
    with self.command_group('apimgmt products policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_products_policies')
        g.custom_command('delete', 'delete_apimgmt_products_policies')
        g.custom_command('list', 'list_apimgmt_products_policies')
        g.custom_command('show', 'show_apimgmt_products_policies')
    with self.command_group('apimgmt products policies', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_products_policies')
        g.custom_command('list', 'list_apimgmt_products_policies')
    with self.command_group('apimgmt properties', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_properties')
        g.custom_command('update', 'update_apimgmt_properties')
        g.custom_command('delete', 'delete_apimgmt_properties')
        g.custom_command('list', 'list_apimgmt_properties')
        g.custom_command('show', 'show_apimgmt_properties')
    with self.command_group('apimgmt properties', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_properties')
        g.custom_command('list', 'list_apimgmt_properties')
    with self.command_group('apimgmt quotas', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_quotas')
    with self.command_group('apimgmt quotas periods', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_quotas_periods')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt')
    with self.command_group('apimgmt subscriptions', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_subscriptions')
        g.custom_command('update', 'update_apimgmt_subscriptions')
        g.custom_command('delete', 'delete_apimgmt_subscriptions')
        g.custom_command('list', 'list_apimgmt_subscriptions')
        g.custom_command('show', 'show_apimgmt_subscriptions')
    with self.command_group('apimgmt subscriptions', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_subscriptions')
        g.custom_command('show', 'show_apimgmt_subscriptions')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt')
    with self.command_group('apimgmt tenant', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_tenant')
    with self.command_group('apimgmt tenant', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_tenant')
    with self.command_group('apimgmt tenant', apimgmt_sdk, client_factory=cf_apimgmt) as g:
    with self.command_group('apimgmt users', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_users')
        g.custom_command('update', 'update_apimgmt_users')
        g.custom_command('delete', 'delete_apimgmt_users')
        g.custom_command('list', 'list_apimgmt_users')
        g.custom_command('show', 'show_apimgmt_users')
    with self.command_group('apimgmt users', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_users')
        g.custom_command('list', 'list_apimgmt_users')
    with self.command_group('apimgmt users', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_users')
    with self.command_group('apimgmt users', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_users')
    with self.command_group('apimgmt users', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('list', 'list_apimgmt_users')
    with self.command_group('apimgmt apis', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('show', 'show_apimgmt_apis')