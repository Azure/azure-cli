#!/usr/bin/env python3
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unified Test Runner for Azure Migrate CLI
Uses the comprehensive test framework with PowerShell mocking.
"""

import sys
import os
from latest.test_framework import run_all_tests

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == '__main__':
    # Run all tests with the unified framework
    success = run_all_tests(
        verbosity=2,
        buffer=True,
        exclude_modules=['test_framework']  # Don't test the framework itself
    )
    
    sys.exit(0 if success else 1)
