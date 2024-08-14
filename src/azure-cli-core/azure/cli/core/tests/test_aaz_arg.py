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
        self.assertEqual(parser("null", is_simple=True), None)
        self.assertEqual(parser("'null'", is_simple=True), 'null')

        self.assertEqual(parser("None", is_simple=True), 'None')
        self.assertEqual(parser("'None'", is_simple=True), 'None')

        # test single quota
        self.assertEqual(parser("''/'", is_simple=True), "'")
        self.assertEqual(parser("'/'", is_simple=True), "/")
        self.assertEqual(parser("'\"'", is_simple=True), '"')

        self.assertEqual(parser('"\'"', is_simple=True), '"\'"')
        self.assertEqual(parser('"\""', is_simple=True), '"\""')
        self.assertEqual(parser("'https://azure.microsoft.com/en-us/'", is_simple=True), "https://azure.microsoft.com/en-us/")
        self.assertEqual(parser("'C:\\Program Files (x86)\\'", is_simple=True), "C:\\Program Files (x86)\\")
        self.assertEqual(parser("'/usr/lib/python3.8/'", is_simple=True), "/usr/lib/python3.8/")

        # test escape character
        self.assertEqual(parser("'\"'", is_simple=True), "\"")
        self.assertEqual(parser("'\'/'", is_simple=True), "\'")

        self.assertEqual(parser("'\b'", is_simple=True), "\b")
        self.assertEqual(parser("'\f'", is_simple=True), "\f")
        self.assertEqual(parser("'\n'", is_simple=True), "\n")
        self.assertEqual(parser("'\r'", is_simple=True), "\r")
        self.assertEqual(parser("'\t'", is_simple=True), "\t")

        self.assertEqual(parser('\b', is_simple=True), '\b')
        self.assertEqual(parser('\f', is_simple=True), '\f')
        self.assertEqual(parser('\n', is_simple=True), '\n')
        self.assertEqual(parser('\r', is_simple=True), '\r')
        self.assertEqual(parser('\t', is_simple=True), '\t')

        self.assertEqual(parser('"\b"', is_simple=True), '"\b"')
        self.assertEqual(parser('"\f"', is_simple=True), '"\f"')
        self.assertEqual(parser('"\n"', is_simple=True), '"\n"')
        self.assertEqual(parser('"\r"', is_simple=True), '"\r"')
        self.assertEqual(parser('"\t"', is_simple=True), '"\t"')

        # whitespace character should be warped in single quotes

        # test normal string
        self.assertEqual(parser("abc", is_simple=True), "abc")
        self.assertEqual(parser("1", is_simple=True), "1")
        self.assertEqual(parser("_", is_simple=True), "_")
        self.assertEqual(parser("''", is_simple=True), '')
        self.assertEqual(parser('""', is_simple=True), '""')
        self.assertEqual(parser("'{'", is_simple=True), "{")
        self.assertEqual(parser('"{"', is_simple=True), '"{"')
        self.assertEqual(parser("'}'", is_simple=True), "}")
        self.assertEqual(parser('"}"', is_simple=True), '"}"')
        self.assertEqual(parser(' ', is_simple=True), ' ')
        self.assertEqual(parser("' '", is_simple=True), ' ')

        self.assertEqual(parser("'{abc'", is_simple=True), "{abc")
        self.assertEqual(parser("'abc}'", is_simple=True), "abc}")
        self.assertEqual(parser("'abc{'", is_simple=True), "abc{")
        self.assertEqual(parser("'}abc'", is_simple=True), "}abc")
        self.assertEqual(parser("'{a:1, b:2}'", is_simple=True), "{a:1, b:2}")

        self.assertEqual(parser("'['", is_simple=True), "[")
        self.assertEqual(parser('"["', is_simple=True), '"["')
        self.assertEqual(parser("']'", is_simple=True), "]")
        self.assertEqual(parser('"]"', is_simple=True), '"]"')

        self.assertEqual(parser("'[abc'", is_simple=True), "[abc")
        self.assertEqual(parser("'abc['", is_simple=True), "abc[")
        self.assertEqual(parser("'abc]'", is_simple=True), "abc]")
        self.assertEqual(parser("']abc'", is_simple=True), "]abc")
        self.assertEqual(parser("'[1, 2, 3]'", is_simple=True), "[1, 2, 3]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("", is_simple=True)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'", is_simple=True)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'No", is_simple=True)

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("'A'bc", is_simple=True)

    def test_aaz_shorthand_syntax_dict_value(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser, AAZBlankArgValue
        from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
        parser = AAZShortHandSyntaxParser()
        self.assertEqual(parser("{}"), {})
        self.assertEqual(parser("{a:1,b:2,c:null,d:''}"), {
            "a": "1",
            "b": "2",
            "c": None,
            "d": ''
        })
        self.assertEqual(parser("{a:1,b:2,c:None,d:'',}"), {
            "a": "1",
            "b": "2",
            "c": "None",
            "d": ''
        })
        self.assertEqual(parser("{a:1,b:''/'}"), {
            "a": "1",
            "b": "'"
        })

        self.assertEqual(parser("{a:1,b:'/'}"), {
            "a": "1",
            "b": "/"
        })

        self.assertEqual(parser("{a:1,b:'//'}"), {
            "a": "1",
            "b": "//"
        })

        self.assertEqual(parser("{a:1,b:/}"), {
            "a": "1",
            "b": "/"
        })

        self.assertEqual(parser("{a:1,b:2,c:Null,d:''}"), {
            "a": "1",
            "b": "2",
            "c": "Null",
            "d": ''
        })
        self.assertEqual(parser("{a:1,b:2,c:none,d:'',}"), {
            "a": "1",
            "b": "2",
            "c": "none",
            "d": ''
        })

        self.assertEqual(parser("{a:{a1:' \n '/',a2:2}}"), {
            "a": {
                "a1": " \n '",
                "a2": "2",
            }
        })

        self.assertEqual(parser("{a:{a1:1,a2:2}}"), {
            "a": {
                "a1": "1",
                "a2": "2",
            }
        })
        self.assertEqual(parser("{a:{a1:1,a2:2},}"), {
            "a": {
                "a1": "1",
                "a2": "2",
            }
        })

        self.assertEqual(parser("{a:{a1:{},a2:2}}"), {
            "a": {
                "a1": {},
                "a2": "2",
            }
        })

        self.assertEqual(parser("{a:{a1,a2:2,c},a3,a4:''}"), {
            "a": {
                "a1": AAZBlankArgValue,
                "a2": "2",
                "c": AAZBlankArgValue,
            },
            "a3": AAZBlankArgValue,
            "a4": '',
        })

        self.assertEqual(parser("{a:1,'',c:1,e}"), {
            "a": "1",
            "": AAZBlankArgValue,
            "c": "1",
            "e": AAZBlankArgValue,
        })

        self.assertEqual(parser("{a:[{prop1:1,prop2:2},{a1:[b,null,c,'d:e \"]'],a2:'2 3\t\"}',a4:'',a3:null,}],e:f,g:null}"), {
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
        })

        # compare with json
        dt = {}
        s = json.dumps(dt, separators=(',', ':'))
        self.assertEqual(parser(s), dt)

        dt = {"a": 1}
        s = json.dumps(dt, separators=(',', ':'))
        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser(s)

        # other forbidden expression
        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,,c:1}")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:1]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parser("{a:1,b:]")

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
        self.assertEqual(parser("[]"), [])

        self.assertEqual(parser("[c]"), ["c"])

        self.assertEqual(parser("['c']"), ["c"])

        self.assertEqual(parser("[c,]"), ["c"])

        self.assertEqual(parser("[null]"), [None])
        self.assertEqual(parser("[null,]"), [None])
        self.assertEqual(parser("[None]"), ['None'])
        self.assertEqual(parser("[None,]"), ['None'])

        self.assertEqual(parser("['null',]"), ['null'])

        self.assertEqual(parser("['None',]"), ['None'])

        self.assertEqual(parser("[' ',]"), [' '])

        self.assertEqual(parser("[a,b,c,d]"), [
            "a", "b", "c", "d"
        ])
        self.assertEqual(parser("[a,null,'',d]"), [
            "a", None, "", "d"
        ])
        self.assertEqual(parser("[a,None,'',d,]"), [
            "a", 'None', "", "d"
        ])
        self.assertEqual(parser("[a,[],{},[b,c,d],]"), [
            "a", [], {}, ["b", "c", "d"]
        ])

        # compare with json
        ls = []
        s = json.dumps(ls, separators=(',', ':'))
        self.assertEqual(parser(s), ls)

        ls = [None, {}]
        s = json.dumps(ls, separators=(',', ':'))
        self.assertEqual(parser(s), ls)

        ls = [1, 2, 3, 4]
        s = json.dumps(ls, separators=(',', ':'))
        self.assertEqual(parser(s), ['1', '2', '3', '4'])

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
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser
        key_pattern = AAZShortHandSyntaxParser.partial_value_key_pattern

        test_value = "a.b.c="
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], 'a.b.c')
        self.assertEqual(match[len(match.regs) - 1], '')

        test_value = "a_b-C=aaa"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], 'a_b-C')
        self.assertEqual(match[len(match.regs) - 1], 'aaa')

        test_value = "[10]=aaa"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], '[10]')
        self.assertEqual(match[len(match.regs) - 1], 'aaa')

        test_value = "a_b.C[10]=aaa"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], 'a_b.C[10]')
        self.assertEqual(match[len(match.regs) - 1], 'aaa')

        test_value = "a_b.C[10].D-e_f=aaa"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], 'a_b.C[10].D-e_f')
        self.assertEqual(match[len(match.regs) - 1], 'aaa')

        test_value = "a_b-C={aaa:b}"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], 'a_b-C')
        self.assertEqual(match[len(match.regs) - 1], '{aaa:b}')

        test_value = "a_b-C=[aaa,b]"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], 'a_b-C')
        self.assertEqual(match[len(match.regs) - 1], '[aaa,b]')

        test_value = "a.'/bc sef'/.sss[2]'[1]='/a='"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match[1], "a.'/bc sef'/.sss[2]'[1]")
        self.assertEqual(match[len(match.regs) - 1], "'/a='")

        test_value = "{a_b:aaa}"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match, None)

        test_value = "[aaa,bbb]"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match, None)

        test_value = "a_b.C[abc]=aaa"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match, None)

        test_value = "a_b.C[10].D-e_f"
        match = key_pattern.fullmatch(test_value)
        self.assertEqual(match, None)

    def test_aaz_compound_type_split_key(self):
        from azure.cli.core.aaz._utils import AAZShortHandSyntaxParser, AAZInvalidShorthandSyntaxError
        parse_partial_value_key = AAZShortHandSyntaxParser.parse_partial_value_key
        self.assertEqual(parse_partial_value_key("a.b.c"), ("a", "b", "c"))
        self.assertEqual(parse_partial_value_key("[1]"), (1,))
        self.assertEqual(parse_partial_value_key("[-10]"), (-10,))
        self.assertEqual(parse_partial_value_key("a1[5].b[2].c"), ("a1", 5, "b", 2, "c"))
        self.assertEqual(parse_partial_value_key("a.'/bc sef'/.sss[2]'[1]"), ("a", "/bc sef'.sss[2]", 1))
        self.assertEqual(parse_partial_value_key("'/bc sef'/.sss[2]'"), ("/bc sef'.sss[2]", ))
        self.assertEqual(parse_partial_value_key("'/bc sef'/.sss[2]'.c"), ("/bc sef'.sss[2]", "c"))

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parse_partial_value_key(".a")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parse_partial_value_key(".[5]")

        with self.assertRaises(AAZInvalidShorthandSyntaxError):
            parse_partial_value_key("b.a.'/bc sef'/.sss[2]")

    def test_aaz_str_arg(self):
        from azure.cli.core.aaz._arg import AAZStrArg, AAZArgumentsSchema, AAZListArg
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
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
        schema.tasks = AAZListArg(
            options=["--tasks"],
            singular_options=["--task", "-t"],
        )
        schema.tasks.Element = AAZStrArg(
            enum={"task1", "task2"},
            enum_support_extension=True,
        )
        self.assertFalse(has_value(v.work_day))

        arg = schema.work_day.to_cmd_arg("work_day")
        self.assertEqual(len(arg.choices), 14)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, "1")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, "Monday")

        action.setup_operations(dest_ops, "2")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, "Tuesday")

        action.setup_operations(dest_ops, "Thu")
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, "Thursday")

        action.setup_operations(dest_ops, "fri")
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, "Friday")

        # null value
        action.setup_operations(dest_ops, 'null')
        self.assertEqual(len(dest_ops._ops), 5)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, None)  # must use '== None', because 'is None' will not work

        # blank value
        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 6)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, "Sunday")

        # null value
        action.setup_operations(dest_ops, 'null')
        self.assertEqual(len(dest_ops._ops), 7)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, None)

        # test invalid operations
        with self.assertRaises(azclierror.InvalidArgumentValueError):
            action.setup_operations(dest_ops, '1234')
        self.assertEqual(len(dest_ops._ops), 7)
        dest_ops.apply(v, "work_day")
        self.assertEqual(v.work_day, None)

        # Task argument
        arg = schema.tasks.to_cmd_arg("tasks")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, ["[task1,task2,task_ext]"])
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "tasks")
        self.assertEqual(v.tasks.to_serialized_data(), ["task1", "task2", "task_ext"])

        # New argument
        schema.name = AAZStrArg(options=["--name", "-n"])
        arg = schema.name.to_cmd_arg("work_day")
        action = arg.type.settings["action"]
        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, "test name")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "name")
        self.assertEqual(v.name, "test name")

        action.setup_operations(dest_ops, "")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "name")
        self.assertEqual(v.name, "")

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "null")
        with self.assertRaises(aazerror.AAZInvalidShorthandSyntaxError):
            action.setup_operations(dest_ops, "'l")
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, None)

        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "name")
        self.assertEqual(v.name, "")

        action.setup_operations(dest_ops, " aa' l_;{]'")
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "name")
        self.assertEqual(v.name, " aa' l_;{]'")

    def test_aaz_int_arg(self):
        from azure.cli.core.aaz._arg import AAZIntArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
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
            enum_support_extension=True,
            nullable=True,
            blank=0
        )

        self.assertFalse(has_value(v.score))

        arg = schema.score.to_cmd_arg("score")
        self.assertEqual(arg.choices, None)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, "A")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, 100)

        # null value
        action.setup_operations(dest_ops, "null")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, None)

        # blank value
        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, 0)

        # null value
        action.setup_operations(dest_ops, "null")
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, None)

         # extension value
        action.setup_operations(dest_ops, "1234")
        self.assertEqual(len(dest_ops._ops), 5)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, 1234)

        # extension invalid value
        with self.assertRaises(azclierror.InvalidArgumentValueError):
            action.setup_operations(dest_ops, "12A34")

        # credit argument
        schema.credit = AAZIntArg(options=["--credit", "-c"])
        arg = schema.credit.to_cmd_arg("credit")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, "-100")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, -100)

        action.setup_operations(dest_ops, "0")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, 0)

        action.setup_operations(dest_ops, "100")
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, 100)

        action.setup_operations(dest_ops, "'10'")
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, 10)

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
        from azure.cli.core.aaz import has_value
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
            enum_support_extension=True,
            nullable=True,
            blank=0.0
        )
        self.assertFalse(has_value(v.score))

        arg = schema.score.to_cmd_arg("score")
        self.assertEqual(arg.choices, None)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, "A")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, 100.0)

        # null value
        action.setup_operations(dest_ops, "null")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, None)

        # blank value
        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, 0.0)

        # null value
        action.setup_operations(dest_ops, "null")
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "score")
        self.assertEqual(v.score, None)
        
        # extension value
        from unittest import mock
        with mock.patch('azure.cli.core.aaz._arg.logger') as mock_logger:
            action.setup_operations(dest_ops, "1234")
            self.assertEqual(len(dest_ops._ops), 5)
            dest_ops.apply(v, "score")
            self.assertEqual(v.score, 1234.0)
            call_args = mock_logger.warning.call_args
            self.assertEqual("Use extended value '%s' outside choices %s.", call_args[0][0])
            self.assertEqual("1234.0", call_args[0][1])

        # extension invalid value
        with self.assertRaises(azclierror.InvalidArgumentValueError):
            action.setup_operations(dest_ops, "12A34")

        # credit argument
        schema.credit = AAZFloatArg(options=["--credit", "-c"])
        arg = schema.credit.to_cmd_arg("credit")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, "-100")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, -100.0)

        action.setup_operations(dest_ops, "0.23")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, 0.23)

        action.setup_operations(dest_ops, "100.1")
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, 100.1)

        action.setup_operations(dest_ops, "'10.123'")
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "credit")
        self.assertEqual(v.credit, 10.123)

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
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.enable = AAZBoolArg(options=["--enable", "-e"])
        self.assertFalse(has_value(v.enable))

        arg = schema.enable.to_cmd_arg("enable")
        self.assertEqual(len(arg.choices), 10)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, True)

        action.setup_operations(dest_ops, "false")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, False)

        action.setup_operations(dest_ops, "true")
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, True)

        action.setup_operations(dest_ops, "f")
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, False)

        action.setup_operations(dest_ops, "t")
        self.assertEqual(len(dest_ops._ops), 5)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, True)

        action.setup_operations(dest_ops, "no")
        self.assertEqual(len(dest_ops._ops), 6)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, False)

        action.setup_operations(dest_ops, "yes")
        self.assertEqual(len(dest_ops._ops), 7)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, True)

        action.setup_operations(dest_ops, "n")
        self.assertEqual(len(dest_ops._ops), 8)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, False)

        action.setup_operations(dest_ops, "y")
        self.assertEqual(len(dest_ops._ops), 9)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, True)

        action.setup_operations(dest_ops, "0")
        self.assertEqual(len(dest_ops._ops), 10)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, False)

        action.setup_operations(dest_ops, "1")
        self.assertEqual(len(dest_ops._ops), 11)
        dest_ops.apply(v, "enable")
        self.assertEqual(v.enable, True)

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
        self.assertEqual(len(arg.choices), 10)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        # null value
        action.setup_operations(dest_ops, "null")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "started")
        self.assertEqual(v.started, None)

        # blank value
        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "started")
        self.assertEqual(v.started, False)

        action.setup_operations(dest_ops, "TRUE")
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "started")
        self.assertEqual(v.started, True)

        # self.assertEqual(len(dest_ops._ops), 12)
        # dest_ops.apply(v, "enable")
        # self.assertEqual(v.enable, False)
        #
        # action.setup_operations(dest_ops, "true")
        # self.assertEqual(len(dest_ops._ops), 3)
        # dest_ops.apply(v, "enable")
        # self.assertEqual(v.enable, True)

    def test_aaz_list_arg(self):
        from azure.cli.core.aaz._arg import AAZListArg, AAZStrArg, AAZArgumentsSchema, AAZObjectArg
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations, _ELEMENT_APPEND_KEY
        from azure.cli.core.aaz import has_value
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
        schema.user_assigned = AAZListArg(
            options=["--user-assigned"],
            blank=["1", "2"],
        )
        schema.user_assigned.Element = AAZStrArg(
        )
        schema.objs = AAZListArg(
            options=["--objs"],
            singular_options=["--obj"]
        )
        element = schema.objs.Element = AAZObjectArg()
        element.attr = AAZStrArg(options=["--attr"])
        element.prop = AAZStrArg(options=["--prop"])

        self.assertFalse(has_value(v.names))

        arg = schema.names.to_cmd_arg("names")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        # null value
        action.setup_operations(dest_ops, ["null"])
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, [None, ])

        action.setup_operations(dest_ops, ["[a,b,'c',' ']"])
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ['a', 'b', 'c', ' '])

        action.setup_operations(dest_ops, ["[2]=efg", "[-1]='null'", "[0]="])
        self.assertEqual(len(dest_ops._ops), 5)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ['a blank value', 'b', 'efg', 'null'])

        action.setup_operations(dest_ops, ["c", "d"])
        self.assertEqual(len(dest_ops._ops), 6)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ['c', 'd'])

        action.setup_operations(dest_ops, ["[]"])
        self.assertEqual(len(dest_ops._ops), 7)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, [])

        action.setup_operations(dest_ops, ["a"])
        self.assertEqual(len(dest_ops._ops), 8)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["a"])

        action.setup_operations(dest_ops, ["", "''"])
        self.assertEqual(len(dest_ops._ops), 9)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["", ""])

        action.setup_operations(dest_ops, ["a", 'null', 'None', "b", ""])
        self.assertEqual(len(dest_ops._ops), 10)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["a", None, 'None', "b", ""])

        # blank value
        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, None)

        action.setup_operations(dest_ops, ["[]"])
        self.assertEqual(len(dest_ops._ops), 11)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, [])

        # test singular action
        singular_action = schema.names.Element._build_cmd_action()

        singular_action.setup_operations(dest_ops, ["a"], prefix_keys=[_ELEMENT_APPEND_KEY])
        self.assertEqual(len(dest_ops._ops), 12)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["a"])

        singular_action.setup_operations(dest_ops, ["b"], prefix_keys=[_ELEMENT_APPEND_KEY])
        self.assertEqual(len(dest_ops._ops), 13)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["a", "b"])

        singular_action.setup_operations(dest_ops, None, prefix_keys=[_ELEMENT_APPEND_KEY])
        self.assertEqual(len(dest_ops._ops), 14)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["a", "b", "a blank value"])

        singular_action.setup_operations(dest_ops, [""], prefix_keys=[_ELEMENT_APPEND_KEY])
        self.assertEqual(len(dest_ops._ops), 15)
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ["a", "b", "a blank value", ""])

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)
        singular_action = schema.objs.Element._build_cmd_action()
        singular_action.setup_operations(dest_ops, ["attr=a"], prefix_keys=[_ELEMENT_APPEND_KEY])
        singular_action.setup_operations(dest_ops, ["prop=b"], prefix_keys=[-1])
        dest_ops.apply(v, "objs")
        self.assertEqual(v.objs, [{"attr": "a", "prop": "b"}])

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)
        action = schema.user_assigned._build_cmd_action()
        action.setup_operations(dest_ops, [])
        dest_ops.apply(v, "user_assigned")
        self.assertEqual(v.user_assigned, ["1", "2"])

        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "user_assigned")
        self.assertEqual(v.user_assigned, ["1", "2"])

    def test_aaz_dict_arg(self):
        from azure.cli.core.aaz._arg import AAZDictArg, AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.tags = AAZDictArg(
            options=["--tags", "-t"],
            blank={"ab": '1', "bc": '2'},
        )
        schema.tags.Element = AAZStrArg(
            nullable=True,
            blank="a blank value"
        )

        self.assertFalse(has_value(v.tags))

        arg = schema.tags.to_cmd_arg("tags")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        # null value
        action.setup_operations(dest_ops, ["a=null", "b=None"])
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"a": None, "b": 'None'})

        action.setup_operations(dest_ops, ["b=6", "c="])
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"a": None, "b": "6", "c": "a blank value"})

        action.setup_operations(dest_ops, ["{ab:1,bc:2,cd:'null'}"])
        self.assertEqual(len(dest_ops._ops), 5)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"ab": '1', "bc": '2', 'cd': 'null'})

        action.setup_operations(dest_ops, ["{}"])
        self.assertEqual(len(dest_ops._ops), 6)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {})

        # blank value
        action.setup_operations(dest_ops, [])
        self.assertEqual(len(dest_ops._ops), 7)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"ab": '1', "bc": '2'})

        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 8)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"ab": '1', "bc": '2'})

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, ["=1"])

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, ["null"])

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, ["null"])

        with self.assertRaises(aazerror.AAZInvalidShorthandSyntaxError):
            action.setup_operations(dest_ops, ["{c:}"])

    def test_aaz_freeform_dict_arg(self):
        from azure.cli.core.aaz._arg import AAZFreeFormDictArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.tags = AAZFreeFormDictArg(
            options=["--tags", "-t"],
            nullable=True,
            blank={"blank": True}
        )

        self.assertFalse(has_value(v.tags))

        arg = schema.tags.to_cmd_arg("tags")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        # null value
        action.setup_operations(dest_ops, "null")
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, None)

        # empty dict
        action.setup_operations(dest_ops, "{}")
        self.assertEqual(len(dest_ops._ops), 2)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {})

        # freeform dict
        action.setup_operations(dest_ops, '{"a": 1, "b": null, "c": false, "d": "string", "e": [1, "str", null]}')
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"a": 1, "b": None, "c": False, "d": "string", "e": [1, "str", None]})

        # blank value
        action.setup_operations(dest_ops, None)
        self.assertEqual(len(dest_ops._ops), 4)
        dest_ops.apply(v, "tags")
        self.assertEqual(v.tags, {"blank": True})

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "'null'")

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "'123'")

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "123")

        with self.assertRaises(aazerror.AAZInvalidValueError):
            action.setup_operations(dest_ops, "[1, 2, 3]")

    def test_aaz_object_arg(self):
        from azure.cli.core.aaz._arg import AAZDictArg, AAZListArg, AAZObjectArg, AAZIntArg, AAZBoolArg, AAZFloatArg, \
            AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
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
        schema.properties.identities = AAZDictArg(
            options=["identities"],
        )
        schema.properties.identities.Element = AAZObjectArg(
            blank={},
            nullable=True,
        )
        schema.properties.tags.Element = AAZIntArg(
            blank="0"
        )
        schema.properties.vnets = AAZListArg(
            options=["vnets"],
            singular_options=["vnet"],
            nullable=True
        )
        schema.properties.vnets.Element = AAZObjectArg()
        schema.properties.vnets.Element.id = AAZStrArg(
            options=["id"],
            blank="666"
        )

        schema.properties.new_i_pv6 = AAZStrArg(
            options=["new_ipv6"],
        )

        schema.properties.pt = AAZFloatArg(
            options=["pt"],
            nullable=True,
            blank="0.1"
        )

        self.assertFalse(has_value(v.properties.identities))
        self.assertFalse(has_value(v.properties.vnets))
        self.assertFalse(has_value(v.properties.pt))
        self.assertFalse(has_value(v.properties))

        arg = schema.properties.to_cmd_arg("properties")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, ["{enable:false,tags:{a:1,3:2},vnets:[{id:/123}],pt:12.123}"])
        self.assertEqual(len(dest_ops._ops), 1)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, {
            "enable": False,
            "tags": {
                "a": 1,
                "3": 2,
            },
            "vnets": [
                {"id": "/123"},
            ],
            "pt": 12.123
        })

        action.setup_operations(dest_ops, ["vnet.id=223", "vnet={id:456}"])
        self.assertEqual(len(dest_ops._ops), 3)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties.to_serialized_data(), {
            "enable": False,
            "tags": {
                "a": 1,
                "3": 2,
            },
            "vnets": [
                {"id": "/123"},
                {"id": "223"},
                {"id": "456"}
            ],
            "pt": 12.123
        })

        action.setup_operations(dest_ops, ["pt=", "enable=null", "vnets=[]"])
        self.assertEqual(len(dest_ops._ops), 6)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, {
            "enable": None,
            "tags": {
                "a": 1,
                "3": 2,
            },
            "vnets": [],
            "pt": 0.1
        })

        action.setup_operations(dest_ops, ["{enable:false,pt,tags:{a:1,3:2,c},vnets:[{id}],identities:{a:{},'http://b/c/d/e'}}"])
        self.assertEqual(len(dest_ops._ops), 7)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, {
            "enable": False,
            "tags": {
                "a": 1,
                "3": 2,
                "c": 0,
            },
            "vnets": [
                {"id": "666"},
            ],
            "identities": {
                "a": {},
                "http://b/c/d/e": {},
            },
            "pt": 0.1
        })

        action.setup_operations(dest_ops, ["identities.'http://b.p['/]/c'=", "identities.a=null"])
        self.assertEqual(len(dest_ops._ops), 9)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, {
            "enable": False,
            "tags": {
                "a": 1,
                "3": 2,
                "c": 0,
            },
            "vnets": [
                {"id": "666"},
            ],
            "identities": {
                "a": None,
                "http://b/c/d/e": {},
                "http://b.p[']/c": {},
            },
            "pt": 0.1
        })

        action.setup_operations(dest_ops, ["{}"])
        self.assertEqual(len(dest_ops._ops), 10)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, {})

        action.setup_operations(dest_ops, ["null"])
        self.assertEqual(len(dest_ops._ops), 11)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, None)

        action.setup_operations(dest_ops, ["{enable:True,tags:null,vnets:null,pt:12.123,newIPv6:'00:00:00'}"])
        self.assertEqual(len(dest_ops._ops), 12)
        dest_ops.apply(v, "properties")
        self.assertEqual(v.properties, {
            "enable": True,
            "tags": None,
            "vnets": None,
            "pt": 12.123,
            "new_i_pv6": '00:00:00'
        })

    def test_aaz_has_value_for_buildin(self):
        from azure.cli.core.aaz import has_value, AAZUndefined
        self.assertTrue(has_value(0))
        self.assertTrue(has_value(""))
        self.assertTrue(has_value(False))
        self.assertTrue(has_value(None))

        self.assertFalse(has_value(AAZUndefined))

    def test_aaz_registered_arg(self):
        from azure.cli.core.aaz._arg import AAZStrArg, AAZObjectArg, AAZBoolArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
        from azure.cli.core.aaz.exceptions import AAZUnregisteredArg
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
        self.assertTrue(schema.work_day._registered)

        arg = schema.work_day.to_cmd_arg("work_day")

        schema.work_day._registered = False
        with self.assertRaises(AAZUnregisteredArg):
            schema.work_day.to_cmd_arg("work_day")

        schema.properties = AAZObjectArg(
            options=["--prop", "-p"],
            nullable=True
        )

        schema.properties.enable = AAZBoolArg(
            options=["enable"],
            nullable=True,
        )

        self.assertTrue(schema.properties._registered)
        arg = schema.properties.to_cmd_arg("properties")

        schema.properties._registered = False
        with self.assertRaises(AAZUnregisteredArg):
            schema.properties.to_cmd_arg("properties")

    def test_aaz_configured_default_arg(self):
        from azure.cli.core.aaz._arg import AAZResourceGroupNameArg, AAZResourceLocationArg, AAZStrArg, AAZIntArg,\
            AAZArgumentsSchema
        schema = AAZArgumentsSchema()
        v = schema()

        schema.resource_group = AAZResourceGroupNameArg()
        schema.location = AAZResourceLocationArg()
        schema.name = AAZStrArg(configured_default="specialname")
        schema.count = AAZIntArg(configured_default="specialcount")
        arg = schema.resource_group.to_cmd_arg("resource_group")
        self.assertEqual(arg.type.settings['configured_default'], 'group')
        arg = schema.location.to_cmd_arg("location")
        self.assertEqual(arg.type.settings['configured_default'], 'location')
        arg = schema.name.to_cmd_arg("name")
        self.assertEqual(arg.type.settings['configured_default'], 'specialname')
        arg = schema.count.to_cmd_arg("count")
        self.assertEqual(arg.type.settings['configured_default'], 'specialcount')


