# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.testsdk.scenario_tests import RecordingProcessor


class ExpressRoutePortLOAContentReplacer(RecordingProcessor):

    def process_response(self, response):
        import json
        import base64

        body = response['body']['string']

        json_body = json.loads(body)
        json_body['encodedContent'] = base64.b64encode('Raw bytes of a PDF content replaced by ExpressRoutePortLOAContentReplacer'.encode('utf-8')).decode('utf-8')

        response['body']['string'] = json.dumps(json_body)

        return response
