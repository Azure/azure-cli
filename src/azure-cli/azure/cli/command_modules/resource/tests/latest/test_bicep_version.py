# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import semver

from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.resource._bicep_version import parse_bicep_version_constraint


class TestBicepVersionConstraint(unittest.TestCase):
    def test_numeric_version_components_match_bicep_core(self):
        # Cases from Bicep.Core's SemanticVersionTests, exercised through our parser.
        cases = (
            ("1.2.3", (1, 2, 3)),
            ("0.0.0", (0, 0, 0)),
            ("0.47.12", (0, 47, 12)),
            ("1.2", (1, 2, 0)),
            ("1", (1, 0, 0)),
            ("0", (0, 0, 0)),
            ("10.200.3000", (10, 200, 3000)),
            ("2147483647.0.0", (2147483647, 0, 0)),
            ("0.2147483647.0", (0, 2147483647, 0)),
            ("0.0.2147483647", (0, 0, 2147483647)),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                constraint = parse_bicep_version_constraint(value)
                version = constraint.lower_bound
                self.assertEqual(expected, (version.major, version.minor, version.patch))
                self.assertEqual(version, constraint.upper_bound)
                self.assertTrue(constraint.is_satisfied_by(semver.VersionInfo(*expected)))

    def test_semver_numeric_ordering_matches_bicep_core(self):
        cases = (
            ("1.2.3", "1.2.3", 0),
            ("2.0.0", "1.99.99", 1),
            ("1.99.99", "2.0.0", -1),
            ("1.3.0", "1.2.99", 1),
            ("1.2.99", "1.3.0", -1),
            ("1.2.4", "1.2.3", 1),
            ("1.2.3", "1.2.4", -1),
            ("1.10.0", "1.9.0", 1),
            ("0.47.12", "0.47.2", 1),
            ("1.2", "1.2.0", 0),
            ("1", "1.0.0", 0),
            ("0", "0.0.0", 0),
            ("0.0.0", "0.0.1", -1),
            ("2147483647.0.0", "2147483646.2147483647.2147483647", 1),
            ("0.2147483647.2147483647", "1.0.0", -1),
            ("0.0.2147483647", "0.1.0", -1),
        )
        for left, right, expected_sign in cases:
            with self.subTest(left=left, right=right):
                candidate = parse_bicep_version_constraint(left).lower_bound
                bound = parse_bicep_version_constraint(right).lower_bound
                comparison = candidate.compare(bound)
                self.assertEqual(expected_sign, (comparison > 0) - (comparison < 0))
                for operator, expected in (
                        ("=", expected_sign == 0), (">", expected_sign > 0), (">=", expected_sign >= 0),
                        ("<", expected_sign < 0), ("<=", expected_sign <= 0)):
                    with self.subTest(operator=operator):
                        constraint = parse_bicep_version_constraint(f"{operator}{right}")
                        self.assertEqual(expected, constraint.is_satisfied_by(candidate))

    def test_parse_and_normalize_supported_constraints(self):
        cases = (
            ("1.2.3", "1.2.3"),
            ("=0.31.0", "0.31.0"),
            ("1", "1.0.0"),
            ("1.2", "1.2.0"),
            ("0", "0.0.0"),
            (">=1", ">=1.0.0"),
            (">=1.2", ">=1.2.0"),
            ("<0.31.0", "<0.31.0"),
            (">0.31.0", ">0.31.0"),
            ("<=0.31.0", "<=0.31.0"),
            (">=1.2.3, <=1.2.3", "1.2.3"),
            (">=0.31.0,<1.0.0", ">=0.31.0, <1.0.0"),
            ("   >=  0.31.0   ,   < 1.0.0   ", ">=0.31.0, <1.0.0"),
            ("<1.0.0, >=0.31.0", ">=0.31.0, <1.0.0"),
            (">0.31.0, <=1.0.0", ">0.31.0, <=1.0.0"),
            ("\t>=1,\n<2\r\n", ">=1.0.0, <2.0.0"),
            ("2147483647.2147483647.2147483647", "2147483647.2147483647.2147483647"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(expected, str(parse_bicep_version_constraint(value)))

    def test_reject_unsupported_or_malformed_constraints(self):
        cases = (
            "", "   ", "whatever", ">=", ">", "=", "1.2.3.4", "1.", "1..2", ".1.2", "1.2.",
            "-1.2.3", "+1.2.3", "01.2.3", "1.02.3", "1.2.03", "١.٢.٣",
            "v1.2.3", "V1.2.3", ">=v1.0.0, <v2.0.0",
            "1.2.3-preview", ">=1.0.0-rc.1", "1.2.3+abc123", "1.2.3-rc.1+abc123",
            "(>=1.0.0, <2.0.0)", "^1.0.0", "~1.0.0", "1.x", "*", "1.*",
            "=>1.2.3", "==1.2.3", "!=1.2.3", "> =1.2.3", "1. 2.3",
            ">=1.0.0 <2.0.0", "1.0.0 - 2.0.0", "1.0.0 || 2.0.0", "[1.0.0,2.0.0)",
            ">=1.0.0, <2.0.0, <3.0.0", ">=1.0.0,", ",<2.0.0", ",",
            ">=1.0.0, >=2.0.0", "<1.0.0, <2.0.0", "=1.0.0, <2.0.0", "1.0.0, 2.0.0",
            ">=1.0.0, =1.0.0", "<2.0.0, =1.0.0",
            "2147483648.0.0", "0.2147483648.0", "0.0.2147483648",
            ">=2147483648.0.0", ">=0.2147483648.0", ">=0.0.2147483648",
            "<=2147483648.0.0", "<=0.2147483648.0", "<=0.0.2147483648",
            "99999999999999999999.0.0", "9" * 5000,
        )
        for value in cases:
            with self.subTest(value=value[:100]):
                with self.assertRaisesRegex(ValidationError, "bicep.version"):
                    parse_bicep_version_constraint(value)

    def test_evaluate_versions_with_numeric_order_and_inclusive_exclusive_bounds(self):
        cases = (
            (">=0.31.0", "0.31.0", True),
            (">=0.31.0", "0.31.1", True),
            (">=0.31.0", "0.30.9", False),
            (">0.31.0", "0.31.0", False),
            ("<0.31.0", "0.30.0", True),
            ("<0.31.0", "0.31.0", False),
            ("<=0.31.0", "0.31.0", True),
            ("0.31.0", "0.31.0", True),
            ("0.31.0", "0.31.1", False),
            ("=0.31.0", "0.31.0", True),
            ("1.2", "1.2.0", True),
            ("1.2", "1.2.5", False),
            (">=1", "1.0.0", True),
            (">=1", "0.9.9", False),
            (">=0.31.0, <1.0.0", "0.31.0", True),
            (">=0.31.0, <1.0.0", "0.99.99", True),
            (">=0.31.0, <1.0.0", "1.0.0", False),
            (">=0.31.0, <1.0.0", "0.30.0", False),
            ("<=1, >0.31", "1.0.0", True),
            ("<=1, >0.31", "0.31.0", False),
            (">=1.9", "1.10.0", True),
            (">=1.0", "0.99.99", False),
            (">=2, <1", "1.5.0", False),
            (">1.2.3, <1.2.4", "1.2.4", False),
        )
        for constraint, version, expected in cases:
            with self.subTest(constraint=constraint, version=version):
                parsed = parse_bicep_version_constraint(constraint)
                self.assertEqual(expected, parsed.is_satisfied_by(semver.VersionInfo.parse(version)))

    def test_unsatisfiable_ranges_parse_without_becoming_syntax_errors(self):
        cases = (
            ("1.0.0", True), (">=1.0.0", True), (">=1, <2", True),
            (">=1, <=1", True), (">=2, <1", False), (">=1, <1", False), (">1, <=1", False),
            (">=1.0.0, <1.0.1", True), (">1.0.0, <1.0.2", True),
            (">1.2.3, <1.2.4", False), (">1.2.4, <1.2.5", False),
            (">1.2.2147483647, <1.3.1", True),
        )
        for constraint, expected in cases:
            with self.subTest(constraint=constraint):
                self.assertEqual(expected, parse_bicep_version_constraint(constraint).is_satisfiable)

    def test_exact_constraints_are_distinguished_from_open_ranges(self):
        for constraint, expected in (
                ("1.2.3", True), ("=1.2.3", True), (">=1.2.3, <=1.2.3", True),
                (">=1.2.3", False), ("<=1.2.3", False), (">=1, <2", False), (">1, <1", False)):
            with self.subTest(constraint=constraint):
                self.assertEqual(expected, parse_bicep_version_constraint(constraint).is_exact_version)

    def test_prerelease_and_metadata_versions_do_not_match_numeric_constraints(self):
        constraint = parse_bicep_version_constraint(">=0")
        for version in ("1.2.3-preview", "1.2.3+metadata"):
            with self.subTest(version=version):
                self.assertFalse(constraint.is_satisfied_by(semver.VersionInfo.parse(version)))
