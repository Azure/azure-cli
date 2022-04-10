# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals

from azure.cli.core.commands.parameters import (get_three_state_flag,
                                                get_enum_type,
                                                resource_group_name_type)
from azure.mgmt.security.models._security_center_enums import Enum69
from knack.arguments import CLIArgumentType
from ._validators import (validate_alert_status,
                          validate_auto_provisioning_toggle,
                          validate_pricing_tier,
                          validate_assessment_status_code)
from .actions import AppendBaselines, AppendBaseline

name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME', help='name of the resource to be fetched')
home_region_arg_type = CLIArgumentType(options_list=('--home-region', '-hr'), metavar='HOMEREGION', help='home region that was selected for the subscription')
location_arg_type = CLIArgumentType(options_list=('--location', '-l'), metavar='LOCATION', help='location of the resource')

# Alerts
alert_status_arg_type = CLIArgumentType(options_list=('--status'), metavar='STATUS', help='target status of the alert. possible values are "dismiss" and "activate"')


# Alerts Suppression Rules
suppression_rule_name_arg_type = CLIArgumentType(options_list=('--rule-name'), metavar='RULENAME', help='The unique name of the alerts suppression rule.')
suppression_alert_type_arg_type = CLIArgumentType(options_list=('--alert-type'), metavar='ALERTTYPE', help='Type of the alert to automatically suppress. For all alert types, use "*".')
suppression_reason_arg_type = CLIArgumentType(options_list=('--reason'), metavar='REASON', help='The reason for dismissing the alert.')
suppression_expiration_date_utc_arg_type = CLIArgumentType(options_list=('--expiration-date-utc'), metavar='EXPIRATIONDATEUTC', help='Expiration date of the rule, if value is not provided or provided as null this field will default to the maximum allowed expiration date.')
suppression_state_arg_type = CLIArgumentType(options_list=('--state'), metavar='STATE', help='Possible states of the rule. Possible values are "Enabled" and "Disabled".')
suppression_comment_arg_type = CLIArgumentType(options_list=('--comment'), metavar='COMMENT', help='Any comment regarding the rule.')
suppression_all_of_arg_type = CLIArgumentType(options_list=('--all-of'), metavar='ALLOF', help='The suppression conditions. Should be provided in a json array format.')

# Atp
storage_account_arg_type = CLIArgumentType(options_list=('--storage-account'), metavar='NAME', help='Name of an existing storage account.')

# Sql Vulnerability Assessment
va_sql_vm_resource_id_arg_type = CLIArgumentType(options_list=('--vm-resource-id'), metavar='VMRESOURCEID', help='Resource ID of the scanned machine. For On-Premise machines, please provide your workspace resource ID')
va_sql_workspace_id_arg_type = CLIArgumentType(options_list=('--workspace-id'), metavar='WORKSPACEID', help='The ID of the workspace connected to the scanned machine')
va_sql_server_name_arg_type = CLIArgumentType(options_list=('--server-name'), metavar='SERVERNAME', help='The name of the scanned server')
va_sql_database_name_arg_type = CLIArgumentType(options_list=('--database-name'), metavar='DATABASENAME', help='The name of the scanned database')
va_sql_scan_id_arg_type = CLIArgumentType(options_list=('--scan-id'), metavar='SCANID', help='The ID of the scan')
va_sql_rule_id_arg_type = CLIArgumentType(options_list=('--rule-id'), metavar='RULEID', help='The ID of the scanned rule. Format: "VAXXXX", where XXXX indicates the number of the rule')
va_sql_baseline_single_arg_type = CLIArgumentType(options_list=('--baseline', '-b'), metavar='BASELINE', help='Baseline records to be set. The following example will set a baseline with two records: --baseline line1_w1 line1_w2 line1_w3 --baseline line2_w1 line2_w2 line2_w3', action=AppendBaseline, nargs='+')
va_sql_baseline_multiple_arg_type = CLIArgumentType(options_list=('--baseline', '-b'), metavar='BASELINE', help='Baseline records to be set. The following example will set a baseline for two rules: --baseline rule=VA1111 line1_w1 line1_w2 --baseline rule=VA2222 line1_w1 line1_w2 line1_w3 --baseline rule=VA1111 line2_w1 line2_w2', action=AppendBaselines, nargs='+')
va_sql_vm_name_arg_type = CLIArgumentType(options_list=('--vm-name'), metavar='VMNAME', help='Provide the name of the machine, for On-Premise resources only')
va_sql_agent_id_arg_type = CLIArgumentType(options_list=('--agent-id'), metavar='AGENTID', help='Provide the ID of the agent on the scanned machine, for On-Premise resources only')
va_sql_vm_uuid_arg_type = CLIArgumentType(options_list=('--vm-uuid'), metavar='VMUUID', help='Provide the UUID of the scanned machine, for On-Premise resources only')

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

