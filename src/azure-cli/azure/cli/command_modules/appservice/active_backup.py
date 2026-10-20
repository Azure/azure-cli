# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from urllib.parse import quote, unquote

from knack.log import get_logger

from azure.cli.core.azclierror import AzureResponseError, FileOperationError, InvalidArgumentValueError

from ._active_backup_client import ActiveBackupClient, DEFAULT_TIMEOUT, load_json, segment


logger = get_logger(__name__)


def _client(cmd, resource_group_name, name, plan=False):
    return ActiveBackupClient(cmd.cli_ctx, resource_group_name, name, 'serverfarms' if plan else 'sites')


def _boolean(value):
    if value is None or isinstance(value, bool):
        return value
    if str(value).lower() in ('true', 'false'):
        return str(value).lower() == 'true'
    raise InvalidArgumentValueError('Provide true or false.')


def _primary_location(cmd, resource_group_name, name, plan):
    from ._client_factory import web_client_factory
    client = web_client_factory(cmd.cli_ctx)
    operations = client.app_service_plans if plan else client.web_apps
    return operations.get(resource_group_name, name).location


def _silo_body(cmd, resource_group_name, name, silo, location, primary_location, properties, plan, update):
    client = _client(cmd, resource_group_name, name, plan)
    if update:
        existing = client.get_resource(client.resource(silo))
        if not isinstance(existing, dict) or not isinstance(existing.get('properties'), dict):
            raise AzureResponseError('The silo API did not return the resource properties required for update.')
        existing_properties = existing['properties']
        location = location or existing.get('location') or existing_properties.get('siloLocation')
        primary_location = primary_location or existing_properties.get('primaryLocation')
    elif not primary_location:
        primary_location = _primary_location(cmd, resource_group_name, name, plan)
    if not location or not primary_location:
        raise InvalidArgumentValueError('Provide --location and --primary-location for the silo.')
    properties = {key: value for key, value in properties.items() if value is not None}
    properties.update(name=silo, primaryLocation=primary_location)
    return client, {'location': location, 'properties': properties}


def _plan_properties(number_of_workers, zone_redundant):
    if number_of_workers is not None and not 1 <= number_of_workers <= 30:
        raise InvalidArgumentValueError('--number-of-workers must be between 1 and 30.')
    return {'instanceNumberOverride': number_of_workers, 'zoneRedundantOverride': _boolean(zone_redundant)}


def create_plan_silo(cmd, resource_group_name, name, silo, location, primary_location=None,
                     number_of_workers=None, zone_redundant=None, no_wait=False, timeout=DEFAULT_TIMEOUT):
    client, body = _silo_body(cmd, resource_group_name, name, silo, location, primary_location,
                              _plan_properties(number_of_workers, zone_redundant), True, False)
    return client.mutate('PUT', client.resource(silo), body, no_wait, timeout)


def update_plan_silo(cmd, resource_group_name, name, silo, location=None, primary_location=None,
                     number_of_workers=None, zone_redundant=None, no_wait=False, timeout=DEFAULT_TIMEOUT):
    client, body = _silo_body(cmd, resource_group_name, name, silo, location, primary_location,
                              _plan_properties(number_of_workers, zone_redundant), True, True)
    return client.mutate('PUT', client.resource(silo), body, no_wait, timeout)


def show_plan_silo(cmd, resource_group_name, name, silo):
    client = _client(cmd, resource_group_name, name, True)
    return client.decode(client.request('GET', client.resource(silo)))


def list_plan_silos(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name, True)
    return client.list(client.resource())


def delete_plan_silo(cmd, resource_group_name, name, silo, no_wait=False, timeout=DEFAULT_TIMEOUT):
    client = _client(cmd, resource_group_name, name, True)
    return client.mutate('DELETE', client.resource(silo), no_wait=no_wait, timeout=timeout)


def show_plan_silo_operation(cmd, resource_group_name, name, silo, operation_id):
    client = _client(cmd, resource_group_name, name, True)
    return client.operation(client.operation_url(silo, operation_id))


