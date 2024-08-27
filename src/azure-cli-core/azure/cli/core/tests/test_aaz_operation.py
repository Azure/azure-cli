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

        ctx = None

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
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

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
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

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("add", ["props.l", "{'s':'add_l'}"]),
                ]
            }
        )
        self.assertEqual(instance.props.l[3], {'s':'add_l'})

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
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
        self.assertEqual(len(instance.props.d.to_serialized_data()), 3)

    def test_aaz_generic_update_operation_with_flatten(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZDictType, AAZStrType, AAZIntType
        from azure.cli.core.aaz._operation import AAZGenericInstanceUpdateOperation
        from azure.cli.core.aaz._base import has_value

        schema = AAZObjectType()
        schema.props = AAZObjectType(flags={"client_flatten": True})
        schema.props.i = AAZIntType()
        schema.props.s = AAZStrType()
        schema.props.l = AAZListType()
        schema.props.l.Element = AAZObjectType()
        schema.props.l.Element.s = AAZStrType()
        schema.props.l.Element.o = AAZObjectType(flags={"client_flatten": True})
        schema.props.l.Element.o.p = AAZStrType()
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
                        "s": "lb",
                        "o": {
                            "p": "p",
                        }
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

        ctx = None

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("set", ["i=666"]),
                    ("set", ["s=sss"]),
                    ("set", ["l[2].s='l2'"]),
                    ("set", ["l[0].p='l5'"]),
                    ("set", ["l2=[123,123]"]),
                    ("set", ["d.c.s='d2'"]),
                    ("set", ["d.e={'s':'d3'}"]),
                    ("set", ["d2={'a':'123','b':'1234'}"]),
                ]
            }
        )

        self.assertEqual(instance.props.i, 666)
        self.assertEqual(instance.props.s, "sss")
        self.assertEqual(instance.props.l[0].o.p, 'l5')
        self.assertEqual(instance.props.l[2].s, 'l2')
        self.assertEqual(instance.props.l2, [123, 123])
        self.assertEqual(instance.props.d['c'].s, 'd2')
        self.assertEqual(instance.props.d['e'], {'s': 'd3'})
        self.assertEqual(instance.props.d2, {'a': '123', 'b': '1234'})

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
            instance,
            {
                "force_string": True,
                "actions": [
                    ("set", ["s=666"]),
                    ("set", ["l[2].s=2"]),
                    ("set", ["l[p='p'].s=ll"]),
                    ("set", ["l[0].p=5"]),
                    ("set", ["d.c.s=3"]),
                ]
            }
        )
        self.assertEqual(instance.props.s, "666")
        self.assertEqual(instance.props.l[0].o.p, '5')
        self.assertEqual(instance.props.l[1].s, 'll')
        self.assertEqual(instance.props.l[2].s, '2')
        self.assertEqual(instance.props.d['c'].s, '3')

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("add", ["l", "{'s':'add_l','xxx':666}"]),
                    ("add", ["l", "s=666"]),
                ]
            }
        )
        # xxx will be ignored if it's not exist
        self.assertEqual(instance.props.l[3], {'s': 'add_l'})
        self.assertEqual(instance.props.l[4], {'s': '666'})

        AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
            instance,
            {
                "actions": [
                    ("remove", ["l", "4"]),
                    ("remove", ["l", "3"]),
                    ("remove", ["l[1].p"]),
                    ("remove", ["l2"]),
                    ("remove", ["d2"]),
                    ("remove", ["d.e"]),
                    ("remove", ["s"]),
                ]
            }
        )

        self.assertEqual(len(instance.props.l.to_serialized_data()), 3)
        self.assertEqual(instance.props.l2, [])
        self.assertEqual(instance.props.l[1].o.to_serialized_data(), {})
        self.assertEqual(instance.props.d2, {})
        self.assertEqual(len(instance.props.d.to_serialized_data()), 3)
        self.assertFalse(has_value(instance.props.s))

    def test_aaz_generic_update_operation_with_error_response(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZDictType, AAZStrType, AAZIntType
        from azure.cli.core.aaz._operation import AAZGenericInstanceUpdateOperation
        from azure.cli.core.azclierror import InvalidArgumentValueError

        schema = AAZObjectType()
        schema.props = AAZObjectType(flags={"client_flatten": True})
        schema.props.i = AAZIntType()
        schema.props.s = AAZStrType()
        schema.props.l = AAZListType()
        schema.props.l.Element = AAZObjectType()
        schema.props.l.Element.s = AAZStrType()
        schema.props.l.Element.o = AAZObjectType(flags={"client_flatten": True})
        schema.props.l.Element.o.p = AAZStrType()
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
                        "s": "lb",
                        "o": {
                            "p": "p",
                        }
                    },
                    {
                        "s": "lc",
                        "o": {
                            "p": "p",
                        }
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
        ctx = None

        # test set
        with self.assertRaisesRegex(InvalidArgumentValueError, r"Empty key in --set"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["=666"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"Couldn't find '\[1\]' in ''. Available options: \['d', 'd2', 'i', 'l', 'l2', 's'\]"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["[1]=666"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"Couldn't find 'props' in ''. Available options: \['d', 'd2', 'i', 'l', 'l2', 's'\]"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["props.i=666"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"Couldn't find 'o' in 'l\[0\]'. Available options: \['p', 's'\]"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["l[0].o.p='l5'"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"non-unique key 'p' found"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "force_string": True,
                    "actions": [
                        ("set", ["l[p='p'].s=ll"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"item with value 'x' doesn't exist for key 'p' on l"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "force_string": True,
                    "actions": [
                        ("set", ["l[p='x'].s=ll"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"index 10 doesn't exist"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["l[10].s='l5'"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"Couldn't find 't' in 'l\[1\]'. Available options: \['p', 's'\]"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["l[1].t='l5'"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"`--set property1.property2=<value>`"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ['l[a]={"s":"l5"}']),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"Expect <class 'str'>, got 3 \(<class 'int'>\)"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ['l[1]={"s":3}']),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"index 8 doesn't exist on l"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ['l[8]={"s":"l5"}']),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"Couldn't find '\[10\]' in 'd'. Available options: \['a', 'b', 'c'\]"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("set", ["d[10].s='l5'"]),
                    ]
                }
            )

        # test add
        with self.assertRaisesRegex(InvalidArgumentValueError, r"Expect <class 'int'>, got a \(<class 'str'>\)"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("add", ["l2", "'a'"]),
                    ]
                }
            )

        # test remove

        with self.assertRaisesRegex(InvalidArgumentValueError, r"index 9 doesn't exist"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("remove", ["l", "9"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"`--remove property.list <indexToRemove>` OR `--remove propertyToRemove`"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("remove", ["l[0]"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"index 2 doesn't exist on l"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("remove", ["l", "1"]),
                        ("remove", ["l", "2"]),
                    ]
                }
            )

        with self.assertRaisesRegex(InvalidArgumentValueError, r"index 1 doesn't exist on s"):
            AAZGenericInstanceUpdateOperation(ctx)._update_instance_by_generic(
                instance,
                {
                    "actions": [
                        ("remove", ["s", "1"]),
                    ]
                }
            )
