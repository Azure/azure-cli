# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
from azure.mgmt.advisor.models import SuppressionContract


def list_recommendations(client, ids=None, resource_group_name=None,
                         category=None, refresh=None):
    if refresh:
        _generate_recommendations(client)
    scope = _build_filter_string(ids, resource_group_name, category)
    return client.list(scope)


def disable_recommendations(client, ids=None, recommendation_name=None,
                            resource_group_name=None, days=None):
    recs = _get_recommendations(
        client=client.recommendations,
        ids=ids,
        resource_group_name=resource_group_name,
        recommendation_name=recommendation_name)

    for rec in recs:
        suppression_name = str(uuid.uuid4())
        ttl = '{}:00:00:00'.format(days) if days else ''

        result = _parse_recommendation_uri(rec.id)
        resource_uri = result['resource_uri']
        recommendation_id = result['recommendation_id']
        suppression_contract = SuppressionContract(ttl=ttl)

        sup = client.suppressions.create(
            resource_uri=resource_uri,
            recommendation_id=recommendation_id,
            name=suppression_name,
            suppression_contract=suppression_contract
        )

        if rec.suppression_ids:
            rec.suppression_ids.append(sup.suppression_id)
        else:
            rec.suppression_ids = [sup.suppression_id]

    return recs


def enable_recommendations(client, ids=None, resource_group_name=None, recommendation_name=None):
    recs = _get_recommendations(
        client=client.recommendations,
        ids=ids,
        resource_group_name=resource_group_name,
        recommendation_name=recommendation_name)
    all_sups = list(client.suppressions.list())

    for rec in recs:
        for sup in all_sups:
            try:
                if sup.suppression_id in rec.suppression_ids:
                    result = _parse_recommendation_uri(rec.id)
                    client.suppressions.delete(
                        resource_uri=result['resource_uri'],
                        recommendation_id=result['recommendation_id'],
                        name=sup.name)
            except TypeError:  # when rec.id is already suppressed, rec.suppression_ids is None
                pass
        rec.suppression_ids = None

    return recs


def list_configuration(client):
    return client.list_by_subscription()


def show_configuration(client, resource_group_name=None):
    output = None
    if resource_group_name:
        output = client.list_by_resource_group(resource_group_name)
    else:
        output = client.list_by_subscription()
    # the list is guaranteed to have one element
    return list(output)[0]


def update_configuration(instance, low_cpu_threshold=None,
                         exclude=None, include=None):
    instance.low_cpu_threshold = low_cpu_threshold
    instance.exclude = exclude
    if include:
        instance.exclude = False

    return instance


def _build_filter_string(ids=None, resource_group_name=None, category=None):

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
    if categoryFilter:
        return categoryFilter

    return None


def _parse_operation_id(location):
    # extract the operation ID from the Location header
    # it is a GUID (i.e. a string of length 36) immediately preceding the api-version query parameter
    end = location.find('?api-version')
    start = end - 36
    operation_id = location[start:end]
    return operation_id


def _parse_recommendation_uri(recommendation_uri):
    resource_uri = recommendation_uri[:recommendation_uri.find("/providers/Microsoft.Advisor/recommendations")]
    rStart = recommendation_uri.find("/recommendations/") + len('/recommendations/')
    # recommendation ID is a GUID (i.e. a string of length 36)
    rEnd = rStart + 36
    recommendation_id = recommendation_uri[rStart:rEnd]
    return {'resource_uri': resource_uri, 'recommendation_id': recommendation_id}


def _generate_recommendations(client):
    from msrestazure.azure_exceptions import CloudError

    response = client.generate(raw=True)
    location = response.headers['Location']
    operation_id = _parse_operation_id(location)

    try:
        client.get_generate_status(operation_id=operation_id)
    except CloudError as ex:
        # Advisor API returns 204 which is not aligned with ARM guidelines
        # so the SDK will throw an exception that we will have to ignore
        if ex.status_code != 204:
            raise ex


def _set_configuration(client, resource_group_name=None, parameters=None, configuration_name=None):

    if not configuration_name:
        configuration_name = 'default'

    if resource_group_name:
        return client.create_in_resource_group(
            config_contract=parameters,
            resource_group=resource_group_name,
            configuration_name=configuration_name)

    return client.create_in_subscription(config_contract=parameters,
                                         configuration_name=configuration_name)


def _get_recommendations(client, ids=None, resource_group_name=None, recommendation_name=None):
    if ids:
        resource_ids = [_parse_recommendation_uri(id_arg)['resource_uri'] for id_arg in ids]
        recs = list_recommendations(
            client=client,
            ids=resource_ids
        )
        return [r for r in recs if r.id in ids]

    if recommendation_name:
        recs = list_recommendations(
            client=client,
            resource_group_name=resource_group_name)
        return [r for r in recs if r.name == recommendation_name]

    return None