def wait_plan_silo(cmd, resource_group_name, name, silo, operation_id, timeout=DEFAULT_TIMEOUT):
    client = _client(cmd, resource_group_name, name, True)
    return client.wait(client.operation_url(silo, operation_id), timeout)


def list_plan_silo_vnet_integrations(cmd, resource_group_name, name, silo):
    client = _client(cmd, resource_group_name, name, True)
    return client.decode(client.request('GET', client.resource(silo) + '/virtualNetworkIntegrations'))


def _site_properties(endpoint_status, follow_last_known_good, subnet):
    properties = {'endpointStatus': endpoint_status, 'followLastKnownGood': _boolean(follow_last_known_good)}
    if subnet is not None:
        properties['networkingOverride'] = {'vnetIntegrationOverride': subnet}
    return properties


def create_site_silo(cmd, resource_group_name, name, silo, location, primary_location=None,
                     traffic_mode=None, endpoint_status=None, follow_last_known_good=None, subnet=None,
                     no_wait=False, timeout=DEFAULT_TIMEOUT):
    properties = _site_properties(endpoint_status, follow_last_known_good, subnet)
    properties['trafficMode'] = traffic_mode
    client, body = _silo_body(cmd, resource_group_name, name, silo, location, primary_location,
                              properties, False, False)
    return client.mutate('PUT', client.resource(silo), body, no_wait, timeout)


def update_site_silo(cmd, resource_group_name, name, silo, location=None, primary_location=None,
                     endpoint_status=None, follow_last_known_good=None, subnet=None,
                     no_wait=False, timeout=DEFAULT_TIMEOUT):
    client, body = _silo_body(cmd, resource_group_name, name, silo, location, primary_location,
                              _site_properties(endpoint_status, follow_last_known_good, subnet), False, True)
    return client.mutate('PUT', client.resource(silo), body, no_wait, timeout)


def show_site_silo(cmd, resource_group_name, name, silo):
    client = _client(cmd, resource_group_name, name)
    return client.get_resource(client.resource(silo))


def list_site_silos(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name)
    return client.list(client.resource())


def delete_site_silo(cmd, resource_group_name, name, silo, no_wait=False, timeout=DEFAULT_TIMEOUT):
    client = _client(cmd, resource_group_name, name)
    return client.mutate('DELETE', client.resource(silo), no_wait=no_wait, timeout=timeout)


def show_site_silo_operation(cmd, resource_group_name, name, silo, operation_id):
    client = _client(cmd, resource_group_name, name)
    return client.operation(client.operation_url(silo, operation_id))


def wait_site_silo(cmd, resource_group_name, name, silo, operation_id, timeout=DEFAULT_TIMEOUT):
    client = _client(cmd, resource_group_name, name)
    return client.wait(client.operation_url(silo, operation_id), timeout)


def refresh_site_silos(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name)
    response = client.request('POST', client.parent + '/refreshSilos')
    if response.status_code != 204:
        raise AzureResponseError('The refresh API did not return the expected 204 acceptance response.')
    logger.warning('Refresh request accepted. Revision propagation continues asynchronously and may take a few '
                   'minutes. Use silo show/list to inspect revision numbers.')


def list_last_known_good(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name)
    return client.list(client.parent + '/lastKnownGood')


def show_last_known_good(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name)
    return client.decode(client.request('GET', client.parent + '/lastKnownGood/default'))


def mark_last_known_good(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name)
    return client.decode(client.request('POST', client.parent + '/lastKnownGood/default/mark'))


def list_managed_traffic(cmd, resource_group_name, name, expand_endpoints=False):
    client = _client(cmd, resource_group_name, name)
    return client.list(client.parent + '/managedTrafficConfig',
                       {'$expand': 'endpoints'} if expand_endpoints else None)


def show_managed_traffic(cmd, resource_group_name, name):
    client = _client(cmd, resource_group_name, name)
    return client.decode(client.request('GET', client.parent + '/managedTrafficConfig/default'))


