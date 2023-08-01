# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import CLIInternalError


# pylint: disable=inconsistent-return-statements
def ex_handler_factory(no_throw=False):
    def _polish_bad_errors(ex):
        import json
        try:
            content = json.loads(ex.response.content)
            if 'message' in content:
                detail = content['message']
            elif 'Message' in content:
                detail = content['Message']

            ex = CLIInternalError(detail)
        except Exception:  # pylint: disable=broad-except
            pass
        if no_throw:
            return ex
        raise ex
    return _polish_bad_errors


def handle_raw_exception(e):
    import json

    stringErr = str(e)

    if "WorkloadProfileNameRequired" in stringErr:
        raise CLIInternalError("Workload profile name is required. Please provide --workload-profile-name.")

    if "Unknown properties Name in Microsoft.ContainerApps.WebApi.Views.Version20221101Preview.WorkloadProfile are not supported" in stringErr:
        raise CLIInternalError("Bad Request: Workload profile name is not yet supported in this region.")

    if "Error starting job" in stringErr:
        raise CLIInternalError("There was an error starting the job execution. Please check input parameters and try again.")

    if "{" in stringErr and "}" in stringErr:
        jsonError = stringErr[stringErr.index("{"):stringErr.rindex("}") + 1]
        jsonError = json.loads(jsonError)

        if 'error' in jsonError:
            jsonError = jsonError['error']

            if 'code' in jsonError and 'message' in jsonError:
                code = jsonError['code']
                message = jsonError['message']
                raise CLIInternalError('({}) {}'.format(code, message))
        elif "Message" in jsonError:
            message = jsonError["Message"]
            raise CLIInternalError(message)
        elif "message" in jsonError:
            message = jsonError["message"]
            raise CLIInternalError(message)
    raise e


def handle_non_404_exception(e):
    import json

    stringErr = str(e)

    if "{" in stringErr and "}" in stringErr:
        jsonError = stringErr[stringErr.index("{"):stringErr.rindex("}") + 1]
        jsonError = json.loads(jsonError)

        if 'error' in jsonError:
            jsonError = jsonError['error']

            if 'code' in jsonError and 'message' in jsonError:
                code = jsonError['code']
                message = jsonError['message']
                if code != "ResourceNotFound":
                    raise CLIInternalError('({}) {}'.format(code, message))
                return jsonError
        elif "Message" in jsonError:
            message = jsonError["Message"]
            raise CLIInternalError(message)
        elif "message" in jsonError:
            message = jsonError["message"]
            raise CLIInternalError(message)
    raise e


def providers_client_factory(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, subscription_id=subscription_id).providers


def cf_resource_groups(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   subscription_id=subscription_id).resource_groups


def log_analytics_client_factory(cli_ctx):
    from azure.mgmt.loganalytics import LogAnalyticsManagementClient

    return get_mgmt_service_client(cli_ctx, LogAnalyticsManagementClient).workspaces


def log_analytics_shared_key_client_factory(cli_ctx):
    from azure.mgmt.loganalytics import LogAnalyticsManagementClient

    return get_mgmt_service_client(cli_ctx, LogAnalyticsManagementClient).shared_keys
