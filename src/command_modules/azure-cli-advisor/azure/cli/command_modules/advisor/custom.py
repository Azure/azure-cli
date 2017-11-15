# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import time
import uuid

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.advisor.models import Category, ConfigData, ConfigDataProperties

def cli_advisor_generate_recommendations(client, timeout=30):
    """
    :param timeout: The timeout in seconds.
    :type timeout: str
    """
    response = client.generate(raw=True)
    location = response.headers['Location']

    # extract the operation ID from the Location header
    operation_id = re.findall("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", location)

    elapsedTime = 0
    maxTime = int(timeout)
    if maxTime < 1:
        maxTime = 1
    while elapsedTime < maxTime:
        response = client.get_generate_status(
            raw=True,
            operation_id = operation_id[0]
        )
        status_code = response.response.status_code
        if status_code == 204:
            break
        time.sleep(1)
        elapsedTime += 1
    if status_code != 204:
        raise CLIError('Recommendation generation timed out.')
    return 'Recommendations successfully generated.'

def cli_advisor_list_recommendations(client, ids=None, rg_name=None, category=None):
    """
    :param category: The category of the recommendation.
    :type category: str or :class:`Category
     <azure.mgmt.advisor.models.Category>`
    """
    filter = None
    if ids:
        for id_arg in ids:
            subFilter = 'ResourceId eq \'{}\''.format(id_arg)
            if filter:
                filter += 'and {}'.format(subFilter)
            else:
                filter = subFilter
    elif rg_name:
        filter = 'ResourceGroup eq \'{}\''.format(rg_name)
    if category:
        subFilter = 'Category eq \'{}\''.format(category)
        if filter:
            filter += 'and {}'.format(subFilter)
        else:
            filter = subFilter
    return list(client.list(filter))

def cli_advisor_disable_recommendations(client, ids=None, name=None, duration=None):
    suppressionName = str(uuid.uuid4())
    if len(ids) > 1:
        raise CLIError('Only one recommendation can be disabled at a time.')
    id_arg = ids[0]
    client.create(
        resource_uri = id_arg,
        recommendation_id = name,
        name = suppressionName,
        ttl = duration
    )
    return suppressionName

def cli_advisor_enable_recommendations(client, ids=None, name=None, duration=None):
    if len(ids) > 1:
        raise CLIError('Only one recommendation can be enabled at a time.')
    id_arg = ids[0]
    recs = cli_advisor_list_recommendations(client=client.recommendations, ids=id_arg)
    for rec in recs:
        if rec.suppression_ids:
            for id in rec.suppression_ids:
                client.suppressions.delete(
                    resource_uri = id_arg,
                    recommendation_id = name,
                    name = id
                )

def cli_advisor_get_configurations(client, rg_name=None):
    if rg_name:
        return list(client.list_by_resource_group(rg_name).value)
    else:
        return list(client.list_by_subscription().value)

def cli_advisor_set_configurations(client, rg_name=None, low_cpu_threshold=None, exclude=None):
    input = ConfigData()
    input.properties = ConfigDataProperties()

    if low_cpu_threshold:
        input.properties.low_cpu_threshold = low_cpu_threshold

    if exclude:
        if exclude == 'True':
            input.properties.exclude = True
        elif exclude == 'False':
            input.properties.exclude = False

    if rg_name:
        return client.create_in_resource_group(
            config_contract = input,
            resource_group = rg_name)
    else:
        return client.create_in_subscription(input)
