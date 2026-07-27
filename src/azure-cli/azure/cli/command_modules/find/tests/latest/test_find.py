# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from unittest import mock
from io import StringIO

from azure.cli.command_modules.find.custom import (
    MCPClient, search_mslearn, format_results, process_query, _extract_summary,
    _is_cli_command_relevant, _extract_query_command, _filter_results,
    _get_query_keywords, _has_keyword_overlap, _stem, _matches_keywords,
    _extract_command, _build_docs_query, _prefer_cli_docs, _dedupe_key,
    MAX_DOC_RESULTS, MAX_CODE_RESULTS, MAX_SUMMARY_LENGTH, CONTINUATION_MARKER
)


def _make_sse_response(result_data, session_id="test-session-id"):
    """Create a mock requests.Response with SSE-formatted MCP response."""
    resp = mock.MagicMock()
    resp.status_code = 200
    resp.headers = {"mcp-session-id": session_id}
    sse_data = json.dumps(result_data)
    resp.text = f"event: message\ndata: {sse_data}\n\n"
    resp.raise_for_status = mock.MagicMock()
    return resp


def _make_init_response(session_id="test-session-id"):
    """Create a mock initialize response."""
    return _make_sse_response({
        "result": {
            "protocolVersion": "2025-03-26",
            "serverInfo": {"name": "Microsoft Learn MCP Server", "version": "1.0.0"},
            "capabilities": {"tools": {"listChanged": True}}
        },
        "id": 1,
        "jsonrpc": "2.0"
    }, session_id)


def _make_notify_response():
    """Create a mock notify response (empty 200)."""
    resp = mock.MagicMock()
    resp.status_code = 200
    resp.raise_for_status = mock.MagicMock()
    return resp


def _make_tool_response(results, request_id=2):
    """Create a mock tool call response."""
    inner_text = json.dumps({"results": results})
    return _make_sse_response({
        "result": {
            "content": [{"type": "text", "text": inner_text}]
        },
        "id": request_id,
        "jsonrpc": "2.0"
    })


SAMPLE_DOC_RESULTS = [
    {
        "title": "az vm delete",
        "content": "### Command\naz vm delete\n\n### Summary\nDelete a virtual machine.\n\n### Optional Parameters\n--name\nName of the VM.",
        "contentUrl": "https://learn.microsoft.com/cli/azure/vm?view=azure-cli-latest"
    },
    {
        "title": "Delete a VM and attached resources",
        "content": "# Delete a VM and attached resources\nYou can change the behavior when you delete a VM.\n\naz vm delete --resource-group myResourceGroup --name myVM",
        "contentUrl": "https://learn.microsoft.com/azure/virtual-machines/delete"
    }
]

SAMPLE_CODE_RESULTS = [
    {
        "description": "Deletes an Azure virtual machine using force deletion.",
        "codeSnippet": "az vm delete \\\n    --resource-group myResourceGroup \\\n    --name myVM \\\n    --force-deletion true",
        "link": "https://learn.microsoft.com/azure/virtual-machines/delete#force-delete",
        "language": "azurecli"
    },
    {
        "description": "Deletes a virtual machine in Azure.",
        "codeSnippet": "az vm delete \\\n --resource-group myResourceGroup \\\n --name myVM",
        "link": "https://learn.microsoft.com/azure/aks/rdp#remove-rdp-access",
        "language": "azurecli"
    }
]


