# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import web_client_factory


def _generic_site_operation(cli_ctx, resource_group_name, name, operation_name, slot=None,
                            extra_parameter=None, client=None):
    client = client or web_client_factory(cli_ctx)
    operation = getattr(client.web_apps,
                        operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (operation(resource_group_name, name)
                if extra_parameter is None else operation(resource_group_name,
                                                          name, extra_parameter))

    return (operation(resource_group_name, name, slot)
            if extra_parameter is None else operation(resource_group_name,
                                                      name, extra_parameter, slot))


def _check_deployment_status(deployment_status_url, authorization):
    num_trials = 1
    import requests
    while num_trials < 200:
        response = requests.get(deployment_url, headers=authorization)
        res_dict = response.json()
        num_trials = num_trials + 1
        if res_dict['status'] == 5:
            logger.warning("Zip deployment failed status {}".format(
                res_dict['status_text']
            ))
            break
        elif res_dict['status'] == 4:
            break
        logger.warning(res_dict['progress'])
    # if the deployment is taking longer than expected
    r = requests.get(deployment_url, headers=authorization)
    if r.json()['status'] != 4:
        logger.warning("""Deployment is taking longer than expected. Please verify status at '{}'
            beforing launching the app""".format(deployment_url))
    return r.json()
