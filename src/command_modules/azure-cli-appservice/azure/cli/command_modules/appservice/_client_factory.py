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
                    detail = ("Plan with linux worker is not supported in current region. For " +
                              "supported regions, please refer to https://docs.microsoft.com/en-us/"
                              "azure/app-service-web/app-service-linux-intro")
                elif 'Not enough available reserved instance servers to satisfy' in detail:
                    detail = ("Plan with Linux worker can only be created in a group " +
                              "which has never contained a Windows worker, and vice versa. " +
                              "Please use a new resource group. Original error:" + detail)
            ex = CLIError(detail)
        except Exception:  # pylint: disable=broad-except
            pass
        if no_throw:
            return ex
        raise ex
    return _polish_bad_errors


def web_client_factory(cli_ctx, **_):
    from azure.mgmt.web import WebSiteManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, WebSiteManagementClient)


def cf_plans(cli_ctx, _):
    return web_client_factory(cli_ctx).app_service_plans


def cf_webapps(cli_ctx, _):
    return web_client_factory(cli_ctx).web_apps


def cf_providers(cli_ctx, _):
    return web_client_factory(cli_ctx).provider  # pylint: disable=no-member


def cf_web_client(cli_ctx, _):
    return web_client_factory(cli_ctx)
