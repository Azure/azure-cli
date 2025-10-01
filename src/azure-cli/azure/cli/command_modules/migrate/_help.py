# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['migrate'] = """
    type: group
    short-summary: Commands to migrate workloads using PowerShell automation.
    long-summary: |
        This command group provides cross-platform migration capabilities by leveraging PowerShell cmdlets
        from within Azure CLI. These commands work on Windows, Linux, and macOS when PowerShell Core is installed.
        Use 'az migrate setup-env' to configure your system for optimal migration operations.
        
        Available command groups:
        - migrate                    : Core migration setup and prerequisite checks
        - migrate server             : Server discovery and replication management
        - migrate local              : Azure Local/Stack HCI migration commands
        - migrate powershell         : PowerShell module management
        - migrate auth               : Azure authentication management
"""
