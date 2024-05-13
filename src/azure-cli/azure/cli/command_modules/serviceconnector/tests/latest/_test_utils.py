# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload


class CredentialReplacer(RecordingProcessor):

    def recursive_hide(self, props):
        # hide sensitive data recursively
        fake_content = 'hidden'
        sensitive_keys = ['secret']
        sensitive_data = ['password=', 'key=']

        if isinstance(props, dict):
            for key in props:
                if key in sensitive_keys:
                    props[key] = fake_content
                props[key] = self.recursive_hide(props[key])
        elif isinstance(props, list):
            for index, val in enumerate(props):
                props[index] = self.recursive_hide(val)
        elif isinstance(props, str):
            for data in sensitive_data:
                if data in props.lower():
                    props = fake_content

        return props

    def process_request(self, request):
        import json

        # hide secrets in request body
        if is_text_payload(request) and request.body and json.loads(request.body):
            body = self.recursive_hide(json.loads(request.body))
            request.body = json.dumps(body)

        # hide token in header
        if 'x-ms-cupertino-test-token' in request.headers:
            request.headers['x-ms-cupertino-test-token'] = 'hidden'
        if 'x-ms-serviceconnector-user-token' in request.headers:
            request.headers['x-ms-serviceconnector-user-token'] = 'hidden'

        return request

    def process_response(self, response):
        import json

        if is_text_payload(response) and response['body']['string']:
            try:
                body = json.loads(response['body']['string'])
                body = self.recursive_hide(body)
                response['body']['string'] = json.dumps(body)
            except Exception:  # pylint: disable=broad-except
                pass

        return response

MASK_ID = '00000000-0000-0000-0000-000000000000'

class ConfigCredentialReplacer(RecordingProcessor):

    def process_request(self, request):
        if is_text_payload(request) and request.body and isinstance(request.body, str):
            request.body = self._replace_ids_str(request.body)
            request.body = self._replace_name_value_keys_str(request.body)
        elif is_text_payload(request) and request.body and isinstance(request.body, bytes):
            request.body = self._replace_ids_bytes(request.body)
            request.body = self._replace_name_value_keys_bytes(request.body)
        
        return request
    
    def process_response(self, response):
        if is_text_payload(response) and response['body']['string']:
            response['body']['string'] = self._replace_name_value_keys_str(response['body']['string'])
            response['body']['string'] = self._replace_ids_str(response['body']['string'])
        return response

    def _replace_name_value_keys_str(self, res):
        import re
        sensitive_key = [r'secret', r'key', r'clientid']

        for key in sensitive_key:
            if key in res.lower():
                res = re.sub(r'("name":( ?)"[^"]*{}[^"]*",( ?)"value":( ?))"[^"]*"'.format(key), 
                             r'\1"HIDDEN"', 
                             res, flags=re.IGNORECASE)

        if 'vault' in res.lower() or 'rawvalue' in res.lower():
            res = re.sub(r'("value":( ?))"[^"]*"',
                         r'\1"HIDDEN"',
                         res, flags=re.IGNORECASE)

        return res
    
    def _replace_name_value_keys_bytes(self, res):
        import re
        sensitive_key = [b'secret', b'key', b'clientid']

        for key in sensitive_key:
            if key in res.lower():
                res = re.sub(rb'("name":( ?)"[^"]*' + key + rb'[^"]*",( ?)"value":( ?))"[^"]*"', 
                             rb'\1"HIDDEN"', 
                             res, flags=re.IGNORECASE)

        if b'vault' in res.lower() or b'rawvalue' in res.lower():
            res = re.sub(rb'("value":( ?))"[^"]*"',
                         rb'\1"HIDDEN"',
                         res, flags=re.IGNORECASE)

        return res

    def _replace_ids_str(self, req):
        import re

        sensitive_ids = [r'subscriptionId', r'tenantId', r'clientId', r'principalId']
        for sensitive_id in sensitive_ids:
            if sensitive_id in req:
                req = re.sub(r'"' + sensitive_id + '":( ?)"[^"]*"', 
                             r'"'+ sensitive_id + '" :"'+ MASK_ID + r'"', 
                             req, flags=re.IGNORECASE)
        return req

    def _replace_ids_bytes(self, req):
        import re

        sensitive_ids = [b'subscriptionId', b'tenantId', b'clientId', b'principalId']
        for sensitive_id in sensitive_ids:
            if sensitive_id in req:
                req = re.sub(b'"' + sensitive_id + b'":( ?)"[^"]*"', 
                             b'"'+ sensitive_id + b'":"'+ MASK_ID.encode() + b'"', 
                             req, flags=re.IGNORECASE)
        
        return req