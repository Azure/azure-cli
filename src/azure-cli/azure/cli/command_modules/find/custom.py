# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import namedtuple
import hashlib
import random
import json
import re
import sys
import platform
import requests
import colorama  # pylint: disable=import-error


from azure.cli.core import telemetry as telemetry_core
from azure.cli.core import __version__ as core_version
from packaging.version import parse
from knack.log import get_logger
logger = get_logger(__name__)

WAIT_MESSAGE = ['Finding examples...']

# Display limits
MAX_DOC_RESULTS = 5
MAX_CODE_RESULTS = 3

Example = namedtuple("Example", "title snippet")


class MCPClient:
    """Lightweight MCP client for Microsoft Learn MCP Server.

    Implements the minimum JSON-RPC 2.0 over Streamable HTTP protocol
    needed for single-invocation tool calls (initialize → notify → tools/call).
    """

    MCP_ENDPOINT = "https://learn.microsoft.com/api/mcp"

    def __init__(self, client_version=None):
        self.session_id = None
        self.client_version = client_version or str(parse(core_version))
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        self._request_id = 0
        self._add_telemetry_headers()

    def _add_telemetry_headers(self):
        """Add telemetry context as custom headers."""
        # Used for DDOS protection and rate limiting
        user_id = telemetry_core._get_installation_id()  # pylint: disable=protected-access
        hashed_user_id = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        self._headers["X-UserId"] = hashed_user_id

        if telemetry_core.is_telemetry_enabled():
            correlation_id = telemetry_core._session.correlation_id  # pylint: disable=protected-access
            event_id = telemetry_core._session.event_id  # pylint: disable=protected-access
            subscription_id = telemetry_core._get_azure_subscription_id()  # pylint: disable=protected-access

            self._headers["X-CorrelationId"] = correlation_id
            self._headers["X-EventId"] = event_id
            if subscription_id is not None:
                self._headers["X-SubscriptionId"] = subscription_id

    def _next_id(self):
        self._request_id += 1
        return self._request_id

    def initialize(self):
        """Send initialize request and store session ID."""
        body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "azure-cli-find",
                    "version": self.client_version
                }
            }
        }
        resp = requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, timeout=10)
        resp.raise_for_status()
        self.session_id = resp.headers.get("mcp-session-id")
        if self.session_id:
            self._headers["mcp-session-id"] = self.session_id
        return self._parse_sse(resp.text)

    def notify_initialized(self):
        """Send initialized notification to confirm client readiness."""
        body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, timeout=10)

    def call_tool(self, tool_name, arguments):
        """Call an MCP tool and return parsed results.

        Args:
            tool_name: Name of the MCP tool (e.g., 'microsoft_docs_search').
            arguments: Dict of tool arguments.

        Returns:
            Parsed JSON result from the tool's text content.
        """
        body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        resp = requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, timeout=30)
        resp.raise_for_status()
        result = self._parse_sse(resp.text)
        content_list = result.get("result", {}).get("content", [])
        if content_list and content_list[0].get("text"):
            return json.loads(content_list[0]["text"])
        return {}

    @staticmethod
    def _parse_sse(text):
        """Parse single-event SSE response.

        The MCP server returns responses in SSE format with a single 'data:' event.
        """
        for line in text.split("\n"):
            if line.startswith("data: "):
                return json.loads(line[6:])
        return {}


def _extract_query_command(query):
    """Extract the CLI command group/name from a query string.

    Examples:
        'az vm create' → 'az vm create'
        'az vm' → 'az vm'
        'vm create' → 'az vm create'
        'deploy arm template' → None (not a CLI command pattern)

    Returns:
        Normalized command string or None if not a CLI command pattern.
    """
    query = query.strip().lower()
    if query.startswith('az '):
        return query
    # If the query looks like a CLI subcommand (single words that could be a group)
    parts = query.split()
    if parts and not any(c in parts[0] for c in ' ./-'):
        return 'az ' + query
    return None


