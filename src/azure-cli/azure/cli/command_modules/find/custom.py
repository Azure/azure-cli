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

# Hints appended to the docs query so results stay Azure CLI specific
DOCS_QUERY_HINTS = ['Azure CLI', 'az command']

# Doc summary length and the marker shown when a summary is cut short
MAX_SUMMARY_LENGTH = 150
MIN_SUMMARY_LENGTH = 40
CONTINUATION_MARKER = ' ... (see link for the full article)'

# Filler words that carry no search signal and would otherwise skew filtering
STOP_WORDS = {
    'about', 'all', 'also', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'been', 'being', 'but',
    'by', 'can', 'could', 'did', 'do', 'does', 'for', 'from', 'had', 'has', 'have', 'here', 'how',
    'if', 'in', 'into', 'is', 'it', 'its', 'may', 'me', 'might', 'must', 'my', 'no', 'not', 'of',
    'on', 'or', 'our', 'over', 'please', 'shall', 'should', 'so', 'some', 'such', 'than', 'that',
    'the', 'their', 'them', 'then', 'there', 'these', 'they', 'this', 'those', 'to', 'up', 'us',
    'via', 'want', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'why',
    'will', 'with', 'would', 'you', 'your',
}

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
    """Extract meaningful keywords from the query.

    Keeps words of 2+ characters so short but meaningful Azure terms such as
    'vm', 'ad' or 'k8s' survive, while dropping the 'az' prefix and common
    filler words (articles, auxiliaries, interrogatives) that carry no signal.

    Args:
        query: The user's query string.

    Returns:
        Set of lowercase keyword strings.
    """
    words = re.findall(r'[a-z0-9]{2,}', query.lower())
    return {w for w in words if w != 'az' and w not in STOP_WORDS}


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
    text_stems = {_stem(w) for w in re.findall(r'[a-z0-9]+', text.lower())}
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


def _build_docs_query(query):
    """Scope a user query to Azure CLI documentation.

    The docs search is semantic and otherwise returns portal/PowerShell/SDK
    articles. Appending Azure CLI hints biases results toward `az` content.

    Args:
        query: The user's query string.

    Returns:
        The query string with Azure CLI hint keywords appended.
    """
    query = (query or "").strip()
    lowered = query.lower()
    hints = [hint for hint in DOCS_QUERY_HINTS if hint.lower() not in lowered]
    return " ".join([query] + hints) if hints else query


def _cli_doc_score(result):
    """Score how Azure CLI specific a doc result is.

    Args:
        result: A doc result dict from MCP.

    Returns:
        3 for the `az` command reference, 2 for content with `az` invocations,
        1 for content merely mentioning the Azure CLI, 0 otherwise.
    """
    url = (result.get("contentUrl", "") or "").lower()
    if "/cli/azure" in url:
        return 3

    content = (result.get("content", "") or "") + " " + (result.get("title", "") or "")
    if re.search(r'(?m)^\s*az\s+[a-z][\w-]*', content) or "azurecli" in content.lower():
        return 2

    return 1 if "azure cli" in content.lower() else 0


def _prefer_cli_docs(results):
    """Keep and rank the Azure CLI related doc results.

    Results without any Azure CLI signal are dropped; the rest are ordered
    most-CLI-specific first, preserving the server's relative ranking within
    the same score. Falls back to the original results if none look CLI
    specific, so the user still gets something back.

    Args:
        results: List of doc result dicts from MCP.

    Returns:
        Filtered and ranked list of doc results.
    """
    scored = [(_cli_doc_score(r), i, r) for i, r in enumerate(results)]
    cli_results = [item for item in scored if item[0] > 0]
    if not cli_results:
        return results

    cli_results.sort(key=lambda item: (-item[0], item[1]))
    return [r for _, _, r in cli_results]


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
        {"query": _build_docs_query(query)}
    )

    code_response = client.call_tool(
        "microsoft_code_sample_search",
        {"query": query, "language": "azurecli"}
    )

    docs_results = docs_response.get("results", [])
    code_results = code_response.get("results", [])

    # Filter out irrelevant CLI commands (e.g., 'az lab vm' when searching 'az vm')
    docs_results = _filter_results(docs_results, query)

    # Drop docs that aren't about the Azure CLI (portal/PowerShell/SDK articles)
    docs_results = _prefer_cli_docs(docs_results)

    # Filter code results by keyword overlap too
    query_words = _get_query_keywords(query)
    if query_words:
        code_results = [r for r in code_results
                        if _matches_keywords(
                            r.get("codeSnippet", "") + " " + r.get("description", ""),
                            query_words)]

    return docs_results, code_results


