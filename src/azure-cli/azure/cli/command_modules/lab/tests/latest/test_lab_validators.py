# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import patch

from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.aaz import AAZArgumentsSchema, AAZBoolArg, AAZStrArg, has_value
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.lab.custom import LabVmCreate
from azure.cli.command_modules.lab.validators import (_update_artifacts, _validate_other_parameters,
                                                      validate_authentication_type)


class ValidatorsCommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vm_create_schema = LabVmCreate.get_arguments_schema()
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

    def test_formula_authentication_preserves_supplied_password_when_response_omits_password(self):
        args = self._authentication_args(password='supplied-password')
        formula = {
            'formulaContent': {
                'isAuthenticationWithSshKey': False,
                'userName': 'formula-user'
            }
        }

        validate_authentication_type(args, formula)

        self.assertEqual('supplied-password', args.password.to_serialized_data())

    def test_formula_authentication_prompts_when_response_omits_password(self):
        args = self._authentication_args()
        formula = {
            'formulaContent': {
                'isAuthenticationWithSshKey': False,
                'userName': 'formula-user'
            }
        }

        with patch('knack.prompting.prompt_pass', return_value='prompted-password'):
            validate_authentication_type(args, formula)

        self.assertEqual('prompted-password', args.password.to_serialized_data())

    def test_formula_authentication_uses_legacy_response_password_when_not_supplied(self):
        args = self._authentication_args()
        formula = {
            'formulaContent': {
                'isAuthenticationWithSshKey': False,
                'userName': 'formula-user',
                'password': 'formula-password'
            }
        }

        validate_authentication_type(args, formula)

        self.assertEqual('formula-password', args.password.to_serialized_data())

    def test_formula_authentication_prefers_supplied_password_over_legacy_response_password(self):
        args = self._authentication_args(password='supplied-password')
        formula = {
            'formulaContent': {
                'isAuthenticationWithSshKey': False,
                'userName': 'formula-user',
                'password': 'formula-password'
            }
        }

        validate_authentication_type(args, formula)

        self.assertEqual('supplied-password', args.password.to_serialized_data())

    def test_formula_without_optional_properties(self):
        # The service omits formula properties that are not set, such as tags and artifacts.
        formula = {
            'osType': 'Linux',
            'formulaContent': {
                'size': 'Standard_B2s'
            }
        }
        for tags in (None, {'Tag': 'Value'}):
            args = self._vm_create_args(tags=tags)

            _validate_other_parameters(args, formula)

            if tags:
                self.assertEqual(tags, args.tags.to_serialized_data())
            else:
                self.assertFalse(has_value(args.tags))
            self.assertFalse(has_value(args.allow_claim))
            self.assertFalse(has_value(args.artifacts_org))
            self.assertFalse(has_value(args.notes))
            self.assertFalse(has_value(args.storage_type))
            self.assertEqual('Standard_B2s', args.size.to_serialized_data())
            self.assertEqual('Linux', args.os_type.to_serialized_data())

    def test_formula_properties_are_copied(self):
        formula = {
            'osType': 'Windows',
            'tags': {'Tag': 'Value'},
            'formulaContent': {
                'allowClaim': True,
                'artifacts': [{'artifactId': '/artifactsources/public repo/artifacts/linux-java'}],
                'notes': 'formula notes',
                'size': 'Standard_B2s',
                'storageType': 'Premium'
            }
        }
        args = self._vm_create_args()

        _validate_other_parameters(args, formula)

        self.assertEqual({'Tag': 'Value'}, args.tags.to_serialized_data())
        self.assertTrue(args.allow_claim.to_serialized_data())
        self.assertEqual([{'artifact_id': '/artifactsources/public repo/artifacts/linux-java'}],
                         args.artifacts_org.to_serialized_data())
        self.assertEqual('formula notes', args.notes.to_serialized_data())
        self.assertEqual('Standard_B2s', args.size.to_serialized_data())
        self.assertEqual('Premium', args.storage_type.to_serialized_data())
        self.assertEqual('Windows', args.os_type.to_serialized_data())

    def test_formula_authentication_without_authentication_properties(self):
        args = self._authentication_args(password='supplied-password')

        validate_authentication_type(args, {'formulaContent': {'size': 'Standard_B2s'}})

        self.assertEqual('password', args.authentication_type.to_serialized_data())
        self.assertEqual('supplied-password', args.password.to_serialized_data())

    def _vm_create_args(self, tags=None):
        data = {'name': 'MyVM', 'lab_name': 'MyLab', 'resource_group': 'MyRG', 'formula': 'MyFormula'}
        if tags is not None:
            data['tags'] = tags
        return self.vm_create_schema(data)

    @staticmethod
    def _authentication_args(password=None):
        args_schema = AAZArgumentsSchema()
        args_schema.authentication_type = AAZStrArg()
        args_schema.generate_ssh_keys = AAZBoolArg()
        args_schema.os_type = AAZStrArg()
        args_schema.password = AAZStrArg()
        args_schema.saved_secret = AAZStrArg()
        args_schema.ssh_key = AAZStrArg()
        args_schema.user_name = AAZStrArg()

        data = {
            'authentication_type': 'password',
            'generate_ssh_keys': False,
            'os_type': 'Windows'
        }
        if password is not None:
            data['password'] = password
        return args_schema(data)
