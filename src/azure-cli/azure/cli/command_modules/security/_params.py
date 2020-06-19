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
                          validate_pricing_tier,
                          validate_assessment_status_code)

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

# Assessments
assessment_assessed_resource_id_arg_type = CLIArgumentType(options_list=('--assessed-resource-id'), metavar='ASSESSEDRESOURCEID', help='The target resource for this assessment')
assessment_additional_data_arg_type = CLIArgumentType(options_list=('--additional-data'), metavar='ADDITIONALDATA', help='Data that is attached to the assessment result for better investigations or status clarity')
assessment_status_code_arg_type = CLIArgumentType(options_list=('--status-code'), metavar='STATUSCODE', help='Progremmatic code for the result of the assessment. can be "Healthy", "Unhealthy" or "NotApplicable"')
assessment_status_cause_arg_type = CLIArgumentType(options_list=('--status-cause'), metavar='STATUSCAUSE', help='Progremmatic code for the cause of the assessment result')
assessment_status_description_arg_type = CLIArgumentType(options_list=('--status-description'), metavar='STATUSDESCRIPTION', help='Human readable description of the cause of the assessment result')

# Assessment metadata
assessment_metadata_display_name_arg_type = CLIArgumentType(options_list=('--display-name'), metavar='DISPLAYNAME', help='Human readable title for this object')
assessment_metadata_remediation_description_arg_type = CLIArgumentType(options_list=('--remediation-description'), metavar='REMEDIATIONDESCRIPTION', help='Detailed string that will help users to understand the different ways to mitigate or fix the security issue')
assessment_metadata_description_arg_type = CLIArgumentType(options_list=('--description'), metavar='DESCRIPTION', help='Detailed string that will help users to understand the assessment and how it is calculated')
assessment_metadata_severity_arg_type = CLIArgumentType(options_list=('--severity'), metavar='SEVERITY', help='Indicates the importance of the security risk if the assessment is unhealthy')

# Sub Assessment
sub_assessment_assessment_name_arg_type = CLIArgumentType(options_list=('--assessment-name'), metavar='ASSESSMENTNAME', help='Name of the assessment resource')


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
                  'workspace-setting',
                  'assessment',
                  'assessment-metadata',
                  'sub-assessment']:
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

    for scope in ['assessment']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'assessed_resource_id',
                arg_type=assessment_assessed_resource_id_arg_type)

    for scope in ['assessment create']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'additional_data',
                arg_type=assessment_additional_data_arg_type)
            c.argument(
                'status_code',
                validator=validate_assessment_status_code,
                arg_type=assessment_status_code_arg_type)
            c.argument(
                'status_cause',
                arg_type=assessment_status_cause_arg_type)
            c.argument(
                'status_description',
                arg_type=assessment_status_description_arg_type)

    for scope in ['assessment-metadata create']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'display_name',
                arg_type=assessment_metadata_display_name_arg_type)
            c.argument(
                'remediation_description',
                arg_type=assessment_metadata_remediation_description_arg_type)
            c.argument(
                'description',
                arg_type=assessment_metadata_description_arg_type)
            c.argument(
                'severity',
                arg_type=assessment_metadata_severity_arg_type)

    for scope in ['sub-assessment']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'assessed_resource_id',
                arg_type=assessment_assessed_resource_id_arg_type)
            c.argument(
                'assessment_name',
                arg_type=sub_assessment_assessment_name_arg_type)
