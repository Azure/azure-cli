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
from azure.cli.core.style import Style, format_styled_text
from packaging.version import parse
from knack.log import get_logger
logger = get_logger(__name__)

WAIT_MESSAGE = ['\nFinding examples and documentation...']

# Display limits
MAX_DOC_RESULTS = 2
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
        self._context = self._build_telemetry_context()

    def _build_telemetry_context(self):
        """Build telemetry context sent alongside MCP requests.

        Mirrors the dev branch behavior: the hashed installation id is always
        sent as the ``X-UserId`` header (used for DDOS protection and rate
        limiting), while the remaining contextual values are only included when
        the user has consented to telemetry.
        """
        # Used for DDOS protection and rate limiting
        user_id = telemetry_core._get_installation_id()  # pylint: disable=protected-access
        hashed_user_id = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        self._headers["X-UserId"] = hashed_user_id

        context = {
            "versionNumber": self.client_version,
        }

        # Only pull in the contextual values if we have consent
        if telemetry_core.is_telemetry_enabled():
            correlation_id = telemetry_core._session.correlation_id  # pylint: disable=protected-access
            event_id = telemetry_core._session.event_id  # pylint: disable=protected-access
            subscription_id = telemetry_core._get_azure_subscription_id()  # pylint: disable=protected-access

            context["correlationId"] = correlation_id
            context["eventId"] = event_id
            if subscription_id is not None:
                context["subscriptionId"] = subscription_id

        return context

    @property
    def _params(self):
        return {"context": json.dumps(self._context)}

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
        resp = requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, params=self._params, timeout=10)
        resp.raise_for_status()
        self.session_id = resp.headers.get("mcp-session-id")
        if self.session_id:
            self._headers["mcp-session-id"] = self.session_id
        return self._parse_sse(resp.text)

    def notify_initialized(self):
        """Send initialized notification to confirm client readiness."""
        body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, params=self._params, timeout=10)

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
        resp = requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, params=self._params, timeout=30)
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


def _stem(word):
    """Reduce a word to a crude stem so morphological variants match.

    Strips common inflectional suffixes and a trailing 'e' so that variants
    such as 'creating', 'creates', 'created' and 'create' all collapse to the
    same stem ('creat'). This is a lightweight, dependency-free approximation
    (not a full Porter stemmer) that is sufficient for matching query terms
    against documentation and code samples.

    Args:
        word: A single word.

    Returns:
        The stemmed, lowercased word.
    """
    word = word.lower()
    for suffix in ('ings', 'ing', 'ies', 'ied', 'es', 'ed', 's'):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    if len(word) > 3 and word.endswith('e'):
        word = word[:-1]
    return word


def _matches_keywords(text, query_words):
    """Check if any query keyword matches a word in the text after stemming.

    Both the query keywords and the text words are stemmed before comparison,
    so morphological variants match (e.g. query 'creating' matches text
    'create').

    Args:
        text: The text to search within.
        query_words: Set of query keywords to match against.

    Returns:
        True if at least one query keyword stem matches a word stem in the text.
    """
    text_stems = {_stem(w) for w in re.findall(r'[a-zA-Z]+', text.lower())}
    return any(_stem(word) in text_stems for word in query_words)


def _has_keyword_overlap(result, query_words):
    """Check if a result has meaningful keyword overlap with the query.

    Args:
        result: A doc result dict with 'title' and optionally 'content'.
        query_words: Set of query keywords to match against.

    Returns:
        True if at least one query keyword appears in the result's title or content.
    """
    title = result.get("title", "")
    content = result.get("content", "")[:500]  # Only check first 500 chars of content
    combined = title + " " + content

    return _matches_keywords(combined, query_words)


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
                        if _matches_keywords(
                            r.get("codeSnippet", "") + " " + r.get("description", ""),
                            query_words)]

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


def _clean_title(title):
    """Normalize a title into a real sentence.

    Strips leading markdown header markers ('#') and ensures the title
    ends with a sentence mark (period, question mark, or exclamation mark).

    Args:
        title: Raw title string.

    Returns:
        Cleaned title string, or empty string if no title.
    """
    if not title:
        return ""

    title = title.strip().lstrip('#').strip()
    if title and title[-1] not in '.?!':
        title += '.'
    return title


def _to_imperative(text):
    """Convert a leading third-person-singular verb to imperative mood.

    Examples:
        'Deploys the template.' -> 'Deploy the template.'
        'Creates a virtual machine.' -> 'Create a virtual machine.'
        'Specifies the name.' -> 'Specify the name.'

    Args:
        text: A description sentence.

    Returns:
        The sentence with its first word converted to imperative mood.
    """
    if not text:
        return text

    first, _, rest = text.partition(' ')
    lower = first.lower()
    if lower.endswith('ies') and len(first) > 4:
        first = first[:-3] + 'y'
    elif lower.endswith('s') and not lower.endswith('ss'):
        first = first[:-1]

    return first + (' ' + rest if rest else '')


