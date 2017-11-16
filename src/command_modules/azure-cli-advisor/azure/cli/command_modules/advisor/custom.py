# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import uuid

from azure.mgmt.advisor.models import ConfigData, ConfigDataProperties


def cli_advisor_generate_recommendations(client, timeout=30):
    response = client.generate(raw=True)
    location = response.headers['Location']

    operation_id = _parse_operation_id(location)

    elapsedTime = 0
    maxTime = int(timeout)
    if maxTime < 1:
        maxTime = 1
    while elapsedTime < maxTime:
        response = client.get_generate_status(
            raw=True,
            operation_id=operation_id
        )
        status_code = response.response.status_code
        if status_code == 204:
            return {'Status': 204, 'Message': 'Recommendation generation has been completed.'}
        time.sleep(1)
        elapsedTime += 1
    return {'Status': 202, 'Message': 'Recommendation generation is in progress.'}


def cli_advisor_list_recommendations(client, ids=None, rg_name=None, category=None):
    scope = None
    if ids:
        for id_arg in ids:
            subScope = 'ResourceId eq \'{}\''.format(id_arg)
            if scope:
                scope += 'and {}'.format(subScope)
            else:
                scope = subScope
    elif rg_name:
        scope = 'ResourceGroup eq \'{}\''.format(rg_name)
    if category:
        subScope = 'Category eq \'{}\''.format(category)
        if scope:
            scope += 'and {}'.format(subScope)
        else:
            scope = subScope
    return list(client.list(scope))


def cli_advisor_disable_recommendations(client, ids, days=None):
    suppressions = []
    suppressionName = str(uuid.uuid4())
    for id_arg in ids:
        result = _parse_recommendation_uri(id_arg)
        resourceUri = result['resourceUri']
        recommendationId = result['recommendationId']
        if days:
            ttl = '{}:00:00:00'.format(days)
        else:
            ttl = ''
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
        result = _parse_recommendation_uri(id_arg)
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


def cli_advisor_get_configurations(client, rg_name=None):
    if rg_name:
        return list(client.list_by_resource_group(rg_name).value)
    return list(client.list_by_subscription().value)


def cli_advisor_set_configurations(client, rg_name=None, low_cpu_threshold=None, exclude=None):
    cfg = ConfigData()
    cfg.properties = ConfigDataProperties()

    if low_cpu_threshold:
        cfg.properties.low_cpu_threshold = low_cpu_threshold

    if exclude:
        if exclude == 'True':
            cfg.properties.exclude = True
        elif exclude == 'False':
            cfg.properties.exclude = False

    if rg_name:
        return client.create_in_resource_group(
            config_contract=cfg,
            resource_group=rg_name)

    return client.create_in_subscription(cfg)


def _parse_recommendation_uri(recommendationUri):
    resourceUri = recommendationUri[:recommendationUri.find("/providers/Microsoft.Advisor/recommendations")]
    recommendationId = recommendationUri[recommendationUri.find("/recommendations/") + len('/recommendations/'):]
    return {'resourceUri': resourceUri, 'recommendationId': recommendationId}


def _parse_operation_id(location):
    # extract the operation ID from the Location header
    # it is a GUID (i.e. a string of length 36) immediately preceding the api-version query parameter
    end = location.find('?api-version')
    start = end - 36
    operation_id = location[start:end]
    return operation_id
