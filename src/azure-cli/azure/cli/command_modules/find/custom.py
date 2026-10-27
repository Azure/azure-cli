# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import hashlib
import json
import platform
import re
import sys

import requests
import colorama  # pylint: disable=import-error

from azure.cli.core import telemetry as telemetry_core
from azure.cli.core import __version__ as core_version
from azure.cli.core.style import Style, format_styled_text
from packaging.version import parse
from knack.log import get_logger

logger = get_logger(__name__)

WAIT_MESSAGE = '\nFinding examples and documentation...'

# Number of entries printed in each section
MAX_CODE_RESULTS = 3
MAX_DOC_RESULTS = 2

# Hints appended to the docs query so the semantic search stays Azure CLI specific
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


class MCPClient:
    """Lightweight MCP client for the Microsoft Learn MCP server.

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
        """Build the telemetry context sent alongside MCP requests.

        The hashed installation id is always sent as the ``X-UserId`` header
        (used for DDOS protection and rate limiting); the remaining contextual
        values are only included when the user has consented to telemetry.
        """
        user_id = telemetry_core._get_installation_id()  # pylint: disable=protected-access
        self._headers["X-UserId"] = hashlib.sha256(user_id.encode('utf-8')).hexdigest()

        context = {"versionNumber": self.client_version}

        if telemetry_core.is_telemetry_enabled():
            context["correlationId"] = telemetry_core._session.correlation_id  # pylint: disable=protected-access
            context["eventId"] = telemetry_core._session.event_id  # pylint: disable=protected-access
            subscription_id = telemetry_core._get_azure_subscription_id()  # pylint: disable=protected-access
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
        """Send the initialize request and store the session ID."""
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
        """Send the initialized notification to confirm client readiness."""
        body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(self.MCP_ENDPOINT, json=body, headers=self._headers, params=self._params, timeout=10)

    def call_tool(self, tool_name, arguments):
        """Call an MCP tool (e.g. 'microsoft_docs_search') and return its parsed result."""
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
        content = self._parse_sse(resp.text).get("result", {}).get("content", [])
        if content and content[0].get("text"):
            return json.loads(content[0]["text"])
        return {}

    @staticmethod
    def _parse_sse(text):
        """Parse a single-event SSE response, which carries one 'data:' line."""
        for line in text.split("\n"):
            if line.startswith("data: "):
                return json.loads(line[6:])
        return {}


def _get_query_keywords(query):
    """Extract the meaningful keywords of a query.

    Words of 2+ characters are kept so short but meaningful Azure terms such as
    'vm', 'ad' or 'k8s' survive; the 'az' prefix and filler words (articles,
    auxiliaries, interrogatives) are dropped because they carry no signal.
    """
    words = re.findall(r'[a-z0-9]{2,}', query.lower())
    return {w for w in words if w != 'az' and w not in STOP_WORDS}


def _stem(word):
    """Reduce a word to a crude stem so morphological variants match.

    Strips common inflectional suffixes and a trailing 'e' so that 'creating',
    'creates', 'created' and 'create' all collapse to 'creat'. A lightweight,
    dependency-free approximation of a real stemmer, good enough for matching
    query terms against documentation and code samples.
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
    """Check whether any query keyword appears in the text, comparing stems."""
    text_stems = {_stem(w) for w in re.findall(r'[a-z0-9]+', text.lower())}
    return any(_stem(word) in text_stems for word in query_words)


def _has_keyword_overlap(result, query_words):
    """Check whether a doc result's title or content shares a keyword with the query."""
    combined = result.get("title", "") + " " + result.get("content", "")[:500]
    return _matches_keywords(combined, query_words)


def _extract_query_command(query):
    """Normalize a query into an `az` command, or None if it isn't one.

    'az vm create' → 'az vm create'; 'vm create' → 'az vm create';
    'deploy/arm template' → None (doesn't look like a command).
    """
    query = query.strip().lower()
    if query.startswith('az '):
        return query

    parts = query.split()
    if parts and not any(c in parts[0] for c in './-'):
        return 'az ' + query
    return None


def _is_cli_command_relevant(title, query):
    """Check whether a CLI command title belongs to the same command group as the query.

    Only titles that look like a command ('az ...') are judged; anything else
    (tutorials, concept articles) is always considered relevant.

    With query='az vm create': 'az vm create' and 'az vm run-command create'
    are relevant, while 'az lab vm create' and 'az connectedvmware vm create'
    belong to other groups.
    """
    title_lower = title.strip().lower()
    if not title_lower.startswith('az '):
        return True

    command = _extract_query_command(query)
    if not command:
        return True

    command_parts = command.split()
    title_parts = title_lower.split()
    if len(command_parts) < 2 or len(title_parts) < 2:
        return True

    # e.g. 'vm' from 'az vm create' vs 'lab' from 'az lab vm create'
    return title_parts[1] == command_parts[1]