def _is_cli_command_relevant(title, query):
    """Check if a CLI command result title is relevant to the query.

    For CLI command results (titles starting with 'az '), checks that
    the result command shares the same command group as the query.

    Examples (query='az vm create'):
        'az vm create' → True (exact match)
        'az vm run-command create' → True (same group)
        'az lab vm create' → False (different group: 'lab' vs 'vm')
        'az connectedvmware vm create' → False (different group)

    Args:
        title: The result title string.
        query: The user's query string.

    Returns:
        True if the result is relevant, False otherwise.
    """
    title_lower = title.strip().lower()

    # Only filter CLI command titles (starting with 'az ')
    if not title_lower.startswith('az '):
        return True

    cmd = _extract_query_command(query)
    if not cmd:
        return True

    # Extract the command group (first word after 'az')
    cmd_parts = cmd.split()
    if len(cmd_parts) < 2:
        return True

    query_group = cmd_parts[1]  # e.g., 'vm' from 'az vm create'

    title_parts = title_lower.split()
    if len(title_parts) < 2:
        return True

    title_group = title_parts[1]  # e.g., 'lab' from 'az lab vm create'

    # The result's first command group must match the query's command group
    return title_group == query_group


def _filter_results(results, query):
    """Filter MCP results for relevance to the query.

    Removes CLI command results that belong to different command groups,
    and filters out results whose titles have no meaningful word overlap
    with the query (to discard noise from semantic search on gibberish queries).

    Args:
        results: List of MCP doc result dicts.
        query: The user's query string.

    Returns:
        Filtered list of result dicts.
    """
    filtered = [r for r in results if _is_cli_command_relevant(r.get("title", ""), query)]

    # For non-empty queries, check that at least some results are genuinely relevant
    # by verifying word overlap between the query and result titles/content
    query_words = _get_query_keywords(query)
    if query_words:
        filtered = [r for r in filtered if _has_keyword_overlap(r, query_words)]

    return filtered


def _get_query_keywords(query):
    """Extract meaningful keywords from the query (words with 3+ chars, excluding 'az').

    Args:
        query: The user's query string.

    Returns:
        Set of lowercase keyword strings.
    """
    words = re.findall(r'[a-zA-Z]{3,}', query.lower())
    stop_words = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'are', 'was', 'has', 'have'}
    return {w for w in words if w != 'az' and w not in stop_words}


def _has_keyword_overlap(result, query_words):
    """Check if a result has meaningful keyword overlap with the query.

    Args:
        result: A doc result dict with 'title' and optionally 'content'.
        query_words: Set of query keywords to match against.

    Returns:
        True if at least one query keyword appears in the result's title or content.
    """
    title = result.get("title", "").lower()
    content = result.get("content", "").lower()[:500]  # Only check first 500 chars of content
    combined = title + " " + content

    return any(word in combined for word in query_words)


def search_mslearn(query):
    """Search Microsoft Learn via MCP for docs and code samples.

    Calls two MCP tools:
    1. microsoft_docs_search - for command reference and documentation
    2. microsoft_code_sample_search - for runnable CLI examples

    Args:
        query: Search query string (e.g., 'az vm delete').

    Returns:
        Tuple of (docs_results, code_results) where each is a list of dicts.
    """
    client = MCPClient()

    client.initialize()
    client.notify_initialized()

    docs_response = client.call_tool(
        "microsoft_docs_search",
        {"query": query}
    )

    code_response = client.call_tool(
        "microsoft_code_sample_search",
        {"query": query, "language": "azurecli"}
    )

    docs_results = docs_response.get("results", [])
    code_results = code_response.get("results", [])

    # Filter out irrelevant CLI commands (e.g., 'az lab vm' when searching 'az vm')
    docs_results = _filter_results(docs_results, query)

    # Filter code results by keyword overlap too
    query_words = _get_query_keywords(query)
    if query_words:
        code_results = [r for r in code_results
                        if any(word in (r.get("codeSnippet", "") + " " +
                                        r.get("description", "")).lower()
                               for word in query_words)]

    return docs_results, code_results


