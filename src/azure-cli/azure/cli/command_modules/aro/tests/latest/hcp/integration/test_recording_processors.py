# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import types
import unittest

import yaml

from azure.cli.command_modules.aro.tests.latest.hcp.integration.test_aro_hcp_scenario import AroHcpRecordingProcessor


class AroHcpRecordingProcessorTest(unittest.TestCase):

    def setUp(self):
        self.processor = AroHcpRecordingProcessor()

    @staticmethod
    def _request(uri, body=None):
        return types.SimpleNamespace(uri=uri, body=body)

    @staticmethod
    def _response(body, headers=None):
        return {
            'body': {'string': body},
            'headers': headers or {},
        }

    def test_identity_values_are_consistent_between_response_and_request(self):
        response = self._response(json.dumps({
            'tenantId': '11111111-1111-1111-1111-111111111111',
            'principalId': '22222222-2222-2222-2222-222222222222',
            'clientId': '33333333-3333-3333-3333-333333333333',
        }))

        processed_response = self.processor.process_response(response)
        identity = json.loads(processed_response['body']['string'])
        request = self._request(
            'https://management.azure.com/roleAssignments/example',
            json.dumps({'principalId': '22222222-2222-2222-2222-222222222222'}).encode(),
        )
        processed_request = self.processor.process_request(request)
        assignment = json.loads(processed_request.body)

        self.assertEqual(identity['tenantId'], self.processor.MOCK_TENANT_ID)
        self.assertEqual(identity['principalId'], self.processor.MOCK_PRINCIPAL_ID)
        self.assertEqual(identity['clientId'], self.processor.MOCK_CLIENT_ID)
        self.assertEqual(assignment['principalId'], identity['principalId'])

    def test_preserves_bytes_response_body(self):
        response = self._response(json.dumps({
            'tenantId': '11111111-1111-1111-1111-111111111111',
            'name': 'example-resource',
        }).encode('utf-8'))

        processed = self.processor.process_response(response)

        self.assertIsInstance(processed['body']['string'], bytes)
        self.assertEqual(
            json.loads(processed['body']['string'])['tenantId'],
            self.processor.MOCK_TENANT_ID,
        )

    def test_normalizes_generated_role_assignment_ids(self):
        recorded_id = '11111111-1111-4111-8111-111111111111'
        replay_id = '22222222-2222-4222-8222-222222222222'
        recorded = self._response(json.dumps({
            'id': '/subscriptions/example/providers/Microsoft.Authorization/'
                  'roleAssignments/{}'.format(recorded_id),
        }))
        replay = self._request(
            'https://management.azure.com/subscriptions/example/providers/'
            'Microsoft.Authorization/roleAssignments/{}'.format(replay_id)
        )

        processed_recorded = self.processor.process_response(recorded)
        processed_replay = self.processor.process_request(replay)

        self.assertIn(
            '/roleAssignments/{}'.format(self.processor.MOCK_ROLE_ASSIGNMENT_ID),
            json.loads(processed_recorded['body']['string'])['id'],
        )
        self.assertIn(
            '/roleAssignments/{}'.format(self.processor.MOCK_ROLE_ASSIGNMENT_ID),
            processed_replay.uri,
        )

    def test_redacts_personal_data_and_lro_context(self):
        tenant_id = '11111111-1111-1111-1111-111111111111'
        response = self._response(
            json.dumps({
                'systemData': {
                    'createdBy': 'person@example.com',
                    'lastModifiedBy': 'person@example.com',
                },
                'issuer': 'https://uksouth.oic.aro-hcp.azure.com/{}/cluster'.format(tenant_id),
            }),
            {
                'Azure-AsyncOperation': [
                    'https://management.azure.com/operations/id?'
                    't=1&c=signed-context&s=signed-request&h=signed-hash'
                ],
                'WWW-Authenticate': [
                    'Bearer authorization="https://login.microsoftonline.com/{}"'.format(tenant_id)
                ],
                'x-ms-keyvault-network-info': ['addr=192.0.2.1'],
                'x-ms-operation-identifier': ['operation-id'],
            },
        )

        processed = self.processor.process_response(response)
        body = json.loads(processed['body']['string'])

        self.assertEqual(body['systemData']['createdBy'], self.processor.MOCK_USER_EMAIL)
        self.assertEqual(body['systemData']['lastModifiedBy'], self.processor.MOCK_USER_EMAIL)
        self.assertIn(self.processor.MOCK_TENANT_ID, body['issuer'])
        operation_url = processed['headers']['Azure-AsyncOperation'][0]
        self.assertIn('c=REDACTED', operation_url)
        self.assertIn('s=REDACTED', operation_url)
        self.assertIn('h=REDACTED', operation_url)
        self.assertIn(self.processor.MOCK_TENANT_ID, processed['headers']['WWW-Authenticate'][0])
        self.assertNotIn('x-ms-keyvault-network-info', processed['headers'])
        self.assertNotIn('x-ms-operation-identifier', processed['headers'])

    def test_redacts_graph_profile_and_credential_payload(self):
        profile = self._response(json.dumps({
            'id': '22222222-2222-2222-2222-222222222222',
            'displayName': 'Example Person',
            'mail': 'person@example.com',
            'userPrincipalName': 'person@example.com',
        }))
        processed_profile = self.processor.process_response(profile)

        credential_request = self._request(
            'https://management.azure.com/requestAdminCredential?'
            'c=signed-context&s=signed-request&h=signed-hash',
            json.dumps({'certificateSigningRequest': 'real-csr'}),
        )
        processed_request = self.processor.process_request(credential_request)

        self.assertEqual(
            json.loads(processed_profile['body']['string']),
            {'id': self.processor.MOCK_PRINCIPAL_ID},
        )
        self.assertEqual(
            json.loads(processed_request.body)['certificateSigningRequest'],
            'redacted-csr',
        )
        self.assertIn('c=REDACTED', processed_request.uri)
        self.assertIn('s=REDACTED', processed_request.uri)
        self.assertIn('h=REDACTED', processed_request.uri)

    def test_redacts_kubeconfig_credentials(self):
        kubeconfig = yaml.safe_dump({
            'clusters': [{
                'name': 'cluster',
                'cluster': {'certificate-authority-data': 'real-ca'},
            }],
            'users': [{
                'name': 'admin',
                'user': {
                    'client-certificate-data': 'real-certificate',
                    'client-key-data': 'real-private-key',
                },
            }],
        })

        processed = self.processor.process_response(
            self._response(json.dumps({'kubeconfig': kubeconfig}))
        )
        redacted = yaml.safe_load(json.loads(processed['body']['string'])['kubeconfig'])

        self.assertEqual(
            redacted['clusters'][0]['cluster']['certificate-authority-data'],
            self.processor.REDACTED_DATA,
        )
        self.assertEqual(
            redacted['users'][0]['user']['client-certificate-data'],
            self.processor.REDACTED_DATA,
        )
        self.assertEqual(
            redacted['users'][0]['user']['client-key-data'],
            self.processor.REDACTED_DATA,
        )


if __name__ == '__main__':
    unittest.main()