# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unit tests for the build log streaming feature:
  - _build_log_formatter.py  (BuildLogFormatter verbosity/filtering, helpers)
  - custom._fetch_kudu_log_entries streaming details-dedup carve-out
"""

import io
import unittest
from unittest.mock import MagicMock, patch

from azure.cli.command_modules.appservice._build_log_formatter import (
    BuildLogFormatter,
    BuildLogRenderer,
    BUILD_LOGS_FULL,
    BUILD_LOGS_SUMMARY,
    BUILD_LOGS_NONE,
    format_final_url,
    format_build_failure_with_logs,
)


def _text(result):
    """Return the rendered text from a (text, persistent) classification."""
    return None if result is None else result[0]


def _is_persistent(result):
    return result is not None and result[1] is True


def _is_transient(result):
    return result is not None and result[1] is False


class TestBuildLogFormatterFullMode(unittest.TestCase):
    def test_full_mode_passes_everything_through(self):
        fmt = BuildLogFormatter(verbosity=BUILD_LOGS_FULL)
        for line in [
            "Oryx Version: 0.2\n",
            "npm warn deprecated something@1.0.0\n",
            "            Collecting flask\n",
            "random build line\n",
            "\n",
        ]:
            result = fmt.format_log_line(line)
            self.assertEqual(_text(result), line)
            self.assertTrue(_is_persistent(result), msg="full mode should be persistent")


class TestBuildLogFormatterNoneMode(unittest.TestCase):
    def test_none_mode_suppresses_everything(self):
        fmt = BuildLogFormatter(verbosity=BUILD_LOGS_NONE)
        for line in ["anything\n", "Running pip install\n", "error: boom\n"]:
            self.assertIsNone(fmt.format_log_line(line))


class TestBuildLogFormatterSummaryMode(unittest.TestCase):
    def setUp(self):
        self.fmt = BuildLogFormatter(verbosity=BUILD_LOGS_SUMMARY)

    def test_blank_lines_suppressed(self):
        self.assertIsNone(self.fmt.format_log_line("   \n"))

    def test_oryx_metadata_is_transient_not_persistent(self):
        # No denylist: oryx/SDK chatter is transient (rolling window), not persistent.
        for line in [
            "Oryx Version: 0.2.20\n",
            "Build Operation ID: abc123\n",
            "Operation performed by Microsoft Oryx\n",
            "-----------------------------\n",
        ]:
            result = self.fmt.format_log_line(line)
            self.assertTrue(_is_transient(result),
                            msg="expected transient for: {}".format(line))

    def test_milestones_are_persistent(self):
        for line in [
            "Running pip install\n",
            "Detected following platforms:\n",
            "Deployment successful\n",
        ]:
            result = self.fmt.format_log_line(line)
            self.assertEqual(_text(result), line)
            self.assertTrue(_is_persistent(result), msg="expected persistent for: {}".format(line))

    def test_unknown_lines_are_transient(self):
        # Unknown lines, npm warnings and pip notices all fall through to the transient path.
        for line in [
            "ModuleNotFoundError: No module named 'foo'\n",
            "npm warn deprecated a@1\n",
            "[notice] A new release of pip\n",
        ]:
            result = self.fmt.format_log_line(line)
            self.assertTrue(_is_transient(result), msg="expected transient for: {}".format(line))

    def test_pip_collecting_lines_are_transient(self):
        self.assertTrue(_is_transient(self.fmt.format_log_line("[12:00:00+00:00] Collecting flask\n")))
        self.assertTrue(_is_transient(self.fmt.format_log_line("[12:00:01+00:00] Using cached flask.whl\n")))

    def test_pip_successfully_installed_emits_aggregated_persistent_summary(self):
        # Collecting lines are transient/counted, then the final line is aggregated persistent.
        self.fmt.format_log_line("[12:00:00+00:00] Collecting flask\n")
        self.fmt.format_log_line("[12:00:01+00:00] Collecting jinja2\n")
        result = self.fmt.format_log_line(
            "[12:00:05+00:00] Successfully installed flask-3.0 jinja2-3.1 click-8.1\n")
        self.assertTrue(_is_persistent(result))
        self.assertIn("Installed 3 packages", _text(result))
        # The raw "Successfully installed ..." text must not be the returned value.
        self.assertNotIn("Successfully installed flask-3.0", _text(result))

    def test_npm_added_packages_aggregated_persistent(self):
        result = self.fmt.format_log_line("added 145 packages in 12s\n")
        self.assertTrue(_is_persistent(result))
        self.assertIn("Installed 145 packages", _text(result))


class TestBuildLogRenderer(unittest.TestCase):
    """The single self-overwriting status-line renderer."""

    def _renderer(self):
        buf = io.StringIO()
        return buf, BuildLogRenderer(stream=buf, interactive=True)

    def test_non_interactive_writes_plain_lines(self):
        buf = io.StringIO()
        r = BuildLogRenderer(stream=buf, interactive=False)
        r.emit_persistent("milestone")
        r.emit_transient("chatter")
        out = buf.getvalue()
        self.assertIn("milestone\n", out)
        # With no overwriting, transient lines are written plainly too (honest fallback).
        self.assertIn("chatter\n", out)

    def test_transient_overwrites_in_place(self):
        buf, r = self._renderer()
        r.emit_transient("first")
        r.emit_transient("second")
        out = buf.getvalue()
        # Both writes use carriage-return + clear-line and stay on one row (no '\n').
        self.assertIn("\r\x1b[2K", out)
        self.assertIn("first", out)
        self.assertIn("second", out)
        self.assertNotIn("\n", out)
        self.assertTrue(r._active)

    def test_persistent_clears_active_transient(self):
        buf, r = self._renderer()
        r.emit_transient("noise")
        r.emit_persistent("MILESTONE")
        out = buf.getvalue()
        # The active status line is cleared, then the milestone is printed on its own row.
        self.assertIn("MILESTONE\n", out)
        self.assertFalse(r._active)

    def test_finalize_clears_active_line(self):
        buf, r = self._renderer()
        r.emit_transient("a")
        self.assertTrue(r._active)
        r.finalize()
        self.assertFalse(r._active)
        # A clear-line sequence is emitted so the transient text is wiped.
        self.assertIn("\r\x1b[2K", buf.getvalue())

    def test_empty_transient_ignored(self):
        buf, r = self._renderer()
        r.emit_transient("   ")
        self.assertFalse(r._active)

    def test_long_transient_line_truncated_to_single_row(self):
        # A line far longer than the terminal width must be clipped to a single physical
        # row so it never wraps (a wrapped line cannot be fully cleared in place).
        buf, r = self._renderer()
        r.emit_transient("x" * 5000)
        out = buf.getvalue()
        self.assertNotIn("x" * 5000, out)   # clipped well below the raw length
        self.assertIn("\u2026", out)         # ellipsis marker present
        self.assertNotIn("\n", out)          # stays on one row

    def test_non_tty_stream_auto_disables_interactive(self):
        # A StringIO is not a TTY, so auto-detection must disable interactive rendering.
        r = BuildLogRenderer(stream=io.StringIO())
        self.assertFalse(r._interactive)

    def test_pace_is_noop_when_not_interactive(self):
        r = BuildLogRenderer(stream=io.StringIO(), interactive=False)
        with patch("azure.cli.command_modules.appservice._build_log_formatter.time.sleep") as slept:
            r.pace()
            slept.assert_not_called()

    def test_pace_sleeps_when_interactive(self):
        r = BuildLogRenderer(stream=io.StringIO(), interactive=True)
        with patch("azure.cli.command_modules.appservice._build_log_formatter.time.sleep") as slept:
            r.pace()
            slept.assert_called_once()


class TestBuildLogFormatterHelpers(unittest.TestCase):
    def test_format_final_url_contains_url(self):
        out = format_final_url("https://myapp.azurewebsites.net")
        self.assertIn("https://myapp.azurewebsites.net", out)
        self.assertIn("Deployment complete!", out)

    def test_format_build_failure_with_logs_includes_logs_and_error(self):
        out = format_build_failure_with_logs(
            "Deployment failed because the build process failed\n",
            ["line one\n", "line two"])  # second line intentionally lacks newline
        self.assertIn("Full Build Logs", out)
        self.assertIn("line one", out)
        self.assertIn("line two", out)
        self.assertIn("Deployment failed because the build process failed", out)

    def test_format_build_failure_with_empty_logs(self):
        out = format_build_failure_with_logs("err\n", [])
        self.assertIn("err", out)


class TestFetchKuduLogEntriesDedup(unittest.TestCase):
    """Validate the streaming details-dedup carve-out in _fetch_kudu_log_entries.

    Completed (non-tail) entries must have their details fetched exactly once; the in-progress
    tail entry must be re-fetched every poll; and no detail lines may be lost.
    """

    def _run_poll_sequence(self):
        from azure.cli.command_modules.appservice import custom as m

        # Simulated server state across three polls. The deployment-log list grows, and the
        # tail entry's details accumulate new lines each poll.
        polls = [
            {"list": [{"id": "A", "log_time": "t0", "message": "A", "details_url": "d/A"}],
             "details": {"d/A": [{"id": "a1", "log_time": "t0", "message": "a1"}]}},
            {"list": [{"id": "A", "log_time": "t0", "message": "A", "details_url": "d/A"},
                      {"id": "B", "log_time": "t1", "message": "B", "details_url": "d/B"}],
             "details": {"d/A": [{"id": "a1", "log_time": "t0", "message": "a1"},
                                 {"id": "a2", "log_time": "t0", "message": "a2"}],
                         "d/B": [{"id": "b1", "log_time": "t1", "message": "b1"}]}},
            {"list": [{"id": "A", "log_time": "t0", "message": "A", "details_url": "d/A"},
                      {"id": "B", "log_time": "t1", "message": "B", "details_url": "d/B"},
                      {"id": "C", "log_time": "t2", "message": "C", "details_url": "d/C"}],
             "details": {"d/A": [{"id": "a1", "log_time": "t0", "message": "a1"},
                                 {"id": "a2", "log_time": "t0", "message": "a2"}],
                         "d/B": [{"id": "b1", "log_time": "t1", "message": "b1"},
                                 {"id": "b2", "log_time": "t1", "message": "b2"}],
                         "d/C": [{"id": "c1", "log_time": "t2", "message": "c1"}]}},
        ]
        state = {"poll": 0}
        detail_calls = []

        class FakeResp:
            def __init__(self, data):
                self._d = data
                self.status_code = 200

            def json(self):
                return self._d

        def fake_get(url, **kwargs):
            cur = polls[state["poll"]]
            if url.endswith("/log"):
                return FakeResp(cur["list"])
            detail_calls.append((state["poll"], url))
            return FakeResp(cur["details"][url])

        seen_details = []
        details_complete_ids = set()
        with patch("requests.get", side_effect=fake_get), \
                patch.object(m, "get_scm_site_headers", return_value={}), \
                patch.object(m, "_get_scm_url", return_value="https://scm"), \
                patch.object(m, "should_disable_connection_verify", return_value=True, create=True):
            for p in range(3):
                state["poll"] = p
                entries = m._fetch_kudu_log_entries(
                    MagicMock(), "rg", "app", None, "depid",
                    details_complete_ids=details_complete_ids)
                for _msg, _lt, _eid, ditems in entries:
                    for dmsg, _dt, did in ditems:
                        seen_details.append(did)
        return detail_calls, seen_details

    def test_completed_entries_fetched_once_tail_always(self):
        detail_calls, _ = self._run_poll_sequence()
        # A is the tail at poll 0 (fetched), becomes final at poll 1 (fetched once more), then
        # must be skipped at poll 2.
        self.assertEqual(detail_calls.count((0, "d/A")), 1)
        self.assertEqual(detail_calls.count((1, "d/A")), 1)
        self.assertEqual(detail_calls.count((2, "d/A")), 0)
        # B becomes final at poll 2.
        self.assertEqual(detail_calls.count((1, "d/B")), 1)
        self.assertEqual(detail_calls.count((2, "d/B")), 1)
        # C is the tail at poll 2.
        self.assertEqual(detail_calls.count((2, "d/C")), 1)

    def test_no_detail_lines_lost(self):
        _, seen_details = self._run_poll_sequence()
        for did in ("a1", "a2", "b1", "b2", "c1"):
            self.assertIn(did, seen_details)

    def test_default_fetches_all_details_every_call(self):
        # Without details_complete_ids (failure-path full fetch), every entry is fetched.
        from azure.cli.command_modules.appservice import custom as m

        entries_list = [{"id": "A", "log_time": "t0", "message": "A", "details_url": "d/A"},
                        {"id": "B", "log_time": "t1", "message": "B", "details_url": "d/B"}]
        details = {"d/A": [{"id": "a1", "log_time": "t0", "message": "a1"}],
                   "d/B": [{"id": "b1", "log_time": "t1", "message": "b1"}]}
        detail_calls = []

        class FakeResp:
            def __init__(self, data):
                self._d = data
                self.status_code = 200

            def json(self):
                return self._d

        def fake_get(url, **kwargs):
            if url.endswith("/log"):
                return FakeResp(entries_list)
            detail_calls.append(url)
            return FakeResp(details[url])

        with patch("requests.get", side_effect=fake_get), \
                patch.object(m, "get_scm_site_headers", return_value={}), \
                patch.object(m, "_get_scm_url", return_value="https://scm"), \
                patch.object(m, "should_disable_connection_verify", return_value=True, create=True):
            for _ in range(2):
                m._fetch_kudu_log_entries(MagicMock(), "rg", "app", None, "depid")
        # Both polls fetch both entries' details (no dedup when set not provided).
        self.assertEqual(detail_calls.count("d/A"), 2)
        self.assertEqual(detail_calls.count("d/B"), 2)


if __name__ == "__main__":
    unittest.main()