def _extract_summary(content):
    """Extract a clean summary from MCP doc content.

    MCP returns markdown content with headers. Extract the Summary section
    or first meaningful paragraph.

    Args:
        content: Raw markdown content string.

    Returns:
        Clean summary string, max 150 chars.
    """
    if not content:
        return ""

    # Try to find a "### Summary" section
    summary_match = re.search(r'###\s*Summary\s*\n(.+?)(?:\n###|\Z)', content, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
        # Take first sentence/line
        first_line = summary.split('\n')[0].strip()
        if first_line:
            return first_line[:150]

    # Try first non-header, non-empty line
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            return line[:150]

    return content[:150]


def format_results(query, docs_results, code_results):
    """Format and print search results to stdout.

    Displays results in two sections:
    1. Commands & Documentation - from microsoft_docs_search
    2. Code Examples - from microsoft_code_sample_search

    Args:
        query: Original search query (for display).
        docs_results: List of doc result dicts from MCP.
        code_results: List of code sample dicts from MCP.
    """
    if not docs_results and not code_results:
        print("\nSorry I am not able to help with [" + query + "]."
              "\nTry typing the beginning of a command e.g. " + style_message('az vm') + ".", file=sys.stderr)
        return

    print("\nHere are the most common ways to use [" + query + "]: \n", file=sys.stderr)

    if docs_results:
        print(style_message(" Commands & Documentation"))
        print("  " + "─" * 50)
        for result in docs_results[:MAX_DOC_RESULTS]:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("contentUrl", "")

            summary = _extract_summary(content)

            print(style_message("  " + title))
            if summary:
                print("  " + summary)
            if url:
                print("  " + url)
            print()

    if code_results:
        print(style_message(" Code Examples"))
        print("  " + "─" * 50)
        for result in code_results[:MAX_CODE_RESULTS]:
            snippet = result.get("codeSnippet", "")
            url = result.get("link", "")

            if snippet:
                # Indent the code snippet
                for line in snippet.strip().split('\n'):
                    print("  " + line)
            if url:
                print("  Source: " + url)
            print()


def process_query(cli_term):
    if not cli_term:
        logger.error('Please provide a search term e.g. az find "vm"')
    else:
        print(random.choice(WAIT_MESSAGE), file=sys.stderr)

        try:
            docs_results, code_results = search_mslearn(cli_term)
        except requests.exceptions.RequestException as ex:
            logger.debug("MCP request failed: %s", ex)
            logger.error(
                "Unable to search Microsoft Learn. Please check your network connection. "
                "In the meantime, use `az <command> --help` or visit https://aka.ms/cli_ref."
            )
            return

        if platform.system() == 'Windows' and should_enable_styling():
            colorama.init(convert=True)

        format_results(cli_term, docs_results, code_results)

    from azure.cli.core.util import show_updates_available
    show_updates_available()


def get_generated_examples(cli_term):
    """Get generated examples for a CLI term.

    Returns list of Example namedtuples for backward compatibility.
    """
    examples = []
    try:
        docs_results, code_results = search_mslearn(cli_term)

        for result in docs_results:
            title = result.get("title", "")
            summary = _extract_summary(result.get("content", ""))
            examples.append(Example(title, summary))

        for result in code_results:
            snippet = result.get("codeSnippet", "")
            desc = result.get("description", "")
            examples.append(Example(desc[:100] if desc else "Example", snippet))

    except requests.exceptions.RequestException:
        pass

    return examples


def style_message(msg):
    if should_enable_styling():
        try:
            msg = colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL
        except KeyError:
            pass
    return msg


def should_enable_styling():
    try:
        # Style if tty stream is available
        if sys.stdout.isatty():
            return True
    except AttributeError:
        pass
    return False
