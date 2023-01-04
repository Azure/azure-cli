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


class TestAAZGenericUpdateOperation(unittest.TestCase):

    def test_aaz_generic_update_operation(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZDictType, AAZStrType, AAZIntType
        from azure.cli.core.aaz._operation import AAZGenericInstanceUpdateOperation

        schema = AAZObjectType()
        schema.props = AAZObjectType()
        schema.props.i = AAZIntType()
        schema.props.s = AAZStrType()
        schema.props.l = AAZListType()
        schema.props.l.Element = AAZObjectType()
        schema.props.l.Element.s = AAZStrType()
        schema.props.l2 = AAZListType()
        schema.props.l2.Element = AAZIntType()
        schema.props.d = AAZDictType()
        schema.props.d.Element = AAZObjectType()
        schema.props.d.Element.s = AAZStrType()
        schema.props.d2 = AAZDictType()
        schema.props.d2.Element = AAZStrType()

        instance = schema._ValueCls(schema=schema, data=schema.process_data({
            "props": {
                "i": 123,
                "s": "abc",
                "l": [
                    {
                        "s": "la"
                    },
                    {
                        "s": "lb"
                    },
                    {
                        "s": "lc"
                    }
                ],
                "d": {
                    "a": {
                        "s": "da"
                    },
                    "b": {
                        "s": "db"
                    },
                    "c": {
                        "s": "dc"
                    }
                }
            }
        }))

        AAZGenericInstanceUpdateOperation._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("set", ["props.i=666"]),
                    ("set", ["props.s=sss"]),
                    ("set", ["props.l[2].s='l2'"]),
                    ("set", ["props.l2=[123,123]"]),
                    ("set", ["props.d.c.s='d2'"]),
                    ("set", ["props.d.e={'s':'d3'}"]),
                    ("set", ["props.d2={'a':'123','b':'1234'}"]),
                ]
            }
        )

        self.assertEqual(instance.props.i, 666)
        self.assertEqual(instance.props.s, "sss")
        self.assertEqual(instance.props.l[2].s, 'l2')
        self.assertEqual(instance.props.l2, [123,123])
        self.assertEqual(instance.props.d['c'].s, 'd2')
        self.assertEqual(instance.props.d['e'], {'s':'d3'})
        self.assertEqual(instance.props.d2, {'a':'123','b':'1234'})

        AAZGenericInstanceUpdateOperation._update_instance_by_generic(
            instance,
            {
                "force_string": True,
                "actions": [
                    ("set", ["props.s=666"]),
                    ("set", ["props.l[2].s=2"]),
                    ("set", ["props.d.c.s=3"]),
                ]
            }
        )
        self.assertEqual(instance.props.s, "666")
        self.assertEqual(instance.props.l[2].s, '2')
        self.assertEqual(instance.props.d['c'].s, '3')

        AAZGenericInstanceUpdateOperation._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("add", ["props.l", "{'s':'add_l'}"]),
                ]
            }
        )
        self.assertEqual(instance.props.l[3], {'s':'add_l'})

        AAZGenericInstanceUpdateOperation._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("remove", ["props.l", "3"]),
                    ("remove", ["props.l2"]),
                    ("remove", ["props.d2"]),
                    ("remove", ["props.d.e"]),
                ]
            }
        )

        self.assertEqual(len(instance.props.l), 3)
        self.assertEqual(instance.props.l2, [])
        self.assertEqual(instance.props.d2, {})
        self.assertEqual(len(instance.props.d), 3)
