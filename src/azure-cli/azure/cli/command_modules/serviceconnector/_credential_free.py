# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from knack.log import get_logger
from msrestazure.tools import parse_resource_id
from azure.cli.core.extension.operations import _install_deps_for_psycopg2
from azure.cli.core.profiles import ResourceType
from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import random_string
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import ArmTemplateBuilder
from ._utils import run_cli_cmd, generate_random_string
from ._resource_config import (
    SOURCE_RESOURCES_USERTOKEN,
    TARGET_RESOURCES_USERTOKEN,
    RESOURCE
)
# pylint: disable=unused-argument, not-an-iterable, too-many-statements

logger = get_logger(__name__)


def enable_mi_for_db_linker(cmd, source_id, target_id, auth_info, source_type, target_type):
    cli_ctx = cmd.cli_ctx
    # return if connection is not for db mi
    if auth_info['auth_type'] not in {'systemAssignedIdentity'}:
        return
    source_handler = getSourceHandler(source_id, source_type)
    if(source_handler == None):
        return
    target_handler = getTargetHandler(
        cmd, target_id, target_type, auth_info['auth_type'])
    if(target_handler == None):
        return

    # get login user info
    login_user = Profile(cli_ctx=cli_ctx).get_current_account_user()
    # Get login user info
    user_info = run_cli_cmd('az ad user show --id {}'.format(login_user))
    user_object_id = user_info.get('objectId') if user_info.get('objectId') is not None \
        else user_info.get('id')
    if user_object_id is None:
        raise Exception(
            "no object id found for user {}".format(login_user))

    # enable source mi
    identity = source_handler.get_identity()
    object_id = identity.get('principalId')
    identity_info = run_cli_cmd(
        'az ad sp show --id {0}'.format(object_id))
    client_id = identity_info.get('appId')
    identity_name = identity_info.get('displayName')

    # enable target aad authentication and set login user as db aad admin
    target_handler.enable_target_aad_auth()
    target_handler.set_user_admin(login_user, user_object_id)

    # create an aad user in db
    target_handler.create_aad_user(identity_name, client_id)
    return target_handler.get_auth_config()


def getTargetHandler(cmd, target_id, target_type, auth_type):
    if target_type in {RESOURCE.Postgres}:
        return PostgresSingleHandler(cmd, target_id, target_type, auth_type)
    elif target_type in {RESOURCE.PostgresFlexible}:
        return PostgresFlexHandler(cmd, target_id, target_type, auth_type)


class TargetHandler:
    target_id = ""
    target_type = ""
    profile = None
    cmd = None
    tenant_id = ""
    sub = ""
    rg = ""

    auth_type = ""

    def __init__(self, cmd, target_id, target_type, auth_type):
        self.profile = Profile(cli_ctx=cmd.cli_ctx)
        self.cmd = cmd
        self.target_id = target_id
        self.target_type = target_type
        self.tenant_id = Profile(
            cli_ctx=cmd.cli_ctx).get_subscription().get("tenantId")
        target_segments = parse_resource_id(target_id)
        self.sub = target_segments.get('subscription')
        self.rg = target_segments.get('resource_group')
        self.auth_type = auth_type

    def enable_target_aad_auth(self):
        return

    def set_user_admin(self, login_user, user_object_id):
        return

    def set_target_firewall(self):
        return

    def create_aad_user(self):
        return

    def get_auth_config(self):
        return


