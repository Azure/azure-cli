# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os.path
from unittest import mock
from io import StringIO

from knack.util import CLIError
from azure.cli.command_modules.resource._validators import (
    _validate_deployment_name,
    validate_lock_parameters,
)


class NamespaceObject:
    pass


class TestResourceValidators(unittest.TestCase):
    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_validate_lock_params(self):
        valid = [
            {
                'test': 'just name',
                'name': 'foo'
            },
            {
                'test': 'name and group',
                'name': 'foo',
                'resource_group': 'foo',
            },
            {
                'test': 'name, group, type [compact]',
                'name': 'foo',
                'resource_group': 'bar',
                'resource_name': 'baz',
                'resource_type': 'Microsoft.Compute/VirtualMachines'
            },
            {
                'test': 'name, group, type, namespace',
                'name': 'foo',
                'resource_group': 'bar',
                'resource_name': 'baz',
                'resource_type': 'VirtualMachines',
                'resource_provider_namespace': 'Microsoft.Compute',
            },
            {
                'test': 'name, group, type, namespace, parent',
                'name': 'foo',
                'resource_group': 'bar',
                'resource_name': 'baz',
                'resource_type': 'VirtualMachines',
                'resource_provider_namespace': 'Microsoft.Compute',
                'parent_resource_path': 'Foo.Bar/baz',
            }
        ]
        for valid_namespace in valid:
            namespace_obj = NamespaceObject()
            for key in valid_namespace:
                setattr(namespace_obj, key, valid_namespace[key])
            try:
                # If unexpected invalid, this throws, so no need for asserts
                validate_lock_parameters(namespace_obj)
            except CLIError as ex:
                self.fail('Test {} failed. {}'.format(valid_namespace['test'], ex))

    def test_validate_lock_params_invalid(self):
        invalid = [
            {
                'test': 'just name and type',
                'name': 'foo',
                'resource_type': 'baz'
            },
            {
                'test': 'name and group and type',
                'name': 'foo',
                'resource_group': 'foo',
                'resource_type': 'bar',
            },
            {
                'test': 'name, group, no type',
                'name': 'foo',
                'resource_group': 'bar',
                'resource_name': 'baz',
            },
            {
                'test': 'name, group, type, namespace',
                'name': 'foo',
                'resource_group': 'bar',
                'resource_name': 'baz',
                'resource_provider_namespace': 'Microsoft.Compute',
            },
            {
                'test': 'name, group, type, namespace, parent',
                'name': 'foo',
                'resource_group': 'bar',
                'resource_type': 'VirtualMachines',
                'resource_provider_namespace': 'Microsoft.Compute',
                'parent_resource_path': 'Foo.Bar/baz',
            }
        ]
        for invalid_namespace in invalid:
            with self.assertRaises(CLIError):
                namespace_obj = NamespaceObject()
                for key in invalid_namespace:
                    setattr(namespace_obj, key, invalid_namespace[key])
                validate_lock_parameters(namespace_obj)

    def test_generate_deployment_name_from_file(self):
        # verify auto-gen from uri
        namespace = mock.MagicMock()
        namespace.template_uri = 'https://templates/template123.json?foo=bar'
        namespace.template_file = None
        namespace.deployment_name = None
        _validate_deployment_name(namespace)
        self.assertEqual('template123', namespace.deployment_name)

        namespace = mock.MagicMock()
        namespace.template_file = __file__
        namespace.template_uri = None
        namespace.deployment_name = None
        _validate_deployment_name(namespace)

        file_base_name = os.path.basename(__file__)
        file_base_name = file_base_name[:str.find(file_base_name, '.')]
        self.assertEqual(file_base_name, namespace.deployment_name)

        # verify use default if get a file content
        namespace = mock.MagicMock()
        namespace.template_file = '{"foo":"bar"}'
        namespace.template_uri = None
        namespace.deployment_name = None
        _validate_deployment_name(namespace)
        self.assertEqual('deployment1', namespace.deployment_name)


if __name__ == '__main__':
    unittest.main()