def update_managed_traffic(cmd, resource_group_name, name, traffic_mode=None, endpoints=None):
    properties = {}
    if traffic_mode is not None:
        properties['trafficMode'] = traffic_mode
    if endpoints is not None:
        values = load_json(endpoints, list)
        for endpoint in values:
            if not isinstance(endpoint, dict) or not isinstance(endpoint.get('region'), str):
                raise InvalidArgumentValueError('Each endpoint must be an object with a region.')
            if set(endpoint) - {'region', 'weight', 'priority'}:
                raise InvalidArgumentValueError('Endpoint inputs support region, weight, and priority.')
            for key in ('weight', 'priority'):
                value = endpoint.get(key)
                if value is not None and (type(value) is not int or not 1 <= value <= 1000):
                    raise InvalidArgumentValueError('Endpoint {} must be an integer from 1 to 1000.'.format(key))
        properties['endpoints'] = values
    if not properties:
        raise InvalidArgumentValueError('Provide --traffic-mode or --endpoints.')
    client = _client(cmd, resource_group_name, name)
    return client.decode(client.request(
        'PUT', client.parent + '/managedTrafficConfig/default', {'properties': properties}))


def _metric_query(start_time=None, end_time=None, time_grain=None, names=None, filter_string=None):
    if filter_string:
        if any(value is not None for value in (start_time, end_time, time_grain, names)):
            raise InvalidArgumentValueError('Use --filter or individual metric filter arguments, not both.')
        return {'$filter': filter_string}
    values = []
    for key, value in (('startTime', start_time), ('endTime', end_time), ('timeGrain', time_grain)):
        if value is not None:
            if "'" in value:
                raise InvalidArgumentValueError('Metric filter values must not contain quotes.')
            values.append("{} eq {}'{}'".format(key, 'duration' if key == 'timeGrain' else '', value))
    if names:
        name_filters = ["name.value eq '{}'".format(value.replace("'", "''")) for value in names]
        values.append('(' + ' or '.join(name_filters) + ')')
    return {'$filter': ' and '.join(values)} if values else {}


def list_managed_traffic_metrics(cmd, resource_group_name, name, start_time=None, end_time=None, time_grain=None):
    client = _client(cmd, resource_group_name, name)
    return client.decode(client.request('GET', client.parent + '/managedTrafficConfig/default/metrics',
                                        query=_metric_query(start_time, end_time, time_grain)))


