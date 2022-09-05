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
    RESOURCE
)
# pylint: disable=unused-argument, not-an-iterable, too-many-statements, too-few-public-methods, no-self-use, too-many-instance-attributes, line-too-long, c-extension-no-member

logger = get_logger(__name__)


def enable_mi_for_db_linker(cmd, source_id, target_id, auth_info, source_type, target_type):
    cli_ctx = cmd.cli_ctx
    # return if connection is not for db mi
    if auth_info['auth_type'] not in {'systemAssignedIdentity'}:
        return
    source_handler = getSourceHandler(source_id, source_type)
    if source_handler is None:
        return
    target_handler = getTargetHandler(
        cmd, target_id, target_type, auth_info['auth_type'])
    if target_handler is None:
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
    if target_type in {RESOURCE.PostgresFlexible}:
        return PostgresFlexHandler(cmd, target_id, target_type, auth_type)
    return None


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

    def set_target_firewall(self, add_new_rule, ip_name):
        return

    def create_aad_user(self, identity_name, client_id):
        return

    def get_auth_config(self):
        return


class SqlHandler(TargetHandler):
    aad_user = generate_random_string(
        prefix="aad_" + RESOURCE.Sql.value + '_')

    db_server = ""
    dbname = ""
    user = ""

    def __init__(self, cmd, target_id, target_type, auth_type):
        super().__init__(cmd, target_id, target_type, auth_type)

        target_segments = parse_resource_id(target_id)
        self.db_server = target_segments.get('name')
        self.dbname = target_segments.get('child_name_1')
        self.user = self.profile.get_current_account_user()

    def set_user_admin(self, login_user, user_object_id):
        # pylint: disable=not-an-iterable
        admins = run_cli_cmd(
            'az sql server ad-admin list --ids {}'.format(self.target_id))
        is_admin = any(ad.get('sid') == user_object_id for ad in admins)
        if not is_admin:
            logger.warning('Setting current user as database server AAD admin:'
                           ' user=%s object id=%s', login_user, user_object_id)
            run_cli_cmd('az sql server ad-admin create -g {} --server-name {} --display-name {} --object-id {}'
                        ' --subscription {}'.format(self.rg, self.db_server, login_user, user_object_id, self.sub)).get('objectId')

    def create_aad_user(self, identity_name, client_id):
        self.aad_user = identity_name

        query_list = self.get_create_query(client_id)
        connection_string = self.get_connection_string()
        ip_name = None
        try:
            logger.warning("Connecting to database...")
            self.create_aad_user_in_sql(connection_string, query_list)
        except ConnectionFailError:
            # allow public access
            ip_name = generate_random_string(prefix='svc_')
            self.set_target_firewall(True, ip_name)
            # create again
            self.create_aad_user_in_sql(connection_string, query_list)

        # remove firewall rule
        if ip_name is not None:
            try:
                self.set_target_firewall(False, ip_name)
            # pylint: disable=bare-except
            except:
                pass
                # logger.warning('Please manually delete firewall rule %s to avoid security issue', ipname)

    def set_target_firewall(self, add_new_rule, ip_name):
        if add_new_rule:
            target = run_cli_cmd(
                'az postgres flexible-server show --ids {}'.format(self.target_id))
            # logger.warning("Update database server firewall rule to connect...")
            if target.get('publicNetworkAccess') == "Disabled":
                return True
            run_cli_cmd(
                'az postgres flexible-server firewall-rule create --resource-group {0} --name {1} --rule-name {2} '
                '--subscription {3} --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255'.format(
                    self.rg, self.db_server, ip_name, self.sub)
            )
            return False
        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))

    def create_aad_user_in_sql(self, conn_string, query_list):
        import pkg_resources
        installed_packages = pkg_resources.working_set
        psy_installed = any(('pyodbc') in d.key.lower()
                            for d in installed_packages)
        if not psy_installed:
            import platform
            system = platform.system()
            if system != 'Windows':
                logger.error(
                    "Only windows supports AAD authentication by pyodbc")
            import pip
            pip.main(['install', 'pyodbc'])
            logger.error(
                "please manually install odbc 18 for sql server and run 'pip install pyodbc'")

        import pyodbc

        try:
            with pyodbc.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    for execution_query in query_list:
                        try:
                            cursor.execute(execution_query)
                        except pyodbc.ProgrammingError as e:
                            logger.warning(e)
                        conn.commit()
        except pyodbc.Error as e:
            raise ConnectionFailError

    def get_connection_string(self):
        conn_string = 'DRIVER={ODBC Driver 18 for SQL Server};server=' + \
            self.db_server + '.database.windows.net;database=' + self.dbname + ';UID=' + self.user + \
            ';Authentication=ActiveDirectoryInteractive;'
        return conn_string

    def get_create_query(self, client_id):
        role_q = "CREATE USER \"{}\" FROM EXTERNAL PROVIDER;".format(
            self.aad_user)
        grant_q = "GRANT CONTROL ON DATABASE::{} TO \"{}\";".format(
            self.dbname, self.aad_user)

        return [role_q, grant_q]