def _clean_markdown(text):
    """Strip markdown noise so a summary reads as plain prose.

    Converts `[label](url)` links to their label and removes emphasis and
    inline code markers.

    Args:
        text: Raw markdown text.

    Returns:
        Plain-text version of the input.
    """
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[*_`]+', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _shorten(text):
    """Trim a summary to MAX_SUMMARY_LENGTH without cutting mid-word.

    Prefers ending on a sentence boundary. When the text is cut short, a
    continuation marker is appended so it's clear more content follows at the
    documentation link.

    Args:
        text: The summary text.

    Returns:
        A summary no longer than MAX_SUMMARY_LENGTH (plus the marker).
    """
    text = text.strip()
    if len(text) <= MAX_SUMMARY_LENGTH:
        return text

    window = text[:MAX_SUMMARY_LENGTH + 1]

    # Prefer a sentence boundary, as long as it keeps most of the window.
    sentence_end = max(window.rfind('. '), window.rfind('! '), window.rfind('? '))
    if sentence_end >= MAX_SUMMARY_LENGTH // 2:
        return window[:sentence_end + 1] + CONTINUATION_MARKER

    cut = window.rfind(' ')
    if cut <= 0:
        cut = MAX_SUMMARY_LENGTH
    return window[:cut].rstrip(' ,;:-') + CONTINUATION_MARKER


def _extract_summary(content):
    """Extract a clean summary from MCP doc content.

    MCP returns markdown content with headers. Extract the Summary section
    or first meaningful paragraph, then trim it to a readable length with a
    continuation marker when the text is cut short.

    Args:
        content: Raw markdown content string.

    Returns:
        Clean summary string, at most MAX_SUMMARY_LENGTH chars plus a
        continuation marker.
    """
    if not content:
        return ""

    # Try to find a "### Summary" section
    summary_match = re.search(r'###\s*Summary\s*\n(.+?)(?:\n###|\Z)', content, re.DOTALL)
    if summary_match:
        summary = _clean_markdown(summary_match.group(1).split('\n\n')[0])
        if summary:
            return _shorten(summary)

    # Try the first meaningful prose line, preferring one that reads as a
    # complete thought over a short fragment or heading-like lead-in.
    candidates = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith(('#', '---', '|', '```', '>')):
            continue
        cleaned = _clean_markdown(line)
        if cleaned:
            candidates.append(cleaned)
        if len(candidates) >= 10:
            break

    if candidates:
        best = next((c for c in candidates
                     if len(c) >= MIN_SUMMARY_LENGTH and not c.endswith((':', ';', ','))),
                    candidates[0])
        return _shorten(best)

    return _shorten(_clean_markdown(content))


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
        # Docs sometimes typo the continuation as ' /'; only treat a slash
        # preceded by whitespace as one so trailing-slash values are kept.
        if not continued and re.search(r'\s/$', stripped):
            continued = True
        if continued:
            stripped = stripped[:-1].rstrip()

        pending = stripped if pending is None else (pending + ' ' + stripped).strip()

        if not continued:
            result.append(pending)
            pending = None

    if pending:
        result.append(pending)

    return result


def _dedupe_key(text):
    """Normalize text into a key for duplicate detection.

    Lowercases and collapses whitespace and punctuation so titles that differ
    only in casing or trailing punctuation compare equal.

    Args:
        text: The text to normalize.

    Returns:
        Normalized key string, or '' if there's nothing meaningful.
    """
    return re.sub(r'[^a-z0-9]+', ' ', (text or "").lower()).strip()


def _collect_unique(results, limit, build_entry):
    """Collect entries from results, skipping duplicates and empty entries.

    An entry is skipped when its URL or its normalized title has already been
    seen, so the same article never appears twice even if its URL fragment
    differs.

    Args:
        results: List of raw result dicts from MCP.
        limit: Maximum number of entries to collect.
        build_entry: Callable taking a result and returning
            (title, body, url), or None to skip the result.

    Returns:
        List of (title, body, url) tuples.
    """
    entries = []
    seen_urls = set()
    seen_titles = set()

    for result in results:
        entry = build_entry(result)
        if not entry:
            continue

        title, _, url = entry
        title_key = _dedupe_key(title)
        if (url and url in seen_urls) or (title_key and title_key in seen_titles):
            continue

        seen_urls.add(url)
        seen_titles.add(title_key)
        entries.append(entry)
        if len(entries) >= limit:
            break

    return entries


def _build_example_entry(result):
    """Build an example entry from a code sample result.

    Args:
        result: A code sample dict from MCP.

    Returns:
        (title, command_lines, url) tuple, or None if there's no `az` command.
    """
    command_lines = _extract_command(result.get("codeSnippet", ""))
    if not command_lines:
        return None

    return (_extract_description(result.get("description", "")),
            command_lines,
            result.get("link", ""))


def _build_doc_entry(result):
    """Build a documentation entry from a doc result.

    Args:
        result: A doc result dict from MCP.

    Returns:
        (title, summary, url) tuple.
    """
    return (_clean_title(result.get("title", "")),
            _extract_summary(result.get("content", "")),
            result.get("contentUrl", ""))


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
        print('\nSorry I am not able to help with [' + query + '].'
              '\nTry typing the beginning of a command, e.g., "az vm create".\n', file=sys.stderr)
        return

    print("\nHere is what I found for [" + query + "]: \n", file=sys.stderr)

    examples = _collect_unique(code_results, MAX_CODE_RESULTS, _build_example_entry)
    if examples:
        print("Examples")
        for title, command_lines, url in examples:
            print(format_styled_text((Style.HIGHLIGHT, "  - " + title)))
            for line in command_lines:
                print("    " + line)
            if url:
                print("    " + format_styled_text((Style.SECONDARY, url)))
            print()

    docs = _collect_unique(docs_results, MAX_DOC_RESULTS, _build_doc_entry)
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
        logger.error('Please provide a search term, e.g., az find "az vm create".')
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
