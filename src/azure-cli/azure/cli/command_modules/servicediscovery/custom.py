# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
import json

from knack.log import get_logger
logger = get_logger(__name__)

def _run_cli_cmd(cmd, retry=0, interval=0, should_retry_func=None):
    '''Run a CLI command
    :param cmd: The CLI command to be executed
    :param retry: The times to re-try
    :param interval: The seconds wait before retry
    '''
    import json
    import time
    import subprocess

    output = subprocess.run(cmd, shell=True, check=False,
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if output.returncode != 0 or (should_retry_func and should_retry_func(output)):
        if retry:
            time.sleep(interval)
            return _run_cli_cmd(cmd, retry - 1, interval)
        err = output.stderr.decode(encoding='UTF-8', errors='ignore')
        raise Exception('Command execution failed, command is: '
                               '{}, error message is: \n {}'.format(cmd, err))
    try:
        return json.loads(output.stdout.decode(encoding='UTF-8', errors='ignore')) if output.stdout else None
    except ValueError as e:
        return output.stdout or None


def create_namespace(cmd, ns_name, description='', app_config=None):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}'.format(ns_name)
    payload = {
        'description': description
    }

    response = requests.put(url, json=payload)
    return json.loads(response.text)


def create_service(cmd, ns_name, service, description='', protocol='HTTP'):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}'.format(ns_name, service)
    payload = {
        'description': description,
        'protocol': protocol
    }
    
    response = requests.put(url, json=payload)
    return json.loads(response.text)


def create_instance(cmd, ns_name, service, instance, description='', address='', port=0, metadata=dict(), connection_string=''):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances/{}'.format(ns_name, service, instance)
    if connection_string:
        metadata['connection_string'] = connection_string
    payload = {
        'description': description,
        'metadatas': metadata,
        'address': address,
        'port': port
    }

    response = requests.put(url, json=payload)
    return json.loads(response.text)


def delete_namespace(cmd, ns_name):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}'.format(ns_name)

    response = requests.delete(url)
    return json.loads(response.text)


def delete_service(cmd, ns_name, service):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}'.format(ns_name, service)

    response = requests.delete(url)
    return json.loads(response.text)


def delete_instance(cmd, ns_name, service, instance):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances/{}'.format(ns_name, service, instance)

    response = requests.delete(url)
    return json.loads(response.text)


def show_namespace(cmd, ns_name):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}'.format(ns_name)

    response = requests.get(url)
    return json.loads(response.text)


def show_service(cmd, ns_name, service):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}'.format(ns_name, service)

    response = requests.get(url)
    return json.loads(response.text)


def show_instance(cmd, ns_name, service, instance):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances/{}'.format(ns_name, service, instance)

    response = requests.get(url)
    return json.loads(response.text)


def list_namespace(cmd):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces'

    response = requests.get(url)
    return json.loads(response.text)


def list_service(cmd, ns_name):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services'.format(ns_name)

    response = requests.get(url)
    return json.loads(response.text)


def list_instance(cmd, ns_name, service):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances'.format(ns_name, service)

    response = requests.get(url)
    return json.loads(response.text)


def export_namespace(cmd, ns_name, app_config):
    instance_kv_pairs = dict()

    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services'.format(ns_name)
    response = requests.get(url)

    service_res = json.loads(response.text)
    
    # DB service nammes
    db_service_names = [res.get('id').split('/')[-1] for res in service_res if res.get('protocol') == 'DB']
    for service_name in db_service_names:
        url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances'.format(ns_name, service_name)
        response = requests.get(url)
        instance_res = json.loads(response.text)
        for instance in instance_res:
            instance_name = instance.get('id').split('/')[-1]
            conn_string = instance.get('metadatas', dict()).get('connection_string', '')
            if conn_string:
                instance_kv_pairs['ConnectionStrings:{}'.format(service_name)] = conn_string

    # HTTP service names
    http_service_names = [res.get('id').split('/')[-1] for res in service_res if res.get('protocol') == 'HTTP']
    for service_name in http_service_names:
        url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances'.format(ns_name, service_name)
        response = requests.get(url)
        instance_res = json.loads(response.text)
        for instance in instance_res:
            instance_name = instance.get('id').split('/')[-1]
            fqdn = instance.get('address', '')
            if 'azurecontainerapps.io' in fqdn:
                instance_kv_pairs['Services:{}'.format(service_name)] = fqdn

    import tempfile, datetime
    temp = tempfile.NamedTemporaryFile(mode='w', delete=False)
    temp.write(json.dumps(instance_kv_pairs, ensure_ascii=False))
    temp.flush()

    logger.warning("Service instances collected. Exporting to app config: {} ...".format(app_config))
    _run_cli_cmd('az appconfig kv import -n {} --source file --format json --path {} --yes'.format(app_config, temp.name))

    return {
        'Result': 'Succeeded',
        'Count of key-values exported': len(instance_kv_pairs),
        'Time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }