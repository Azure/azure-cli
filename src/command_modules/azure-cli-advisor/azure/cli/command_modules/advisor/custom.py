# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from msrestazure.azure_exceptions import CloudError

from azure.mgmt.advisor.models import ConfigData, ConfigDataProperties


def cli_advisor_generate_recommendations(client):
    response = client.generate(raw=True)
    location = response.headers['Location']
    operation_id = parse_operation_id(location)

    try:
        client.get_generate_status(operation_id=operation_id)
    except CloudError as ex:
        # Advisor API returns 204 which is not aligned with ARM guidelines
        # so the SDK will throw an exception that we will have to ignore
        if ex.status_code != 204:
            raise ex


def cli_advisor_list_recommendations(client, ids=None, resource_group_name=None, category=None):
    scope = build_filter_string(ids, resource_group_name, category)
    return client.list(scope)


def cli_advisor_disable_recommendations(client, ids, days=None):
    suppressions = []
    suppressionName = str(uuid.uuid4())
    for id_arg in ids:
        result = parse_recommendation_uri(id_arg)
        resourceUri = result['resourceUri']
        recommendationId = result['recommendationId']
        ttl = '{}:00:00:00'.format(days) if days else ''
        client.create(
            resource_uri=resourceUri,
            recommendation_id=recommendationId,
            name=suppressionName,
            ttl=ttl
        )
        suppressions.append(client.get(
            resource_uri=resourceUri,
            recommendation_id=recommendationId,
            name=suppressionName
        ))
    return suppressions


def cli_advisor_enable_recommendations(client, ids):
    enabledRecs = []
    allSups = list(client.suppressions.list())
    for id_arg in ids:
        result = parse_recommendation_uri(id_arg)
        resourceUri = result['resourceUri']
        recommendationId = result['recommendationId']
        recs = cli_advisor_list_recommendations(
            client=client.recommendations,
            ids=[resourceUri]
        )
        rec = next(x for x in recs if x.name == recommendationId)
        matches = [x for x in allSups if x.suppression_id in rec.suppression_ids]
        for match in matches:
            client.suppressions.delete(
                resource_uri=resourceUri,
                recommendation_id=recommendationId,
                name=match.name
            )
        rec.suppression_ids = None
        enabledRecs.append(rec)
    return enabledRecs


def cli_advisor_get_configurations(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()


def cli_advisor_set_configurations(client, resource_group_name=None,
                                   low_cpu_threshold=None, exclude=None, include=None):

    cfg = ConfigData()
    cfg.properties = ConfigDataProperties()

    cfg.properties.low_cpu_threshold = low_cpu_threshold
    cfg.properties.exclude = exclude
    if include:
        cfg.properties.exclude = False

    if resource_group_name:
        return client.create_in_resource_group(
            config_contract=cfg,
            resource_group=resource_group_name)

    return client.create_in_subscription(cfg)


def build_filter_string(ids=None, resource_group_name=None, category=None):

    idFilter = None
    if ids:
        idFilter = ' or '.join(["ResourceId eq '{}'".format(id_arg) for id_arg in ids])
    elif resource_group_name:
        idFilter = "ResourceGroup eq '{}'".format(resource_group_name)

    categoryFilter = "Category eq '{}'".format(category) if category else None

    if idFilter:
        if categoryFilter:
            return '({}) and {}'.format(idFilter, categoryFilter)
        return idFilter
    elif categoryFilter:
        return categoryFilter

    return None


def parse_operation_id(location):
    # extract the operation ID from the Location header
    # it is a GUID (i.e. a string of length 36) immediately preceding the api-version query parameter
    end = location.find('?api-version')
    start = end - 36
    operation_id = location[start:end]
    return operation_id


def parse_recommendation_uri(recommendationUri):
    resourceUri = recommendationUri[:recommendationUri.find("/providers/Microsoft.Advisor/recommendations")]
    recommendationId = recommendationUri[recommendationUri.find("/recommendations/") + len('/recommendations/'):]
    return {'resourceUri': resourceUri, 'recommendationId': recommendationId}
