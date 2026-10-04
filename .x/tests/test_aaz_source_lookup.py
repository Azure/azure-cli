# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Bounded source linkage regression tests without network access."""

import ast
from pathlib import Path
from unittest.mock import Mock

import pytest


def lookup(response):
    path = Path(__file__).parents[1] / "tools/fixer/azure_cli/aaz.py"
    tree = ast.parse(path.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "find_promoted_aaz_source_pr")
    request = Mock(side_effect=response) if isinstance(response, list) else Mock(return_value=response)
    namespace = {
        "github_get": request, "AAZ_SOURCE_REPOSITORY": "Azure/aaz",
        "AAZ_SOURCE_FORK": "a0x1ab/aaz",
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[function.name], request


def pull(number, state="open", merged=False):
    return {
        "number": number, "state": state, "merged_at": "timestamp" if merged else None,
        "head": {"ref": "agent-issue-12-change", "repo": {"full_name": "a0x1ab/aaz"}},
    }


def test_source_after_first_page_is_retained():
    function, request = lookup([
        {"data": [{"head": {}}] * 100, "truncated": True},
        {"data": [pull(101)], "truncated": False},
    ])
    assert function(12)["number"] == 101
    assert request.call_count == 2
    assert request.call_args.kwargs["params"]["page"] == 2


def test_closed_unmerged_source_is_not_linked():
    function, _ = lookup({"data": [pull(1, "closed")], "truncated": False})
    assert function(12) is None


def test_merged_source_remains_linked():
    function, _ = lookup({"data": [pull(1, "closed", True)], "truncated": False})
    assert function(12)["number"] == 1


def test_incomplete_search_does_not_claim_no_source():
    function, request = lookup({"data": [], "truncated": True})
    with pytest.raises(RuntimeError, match="incomplete"):
        function(12)
    assert request.call_count == 10


def test_matching_source_in_truncated_search_is_usable():
    function, _ = lookup({"data": [pull(1)], "truncated": True})
    assert function(12)["number"] == 1
