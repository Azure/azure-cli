# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import requests

from azure.cli.core.prompting import prompt, prompt_pass, NoTTYException
from azure.cli.core.util import CLIError

from ._utils import (
    get_registry_by_name
)
from .credential import acr_credential_show


def _obtain_data_from_registry(login_server, path, resultIndex, username, password):
    registryEndpoint = 'https://' + login_server
    resultList = []
    executeNextHttpCall = True

    while executeNextHttpCall:
        executeNextHttpCall = False
        response = requests.get(
            registryEndpoint + path,
            auth=requests.auth.HTTPBasicAuth(
                username,
                password
            )
        )

        if response.status_code == 200:
            resultList += response.json()[resultIndex]
            if 'link' in response.headers and response.headers['link']:
                linkHeader = response.headers['link']
                # The registry is telling us there's more items in the list,
                # and another call is needed. The link header looks something
                # like `Link: </v2/_catalog?last=hello-world&n=1>; rel="next"`
                # we should follow the next path indicated in the link header
                path = linkHeader[(linkHeader.index('<') + 1):linkHeader.index('>')]
                executeNextHttpCall = True
        elif response.status_code == 401:
            raise CLIError('Invalid username or password specified.')
        else:
            raise CLIError(json.loads(response.text)['errors'][0]['message'])

    return resultList


def _validate_user_credentials(registry_name, path, resultIndex, username=None, password=None):
    registry, _ = get_registry_by_name(registry_name)
    login_server = registry.login_server  # pylint: disable=no-member

    if username:
        if not password:
            try:
                password = prompt_pass(msg='Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')
        return _obtain_data_from_registry(login_server, path, resultIndex, username, password)

    try:
        cred = acr_credential_show(registry_name)
        username = cred.username
        password = cred.passwords[0].value
        return _obtain_data_from_registry(login_server, path, resultIndex, username, password)
    except:  # pylint: disable=bare-except
        pass

    try:
        username = prompt('Username: ')
        password = prompt_pass(msg='Password: ')
    except NoTTYException:
        raise CLIError(
            'Unable to authenticate using admin login credentials or admin is not enabled. ' +
            'Please specify both username and password in non-interactive mode.')
    return _obtain_data_from_registry(login_server, path, resultIndex, username, password)


def acr_repository_list(registry_name, username=None, password=None):
    """Lists repositories in the specified container registry.
    :param str registry_name: The name of container registry
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    path = '/v2/_catalog'
    return _validate_user_credentials(registry_name, path, 'repositories', username, password)


def acr_repository_show_tags(registry_name, repository, username=None, password=None):
    """Shows tags of a given repository in the specified container registry.
    :param str registry_name: The name of container registry
    :param str repository: The repository to obtain tags from
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    path = '/v2/' + repository + '/tags/list'
    return _validate_user_credentials(registry_name, path, 'tags', username, password)