def show_silo_vnet_integration(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/virtualNetworkConnections/virtualNetwork')


def _vnet(cmd, resource_group_name, name, silo, method, subnet, body):
    envelope = load_json(body) if body is not None else {'properties': {}}
    if not isinstance(envelope.get('properties'), dict):
        raise InvalidArgumentValueError('--body must contain a properties object.')
    if subnet is not None:
        envelope['properties']['subnetResourceId'] = subnet
    return _site(cmd, resource_group_name, name, silo, '/virtualNetworkConnections/virtualNetwork',
                 method=method, body=envelope)


def add_silo_vnet_integration(cmd, resource_group_name, name, silo, subnet=None, body=None):
    if subnet is None and body is None:
        raise InvalidArgumentValueError('Provide --subnet or --body.')
    return _vnet(cmd, resource_group_name, name, silo, 'PUT', subnet, body)


def update_silo_vnet_integration(cmd, resource_group_name, name, silo, subnet=None, body=None):
    if subnet is None and body is None:
        raise InvalidArgumentValueError('Provide --subnet or --body.')
    return _vnet(cmd, resource_group_name, name, silo, 'PATCH', subnet, body)


def remove_silo_vnet_integration(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/virtualNetworkConnections/virtualNetwork', method='DELETE')


def _site(cmd, resource_group_name, name, silo, suffix='', method='GET', query=None, body=None,
          filename=None, overwrite=False, tail=False, content_type=None, no_wait=False, timeout=None, collection=False):
    client = _client(cmd, resource_group_name, name)
    path = client.resource(silo) + suffix
    if collection:
        return client.list(path, query)
    if filename is not None or tail:
        return client.consume(method, path, filename, overwrite, query, body, content_type, tail)
    if timeout is not None:
        return client.mutate(method, path, body, no_wait, timeout, query)
    return client.decode(client.request(method, path, body, query, content_type=content_type))


def _instance(instance):
    return '/instances/' + segment(instance) if instance is not None else ''


def _process(process_id, instance=None):
    return _instance(instance) + '/processes/' + segment(process_id)


def show_silo_php_logging(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/phplogging')


def list_silo_deployments(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/deployments', collection=True)


def show_silo_deployment(cmd, resource_group_name, name, silo, deployment_id):
    return _site(cmd, resource_group_name, name, silo, '/deployments/' + segment(deployment_id))


def list_silo_deployment_logs(cmd, resource_group_name, name, silo, deployment_id):
    return _site(cmd, resource_group_name, name, silo, '/deployments/' + segment(deployment_id) + '/log')


def delete_silo_process(cmd, resource_group_name, name, silo, process_id, instance=None):
    return _site(cmd, resource_group_name, name, silo, _process(process_id, instance), method='DELETE')


def stop_silo_process(cmd, resource_group_name, name, silo, process_id, instance=None):
    return _site(cmd, resource_group_name, name, silo, _process(process_id, instance) + '/stop', method='POST')


def restart_silo_container(cmd, resource_group_name, name, silo, container_name, instance=None):
    return _site(cmd, resource_group_name, name, silo,
                 _instance(instance) + '/containers/' + segment(container_name) + '/restart', method='POST')


def show_silo_process(cmd, resource_group_name, name, silo, process_id, instance=None):
    return _site(cmd, resource_group_name, name, silo, _process(process_id, instance))


def list_silo_process_threads(cmd, resource_group_name, name, silo, process_id, instance=None):
    return _site(cmd, resource_group_name, name, silo, _process(process_id, instance) + '/threads', collection=True)


def show_silo_process_thread(cmd, resource_group_name, name, silo, process_id, thread_id, instance=None):
    return _site(cmd, resource_group_name, name, silo,
                 _process(process_id, instance) + '/threads/' + segment(thread_id))


def list_silo_process_modules(cmd, resource_group_name, name, silo, process_id, instance=None):
    return _site(cmd, resource_group_name, name, silo, _process(process_id, instance) + '/modules', collection=True)


def show_silo_process_module(cmd, resource_group_name, name, silo, process_id, base_address, instance=None):
    return _site(cmd, resource_group_name, name, silo,
                 _process(process_id, instance) + '/modules/' + segment(base_address))


def dump_silo_process(cmd, resource_group_name, name, silo, process_id, file, instance=None, overwrite=False):
    return _site(cmd, resource_group_name, name, silo, _process(process_id, instance) + '/dump',
                 filename=file, overwrite=overwrite)


def download_silo_container_logs(cmd, resource_group_name, name, silo, file, format='zip', overwrite=False):
    return _site(cmd, resource_group_name, name, silo, '/containerlogs' + ('/zip' if format == 'zip' else ''),
                 method='POST', filename=file, overwrite=overwrite)


def list_silo_startup_logs(cmd, resource_group_name, name, silo, log_type=None, instance=None, latest=None):
    return _site(cmd, resource_group_name, name, silo, '/startuplogs',
                 query={'type': log_type, 'targetSiteInstance': instance, 'latest': _boolean(latest)})


def show_silo_startup_summary(cmd, resource_group_name, name, silo, duration=None, instance=None):
    return _site(cmd, resource_group_name, name, silo, '/startuplogs/summary',
                 query={'duration': duration, 'targetSiteInstance': instance})


def show_silo_startup_log(cmd, resource_group_name, name, silo, filename):
    return _site(cmd, resource_group_name, name, silo, '/startuplogs/' + segment(filename))


def list_silo_logs(cmd, resource_group_name, name, silo, instance=None):
    return _site(cmd, resource_group_name, name, silo, '/logs', query={'instanceId': instance})


def tail_silo_logs(cmd, resource_group_name, name, silo, instance=None, file=None, overwrite=False):
    return _site(cmd, resource_group_name, name, silo, _instance(instance) + '/logs/live',
                 filename=file, overwrite=overwrite, tail=True)


def _webjob(webjob_name, kind='webjobs'):
    return '/' + kind + '/' + segment(webjob_name)


def list_silo_webjobs(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/webjobs', collection=True)


def show_silo_webjob(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name))


def list_silo_continuous_webjobs(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/continuouswebjobs', collection=True)


def show_silo_continuous_webjob(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name, 'continuouswebjobs'))


def start_silo_continuous_webjob(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name, 'continuouswebjobs') + '/start',
                 method='POST')


def stop_silo_continuous_webjob(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name, 'continuouswebjobs') + '/stop',
                 method='POST')


def list_silo_triggered_webjobs(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/triggeredwebjobs', collection=True)


def show_silo_triggered_webjob(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name, 'triggeredwebjobs'))


def list_silo_webjob_history(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name, 'triggeredwebjobs') + '/history',
                 collection=True)


def show_silo_webjob_history(cmd, resource_group_name, name, silo, webjob_name, run_id):
    return _site(cmd, resource_group_name, name, silo,
                 _webjob(webjob_name, 'triggeredwebjobs') + '/history/' + segment(run_id))


def run_silo_triggered_webjob(cmd, resource_group_name, name, silo, webjob_name):
    return _site(cmd, resource_group_name, name, silo, _webjob(webjob_name, 'triggeredwebjobs') + '/run',
                 method='POST')


def list_silo_site_extensions(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/siteextensions', collection=True)


def show_silo_site_extension(cmd, resource_group_name, name, silo, extension_name):
    return _site(cmd, resource_group_name, name, silo, '/siteextensions/' + segment(extension_name))


def check_silo_connectivity(cmd, resource_group_name, name, silo, body):
    return _site(cmd, resource_group_name, name, silo, '/connectivityCheck', method='POST', body=load_json(body))


def check_silo_dns(cmd, resource_group_name, name, silo, body):
    return _site(cmd, resource_group_name, name, silo, '/dnsCheck', method='POST', body=load_json(body))


def check_silo_tcp(cmd, resource_group_name, name, silo, body):
    return _site(cmd, resource_group_name, name, silo, '/tcpPingCheck', method='POST', body=load_json(body))


def invoke_silo_extension(cmd, resource_group_name, name, silo, instance, path, method='GET',
                          body=None, content_type=None, file=None, overwrite=False, uri_parameters=None):
    if method.upper() not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'):
        raise InvalidArgumentValueError('Provide a supported HTTP method.')
    if not path or path.startswith('/') or '\\' in path or '?' in path or '#' in path:
        raise InvalidArgumentValueError('--path must be a relative extension path without a query or fragment.')
    parts = path.split('/')
    for part in parts:
        decoded = part
        for _ in range(3):
            decoded = unquote(decoded)
        segment(decoded)
    suffix = _instance(instance) + '/extensions/' + '/'.join(quote(unquote(part), safe='') for part in parts)
    if body is not None and (not content_type or 'json' in content_type.lower()):
        body = load_json(body, expected_type=None)
        if body is None:
            body = b'null'
    elif isinstance(body, str) and body.startswith('@'):
        try:
            with open(body[1:], 'rb') as handle:
                body = handle.read()
        except OSError as ex:
            raise FileOperationError('Unable to read the request body file: {}.'.format(ex.strerror)) from ex
    query = {}
    for parameter in uri_parameters or []:
        key, separator, value = parameter.partition('=')
        if not key or not separator or key.lower() == 'api-version':
            raise InvalidArgumentValueError('--uri-parameters accepts KEY=VALUE pairs other than api-version.')
        query.setdefault(key, []).append(value)
    return _site(cmd, resource_group_name, name, silo, suffix, method=method.upper(), body=body,
                 content_type=content_type, filename=file, overwrite=overwrite, query=query)


def show_silo_onedeploy_status(cmd, resource_group_name, name, silo, instance=None):
    return _site(cmd, resource_group_name, name, silo, '/extensions/onedeploy', query={'instanceId': instance})


def show_silo_msdeploy_log(cmd, resource_group_name, name, silo, instance=None):
    return _site(cmd, resource_group_name, name, silo, '/extensions/MSDeploy/log', query={'instanceId': instance})


def list_silo_instances(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/instances', collection=True)


def show_silo_instance(cmd, resource_group_name, name, silo, instance):
    return _site(cmd, resource_group_name, name, silo, '/instances/' + segment(instance))


def show_silo_config(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/web')


def list_silo_config(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config', collection=True)


def list_silo_config_snapshots(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/web/snapshots', collection=True)


def show_silo_config_snapshot(cmd, resource_group_name, name, silo, snapshot_id, include_secrets=False):
    return _site(cmd, resource_group_name, name, silo,
                 '/config/web/snapshots/' + segment(snapshot_id) + ('/listsecrets' if include_secrets else ''),
                 method='POST' if include_secrets else 'GET')


def list_silo_keyvault_references(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/configreferences/connectionstrings', collection=True)


def refresh_silo_keyvault_references(cmd, resource_group_name, name, silo, force_restart=None):
    return _site(cmd, resource_group_name, name, silo, '/config/configreferences/appsettings/refresh',
                 method='POST', query={'forceRestart': _boolean(force_restart)})


def list_silo_detected_stacks(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/detectedstacks')


def list_silo_appsettings(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/appsettings/list', method='POST')


def list_silo_storage_accounts(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/azurestorageaccounts/list', method='POST')


def show_silo_connection_strings(cmd, resource_group_name, name, silo, key=None):
    suffix = '/config/web/connectionstrings/' + segment(key) if key is not None else '/config/connectionstrings'
    return _site(cmd, resource_group_name, name, silo, suffix, method='POST' if key is not None else 'GET')


def list_silo_connection_strings(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/connectionstrings/list', method='POST')


def show_silo_auth(cmd, resource_group_name, name, silo, metadata_only=False):
    return _site(cmd, resource_group_name, name, silo,
                 '/config/authsettings' + ('' if metadata_only else '/list'),
                 method='GET' if metadata_only else 'POST')


def show_silo_auth_v2(cmd, resource_group_name, name, silo, legacy=False):
    return _site(cmd, resource_group_name, name, silo, '/config/authsettingsV2' + ('/list' if legacy else ''))


def show_silo_push_settings(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/pushsettings/list', method='POST')


def list_silo_metadata(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/metadata/list', method='POST')


def show_silo_log_config(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/config/logs')


def list_silo_premier_addons(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/premieraddons', collection=True)


def show_silo_premier_addon(cmd, resource_group_name, name, silo, addon_name):
    return _site(cmd, resource_group_name, name, silo, '/premieraddons/' + segment(addon_name))


def list_silo_metrics(cmd, resource_group_name, name, silo, start_time=None, end_time=None,
                      time_grain=None, names=None, filter_string=None, details=None, slot_view=None):
    query = _metric_query(start_time, end_time, time_grain, names, filter_string)
    query['details'] = _boolean(details)
    query['slotView'] = _boolean(slot_view)
    return _site(cmd, resource_group_name, name, silo, '/metrics', query=query, collection=True)


def list_silo_metric_definitions(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/metricdefinitions', collection=True)


def list_silo_perf_counters(
        cmd, resource_group_name, name, silo, start_time=None, end_time=None,
        time_grain=None, names=None, filter_string=None):
    return _site(cmd, resource_group_name, name, silo, '/perfcounters',
                 query=_metric_query(start_time, end_time, time_grain, names, filter_string), collection=True)


def restart_site_silo(
        cmd, resource_group_name, name, silo, soft_restart=None, synchronous=None,
        no_wait=False, timeout=DEFAULT_TIMEOUT):
    return _site(cmd, resource_group_name, name, silo, '/restart', method='POST',
                 query={'softRestart': _boolean(soft_restart), 'synchronous': _boolean(synchronous)},
                 no_wait=no_wait, timeout=timeout)


def start_site_silo(cmd, resource_group_name, name, silo, no_wait=False, timeout=DEFAULT_TIMEOUT):
    return _site(cmd, resource_group_name, name, silo, '/start', method='POST', no_wait=no_wait, timeout=timeout)


def stop_site_silo(cmd, resource_group_name, name, silo, no_wait=False, timeout=DEFAULT_TIMEOUT):
    return _site(cmd, resource_group_name, name, silo, '/stop', method='POST', no_wait=no_wait, timeout=timeout)


def start_silo_network_trace(
        cmd, resource_group_name, name, silo, duration=None, max_frame_length=None,
        sas_url=None, legacy=False, no_wait=False, timeout=DEFAULT_TIMEOUT):
    return _site(cmd, resource_group_name, name, silo, '/networkTrace/start' + ('' if legacy else 'Operation'),
                 method='POST', query={
                     'durationInSeconds': duration, 'maxFrameLength': max_frame_length, 'sasUrl': sas_url},
                 no_wait=no_wait, timeout=timeout)


def stop_silo_network_trace(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/networkTrace/stop', method='POST')


def show_silo_network_trace_operation(cmd, resource_group_name, name, silo, operation_id):
    return _site(cmd, resource_group_name, name, silo, '/networkTrace/operationresults/' + segment(operation_id))


def show_silo_network_trace(cmd, resource_group_name, name, silo, operation_id):
    return _site(cmd, resource_group_name, name, silo, '/networkTrace/' + segment(operation_id))


def show_silo_runtime_operation(cmd, resource_group_name, name, silo, operation_id):
    return _site(cmd, resource_group_name, name, silo, '/operations/' + segment(operation_id))


def scan_silo_antivirus(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/antivirus/queue', method='POST')


def show_silo_antivirus_config(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/antivirus/config')


def update_silo_antivirus_config(cmd, resource_group_name, name, silo, body):
    return _site(cmd, resource_group_name, name, silo, '/antivirus/config', method='PUT', body=load_json(body))


def list_silo_antivirus_logs(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/antiviruslogs')


def show_silo_antivirus_log(cmd, resource_group_name, name, silo, scan_id, include_file_paths=False):
    return _site(cmd, resource_group_name, name, silo,
                 '/antiviruslogs/' + segment(scan_id) + ('/list' if include_file_paths else ''),
                 method='POST' if include_file_paths else 'GET')


def list_silo_deployment_statuses(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/deploymentStatus', collection=True)


def list_silo_sitecontainers(cmd, resource_group_name, name, silo):
    return _site(cmd, resource_group_name, name, silo, '/sitecontainers', collection=True)


def show_silo_sitecontainer(cmd, resource_group_name, name, silo, container_name):
    return _site(cmd, resource_group_name, name, silo, '/sitecontainers/' + segment(container_name))


def silo_table(result):
    rows = result if isinstance(result, list) else [result]
    output = []
    for row in rows:
        if row.get('status') == 'Accepted':
            output.append({'Status': 'Accepted', 'Operation': row.get('operationId'),
                           'Resource': row.get('resourceId')})
            continue
        properties = row.get('properties') or {}
        output.append({
            'Name': row.get('name'), 'Location': row.get('location'),
            'State': properties.get('provisioningState'), 'Revision': properties.get('revisionNumber'),
            'FollowLastKnownGood': properties.get('followLastKnownGood'),
            'Endpoint': properties.get('endpointStatus'), 'Monitor': properties.get('monitorStatus'),
            'Error': properties.get('errorCode'),
        })
    return output
