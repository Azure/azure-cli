#pylint: disable=unused-import
import argparse

from azure.mgmt.web import WebSiteManagementClient, WebSiteManagementClientConfiguration

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, patch_aliases
from azure.cli.commands._command_creation import get_mgmt_service_client

# FACTORIES

def _web_client_factory(**_):
    return get_mgmt_service_client(WebSiteManagementClient, WebSiteManagementClientConfiguration)
