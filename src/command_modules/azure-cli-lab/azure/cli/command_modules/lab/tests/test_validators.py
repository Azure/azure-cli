# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from knack.util import CLIError
from azure.cli.core.commands.arm import is_valid_resource_id
from azure.cli.command_modules.lab.validators import (_update_artifacts)


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

        with self.assertRaises(CLIError):
            _update_artifacts({}, self.lab_resource_id)

        invalid_artifact = self.jdk_artifact
        del invalid_artifact['artifact_id']
        with self.assertRaises(CLIError):
            _update_artifacts([invalid_artifact], self.lab_resource_id)
