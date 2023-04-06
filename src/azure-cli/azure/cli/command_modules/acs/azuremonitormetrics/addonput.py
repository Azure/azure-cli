import json

from azure.cli.core.azclierror import (
    UnknownError,
    CLIError
)


def addon_put(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    from azure.cli.core.util import send_raw_request
    feature_check_url = f"https://management.azure.com/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}?api-version={AKS_CLUSTER_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.addon_get']
        r = send_raw_request(cmd.cli_ctx, "GET", feature_check_url,
                             body={}, headers=headers)
    except CLIError as e:
        raise UnknownError(e)
    json_response = json.loads(r.text)
    values_array = json_response["properties"]
    if "azureMonitorProfile" in values_array:
        if "metrics" in values_array["azureMonitorProfile"]:
            if values_array["azureMonitorProfile"]["metrics"]["enabled"] is False:
                ## What if enabled doesn't exist
                values_array["azureMonitorProfile"]["metrics"]["enabled"] = True
    try:
        headers = ['User-Agent=azuremonitormetrics.addon_put']
        body = json.dumps(values_array)
        r = send_raw_request(cmd.cli_ctx, "PUT", feature_check_url,
                             body=body, headers=headers)
    except CLIError as e:
        raise UnknownError(e)
