# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestAAZField(unittest.TestCase):

    def test_aaz_model_and_simple_types(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZIntType, AAZStrType, AAZBoolType, AAZFloatType
        from azure.cli.core.aaz._field_value import AAZObject
        model_schema = AAZObjectType()
        v = AAZObject(model_schema, data={})

        model_schema.properties = AAZObjectType(options=["prop", "pr"])

        # test int type
        model_schema.properties.count = AAZIntType()
        v.properties.count = 10
        assert isinstance(v.properties, AAZObject)
        assert v.properties._is_patch
        assert not v.properties.count._is_patch
        assert v.properties.count._data == 10
        assert v.properties.count == 10 and v.properties.count <= 10 and v.properties.count >= 10
        assert not (v.properties.count != 10) and not (v.properties.count < 10) and not (v.properties.count > 10)
        assert v.properties.count != 11 and v.properties.count < 11 and v.properties.count <= 11
        assert not (v.properties.count == 11) and not (v.properties.count > 11) and not (v.properties.count >= 11)
        assert v.properties.count != 9 and v.properties.count > 9 and v.properties.count >= 9
        assert not (v.properties.count == 9) and not (v.properties.count < 9) and not (v.properties.count <= 9)
        assert v.properties.count
        assert (not v.properties.count) is False
        v.properties.count = 0
        assert (not v.properties.count) is True

        with self.assertRaises(AssertionError):
            v.properties.count = "a"

        # test string type
        model_schema.properties.name = AAZStrType()
        v.properties.name = "a"
        assert not v.properties.name._is_patch
        assert v.properties.name._data == "a"
        assert v.properties.name == "a"
        assert not v.properties.name != "a"
        assert v.properties.name != "b"
        assert not v.properties.name == "b"
        assert v.properties.name
        assert (not v.properties.name) is False
        v.properties.name = ""
        assert (not v.properties.name) is True

        with self.assertRaises(AssertionError):
            v.properties.name = 1

        # test bool type
        model_schema.properties.enable = AAZBoolType()
        v.properties.enable = True
        assert not v.properties.enable._is_patch
        assert v.properties.enable == True
        assert not (v.properties.enable != True)
        assert v.properties.enable
        assert v.properties.enable is not True  # cannot us is

        v.properties.enable = False
        assert v.properties.enable == False
        assert not (v.properties.enable != False)
        assert not v.properties.enable
        assert v.properties.enable is not False

        # test float type
        model_schema.properties.height = AAZFloatType()
        v.properties.height = 10.0
        assert str(v.properties.height) == "10.0"
        assert not v.properties.height._is_patch
        assert v.properties.height._data == 10
        assert v.properties.height == 10 and v.properties.height <= 10 and v.properties.height >= 10
        assert not (v.properties.height != 10) and not (v.properties.height < 10) and not (v.properties.height > 10)
        assert v.properties.height != 11 and v.properties.height < 11 and v.properties.height <= 11
        assert not (v.properties.height == 11) and not (v.properties.height > 11) and not (v.properties.height >= 11)
        assert v.properties.height != 9 and v.properties.height > 9 and v.properties.height >= 9
        assert not (v.properties.height == 9) and not (v.properties.height < 9) and not (v.properties.height <= 9)

        v.properties.height = 10  # test assign int
        assert str(v.properties.height) == "10.0"

        # test assign properties by dict
        v.properties = {
            "count": 100,
            "name": "abc",
            "enable": True,
            "height": 111
        }

        assert not v.properties._is_patch
        assert v.properties.name._data == "abc"
        assert v.properties.count._data == 100
        assert v.properties.enable._data == True
        assert v.properties.height._data == 111

    def test_aaz_dict_type(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZDictType, AAZStrType
        from azure.cli.core.aaz._field_value import AAZObject
        model_schema = AAZObjectType()
        model_schema.tags = AAZDictType()
        model_schema.tags.Element = AAZStrType()
        model_schema.additional = AAZDictType()
        model_schema.additional.Element = AAZObjectType()
        model_schema.additional.Element.name = AAZStrType()

        v = AAZObject(schema=model_schema, data={})
        assert v.tags["p"]._is_patch
        del v.tags["p"]
        with self.assertRaises(KeyError):
            del v.tags["a"]

        v.tags["flag_1"] = "f1"

        assert v.tags["flag_1"]._data == "f1"
        assert v.tags["flag_1"] == "f1"
        assert "flag_1" in v.tags
        assert "flag_2" not in v.tags
        assert len(v.tags) == 1

        for key in v.tags:
            assert key == "flag_1"

        for key in v.tags.keys():
            assert key == "flag_1"

        for value in v.tags.values():
            assert value._data == "f1"
            assert value == "f1"

        for key, value in v.tags.items():
            assert key == "flag_1"
            assert value._data == "f1"
            assert value == "f1"

        v.tags.clear()
        assert len(v.tags) == 0
        for key in v.tags:
            assert False
        for key in v.tags.keys():
            assert False
        for value in v.tags.values():
            assert False
        for key, value in v.tags.items():
            assert False

        del v.tags
        for key in v.tags:
            assert False
        del v.tags
        for key in v.tags.keys():
            assert False
        del v.tags
        for value in v.tags.values():
            assert False
        del v.tags
        for key, value in v.tags.items():
            assert False

    def test_aaz_free_form_dict_type(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZFreeFormDictType, AAZDictType, AAZListType
        from azure.cli.core.aaz._field_value import AAZObject, AAZBaseValue, AAZUndefined, AAZValuePatch
        from azure.cli.core.aaz.exceptions import AAZInvalidValueError

        model_schema = AAZObjectType()
        model_schema.additional = AAZFreeFormDictType()
        model_schema.configs = AAZListType()
        model_schema.configs.Element = AAZFreeFormDictType()
        model_schema.nullable_additional = AAZFreeFormDictType(nullable=True)

        v = AAZObject(schema=model_schema, data={})

        assert 'A' not in v.additional
        with self.assertRaises(KeyError):
            v.additional['A']

        v.additional['number'] = 1
        self.assertEqual(v.additional['number'], 1)

        for key in v.additional:
            self.assertEqual(key, 'number')

        for key in v.additional.keys():
            self.assertEqual(key, "number")

        for key, value in v.additional.items():
            self.assertEqual(key, 'number')
            self.assertEqual(value, 1)
            self.assertTrue(isinstance(value, int))

        v.additional.clear()
        self.assertEqual(len(v.additional), 0)

        for key in v.additional:
            self.assertTrue(False)

        for key in v.additional.keys():
            self.assertTrue(False)

        for key, value in v.additional.items():
            self.assertTrue(False)

        v.additional['str'] = 'str'
        self.assertEqual(v.additional['str'], 'str')

        del v.additional

        for key in v.additional:
            self.assertTrue(False)

        for key in v.additional.keys():
            self.assertTrue(False)

        for key, value in v.additional.items():
            self.assertTrue(False)

        v.additional['bool'] = True
        self.assertEqual(v.additional['bool'], True)

        del v.additional['bool']
        with self.assertRaises(KeyError):
            v.additional['bool']

        v.additional['none'] = None
        self.assertEqual(v.additional['none'], None)

        v.additional['obj'] = {"a": 1, "b": "str", "c": True, "d": None}
        self.assertEqual(v.additional['obj'], {"a": 1, "b": "str", "c": True, "d": None})

        v.additional['list'] = ['a', 1, True, None, ["s", "v"], {"a": 1, "b": 2}]
        self.assertEqual(v.additional['list'], ['a', 1, True, None, ["s", "v"], {"a": 1, "b": 2}])

        self.assertTrue(v.additional._is_patch)

        self.assertEqual(v.to_serialized_data(), {
            "additional": {
                'none': None,
                'obj': {'a': 1, 'b': 'str', 'c': True, 'd': None},
                'list': ['a', 1, True, None, ['s', 'v'], {'a': 1, 'b': 2}]
            }
        })

        v.configs[0] = {'a': 1, 'b': 'str', 'c': True, 'd': None}
        self.assertEqual(v.configs[0], {'a': 1, 'b': 'str', 'c': True, 'd': None})
        self.assertEqual(v.configs[0]._data, {'a': 1, 'b': 'str', 'c': True, 'd': None})

        v.configs[1] = {"obj": {"a": 1, "c": 2}}
        del v.configs[1]['obj']['a']
        self.assertEqual(v.configs[1], {"obj": {"c": 2}})

        v.configs[0] = None
        self.assertEqual(v.configs.to_serialized_data(), [{"obj": {"c": 2}}])

        with self.assertRaises(AAZInvalidValueError):
            v.nullable_additional['a'] = AAZValuePatch(AAZUndefined)

        self.assertTrue(v.additional._is_patch)
        with self.assertRaises(AAZInvalidValueError):
            v.nullable_additional['p'] = v.additional

        self.assertTrue(v.configs[1]._is_patch is False)

        v.nullable_additional['z'] = v.configs[1]

        v.configs[1]['more'] = True
        self.assertEqual(v.nullable_additional.to_serialized_data(), {
            "z": {"obj": {"c": 2}},
        })

        self.assertEqual(v.to_serialized_data(), {
            "additional": {
                'none': None,
                'obj': {'a': 1, 'b': 'str', 'c': True, 'd': None},
                'list': ['a', 1, True, None, ['s', 'v'], {'a': 1, 'b': 2}]
            },
            "configs": [{"obj": {"c": 2}, "more": True}],
            "nullable_additional": {"z": {"obj": {"c": 2}}}
        })

        v.nullable_additional = None
        self.assertEqual(v.to_serialized_data(), {
            "additional": {
                'none': None,
                'obj': {'a': 1, 'b': 'str', 'c': True, 'd': None},
                'list': ['a', 1, True, None, ['s', 'v'], {'a': 1, 'b': 2}]
            },
            "configs": [{"obj": {"c": 2}, "more": True}],
            "nullable_additional": None
        })

    def test_aaz_list_type(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZStrType
        from azure.cli.core.aaz._field_value import AAZObject
        model_schema = AAZObjectType()
        model_schema.sub_nets = AAZListType()
        model_schema.sub_nets.Element = AAZObjectType()
        model_schema.sub_nets.Element.id = AAZStrType()

        v = AAZObject(schema=model_schema, data={})
        v.sub_nets[0].id = "/0/"
        assert len(v.sub_nets) == 1
        assert v.sub_nets[0]._is_patch
        assert v.sub_nets[0].id._data == "/0/"
        assert v.sub_nets[0].id == "/0/"
        v.sub_nets[1] = {
            "id": "/1/"
        }
        assert len(v.sub_nets) == 2
        assert not v.sub_nets[1]._is_patch
        assert v.sub_nets[1].id._data == "/1/"
        assert v.sub_nets[1].id == "/1/"

        assert not v.sub_nets[-1]._is_patch
        assert v.sub_nets[-1].id._data == "/1/"
        assert v.sub_nets[-1].id == "/1/"

        assert v.sub_nets._is_patch

        v.sub_nets = [
            {
                "id": "/2/",
            },
        ]

        assert len(v.sub_nets) == 1
        assert not v.sub_nets._is_patch
        assert not v.sub_nets[0]._is_patch
        assert v.sub_nets[0].id._data == "/2/"
        assert v.sub_nets[0].id == "/2/"

        for sub_net in v.sub_nets:
            assert sub_net.id == "/2/"

        v.sub_nets.append({
            "id": "/3/"
        })
        assert len(v.sub_nets) == 2
        v.sub_nets.clear()
        assert len(v.sub_nets) == 0
        for sub_net in v.sub_nets:
            assert False

        v.sub_nets.extend([{"id": "/1/"}, {"id": "/2/"}])
        assert len(v.sub_nets) == 2

        del v.sub_nets
        for sub_net in v.sub_nets:
            assert False

    def test_aaz_types_with_alias(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZStrType, AAZDictType, AAZListType
        from azure.cli.core.aaz._field_value import AAZObject
        model_schema = AAZObjectType()
        model_schema.sub_properties = AAZObjectType(options=["sub-properties"], serialized_name="subProperties")
        model_schema.sub_properties.vnet_id = AAZStrType(options=["vnet-id"], serialized_name="vnetId")
        model_schema.sub_properties.sub_tags = AAZDictType(options=["sub-tags"], serialized_name="subTags")
        model_schema.sub_properties.sub_tags.Element = AAZStrType()
        model_schema.sub_properties.sub_nets = AAZListType(options=["sub-nets"], serialized_name="subNets")
        model_schema.sub_properties.sub_nets.Element = AAZObjectType()
        model_schema.sub_properties.sub_nets.Element.address_id = AAZStrType(options=["address-id"],
                                                                             serialized_name="addressId")

        v = AAZObject(model_schema, data={})

        v.sub_properties = {
            "vnetId": "vnetId",
            "subTags": {
                "aa": "aa",
                "bb": "bb"
            },
            "subNets": [
                {
                    "addressId": "1.1.1.1"
                },
                {
                    "addressId": "2.2.2.2"
                }
            ]
        }
        assert v.sub_properties.vnet_id._data == "vnetId"
        assert v.sub_properties.sub_tags._data == {"aa": "aa", "bb": "bb"}
        assert v.sub_properties.sub_nets[0].address_id._data == "1.1.1.1"
        assert v.sub_properties.sub_nets[1].address_id._data == "2.2.2.2"
        assert v.sub_properties.vnetId._data == "vnetId"
        assert v.sub_properties.subTags._data == {"aa": "aa", "bb": "bb"}
        assert v.sub_properties.subNets[0].addressId._data == "1.1.1.1"
        assert v.sub_properties.subNets[1].addressId._data == "2.2.2.2"

        v.sub_properties = {
            "vnet-id": "vnet-id",
            "sub-tags": {
                "cc": "cc",
            },
            "sub-nets": [
                {
                    "address-id": "3.3.3.3"
                }
            ]
        }

        assert v.sub_properties.vnet_id._data == "vnet-id"
        assert v.sub_properties.sub_tags._data == {"cc": "cc"}
        assert v.sub_properties.sub_nets[0].address_id._data == "3.3.3.3"
        assert v.sub_properties.vnetId._data == "vnet-id"
        assert v.sub_properties.subTags._data == {"cc": "cc"}
        assert v.sub_properties.subNets[0].addressId._data == "3.3.3.3"

        model_schema.sub_properties.err_sub_nets = AAZListType()
        with self.assertRaises(AssertionError):
            model_schema.sub_properties.err_sub_nets.Element = AAZStrType(options=["aaa"])

        model_schema.sub_properties.err_sub_tags = AAZDictType()
        with self.assertRaises(AssertionError):
            model_schema.sub_properties.err_sub_tags.Element = AAZStrType(options=["bbb"])

    def test_aaz_recursive_type(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZStrType, AAZDictType, AAZListType
        from azure.cli.core.aaz._field_value import AAZObject
        model_schema = AAZObjectType()

        v = AAZObject(model_schema, data={})

        model_schema.errors = AAZListType()

        error = model_schema.errors.Element = AAZObjectType()

        error.code = AAZStrType()
        error.message = AAZStrType()
        error.target = AAZStrType()
        error.additional_info = AAZListType(serialized_name="additionalInfo")
        error.details = AAZListType()
        error.details.Element = error

        add_info_element = model_schema.errors.Element.additional_info.Element = AAZObjectType()
        add_info_element.type = AAZStrType()
        add_info_element.info = AAZDictType()
        add_info_element.info.Element = AAZStrType()

        v.errors = [
            {
                "code": "",
                "message": "",
                "target": "",
                "additionalInfo": [],
                "details": [
                    {
                        "code": "",
                        "target": "",
                        "message": "",
                        "additionalInfo": [
                            {
                                "type": "PolicyViolation",
                                "info": {
                                    "policySetDefinitionDisplayName": "Secure the environment",
                                    "policySetDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policySetDefinitions/TestPolicySet",
                                    "policyDefinitionDisplayName": "Allowed locations",
                                    "policyDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyDefinitions/TestPolicy1",
                                    "policyAssignmentDisplayName": "Allow Central US and WEU only",
                                    "policyAsssignmentId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyAssignments/TestAssignment1"
                                }
                            },
                            {
                                "type": "SomeOtherViolation",
                                "info": {
                                    "innerException": "innerException Details"
                                }
                            }
                        ],
                        "details": [
                            {
                                "code": "",
                                "target": "",
                                "message": "",
                                "additionalInfo": [
                                    {
                                        "type": "PolicyViolation",
                                        "info": {
                                            "policySetDefinitionDisplayName": "Secure the environment",
                                            "policySetDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policySetDefinitions/TestPolicySet",
                                            "policyDefinitionDisplayName": "Allowed locations",
                                            "policyDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyDefinitions/TestPolicy1",
                                            "policyAssignmentDisplayName": "Allow Central US and WEU only",
                                            "policyAsssignmentId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyAssignments/TestAssignment1"
                                        }
                                    },
                                    {
                                        "type": "SomeOtherViolation",
                                        "info": {
                                            "innerException": "innerException Details"
                                        }
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }
        ]

        data = v.to_serialized_data()
        self.assertTrue(data == {
            "errors": [
                {
                    "code": "",
                    "message": "",
                    "target": "",
                    "additionalInfo": [],
                    "details": [
                        {
                            "code": "",
                            "target": "",
                            "message": "",
                            "additionalInfo": [
                                {
                                    "type": "PolicyViolation",
                                    "info": {
                                        "policySetDefinitionDisplayName": "Secure the environment",
                                        "policySetDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policySetDefinitions/TestPolicySet",
                                        "policyDefinitionDisplayName": "Allowed locations",
                                        "policyDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyDefinitions/TestPolicy1",
                                        "policyAssignmentDisplayName": "Allow Central US and WEU only",
                                        "policyAsssignmentId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyAssignments/TestAssignment1"
                                    }
                                },
                                {
                                    "type": "SomeOtherViolation",
                                    "info": {
                                        "innerException": "innerException Details"
                                    }
                                }
                            ],
                            "details": [
                                {
                                    "code": "",
                                    "target": "",
                                    "message": "",
                                    "additionalInfo": [
                                        {
                                            "type": "PolicyViolation",
                                            "info": {
                                                "policySetDefinitionDisplayName": "Secure the environment",
                                                "policySetDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policySetDefinitions/TestPolicySet",
                                                "policyDefinitionDisplayName": "Allowed locations",
                                                "policyDefinitionId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyDefinitions/TestPolicy1",
                                                "policyAssignmentDisplayName": "Allow Central US and WEU only",
                                                "policyAsssignmentId": "/subscriptions/00000-00000-0000-000/providers/Microsoft.Authorization/policyAssignments/TestAssignment1"
                                            }
                                        },
                                        {
                                            "type": "SomeOtherViolation",
                                            "info": {
                                                "innerException": "innerException Details"
                                            }
                                        }
                                    ],
                                }
                            ]
                        }
                    ]
                }
            ]
        })

    def test_aaz_object_with_polymorphism_support(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZStrType, AAZIntType
        from azure.cli.core.aaz._field_value import AAZObject
        from azure.cli.core.aaz.exceptions import AAZUnknownFieldError
        from azure.cli.core.aaz._command import AAZCommand

        model_schema = AAZObjectType()
        v = AAZObject(model_schema, data={})

        model_schema.display_name = AAZStrType()
        model_schema.actions = AAZListType()

        element = model_schema.actions.Element = AAZObjectType()

        element.action_type = AAZStrType()
        element.order = AAZIntType()
        disc_modify_properties = element.discriminate_by('action_type', 'ModifyProperties')
        action_configuration = disc_modify_properties.action_configuration = AAZObjectType(
            flags={"client_flatten": True})
        action_configuration.classification = AAZStrType()
        action_configuration.classification_comment = AAZStrType()
        action_configuration.severity = AAZStrType()

        disc_run_playbook = element.discriminate_by('action_type', 'RunPlaybook')
        disc_run_playbook.logic_app_resource_id = AAZStrType()
        disc_run_playbook.tenant_id = AAZStrType()

        v.actions = [
            {
                "action_type": "ModifyProperties",
                "order": 0,
                "action_configuration": {
                    "classification": "BenignPositive",
                    "classification_comment": "comments 1",
                    "severity": "High",
                }
            },
            {
                "action_type": "RunPlaybook",
                "order": 1,
                "logic_app_resource_id": "123333",
                "tenant_id": "111111",
            }
        ]

        self.assertTrue(v.to_serialized_data() == {
            "actions": [
                {
                    "action_type": "ModifyProperties",
                    "order": 0,
                    "action_configuration": {
                        "classification": "BenignPositive",
                        "classification_comment": "comments 1",
                        "severity": "High",
                    }
                },
                {
                    "action_type": "RunPlaybook",
                    "order": 1,
                    "logic_app_resource_id": "123333",
                    "tenant_id": "111111",
                }
            ]
        })

        v.actions[2] = {
            "action_type": "ModifyProperties",
        }

        v.actions[2].order = 2
        with self.assertRaises(AAZUnknownFieldError):
            v.actions[2].logic_app_resource_id = "6666"
        self.assertTrue(v.actions[2].action_configuration.classification._is_patch)
        v.actions[2].action_configuration.classification = "FalsePositive"
        self.assertEqual(v.actions[2].action_configuration.classification, "FalsePositive")
        self.assertEqual(v.actions[2].actionConfiguration.classification, "FalsePositive")

        self.assertTrue(v.to_serialized_data() == {
            "actions": [
                {
                    "action_type": "ModifyProperties",
                    "order": 0,
                    "action_configuration": {
                        "classification": "BenignPositive",
                        "classification_comment": "comments 1",
                        "severity": "High",
                    }
                },
                {
                    "action_type": "RunPlaybook",
                    "order": 1,
                    "logic_app_resource_id": "123333",
                    "tenant_id": "111111",
                },
                {
                    "action_type": "ModifyProperties",
                    "order": 2,
                    "action_configuration": {
                        "classification": "FalsePositive"
                    }
                }
            ]
        })

        # change the action_type will disable the access to previous discriminator, event though the data still in _data
        v.actions[2]['actionType'] = "RunPlaybook"
        with self.assertRaises(AAZUnknownFieldError):
            v.actions[2].action_configuration
        self.assertTrue(v.actions[2].logic_app_resource_id._is_patch)
        v.actions[2].logic_app_resource_id = "678"

        # will not serialize action_configuration
        self.assertTrue(v.to_serialized_data() == {
            "actions": [
                {
                    "action_type": "ModifyProperties",
                    "order": 0,
                    "action_configuration": {
                        "classification": "BenignPositive",
                        "classification_comment": "comments 1",
                        "severity": "High",
                    }
                },
                {
                    "action_type": "RunPlaybook",
                    "order": 1,
                    "logic_app_resource_id": "123333",
                    "tenant_id": "111111",
                },
                {
                    "action_type": "RunPlaybook",
                    "order": 2,
                    "logic_app_resource_id": "678",
                }
            ]
        })

        # change back the action_type, action_configuration show again
        v.actions[2].action_type = "ModifyProperties"
        self.assertTrue(v.to_serialized_data() == {
            "actions": [
                {
                    "action_type": "ModifyProperties",
                    "order": 0,
                    "action_configuration": {
                        "classification": "BenignPositive",
                        "classification_comment": "comments 1",
                        "severity": "High",
                    }
                },
                {
                    "action_type": "RunPlaybook",
                    "order": 1,
                    "logic_app_resource_id": "123333",
                    "tenant_id": "111111",
                },
                {
                    "action_type": "ModifyProperties",
                    "order": 2,
                    "action_configuration": {
                        "classification": "FalsePositive"
                    }
                }
            ]
        })

        # test client flatten
        self.assertTrue(AAZCommand.deserialize_output(v, client_flatten=True) == {
            "actions": [
                {
                    "action_type": "ModifyProperties",
                    "order": 0,
                    "classification": "BenignPositive",
                    "classification_comment": "comments 1",
                    "severity": "High",
                },
                {
                    "action_type": "RunPlaybook",
                    "order": 1,
                    "logic_app_resource_id": "123333",
                    "tenant_id": "111111",
                },
                {
                    "action_type": "ModifyProperties",
                    "order": 2,
                    "classification": "FalsePositive"
                }
            ]
        })

    def test_aaz_types_process_patch_data(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZDictType, AAZListType, \
            AAZIntType, AAZStrType, AAZBoolType, AAZFloatType
        from azure.cli.core.aaz._field_value import AAZObject, AAZValuePatch

        model_schema = AAZObjectType()
        model_schema.tags = AAZDictType()
        model_schema.tags.Element = AAZStrType()

        model_schema.properties = AAZObjectType()
        model_schema.properties.enabled = AAZBoolType()
        model_schema.properties.closed = AAZBoolType()

        model_schema.subnets = AAZListType()
        model_schema.subnets.Element = AAZObjectType()
        model_schema.subnets.Element.score = AAZFloatType()
        model_schema.subnets.Element.count = AAZIntType()

        v = AAZObject(schema=model_schema, data=AAZValuePatch.build(model_schema))
        v_copy = AAZObject(schema=model_schema, data=AAZValuePatch.build(model_schema))

        v.tags['a'] = "11"
        _ = v.tags['b']
        self.assertTrue(v.tags._is_patch and not v.tags['a']._is_patch)
        self.assertTrue(v.tags['b']._is_patch)

        data = model_schema.tags.process_data(v.tags)
        self.assertTrue(isinstance(data, AAZValuePatch))
        self.assertTrue(data.data['a'] == '11')
        self.assertTrue(isinstance(data.data['b'], AAZValuePatch))
        v_copy.tags = v.tags
        self.assertTrue(v_copy.tags._is_patch and not v_copy.tags['a']._is_patch)
        self.assertTrue(v_copy.tags['b']._is_patch)

        v.properties.enabled = False
        _ = v.properties.closed
        self.assertTrue(v.properties._is_patch and not v.properties.enabled._is_patch)
        self.assertTrue(v.properties.closed._is_patch)

        data = model_schema.properties.process_data(v.properties)
        self.assertTrue(isinstance(data, AAZValuePatch))
        self.assertTrue(data.data['enabled'] is False)
        self.assertTrue(isinstance(data.data['closed'], AAZValuePatch))
        v_copy.properties = v.properties
        self.assertTrue(v_copy.properties._is_patch and not v_copy.properties.enabled._is_patch)
        self.assertTrue(v_copy.properties.closed._is_patch)

        v.subnets[0].score = 1.1
        v.subnets[0].count = 1
        _ = v.subnets[1].score
        _ = v.subnets[1].count
        self.assertTrue(v.subnets[0]._is_patch and not v.subnets[0].score._is_patch and not v.subnets[0].count._is_patch)
        self.assertTrue(v.subnets[1]._is_patch and v.subnets[1].score._is_patch and v.subnets[1].count._is_patch)

        data = model_schema.subnets.process_data(v.subnets)
        self.assertTrue(isinstance(data, AAZValuePatch))
        self.assertTrue(isinstance(data.data[0], AAZValuePatch))
        self.assertTrue(data.data[0].data['score'] == 1.1)
        self.assertTrue(data.data[0].data['count'] == 1)
        self.assertTrue(isinstance(data.data[1], AAZValuePatch))
        self.assertTrue(isinstance(data.data[1].data['score'], AAZValuePatch))
        self.assertTrue(isinstance(data.data[1].data['count'], AAZValuePatch))

        v_copy.subnets = v.subnets

        self.assertTrue(v_copy.subnets[0]._is_patch and not v_copy.subnets[0].score._is_patch and not v_copy.subnets[0].count._is_patch)
        self.assertTrue(v_copy.subnets[1]._is_patch and v_copy.subnets[1].score._is_patch and v_copy.subnets[1].count._is_patch)

    def test_aaz_equal_comparison(self):
        from azure.cli.core.aaz._field_type import AAZObjectType, AAZListType, AAZFreeFormDictType, AAZDictType, AAZIntType, AAZStrType, AAZBoolType, AAZFloatType
        from azure.cli.core.aaz._field_value import AAZObject
        model_schema = AAZObjectType()

        model_schema.name = AAZStrType()

        model_schema.list = AAZListType()
        element = model_schema.list.Element = AAZObjectType()
        element.name = AAZStrType()

        model_schema.e_list = AAZListType()
        element = model_schema.e_list.Element = AAZStrType()

        model_schema.props = AAZObjectType()
        model_schema.props.name = AAZStrType()

        model_schema.e_props = AAZObjectType()
        model_schema.e_props.name = AAZStrType()

        model_schema.dict = AAZDictType()
        element = model_schema.dict.Element = AAZObjectType()
        element.name = AAZStrType()

        model_schema.e_dict = AAZDictType()
        element = model_schema.e_dict.Element = AAZStrType()

        model_schema.ff_dict = AAZFreeFormDictType()
        model_schema.e_ff_dict = AAZFreeFormDictType()

        data = {
            "name": "name",
            "list": [
                {
                    "name": "a"
                },
                {
                    "name": "b"
                }
            ],
            "props": {
                "name": "props"
            },
            "dict": {
                "key1": {
                    "name": "key1"
                },
                "key2": {
                    "name": "key2"
                }
            },
            "ff_dict": {
                "key1": {
                    "name": "key1"
                },
                "key2": {
                    "name": "key2"
                }
            },
        }
        v1 = AAZObject(model_schema, data=model_schema.process_data(data))
        v2 = AAZObject(model_schema, data=model_schema.process_data(data))
        self.assertEqual(v1, v2)
        self.assertEqual(v1, data)

        self.assertEqual(v1.name, v2.name)
        self.assertEqual(v1.list, v2.list)
        self.assertEqual(v1.props, v2.props)
        self.assertEqual(v1.dict, v2.dict)
        self.assertTrue(v1.ff_dict, v2.ff_dict)
        self.assertEqual(v1.ff_dict, v1.dict)

        self.assertEqual(v1.e_list, v2.e_list)
        self.assertEqual(v1.e_props, v2.e_props)
        self.assertEqual(v1.e_dict, v2.e_dict)
        self.assertEqual(v1.e_ff_dict, v2.e_ff_dict)
        self.assertEqual(v1.e_ff_dict, v1.e_dict)

        # not exist compare
        self.assertEqual(v1.list[10], v2.list[10])
        self.assertEqual(v1.dict["NotExist"], v2.dict["NotExist"])
