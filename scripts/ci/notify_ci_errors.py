#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import os
import requests
import sys


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


teams_api_url = sys.argv[1]
teams_api_key = sys.argv[2]
teams_channel_id = sys.argv[3]
# https://dev.azure.com/azclitools/
base_uri = os.environ.get('BASE_URI', False)
# public
project_type = os.environ.get('PROJECT_TYPE', False)
# 45514
build_id = os.environ.get('BUILD_ID', False)
# 15eab87b-4a33-5480-11eb-66f5d5b3681b
job_id = os.environ.get('JOB_ID', False)


def notify_batch_ci_errors():
    if all([base_uri, project_type, build_id, job_id]):
        # https://dev.azure.com/azclitools/public/_build/results?buildId=45514&view=logs&j=15eab87b-4a33-5480-11eb-66f5d5b3681b
        url = f'{base_uri}{project_type}/_build/results?buildId={build_id}&view=logs&j={job_id}'

        data = {
            "title": "Batch CI Error Appears!",
            "body": "Azure cli team,\n\nPlease click to take a look at the batch CI error.",
            "notificationUrl": url,
            "targetType": "channel",
            "recipients": teams_channel_id
        }
        headers = {
          'x-api-key': teams_api_key
        }

        response = requests.request("POST", teams_api_url, headers=headers, data=data)
        logger.debug('Status Code: %s', response.status_code)
        logger.debug('Response Content: %s', response.content)
    else:
        logger.error('Missing variables: \nBASE_URI: %s, PROJECT_TYPE: %s, '
                     'BUILD_ID: %s, JOB_ID: %s', base_uri, project_type, build_id, job_id)


if __name__ == '__main__':
    notify_batch_ci_errors()
