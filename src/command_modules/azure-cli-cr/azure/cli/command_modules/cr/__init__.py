#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# Add command module logic to this package.

import httplib
import base64
import json

from azure.cli.commands import cli_command

def obtain_data_from_registry(registry, username, password, path, resultIndex):
    registryEndpoint = registry + '.azurecr.io'
    tokenSeed = username + ':' + password
    token = 'Basic ' + base64.b64encode(tokenSeed)
    headers = {"Authorization": token}
    conn = httplib.HTTPSConnection(registryEndpoint)
    aggregateList = []
    executeNextHttpCall = True
    while executeNextHttpCall:
        executeNextHttpCall = False
        conn.request('GET', path, None, headers)
        res = conn.getresponse()
        if res.status == 200:
            linkHeader = res.getheader('link')
            if linkHeader <> None:
                # the registry is telling us there's more items in the list, and another call is needed
                # the link header looks something like `Link: </v2/_catalog?last=hello-world&n=1>; rel="next"`
                # we should follow the next path indicated in the link header
                path = linkHeader[(linkHeader.index('<')+1):linkHeader.index('>')]
                executeNextHttpCall = True
            repos = json.loads(res.read())[resultIndex]
            for repo in repos:
                aggregateList.append(repo)
    return {resultIndex: aggregateList}

def cr_catalog(registry, username, password):
    '''Returns the catalog of containers in the specified registry.
    :param str registry: The name of your Azure container registry
    :param str username: The user name used to log into the container registry
    :param str password: The password used to log into the container registry
    '''
    path = '/v2/_catalog'
    return obtain_data_from_registry(registry, username, password, path, 'repositories')

def cr_tags(registry, username, password, container):
    '''Returns the list of tags for a given container in the specified registry.
    :param str registry: The name of your Azure container registry
    :param str username: The user name used to log into the container registry
    :param str password: The password used to log into the container registry
    :param str container: The container to obtain tags from
    '''
    path = '/v2/' + container + '/tags/list'
    return obtain_data_from_registry(registry, username, password, path, 'tags')

cli_command('cr catalog', cr_catalog)
cli_command('cr tags', cr_tags)
