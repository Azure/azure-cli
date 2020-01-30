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