class PostgresFlexHandler(TargetHandler):
    aad_user = generate_random_string(
        prefix="aad_" + RESOURCE.PostgresFlexible.value + '_')

    db_server = ""
    host = ""
    dbname = ""
    user = ""

    def __init__(self, cmd, target_id, target_type, auth_type):
        super().__init__(cmd, target_id, target_type, auth_type)

        target_segments = parse_resource_id(target_id)
        self.db_server = target_segments.get('name')
        self.host = "{0}.postgres.database.azure.com".format(self.db_server)
        self.dbname = target_segments.get('child_name_1')
        self.user = self.profile.get_current_account_user()

    def enable_target_aad_auth(self):
        logger.warning('Enable service aad authentication')
        server = self.db_server
        master_template = ArmTemplateBuilder()
        master_template.add_resource({
            'type': "Microsoft.DBforPostgreSQL/flexibleServers",
            'apiVersion': '2022-03-08-privatepreview',
            'name': server,
            'location': "East US",
            'properties': {
                    'authConfig': {
                        'activeDirectoryAuthEnabled': True,
                        'tenantId': self.tenant_id
                    },
                'createMode': "Update"
            },
        })

        template = master_template.build()
        # parameters = master_template.build_parameters()

        # deploy ARM template
        cmd = self.cmd
        deployment_name = 'pg_deploy_' + random_string(32)
        client = get_mgmt_service_client(
            cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
        DeploymentProperties = cmd.get_models(
            'DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
        properties = DeploymentProperties(
            template=template, parameters={}, mode='incremental')
        Deployment = cmd.get_models(
            'Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
        deployment = Deployment(properties=properties)

        LongRunningOperation(cmd.cli_ctx)(
            client.begin_create_or_update(self.rg, deployment_name, deployment))

    def set_user_admin(self, login_user, user_object_id):
        logger.warning('Set current user as DB Server AAD Administrators.')
        cmd = self.cmd
        master_template = ArmTemplateBuilder()
        master_template.add_resource({
            'type': "Microsoft.DBforPostgreSQL/flexibleServers/administrators",
            'apiVersion': '2022-03-08-privatepreview',
            'name': self.db_server+"/"+user_object_id,
            'location': "East US",
            'properties': {
                'principalName': login_user,
                'principalType': 'User',
                'tenantId': self.tenant_id,
                'createMode': "Update"
            },
        })

        template = master_template.build()
        # parameters = master_template.build_parameters()

        # deploy ARM template
        deployment_name = 'pg_addAdmins_' + random_string(32)
        client = get_mgmt_service_client(
            cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
        DeploymentProperties = cmd.get_models(
            'DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
        properties = DeploymentProperties(
            template=template, parameters={}, mode='incremental')
        Deployment = cmd.get_models(
            'Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
        deployment = Deployment(properties=properties)

        LongRunningOperation(cmd.cli_ctx)(
            client.begin_create_or_update(self.rg, deployment_name, deployment))

    def create_aad_user(self, identity_name, client_id):
        self.aad_user = identity_name or self.aad_user

        q = self.get_create_query(client_id)
        connection_string = self.get_connection_string()
        ip_name = None
        try:
            logger.warning("Connecting to database...")
            self.create_aad_user_in_pg(connection_string, q)
        except ConnectionFailError as e:
            # allow public access
            ip_name = generate_random_string(prefix='svc_')
            deny_public_access = self.set_target_firewall(True, ip_name)
            # create again
            self.create_aad_user_in_pg(connection_string, q)

        # remove firewall rule
        if ip_name is not None:
            try:
                self.set_target_firewall(False, ip_name)
            # pylint: disable=bare-except
            except:
                pass
                # logger.warning('Please manually delete firewall rule %s to avoid security issue', ipname)

    def create_aad_user_in_pg(self, conn_string, execution_query):
        import pkg_resources
        installed_packages = pkg_resources.working_set
        psy_installed = any(('psycopg2') in d.key.lower()
                            for d in installed_packages)
        if not psy_installed:
            _install_deps_for_psycopg2()
            import pip
            pip.main(['install', 'psycopg2-binary'])

        import psycopg2

        # pylint: disable=protected-access
        try:
            logger.warning("Connecting to database...")
            conn = psycopg2.connect(conn_string)
        except psycopg2.Error as e:
            logger.warning(e)
            raise ConnectionFailError

        conn.autocommit = True
        cursor = conn.cursor()
        try:
            logger.warning(
                "Adding new AAD user %s to database...", self.aad_user)
            cursor.execute(execution_query)
        except psycopg2.Error as e:  # role "aad_user" already exists
            logger.debug(e)
            conn.commit()

        # Clean up
        conn.commit()
        cursor.close()
        conn.close()

    def get_connection_string(self):
        password = run_cli_cmd(
            'az account get-access-token --resource-type oss-rdbms').get('accessToken')
        sslmode = "require"

        conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(
            self.host, self.user, self.dbname, password, sslmode)
        return conn_string

    def get_create_query(self, client_id):
        aad_user = self.aad_user
        role_q = "drop role IF EXISTS \"{}\"; \
            select * from pgaadauth_create_principal_with_oid('{}', '{}', 'ServicePrincipal', false, false);".format(aad_user, aad_user, client_id)
        grant_q = "GRANT ALL PRIVILEGES ON DATABASE {} TO \"{}\"; \
                    GRANT ALL ON ALL TABLES IN SCHEMA public TO \"{}\";".format(self.dbname, aad_user, aad_user)

        return role_q+grant_q

    def get_auth_config(self):
        if(self.auth_type in {'systemAssignedIdentity'}):
            return {
                'auth_type': 'secret',
                'name': self.aad_user,
                'secret_info': {
                    'secret_type': 'rawValue'
                }
            }


class PostgresSingleHandler(PostgresFlexHandler):
    def __init__(self, cmd, target_id, target_type, auth_type):
        super().__init__(cmd, target_id, target_type, auth_type)
        self.user = self.profile.get_current_account_user() + '@' + self.db_server

    def enable_target_aad_auth(self):
        return

    def set_user_admin(self, login_user, user_object_id):
        sub = self.sub
        rg = self.rg
        server = self.db_server
        is_admin = True

        # pylint: disable=not-an-iterable
        admins = run_cli_cmd(
            'az postgres server ad-admin list --ids {}'.format(self.target_id))
        is_admin = any(ad.get('sid') == user_object_id for ad in admins)
        if not is_admin:
            logger.warning('Setting current user as database server AAD admin:'
                           ' user=%s object id=%s', login_user, user_object_id)
            run_cli_cmd('az postgres server ad-admin create -g {} --server-name {} --display-name {} --object-id {}'
                        ' --subscription {}'.format(rg, server, login_user, user_object_id, sub)).get('objectId')

    def set_target_firewall(self, add_new_rule, ip_name, deny_public_access=False):
        sub = self.sub
        rg = self.rg
        server = self.db_server
        target_id = self.target_id
        if add_new_rule:
            target = run_cli_cmd(
                'az postgres server show --ids {}'.format(target_id))
            # logger.warning("Update database server firewall rule to connect...")
            if target.get('publicNetworkAccess') == "Disabled":
                run_cli_cmd(
                    'az postgres server update --public Enabled --ids {}'.format(target_id))
            run_cli_cmd(
                'az postgres server firewall-rule create -g {0} -s {1} -n {2} --subscription {3}'
                ' --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255'.format(
                    rg, server, ip_name, sub)
            )
            return target.get('publicNetworkAccess') == "Disabled"
        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))

    def get_create_query(self, client_id):
        aad_user = self.aad_user
        role_q = "SET aad_validate_oids_in_tenant = off; \
                    drop role IF EXISTS \"{}\"; \
                    CREATE ROLE \"{}\" WITH LOGIN PASSWORD '{}' IN ROLE azure_ad_user;".format(aad_user, aad_user, client_id)
        grant_q = "GRANT ALL PRIVILEGES ON DATABASE {} TO \"{}\"; \
                    GRANT ALL ON ALL TABLES IN SCHEMA public TO \"{}\";".format(self.dbname, aad_user, aad_user)

        return role_q+grant_q


def getSourceHandler(source_id, source_type):
    if source_type in {RESOURCE.WebApp}:
        return WebappHandler(source_id, source_type)
    if source_type in {RESOURCE.ContainerApp}:
        return ContainerappHandler(source_id, source_type)
    elif source_type in {RESOURCE.SpringCloud, RESOURCE.SpringCloudDeprecated}:
        return SpringHandler(source_id, source_type)


class SourceHandler:
    source_id = ""
    source_type = ""

    def __init__(self, source_id, source_type: RESOURCE):
        self.source_id = source_id
        self.source_type = source_type.value

    def get_identity(source_id):
        return


class SpringHandler(SourceHandler):
    def get_identity(self):
        segments = parse_resource_id(self.source_id)
        sub = segments.get('subscription')
        spring = segments.get('name')
        app = segments.get('child_name_1')
        rg = segments.get('resource_group')
        logger.warning(
            'Checking if Spring Cloud app enables System Identity...')
        identity = run_cli_cmd(
            'az {} app show -g {} -s {} -n {} --subscription {}'.format(self.source_type, rg, spring, app, sub)).get('identity')
        if (identity is None or identity.get('type') != "SystemAssigned"):
            # assign system identity for spring-cloud
            logger.warning('Enabling Spring Cloud app System Identity...')
            run_cli_cmd(
                'az {} app identity assign -g {} -s {} -n {} --subscription {}'.format(self.source_type, rg, spring, app, sub))
            cnt = 0
            while (identity is None and cnt < 5):
                identity = run_cli_cmd('az {} app show -g {} -s {} -n {} --subscription {}'
                                       .format(self.source_type, rg, spring, app, sub)).get('identity')
                time.sleep(3)
                cnt += 1
        return identity


class WebappHandler(SourceHandler):
    def get_identity(self):
        logger.warning('Checking if WebApp enables System Identity...')
        identity = run_cli_cmd(
            'az webapp show --ids {}'.format(self.source_id)).get('identity')
        if (identity is None or "SystemAssigned" not in identity.get('type')):
            # assign system identity for spring-cloud
            logger.warning('Enabling WebApp System Identity...')
            run_cli_cmd(
                'az webapp identity assign --ids {}'.format(self.source_id))
            cnt = 0
            while (identity is None and cnt < 5):
                identity = run_cli_cmd(
                    'az webapp identity show --ids {}'.format(self.source_id)).get('identity')
                time.sleep(3)
                cnt += 1
        return identity


class ContainerappHandler(SourceHandler):
    def get_identity(self):
        logger.warning('Checking if Container App enables System Identity...')
        identity = run_cli_cmd(
            'az containerapp show --ids {}'.format(self.source_id)).get('identity')
        if (identity is None or "SystemAssigned" not in identity.get('type')):
            # assign system identity for spring-cloud
            logger.warning('Enabling Container App System Identity...')
            run_cli_cmd(
                'az containerapp identity assign --ids {} --system-assigned'.format(self.source_id))
            cnt = 0
            while (identity is None and cnt < 5):
                identity = run_cli_cmd(
                    'az containerapp identity show --ids {}'.format(self.source_id)).get('identity')
                time.sleep(3)
                cnt += 1
        return identity


class ConnectionFailError(Exception):
    pass
