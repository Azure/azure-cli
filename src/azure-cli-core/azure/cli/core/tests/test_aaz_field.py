import unittest


class TestAAZField(unittest.TestCase):

    def test_aaz_model_and_simple_types(self):
        from azure.cli.core.aaz._field_type import AAZModelType, AAZIntType, AAZStrType, AAZBoolType, AAZFloatType
        from azure.cli.core.aaz._field_value import AAZModel
        model_schema = AAZModelType()
        v = AAZModel(model_schema, data={})

        model_schema.properties = AAZModelType(options=["prop", "pr"])

        # test int type
        model_schema.properties.count = AAZIntType()
        v.properties.count = 10
        assert isinstance(v.properties, AAZModel)
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

        v.properties.height = 10    # test assign int
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
        from azure.cli.core.aaz._field_type import AAZModelType, AAZDictType, AAZStrType
        from azure.cli.core.aaz._field_value import AAZModel
        model_schema = AAZModelType()
        model_schema.tags = AAZDictType()
        model_schema.tags.Element = AAZStrType()
        model_schema.additional = AAZDictType()
        model_schema.additional.Element = AAZModelType()
        model_schema.additional.Element.name = AAZStrType()

        v = AAZModel(schema=model_schema, data={})
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

    def test_aaz_list_type(self):
        from azure.cli.core.aaz._field_type import AAZModelType, AAZListType, AAZStrType
        from azure.cli.core.aaz._field_value import AAZModel
        model_schema = AAZModelType()
        model_schema.sub_nets = AAZListType()
        model_schema.sub_nets.Element = AAZModelType()
        model_schema.sub_nets.Element.id = AAZStrType()

        v = AAZModel(schema=model_schema, data={})
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
        from azure.cli.core.aaz._field_type import AAZModelType, AAZIntType, AAZStrType, AAZBoolType, AAZFloatType, AAZDictType, AAZListType
        from azure.cli.core.aaz._field_value import AAZModel
        model_schema = AAZModelType()
        model_schema.sub_properties = AAZModelType(options=["sub-properties"], serialized_name="subProperties")
        model_schema.sub_properties.vnet_id = AAZStrType(options=["vnet-id"], serialized_name="vnetId")
        model_schema.sub_properties.sub_tags = AAZDictType(options=["sub-tags"], serialized_name="subTags")
        model_schema.sub_properties.sub_tags.Element = AAZStrType()
        model_schema.sub_properties.sub_nets = AAZListType(options=["sub-nets"], serialized_name="subNets")
        model_schema.sub_properties.sub_nets.Element = AAZModelType()
        model_schema.sub_properties.sub_nets.Element.address_id = AAZStrType(options=["address-id"], serialized_name="addressId")

        v = AAZModel(model_schema, data={})

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
