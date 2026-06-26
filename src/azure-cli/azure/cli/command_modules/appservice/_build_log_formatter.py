# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Build log formatter for `az webapp deploy`.

Renders a curated view of the Oryx build by default: milestones and aggregated package counts
stay on screen, while ordinary chatter is shown on a single self-overwriting status line.
--build-logs full shows verbatim output; --build-logs none hides build logs.
"""

import re
import shutil
import sys
import time


# Log verbosity levels
BUILD_LOGS_FULL = "full"
BUILD_LOGS_SUMMARY = "summary"
BUILD_LOGS_NONE = "none"

# Design: no denylist of "noise". A line is kept permanently only if it matches a milestone
# (or is an aggregated summary); every other non-blank line is transient chatter.

# Patterns for counting packages
_PIP_COLLECTING = re.compile(r'^\s*\[[\d:+]+\]\s*Collecting\s+(\S+)')
_PIP_INSTALLED = re.compile(r'^\s*\[[\d:+]+\]\s*Successfully installed\s+(.*)')
_NPM_ADDED = re.compile(r'^\s*added (\d+) packages')

# Important milestone lines (always shown in summary)
_MILESTONE_PATTERNS = [
    # Generic Oryx build lifecycle (platform-agnostic)
    re.compile(r'^\s*(Detected following platforms:)'),
    re.compile(r'^\s*(python|nodejs|dotnet|php):\s*[\d.]+', re.IGNORECASE),
    re.compile(r'^\s*(Detected the following frameworks:)'),
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
    re.compile(r'^\s*(Source directory)'),
    re.compile(r'^\s*(Destination directory)'),
    re.compile(r'^\s*(Running oryx build)'),
    re.compile(r'^\s*(Command:)'),
    re.compile(r'^\s*(Running post deployment command)'),
    re.compile(r'^\s*(Deployment successful)'),
    re.compile(r'^\s*v\d+\.\d+\.\d+$'),  # version number lines like v24.15.0
    re.compile(r'^\s*\d+\.\d+\.\d+$'),    # version number lines like 11.12.1
    # Node / npm / yarn milestones
    re.compile(r"^\s*(Running 'npm install')"),
    re.compile(r"^\s*(Running 'yarn install')"),
    re.compile(r'^\s*(Using Node version:)'),
    re.compile(r'^\s*(Using Npm version:)'),
    # Python / pip / virtualenv milestones
    re.compile(r'^\s*(Running pip install)'),
    re.compile(r'^\s*(pip install done in)'),
    re.compile(r'^\s*(Python Version:)'),
    re.compile(r'^\s*(Python Virtual Environment:)'),
    re.compile(r'^\s*(Creating virtual environment)'),
    re.compile(r'^\s*(Activating virtual environment)'),
    # PHP / Composer milestones
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

    def format_log_line(self, line):  # pylint: disable=too-many-return-statements
        """Classify a log line: returns (text, is_persistent), or None to omit.

        is_persistent True keeps it on screen (milestones/summaries); False shows it on the
        transient status line. None omits blank lines or --build-logs none.
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

        # pip "Collecting <pkg>": count for the install summary, then scroll transiently.
        if _PIP_COLLECTING.match(stripped):
            self._package_count += 1
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


class BuildLogRenderer:
    """Render build logs as persistent milestones plus one self-overwriting status line.

    Chatter overwrites itself in place via carriage-return + clear-to-EOL (no vertical cursor
    moves), truncated to terminal width so it never wraps. On a non-TTY or --build-logs full,
    lines are printed plainly with no overwriting. All output goes through one stream.
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
        """Briefly pause between batched lines so a poll streams in one-by-one. No-op unless interactive."""
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
    output.append("\n------------------- Full Build Logs -------------------\n\n")
    for log_line in log_lines:
        output.append(log_line if log_line.endswith('\n') else log_line + '\n')
    output.append("\n------------------- End of Build Logs -------------------\n\n")
    output.append(error_text)
    return "".join(output)