class TestAAZArgUtils(unittest.TestCase):

    def test_assign_aaz_list_arg(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        from azure.cli.core.aaz._arg import AAZListArg, AAZStrArg, AAZObjectArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value, AAZUndefined
        schema = AAZArgumentsSchema()
        v = schema()

        schema.names = AAZListArg(
            options=["--names", "--ns"],
            singular_options=["--name", "-n"],
            nullable=True
        )
        schema.names.Element = AAZStrArg(
            nullable=True,
            blank="a blank value"
        )
        schema.items = AAZListArg(
            nullable=True,
        )
        schema.items.Element = AAZObjectArg(
            nullable=True,
        )
        schema.items.Element.name = AAZStrArg()

        # AAZUndefined
        self.assertFalse(has_value(v.names))
        v.items = assign_aaz_list_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertFalse(has_value(v.items))

        v.items = [{"name": "1"}]
        v.items = assign_aaz_list_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, [{"name": "1"}])

        arg = schema.names.to_cmd_arg("names")
        action = arg.type.settings["action"]

        # null value
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["null"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, None)

        v.items = assign_aaz_list_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, None)

        # null element value
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["[0]=null"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, [None, ])

        v.items = assign_aaz_list_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, [None, ])

        # element
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["1", "2", "3"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, ['1', '2', '3'])
        self.assertFalse(v.names._is_patch)

        v.items = assign_aaz_list_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, [{"name": '1'}, {"name": '2'}, {"name": "3"}])
        self.assertFalse(v.items._is_patch)

        # patch element
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["[3]=n5"])
        dest_ops.apply(v, "names")
        self.assertTrue(v.names._is_patch)
        self.assertEqual(len(v.names), 4)
        self.assertFalse(has_value(v.items[0]))
        self.assertFalse(has_value(v.items[1]))
        self.assertFalse(has_value(v.items[2]))
        self.assertEqual(v.names[3], 'n5')
        v.items = assign_aaz_list_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertTrue(v.items._is_patch)
        self.assertEqual(len(v.items), 4)
        self.assertFalse(has_value(v.items[0]))
        self.assertFalse(has_value(v.items[1]))
        self.assertFalse(has_value(v.items[2]))
        self.assertEqual(v.items[3], {"name": 'n5'})

    def test_assign_aaz_dict_arg(self):
        from azure.cli.core.aaz.utils import assign_aaz_dict_arg
        from azure.cli.core.aaz._arg import AAZDictArg, AAZStrArg, AAZObjectArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value, AAZUndefined
        schema = AAZArgumentsSchema()
        v = schema()

        schema.names = AAZDictArg(
            options=["--names", "--ns"],
            nullable=True
        )
        schema.names.Element = AAZStrArg(
            nullable=True,
            blank="a blank value"
        )
        schema.items = AAZDictArg(
            nullable=True,
        )
        schema.items.Element = AAZObjectArg(
            nullable=True,
        )
        schema.items.Element.name = AAZStrArg()

        # AAZUndefined
        self.assertFalse(has_value(v.names))
        v.items = assign_aaz_dict_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertFalse(has_value(v.items))

        v.items = {"a": {"name": "1"}}
        v.items = assign_aaz_dict_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, {"a": {"name": "1"}})

        arg = schema.names.to_cmd_arg("names")
        action = arg.type.settings["action"]

        # null value
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["null"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, None)

        v.items = assign_aaz_dict_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, None)

        # null element value
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["a=null"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, {'a': None})

        v.items = assign_aaz_dict_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertEqual(v.items, {'a': None})

        # element
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["{a:a1,b:b2}"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, {'a': 'a1', 'b': 'b2'})
        self.assertFalse(v.names._is_patch)

        v.items = assign_aaz_dict_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertFalse(v.items._is_patch)
        self.assertEqual(v.items, {'a': {"name": 'a1'}, 'b': {"name": 'b2'}})

        # element with patch
        v = schema()
        dest_ops = AAZArgActionOperations()

        action.setup_operations(dest_ops, ["a=1", "b=2", "c=3"])
        dest_ops.apply(v, "names")
        self.assertEqual(v.names, {'a': '1', 'b': '2', 'c': '3'})
        self.assertTrue(v.names._is_patch)

        v.items = assign_aaz_dict_arg(v.items, v.names, element_transformer=lambda _, name: {"name": name})
        self.assertTrue(v.items._is_patch)
        self.assertEqual(v.items, {'a': {"name": '1'}, 'b': {"name": '2'}, 'c': {"name": "3"}})


