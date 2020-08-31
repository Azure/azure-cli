# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines


helps['postgres flexible-server'] = """
type: group
short-summary: Manage Azure Database for PostgreSQL Flexible Servers.
"""

helps['postgres flexible-server create'] = """
type: command
short-summary: Creates a new Azure Database for PostgreSQL Flexible Server.
"""

helps['postgres flexible-server list'] = """
type: command
short-summary: Provides a list of Azure Database for PostgreSQL Flexible Server.
"""

helps['postgres flexible-server restore'] = """
type: command
short-summary: Restore a Azure Database for PostgreSQL Flexible Server from the backup.
"""

helps['postgres flexible-server update'] = """
type: command
short-summary: Update a Azure Database for PostgreSQL Flexible Server.
"""

helps['postgres flexible-server firewall-rule'] = """
type: group
short-summary: Manage firewall rules for the Azure Database for PostgreSQL Flexible Servers.
"""

helps['postgres flexible-server parameter'] = """
type: group
short-summary: Manage server parameters for the Azure Database for PostgreSQL Flexible Servers.
"""

helps['postgres flexible-server vnet-rule'] = """
type: group
short-summary: Manage Virtual Network rules for the Azure Database for PostgreSQL Flexible Servers.
"""
