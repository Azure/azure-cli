import unittest


class TestAAZArgument(unittest.TestCase):

    def test_aaz_arguments(self):
        from azure.cli.core.aaz._argument import AAZArguments
        from azure.cli.core.aaz._base import AAZValuePatch
        from azure.cli.core.aaz._field_type import AAZModelType, AAZBoolType, AAZIntType, AAZStrType, AAZFloatType

        class Arguments(AAZArguments):
            name = AAZStrType()
            properties = AAZModelType()
            properties.enable = AAZBoolType()
            properties.count = AAZIntType()
            properties.vnet = AAZModelType()
            properties.vnet.address = AAZStrType()
            properties.vnet.threshold = AAZFloatType()

        arguments = Arguments()
        arguments.name = "test"
        arguments.properties = {
            "enable": True,
            "count": 10,
            "vnet": {
                "address": "10.10.10.10",
                "threshold": 1,
            }
        }
        assert arguments.name == "test"
        assert arguments.properties.enable == True
        assert arguments.properties.count == 10
        assert arguments.properties.vnet.address == "10.10.10.10"
        assert arguments.properties.vnet.threshold == 1