class TestAazArgCompleter(unittest.TestCase):
    from azure.cli.core.decorators import Completer

    @staticmethod
    @Completer
    def custom_completer(cmd, prefix, namespace):
        return ['a', 'b']

    def test_custom_completer(self):
        from azure.cli.core.aaz._arg import AAZStrArg, AAZArgumentsSchema, AAZUnregisteredArg

        schema = AAZArgumentsSchema()
        v = schema()

        schema.foo = AAZStrArg(
            options=['foo'],
            nullable=True,
            completer=self.custom_completer
        )
        args = {}
        for name, field in schema._fields.items():
            # generate command arguments from argument schema.
            try:
                args[name] = field.to_cmd_arg(name)
            except AAZUnregisteredArg:
                continue
        self.assertEqual(args['foo'].completer, schema.foo._completer)
        self.assertEqual(args['foo'].completer, self.custom_completer)

    def test_completer_override(self):
        from azure.cli.core.aaz._arg import (AAZResourceLocationArg, AAZArgumentsSchema, AAZUnregisteredArg,
                                             AAZSubscriptionIdArg)
        from azure.cli.core.commands.parameters import get_location_completion_list
        from azure.cli.core._completers import get_subscription_id_list

        schema = AAZArgumentsSchema()
        v = schema()

        schema.foo = AAZResourceLocationArg(
            options=['foo'],
            completer=self.custom_completer
        )
        schema.bar = AAZResourceLocationArg(
            options=['bar']
        )
        schema.sub = AAZSubscriptionIdArg(
            options=["--subscription-id"],
            help="subscription id",
            required=True,
            id_part="subscription")
        self.assertEqual(schema.foo._completer, self.custom_completer)
        self.assertEqual(schema.bar._completer, get_location_completion_list)
        self.assertEqual(schema.sub._completer, get_subscription_id_list)

        args = {}
        for name, field in schema._fields.items():
            # generate command arguments from argument schema.
            try:
                args[name] = field.to_cmd_arg(name)
            except AAZUnregisteredArg:
                continue
        self.assertEqual(args['foo'].completer, self.custom_completer)
        self.assertEqual(args['bar'].completer, get_location_completion_list)
        self.assertEqual(args['sub'].completer, get_subscription_id_list)
        schema.bar._completer = self.custom_completer
        new_arg = schema.bar.to_cmd_arg('bar')
        self.assertEqual(new_arg.completer, self.custom_completer)
