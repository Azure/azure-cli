# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestAAZHttpOperation(unittest.TestCase):

    def test_aaz_http_operation_serialize_content(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZDictType, AAZStrType, AAZIntType
        from azure.cli.core.aaz._operation import AAZHttpOperation

        # test required Case 1
        schema = AAZObjectType(flags={"required": True})
        schema.properties = AAZObjectType(flags={"required": True})

        v = schema._ValueCls(schema=schema, data=schema.process_data(None))
        data = AAZHttpOperation.serialize_content(v)
        self.assertEqual(data, {"properties": {}})

        schema.properties.prop1 = AAZListType(flags={"required": True})
        schema.properties.prop2 = AAZDictType(flags={"required": True}, serialized_name='property2')

        schema.properties.prop3 = AAZObjectType()
        schema.properties.prop4 = AAZObjectType(flags={"required": True, "read_only": True})
        schema.properties.prop5 = AAZDictType(flags={"required": True, "read_only": True}, serialized_name='Prop5')
        schema.properties.prop6 = AAZListType(flags={"required": True, "read_only": True})

        v = schema._ValueCls(schema=schema, data=schema.process_data(None))
        data = AAZHttpOperation.serialize_content(v)
        self.assertEqual(data, {"properties": {'prop1': [], "property2": {}}})

        # test required Case 2
        schema = AAZObjectType(flags={"required": True})
        schema.properties = AAZObjectType()
        schema.properties.prop1 = AAZListType(flags={"required": True})
        schema.properties.prop2 = AAZDictType(flags={"required": True})
        schema.properties.prop3 = AAZObjectType()
        schema.properties.prop3.sub1 = AAZIntType(serialized_name="subProperty1")
        schema.properties.prop4 = AAZStrType(flags={"required": True, "read_only": True})

        v = schema._ValueCls(schema=schema, data=schema.process_data(None))
        data = AAZHttpOperation.serialize_content(v)
        self.assertEqual(data, {})

        v = schema._ValueCls(schema=schema, data=schema.process_data(None))
        v.properties.prop3.sub1 = 6
        self.assertTrue(v._is_patch)
        data = AAZHttpOperation.serialize_content(v)
        self.assertEqual(data, {'properties': {'prop3': {'subProperty1': 6}, 'prop1': [], 'prop2': {}}})

        schema.properties.prop3.sub2 = AAZStrType(flags={"required": True})
        v = schema._ValueCls(schema=schema, data=schema.process_data(None))
        v.properties.prop3.sub1 = 6
        with self.assertRaises(ValueError):
            AAZHttpOperation.serialize_content(v)