# IoT Solution
iot_solution_name_arg_type = CLIArgumentType(options_list=('--solution-name'), metavar='SOLUTIONNAME', help='Name of the IoT Security solution')
iot_solution_display_name_arg_type = CLIArgumentType(options_list=('--display-name'), metavar='DISPLAYNAME', help='Resource display name')
iot_solution_iot_hubs_arg_type = CLIArgumentType(options_list=('--iot-hubs'), metavar='IOTHUBS', help='IoT Hub resource IDs')

# Regulatory Compliance
regulatory_compliance_standard_name = CLIArgumentType(option_list=('--standard-name'), metave='STANDARDNAME', help='The compliance standard name')
regulatory_compliance_control_name = CLIArgumentType(option_list=('--control-name'), metave='CONTROLNAME', help='The compliance control name')

# Adaptive Network hardenings
adaptive_network_hardenings_resource_namespace = CLIArgumentType(option_list=('--resource_namespace'), metave='RESOURCENAMESPACE', help='The Namespace of the resource')
adaptive_network_hardenings_resource_resource_type = CLIArgumentType(option_list=('--resource_type'), metave='RESOURCETYPE', help='The type of the resource')
adaptive_network_hardenings_resource_resource_name = CLIArgumentType(option_list=('--resource_name'), metave='RESOURCENAME', help='Name of the resource')
adaptive_network_hardenings_resource_adaptive_network_hardenings_resource_name = CLIArgumentType(option_list=('--adaptive_network_hardenings_resource_name'), metave='ADAPTIVENETWORKHARDENINGSRESOURCENAME', help='Adaptive Network Hardening resource name')

# Adaptive Application Controls
adaptive_application_controls_group_name = CLIArgumentType(option_list=('--group-name'), metave='GROUPNAME', help='Name of an application control VM/server group')


