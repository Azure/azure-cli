import unittest


class TestAAZArgument(unittest.TestCase):

    def test_aaz_arguments(self):
        from azure.cli.core.aaz._arg import AAZArguments
        from azure.cli.core.aaz._field_type import AAZModelType, AAZBoolType, AAZIntType, AAZStrType, AAZFloatType

        class Arguments(AAZArguments):
            name = AAZStrType(options=["--name", "-n"])

            properties = AAZModelType(options=["--properties"])
            properties.enable = AAZBoolType(options=["enable"])
            properties.count = AAZIntType(options=["count"])
            properties.vnet = AAZModelType(options=["vnet"])
            properties.vnet.address = AAZStrType(options=["address"])
            properties.vnet.threshold = AAZFloatType(options=["threshold"])

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

        assert arguments.name._data == "test"
        assert arguments.properties.enable._data == True
        assert arguments.properties.count._data == 10
        assert arguments.properties.vnet.address._data == "10.10.10.10"
        assert arguments.properties.vnet.threshold._data == 1
