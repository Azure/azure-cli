# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.resource.custom import (_list_resources_odata_filter_builder,
                                                       _find_missing_parameters)
from azure.cli.core.parser import IncorrectUsageError


class TestDeployResource(unittest.TestCase):
    def test_find_missing_parameters_none(self):
        template = {
            "parameters": {
                "foo": {
                    "defaultValue": "blah"
                },
                "bar": {},
                "baz": {},
            }
        }

        missing = _find_missing_parameters(None, template)
        self.assertEqual(2, len(missing))

    def test_find_missing_parameters(self):
        parameters = {
            "foo": "value1",
            "bar": "value2"
        }

        template = {
            "parameters": {
                "foo": {
                    "defaultValue": "blah"
                },
                "bar": {},
                "baz": {},
            }
        }

        missing = _find_missing_parameters(parameters, template)
        self.assertEqual(1, len(missing))


class TestListResources(unittest.TestCase):
    def test_tag_name(self):
        odata_filter = _list_resources_odata_filter_builder(tag='foo')
        self.assertEqual(odata_filter, "tagname eq 'foo'")

    def test_tag_name_starts_with(self):
        odata_filter = _list_resources_odata_filter_builder(tag='f*')
        self.assertEqual(odata_filter, "startswith(tagname, 'f')")

    def test_tag_name_value_equals(self):
        odata_filter = _list_resources_odata_filter_builder(tag={'foo': 'bar'})
        self.assertEqual(odata_filter, "tagname eq 'foo' and tagvalue eq 'bar'")

    def test_name_location_equals_resource_type_equals(self):
        odata_filter = _list_resources_odata_filter_builder(
            name='wonky', location='dory', resource_provider_namespace='resource',
            resource_type='type')  # pylint: disable=line-too-long
        self.assertEqual(odata_filter,
                         "name eq 'wonky' and location eq 'dory' and resourceType eq 'resource/type'")  # pylint: disable=line-too-long

    def test_name_location_equals(self):
        odata_filter = _list_resources_odata_filter_builder(name='wonky', location='dory')
        self.assertEqual(odata_filter, "name eq 'wonky' and location eq 'dory'")

    def test_tag_and_name_fails(self):
        with self.assertRaises(IncorrectUsageError):
            _list_resources_odata_filter_builder(tag='foo=bar', name='should not work')


if __name__ == '__main__':
    unittest.main()