class TestMCPClient(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('requests.post')
    def test_initialize(self, mock_post, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False
        mock_post.return_value = _make_init_response("my-session-123")

        client = MCPClient(client_version="2.60.0")
        result = client.initialize()

        self.assertEqual(client.session_id, "my-session-123")
        self.assertEqual(client._headers["mcp-session-id"], "my-session-123")
        self.assertEqual(result["result"]["serverInfo"]["name"], "Microsoft Learn MCP Server")

        # Verify the POST was made correctly
        call_args = mock_post.call_args
        body = call_args[1]["json"]
        self.assertEqual(body["method"], "initialize")
        self.assertEqual(body["params"]["clientInfo"]["name"], "azure-cli-find")
        self.assertEqual(body["params"]["clientInfo"]["version"], "2.60.0")

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('requests.post')
    def test_notify_initialized(self, mock_post, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False
        mock_post.return_value = _make_notify_response()

        client = MCPClient()
        client.session_id = "test-session"
        client._headers["mcp-session-id"] = "test-session"
        client.notify_initialized()

        call_args = mock_post.call_args
        body = call_args[1]["json"]
        self.assertEqual(body["method"], "notifications/initialized")

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('requests.post')
    def test_call_tool(self, mock_post, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False
        mock_post.return_value = _make_tool_response(SAMPLE_DOC_RESULTS)

        client = MCPClient()
        client.session_id = "test-session"
        result = client.call_tool("microsoft_docs_search", {"query": "az vm delete"})

        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["title"], "az vm delete")

        call_args = mock_post.call_args
        body = call_args[1]["json"]
        self.assertEqual(body["method"], "tools/call")
        self.assertEqual(body["params"]["name"], "microsoft_docs_search")

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    def test_telemetry_context_enabled(self, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = True
        mock_telemetry._session.correlation_id = "corr-123"
        mock_telemetry._session.event_id = "evt-456"
        mock_telemetry._get_azure_subscription_id.return_value = "sub-789"

        client = MCPClient(client_version="2.60.0")

        # Hashed installation id is always sent as a header for rate limiting.
        self.assertIn("X-UserId", client._headers)
        # Contextual values are bundled into the context object when consented.
        self.assertEqual(client._context["versionNumber"], "2.60.0")
        self.assertEqual(client._context["correlationId"], "corr-123")
        self.assertEqual(client._context["eventId"], "evt-456")
        self.assertEqual(client._context["subscriptionId"], "sub-789")
        self.assertEqual(json.loads(client._params["context"]), client._context)

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    def test_telemetry_context_disabled(self, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False

        client = MCPClient(client_version="2.60.0")

        self.assertIn("X-UserId", client._headers)
        # Without consent only the version number is sent.
        self.assertEqual(client._context["versionNumber"], "2.60.0")
        self.assertNotIn("correlationId", client._context)
        self.assertNotIn("eventId", client._context)
        self.assertNotIn("subscriptionId", client._context)

    def test_parse_sse(self):
        sse_text = 'event: message\ndata: {"id": 1, "result": "ok"}\n\n'
        result = MCPClient._parse_sse(sse_text)
        self.assertEqual(result["result"], "ok")

    def test_parse_sse_empty(self):
        result = MCPClient._parse_sse("no data here")
        self.assertEqual(result, {})


class TestExtractSummary(unittest.TestCase):

    def test_extract_summary_from_markdown(self):
        content = "### Command\naz vm delete\n\n### Summary\nDelete a virtual machine.\n\n### Parameters\n--name"
        summary = _extract_summary(content)
        self.assertEqual(summary, "Delete a virtual machine.")

    def test_extract_summary_no_summary_section(self):
        content = "# Delete a VM\nYou can change the behavior when deleting a VM."
        summary = _extract_summary(content)
        self.assertEqual(summary, "You can change the behavior when deleting a VM.")

    def test_extract_summary_empty(self):
        self.assertEqual(_extract_summary(""), "")
        self.assertEqual(_extract_summary(None), "")

    def test_extract_summary_truncates(self):
        long_content = "A" * 200
        summary = _extract_summary(long_content)
        self.assertTrue(summary.endswith(CONTINUATION_MARKER))
        self.assertEqual(len(summary), MAX_SUMMARY_LENGTH + len(CONTINUATION_MARKER))

    def test_extract_summary_marks_truncated_sentence(self):
        content = "Create a VM with the Azure CLI. " + ("word " * 60)
        summary = _extract_summary(content)
        self.assertTrue(summary.startswith("Create a VM with the Azure CLI."))
        self.assertTrue(summary.endswith(CONTINUATION_MARKER))

    def test_extract_summary_not_truncated_has_no_marker(self):
        self.assertNotIn(CONTINUATION_MARKER, _extract_summary("A short summary."))

    def test_extract_summary_strips_markdown_links(self):
        content = "# Title\n[New-AZVM](https://learn.microsoft.com/powershell) creates the resources you need."
        self.assertEqual(_extract_summary(content),
                         "New-AZVM creates the resources you need.")

    def test_extract_summary_skips_fragment_lines(self):
        content = "# Title\nIf you plan to use Cloud Shell:\nCloud Shell is an interactive shell that you run in your browser."
        self.assertEqual(_extract_summary(content),
                         "Cloud Shell is an interactive shell that you run in your browser.")


class TestRelevanceFiltering(unittest.TestCase):

    def test_extract_query_command_with_az_prefix(self):
        self.assertEqual(_extract_query_command("az vm create"), "az vm create")
        self.assertEqual(_extract_query_command("az storage blob"), "az storage blob")

    def test_extract_query_command_without_az_prefix(self):
        self.assertEqual(_extract_query_command("vm create"), "az vm create")
        self.assertEqual(_extract_query_command("vm"), "az vm")

    def test_extract_query_command_non_cli(self):
        # Free-text queries get 'az' prepended but won't match real CLI groups,
        # so filtering still works correctly (non-matching titles pass through)
        result = _extract_query_command("deploy arm template")
        self.assertEqual(result, "az deploy arm template")

    def test_is_relevant_exact_match(self):
        self.assertTrue(_is_cli_command_relevant("az vm create", "az vm create"))

    def test_is_relevant_parent_group(self):
        self.assertTrue(_is_cli_command_relevant("az vm", "az vm create"))

    def test_is_relevant_subcommand(self):
        self.assertTrue(_is_cli_command_relevant("az vm run-command create", "az vm create"))

    def test_is_relevant_different_group(self):
        self.assertFalse(_is_cli_command_relevant("az lab vm create", "az vm create"))
        self.assertFalse(_is_cli_command_relevant("az connectedvmware vm create", "az vm create"))
        self.assertFalse(_is_cli_command_relevant("az scvmm vm create", "az vm create"))
        self.assertFalse(_is_cli_command_relevant("az sql vm create", "az vm create"))
        self.assertFalse(_is_cli_command_relevant("az networkcloud virtualmachine create", "az vm create"))

    def test_is_relevant_non_cli_title(self):
        # Non-CLI titles (docs, tutorials) are always relevant
        self.assertTrue(_is_cli_command_relevant("Create a virtual machine", "az vm create"))
        self.assertTrue(_is_cli_command_relevant("Delete a VM and attached resources", "az vm delete"))

    def test_filter_results(self):
        results = [
            {"title": "az vm create", "content": "Create VM", "contentUrl": "url1"},
            {"title": "az lab vm create", "content": "Lab VM", "contentUrl": "url2"},
            {"title": "az connectedvmware vm create", "content": "Connected VM", "contentUrl": "url3"},
            {"title": "Create a virtual machine", "content": "Tutorial about VM creation", "contentUrl": "url4"},
        ]
        filtered = _filter_results(results, "az vm create")
        titles = [r["title"] for r in filtered]
        self.assertIn("az vm create", titles)
        self.assertIn("Create a virtual machine", titles)
        self.assertNotIn("az lab vm create", titles)
        self.assertNotIn("az connectedvmware vm create", titles)

    def test_filter_results_gibberish_query(self):
        """Gibberish queries should return no results when nothing matches."""
        results = [
            {"title": "Albanian Keyboard", "content": "KLID: 0000041C", "contentUrl": "url1"},
            {"title": "ADLaM Keyboard", "content": "KLID: 00140C00", "contentUrl": "url2"},
            {"title": "!asd", "content": "debugger extension", "contentUrl": "url3"},
        ]
        filtered = _filter_results(results, "alskdn1k2lenasd")
        self.assertEqual(len(filtered), 0)

    def test_get_query_keywords(self):
        # 'az' is dropped, short-but-meaningful terms like 'vm' are kept
        self.assertEqual(_get_query_keywords("az vm create"), {"vm", "create"})
        self.assertEqual(_get_query_keywords("az storage blob list"), {"storage", "blob", "list"})
        self.assertEqual(_get_query_keywords("deploy arm template"), {"deploy", "arm", "template"})

    def test_get_query_keywords_drops_filler_words(self):
        # Regression: natural-language queries must keep their subject
        self.assertEqual(_get_query_keywords("what is vm"), {"vm"})
        self.assertEqual(_get_query_keywords("how do i create a vm"), {"vm", "create"})

    def test_has_keyword_overlap_match(self):
        result = {"title": "az vm create", "content": "Create a virtual machine"}
        self.assertTrue(_has_keyword_overlap(result, {"create"}))

    def test_has_keyword_overlap_no_match(self):
        result = {"title": "Albanian Keyboard", "content": "KLID code"}
        self.assertFalse(_has_keyword_overlap(result, {"alskdn1k2lenasd"}))

    def test_stem_verb_variants_collapse(self):
        # Inflected verb forms should collapse to the same stem
        self.assertEqual(_stem("creating"), _stem("create"))
        self.assertEqual(_stem("creates"), _stem("create"))
        self.assertEqual(_stem("created"), _stem("create"))
        self.assertEqual(_stem("deleting"), _stem("delete"))

    def test_matches_keywords_morphological_variant(self):
        # 'creating' in the query should match 'create' in the sample text
        self.assertTrue(_matches_keywords("az vm create --name myvm", {"creating"}))
        self.assertTrue(_matches_keywords("az vm delete --name myvm", {"deleting"}))

    def test_matches_keywords_no_match(self):
        self.assertFalse(_matches_keywords("az vm create", {"storage"}))

    def test_has_keyword_overlap_morphological_variant(self):
        # Regression: 'creating a vm' should still surface 'az vm create' results
        result = {"title": "az vm create", "content": "Create a virtual machine"}
        self.assertTrue(_has_keyword_overlap(result, _get_query_keywords("creating a vm")))


class TestCliScoping(unittest.TestCase):

    def test_build_docs_query_appends_hints(self):
        query = _build_docs_query("create a vm")
        self.assertTrue(query.startswith("create a vm"))
        self.assertIn("Azure CLI", query)

    def test_build_docs_query_skips_existing_hint(self):
        self.assertEqual(_build_docs_query("azure cli vm create").count("Azure CLI"), 0)

    def test_prefer_cli_docs_drops_non_cli(self):
        results = [
            {"title": "Create a VM in the portal", "content": "Select Create.", "contentUrl": "https://x/portal"},
            {"title": "az vm create", "content": "Create a VM.", "contentUrl": "https://learn.microsoft.com/cli/azure/vm"},
        ]
        kept = _prefer_cli_docs(results)
        self.assertEqual([r["title"] for r in kept], ["az vm create"])

    def test_prefer_cli_docs_ranks_reference_first(self):
        results = [
            {"title": "Tutorial", "content": "Run:\naz vm create --name myVM", "contentUrl": "https://x/tutorial"},
            {"title": "az vm create", "content": "Create a VM.", "contentUrl": "https://learn.microsoft.com/cli/azure/vm"},
        ]
        self.assertEqual([r["title"] for r in _prefer_cli_docs(results)], ["az vm create", "Tutorial"])

    def test_prefer_cli_docs_falls_back_when_none_match(self):
        results = [{"title": "Portal", "content": "Select Create.", "contentUrl": "https://x/portal"}]
        self.assertEqual(_prefer_cli_docs(results), results)


class TestExtractCommand(unittest.TestCase):

    def test_collapses_backslash_continuations(self):
        snippet = "az vm create \\\n  -n myVM \\\n  --image myImage"
        self.assertEqual(_extract_command(snippet), ["az vm create -n myVM --image myImage"])

    def test_collapses_caret_and_backtick_continuations(self):
        self.assertEqual(_extract_command("az vm create ^\n  -n myVM"), ["az vm create -n myVM"])
        self.assertEqual(_extract_command("az vm create `\n  -n myVM"), ["az vm create -n myVM"])

    def test_collapses_mistyped_slash_continuation(self):
        snippet = "az storage account create -n acc /\n  -g rg --sku Standard_GRS"
        self.assertEqual(_extract_command(snippet), ["az storage account create -n acc -g rg --sku Standard_GRS"])

    def test_keeps_trailing_slash_in_values(self):
        snippet = "az storage blob upload --url https://x.blob.core.windows.net/c/"
        self.assertEqual(_extract_command(snippet), [snippet])

    def test_keeps_separate_commands_on_separate_lines(self):
        self.assertEqual(_extract_command("az vm create -n x\n\naz vm show -n x"),
                         ["az vm create -n x", "az vm show -n x"])

    def test_no_command_returns_empty(self):
        self.assertEqual(_extract_command("Write-Host hello"), [])
        self.assertEqual(_extract_command(""), [])


class TestDedupeKey(unittest.TestCase):

    def test_ignores_case_and_punctuation(self):
        self.assertEqual(_dedupe_key("Create an Azure storage account"),
                         _dedupe_key("Create an Azure Storage Account."))

    def test_empty_input(self):
        self.assertEqual(_dedupe_key(""), "")
        self.assertEqual(_dedupe_key(None), "")


class TestSearchMslearn(unittest.TestCase):
    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('requests.post')
    def test_search_returns_docs_and_code(self, mock_post, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False

        mock_post.side_effect = [
            _make_init_response(),
            _make_notify_response(),
            _make_tool_response(SAMPLE_DOC_RESULTS),
            _make_tool_response(SAMPLE_CODE_RESULTS),
        ]

        docs, code = search_mslearn("az vm delete")

        self.assertEqual(len(docs), 2)
        self.assertEqual(len(code), 2)
        self.assertEqual(docs[0]["title"], "az vm delete")
        self.assertIn("codeSnippet", code[0])

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('requests.post')
    def test_search_empty_results(self, mock_post, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False

        mock_post.side_effect = [
            _make_init_response(),
            _make_notify_response(),
            _make_tool_response([]),
            _make_tool_response([]),
        ]

        docs, code = search_mslearn("xyznonexistent")
        self.assertEqual(len(docs), 0)
        self.assertEqual(len(code), 0)


class TestFormatResults(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_format_with_results(self, mock_stdout, _):
        format_results("az vm delete", SAMPLE_DOC_RESULTS, SAMPLE_CODE_RESULTS)

        output = mock_stdout.getvalue()
        self.assertIn("Documentation", output)
        self.assertIn("az vm delete", output)
        self.assertIn("Delete a virtual machine.", output)
        self.assertIn("learn.microsoft.com/cli/azure/vm", output)
        self.assertIn("Examples", output)
        self.assertIn("--resource-group myResourceGroup", output)
        self.assertIn("--force-deletion true", output)

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stderr', new_callable=StringIO)
    def test_format_empty_results(self, mock_stderr, _):
        format_results("xyznonexistent", [], [])
        output = mock_stderr.getvalue()
        self.assertIn("Sorry I am not able to help with", output)

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_format_docs_only(self, mock_stdout, _):
        format_results("az vm", SAMPLE_DOC_RESULTS, [])
        output = mock_stdout.getvalue()
        self.assertIn("Documentation", output)
        self.assertNotIn("Examples", output)

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_format_code_only(self, mock_stdout, _):
        format_results("az vm", [], SAMPLE_CODE_RESULTS)
        output = mock_stdout.getvalue()
        self.assertNotIn("Documentation", output)
        self.assertIn("Examples", output)

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_format_caps_results(self, mock_stdout, _):
        # Create more (distinct URL and title) results than the max.
        many_docs = []
        for i in range(MAX_DOC_RESULTS + 5):
            doc = dict(SAMPLE_DOC_RESULTS[0])
            doc["title"] = "az vm delete %d" % i
            doc["contentUrl"] = "https://learn.microsoft.com/doc/%d" % i
            many_docs.append(doc)
        many_code = []
        for i in range(MAX_CODE_RESULTS + 5):
            code = dict(SAMPLE_CODE_RESULTS[0])
            code["description"] = "Deletes an Azure virtual machine, variant %d." % i
            code["link"] = "https://learn.microsoft.com/code/%d" % i
            many_code.append(code)
        format_results("az vm", many_docs, many_code)
        output = mock_stdout.getvalue()
        # Count printed doc/code URLs to confirm the caps are enforced.
        doc_count = output.count("https://learn.microsoft.com/doc/")
        code_count = output.count("https://learn.microsoft.com/code/")
        self.assertEqual(doc_count, MAX_DOC_RESULTS)
        self.assertEqual(code_count, MAX_CODE_RESULTS)

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_format_dedupes_by_url(self, mock_stdout, _):
        # Duplicate URLs should be collapsed (first kept), and later unique
        # results used to fill up to the cap.
        dup_doc = dict(SAMPLE_DOC_RESULTS[0])
        extra_doc = dict(SAMPLE_DOC_RESULTS[1])
        extra_doc["contentUrl"] = "https://learn.microsoft.com/doc/extra"
        # With MAX_DOC_RESULTS == 2, the duplicate must be collapsed so the
        # unique extra_doc fills the freed slot.
        docs = [SAMPLE_DOC_RESULTS[0], dup_doc, extra_doc]

        dup_code = dict(SAMPLE_CODE_RESULTS[0])
        extra_code = dict(SAMPLE_CODE_RESULTS[1])
        extra_code["description"] = "Deletes a virtual machine and its disks in Azure."
        extra_code["link"] = "https://learn.microsoft.com/code/extra"
        code = [SAMPLE_CODE_RESULTS[0], dup_code, SAMPLE_CODE_RESULTS[1], extra_code]

        format_results("az vm", docs, code)
        output = mock_stdout.getvalue()

        # Each duplicated URL is printed only once.
        self.assertEqual(output.count(SAMPLE_DOC_RESULTS[0]["contentUrl"]), 1)
        self.assertEqual(output.count(SAMPLE_CODE_RESULTS[0]["link"]), 1)
        # Caps are filled from the remaining unique results.
        self.assertIn("https://learn.microsoft.com/doc/extra", output)
        self.assertIn("https://learn.microsoft.com/code/extra", output)

    @mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_format_dedupes_by_title(self, mock_stdout, _):
        # Same article under different URL fragments must appear only once.
        dup_doc = dict(SAMPLE_DOC_RESULTS[0])
        dup_doc["title"] = "AZ VM Delete."  # same title, different casing/punctuation
        dup_doc["contentUrl"] = "https://learn.microsoft.com/cli/azure/vm#delete"
        other_doc = dict(SAMPLE_DOC_RESULTS[1])

        dup_code = dict(SAMPLE_CODE_RESULTS[0])
        dup_code["link"] = "https://learn.microsoft.com/code/other-fragment"

        format_results("az vm", [SAMPLE_DOC_RESULTS[0], dup_doc, other_doc],
                       [SAMPLE_CODE_RESULTS[0], dup_code, SAMPLE_CODE_RESULTS[1]])
        output = mock_stdout.getvalue()

        self.assertEqual(output.count("az vm delete."), 1)
        self.assertNotIn("https://learn.microsoft.com/cli/azure/vm#delete", output)
        self.assertNotIn("https://learn.microsoft.com/code/other-fragment", output)
        # The next unique results still fill the freed slots.
        self.assertIn(SAMPLE_DOC_RESULTS[1]["contentUrl"], output)
        self.assertIn(SAMPLE_CODE_RESULTS[1]["link"], output)


class TestProcessQuery(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('azure.cli.command_modules.find.custom.show_updates_available', create=True)
    @mock.patch('requests.post')
    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('sys.stderr', new_callable=StringIO)
    def test_process_query_success(self, mock_stderr, mock_stdout, mock_post, _, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False

        mock_post.side_effect = [
            _make_init_response(),
            _make_notify_response(),
            _make_tool_response(SAMPLE_DOC_RESULTS),
            _make_tool_response(SAMPLE_CODE_RESULTS),
        ]

        with mock.patch('azure.cli.command_modules.find.custom.should_enable_styling', return_value=False):
            process_query("az vm delete")

        output = mock_stdout.getvalue()
        self.assertIn("az vm delete", output)

    @mock.patch('azure.cli.command_modules.find.custom.telemetry_core')
    @mock.patch('azure.cli.command_modules.find.custom.show_updates_available', create=True)
    @mock.patch('requests.post')
    def test_process_query_network_error(self, mock_post, _, mock_telemetry):
        mock_telemetry._get_installation_id.return_value = "test-install-id"
        mock_telemetry.is_telemetry_enabled.return_value = False

        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("Connection failed")

        # Should not raise
        process_query("az vm delete")

    @mock.patch('azure.cli.command_modules.find.custom.show_updates_available', create=True)
    def test_process_query_empty_term(self, _):
        # Should not raise, just log error
        process_query(None)


if __name__ == '__main__':
    unittest.main()
