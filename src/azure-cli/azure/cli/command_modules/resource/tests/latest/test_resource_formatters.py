# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.profiles import ResourceType
from azure.cli.core.mock import DummyCli
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand

from azure.cli.command_modules.resource._color import Color, ColoredStringBuilder
from azure.cli.command_modules.resource._formatters import format_json, format_what_if_operation_result


cli_ctx = DummyCli()
loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
cmd = AzCliCommand(loader, "test", None, resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

WhatIfOperationResult, WhatIfChange, WhatIfPropertyChange, ChangeType, PropertyChangeType = cmd.get_models(
    "WhatIfOperationResult", "WhatIfChange", "WhatIfPropertyChange", "ChangeType", "PropertyChangeType",
)


class TestFormatJson(unittest.TestCase):
    _colon = ColoredStringBuilder().append(":", Color.RESET).build()
    _left_square_bracket = ColoredStringBuilder().append("[", Color.RESET).build()
    _right_square_bracket = ColoredStringBuilder().append("]", Color.RESET).build()

    def test_leaf(self):
        test_data = (
            ("null", None),
            ("true", True),
            ("false", False),
            ("42", 42),
            ("42.12345", 42.12345),
            ('"foo"', "foo"),
            ("{}", {}),
            ("[]", []),
        )
        for expected, value in test_data:
            with self.subTest(expected=expected, value=value):
                self.assertEqual(expected, format_json(value))

    def test_non_empty_array(self):
        value = [x for x in range(11)]
        expected = """[
  0:  0
  1:  1
  2:  2
  3:  3
  4:  4
  5:  5
  6:  6
  7:  7
  8:  8
  9:  9
  10: 10
]"""
        expected = expected.replace("[", self._left_square_bracket)
        expected = expected.replace("]", self._right_square_bracket)
        expected = expected.replace(":", self._colon)

        self.assertEqual(expected, format_json(value))

    def test_non_empty_object(self):
        value = {"path": {"to": {"foo": "foo"}}, "longPath": {"to": {"bar": "bar"}}}
        expected = """

  path.to.foo:     "foo"
  longPath.to.bar: "bar"
"""
        expected = expected.replace(":", self._colon)

        self.assertEqual(expected, format_json(value))

    def test_complex_value(self):
        value = {
            "root": {
                "foo": 1234,
                "bar": [True, None, {"nestedString": "value", "nestedArray": [92747, "test"]}, [False]],
                "foobar": "foobar",
            }
        }

        expected = """

  root.foo:    1234
  root.bar: [
    0: true
    1: null
    2:

      nestedString: "value"
      nestedArray: [
        0: 92747
        1: "test"
      ]

    3: [
      0: false
    ]
  ]
  root.foobar: "foobar"
"""
        expected = expected.replace("[", self._left_square_bracket)
        expected = expected.replace("]", self._right_square_bracket)
        expected = expected.replace(":", self._colon)

        self.assertEqual(expected, format_json(value))


class TestFormatWhatIfOperationResult(unittest.TestCase):
    def test_change_type_legend(self):
        changes = [
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo1",
                change_type=ChangeType.modify,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p2/bar",
                change_type=ChangeType.create,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg2/providers/p1/foo2",
                change_type=ChangeType.modify,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/providers/p3/foobar1",
                change_type=ChangeType.ignore,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg3",
                change_type=ChangeType.modify,
                delta=[
                    WhatIfPropertyChange(
                        path="path.to.array.change",
                        property_change_type=PropertyChangeType.array,
                        children=[
                            WhatIfPropertyChange(
                                path="1", property_change_type=PropertyChangeType.delete, before=12345
                            ),
                        ],
                    ),
                ],
            ),
        ]

        expected = f"""Resource and property changes are indicated with these symbols:
  {Color.ORANGE}-{Color.RESET} Delete
  {Color.GREEN}+{Color.RESET} Create
  {Color.PURPLE}~{Color.RESET} Modify
  {Color.GRAY}*{Color.RESET} Ignore
"""

        self.assertIn(expected, format_what_if_operation_result(WhatIfOperationResult(changes=changes)))

    def test_resource_changes_stats(self):
        changes = [
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo1",
                change_type=ChangeType.create,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p2/bar",
                change_type=ChangeType.create,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg2/providers/p1/foo2",
                change_type=ChangeType.modify,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/providers/p3/foobar1",
                change_type=ChangeType.ignore,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg3",
                change_type=ChangeType.delete,
            ),
        ]

        expected = "\nResource changes: 1 to delete, 2 to create, 1 to modify, 1 to ignore."
        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes))

        self.assertTrue(result.endswith(expected))

    def test_group_resources_changes_by_sorted_scope(self):
        changes = [
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/RG1/providers/p1/foo1",
                change_type=ChangeType.create,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p2/bar",
                change_type=ChangeType.create,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg2/providers/p1/foo2",
                change_type=ChangeType.modify,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/providers/p3/foobar1",
                change_type=ChangeType.ignore,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/providers/p3/foobar2",
                change_type=ChangeType.delete,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg3",
                change_type=ChangeType.delete,
            ),
        ]

        expected = f"""
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/RG1
{Color.GREEN}
  + p1/foo1
  + p2/bar
{Color.RESET}
Scope: /subscriptions/00000000-0000-0000-0000-000000000002
{Color.ORANGE}
  - p3/foobar2
  - resourceGroups/rg3{Color.RESET}{Color.GRAY}
  * p3/foobar1
{Color.RESET}
Scope: /subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg2
{Color.PURPLE}
  ~ p1/foo2
{Color.RESET}"""

        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes))

        self.assertIn(expected, result)

    def test_sort_resource_ids_within_a_scope(self):
        changes = [
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo",
                change_type=ChangeType.ignore,
            ),
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p2/foo",
                change_type=ChangeType.create,
            ),
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p3/foo",
                change_type=ChangeType.no_change,
            ),
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p4/foo",
                change_type=ChangeType.deploy,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p5/foo",
                change_type=ChangeType.delete,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p6/foo",
                change_type=ChangeType.delete,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p7/foo",
                change_type=ChangeType.delete,
            ),
            WhatIfChange(
                resource_id="/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p8/foo",
                change_type=ChangeType.unsupported,
            ),
        ]

        expected = f"""
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1
{Color.ORANGE}
  - p5/foo
  - p6/foo
  - p7/foo{Color.RESET}{Color.GREEN}
  + p2/foo{Color.RESET}{Color.BLUE}
  ! p4/foo{Color.RESET}{Color.RESET}
  = p3/foo{Color.RESET}{Color.GRAY}
  x p8/foo{Color.RESET}{Color.GRAY}
  * p1/foo
{Color.RESET}"""
        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes))

        self.assertIn(expected, result)

    def test_property_create(self):
        changes = [
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo",
                change_type=ChangeType.create,
                after={
                    "numberValue": 1.2,
                    "booleanValue": True,
                    "stringValue": "The quick brown fox jumps over the lazy dog.",
                },
            ),
        ]

        expected = f"""
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1
{Color.GREEN}
  + p1/foo

      numberValue{Color.RESET}:{Color.GREEN}  1.2
      booleanValue{Color.RESET}:{Color.GREEN} true
      stringValue{Color.RESET}:{Color.GREEN}  "The quick brown fox jumps over the lazy dog."
{Color.RESET}"""

        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes))

        self.assertIn(expected, result)

    def test_property_delete(self):
        changes = [
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo",
                change_type=ChangeType.delete,
                before={
                    "apiVersion": "2020-04-01",
                    "numberValue": 1.2,
                    "booleanValue": True,
                    "stringValue": "The quick brown fox jumps over the lazy dog.",
                },
            ),
        ]

        expected = f"""
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1
{Color.ORANGE}
  - p1/foo{Color.RESET} [2020-04-01]{Color.ORANGE}

      apiVersion{Color.RESET}:{Color.ORANGE}   "2020-04-01"
      numberValue{Color.RESET}:{Color.ORANGE}  1.2
      booleanValue{Color.RESET}:{Color.ORANGE} true
      stringValue{Color.RESET}:{Color.ORANGE}  "The quick brown fox jumps over the lazy dog."
{Color.RESET}"""

        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes))

        self.assertIn(expected, result)

    def test_property_modify(self):
        changes = [
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo",
                change_type=ChangeType.modify,
                delta=[
                    WhatIfPropertyChange(
                        path="path.a.to.change",
                        property_change_type=PropertyChangeType.modify,
                        before="foo",
                        after="bar",
                    ),
                    WhatIfPropertyChange(
                        path="path.a.to.change2",
                        property_change_type=PropertyChangeType.modify,
                        before={
                            "tag1": "value"
                        },
                        after={
                            "tag2": "value"
                        },
                    ),
                    WhatIfPropertyChange(
                        path="path.a.to.change3",
                        property_change_type=PropertyChangeType.no_effect,
                        after=12345,
                    ),
                    WhatIfPropertyChange(
                        path="path.b.to.nested.change",
                        property_change_type=PropertyChangeType.array,
                        children=[
                            WhatIfPropertyChange(
                                path="4",
                                property_change_type=PropertyChangeType.modify,
                                children=[
                                    WhatIfPropertyChange(
                                        path="foo.bar",
                                        property_change_type=PropertyChangeType.modify,
                                        before=True,
                                        after=False,
                                    ),
                                    WhatIfPropertyChange(
                                        path="baz",
                                        property_change_type=PropertyChangeType.create,
                                        after=["element1", "element2"],
                                    ),
                                ],
                            ),
                            WhatIfPropertyChange(
                                path="5", property_change_type=PropertyChangeType.delete, before=12345
                            ),
                        ],
                    ),
                ],
            ),
        ]

        expected = f"""
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1
{Color.PURPLE}
  ~ p1/foo{Color.RESET}
    {Color.PURPLE}~{Color.RESET} path.a.to.change{Color.RESET}:{Color.RESET}  {Color.ORANGE}"foo"{Color.RESET} => {Color.GREEN}"bar"{Color.RESET}
    {Color.PURPLE}~{Color.RESET} path.a.to.change2{Color.RESET}:{Color.RESET}{Color.ORANGE}

        tag1{Color.RESET}:{Color.ORANGE} "value"
{Color.RESET}
      =>{Color.GREEN}

        tag2{Color.RESET}:{Color.GREEN} "value"
{Color.RESET}
    {Color.PURPLE}~{Color.RESET} path.b.to.nested.change{Color.RESET}:{Color.RESET} [
      {Color.PURPLE}~{Color.RESET} 4{Color.RESET}:{Color.RESET}

        {Color.GREEN}+{Color.RESET} baz{Color.RESET}:{Color.RESET} {Color.GREEN}{Color.RESET}[{Color.GREEN}
            0{Color.RESET}:{Color.GREEN} "element1"
            1{Color.RESET}:{Color.GREEN} "element2"
          {Color.RESET}]{Color.GREEN}{Color.RESET}
        {Color.PURPLE}~{Color.RESET} foo.bar{Color.RESET}:{Color.RESET} {Color.ORANGE}true{Color.RESET} => {Color.GREEN}false{Color.RESET}

      {Color.ORANGE}-{Color.RESET} 5{Color.RESET}:{Color.RESET} {Color.ORANGE}12345{Color.RESET}
      ]
    {Color.GRAY}x{Color.RESET} path.a.to.change3{Color.RESET}:{Color.RESET} {Color.GRAY}12345{Color.RESET}
{Color.PURPLE}{Color.RESET}"""

        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes))

        self.assertIn(expected, result)

    def test_json_alignment(self):
        changes = [
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo",
                change_type=ChangeType.delete,
                before={
                    "apiVersion": "2020-04-01",
                    "numberValue": 1.2,
                    "booleanValue": True,
                    "stringValue": "The quick brown fox jumps over the lazy dog.",
                    "emptyArray": [],
                    "emptyObject": {},
                    "arrayContaingValues": ["foo", "bar"],
                },
            ),
        ]

        expected = """
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1

  - p1/foo [2020-04-01]

      apiVersion:   "2020-04-01"
      numberValue:  1.2
      booleanValue: true
      stringValue:  "The quick brown fox jumps over the lazy dog."
      emptyArray:   []
      emptyObject:  {}
      arrayContaingValues: [
        0: "foo"
        1: "bar"
      ]
"""

        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes), False)

        self.assertIn(expected, result)

    def test_property_changes_alignment(self):
        changes = [
            WhatIfChange(
                resource_id="subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/p1/foo",
                change_type=ChangeType.modify,
                delta=[
                    WhatIfPropertyChange(path="path", property_change_type=PropertyChangeType.delete, before={},),
                    WhatIfPropertyChange(path="long.path", property_change_type=PropertyChangeType.create, after=[],),
                    WhatIfPropertyChange(
                        path="long.nested.path",
                        property_change_type=PropertyChangeType.array,
                        children=[
                            WhatIfPropertyChange(
                                path="5", property_change_type=PropertyChangeType.delete, before=12345
                            ),
                        ],
                    ),
                ],
            ),
        ]

        expected = """
Scope: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1

  ~ p1/foo
    - path:      {}
    + long.path: []
    ~ long.nested.path: [
      - 5: 12345
      ]
"""

        result = format_what_if_operation_result(WhatIfOperationResult(changes=changes), False)

        self.assertIn(expected, result)
