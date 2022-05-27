# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from azure.cli.command_modules.role import graph_client_factory
from azure.cli.command_modules.role import GraphError

from knack.log import get_logger

logger = get_logger(__name__)


# All methods now return the text based values
# for consistency and hiding implementation details
class AADManager:
    def __init__(self, cli_ctx):
        self.client = graph_client_factory(cli_ctx)

    def create_application(self, display_name):
        request_body = {"displayName": display_name}
        app = self.client.application_create(request_body)
        obj_id = app["id"]
        app_id = app["appId"]
        password = self.add_password(obj_id)
        return app_id, password

    def get_service_principal_id(self, app_id):
        sps = self.client.service_principal_list(f"appId eq '{app_id}'")
        if sps:
            return sps[0]["id"]
        return None

    def get_application_object_id_by_client_id(self, client_id):
        apps = self.client.application_list(f"appId eq '{client_id}'")
        if apps:
            return apps[0]["id"]
        return None

    def create_service_principal(self, app_id):
        max_retries = 3
        retries = 0
        while True:
            try:
                return self.client.service_principal_create({"appId": app_id})["id"]
            except GraphError as ex:
                if retries >= max_retries:
                    raise
                retries += 1
                logger.warning("%s; retry %d of %d", ex, retries, max_retries)
                time.sleep(10)

    def add_password(self, obj_id):
        cred = self.client.application_add_password(obj_id, {})
        return cred["secretText"]