class PostgresFlexHandler(TargetHandler):
    aad_user = generate_random_string(prefix="aad_psqlflex_")

    db_server = ""
    host = ""
    dbname = ""
    user = ""
    ip = ""

    def __init__(self, cmd, target_id, target_type, auth_type):
        super().__init__(cmd, target_id, target_type, auth_type)

        target_segments = parse_resource_id(target_id)
        self.db_server = target_segments.get('name')
        self.host = "{0}.postgres.database.azure.com".format(self.db_server)
        self.dbname = target_segments.get('child_name_1')
        self.user = self.profile.get_current_account_user()

    def enable_target_aad_auth(self):
        rq = 'az rest -u https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}?api-version=2022-03-08-privatepreview'.format(
            self.sub, self.rg, self.db_server)
        server_info = run_cli_cmd(rq)
        if server_info.get("properties").get("authConfig").get("activeDirectoryAuthEnabled"):
            return
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
        rq = 'az rest -u https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/administrators?api-version=2022-03-08-privatepreview'.format(
            self.sub, self.rg, self.db_server)
        admins = run_cli_cmd(rq).get("value")
        is_admin = any(user_object_id in u.get(
            "properties").get("objectId") for u in admins)
        if is_admin:
            return
        logger.warning('Set current user as DB Server AAD Administrators.')
        cmd = self.cmd
        master_template = ArmTemplateBuilder()
        master_template.add_resource({
            'type': "Microsoft.DBforPostgreSQL/flexibleServers/administrators",
            'apiVersion': '2022-03-08-privatepreview',
            'name': self.db_server + "/" + user_object_id,
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
        # self.aad_user = identity_name or self.aad_user

        query_list = self.get_create_query(client_id)
        connection_string = self.get_connection_string()
        ip_name = None
        try:
            logger.warning("Connecting to database...")
            self.create_aad_user_in_pg(connection_string, query_list)
        except ConnectionFailError:
            # allow public access
            ip_name = generate_random_string(prefix='svc_')
            self.set_target_firewall(True, ip_name)
            # create again
            self.create_aad_user_in_pg(connection_string, query_list)

        # remove firewall rule
        if ip_name is not None:
            try:
                self.set_target_firewall(False, ip_name)
            # pylint: disable=bare-except
            except:
                pass
                # logger.warning('Please manually delete firewall rule %s to avoid security issue', ipname)

    def set_target_firewall(self, add_new_rule, ip_name):
        if add_new_rule:
            target = run_cli_cmd(
                'az postgres flexible-server show --ids {}'.format(self.target_id))
            # logger.warning("Update database server firewall rule to connect...")
            if target.get('publicNetworkAccess') == "Disabled":
                return True
            start_ip = self.ip or '0.0.0.0'
            end_ip = self.ip or '255.255.255.255'
            run_cli_cmd(
                'az postgres flexible-server firewall-rule create --resource-group {0} --name {1} --rule-name {2} '
                '--subscription {3} --start-ip-address {4} --end-ip-address {5}'.format(
                    self.rg, self.db_server, ip_name, self.sub, start_ip, end_ip)
            )
            return False
        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))

    def create_aad_user_in_pg(self, conn_string, query_list):
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
            conn = psycopg2.connect(conn_string)
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            import re
            logger.warning(e)
            search_ip = re.search(
                'no pg_hba.conf entry for host "(.*)", user ', str(e))
            if search_ip is not None:
                self.ip = search_ip.group(1)
            raise ConnectionFailError

        conn.autocommit = True
        cursor = conn.cursor()
        logger.warning("Adding new AAD user %s to database...", self.aad_user)
        for execution_query in query_list:
            try:
                logger.debug(execution_query)
                cursor.execute(execution_query)
            except psycopg2.Error as e:  # role "aad_user" already exists
                logger.warning(e)

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
        return [
            'drop role IF EXISTS "{0}";'.format(self.aad_user),
            "select * from pgaadauth_create_principal_with_oid('{0}', '{1}', 'ServicePrincipal', false, false);".format(
                self.aad_user, client_id),
            'GRANT ALL PRIVILEGES ON DATABASE {0} TO "{1}";'.format(
                self.dbname, self.aad_user)]

    def get_auth_config(self):
        if self.auth_type in {'systemAssignedIdentity'}:
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

    def set_target_firewall(self, add_new_rule, ip_name):
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
            start_ip = self.ip or '0.0.0.0'
            end_ip = self.ip or '255.255.255.255'
            run_cli_cmd(
                'az postgres server firewall-rule create -g {0} -s {1} -n {2} --subscription {3}'
                ' --start-ip-address {4} --end-ip-address {5}'.format(
                    rg, server, ip_name, sub, start_ip, end_ip)
            )
            return target.get('publicNetworkAccess') == "Disabled"
        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))

    def get_create_query(self, client_id):

        return [
            'SET aad_validate_oids_in_tenant = off;',
            'drop role IF EXISTS "{0}";'.format(self.aad_user),
            'CREATE ROLE "{0}" WITH LOGIN PASSWORD "{1}" IN ROLE azure_ad_user;'.format(
                self.aad_user, client_id),
            'GRANT ALL PRIVILEGES ON DATABASE {0} TO "{1}";'.format(
                self.dbname, self.aad_user)
        ]


def getSourceHandler(source_id, source_type):
    if source_type in {RESOURCE.WebApp}:
        return WebappHandler(source_id, source_type)
    if source_type in {RESOURCE.ContainerApp}:
        return ContainerappHandler(source_id, source_type)
    if source_type in {RESOURCE.SpringCloud, RESOURCE.SpringCloudDeprecated}:
        return SpringHandler(source_id, source_type)


class SourceHandler:
    source_id = ""
    source_type = ""

    def __init__(self, source_id, source_type: RESOURCE):
        self.source_id = source_id
        self.source_type = source_type.value

    def get_identity(self):
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
            'az {} app show -g {} -s {} -n {} --subscription {}'.format(
                self.source_type, rg, spring, app, sub)).get('identity')
        if (identity is None or identity.get('type') != "SystemAssigned"):
            # assign system identity for spring-cloud
            logger.warning('Enabling Spring Cloud app System Identity...')
            run_cli_cmd(
                'az {} app identity assign -g {} -s {} -n {} --subscription {}'.format(
                    self.source_type, rg, spring, app, sub))
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
