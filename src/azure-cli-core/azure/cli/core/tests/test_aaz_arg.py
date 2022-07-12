# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from azure.cli.core import azclierror
from azure.cli.core.aaz import exceptions as aazerror


class TestAAZArgShorthandSyntax(unittest.TestCase):

    def test_aaz_shorthand_syntax_simple_value(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser
        from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
        parser = AAZShortHandSyntaxParser()

        # test null value
        assert parser("null", is_simple=True) is None
        assert parser("'null'", is_simple=True) == 'null'

        assert parser("None", is_simple=True) == 'None'
        assert parser("'None'", is_simple=True) == 'None'

        # test single quota
        assert parser("''/'", is_simple=True) == "'"
        assert parser("'/'", is_simple=True) == "/"
        assert parser("'\"'", is_simple=True) == '"'

        assert parser('"\'"', is_simple=True) == '"\'"'
        assert parser('"\""', is_simple=True) == '"\""'
        assert parser("'https://azure.microsoft.com/en-us/'", is_simple=True) == "https://azure.microsoft.com/en-us/"
        assert parser("'C:\\Program Files (x86)\\'", is_simple=True) == "C:\\Program Files (x86)\\"
        assert parser("'/usr/lib/python3.8/'", is_simple=True) == "/usr/lib/python3.8/"

        # test escape character
        assert parser("'\"'", is_simple=True) == "\""
        assert parser("'\'/'", is_simple=True) == "\'"

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
            "c": "None",
            "d": ''
        }
        assert parser("{a:1,b:''/'}") == {
            "a": "1",
            "b": "'"
        }

        assert parser("{a:1,b:'/'}") == {
            "a": "1",
            "b": "/"
        }

        assert parser("{a:1,b:'//'}") == {
            "a": "1",
            "b": "//"
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

        assert parser("{a:{a1:' \n '/',a2:2}}") == {
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
            parser("{a:1,b:'/''}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:''/}")

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
            parser("{'a'/1':1}")

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
        assert parser("[None]") == ['None']
        assert parser("[None,]") == ['None']

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
            "a", 'None', "", "d"
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

    def test_aaz_compound_type_split_key(self):
        from azure.cli.core.aaz._arg_action import AAZCompoundTypeArgAction
        split_key = AAZCompoundTypeArgAction._split_key
        assert split_key("a.b.c") == ("a", "b", "c")
        assert split_key("[1]") == (1,)
        assert split_key("[-10]") == (-10,)
        assert split_key("a1[5].b[2].c") == ("a1", 5, "b", 2, "c")

        with self.assertRaises(AssertionError):
            split_key(".a")

        with self.assertRaises(AssertionError):
            split_key(".[5]")

        with self.assertRaises(AssertionError):
            split_key("b.a.[5]")

    def test_aaz_str_arg(self):
        from azure.cli.core.aaz._arg import AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        schema = AAZArgumentsSchema()
        v = schema()

        schema.work_day = AAZStrArg(
            options=["--work-day", "-d"],
            enum={
                "1": "Monday",
                "2": "Tuesday",
                "3": "Wednesday",
                "4": "Thursday",
                "5": "Friday",
                "6": "Saturday",
                "7": "Sunday",
                "Mon": "Monday",
                "Tue": "Tuesday",
                "Wed": "Wednesday",
                "Thu": "Thursday",
                "Fri": "Friday",
                "Sat": "Saturday",
                "Sun": "Sunday",
            },
            nullable=True,
            blank="Sunday"
        )
        arg = schema.work_day.to_cmd_arg("work_day")
        assert len(arg.choices) == 14
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, "1")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "work_day")
        assert v.work_day == "Monday"

        action.setup_operations(dest_ops, "2")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "work_day")
        assert v.work_day == "Tuesday"

        action.setup_operations(dest_ops, "Thu")
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "work_day")
        assert v.work_day == "Thursday"

        action.setup_operations(dest_ops, "fri")
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "work_day")
        assert v.work_day == "Friday"

        # null value
        action.setup_operations(dest_ops, 'null')
        assert len(dest_ops._ops) == 5
        dest_ops.apply(v, "work_day")
        assert v.work_day == None  # must use '== None', because 'is None' will not work

        # blank value
        action.setup_operations(dest_ops, None)
        assert len(dest_ops._ops) == 6
        dest_ops.apply(v, "work_day")
        assert v.work_day == "Sunday"

        # null value
        action.setup_operations(dest_ops, 'null')
        assert len(dest_ops._ops) == 7
        dest_ops.apply(v, "work_day")
        assert v.work_day == None

        # test invalid operations
        with self.assertRaises(azclierror.InvalidArgumentValueError):
            action.setup_operations(dest_ops, '1234')
        assert len(dest_ops._ops) == 7
        dest_ops.apply(v, "work_day")
        assert v.work_day == None

        # New argument
        schema.name = AAZStrArg(options=["--name", "-n"])
        arg = schema.name.to_cmd_arg("work_day")
        action = arg.type.settings["action"]
        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, "test name")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "name")
        assert v.name == "test name"

        action.setup_operations(dest_ops, "")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "name")
        assert v.name == ""

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "null")
        with self.assertRaises(aazerror.AAZInvalidShorthandSyntaxError):
            action.setup_operations(dest_ops, "'l")
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, None)

        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "name")
        assert v.name == ""

        action.setup_operations(dest_ops, " aa' l_;{]'")
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "name")
        assert v.name == " aa' l_;{]'"

    def test_aaz_int_arg(self):
        from azure.cli.core.aaz._arg import AAZIntArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        schema = AAZArgumentsSchema()
        v = schema()

        schema.score = AAZIntArg(
            options=["--score", "-s"],
            enum={
                "A": 100,
                "B": 90,
                "C": 80,
                "D": 0,
            },
            nullable=True,
            blank=0
        )
        arg = schema.score.to_cmd_arg("score")
        assert len(arg.choices) == 4
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, "A")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "score")
        assert v.score == 100

        # null value
        action.setup_operations(dest_ops, "null")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "score")
        assert v.score == None

        # blank value
        action.setup_operations(dest_ops, None)
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "score")
        assert v.score == 0

        # null value
        action.setup_operations(dest_ops, "null")
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "score")
        assert v.score == None

        # credit argument
        schema.credit = AAZIntArg(options=["--credit", "-c"])
        arg = schema.credit.to_cmd_arg("credit")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, "-100")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "credit")
        assert v.credit == -100

        action.setup_operations(dest_ops, "0")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "credit")
        assert v.credit == 0

        action.setup_operations(dest_ops, "100")
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "credit")
        assert v.credit == 100

        action.setup_operations(dest_ops, "'10'")
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "credit")
        assert v.credit == 10

        # test blank
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, None)

        # test null
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "null")

        with self.assertRaises(ValueError):
            action.setup_operations(dest_ops, "100.123")

        with self.assertRaises(ValueError):
            action.setup_operations(dest_ops, " ")

    def test_aaz_float_arg(self):
        from azure.cli.core.aaz._arg import AAZFloatArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        schema = AAZArgumentsSchema()
        v = schema()

        schema.score = AAZFloatArg(
            options=["--score", "-s"],
            enum={
                "A": 100.0,
                "B": 90.0,
                "C": 80.0,
                "D": 0.0,
            },
            nullable=True,
            blank=0.0
        )
        arg = schema.score.to_cmd_arg("score")
        assert len(arg.choices) == 4
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, "A")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "score")
        assert v.score == 100.0

        # null value
        action.setup_operations(dest_ops, "null")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "score")
        assert v.score == None

        # blank value
        action.setup_operations(dest_ops, None)
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "score")
        assert v.score == 0.0

        # null value
        action.setup_operations(dest_ops, "null")
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "score")
        assert v.score == None

        # credit argument
        schema.credit = AAZFloatArg(options=["--credit", "-c"])
        arg = schema.credit.to_cmd_arg("credit")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, "-100")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "credit")
        assert v.credit == -100.0

        action.setup_operations(dest_ops, "0.23")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "credit")
        assert v.credit == 0.23

        action.setup_operations(dest_ops, "100.1")
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "credit")
        assert v.credit == 100.1

        action.setup_operations(dest_ops, "'10.123'")
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "credit")
        assert v.credit == 10.123

        # test blank
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, None)

        # test null
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "null")

        with self.assertRaises(ValueError):
            action.setup_operations(dest_ops, " ")

    def test_aaz_bool_arg(self):
        from azure.cli.core.aaz._arg import AAZBoolArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        schema = AAZArgumentsSchema()
        v = schema()

        schema.enable = AAZBoolArg(options=["--enable", "-e"])
        arg = schema.enable.to_cmd_arg("enable")
        assert len(arg.choices) == 10
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, None)
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "enable")
        assert v.enable == True

        action.setup_operations(dest_ops, "false")
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "enable")
        assert v.enable == False

        action.setup_operations(dest_ops, "true")
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "enable")
        assert v.enable == True

        action.setup_operations(dest_ops, "f")
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "enable")
        assert v.enable == False

        action.setup_operations(dest_ops, "t")
        assert len(dest_ops._ops) == 5
        dest_ops.apply(v, "enable")
        assert v.enable == True

        action.setup_operations(dest_ops, "no")
        assert len(dest_ops._ops) == 6
        dest_ops.apply(v, "enable")
        assert v.enable == False

        action.setup_operations(dest_ops, "yes")
        assert len(dest_ops._ops) == 7
        dest_ops.apply(v, "enable")
        assert v.enable == True

        action.setup_operations(dest_ops, "n")
        assert len(dest_ops._ops) == 8
        dest_ops.apply(v, "enable")
        assert v.enable == False

        action.setup_operations(dest_ops, "y")
        assert len(dest_ops._ops) == 9
        dest_ops.apply(v, "enable")
        assert v.enable == True

        action.setup_operations(dest_ops, "0")
        assert len(dest_ops._ops) == 10
        dest_ops.apply(v, "enable")
        assert v.enable == False

        action.setup_operations(dest_ops, "1")
        assert len(dest_ops._ops) == 11
        dest_ops.apply(v, "enable")
        assert v.enable == True

        # null value
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "null")

        # null value
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "null")

        schema.started = AAZBoolArg(
            options=["--started", "-s"],
            nullable=True,
            blank=False,
        )
        arg = schema.started.to_cmd_arg("started")
        assert len(arg.choices) == 10
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        # null value
        action.setup_operations(dest_ops, "null")
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "started")
        assert v.started == None

        # blank value
        action.setup_operations(dest_ops, None)
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "started")
        assert v.started == False

        action.setup_operations(dest_ops, "TRUE")
        assert len(dest_ops._ops) == 3
        dest_ops.apply(v, "started")
        assert v.started == True

        # assert len(dest_ops._ops) == 12
        # dest_ops.apply(v, "enable")
        # assert v.enable == False
        #
        # action.setup_operations(dest_ops, "true")
        # assert len(dest_ops._ops) == 3
        # dest_ops.apply(v, "enable")
        # assert v.enable == True

    def test_aaz_list_arg(self):
        from azure.cli.core.aaz._arg import AAZListArg, AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations, _ELEMENT_APPEND_KEY
        schema = AAZArgumentsSchema()
        v = schema()

        schema.names = AAZListArg(
            options=["--names", "--ns"],
            singular_options=["--name", "-n"]
        )
        schema.names.Element = AAZStrArg(
            nullable=True,
            blank="a blank value"
        )

        arg = schema.names.to_cmd_arg("names")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        # null value
        action.setup_operations(dest_ops, ["null"])
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "names")
        assert v.names == [None, ]

        action.setup_operations(dest_ops, ["[a,b,'c',' ']"])
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "names")
        assert v.names == ['a', 'b', 'c', ' ']

        action.setup_operations(dest_ops, ["[2]=efg", "[-1]='null'", "[0]="])
        assert len(dest_ops._ops) == 5
        dest_ops.apply(v, "names")
        assert v.names == ['a blank value', 'b', 'efg', 'null']

        action.setup_operations(dest_ops, ["c", "d"])
        assert len(dest_ops._ops) == 6
        dest_ops.apply(v, "names")
        assert v.names == ['c', 'd']

        action.setup_operations(dest_ops, ["[]"])
        assert len(dest_ops._ops) == 7
        dest_ops.apply(v, "names")
        assert v.names == []

        action.setup_operations(dest_ops, ["a"])
        assert len(dest_ops._ops) == 8
        dest_ops.apply(v, "names")
        assert v.names == ["a"]

        action.setup_operations(dest_ops, ["", "''"])
        assert len(dest_ops._ops) == 9
        dest_ops.apply(v, "names")
        assert v.names == ["", ""]

        action.setup_operations(dest_ops, ["a", 'null', 'None', "b", ""])
        assert len(dest_ops._ops) == 10
        dest_ops.apply(v, "names")
        assert v.names == ["a", None, 'None', "b", ""]

        # blank value
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, None)

        action.setup_operations(dest_ops, ["[]"])
        assert len(dest_ops._ops) == 11
        dest_ops.apply(v, "names")
        assert v.names == []

        # test singular action
        singular_action = schema.names.Element._build_cmd_action()

        singular_action.setup_operations(dest_ops, ["a"], prefix_keys=[_ELEMENT_APPEND_KEY])
        assert len(dest_ops._ops) == 12
        dest_ops.apply(v, "names")
        assert v.names == ["a"]

        singular_action.setup_operations(dest_ops, ["b"], prefix_keys=[_ELEMENT_APPEND_KEY])
        assert len(dest_ops._ops) == 13
        dest_ops.apply(v, "names")
        assert v.names == ["a", "b"]

        singular_action.setup_operations(dest_ops, None, prefix_keys=[_ELEMENT_APPEND_KEY])
        assert len(dest_ops._ops) == 14
        dest_ops.apply(v, "names")
        assert v.names == ["a", "b", "a blank value"]

        singular_action.setup_operations(dest_ops, [""], prefix_keys=[_ELEMENT_APPEND_KEY])
        assert len(dest_ops._ops) == 15
        dest_ops.apply(v, "names")
        assert v.names == ["a", "b", "a blank value", ""]

    def test_aaz_dict_arg(self):
        from azure.cli.core.aaz._arg import AAZDictArg, AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        schema = AAZArgumentsSchema()
        v = schema()

        schema.tags = AAZDictArg(
            options=["--tags", "-t"],
        )
        schema.tags.Element = AAZStrArg(
            nullable=True,
            blank="a blank value"
        )

        arg = schema.tags.to_cmd_arg("tags")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        # null value
        action.setup_operations(dest_ops, ["a=null", "b=None"])
        assert len(dest_ops._ops) == 2
        dest_ops.apply(v, "tags")
        assert v.tags == {"a": None, "b": 'None'}

        action.setup_operations(dest_ops, ["b=6", "c="])
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "tags")
        assert v.tags == {"a": None, "b": "6", "c": "a blank value"}

        action.setup_operations(dest_ops, ["{ab:1,bc:2,cd:'null'}"])
        assert len(dest_ops._ops) == 5
        dest_ops.apply(v, "tags")
        assert v.tags == {"ab": '1', "bc": '2', 'cd': 'null'}

        action.setup_operations(dest_ops, ["{}"])
        assert len(dest_ops._ops) == 6
        dest_ops.apply(v, "tags")
        assert v.tags == {}

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, ["=1"])

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, ["null"])

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, ["null"])

        with self.assertRaises(aazerror.AAZInvalidShorthandSyntaxError):
            action.setup_operations(dest_ops, ["{c:}"])

    def test_aaz_object_arg(self):
        from azure.cli.core.aaz._arg import AAZDictArg, AAZListArg, AAZObjectArg, AAZIntArg, AAZBoolArg, AAZFloatArg, \
            AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        schema = AAZArgumentsSchema()
        v = schema()

        schema.properties = AAZObjectArg(
            options=["--prop", "-p"],
            nullable=True
        )

        schema.properties.enable = AAZBoolArg(
            options=["enable"],
            nullable=True,
        )
        schema.properties.tags = AAZDictArg(
            options=["tags"],
            nullable=True
        )
        schema.properties.tags.Element = AAZIntArg()
        schema.properties.vnets = AAZListArg(
            options=["vnets"],
            nullable=True
        )
        schema.properties.vnets.Element = AAZObjectArg()
        schema.properties.vnets.Element.id = AAZStrArg(
            options=["id"],
        )

        schema.properties.pt = AAZFloatArg(
            options=["pt"],
            nullable=True,
            blank="0.1"
        )

        arg = schema.properties.to_cmd_arg("properties")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        assert len(dest_ops._ops) == 0

        action.setup_operations(dest_ops, ["{enable:false,tags:{a:1,3:2},vnets:[{id:/123}],pt:12.123}"])
        assert len(dest_ops._ops) == 1
        dest_ops.apply(v, "properties")
        assert v.properties == {
            "enable": False,
            "tags": {
                "a": 1,
                "3": 2,
            },
            "vnets": [
                {"id": "/123"},
            ],
            "pt": 12.123
        }

        action.setup_operations(dest_ops, ["pt=", "enable=null", "vnets=[]"])
        assert len(dest_ops._ops) == 4
        dest_ops.apply(v, "properties")
        assert v.properties == {
            "enable": None,
            "tags": {
                "a": 1,
                "3": 2,
            },
            "vnets": [],
            "pt": 0.1
        }

        action.setup_operations(dest_ops, ["{}"])
        assert len(dest_ops._ops) == 5
        dest_ops.apply(v, "properties")
        assert v.properties == {}

        action.setup_operations(dest_ops, ["null"])
        assert len(dest_ops._ops) == 6
        dest_ops.apply(v, "properties")
        assert v.properties == None

        action.setup_operations(dest_ops, ["{enable:True,tags:null,vnets:null,pt:12.123}"])
        assert len(dest_ops._ops) == 7
        dest_ops.apply(v, "properties")
        assert v.properties == {
            "enable": True,
            "tags": None,
            "vnets": None,
            "pt": 12.123
        }
