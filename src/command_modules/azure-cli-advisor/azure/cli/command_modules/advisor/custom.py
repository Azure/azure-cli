# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from msrestazure.azure_exceptions import CloudError

from azure.mgmt.advisor.models import ConfigData, ConfigDataProperties


def cli_advisor_list_recommendations(client, ids=None, resource_group_name=None,
                                     category=None, refresh=None):
    if refresh:
        generate_recommendations(client)
    scope = build_filter_string(ids, resource_group_name, category)
    return client.list(scope)


def cli_advisor_disable_recommendations(client, resource_group_name=None,
                                        recommendation_name=None, days=None):
    if recommendation_name:
        recs = cli_advisor_list_recommendations(
                    client=client.recommendations,
                    resource_group_name=resource_group_name)
        rec = next(r for r in recs if r.name == recommendation_name)
        suppressions.append(
            create_suppression(
                client.suppressions,
                rec.id,
                days))

#    if ids:
#        for id_arg in ids:
#            suppressions.append(create_suppression(client.suppressions, id_arg, days))

    return suppressions


def cli_advisor_enable_recommendations(client, ids=None, resource_group_name=None, recommendation_name=None):
    enabledRecs = []
    allSups = list(client.suppressions.list())

    if recommendation_name:
        recs = cli_advisor_list_recommendations(
                    client=client.recommendations,
                    resource_group_name=resource_group_name)
        enabledRecs.append(
            remove_suppressions(
                client.suppressions,
                recommendations=recs,
                recommendation_name=recommendation_name,
                suppressions=allSups))

    if ids:
        for id_arg in ids:
            result = parse_recommendation_uri(id_arg)
            resourceUri = result['resourceUri']
            recommendationId = result['recommendationId']
            recs = cli_advisor_list_recommendations(
                client=client.recommendations,
                ids=[resourceUri]
            )
            enabledRecs.append(
                remove_suppressions(
                    client.suppressions,
                    recommendations=recs,
                    recommendation_name=recommendationId,
                    suppressions=allSups))

    return enabledRecs


def cli_advisor_list_configurations(client):
    return client.list_by_subscription().value


def cli_advisor_show_configuration(client, resource_group_name=None):
    # check for null and zero value
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name).value[0]
    return client.list_by_subscription().value[0]


def _cli_advisor_set_configuration(client, resource_group_name=None, parameters=None):
    if resource_group_name:
        return client.create_in_resource_group(
            config_contract=parameters,
            resource_group=resource_group_name)

    return client.create_in_subscription(parameters)


def cli_advisor_update_configurations(instance, resource_group_name=None,
                                      low_cpu_threshold=None, exclude=None, include=None):

    instance.properties.low_cpu_threshold = low_cpu_threshold
    instance.properties.exclude = exclude
    if include:
        instance.properties.exclude = False

    return instance


def create_suppression(client, recommendation_uri, days=None):
    suppressionName = str(uuid.uuid4())
    ttl = '{}:00:00:00'.format(days) if days else ''

    result = parse_recommendation_uri(recommendation_uri)
    resourceUri = result['resourceUri']
    recommendationId = result['recommendationId']

    client.create(
        resource_uri=resourceUri,
        recommendation_id=recommendationId,
        name=suppressionName,
        ttl=ttl
    )

    return client.get(
        resource_uri=resourceUri,
        recommendation_id=recommendationId,
        name=suppressionName
    )


def remove_suppressions(client, recommendations, recommendation_name, suppressions):
    rec = next(x for x in recommendations if x.name == recommendation_name)

    matches = [x for x in suppressions if x.suppression_id in rec.suppression_ids]
    for match in matches:
        client.delete(
            resource_uri=parse_recommendation_uri(rec.id)['resourceUri'],
            recommendation_id=recommendation_name,
            name=match.name
        )
    rec.suppression_ids = None
    return rec


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


def generate_recommendations(client):
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
