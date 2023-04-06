
def get_dce_from_dcr(cmd, dcrId):
    from azure.cli.core.util import send_raw_request
    association_url = f"https://management.azure.com{dcrId}?api-version={DC_API}"
    headers = ['User-Agent=azuremonitormetrics.get_dce_from_dcr']
    r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
    data = json.loads(r.text)
    return data['properties']['dataCollectionEndpointId']


def get_dc_objects_list(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name):
    try:
        from azure.cli.core.util import send_raw_request
        cluster_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name
        )
        association_url = f"https://management.azure.com{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version={DC_API}"
        headers = ['User-Agent=azuremonitormetrics.get_dcra']
        r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
        data = json.loads(r.text)
        dc_object_array = []
        for item in data['value']:
            dce_id = get_dce_from_dcr(cmd, item['properties']['dataCollectionRuleId'])
            dc_object_array.append({'name': item['name'], 'dataCollectionRuleId': item['properties']['dataCollectionRuleId'], 'dceId': dce_id})
        return dc_object_array
    except CLIError as e:
        error = e
        raise CLIError(error)


def delete_dc_objects_if_prometheus_enabled(cmd, dc_objects_list, cluster_subscription, cluster_resource_group_name, cluster_name):
    from azure.cli.core.util import send_raw_request
    cluster_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        cluster_name
    )
    for item in dc_objects_list:
        association_url = f"https://management.azure.com{item['dataCollectionRuleId']}?api-version={DC_API}"
        try:
            headers = ['User-Agent=azuremonitormetrics.get_dcr_if_prometheus_enabled']
            r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
            data = json.loads(r.text)
            if 'microsoft-prometheusmetrics' in [stream.lower() for stream in data['properties']['dataFlows'][0]['streams']]:
                # delete DCRA
                url = f"https://management.azure.com{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{item['name']}?api-version={DC_API}"
                headers = ['User-Agent=azuremonitormetrics.delete_dcra']
                send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)
                # delete DCR
                url = f"https://management.azure.com{item['dataCollectionRuleId']}?api-version={DC_API}"
                headers = ['User-Agent=azuremonitormetrics.delete_dcr']
                send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)
                # delete DCE
                url = f"https://management.azure.com{item['dceId']}?api-version={DC_API}"
                headers = ['User-Agent=azuremonitormetrics.delete_dce']
                send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)
        except CLIError as e:
            error = e
            raise CLIError(error)
