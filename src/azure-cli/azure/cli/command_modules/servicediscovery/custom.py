# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
import json

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


def create_namespace(cmd, ns_name, description=''):
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


def create_instance(cmd, ns_name, service, instance, description='', address=None, port=None, metadata=None):
    url = 'https://servicediscoverymvp.azurewebsites.net/namespaces/{}/services/{}/instances/{}'.format(ns_name, service, instance)
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