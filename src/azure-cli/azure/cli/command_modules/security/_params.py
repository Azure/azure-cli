# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import (get_three_state_flag,
                                                resource_group_name_type)
from knack.arguments import CLIArgumentType
from ._validators import (validate_alert_status,
                          validate_auto_provisioning_toggle,
                          validate_pricing_tier)

name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME', help='name of the resource to be fetched')
home_region_arg_type = CLIArgumentType(options_list=('--home-region', '-hr'), metavar='HOMEREGION', help='home region that was selected for the subscription')
location_arg_type = CLIArgumentType(options_list=('--location', '-l'), metavar='LOCATION', help='location of the resource')

# Alerts
alert_status_arg_type = CLIArgumentType(options_list=('--status'), metavar='STATUS', help='target status of the alert. possible values are "dismiss" and "activate"')

# Atp
storage_account_arg_type = CLIArgumentType(options_list=('--storage-account'), metavar='NAME', help='Name of an existing storage account.')

# Auto Provisioning
auto_provisioning_auto_provision_arg_type = CLIArgumentType(options_list=('--auto-provision'), metavar='AUTOPROVISION', help='Automatic provisioning toggle. possible values are "On" or "Off"')

# Contacts
contact_email_arg_type = CLIArgumentType(options_list=('--email'), metavar='EMAIL', help='E-mail of the security contact')
contact_phone_arg_type = CLIArgumentType(options_list=('--phone'), metavar='PHONE', help='Phone of the security contact')
contact_alert_notifications_arg_type = CLIArgumentType(options_list=('--alert-notifications'), metavar='ALERTNOTIFICATIONS', help='Whether to send mail notifications to the security contacts')
contact_alerts_admins_arg_type = CLIArgumentType(options_list=('--alerts-admins'), metavar='ALERTADMINS', help='Whether to send mail notifications to the subscription administrators')

# Pricing
pricing_tier_arg_type = CLIArgumentType(options_list=('--tier'), metavar='TIER', help='pricing tier type')

# Workspace settings
workspace_setting_target_workspace_arg_type = CLIArgumentType(options_list=('--target-workspace'), metavar='TARGETWORKSPACE', help='An ID of the workspace resource that will hold the security data')


def load_arguments(self, _):
    for scope in ['alert',
                  'atp',
                  'task',
                  'setting',
                  'contact',
                  'auto-provisioning-setting',
                  'discovered-security-solution',
                  'external-security-solution',
                  'jit-policy',
                  'location',
                  'pricing',
                  'topology',
                  'workspace-setting']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'resource_group_name',
                options_list=['--resource-group', '-g'],
                arg_type=resource_group_name_type)
            c.argument(
                'resource_name',
                arg_type=name_arg_type)
            c.argument(
                'location',
                arg_type=location_arg_type)
            c.argument(
                'storage_account_name',
                arg_type=storage_account_arg_type)

    for scope in ['alert update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'status',
                validator=validate_alert_status,
                arg_type=alert_status_arg_type)

    for scope in ['auto-provisioning-setting update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'auto_provision',
                validator=validate_auto_provisioning_toggle,
                arg_type=auto_provisioning_auto_provision_arg_type)

    for scope in ['atp storage update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('is_enabled', help='Enable or disable Advanced Threat Protection for a received storage account.', arg_type=get_three_state_flag())

    for scope in ['contact create']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'email',
                arg_type=contact_email_arg_type)
            c.argument(
                'phone',
                arg_type=contact_phone_arg_type)
            c.argument(
                'alert_notifications',
                arg_type=contact_alert_notifications_arg_type)
            c.argument(
                'alerts_admins',
                arg_type=contact_alerts_admins_arg_type)

    for scope in ['pricing create']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'tier',
                validator=validate_pricing_tier,
                arg_type=pricing_tier_arg_type)

    for scope in ['workspace-setting create']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'target_workspace',
                arg_type=workspace_setting_target_workspace_arg_type)
