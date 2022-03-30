# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _cf_security(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.security import SecurityCenter

    return get_mgmt_service_client(cli_ctx, SecurityCenter, asc_location="centralus")


def cf_security_tasks(cli_ctx, _):
    # do not return cli_ctx.tasks for home region compatibility
    return _cf_security(cli_ctx)


def cf_security_alerts(cli_ctx, _):
    return _cf_security(cli_ctx).alerts


def cf_security_settings(cli_ctx, _):
    return _cf_security(cli_ctx).settings


def cf_security_contacts(cli_ctx, _):
    return _cf_security(cli_ctx).security_contacts


def cf_security_auto_provisioning_settings(cli_ctx, _):
    return _cf_security(cli_ctx).auto_provisioning_settings


def cf_security_discovered_security_solutions(cli_ctx, _):
    # do not return cli_ctx.discovered_security_solutions for home region compatibility
    return _cf_security(cli_ctx)


def cf_security_external_security_solutions(cli_ctx, _):
    # do not return cli_ctx.external_security_solutions for home region compatibility
    return _cf_security(cli_ctx)


def cf_security_jit_network_access_policies(cli_ctx, _):
    return _cf_security(cli_ctx).jit_network_access_policies


def cf_security_locations(cli_ctx, _):
    return _cf_security(cli_ctx).locations


def cf_security_pricings(cli_ctx, _):
    return _cf_security(cli_ctx).pricings


def cf_security_topology(cli_ctx, _):
    # do not return cli_ctx.topology for home region compatibility
    return _cf_security(cli_ctx)


def cf_security_workspace_settings(cli_ctx, _):
    return _cf_security(cli_ctx).workspace_settings


def cf_security_advanced_threat_protection(cli_ctx, _):
    return _cf_security(cli_ctx).advanced_threat_protection


def cf_sql_vulnerability_assessment_scans(cli_ctx, _):
    return _cf_security(cli_ctx).sql_vulnerability_assessment_scans


def cf_sql_vulnerability_assessment_results(cli_ctx, _):
    return _cf_security(cli_ctx).sql_vulnerability_assessment_scan_results


def cf_sql_vulnerability_assessment_baseline(cli_ctx, _):
    return _cf_security(cli_ctx).sql_vulnerability_assessment_baseline_rules


def cf_security_assessment(cli_ctx, _):
    return _cf_security(cli_ctx).assessments


def cf_security_assessment_metadata(cli_ctx, _):
    return _cf_security(cli_ctx).assessments_metadata


def cf_security_sub_assessment(cli_ctx, _):
    return _cf_security(cli_ctx).sub_assessments


def cf_security_iot_solution(cli_ctx, _):
    return _cf_security(cli_ctx).iot_security_solution


def cf_security_iot_analytics(cli_ctx, _):
    return _cf_security(cli_ctx).iot_security_solution_analytics


def cf_security_iot_alerts(cli_ctx, _):
    return _cf_security(cli_ctx).iot_security_solutions_analytics_aggregated_alert


def cf_security_iot_recommendations(cli_ctx, _):
    return _cf_security(cli_ctx).iot_security_solutions_analytics_recommendation


def cf_security_regulatory_compliance_standards(cli_ctx, _):
    return _cf_security(cli_ctx).regulatory_compliance_standards


def cf_security_regulatory_compliance_control(cli_ctx, _):
    return _cf_security(cli_ctx).regulatory_compliance_controls


def cf_security_regulatory_compliance_assessment(cli_ctx, _):
    return _cf_security(cli_ctx).regulatory_compliance_assessments


def cf_security_adaptive_application_controls(cli_ctx, _):
    # do not return cli_ctx.adaptive_application_controls for home region compatibility
    return _cf_security(cli_ctx).adaptive_application_controls


def cf_security_adaptive_network_hardenings(cli_ctx, _):
    # do not return cli_ctx.adaptive_network_hardenings for home region compatibility
    return _cf_security(cli_ctx).adaptive_network_hardenings


def cf_security_allowed_connections(cli_ctx, _):
    # do not return cli_ctx.allowed_connections for home region compatibility
    return _cf_security(cli_ctx)


def cf_security_secure_scores(cli_ctx, _):
    return _cf_security(cli_ctx).secure_scores


def cf_security_secure_score_controls(cli_ctx, _):
    return _cf_security(cli_ctx).secure_score_controls


def cf_security_secure_score_control_definitions(cli_ctx, _):
    return _cf_security(cli_ctx).secure_score_control_definitions

def cf_security_security_solutions(cli_ctx, _):
    return _cf_security(cli_ctx)