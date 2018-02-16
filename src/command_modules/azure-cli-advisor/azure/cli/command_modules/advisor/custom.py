# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
from knack.util import CLIError


def cli_advisor_list_recommendations(client, ids=None, resource_group_name=None,
                                     category=None, refresh=None):
    if refresh:
        _cli_advisor_generate_recommendations(client)
    scope = _cli_advisor_build_filter_string(ids, resource_group_name, category)
    return client.list(scope)


def cli_advisor_disable_recommendations(client, resource_group_name,
                                        recommendation_name, days=None):
    recs = cli_advisor_list_recommendations(
        client=client.recommendations,
        resource_group_name=resource_group_name)
    rec = next((r for r in recs if r.name == recommendation_name), None)

    if not rec:
        raise CLIError(
            "Recommendation with name {} in resource group {} not found".format(
                recommendation_name,
                resource_group_name))

    suppressionName = str(uuid.uuid4())
    ttl = '{}:00:00:00'.format(days) if days else ''

    result = _cli_advisor_parse_recommendation_uri(rec.id)
    resourceUri = result['resourceUri']
    recommendationId = result['recommendationId']

    sup = client.suppressions.create(
        resource_uri=resourceUri,
        recommendation_id=recommendationId,
        name=suppressionName,
        ttl=ttl
    )

    if rec.suppression_ids:
        rec.suppression_ids.append(sup.suppression_id)
    else:
        rec.suppression_ids = [sup.suppression_id]

    return rec


def cli_advisor_enable_recommendations(client, resource_group_name, recommendation_name):
    allSups = list(client.suppressions.list())

    recs = cli_advisor_list_recommendations(
        client=client.recommendations,
        resource_group_name=resource_group_name)
    rec = next((r for r in recs if r.name == recommendation_name), None)

    if rec:
        matches = [x for x in allSups if x.suppression_id in rec.suppression_ids]
    else:
        matches = [s for s in allSups if 'Microsoft.Advisor/recommendations/{}'.format(recommendation_name) in s.id]

    if matches:
        for match in matches:
            result = _cli_advisor_parse_recommendation_uri(match.id)
            client.suppressions.delete(
                resource_uri=result['resourceUri'],
                recommendation_id=result['recommendationId'],
                name=match.name
            )

        rec = cli_advisor_list_recommendations(
            client=client.recommendations,
            ids=result['resourceUri'])

    return rec


def cli_advisor_list_configuration(client):
    return client.list_by_subscription()


def cli_advisor_show_configuration(client, resource_group_name=None):
    output = None
    if resource_group_name:
        output = client.list_by_resource_group(resource_group_name)
    else:
        output = client.list_by_subscription()
    # the list is guaranteed to have one element
    return list(output)[0]


def cli_advisor_update_configuration(instance, low_cpu_threshold=None,
                                     exclude=None, include=None):
    instance.properties.low_cpu_threshold = low_cpu_threshold
    instance.properties.exclude = exclude
    if include:
        instance.properties.exclude = False

    return instance


def _cli_advisor_build_filter_string(ids=None, resource_group_name=None, category=None):

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


def _cli_advisor_parse_operation_id(location):
    # extract the operation ID from the Location header
    # it is a GUID (i.e. a string of length 36) immediately preceding the api-version query parameter
    end = location.find('?api-version')
    start = end - 36
    operation_id = location[start:end]
    return operation_id


def _cli_advisor_parse_recommendation_uri(recommendationUri):
    resourceUri = recommendationUri[:recommendationUri.find("/providers/Microsoft.Advisor/recommendations")]
    rStart = recommendationUri.find("/recommendations/") + len('/recommendations/')
    # recommendation ID is a GUID (i.e. a string of length 36)
    rEnd = rStart + 36
    recommendationId = recommendationUri[rStart:rEnd]
    return {'resourceUri': resourceUri, 'recommendationId': recommendationId}


def _cli_advisor_generate_recommendations(client):
    from msrestazure.azure_exceptions import CloudError

    response = client.generate(raw=True)
    location = response.headers['Location']
    operation_id = _cli_advisor_parse_operation_id(location)

    try:
        client.get_generate_status(operation_id=operation_id)
    except CloudError as ex:
        # Advisor API returns 204 which is not aligned with ARM guidelines
        # so the SDK will throw an exception that we will have to ignore
        if ex.status_code != 204:
            raise ex


def _cli_advisor_set_configuration(client, resource_group_name=None, parameters=None):
    if resource_group_name:
        return client.create_in_resource_group(
            config_contract=parameters,
            resource_group=resource_group_name)

    return client.create_in_subscription(parameters)