def _filter_results(results, query):
    """Drop doc results that belong to another command group or share no keyword.

    The keyword check discards the noise a semantic search returns for
    gibberish queries.
    """
    filtered = [r for r in results if _is_cli_command_relevant(r.get("title", ""), query)]

    query_words = _get_query_keywords(query)
    if query_words:
        filtered = [r for r in filtered if _has_keyword_overlap(r, query_words)]

    return filtered


def _build_docs_query(query):
    """Append Azure CLI hints to a query so the docs search stays CLI specific.

    Without them the semantic search happily returns portal, PowerShell or SDK
    articles. Hints already present in the query are not repeated.
    """
    query = (query or "").strip()
    lowered = query.lower()
    hints = [hint for hint in DOCS_QUERY_HINTS if hint.lower() not in lowered]
    return " ".join([query] + hints) if hints else query


def _cli_doc_score(result):
    """Score how Azure CLI specific a doc result is.

    3 for the `az` command reference, 2 for content showing `az` invocations,
    1 for content merely mentioning the Azure CLI, 0 for everything else.
    """
    if "/cli/azure" in (result.get("contentUrl", "") or "").lower():
        return 3

    content = (result.get("content", "") or "") + " " + (result.get("title", "") or "")
    lowered = content.lower()
    if "azurecli" in lowered or re.search(r'(?m)^\s*az\s+[a-z][\w-]*', content):
        return 2

    return 1 if "azure cli" in lowered else 0


def _prefer_cli_docs(results):
    """Keep the Azure CLI related doc results, most CLI specific first.

    The server's relative ranking is preserved within the same score. If no
    result looks CLI specific at all, the original list is returned so the user
    still gets something back.
    """
    scored = [(score, i, result) for i, result in enumerate(results)
              if (score := _cli_doc_score(result)) > 0]
    if not scored:
        return results

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [result for _, _, result in scored]


def search_mslearn(query):
    """Search Microsoft Learn for docs and code samples matching the query.

    Returns a (docs_results, code_results) tuple, each a list of result dicts
    already filtered down to what is relevant to the Azure CLI.
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

    docs_results = _prefer_cli_docs(_filter_results(docs_response.get("results", []), query))

    code_results = code_response.get("results", [])
    query_words = _get_query_keywords(query)
    if query_words:
        code_results = [r for r in code_results
                        if _matches_keywords(r.get("codeSnippet", "") + " " + r.get("description", ""),
                                             query_words)]

    return docs_results, code_results


def _clean_markdown(text):
    """Strip markdown noise (images, links, emphasis) so text reads as plain prose."""
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[*_`]+', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _shorten(text):
    """Trim text to MAX_SUMMARY_LENGTH, never cutting mid-word.

    A sentence boundary is preferred as the cut point. Whenever text is
    dropped, CONTINUATION_MARKER is appended so it's clear the rest of the
    article lives behind the link.
    """
    text = text.strip()
    if len(text) <= MAX_SUMMARY_LENGTH:
        return text

    window = text[:MAX_SUMMARY_LENGTH + 1]

    # Only cut at a sentence boundary if that still keeps most of the window.
    sentence_end = max(window.rfind('. '), window.rfind('! '), window.rfind('? '))
    if sentence_end >= MAX_SUMMARY_LENGTH // 2:
        return window[:sentence_end + 1] + CONTINUATION_MARKER

    cut = window.rfind(' ')
    if cut <= 0:
        cut = MAX_SUMMARY_LENGTH
    return window[:cut].rstrip(' ,;:-') + CONTINUATION_MARKER


def _extract_summary(content):
    """Build a short, readable summary from a doc result's markdown content."""
    if not content:
        return ""

    summary_match = re.search(r'###\s*Summary\s*\n(.+?)(?:\n###|\Z)', content, re.DOTALL)
    if summary_match:
        summary = _clean_markdown(summary_match.group(1).split('\n\n')[0])
        if summary:
            return _shorten(summary)

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
        # Prefer a line that reads as a complete thought over a lead-in fragment.
        best = next((c for c in candidates
                     if len(c) >= MIN_SUMMARY_LENGTH and not c.endswith((':', ';', ','))),
                    candidates[0])
        return _shorten(best)

    return _shorten(_clean_markdown(content))


