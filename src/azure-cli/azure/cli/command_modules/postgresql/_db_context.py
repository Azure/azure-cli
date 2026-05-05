# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class DbContext:
    """Database context class for PostgreSQL flexible server operations.

    This class serves as a context container for various database-related configurations,
    factory functions, and clients used throughout PostgreSQL command operations.
    """

    def __init__(self, cmd=None, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 cf_availability=None, cf_private_dns_zone_suffix=None,
                 command_group=None, server_client=None, location=None):
        """
        Initialize DbContext with configuration and factory parameters.

        Args:
            cmd: Azure CLI command context
            azure_sdk: Azure SDK module (e.g., postgresqlflexibleservers)
            logging_name: Name to use for logging (e.g., 'PostgreSQL')
            cf_firewall: Client factory for firewall rules
            cf_db: Client factory for databases
            cf_availability: Client factory for resource availability checks
            cf_private_dns_zone_suffix: Client factory for private DNS zone suffixes
            command_group: The command group name (e.g., 'postgres')
            server_client: The server management client
            location: Azure region location
        """
        self.cmd = cmd
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_availability = cf_availability
        self.cf_private_dns_zone_suffix = cf_private_dns_zone_suffix
        self.logging_name = logging_name
        self.cf_db = cf_db
        self.command_group = command_group
        self.server_client = server_client
        self.location = location
