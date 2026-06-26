# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Build log formatter for `az webapp deploy` / `az functionapp deploy`.

Renders a clean, curated view of the Oryx build by default: deterministic milestones,
aggregated package counts and a warning tally are kept permanently on screen, while
ordinary build chatter is shown on a single self-overwriting status line (the current
line is replaced in place by the next -- like a progress line). Full verbatim output is
available via --build-logs full; --build-logs none hides build logs entirely.

Classification (summary mode):
  - PERSISTENT: stack/version detection, phase milestones, "Installed N packages"
  - TRANSIENT:  package downloads, oryx/SDK metadata, warnings, other chatter
                (shown on the self-overwriting status line; warnings are also counted)
  - OMITTED:    blank lines
"""

import re
import shutil
import sys
import time


# Log verbosity levels
BUILD_LOGS_FULL = "full"
BUILD_LOGS_SUMMARY = "summary"
BUILD_LOGS_NONE = "none"

# --- Patterns for classification ---
#
# Design: we intentionally do NOT keep a denylist of "noise" lines. A line is shown
# *permanently* only if it matches a deterministic milestone (or is an aggregated
# package summary); every other non-blank line is treated as transient chatter shown on
# the self-overwriting status line (still fully available via --build-logs full). This
# avoids the brittle per-stack denylists that previously needed constant maintenance.

# Patterns for counting packages
_PIP_COLLECTING = re.compile(r'^\s*\[[\d:+]+\]\s*Collecting\s+(\S+)')
_PIP_CACHED = re.compile(r'^\s*\[[\d:+]+\]\s*Using cached\s+\S+')
_PIP_INSTALLING = re.compile(r'^\s*\[[\d:+]+\]\s*Installing collected packages:')
_PIP_INSTALLED = re.compile(r'^\s*\[[\d:+]+\]\s*Successfully installed\s+(.*)')
_NPM_ADDED = re.compile(r'^\s*added (\d+) packages')

# Warning patterns (aggregated in summary mode)
_WARNING_PATTERNS = [
    re.compile(r'^\s*npm warn deprecated\s+(.+)'),
    re.compile(r'^\s*npm warn\s+(.+)'),
    re.compile(r'^\s*\[notice\]\s+(.+)'),
    re.compile(r'^\s*\[[\d:+]+\]\s*WARNING:\s+(.+)'),
    re.compile(r'^\s*DEPRECATION:\s+(.+)'),
    re.compile(r'^\s*Deprecation Notice:\s+(.+)'),
    re.compile(r'^\s*Deprecated:\s+(.+)'),
]

# Important milestone lines (always shown in summary)
_MILESTONE_PATTERNS = [
    re.compile(r'^\s*(Detected following platforms:)'),
    re.compile(r'^\s*(python|nodejs|dotnet|java|php|ruby):\s*[\d.]+', re.IGNORECASE),
    re.compile(r'^\s*(Detected the following frameworks:)'),
    re.compile(r'^\s*(Running pip install)'),
    re.compile(r"^\s*(Running 'npm install')"),
    re.compile(r"^\s*(Running 'yarn install')"),
    re.compile(r'^\s*(pip install done in)'),
    re.compile(r'^\s*(Running build script)'),
    re.compile(r'^\s*(Build script snippets done in)'),
    re.compile(r'^\s*(Preparing output)'),
    re.compile(r'^\s*(Compressing content)'),
    re.compile(r'^\s*(Using \w+ for compression)'),
    re.compile(r'^\s*(Compression with .* done in)'),
    re.compile(r'^\s*(Copying files to destination)'),
    re.compile(r'^\s*(Copying to destination directory done in)'),
    re.compile(r'^\s*(Total execution done in)'),
    re.compile(r'^\s*(Platform installation done in)'),
    re.compile(r'^\s*(Installing platform)'),
    re.compile(r'^\s*(Downloading and extracting)'),
    re.compile(r'^\s*(Successfully extracted)'),
    re.compile(r'^\s*(Using Node version:)'),
    re.compile(r'^\s*(Using Npm version:)'),
    re.compile(r'^\s*v\d+\.\d+\.\d+$'),  # version number lines like v24.15.0
    re.compile(r'^\s*\d+\.\d+\.\d+$'),    # version number lines like 11.12.1
    re.compile(r'^\s*(Python Version:)'),
    re.compile(r'^\s*(Python Virtual Environment:)'),
    re.compile(r'^\s*(Creating virtual environment)'),
    re.compile(r'^\s*(Activating virtual environment)'),
    re.compile(r'^\s*(Source directory)'),
    re.compile(r'^\s*(Destination directory)'),
    re.compile(r'^\s*(Running oryx build)'),
    re.compile(r'^\s*(Command:)'),
    re.compile(r'^\s*(Running post deployment command)'),
    re.compile(r'^\s*(Deployment successful)'),
    # PHP/Composer milestones
    re.compile(r"^\s*(Running 'composer install)"),
    re.compile(r'^\s*(PHP executable:)'),
    re.compile(r'^\s*(Composer archive:)'),
    # .NET milestones
    re.compile(r'^\s*(Using \.NET Core SDK Version:)'),
    re.compile(r'^\s*(Publishing to directory)'),
    re.compile(r'^\s*(Restored .+\.csproj)'),
    re.compile(r'^\s*\S+\s*->\s*/home/site/wwwroot'),  # dotnet publish output
]


class BuildLogFormatter:
    """Formats and filters build log output for CLI display."""

    def __init__(self, verbosity=BUILD_LOGS_SUMMARY):
        self.verbosity = verbosity
        self._package_count = 0
        self._warning_count = 0

    def format_log_line(self, line):  # pylint: disable=too-many-return-statements
        """Classify a single log line for display.

        Returns:
            (text, is_persistent): ``text`` is the string to display; ``is_persistent``
                True means keep it permanently on screen (milestones, aggregated
                summaries), False means it is transient build chatter shown on the
                self-overwriting status line.
            None: omit the line entirely (blank lines, or --build-logs none).
        """
        if self.verbosity == BUILD_LOGS_FULL:
            return (line, True)
        if self.verbosity == BUILD_LOGS_NONE:
            return None

        # Summary mode: milestones/aggregates are persistent; everything else (warnings,
        # package chatter, oryx metadata, unknown lines) is transient. Blank lines drop.
        stripped = line.strip()
        if not stripped:
            return None

        # Warnings (incl. "npm warn ...") are counted, then shown transiently.
        for pattern in _WARNING_PATTERNS:
            if pattern.match(stripped):
                self._warning_count += 1
                return (line, False)

        # pip "Collecting <pkg>": count for the install summary, then scroll transiently.
        if _PIP_COLLECTING.match(stripped):
            self._package_count += 1
            return (line, False)

        if _PIP_CACHED.match(stripped) or _PIP_INSTALLING.match(stripped):
            return (line, False)

        # "Successfully installed ..." -> aggregated persistent milestone.
        pip_installed_match = _PIP_INSTALLED.match(stripped)
        if pip_installed_match:
            pkg_list = pip_installed_match.group(1)
            count = len(pkg_list.split())
            result = self._emit_package_summary(count)
            self._package_count = 0
            return (result, True)

        # npm "added N packages" -> aggregated persistent milestone.
        npm_match = _NPM_ADDED.match(stripped)
        if npm_match:
            count = int(npm_match.group(1))
            return (f"            Installed {count} packages\n", True)

        # Deterministic milestones -> persistent.
        for pattern in _MILESTONE_PATTERNS:
            if pattern.match(stripped):
                return (line, True)

        # Everything else is build chatter -> transient rolling window.
        return (line, False)

    def _emit_package_summary(self, installed_count):
        """Generate summary line for package installation."""
        count = installed_count if installed_count > 0 else self._package_count
        return f"            Installed {count} packages successfully\n"

    def get_warning_summary(self):
        """Get aggregated warning summary. Call at end of build phase."""
        if self._warning_count > 0:
            return f"            [!] {self._warning_count} warning(s)\n"
        return None


class BuildLogRenderer:
    """Render build logs as persistent milestones plus one self-overwriting status line.

    Milestones and phase headers are printed permanently (each on its own line). Ordinary
    build chatter is shown on a single transient line that overwrites itself in place as new
    chatter arrives -- like a progress/status line. Only a carriage return + clear-to-end-of-
    line are used (no vertical cursor movement), so the display cannot desync even for very
    long or very rapid output; each transient line is also truncated to the terminal width so
    it never wraps.

    On a non-TTY -- or when interactive rendering is disabled (``--build-logs full``) -- there
    is no overwriting: persistent and transient lines are all printed plainly so nothing is
    lost. All output goes to a single stream (stdout by default); callers must route every
    build-phase line through this renderer so no other writer corrupts the status line.
    """

    _DIM = "\x1b[90m"
    _RESET = "\x1b[0m"
    _CLEAR_LINE = "\r\x1b[2K"
    _TRANSIENT_INDENT = "            "  # align the moving line under detail milestones
    _PACE_SECONDS = 0.1  # small per-line delay so a batched reveal "streams" in (TTY only)

    def __init__(self, stream=None, interactive=None):
        if interactive is None:
            probe = stream if stream is not None else sys.stdout
            try:
                interactive = bool(probe.isatty())
            except Exception:  # pylint: disable=broad-except
                interactive = False
        self._interactive = interactive
        # On legacy Windows consoles colorama makes the ANSI escapes work; only needed
        # when we own the real stdout (tests pass a StringIO and don't need it).
        if self._interactive and stream is None:
            try:
                import colorama
                if hasattr(colorama, 'just_fix_windows_console'):
                    colorama.just_fix_windows_console()
                else:
                    colorama.init()
            except Exception:  # pylint: disable=broad-except
                pass
        self._stream = stream if stream is not None else sys.stdout
        # True while a transient status line is on screen without a trailing newline.
        self._active = False

    def _width(self):
        try:
            return shutil.get_terminal_size((100, 24)).columns
        except Exception:  # pylint: disable=broad-except
            return 100

    def _truncate(self, text):
        # Collapse to a single physical row and clip to the terminal width so the status
        # line never wraps (wrapping would leave stranded rows the clear cannot reach).
        text = text.replace('\r', ' ').replace('\n', ' ').rstrip()
        width = max(self._width() - 1, 20)
        if len(text) > width:
            text = text[:width - 1] + '\u2026'
        return text

    def _clear_active(self):
        if self._active:
            self._stream.write(self._CLEAR_LINE)
            self._active = False

    def emit_persistent(self, text):
        """Print a line that stays on screen permanently (clears any active status line)."""
        text = text.rstrip('\n')
        self._clear_active()
        self._stream.write(text + '\n')
        self._stream.flush()

    def emit_transient(self, text):
        """Show a chatter line on the single self-overwriting status line."""
        if not self._interactive:
            line = text.rstrip('\n')
            if line.strip():
                self._stream.write(line + '\n')
                self._stream.flush()
            return
        line = self._truncate(self._TRANSIENT_INDENT + text)
        if not line.strip():
            return
        self._stream.write(self._CLEAR_LINE + self._DIM + line + self._RESET)
        self._stream.flush()
        self._active = True

    def finalize(self):
        """Erase the active status line, leaving only the persistent lines."""
        self._clear_active()
        self._stream.flush()

    def pace(self):
        """Briefly pause between batched lines so a poll's worth of output streams in
        one-by-one instead of appearing all at once. No-op unless interactive (so
        --build-logs full, CI and piped output stay instant)."""
        if self._interactive and self._PACE_SECONDS:
            time.sleep(self._PACE_SECONDS)


def format_phase_header(label, width=50):
    """Render a phase header with the label centered in a band of dashes.

    e.g. format_phase_header("Build Phase") ->
        "------------------- Build Phase -------------------"
    """
    label = " {} ".format(label.strip())
    if len(label) >= width:
        return label.strip()
    dashes = width - len(label)
    left = dashes // 2
    right = dashes - left
    return ("-" * left) + label + ("-" * right)


def format_final_url(url):
    """Format the final app URL to stand out in terminal output."""
    separator = "-" * 50
    return (
        f"\n{separator}\n"
        f"  Deployment complete!\n"
        f"  App URL: {url}\n"
        f"{separator}\n"
    )


def format_build_failure_with_logs(error_text, log_lines):
    """On build failure, dump the full build logs for debugging, followed by the error."""
    output = []
    output.append("\n-- Build Failed -- Showing full build logs for debugging --\n\n")
    for log_line in log_lines:
        output.append(log_line if log_line.endswith('\n') else log_line + '\n')
    output.append("\n-- End of build logs --\n\n")
    output.append(error_text)
    return "".join(output)
