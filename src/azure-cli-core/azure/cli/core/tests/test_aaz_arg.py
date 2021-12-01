import unittest
import json


class TestAAZArg(unittest.TestCase):

    def test_aaz_compound_type_action_key_pattern(self):
        from azure.cli.core.aaz._arg_action import AAZCompoundTypeArgAction
        key_pattern = AAZCompoundTypeArgAction.key_pattern

        test_value = "a.b.c="
        match = key_pattern.fullmatch(test_value)
        assert match[1] == 'a.b.c'
        assert match[len(match.regs) - 1] == ''

        test_value = "a_b-C=aaa"
        match = key_pattern.fullmatch(test_value)
        assert match[1] == 'a_b-C'
        assert match[len(match.regs) - 1] == 'aaa'

        test_value = "[10]=aaa"
        match = key_pattern.fullmatch(test_value)
        assert match[1] == '[10]'
        assert match[len(match.regs) - 1] == 'aaa'

        test_value = "a_b.C[10]=aaa"
        match = key_pattern.fullmatch(test_value)
        assert match[1] == 'a_b.C[10]'
        assert match[len(match.regs) - 1] == 'aaa'

        test_value = "a_b.C[10].D-e_f=aaa"
        match = key_pattern.fullmatch(test_value)
        assert match[1] == 'a_b.C[10].D-e_f'
        assert match[len(match.regs) - 1] == 'aaa'

        test_value = "a_b-C={aaa:b}"
        match = key_pattern.fullmatch(test_value)
        assert match[1] == 'a_b-C'
        assert match[len(match.regs) - 1] == '{aaa:b}'

        test_value = "a_b-C=[aaa,b]"
        match = key_pattern.fullmatch(test_value)
        assert match[1] == 'a_b-C'
        assert match[len(match.regs) - 1] == '[aaa,b]'

        test_value = "{a_b:aaa}"
        match = key_pattern.fullmatch(test_value)
        assert match is None

        test_value = "[aaa,bbb]"
        match = key_pattern.fullmatch(test_value)
        assert match is None

        test_value = "a_b.C[abc]=aaa"
        match = key_pattern.fullmatch(test_value)
        assert match is None

        test_value = "a_b.C[10].D-e_f"
        match = key_pattern.fullmatch(test_value)
        assert match is None

    def test_aaz_shorthand_syntax_simple_value(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser
        from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
        parser = AAZShortHandSyntaxParser()

        # test null value
        assert parser("null") is None
        assert parser("None") is None
        assert parser("'null'") == 'null'
        assert parser("'None'") == 'None'

        # test quota
        assert parser('"\'"') == "'"
        assert parser("'\"'") == '"'

        # test escape character
        assert parser("'\\\"'") == "\""
        assert parser("'\\\''") == "\'"
        assert parser("'\\\\'") == "\\"
        assert parser("'\\b'") == "\b"
        assert parser("'\\f'") == "\f"
        assert parser("'\\n'") == "\n"
        assert parser("'\\r'") == "\r"
        assert parser("'\\t'") == "\t"

        assert parser('"\\\""') == "\""
        assert parser('"\\\'"') == "\'"
        assert parser('"\\\\"') == "\\"
        assert parser('"\\b"') == "\b"
        assert parser('"\\f"') == "\f"
        assert parser('"\\n"') == "\n"
        assert parser('"\\r"') == "\r"
        assert parser('"\\t"') == "\t"

        # test normal string
        assert parser("abc") == "abc"
        assert parser("1") == "1"
        assert parser("_") == "_"
        assert parser("''") == ""
        assert parser('""') == ""
        assert parser("'{'") == "{"
        assert parser('"{"') == "{"
        assert parser("'}'") == "}"
        assert parser('"}"') == "}"

        assert parser("'{abc'") == "{abc"
        assert parser('"abc{"') == "abc{"
        assert parser("'abc}'") == "abc}"
        assert parser('"}abc"') == "}abc"
        assert parser('"{a:1, b:2}"') == "{a:1, b:2}"

        assert parser("'['") == "["
        assert parser('"["') == "["
        assert parser("']'") == "]"
        assert parser('"]"') == "]"

        assert parser("'[abc'") == "[abc"
        assert parser('"abc["') == "abc["
        assert parser("'abc]'") == "abc]"
        assert parser('"]abc"') == "]abc"
        assert parser('"[1, 2, 3]"') == "[1, 2, 3]"

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'\\")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'\\x'")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser('"')

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[")

    def test_aaz_shorthand_syntax_dict_value(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser
        from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
        parser = AAZShortHandSyntaxParser()
        assert parser("{}") == {}
        assert parser("{a:1,b:2,c:null,d:''}") == {
            "a": "1",
            "b": "2",
            "c": None,
            "d": ''
        }
        assert parser("{a:1,b:2,c:None,d:'',}") == {
            "a": "1",
            "b": "2",
            "c": None,
            "d": ''
        }

        assert parser("{a:1,b:2,c:Null,d:''}") == {
            "a": "1",
            "b": "2",
            "c": "Null",
            "d": ''
        }
        assert parser("{a:1,b:2,c:none,d:'',}") == {
            "a": "1",
            "b": "2",
            "c": "none",
            "d": ''
        }

        assert parser("{a:{a1:1,a2:2}}") == {
            "a": {
                "a1": "1",
                "a2": "2",
            }
        }
        assert parser("{a:{a1:1,a2:2},}") == {
            "a": {
                "a1": "1",
                "a2": "2",
            }
        }

        assert parser("{a:{a1:{},a2:2}}") == {
            "a": {
                "a1": {},
                "a2": "2",
            }
        }

        dt = {
            "a": [
                {
                    "prop1": "1",
                    "prop2": "2",
                },
                {
                    "a1": ["b", None, "c", 'd:e "]'],
                    "a2": '2 3\t"}',
                    "a4": '',
                    "a3": None,
                }
            ],
            "e": "f",
            "g": None,
        }
        assert parser("{a:[{prop1:1,prop2:2},{a1:[b,null,c,'d:e \"]'],a2:'2 3\t\"}',a4:'',a3:null,}],e:f,g:null}") == dt
        s = json.dumps(dt, separators=(',', ':'))
        assert parser(s) == dt

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:1]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1b:}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,a:2}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:'\\'}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:{}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:{}}{")

    def test_aaz_shorthand_syntax_list_value(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser
        from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError

        parser = AAZShortHandSyntaxParser()
        assert parser("[]") == []

        assert parser("[c]") == ["c"]

        assert parser("[c,]") == ["c"]

        assert parser("[a,b,c,d]") == [
            "a", "b", "c", "d"
        ]
        assert parser("[a,null,'',d]") == [
            "a", None, "", "d"
        ]
        assert parser("[a,None,'',d,]") == [
            "a", None, "", "d"
        ]
        assert parser("[a,[],{},[b,c,d],]") == [
            "a", [], {}, ["b", "c", "d"]
        ]

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[,]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a,b")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a,b,")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a,[b,[c]]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a,]]")

    # def test_aaz_arguments(self):
    #     from azure.cli.core.aaz._arg import AAZArguments
    #     from azure.cli.core.aaz._field_type import AAZObjectType, AAZBoolType, AAZIntType, AAZStrType, AAZFloatType
    #
    #     class Arguments(AAZArguments):
    #         name = AAZStrType(options=["--name", "-n"])
    #
    #         properties = AAZObjectType(options=["--properties"])
    #         properties.enable = AAZBoolType(options=["enable"])
    #         properties.count = AAZIntType(options=["count"])
    #         properties.vnet = AAZObjectType(options=["vnet"])
    #         properties.vnet.address = AAZStrType(options=["address"])
    #         properties.vnet.threshold = AAZFloatType(options=["threshold"])
    #
    #     arguments = Arguments()
    #     arguments.name = "test"
    #     arguments.properties = {
    #         "enable": True,
    #         "count": 10,
    #         "vnet": {
    #             "address": "10.10.10.10",
    #             "threshold": 1,
    #         }
    #     }
    #
    #     assert arguments.name == "test"
    #     assert arguments.properties.enable == True
    #     assert arguments.properties.count == 10
    #     assert arguments.properties.vnet.address == "10.10.10.10"
    #     assert arguments.properties.vnet.threshold == 1
    #
    #     assert arguments.name._data == "test"
    #     assert arguments.properties.enable._data == True
    #     assert arguments.properties.count._data == 10
    #     assert arguments.properties.vnet.address._data == "10.10.10.10"
    #     assert arguments.properties.vnet.threshold._data == 1
