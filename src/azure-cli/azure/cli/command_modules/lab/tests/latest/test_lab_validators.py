# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import unittest
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.aaz import AAZArgumentsSchema, AAZDateTimeArg
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.lab.validators import _update_artifacts, _validate_expiration_date


class ValidatorsCommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jdk_artifact = {'artifact_id': '/artifactsources/public repo/artifacts/linux-java',
                            'deploymentStatusMessage': None,
                            'installTime': None,
                            'parameters': [],
                            'status': None,
                            'vmExtensionStatusMessage': None}
        cls.apt_get_artifact = {'artifact_id': '/artifactsources/public repo/artifacts/linux-java',
                                'deploymentStatusMessage': None,
                                'installTime': None,
                                'parameters': [{'name': 'packages',
                                                'value': 'abcd'},
                                               {'name': 'update',
                                                'value': 'true'},
                                               {'name': 'options',
                                                'value': ''}],
                                'status': None,
                                'vmExtensionStatusMessage': None}
        cls.lab_resource_id = "/subscriptions/abcd-abcd-abcd-abcd-abcd/resourceGroups/MyRG/" \
                              "providers/Microsoft.DevTestLab/labs/MyLab"
        cls.full_artifact = {'artifact_id': '/subscriptions/abcd-abcd-abcd-abcd-abcd/resourceGroups'
                                            '/MyRG/providers/Microsoft.DevTestLab/labs/MyLab'
                                            '/artifactsources/public repo/artifacts/linux-java',
                             'parameters': []}

    def test_update_artifacts(self):
        result = _update_artifacts([], self.lab_resource_id)
        assert result == []

        result = _update_artifacts([self.jdk_artifact], self.lab_resource_id)
        for artifact in result:
            assert is_valid_resource_id(artifact.get('artifact_id'))
            self.assertEqual('{}{}'.format(self.lab_resource_id,
                                           self.jdk_artifact.get('artifact_id')),
                             artifact.get('artifact_id'))

        result = _update_artifacts([self.jdk_artifact, self.apt_get_artifact],
                                   self.lab_resource_id)
        for artifact in result:
            assert is_valid_resource_id(artifact.get('artifact_id'))

        result = _update_artifacts([self.full_artifact, self.apt_get_artifact],
                                   self.lab_resource_id)
        for artifact in result:
            assert is_valid_resource_id(artifact.get('artifact_id'))
            self.assertEqual(artifact.get('artifact_id'), self.full_artifact.get('artifact_id'))

        with self.assertRaises(ArgumentUsageError):
            _update_artifacts({}, self.lab_resource_id)

        invalid_artifact = self.jdk_artifact
        del invalid_artifact['artifact_id']
        with self.assertRaises(ArgumentUsageError):
            _update_artifacts([invalid_artifact], self.lab_resource_id)


class ExpirationDateValidatorTest(unittest.TestCase):
    @staticmethod
    def _build_args(expiration_date=None):
        """ Builds the args `az lab vm create` hands to the validator. """
        schema = AAZArgumentsSchema()
        schema.expiration_date = AAZDateTimeArg(options=['--expiration-date'])
        command_args = {} if expiration_date is None else {'expiration_date': expiration_date}
        ctx = AAZCommandCtx(cli_ctx=DummyCli(), schema=schema, command_args=command_args)
        ctx.format_args()
        return ctx.args

    def test_expiration_date_in_future(self):
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)
        # No offset, a Z suffix and an explicit offset all reach the validator as UTC timestamps.
        for expiration_date in (future.strftime('%Y-%m-%d %H:%M:%S'),
                                future.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                future.strftime('%Y-%m-%d %H:%M:%S+00:00')):
            _validate_expiration_date(self._build_args(expiration_date))

    def test_expiration_date_in_past(self):
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)
        with self.assertRaises(ArgumentUsageError):
            _validate_expiration_date(self._build_args(past.strftime('%Y-%m-%dT%H:%M:%S.%fZ')))

    def test_expiration_date_not_provided(self):
        _validate_expiration_date(self._build_args())
