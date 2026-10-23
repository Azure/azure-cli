# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from vcr.request import Request

from azure.cli.testsdk.utilities import MSGraphUserProfileReplacer

ME_ID = '11111111-2222-3333-4444-555555555555'


def _user(display_name='Jane Li', given_name='Jane', surname='Li', user_id=ME_ID):
    return {'@odata.type': '#microsoft.graph.user', 'id': user_id, 'businessPhones': ['+1 555 0100'],
            'displayName': display_name, 'givenName': given_name, 'jobTitle': 'Engineer',
            'mail': 'test@example.com', 'mobilePhone': '+1 555 0101', 'officeLocation': 'Building 1',
            'surname': surname, 'userPrincipalName': 'test@example.com'}


def _response(obj, raw=None):
    return {'body': {'string': raw if raw is not None else json.dumps(obj)}}


class TestMSGraphUserProfileReplacer(unittest.TestCase):
    def _process(self, processor, uri, body, method='GET'):
        processor.process_request(Request(method, uri, None, {}))
        return processor.process_response(_response(body))['body']['string']

    def test_me_response_is_sanitized(self):
        rp = MSGraphUserProfileReplacer()
        result = json.loads(self._process(rp, 'https://graph.microsoft.com/v1.0/me', _user()))
        self.assertEqual(result['displayName'], 'Test User')
        self.assertEqual(result['givenName'], 'Test')
        self.assertEqual(result['surname'], 'User')
        self.assertEqual(result['businessPhones'], [])
        self.assertIsNone(result['mobilePhone'])
        self.assertIsNone(result['jobTitle'])
        self.assertIsNone(result['officeLocation'])
        self.assertEqual(result['id'], ME_ID)

    def test_short_surname_does_not_change_keys_or_identifiers(self):
        rp = MSGraphUserProfileReplacer()
        self._process(rp, 'https://graph.microsoft.com/v1.0/me', _user())
        page = {'@odata.nextLink': 'https://graph.microsoft.com/v1.0/users?$skiptoken=Li42',
                'value': [_user(display_name='Linda', given_name='Linda', surname='Lin', user_id='other')]}
        result = json.loads(self._process(rp, 'https://graph.microsoft.com/v1.0/users', page))
        self.assertIn('@odata.nextLink', result)
        self.assertEqual(result['@odata.nextLink'], page['@odata.nextLink'])
        self.assertEqual(result['value'][0]['displayName'], 'Linda')
        self.assertEqual(result['value'][0]['surname'], 'Lin')
        self.assertEqual(result['value'][0]['businessPhones'], [])

    def test_escaped_names_are_replaced(self):
        rp = MSGraphUserProfileReplacer()
        me = _user(display_name='José Núñez', given_name='José', surname='Núñez')
        raw = json.dumps(me)  # ensure_ascii escapes the names, e.g. Jos\u00e9
        self.assertIn('\\u00e9', raw)
        rp.process_request(Request('GET', 'https://graph.microsoft.com/v1.0/me', None, {}))
        result = rp.process_response(_response(None, raw=raw))['body']['string']
        self.assertNotIn('Jos', result)
        self.assertNotIn('N\\u00fa\\u00f1ez', result)

        other = {'value': [{'principalDisplayName': 'José Núñez', 'note': 'José Núñez owns this'}]}
        result = json.loads(self._process(rp, 'https://management.azure.com/x', other))
        self.assertEqual(result['value'][0]['principalDisplayName'], 'Test User')
        # only exact values are replaced
        self.assertEqual(result['value'][0]['note'], 'José Núñez owns this')

    def test_signed_in_user_in_directory_objects(self):
        rp = MSGraphUserProfileReplacer()
        self._process(rp, 'https://graph.microsoft.com/v1.0/me', _user())
        body = {'value': [_user(display_name='Jane L.', given_name='J', surname='L')]}
        result = json.loads(self._process(rp, 'https://graph.microsoft.com/v1.0/directoryObjects/getByIds',
                                          body, method='POST'))
        self.assertEqual(result['value'][0]['displayName'], 'Test User')
        self.assertEqual(result['value'][0]['surname'], 'User')

    def test_sovereign_cloud_me_endpoints(self):
        for uri in ('https://graph.microsoft.us/v1.0/me', 'https://dod-graph.microsoft.us/v1.0/me',
                    'https://microsoftgraph.chinacloudapi.cn/v1.0/me'):
            rp = MSGraphUserProfileReplacer()
            self._process(rp, uri, _user())
            result = json.loads(self._process(rp, 'https://management.azure.com/x', {'name': 'Jane Li'}))
            self.assertEqual(result['name'], 'Test User', uri)

    def test_non_json_and_unrelated_bodies_are_untouched(self):
        rp = MSGraphUserProfileReplacer()
        self.assertEqual(rp.process_response(_response(None, raw='not json'))['body']['string'], 'not json')
        raw = '{"a":  "b"}'
        self.assertEqual(rp.process_response(_response(None, raw=raw))['body']['string'], raw)

    def test_reset(self):
        rp = MSGraphUserProfileReplacer()
        self._process(rp, 'https://graph.microsoft.com/v1.0/me', _user())
        rp.reset()
        result = json.loads(self._process(rp, 'https://management.azure.com/x', {'name': 'Jane Li'}))
        self.assertEqual(result['name'], 'Jane Li')


if __name__ == '__main__':
    unittest.main()
