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


    with self.command_group('apimgmt api', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api')
        g.custom_command('update', 'update_apimgmt_api')
        g.custom_command('delete', 'delete_apimgmt_api')
        g.custom_command('list', 'list_apimgmt_api')
        g.custom_command('show', 'show_apimgmt_api')
    with self.command_group('apimgmt api release', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_release')
        g.custom_command('update', 'update_apimgmt_api_release')
        g.custom_command('delete', 'delete_apimgmt_api_release')
        g.custom_command('list', 'list_apimgmt_api_release')
        g.custom_command('show', 'show_apimgmt_api_release')
    with self.command_group('apimgmt api operation', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_operation')
        g.custom_command('update', 'update_apimgmt_api_operation')
        g.custom_command('delete', 'delete_apimgmt_api_operation')
        g.custom_command('list', 'list_apimgmt_api_operation')
        g.custom_command('show', 'show_apimgmt_api_operation')
    with self.command_group('apimgmt api operation policy', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_operation_policy')
        g.custom_command('update', 'update_apimgmt_api_operation_policy')
        g.custom_command('delete', 'delete_apimgmt_api_operation_policy')
        g.custom_command('list', 'list_apimgmt_api_operation_policy')
        g.custom_command('show', 'show_apimgmt_api_operation_policy')
    with self.command_group('apimgmt tag', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_tag')
        g.custom_command('update', 'update_apimgmt_tag')
        g.custom_command('delete', 'delete_apimgmt_tag')
        g.custom_command('list', 'list_apimgmt_tag')
        g.custom_command('show', 'show_apimgmt_tag')
    with self.command_group('apimgmt api policy', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_policy')
        g.custom_command('update', 'update_apimgmt_api_policy')
        g.custom_command('delete', 'delete_apimgmt_api_policy')
        g.custom_command('list', 'list_apimgmt_api_policy')
        g.custom_command('show', 'show_apimgmt_api_policy')
    with self.command_group('apimgmt api schema', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_schema')
        g.custom_command('update', 'update_apimgmt_api_schema')
        g.custom_command('delete', 'delete_apimgmt_api_schema')
        g.custom_command('list', 'list_apimgmt_api_schema')
        g.custom_command('show', 'show_apimgmt_api_schema')
    with self.command_group('apimgmt api diagnostic', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_diagnostic')
        g.custom_command('update', 'update_apimgmt_api_diagnostic')
        g.custom_command('delete', 'delete_apimgmt_api_diagnostic')
        g.custom_command('list', 'list_apimgmt_api_diagnostic')
        g.custom_command('show', 'show_apimgmt_api_diagnostic')
    with self.command_group('apimgmt api issue', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_issue')
        g.custom_command('update', 'update_apimgmt_api_issue')
        g.custom_command('delete', 'delete_apimgmt_api_issue')
        g.custom_command('list', 'list_apimgmt_api_issue')
        g.custom_command('show', 'show_apimgmt_api_issue')
    with self.command_group('apimgmt api issue comment', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_issue_comment')
        g.custom_command('update', 'update_apimgmt_api_issue_comment')
        g.custom_command('delete', 'delete_apimgmt_api_issue_comment')
        g.custom_command('list', 'list_apimgmt_api_issue_comment')
        g.custom_command('show', 'show_apimgmt_api_issue_comment')
    with self.command_group('apimgmt api issue attachment', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_issue_attachment')
        g.custom_command('update', 'update_apimgmt_api_issue_attachment')
        g.custom_command('delete', 'delete_apimgmt_api_issue_attachment')
        g.custom_command('list', 'list_apimgmt_api_issue_attachment')
        g.custom_command('show', 'show_apimgmt_api_issue_attachment')
    with self.command_group('apimgmt api tagdescription', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_api_tagdescription')
        g.custom_command('update', 'update_apimgmt_api_tagdescription')
        g.custom_command('delete', 'delete_apimgmt_api_tagdescription')
        g.custom_command('list', 'list_apimgmt_api_tagdescription')
        g.custom_command('show', 'show_apimgmt_api_tagdescription')
    with self.command_group('apimgmt apiversionset', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_apiversionset')
        g.custom_command('update', 'update_apimgmt_apiversionset')
        g.custom_command('delete', 'delete_apimgmt_apiversionset')
        g.custom_command('list', 'list_apimgmt_apiversionset')
        g.custom_command('show', 'show_apimgmt_apiversionset')
    with self.command_group('apimgmt authorizationserver', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_authorizationserver')
        g.custom_command('update', 'update_apimgmt_authorizationserver')
        g.custom_command('delete', 'delete_apimgmt_authorizationserver')
        g.custom_command('list', 'list_apimgmt_authorizationserver')
        g.custom_command('show', 'show_apimgmt_authorizationserver')
    with self.command_group('apimgmt backend', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_backend')
        g.custom_command('update', 'update_apimgmt_backend')
        g.custom_command('delete', 'delete_apimgmt_backend')
        g.custom_command('list', 'list_apimgmt_backend')
        g.custom_command('show', 'show_apimgmt_backend')
    with self.command_group('apimgmt cache', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_cache')
        g.custom_command('update', 'update_apimgmt_cache')
        g.custom_command('delete', 'delete_apimgmt_cache')
        g.custom_command('list', 'list_apimgmt_cache')
        g.custom_command('show', 'show_apimgmt_cache')
    with self.command_group('apimgmt certificate', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_certificate')
        g.custom_command('update', 'update_apimgmt_certificate')
        g.custom_command('delete', 'delete_apimgmt_certificate')
        g.custom_command('list', 'list_apimgmt_certificate')
        g.custom_command('show', 'show_apimgmt_certificate')
    with self.command_group('apimgmt', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt')
        g.custom_command('update', 'update_apimgmt')
        g.custom_command('delete', 'delete_apimgmt')
        g.custom_command('list', 'list_apimgmt')
        g.custom_command('show', 'show_apimgmt')
    with self.command_group('apimgmt diagnostic', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_diagnostic')
        g.custom_command('update', 'update_apimgmt_diagnostic')
        g.custom_command('delete', 'delete_apimgmt_diagnostic')
        g.custom_command('list', 'list_apimgmt_diagnostic')
        g.custom_command('show', 'show_apimgmt_diagnostic')
    with self.command_group('apimgmt template', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_template')
        g.custom_command('update', 'update_apimgmt_template')
        g.custom_command('delete', 'delete_apimgmt_template')
        g.custom_command('list', 'list_apimgmt_template')
        g.custom_command('show', 'show_apimgmt_template')
    with self.command_group('apimgmt group', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_group')
        g.custom_command('update', 'update_apimgmt_group')
        g.custom_command('delete', 'delete_apimgmt_group')
        g.custom_command('list', 'list_apimgmt_group')
        g.custom_command('show', 'show_apimgmt_group')
    with self.command_group('apimgmt group user', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_group_user')
        g.custom_command('delete', 'delete_apimgmt_group_user')
        g.custom_command('list', 'list_apimgmt_group_user')
    with self.command_group('apimgmt identityprovider', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_identityprovider')
        g.custom_command('update', 'update_apimgmt_identityprovider')
        g.custom_command('delete', 'delete_apimgmt_identityprovider')
        g.custom_command('list', 'list_apimgmt_identityprovider')
        g.custom_command('show', 'show_apimgmt_identityprovider')
    with self.command_group('apimgmt logger', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_logger')
        g.custom_command('update', 'update_apimgmt_logger')
        g.custom_command('delete', 'delete_apimgmt_logger')
        g.custom_command('list', 'list_apimgmt_logger')
        g.custom_command('show', 'show_apimgmt_logger')
    with self.command_group('apimgmt notification', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_notification')
        g.custom_command('update', 'update_apimgmt_notification')
        g.custom_command('list', 'list_apimgmt_notification')
        g.custom_command('show', 'show_apimgmt_notification')
    with self.command_group('apimgmt notification recipientuser', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_notification_recipientuser')
        g.custom_command('update', 'update_apimgmt_notification_recipientuser')
        g.custom_command('delete', 'delete_apimgmt_notification_recipientuser')
        g.custom_command('list', 'list_apimgmt_notification_recipientuser')
    with self.command_group('apimgmt notification recipientemail', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_notification_recipientemail')
        g.custom_command('update', 'update_apimgmt_notification_recipientemail')
        g.custom_command('delete', 'delete_apimgmt_notification_recipientemail')
        g.custom_command('list', 'list_apimgmt_notification_recipientemail')
    with self.command_group('apimgmt openidconnectprovider', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_openidconnectprovider')
        g.custom_command('update', 'update_apimgmt_openidconnectprovider')
        g.custom_command('delete', 'delete_apimgmt_openidconnectprovider')
        g.custom_command('list', 'list_apimgmt_openidconnectprovider')
        g.custom_command('show', 'show_apimgmt_openidconnectprovider')
    with self.command_group('apimgmt policy', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_policy')
        g.custom_command('update', 'update_apimgmt_policy')
        g.custom_command('delete', 'delete_apimgmt_policy')
        g.custom_command('list', 'list_apimgmt_policy')
        g.custom_command('show', 'show_apimgmt_policy')
    with self.command_group('apimgmt portalsetting', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_portalsetting')
        g.custom_command('update', 'update_apimgmt_portalsetting')
        g.custom_command('show', 'show_apimgmt_portalsetting')
    with self.command_group('apimgmt portalsetting', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_portalsetting')
        g.custom_command('update', 'update_apimgmt_portalsetting')
        g.custom_command('show', 'show_apimgmt_portalsetting')
    with self.command_group('apimgmt portalsetting', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_portalsetting')
        g.custom_command('update', 'update_apimgmt_portalsetting')
        g.custom_command('show', 'show_apimgmt_portalsetting')
    with self.command_group('apimgmt product', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_product')
        g.custom_command('update', 'update_apimgmt_product')
        g.custom_command('delete', 'delete_apimgmt_product')
        g.custom_command('list', 'list_apimgmt_product')
        g.custom_command('show', 'show_apimgmt_product')
    with self.command_group('apimgmt product api', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_product_api')
        g.custom_command('update', 'update_apimgmt_product_api')
        g.custom_command('delete', 'delete_apimgmt_product_api')
        g.custom_command('list', 'list_apimgmt_product_api')
    with self.command_group('apimgmt product group', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_product_group')
        g.custom_command('update', 'update_apimgmt_product_group')
        g.custom_command('delete', 'delete_apimgmt_product_group')
        g.custom_command('list', 'list_apimgmt_product_group')
    with self.command_group('apimgmt product policy', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_product_policy')
        g.custom_command('update', 'update_apimgmt_product_policy')
        g.custom_command('delete', 'delete_apimgmt_product_policy')
        g.custom_command('list', 'list_apimgmt_product_policy')
        g.custom_command('show', 'show_apimgmt_product_policy')
    with self.command_group('apimgmt property', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_property')
        g.custom_command('update', 'update_apimgmt_property')
        g.custom_command('delete', 'delete_apimgmt_property')
        g.custom_command('list', 'list_apimgmt_property')
        g.custom_command('show', 'show_apimgmt_property')
    with self.command_group('apimgmt subscription', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_subscription')
        g.custom_command('update', 'update_apimgmt_subscription')
        g.custom_command('delete', 'delete_apimgmt_subscription')
        g.custom_command('list', 'list_apimgmt_subscription')
        g.custom_command('show', 'show_apimgmt_subscription')
    with self.command_group('apimgmt user', apimgmt_sdk, client_factory=cf_apimgmt) as g:
        g.custom_command('create', 'create_apimgmt_user')
        g.custom_command('update', 'update_apimgmt_user')
        g.custom_command('delete', 'delete_apimgmt_user')
        g.custom_command('list', 'list_apimgmt_user')
        g.custom_command('show', 'show_apimgmt_user')