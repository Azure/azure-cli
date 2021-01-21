# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import time
import uuid

from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import configure_common_settings
from azure.graphrbac import GraphRbacManagementClient
from azure.graphrbac.models import ApplicationCreateParameters
from azure.graphrbac.models import GraphErrorException
from azure.graphrbac.models import PasswordCredential
from azure.graphrbac.models import ServicePrincipalCreateParameters
from knack.log import get_logger

logger = get_logger(__name__)


class AADManager:
    MANAGED_APP_PREFIX = 'https://az.aro.azure.com/'

    def __init__(self, cli_ctx):
        profile = Profile(cli_ctx=cli_ctx)
        credentials, _, tenant_id = profile.get_login_credentials(
            resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
        self.client = GraphRbacManagementClient(
            credentials, tenant_id, base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
        configure_common_settings(cli_ctx, self.client)

    def create_application(self, display_name):
        password = uuid.uuid4()

        try:
            end_date = datetime.datetime(2299, 12, 31, tzinfo=datetime.timezone.utc)
        except AttributeError:
            end_date = datetime.datetime(2299, 12, 31)

        app = self.client.applications.create(ApplicationCreateParameters(
            display_name=display_name,
            identifier_uris=[
                self.MANAGED_APP_PREFIX + str(uuid.uuid4()),
            ],
            password_credentials=[
                PasswordCredential(
                    end_date=end_date,
                    value=password,
                ),
            ],
        ))

        return app, password

    def get_service_principal(self, app_id):
        sps = list(self.client.service_principals.list(
            filter="appId eq '%s'" % app_id))
        if sps:
            return sps[0]
        return None

    def create_service_principal(self, app_id):
        max_retries = 3
        retries = 0
        while True:
            try:
                return self.client.service_principals.create(
                    ServicePrincipalCreateParameters(app_id=app_id))
            except GraphErrorException as ex:
                if retries >= max_retries:
                    raise
                retries += 1
                logger.warning("%s; retry %d of %d", ex, retries, max_retries)
                time.sleep(10)