def _extract_description(description):
    """Extract the human-readable description from a code sample's metadata.

    The MCP code sample 'description' field is a metadata blob such as:
        'description: Deploys the ARM template ...\\nlanguage: azurecli\\n'
    This extracts just the description text as a clean sentence.

    Args:
        description: Raw description metadata string.

    Returns:
        Cleaned description sentence, or 'Example.' as a fallback.
    """
    if description:
        for line in description.split('\n'):
            line = line.strip()
            if line.lower().startswith('description:'):
                return _clean_title(_to_imperative(line[len('description:'):].strip()))

        # Fallback: first non-empty, non-metadata line
        for line in description.split('\n'):
            line = line.strip()
            if line and not line.lower().startswith(('language:', 'package:')):
                return _clean_title(_to_imperative(line))

    return "Example."


def _extract_command(snippet):
    """Extract the `az` command block from a code snippet.

    Returns the command lines starting from the first line that begins with
    'az'. Shell line-continuations (`\\`, `^` or backtick) are collapsed so that
    each command is returned as a single line.

    Args:
        snippet: Raw code snippet string.

    Returns:
        List of single-line commands, or empty list.
    """
    if not snippet:
        return []

    lines = snippet.split('\n')
    start = next((i for i, line in enumerate(lines) if line.strip().startswith('az ')), None)
    if start is None:
        return []

    result = []
    pending = None
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            continue

        continued = stripped.endswith(('\\', '^', '`'))
        if continued:
            stripped = stripped[:-1].rstrip()

        pending = stripped if pending is None else (pending + ' ' + stripped).strip()

        if not continued:
            result.append(pending)
            pending = None

    if pending:
        result.append(pending)

    return result


def format_results(query, docs_results, code_results):
    """Format and print search results to stdout.

    Displays results in two sections:
    1. Examples - from microsoft_code_sample_search (shown first)
    2. Documentation - from microsoft_docs_search

    Args:
        query: Original search query (for display).
        docs_results: List of doc result dicts from MCP.
        code_results: List of code sample dicts from MCP.
    """
    if not docs_results and not code_results:
        print("\nSorry I am not able to help with [" + query + "]."
              "\nTry typing the beginning of a command e.g., " + style_message('az vm') + ".", file=sys.stderr)
        return

    print("\nHere is what I found for [" + query + "]: \n", file=sys.stderr)

    if code_results:
        examples = []
        seen_urls = set()
        for result in code_results:
            command_lines = _extract_command(result.get("codeSnippet", ""))
            if not command_lines:
                continue
            url = result.get("link", "")
            # Skip duplicate URLs, keeping only the first occurrence.
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            examples.append((
                _extract_description(result.get("description", "")),
                command_lines,
                url
            ))
            if len(examples) >= MAX_CODE_RESULTS:
                break

        if examples:
            print("Examples")
            for title, command_lines, url in examples:
                print(format_styled_text((Style.HIGHLIGHT, "  - " + title)))
                for line in command_lines:
                    print("    " + line)
                if url:
                    print("    " + format_styled_text((Style.SECONDARY, url)))
                print()

    if docs_results:
        docs = []
        seen_urls = set()
        for result in docs_results:
            url = result.get("contentUrl", "")
            # Skip duplicate URLs, keeping only the first occurrence.
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            docs.append((
                _clean_title(result.get("title", "")),
                _extract_summary(result.get("content", "")),
                url
            ))
            if len(docs) >= MAX_DOC_RESULTS:
                break

        if docs:
            print("Documentation")
            for title, summary, url in docs:
                print(format_styled_text((Style.HIGHLIGHT, "  - " + title)))
                if summary:
                    print("    " + summary)
                if url:
                    print("    " + format_styled_text((Style.SECONDARY, url)))
                print()


def process_query(cli_term):
    if not cli_term:
        logger.error('Please provide a search term, e.g., az find "vm"')
    else:
        print(random.choice(WAIT_MESSAGE), file=sys.stderr)

        try:
            docs_results, code_results = search_mslearn(cli_term)
        except requests.exceptions.RequestException as ex:
            logger.debug("MCP request failed: %s", ex)
            logger.error(
                "Unable to search Microsoft Learn. Please check your network connection. "
                "In the meantime, please use `az <command> --help` to explore commands and examples, "
                "or visit https://aka.ms/cli_ref for reference documentation."
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
