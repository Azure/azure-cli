# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Build log formatter for `az webapp deploy` / `az functionapp deploy`.

Provides intelligent log filtering that shows a clean summary by default,
with full verbosity available via --build-logs full.

Log levels:
  - PHASE:   Major deployment phases (always shown)
  - INFO:    Important milestones (shown in summary + full)
  - DETAIL:  Individual package lines, SDK metadata (shown only in full)
  - WARNING: Deprecation notices, pip warnings (aggregated in summary, shown in full)
"""

import re


# Log verbosity levels
BUILD_LOGS_FULL = "full"
BUILD_LOGS_SUMMARY = "summary"
BUILD_LOGS_NONE = "none"

# --- Patterns for classification ---

# Oryx internal metadata lines (hidden in summary mode)
_ORYX_METADATA_PATTERNS = [
    re.compile(r'^\s*(Operation performed by Microsoft Oryx)'),
    re.compile(r'^\s*(You can report issues at)'),
    re.compile(r'^\s*(Oryx Version:)'),
    re.compile(r'^\s*(Build Operation ID:)'),
    re.compile(r'^\s*(Repository Commit\s*:)'),
    re.compile(r'^\s*(OS Type\s*:)'),
    re.compile(r'^\s*(Image Type\s*:)'),
    re.compile(r'^\s*(Primary SDK Storage URL:)'),
    re.compile(r'^\s*(Backup SDK Storage URL:)'),
    re.compile(r'^\s*(ACR SDK Registry URL:)'),
    re.compile(r'^\s*(SDK provider status:)'),
    re.compile(r'^\s*(External ACR SDK provider)'),
    re.compile(r'^\s*(External SDK provider)'),
    re.compile(r'^\s*(Direct ACR SDK provider)'),
    re.compile(r'^\s*(Blob SDK provider)'),
    re.compile(r'^\s*(External ACR provider resolved)'),
    re.compile(r'^\s*(Version resolved using)'),
    re.compile(r'^\s*(Requesting SDK from ACR)'),
    re.compile(r'^\s*(Successfully pulled SDK from ACR)'),
    re.compile(r'^\s*(SDK for .* fetched via)'),
    re.compile(r'^\s*(Requesting metadata for platform)'),
    re.compile(r'^\s*(Not a vso image)'),
    re.compile(r'^\s*(Creating directory for command manifest)'),
    re.compile(r'^\s*(Removing existing manifest file)'),
    re.compile(r'^\s*(Creating a manifest file)'),
    re.compile(r'^\s*(Manifest file created)'),
    re.compile(r'^\s*(Copying \.ostype)'),
    re.compile(r'^\s*(Node Build Command Manifest)'),
    # .NET first-run banner (noisy, not useful for deployment)
    re.compile(r'^\s*(Welcome to \.NET)'),
    re.compile(r'^\s*-{5,}$'),  # separator lines like "---------------------"
    re.compile(r'^\s*(SDK Version:)'),
    re.compile(r'^\s*(Telemetry)$'),
    re.compile(r'^\s*(The \.NET tools collect usage data)'),
    re.compile(r'^\s*(Read more about \.NET CLI Tools telemetry)'),
    re.compile(r'^\s*(Installed an ASP\.NET Core HTTPS)'),
    re.compile(r'^\s*(To trust the certificate)'),
    re.compile(r'^\s*(Learn about HTTPS)'),
    re.compile(r'^\s*(Write your first app)'),
    re.compile(r'^\s*(Find out what.s new)'),
    re.compile(r'^\s*(Explore documentation)'),
    re.compile(r'^\s*(Report issues and find source)'),
    re.compile(r'^\s*(Use .dotnet --help.)'),
    re.compile(r'^\s*={5,}$'),  # separator lines like "==================="
    # Kudu internal deployment metadata
    re.compile(r'^\s*(PreDeployment:)'),
    re.compile(r'^\s*(Repository path is)'),
    re.compile(r'^\s*(Using standard output preparation)'),
    re.compile(r'^\s*(Total time for destination directory preparation)'),
    # Kudu build summary noise (0 errors/warnings not useful on success)
    re.compile(r'^\s*(Found \d+ issue)'),
    re.compile(r'^\s*(Build Summary)'),
    re.compile(r'^\s*(Errors \(\d+\))'),
    re.compile(r'^\s*(Warnings \(\d+\))'),
    re.compile(r'^\s*(Parsing the build logs)'),
    re.compile(r'^\s*(Preparing deployment for commit id)'),
    # Kudu post-build noise
    re.compile(r'^\s*(Updating submodules)'),
    re.compile(r'^\s*(Triggering container recycle)'),
    re.compile(r'^\s*(Generating summary of Oryx build)'),
]

# Package download/cache lines (suppressed, counted instead)
_PACKAGE_LINE_PATTERNS = [
    re.compile(r'^\s*\[[\d:+]+\]\s*(Collecting|Using cached|Downloading|Using)'),
    re.compile(r'^\s*\[[\d:+]+\]\s*(Successfully installed)'),
    re.compile(r'^\s*(npm warn|npm notice)'),
    re.compile(r'^\s*added \d+ packages'),
    re.compile(r'^\s*-\s+(Locking|Installing|Downloading)\s+\S+'),  # composer package ops
    re.compile(r'^\s*\d+/\d+\s*\[[\s=>-]*\]\s*\d+%'),  # composer progress bars (X/Y format)
    re.compile(r'^\s*\d+\s*\[[->=<>\s]*\]'),  # composer progress bars (single number format)
    re.compile(r'^\s*Loading composer repositories'),
    re.compile(r'^\s*(Updating dependencies|Lock file operations:)'),
    re.compile(r'^\s*(Installing dependencies from lock file)'),
    re.compile(r'^\s*(Writing lock file)'),
    re.compile(r'^\s*Package operations:'),
    re.compile(r'^\s*Generating autoload files'),
    re.compile(r'^\s*\d+ package suggestions were added'),
    re.compile(r'^\s*\d+ package you are using is looking for funding'),
    re.compile(r'^\s*Use the `composer'),
]

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
        self._packages_collecting = False
        self._packages_installing = False
        self._warning_count = 0
        self._suppressed_lines = []  # stored for auto-expand on failure

    def format_log_line(self, line):
        """Process a single log line and return formatted output or None to suppress.

        Returns:
            str or None: The formatted line to display, or None if suppressed.
        """
        if self.verbosity == BUILD_LOGS_FULL:
            return line
        if self.verbosity == BUILD_LOGS_NONE:
            self._suppressed_lines.append(line)
            return None

        # Summary mode: intelligent filtering
        stripped = line.strip()
        if not stripped:
            return None

        # Check if it's a warning line - aggregate it
        if stripped.startswith('npm warn'):
            self._warning_count += 1
            self._suppressed_lines.append(line)
            return None

        for pattern in _WARNING_PATTERNS:
            if pattern.match(stripped):
                self._warning_count += 1
                self._suppressed_lines.append(line)
                return None

        # Check if it's a package download/install line - count it
        if _PIP_COLLECTING.match(stripped):
            self._package_count += 1
            if not self._packages_collecting:
                self._packages_collecting = True
                self._suppressed_lines.append(line)
                return None
            self._suppressed_lines.append(line)
            return None

        if _PIP_CACHED.match(stripped):
            self._suppressed_lines.append(line)
            return None

        if _PIP_INSTALLING.match(stripped):
            self._packages_installing = True
            self._suppressed_lines.append(line)
            return None

        # "Successfully installed ..." - emit summary instead
        pip_installed_match = _PIP_INSTALLED.match(stripped)
        if pip_installed_match:
            pkg_list = pip_installed_match.group(1)
            count = len(pkg_list.split())
            self._suppressed_lines.append(line)
            result = self._emit_package_summary(count)
            self._packages_collecting = False
            self._packages_installing = False
            self._package_count = 0
            return result

        # npm "added N packages"
        npm_match = _NPM_ADDED.match(stripped)
        if npm_match:
            count = int(npm_match.group(1))
            self._suppressed_lines.append(line)
            return f"            Installed {count} packages\n"

        # Check for Oryx metadata lines - suppress
        for pattern in _ORYX_METADATA_PATTERNS:
            if pattern.match(stripped):
                self._suppressed_lines.append(line)
                return None

        # Check for other package-level detail lines
        for pattern in _PACKAGE_LINE_PATTERNS:
            if pattern.match(stripped):
                self._suppressed_lines.append(line)
                return None

        # Check if it's a milestone line - always show
        for pattern in _MILESTONE_PATTERNS:
            if pattern.match(stripped):
                return line

        # Default: show lines that aren't matched by any suppression pattern
        return line

    def _emit_package_summary(self, installed_count):
        """Generate summary line for package installation."""
        count = installed_count if installed_count > 0 else self._package_count
        return f"            Installed {count} packages successfully\n"

    def get_warning_summary(self):
        """Get aggregated warning summary. Call at end of build phase."""
        if self._warning_count > 0:
            return (f"            [!] {self._warning_count} warning(s) "
                    f"(use --build-logs full to view)\n")
        return None


def format_final_url(url):
    """Format the final app URL to stand out in terminal output."""
    separator = "-" * 50
    return (
        f"\n{separator}\n"
        f"  Deployment complete!\n"
        f"  App URL: {url}\n"
        f"{separator}\n"
    )


def format_build_failure_with_logs(error_text, suppressed_logs):
    """On build failure, auto-expand suppressed logs for debugging."""
    output = []
    output.append("\n-- Build Failed -- Showing full build logs for debugging --\n\n")
    for log_line in suppressed_logs:
        output.append(log_line if log_line.endswith('\n') else log_line + '\n')
    output.append("\n-- End of build logs --\n\n")
    output.append(error_text)
    return "".join(output)