def _clean_title(title):
    """Normalize a title into a sentence: no leading '#', always end-punctuated."""
    if not title:
        return ""

    title = title.strip().lstrip('#').strip()
    if title and title[-1] not in '.?!':
        title += '.'
    return title


def _to_imperative(text):
    """Convert a leading third-person-singular verb to imperative mood.

    'Deploys the template.' → 'Deploy the template.'
    'Specifies the name.' → 'Specify the name.'
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
    """Pull the human-readable sentence out of a code sample's metadata blob.

    The raw field looks like 'description: Deploys the ARM template\\nlanguage:
    azurecli\\n'.
    """
    if description:
        for line in description.split('\n'):
            line = line.strip()
            if line.lower().startswith('description:'):
                return _clean_title(_to_imperative(line[len('description:'):].strip()))

        for line in description.split('\n'):
            line = line.strip()
            if line and not line.lower().startswith(('language:', 'package:')):
                return _clean_title(_to_imperative(line))

    return "Example."


def _extract_command(snippet):
    """Extract the `az` commands from a code snippet, one per line.

    Shell line-continuations are collapsed so a command that the docs wrapped
    over many lines is printed as a single copy-pasteable line.
    """
    if not snippet:
        return []

    lines = snippet.split('\n')
    start = next((i for i, line in enumerate(lines) if line.strip().startswith('az ')), None)
    if start is None:
        return []

    commands = []
    pending = None
    for line in lines[start:]:
        line = line.strip()
        if not line:
            continue

        # '/' is a typo for '\' seen in some docs; require preceding whitespace
        # so that trailing slashes in URLs and paths are left alone.
        continued = line.endswith(('\\', '^', '`')) or bool(re.search(r'\s/$', line))
        if continued:
            line = line[:-1].rstrip()

        pending = line if pending is None else (pending + ' ' + line).strip()
        if not continued:
            commands.append(pending)
            pending = None

    if pending:
        commands.append(pending)

    return commands


def _dedupe_key(text):
    """Normalize text into a comparison key, ignoring case and punctuation."""
    return re.sub(r'[^a-z0-9]+', ' ', (text or "").lower()).strip()


def _build_example_entry(result):
    """Turn a code sample result into a (title, command lines, url) entry.

    Returns None when the sample contains no `az` command.
    """
    command_lines = _extract_command(result.get("codeSnippet", ""))
    if not command_lines:
        return None

    return (_extract_description(result.get("description", "")),
            command_lines,
            result.get("link", ""))


def _build_doc_entry(result):
    """Turn a doc result into a (title, summary, url) entry."""
    return (_clean_title(result.get("title", "")),
            _extract_summary(result.get("content", "")),
            result.get("contentUrl", ""))


def _collect_unique(results, limit, build_entry):
    """Build up to `limit` entries, skipping empty ones and duplicates.

    A result is skipped when its URL or its normalized title was already used,
    so the same article never shows up twice under different URL fragments.
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


def _print_entry(title, body_lines, url):
    """Print one result: a highlighted title, its body, then the source link."""
    print(format_styled_text((Style.HIGHLIGHT, "  - " + title)))
    for line in body_lines:
        print("    " + line)
    if url:
        print("    " + format_styled_text((Style.SECONDARY, url)))
    print()


def format_results(query, docs_results, code_results):
    """Print the runnable examples first, then the documentation links."""
    # Collect first: results can still end up empty here, for instance when no
    # code sample contains an actual `az` command.
    examples = _collect_unique(code_results, MAX_CODE_RESULTS, _build_example_entry)
    docs = _collect_unique(docs_results, MAX_DOC_RESULTS, _build_doc_entry)

    if not examples and not docs:
        print('\nSorry I am not able to help with [' + query + '].'
              '\nTry typing the beginning of a command, e.g., "az vm create".\n', file=sys.stderr)
        return

    print("\nHere is what I found for [" + query + "]: \n", file=sys.stderr)

    if examples:
        print("Examples")
        for title, command_lines, url in examples:
            _print_entry(title, command_lines, url)

    if docs:
        print("Documentation")
        for title, summary, url in docs:
            _print_entry(title, [summary] if summary else [], url)


def should_enable_styling():
    """Check whether output is going to a terminal that can render styling."""
    try:
        return bool(sys.stdout.isatty())
    except AttributeError:
        return False


def process_query(cli_term):
    """Entry point for `az find`."""
    if not cli_term:
        logger.error('Please provide a search term, e.g., az find "az vm create".')
    else:
        print(WAIT_MESSAGE, file=sys.stderr)

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