# pylint: disable=too-many-branches
def load_arguments(self, _):
    for scope in ['alert',
                  'alerts-suppression-rule',
                  'atp',
                  'va sql',
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
                  'sub-assessment',
                  'iot-solution',
                  'iot-analytics',
                  'iot-alerts',
                  'iot-recommendations',
                  'regulatory-compliance-standards',
                  'regulatory-compliance-controls',
                  'regulatory-compliance-assessments',
                  'adaptive-application-controls',
                  'adaptive_network_hardenings',
                  'allowed_connections',
                  'secure-scores',
                  'secure-score-controls',
                  'secure-score-control-definitions',
                  'setting'
                  ]:
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
            c.argument(
                'vm_resource_id',
                arg_type=va_sql_vm_resource_id_arg_type)
            c.argument(
                'workspace_id',
                arg_type=va_sql_workspace_id_arg_type)
            c.argument(
                'server_name',
                arg_type=va_sql_server_name_arg_type)
            c.argument(
                'database_name',
                arg_type=va_sql_database_name_arg_type)
            c.argument(
                'vm_name',
                arg_type=va_sql_vm_name_arg_type)
            c.argument(
                'agent_id',
                arg_type=va_sql_agent_id_arg_type)
            c.argument(
                'vm_uuid',
                arg_type=va_sql_vm_uuid_arg_type)

    for scope in ['regulatory-compliance-controls']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'standard_name',
                arg_type=regulatory_compliance_standard_name)

    for scope in ['regulatory-compliance-assessments']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'standard_name',
                arg_type=regulatory_compliance_standard_name)
            c.argument(
                'control_name',
                arg_type=regulatory_compliance_control_name)

    for scope in ['alert update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'status',
                validator=validate_alert_status,
                arg_type=alert_status_arg_type)

    for scope in ['alerts-suppression-rule update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'rule_name',
                arg_type=suppression_rule_name_arg_type)
            c.argument(
                'alert_type',
                arg_type=suppression_alert_type_arg_type)
            c.argument(
                'reason',
                arg_type=suppression_reason_arg_type)
            c.argument(
                'expiration_date_utc',
                arg_type=suppression_expiration_date_utc_arg_type)
            c.argument(
                'state',
                arg_type=suppression_state_arg_type)
            c.argument(
                'comment',
                arg_type=suppression_comment_arg_type)
            c.argument(
                'all_of',
                arg_type=suppression_all_of_arg_type)

    for scope in ['alerts-suppression-rule show']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'rule_name',
                arg_type=suppression_rule_name_arg_type)

    for scope in ['alerts-suppression-rule delete']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'rule_name',
                arg_type=suppression_rule_name_arg_type)

    for scope in ['auto-provisioning-setting update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'auto_provision',
                validator=validate_auto_provisioning_toggle,
                arg_type=auto_provisioning_auto_provision_arg_type)

    for scope in ['atp storage update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('is_enabled', help='Enable or disable Advanced Threat Protection for a received storage account.', arg_type=get_three_state_flag())

    for scope in ['va sql scans show',
                  'va sql results']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('scan_id', arg_type=va_sql_scan_id_arg_type)

    for scope in ['va sql results show',
                  'va sql baseline show',
                  'va sql baseline delete',
                  'va sql baseline update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('rule_id', arg_type=va_sql_rule_id_arg_type)

    for scope in ['va sql baseline update']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('baseline', arg_type=va_sql_baseline_single_arg_type)

    for scope in ['va sql baseline set']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('baseline', arg_type=va_sql_baseline_multiple_arg_type)

    for scope in ['va sql baseline update',
                  'va sql baseline set']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('baseline_latest', options_list=('--latest'), metavar='BASELINE', help='Use this argument without parameters to set baseline upon latest scan results', arg_type=get_three_state_flag())

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

    for scope in ['adaptive_network_hardenings']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'resource_namespace',
                arg_type=adaptive_network_hardenings_resource_namespace)
            c.argument(
                'resource_type',
                arg_type=adaptive_network_hardenings_resource_resource_type)
            c.argument(
                'resource_name',
                arg_type=adaptive_network_hardenings_resource_resource_name)
            c.argument(
                'adaptive_network_hardenings_resource_name',
                arg_type=adaptive_network_hardenings_resource_adaptive_network_hardenings_resource_name)

    for scope in ['iot-solution']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'iot_solution_name',
                arg_type=iot_solution_name_arg_type)
            c.argument(
                'iot_solution_display_name',
                arg_type=iot_solution_display_name_arg_type)
            c.argument(
                'iot_solution_iot_hubs',
                arg_type=iot_solution_iot_hubs_arg_type)

    for scope in ['iot-analytics']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'iot_solution_name',
                arg_type=iot_solution_name_arg_type)

    for scope in ['iot-alerts']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'iot_solution_name',
                arg_type=iot_solution_name_arg_type)

    for scope in ['iot-recommendations']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'iot_solution_name',
                arg_type=iot_solution_name_arg_type)

    for scope in ['adaptive-application-controls']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument(
                'group_name',
                arg_type=adaptive_application_controls_group_name)

    for scope in ['setting']:
        with self.argument_context('security {}'.format(scope)) as c:
            c.argument('setting_name', options_list=['--name', '-n'], help='The name of the setting', arg_type=get_enum_type(Enum69))
            c.argument('enabled', help='Enable or disable the setting status.', arg_type=get_three_state_flag())
