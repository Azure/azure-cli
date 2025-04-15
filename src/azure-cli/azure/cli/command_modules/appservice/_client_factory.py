# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=inconsistent-return-statements
def ex_handler_factory(creating_plan=False, no_throw=False):
    def _polish_bad_errors(ex):
        import json
        from knack.util import CLIError
        try:
            detail = json.loads(ex.response.text)['Message']
            if creating_plan:
                if 'Requested features are not supported in region' in detail:
                    detail = ("Selected plan is not supported in current region. " +
                              "Original error: " + detail)
            ex = CLIError(detail)
        except Exception:  # pylint: disable=broad-except
            pass
        if no_throw:
            return ex
        raise ex
    return _polish_bad_errors


def web_client_factory(cli_ctx, api_version=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_APPSERVICE, api_version=api_version)


def dns_client_factory(cli_ctx, api_version=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS, api_version=api_version)


def providers_client_factory(cli_ctx):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).providers


def customlocation_client_factory(cli_ctx, api_version=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CUSTOMLOCATION, api_version=api_version)


def appcontainers_client_factory(cli_ctx, api_version=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_APPCONTAINERS, api_version=api_version)


def cf_plans(cli_ctx, _):
    return web_client_factory(cli_ctx).app_service_plans


def cf_webapps(cli_ctx, _):
    return web_client_factory(cli_ctx).web_apps


def cf_providers(cli_ctx, _):
    return web_client_factory(cli_ctx).provider  # pylint: disable=no-member


def cf_web_client(cli_ctx, _):
    return web_client_factory(cli_ctx)
