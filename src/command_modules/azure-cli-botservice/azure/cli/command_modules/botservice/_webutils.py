# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import requests
import urllib3
from knack.util import CLIError
from .web_app_operations import WebAppOperations


# TODO: Part of KUDU refactor
# TODO: Add other pertinent KUDU methods
def enable_zip_deploy(cmd, resource_group_name, name, src, slot=None):
    user_name, password = WebAppOperations.get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)
    scm_url = WebAppOperations.get_scm_url(cmd, resource_group_name, name, slot)
    zip_url = scm_url + '/api/zipdeploy'

    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization
    headers['content-type'] = 'application/octet-stream'

    # Read file content
    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        r = requests.post(zip_url, data=zip_content, headers=headers)
        if r.status_code != 200:
            raise CLIError("Zip deployment {} failed with status code '{}' and reason '{}'".format(
                zip_url, r.status_code, r.text))

    # on successful deployment navigate to the app, display the latest deployment json response
    response = requests.get(scm_url + '/api/deployments/latest', headers=authorization)
    return response.json()
