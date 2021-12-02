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
        assert parser("null", is_simple=True) is None
        assert parser("'null'", is_simple=True) == 'null'

        assert parser("None", is_simple=True) is None
        assert parser("'None'", is_simple=True) == 'None'

        # test single quota
        assert parser("'/''", is_simple=True) == "'"
        assert parser("'\"'", is_simple=True) == '"'

        assert parser('"\'"', is_simple=True) == '"\'"'
        assert parser('"\""', is_simple=True) == '"\""'

        # test escape character
        assert parser("'\"'", is_simple=True) == "\""
        assert parser("'/\''", is_simple=True) == "\'"

        assert parser("'\b'", is_simple=True) == "\b"
        assert parser("'\f'", is_simple=True) == "\f"
        assert parser("'\n'", is_simple=True) == "\n"
        assert parser("'\r'", is_simple=True) == "\r"
        assert parser("'\t'", is_simple=True) == "\t"

        assert parser('\b', is_simple=True) == '\b'
        assert parser('\f', is_simple=True) == '\f'
        assert parser('\n', is_simple=True) == '\n'
        assert parser('\r', is_simple=True) == '\r'
        assert parser('\t', is_simple=True) == '\t'

        assert parser('"\b"', is_simple=True) == '"\b"'
        assert parser('"\f"', is_simple=True) == '"\f"'
        assert parser('"\n"', is_simple=True) == '"\n"'
        assert parser('"\r"', is_simple=True) == '"\r"'
        assert parser('"\t"', is_simple=True) == '"\t"'

        # whitespace character should be warped in single quotes

        # test normal string
        assert parser("abc", is_simple=True) == "abc"
        assert parser("1", is_simple=True) == "1"
        assert parser("_", is_simple=True) == "_"
        assert parser("''", is_simple=True) == ''
        assert parser('""', is_simple=True) == '""'
        assert parser("'{'", is_simple=True) == "{"
        assert parser('"{"', is_simple=True) == '"{"'
        assert parser("'}'", is_simple=True) == "}"
        assert parser('"}"', is_simple=True) == '"}"'
        assert parser(' ', is_simple=True) == ' '
        assert parser("' '", is_simple=True) == ' '

        assert parser("'{abc'", is_simple=True) == "{abc"
        assert parser("'abc}'", is_simple=True) == "abc}"
        assert parser("'abc{'", is_simple=True) == "abc{"
        assert parser("'}abc'", is_simple=True) == "}abc"
        assert parser("'{a:1, b:2}'", is_simple=True) == "{a:1, b:2}"

        assert parser("'['", is_simple=True) == "["
        assert parser('"["', is_simple=True) == '"["'
        assert parser("']'", is_simple=True) == "]"
        assert parser('"]"', is_simple=True) == '"]"'

        assert parser("'[abc'", is_simple=True) == "[abc"
        assert parser("'abc['", is_simple=True) == "abc["
        assert parser("'abc]'", is_simple=True) == "abc]"
        assert parser("']abc'", is_simple=True) == "]abc"
        assert parser("'[1, 2, 3]'", is_simple=True) == "[1, 2, 3]"

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("", is_simple=True)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'", is_simple=True)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'No", is_simple=True)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'A'bc", is_simple=True)

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
        assert parser("{a:1,b:'/''}") == {
            "a": "1",
            "b": "'"
        }

        assert parser("{a:1,b:'//'}") == {
            "a": "1",
            "b": "/"
        }

        assert parser("{a:1,b:/}") == {
            "a": "1",
            "b": "/"
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

        assert parser("{a:{a1:' \n /\'',a2:2}}") == {
            "a": {
                "a1": " \n '",
                "a2": "2",
            }
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

        assert parser("{a:[{prop1:1,prop2:2},{a1:[b,null,c,'d:e \"]'],a2:'2 3\t\"}',a4:'',a3:null,}],e:f,g:null}") == {
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

        # compare with json
        dt = {}
        s = json.dumps(dt, separators=(',', ':'))
        assert parser(s) == dt

        dt = {"a": 1}
        s = json.dumps(dt, separators=(',', ':'))
        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser(s)

        # other forbidden expression
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
            parser("{a:1,b:'/'}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:{}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:{}}{")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:{a1:1',a2:2}}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:{a1:1'2,a2:2}}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:{a1:1\",a2:2}}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:{a1:1\"2,a2:2}}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:{a1: 1,a2:2}}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:{a1:1 ,a2:2}}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a'1:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a\"1:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a'1:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{'a\"1':1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a'1:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{'a/'1':1}")

    def test_aaz_shorthand_syntax_list_value(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser
        from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError

        parser = AAZShortHandSyntaxParser()
        assert parser("[]") == []

        assert parser("[c]") == ["c"]

        assert parser("['c']") == ["c"]

        assert parser("[c,]") == ["c"]

        assert parser("[null]") == [None]
        assert parser("[null,]") == [None]
        assert parser("[None]") == [None]
        assert parser("[None,]") == [None]

        assert parser("['null',]") == ['null']

        assert parser("['None',]") == ['None']

        assert parser("[' ',]") == [' ']

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

        # compare with json
        ls = []
        s = json.dumps(ls, separators=(',', ':'))
        assert parser(s) == ls

        ls = [None, {}]
        s = json.dumps(ls, separators=(',', ':'))
        assert parser(s) == ls

        ls = [1, 2, 3, 4]
        s = json.dumps(ls, separators=(',', ':'))
        assert parser(s) == ['1', '2', '3', '4']

        ls = ["1", "2"]
        s = json.dumps(ls, separators=(',', ':'))
        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser(s)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[,]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[',]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[ ]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a'b,]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a\"b,]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("[a b,]")

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
