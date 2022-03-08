# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (cf_security_tasks,
                              cf_security_alerts,
                              cf_security_settings,
                              cf_security_contacts,
                              cf_security_auto_provisioning_settings,
                              cf_security_discovered_security_solutions,
                              cf_security_external_security_solutions,
                              cf_security_jit_network_access_policies,
                              cf_security_locations,
                              cf_security_pricings,
                              cf_security_topology,
                              cf_security_workspace_settings,
                              cf_security_advanced_threat_protection,
                              cf_sql_vulnerability_assessment_scans,
                              cf_sql_vulnerability_assessment_results,
                              cf_sql_vulnerability_assessment_baseline,
                              cf_security_assessment,
                              cf_security_assessment_metadata,
                              cf_security_sub_assessment,
                              cf_security_adaptive_application_controls,
                              cf_security_adaptive_network_hardenings,
                              cf_security_allowed_connections,
                              cf_security_iot_solution,
                              cf_security_iot_analytics,
                              cf_security_iot_alerts,
                              cf_security_iot_recommendations,
                              cf_security_regulatory_compliance_standards,
                              cf_security_regulatory_compliance_control,
                              cf_security_regulatory_compliance_assessment,
                              cf_security_secure_scores,
                              cf_security_secure_score_controls,
                              cf_security_secure_score_control_definitions)


# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
def load_command_table(self, _):

    security_secure_scores_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SecureScoresOperations.{}',
        client_factory=cf_security_secure_scores
    )

    security_secure_score_controls_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SecureScoreControlsOperations.{}',
        client_factory=cf_security_secure_score_controls
    )

    security_secure_score_control_definitions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SecureScoreControlDefinitionsOperations.{}',
        client_factory=cf_security_secure_score_control_definitions
    )

    security_regulatory_compliance_standards_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#RegulatoryComplianceStandardsOperations.{}',
        client_factory=cf_security_regulatory_compliance_standards
    )

    security_regulatory_compliance_controls_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#RegulatoryComplianceControlsOperations.{}',
        client_factory=cf_security_regulatory_compliance_control
    )

    security_regulatory_compliance_assessment_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#RegulatoryComplianceAssessmentsOperations.{}',
        client_factory=cf_security_regulatory_compliance_assessment
    )

    security_tasks_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#TasksOperations.{}',
        client_factory=cf_security_tasks,
        operation_group='security_tasks'
    )

    security_alerts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AlertsOperations.{}',
        client_factory=cf_security_alerts,
        operation_group='security_alerts'
    )

    security_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SettingsOperations.{}',
        client_factory=cf_security_settings,
        operation_group='security_settings'
    )

    security_contacts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SecurityContactsOperations.{}',
        client_factory=cf_security_contacts,
        operation_group='security_contacts'
    )

    security_auto_provisioning_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AutoProvisioningSettingsOperations.{}',
        client_factory=cf_security_auto_provisioning_settings,
        operation_group='security_auto_provisioning_settings'
    )

    security_discovered_security_solutions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#DiscoveredSecuritySolutionsOperations.{}',
        client_factory=cf_security_discovered_security_solutions,
        operation_group='security_discovered_security_solutions'
    )

    security_external_security_solutions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#ExternalSecuritySolutionsOperations.{}',
        client_factory=cf_security_external_security_solutions,
        operation_group='security_external_security_solutions'
    )

    security_jit_network_access_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#JitNetworkAccessPoliciesOperations.{}',
        client_factory=cf_security_jit_network_access_policies,
        operation_group='security_jit_network_access_policies'
    )

    security_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#LocationsOperations.{}',
        client_factory=cf_security_locations,
        operation_group='security_locations'
    )

    security_pricings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#PricingsOperations.{}',
        client_factory=cf_security_pricings,
        operation_group='security_pricings'
    )

    security_topology_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#TopologyOperations.{}',
        client_factory=cf_security_topology,
        operation_group='security_topology'
    )

    security_workspace_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#WorkspaceSettingsOperations.{}',
        client_factory=cf_security_workspace_settings,
        operation_group='security_workspace_settings'
    )

    security_advanced_threat_protection_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AdvancedThreatProtectionOperations.{}',
        client_factory=cf_security_advanced_threat_protection
    )

    security_sql_vulnerability_assessment_scans_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SqlVulnerabilityAssessmentScansOperations.{}',
        client_factory=cf_sql_vulnerability_assessment_scans
    )

    security_sql_vulnerability_assessment_results_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SqlVulnerabilityAssessmentScanResultsOperations.{}',
        client_factory=cf_sql_vulnerability_assessment_results
    )

    security_sql_vulnerability_assessment_baseline_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SqlVulnerabilityAssessmentBaselineRulesOperations.{}',
        client_factory=cf_sql_vulnerability_assessment_baseline
    )

    security_assessment_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AssessmentsOperations.{}',
        client_factory=cf_security_assessment
    )

    security_assessment_metadata_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AssessmentMetadataOperations.{}',
        client_factory=cf_security_assessment_metadata
    )

    security_sub_assessment_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#SubAssessmentsOperations.{}',
        client_factory=cf_security_sub_assessment
    )

    security_adaptive_application_controls_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AdaptiveApplicationControlsOperations.{}',
        client_factory=cf_security_adaptive_application_controls,
        operation_group='cf_security_adaptive_application_controls'
    )

    security_adaptive_network_hardenings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AdaptiveNetworkhardeningsOperations.{}',
        client_factory=cf_security_adaptive_network_hardenings,
        operation_group='security_adaptive_network_hardenings'
    )

    security_allowed_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#AllowedConnectionsOperations.{}',
        client_factory=cf_security_allowed_connections,
        operation_group='security_allowed_connections'
    )

    security_iot_solution_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#IotSolutionOperations.{}',
        client_factory=cf_security_iot_solution
    )

    security_iot_analytics_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#IotAnalyticsOperations.{}',
        client_factory=cf_security_iot_analytics
    )

    security_iot_alerts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#IotAlertsOperations.{}',
        client_factory=cf_security_iot_alerts
    )

    security_iot_recommendations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.security.operations#IotRecommendationsOperations.{}',
        client_factory=cf_security_iot_recommendations
    )

    with self.command_group('security secure-scores',
                            security_secure_scores_sdk,
                            client_factory=cf_security_secure_scores) as g:
        g.custom_command('list', 'list_secure_scores')
        g.custom_show_command('show', 'get_secure_score')

    with self.command_group('security secure-score-controls',
                            security_secure_score_controls_sdk,
                            client_factory=cf_security_secure_score_controls) as g:
        g.custom_command('list', 'list_secure_score_controls')
        g.custom_show_command('list_by_score', 'list_by_score')

    with self.command_group('security secure-score-control-definitions',
                            security_secure_score_control_definitions_sdk,
                            client_factory=cf_security_secure_score_control_definitions) as g:
        g.custom_command('list', 'list_secure_score_control_definitions')

    with self.command_group('security regulatory-compliance-standards',
                            security_regulatory_compliance_standards_sdk,
                            client_factory=cf_security_regulatory_compliance_standards) as g:
        g.custom_command('list', 'list_regulatory_compliance_standards')
        g.custom_show_command('show', 'get_regulatory_compliance_standard')

    with self.command_group('security regulatory-compliance-controls',
                            security_regulatory_compliance_controls_sdk,
                            client_factory=cf_security_regulatory_compliance_control) as g:
        g.custom_command('list', 'list_regulatory_compliance_controls')
        g.custom_show_command('show', 'get_regulatory_compliance_control')

    with self.command_group('security regulatory-compliance-assessments',
                            security_regulatory_compliance_assessment_sdk,
                            client_factory=cf_security_regulatory_compliance_assessment) as g:
        g.custom_command('list', 'list_regulatory_compliance_assessments')
        g.custom_show_command('show', 'get_regulatory_compliance_assessment')

    with self.command_group('security task',
                            security_tasks_sdk,
                            client_factory=cf_security_tasks) as g:
        g.custom_command('list', 'list_security_tasks')
        g.custom_show_command('show', 'get_security_task')

    with self.command_group('security atp storage',
                            security_advanced_threat_protection_sdk,
                            client_factory=cf_security_advanced_threat_protection) as g:
        g.custom_show_command('show', 'get_atp_setting')
        g.custom_command('update', 'update_atp_setting')

    with self.command_group('security va sql scans',
                            security_sql_vulnerability_assessment_scans_sdk,
                            client_factory=cf_sql_vulnerability_assessment_scans) as g:
        g.custom_show_command('show', 'get_va_sql_scan')
        g.custom_command('list', 'list_va_sql_scans')

    with self.command_group('security va sql results',
                            security_sql_vulnerability_assessment_results_sdk,
                            client_factory=cf_sql_vulnerability_assessment_results) as g:
        g.custom_show_command('show', 'get_va_sql_result')
        g.custom_command('list', 'list_va_sql_results')

    with self.command_group('security va sql baseline',
                            security_sql_vulnerability_assessment_baseline_sdk,
                            client_factory=cf_sql_vulnerability_assessment_baseline) as g:
        g.custom_show_command('show', 'get_va_sql_baseline')
        g.custom_command('list', 'list_va_sql_baseline')
        g.custom_command('delete', 'delete_va_sql_baseline')
        g.custom_command('update', 'update_va_sql_baseline')
        g.custom_command('set', 'set_va_sql_baseline')

    with self.command_group('security alert',
                            security_alerts_sdk,
                            client_factory=cf_security_alerts) as g:
        g.custom_command('list', 'list_security_alerts')
        g.custom_show_command('show', 'get_security_alert')
        g.custom_command('update', 'update_security_alert')

    with self.command_group('security setting',
                            security_settings_sdk,
                            client_factory=cf_security_settings) as g:
        g.custom_command('list', 'list_security_settings')
        g.custom_show_command('show', 'get_security_setting')
        g.custom_command('update', 'update_security_setting')

    with self.command_group('security contact',
                            security_contacts_sdk,
                            client_factory=cf_security_contacts) as g:
        g.custom_command('list', 'list_security_contacts')
        g.custom_show_command('show', 'get_security_contact')
        g.custom_command('create', 'create_security_contact')
        g.custom_command('delete', 'delete_security_contact')

    with self.command_group('security auto-provisioning-setting',
                            security_auto_provisioning_settings_sdk,
                            client_factory=cf_security_auto_provisioning_settings) as g:
        g.custom_command('list', 'list_security_auto_provisioning_settings')
        g.custom_show_command('show', 'get_security_auto_provisioning_setting')
        g.custom_command('update', 'update_security_auto_provisioning_setting')

    with self.command_group('security discovered-security-solution',
                            security_discovered_security_solutions_sdk,
                            client_factory=cf_security_discovered_security_solutions) as g:
        g.custom_command('list', 'list_security_discovered_security_solutions')
        g.custom_show_command('show', 'get_security_discovered_security_solution')

    with self.command_group('security external-security-solution',
                            security_external_security_solutions_sdk,
                            client_factory=cf_security_external_security_solutions) as g:
        g.custom_command('list', 'list_security_external_security_solutions')
        g.custom_show_command('show', 'get_security_external_security_solution')

    with self.command_group('security jit-policy',
                            security_jit_network_access_policies_sdk,
                            client_factory=cf_security_jit_network_access_policies) as g:
        g.custom_command('list', 'list_security_jit_network_access_policies')
        g.custom_show_command('show', 'get_security_jit_network_access_policy')

    with self.command_group('security location',
                            security_locations_sdk,
                            client_factory=cf_security_locations) as g:
        g.custom_command('list', 'list_security_locations')
        g.custom_show_command('show', 'get_security_location')

    with self.command_group('security pricing',
                            security_pricings_sdk,
                            client_factory=cf_security_pricings) as g:
        g.custom_command('list', 'list_security_pricings')
        g.custom_show_command('show', 'get_security_pricing')
        g.custom_command('create', 'create_security_pricing')

    with self.command_group('security topology',
                            security_topology_sdk,
                            client_factory=cf_security_topology) as g:
        g.custom_command('list', 'list_security_topology')
        g.custom_show_command('show', 'get_security_topology')

    with self.command_group('security workspace-setting',
                            security_workspace_settings_sdk,
                            client_factory=cf_security_workspace_settings) as g:
        g.custom_command('list', 'list_security_workspace_settings')
        g.custom_show_command('show', 'get_security_workspace_setting')
        g.custom_command('create', 'create_security_workspace_setting')
        g.custom_command('delete', 'delete_security_workspace_setting')

    with self.command_group('security assessment',
                            security_assessment_sdk,
                            client_factory=cf_security_assessment) as g:
        g.custom_command('list', 'list_security_assessments')
        g.custom_show_command('show', 'get_security_assessment')
        g.custom_command('create', 'create_security_assessment')
        g.custom_command('delete', 'delete_security_assessment')

    with self.command_group('security assessment-metadata',
                            security_assessment_metadata_sdk,
                            client_factory=cf_security_assessment_metadata) as g:
        g.custom_command('list', 'list_security_assessment_metadata')
        g.custom_show_command('show', 'get_security_assessment_metadata')
        g.custom_command('create', 'create_security_assessment_metadata')
        g.custom_command('delete', 'delete_security_assessment_metadata')

    with self.command_group('security sub-assessment',
                            security_sub_assessment_sdk,
                            client_factory=cf_security_sub_assessment) as g:
        g.custom_command('list', 'list_security_sub_assessments')
        g.custom_show_command('show', 'get_security_sub_assessment')

    with self.command_group('security adaptive-application-controls',
                            security_adaptive_application_controls_sdk,
                            client_factory=cf_security_adaptive_application_controls) as g:
        g.custom_command('list', 'list_security_adaptive_application_controls')
        g.custom_show_command('show', 'get_security_adaptive_application_controls')

    with self.command_group('security adaptive_network_hardenings',
                            security_adaptive_network_hardenings_sdk,
                            client_factory=cf_security_adaptive_network_hardenings) as g:
        g.custom_show_command('show', 'get_security_adaptive_network_hardenings')
        g.custom_command('list', 'list_security_adaptive_network_hardenings')

    with self.command_group('security allowed_connections',
                            security_allowed_connections_sdk,
                            client_factory=cf_security_allowed_connections) as g:
        g.custom_command('list', 'list_security_allowed_connections')
        g.custom_show_command('show', 'get_security_allowed_connections')

    with self.command_group('security iot-solution',
                            security_iot_solution_sdk,
                            client_factory=cf_security_iot_solution) as g:
        g.custom_command('list', 'list_security_iot_solution')
        g.custom_show_command('show', 'show_security_iot_solution')
        g.custom_command('create', 'create_security_iot_solution')
        g.custom_command('delete', 'delete_security_iot_solution')
        g.custom_command('update', 'update_security_iot_solution')

    with self.command_group('security iot-analytics',
                            security_iot_analytics_sdk,
                            client_factory=cf_security_iot_analytics) as g:
        g.custom_command('list', 'list_security_iot_analytics')
        g.custom_show_command('show', 'show_security_iot_analytics')

    with self.command_group('security iot-alerts',
                            security_iot_alerts_sdk,
                            client_factory=cf_security_iot_alerts) as g:
        g.custom_command('list', 'list_security_iot_alerts')
        g.custom_show_command('show', 'show_security_iot_alerts')
        g.custom_command('delete', 'dismiss_security_iot_alerts')

    with self.command_group('security iot-recommendations',
                            security_iot_recommendations_sdk,
                            client_factory=cf_security_iot_recommendations) as g:
        g.custom_command('list', 'list_security_iot_recommendations')
        g.custom_show_command('show', 'show_security_iot_recommendations')

    with self.command_group('security'):
        pass
