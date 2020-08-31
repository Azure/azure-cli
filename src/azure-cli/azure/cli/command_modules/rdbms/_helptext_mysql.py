# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['mysql flexible-server'] = """
type: group
short-summary: Manage Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server create'] = """
type: command
short-summary: Creates a new Azure Database for MySQL Flexible Server.
"""

helps['mysql flexible-server list'] = """
type: command
short-summary: Provides a list of Azure Database for MySQL Flexible Server.
"""

helps['mysql flexible-server restore'] = """
type: command
short-summary: Restore a Azure Database for MySQL Flexible Server from the backup.
"""

helps['mysql flexible-server update'] = """
type: command
short-summary: Update a Azure Database for MySQL Flexible Server.
"""

helps['mysql flexible-server db'] = """
type: group
short-summary: Manage database for the Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server firewall-rule'] = """
type: group
short-summary: Manage firewall rules for the Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server parameter'] = """
type: group
short-summary: Manage server parameters for the Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server vnet-rule'] = """
type: group
short-summary: Manage Virtual Network rules for the Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server replica'] = """
type: group
short-summary: Manage replica servers for the Azure Database for MySQL Flexible Servers.
"""
