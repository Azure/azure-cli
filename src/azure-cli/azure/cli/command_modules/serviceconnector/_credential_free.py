# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id
from azure.cli.core.azclierror import (
    AzureConnectionError,
    ValidationError
)
from azure.cli.core.extension.operations import _install_deps_for_psycopg2
from azure.cli.core.profiles import ResourceType
from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import random_string
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import ArmTemplateBuilder
from ._utils import run_cli_cmd, generate_random_string
from ._resource_config import (
    RESOURCE,
)
from ._validators import (
    get_source_resource_name,
    get_target_resource_name,
)

logger = get_logger(__name__)


# pylint: disable=line-too-long
# For db(mysqlFlex/psql/psqlFlex/sql) linker with auth type=systemAssignedIdentity, enable AAD auth and create db user on data plane
# For other linker, ignore the steps
def enable_mi_for_db_linker(cmd, source_id, target_id, auth_info, client_type, connection_name):
    # return if connection is not for db mi
    if auth_info['auth_type'] not in {'systemAssignedIdentity'}:
        return

    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    source_handler = getSourceHandler(source_id, source_type)
    if source_handler is None:
        return
    target_handler = getTargetHandler(
        cmd, target_id, target_type, auth_info['auth_type'], client_type, connection_name)
    if target_handler is None:
        return

    user_info = run_cli_cmd(
        'az ad user show --id {}'.format(target_handler.login_username))
    user_object_id = user_info.get('objectId') if user_info.get('objectId') is not None \
        else user_info.get('id')
    if user_object_id is None:
        raise Exception(
            "No object id found for user {}".format(target_handler.login_username))

    # enable source mi
    source_object_id = source_handler.get_identity_pid()

    identity_info = run_cli_cmd(
        'az ad sp show --id {}'.format(source_object_id), 15, 10)
    client_id = identity_info.get('appId')
    identity_name = identity_info.get('displayName')

    # enable target aad authentication and set login user as db aad admin
    target_handler.enable_target_aad_auth()
    target_handler.set_user_admin(
        user_object_id, mysql_identity_id=auth_info.get('mysql-identity-id'))

    # create an aad user in db
    target_handler.create_aad_user(identity_name, client_id)
    return target_handler.get_auth_config()


# pylint: disable=no-self-use, unused-argument, too-many-instance-attributes
def getTargetHandler(cmd, target_id, target_type, auth_type, client_type, connection_name):
    if target_type in {RESOURCE.Sql}:
        return SqlHandler(cmd, target_id, target_type, auth_type, connection_name)
    if target_type in {RESOURCE.Postgres}:
        return PostgresSingleHandler(cmd, target_id, target_type, auth_type, connection_name)
    if target_type in {RESOURCE.PostgresFlexible}:
        return PostgresFlexHandler(cmd, target_id, target_type, auth_type, connection_name)
    if target_type in {RESOURCE.MysqlFlexible}:
        return MysqlFlexibleHandler(cmd, target_id, target_type, auth_type, connection_name)
    return None


class TargetHandler:
    target_id = ""
    target_type = ""
    profile = None
    cmd = None
    tenant_id = ""
    subscription = ""
    resource_group = ""
    login_username = ""
    endpoint = ""
    aad_username = ""

    auth_type = ""

    def __init__(self, cmd, target_id, target_type, auth_type, connection_name):
        self.profile = Profile(cli_ctx=cmd.cli_ctx)
        self.cmd = cmd
        self.target_id = target_id
        self.target_type = target_type
        self.aad_username = "aad_" + connection_name
        self.tenant_id = Profile(
            cli_ctx=cmd.cli_ctx).get_subscription().get("tenantId")
        target_segments = parse_resource_id(target_id)
        self.subscription = target_segments.get('subscription')
        self.resource_group = target_segments.get('resource_group')
        self.auth_type = auth_type
        self.login_username = run_cli_cmd(
            'az account show').get("user").get("name")

    def enable_target_aad_auth(self):
        return

    def set_user_admin(self, user_object_id, **kwargs):
        return

    def set_target_firewall(self, add_new_rule, ip_name):
        return

    def create_aad_user(self, identity_name, client_id):
        return

    def get_auth_config(self):
        return


class MysqlFlexibleHandler(TargetHandler):

    server = ""
    dbname = ""

    def __init__(self, cmd, target_id, target_type, auth_type, connection_name):
        super().__init__(cmd, target_id, target_type, auth_type, connection_name)
        self.endpoint = cmd.cli_ctx.cloud.suffixes.mysql_server_endpoint
        target_segments = parse_resource_id(target_id)
        self.server = target_segments.get('name')
        self.dbname = target_segments.get('child_name_1')

    def set_user_admin(self, user_object_id, **kwargs):
        mysql_identity_id = kwargs['mysql_identity_id']
        admins = run_cli_cmd(
            'az mysql flexible-server ad-admin list -g {} -s {} --subscription {}'.format(
                self.resource_group, self.server, self.subscription)
        )
        is_admin = any(ad.get('sid') == user_object_id for ad in admins)
        if is_admin:
            return

        logger.warning('Set current user as DB Server AAD Administrators.')
        # set user as AAD admin
        if mysql_identity_id is None:
            raise ValidationError(
                "Provide '--system-identity mysql-identity-id=xx' to set {} as AAD administrator.".format(self.user))
        mysql_umi = run_cli_cmd(
            'az mysql flexible-server identity list -g {} -s {} --subscription {}'.format(self.resource_group, self.server, self.subscription))
        if (not mysql_umi) or mysql_identity_id not in mysql_umi.get("userAssignedIdentities"):
            run_cli_cmd('az mysql flexible-server identity assign -g {} -s {} --subscription {} --identity {}'.format(
                self.resource_group, self.server, self.subscription, mysql_identity_id))
        run_cli_cmd('az mysql flexible-server ad-admin create -g {} -s {} --subscription {} -u {} -i {} --identity {}'.format(
            self.resource_group, self.server, self.subscription, self.login_username, user_object_id, mysql_identity_id))

    def create_aad_user(self, identity_name, client_id):
        query_list = self.get_create_query(client_id)
        connection_kwargs = self.get_connection_string()
        ip_name = None
        try:
            logger.warning("Connecting to database...")
            self.create_aad_user_in_mysql(connection_kwargs, query_list)
        except AzureConnectionError:
            # allow public access
            ip_name = generate_random_string(prefix='svc_').lower()
            self.set_target_firewall(True, ip_name)
            # create again
            self.create_aad_user_in_mysql(connection_kwargs, query_list)

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
                'az mysql flexible-server show --ids {}'.format(self.target_id))
            # logger.warning("Update database server firewall rule to connect...")
            if target.get('network').get('publicNetworkAccess') == "Disabled":
                return
            run_cli_cmd(
                'az mysql flexible-server firewall-rule create --resource-group {0} --name {1} --rule-name {2} '
                '--subscription {3} --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255'.format(
                    self.resource_group, self.server, ip_name, self.subscription)
            )
        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az mysql server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az mysql server update --public Disabled --ids {}'.format(target_id))

    def create_aad_user_in_mysql(self, connection_kwargs, query_list):
        import pkg_resources
        installed_packages = pkg_resources.working_set
        # pylint: disable=not-an-iterable
        pym_installed = any(('pymysql') in d.key.lower()
                            for d in installed_packages)
        if not pym_installed:
            import pip
            pip.main(['install', 'mycli'])
        # pylint: disable=import-error
        import pymysql
        from pymysql.constants import CLIENT

        connection_kwargs['client_flag'] = CLIENT.MULTI_STATEMENTS
        try:
            connection = pymysql.connect(**connection_kwargs)
            cursor = connection.cursor()
            for q in query_list:
                try:
                    logger.debug(q)
                    cursor.execute(q)
                except Exception as e:  # pylint: disable=broad-except
                    logger.warning(
                        "Query %s, error: %s", q, str(e))
        except pymysql.Error as e:
            raise AzureConnectionError("Fail to connect mysql. " + str(e))
        if cursor is not None:
            try:
                cursor.close()
            except Exception as e:  # pylint: disable=broad-except
                raise CLIError(str(e))

    def get_connection_string(self):
        password = run_cli_cmd(
            'az account get-access-token --resource-type oss-rdbms').get('accessToken')

        return {
            'host': self.server + self.endpoint,
            'database': self.dbname,
            'user': self.login_username,
            'password': password,
            'ssl': {"fake_flag_to_enable_tls": True},
            'autocommit': True
        }

    def get_create_query(self, client_id):
        return [
            "SET aad_auth_validate_oids_in_tenant = OFF;",
            "DROP USER IF EXISTS '{}'@'%';".format(self.aad_username),
            "CREATE AADUSER '{}' IDENTIFIED BY '{}';".format(
                self.aad_username, client_id),
            "GRANT ALL PRIVILEGES ON {}.* TO '{}'@'%';".format(
                self.dbname, self.aad_username),
            "FLUSH privileges;"
        ]

    def get_auth_config(self):
        if self.auth_type in {'systemAssignedIdentity'}:
            return {
                'auth_type': 'secret',
                'name': self.aad_username,
                'secret_info': {
                    'secret_type': 'rawValue'
                }
            }


class SqlHandler(TargetHandler):

    server = ""
    dbname = ""

    def __init__(self, cmd, target_id, target_type, auth_type, connection_name):
        super().__init__(cmd, target_id, target_type, auth_type, connection_name)
        self.endpoint = cmd.cli_ctx.cloud.suffixes.sql_server_hostname
        target_segments = parse_resource_id(target_id)
        self.server = target_segments.get('name')
        self.dbname = target_segments.get('child_name_1')

    def set_user_admin(self, user_object_id, **kwargs):
        # pylint: disable=not-an-iterable
        admins = run_cli_cmd(
            'az sql server ad-admin list --ids {}'.format(self.target_id))
        is_admin = any(ad.get('sid') == user_object_id for ad in admins)
        if not is_admin:
            logger.warning('Setting current user as database server AAD admin:'
                           ' user=%s object id=%s', self.login_username, user_object_id)
            run_cli_cmd('az sql server ad-admin create -g {} --server-name {} --display-name {} --object-id {} --subscription {}'.format(
                self.resource_group, self.server, self.login_username, user_object_id, self.subscription)).get('objectId')

    def create_aad_user(self, identity_name, client_id):
        self.aad_username = identity_name

        query_list = self.get_create_query(client_id)
        connection_args = self.get_connection_string()
        ip_name = None
        try:
            logger.warning("Connecting to database...")
            self.create_aad_user_in_sql(connection_args, query_list)
        except AzureConnectionError:
            # allow public access
            ip_name = generate_random_string(prefix='svc_').lower()
            self.set_target_firewall(True, ip_name)
            # create again
            self.create_aad_user_in_sql(connection_args, query_list)

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
                'az sql server show --ids {}'.format(self.target_id))
            # logger.warning("Update database server firewall rule to connect...")
            if target.get('publicNetworkAccess') == "Disabled":
                run_cli_cmd(
                    'az sql server update -e true --ids {}'.format(self.target_id))
            run_cli_cmd(
                'az sql server firewall-rule create -g {0} -s {1} -n {2} '
                '--subscription {3} --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255'.format(
                    self.resource_group, self.server, ip_name, self.subscription)
            )
            return False

    def create_aad_user_in_sql(self, connection_args, query_list):
        import pkg_resources
        installed_packages = pkg_resources.working_set
        # pylint: disable=not-an-iterable
        psy_installed = any(('pyodbc') in d.key.lower()
                            for d in installed_packages)

        if not psy_installed:
            import pip
            pip.main(['install', 'pyodbc'])
            logger.warning(
                "Please manually install odbc 18 for SQL server, reference: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16 "
                "and run 'pip install pyodbc'")
        # pylint: disable=import-error, c-extension-no-member
        import pyodbc
        try:
            with pyodbc.connect(connection_args.get("connection_string"), attrs_before=connection_args.get("attrs_before")) as conn:
                with conn.cursor() as cursor:
                    for execution_query in query_list:
                        try:
                            cursor.execute(execution_query)
                        except pyodbc.ProgrammingError as e:
                            logger.warning(e)
                        conn.commit()
        except pyodbc.Error as e:
            raise AzureConnectionError("Fail to connect sql. " + str(e))

    def get_connection_string(self):
        token_bytes = run_cli_cmd(
            'az account get-access-token --output json --resource https://database.windows.net/').get('accessToken').encode('utf-16-le')

        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        # This connection option is defined by microsoft in msodbcsql.h
        SQL_COPT_SS_ACCESS_TOKEN = 1256
        conn_string = 'DRIVER={ODBC Driver 18 for SQL Server};server=' + \
            self.server + self.endpoint + ';database=' + self.dbname + ';'
        return {'connection_string': conn_string, 'attrs_before': {SQL_COPT_SS_ACCESS_TOKEN: token_struct}}

    def get_create_query(self, client_id):
        role_q = "CREATE USER \"{}\" FROM EXTERNAL PROVIDER;".format(
            self.aad_username)
        grant_q = "GRANT CONTROL ON DATABASE::{} TO \"{}\";".format(
            self.dbname, self.aad_username)

        return [role_q, grant_q]


class PostgresFlexHandler(TargetHandler):

    db_server = ""
    host = ""
    dbname = ""
    ip = ""

    def __init__(self, cmd, target_id, target_type, auth_type, connection_name):
        super().__init__(cmd, target_id, target_type, auth_type, connection_name)
        self.endpoint = cmd.cli_ctx.cloud.suffixes.postgresql_server_endpoint
        target_segments = parse_resource_id(target_id)
        self.db_server = target_segments.get('name')
        self.host = self.db_server + self.endpoint
        self.dbname = target_segments.get('child_name_1')

    def enable_pg_extension(self):
        run_cli_cmd('az postgres flexible-server parameter set -g {} -s {} --subscription {} --name azure.extensions --value uuid-ossp'.format(self.resource_group, self.db_server, self.subscription))

    def enable_target_aad_auth(self):
        self.enable_pg_extension()

        rq = 'az rest -u https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}?api-version=2022-03-08-privatepreview'.format(
            self.subscription, self.resource_group, self.db_server)
        server_info = run_cli_cmd(rq)
        if server_info.get("properties").get("authConfig").get("activeDirectoryAuthEnabled"):
            return
        logger.warning('Enabling Postgres flexible server AAD authentication')
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
            client.begin_create_or_update(self.resource_group, deployment_name, deployment))

    def set_user_admin(self, user_object_id, **kwargs):
        rq = 'az rest -u https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/administrators?api-version=2022-03-08-privatepreview'.format(
            self.subscription, self.resource_group, self.db_server)
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
                'principalName': self.login_username,
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
            client.begin_create_or_update(self.resource_group, deployment_name, deployment))

    def create_aad_user(self, identity_name, client_id):
        # self.aad_user = identity_name or self.aad_user

        query_list = self.get_create_query(client_id)
        connection_string = self.get_connection_string()
        ip_name = None
        try:
            logger.warning("Connecting to database...")
            self.create_aad_user_in_pg(connection_string, query_list)
        except AzureConnectionError:
            # allow public access
            ip_name = generate_random_string(prefix='svc_').lower()
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
            if target.get('network').get('publicNetworkAccess') == "Disabled":
                return True
            start_ip = self.ip or '0.0.0.0'
            end_ip = self.ip or '255.255.255.255'
            run_cli_cmd(
                'az postgres flexible-server firewall-rule create --resource-group {0} --name {1} --rule-name {2} '
                '--subscription {3} --start-ip-address {4} --end-ip-address {5}'.format(
                    self.resource_group, self.db_server, ip_name, self.subscription, start_ip, end_ip)
            )
            return False
        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))

    def create_aad_user_in_pg(self, conn_string, query_list):
        import pkg_resources
        installed_packages = pkg_resources.working_set
        # pylint: disable=not-an-iterable
        psy_installed = any(('psycopg2') in d.key.lower()
                            for d in installed_packages)
        if not psy_installed:
            _install_deps_for_psycopg2()
            import pip
            pip.main(['install', 'psycopg2-binary'])
        # pylint: disable=import-error
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
            raise AzureConnectionError(
                "Fail to connect to postgresql. " + str(e))

        conn.autocommit = True
        cursor = conn.cursor()
        logger.warning("Adding new AAD user %s to database...",
                       self.aad_username)
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

        # extension functions require the extension to be available, which is the case for postgres (default) database.
        conn_string = "host={} user={} dbname=postgres password={} sslmode=require".format(
            self.host, self.login_username, password)
        return conn_string

    def get_create_query(self, client_id):
        return [
            'drop role IF EXISTS "{0}";'.format(self.aad_username),
            "select * from pgaadauth_create_principal_with_oid('{0}', '{1}', 'ServicePrincipal', false, false);".format(
                self.aad_username, client_id),
            'GRANT ALL PRIVILEGES ON DATABASE {0} TO "{1}";'.format(
                self.dbname, self.aad_username)]

    def get_auth_config(self):
        if self.auth_type in {'systemAssignedIdentity'}:
            return {
                'auth_type': 'secret',
                'name': self.aad_username,
                'secret_info': {
                    'secret_type': 'rawValue'
                }
            }


class PostgresSingleHandler(PostgresFlexHandler):

    def enable_target_aad_auth(self):
        return

    def set_user_admin(self, user_object_id, **kwargs):
        sub = self.subscription
        rg = self.resource_group
        server = self.db_server
        is_admin = True

        # pylint: disable=not-an-iterable
        admins = run_cli_cmd(
            'az postgres server ad-admin list --ids {}'.format(self.target_id))
        is_admin = any(ad.get('sid') == user_object_id for ad in admins)
        if not is_admin:
            logger.warning('Setting current user as database server AAD admin:'
                           ' user=%s object id=%s', self.login_username, user_object_id)
            run_cli_cmd('az postgres server ad-admin create -g {} --server-name {} --display-name {} --object-id {}'
                        ' --subscription {}'.format(rg, server, self.login_username, user_object_id, sub)).get('objectId')

    def set_target_firewall(self, add_new_rule, ip_name):
        sub = self.subscription
        rg = self.resource_group
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

    def get_connection_string(self):
        password = run_cli_cmd('az account get-access-token --resource-type oss-rdbms').get('accessToken')

        # extension functions require the extension to be available, which is the case for postgres (default) database.
        conn_string = "host={} user={} dbname=postgres password={} sslmode=require".format(
            self.host, self.login_username + '@' + self.db_server, password)
        return conn_string

    def get_create_query(self, client_id):

        return [
            'SET aad_validate_oids_in_tenant = off;',
            'drop role IF EXISTS "{0}";'.format(self.aad_username),
            "CREATE ROLE {0} WITH LOGIN PASSWORD '{1}' IN ROLE azure_ad_user;".format(
                self.aad_username, client_id),
            "GRANT ALL PRIVILEGES ON DATABASE {0} TO {1};".format(
                self.dbname, self.aad_username)
        ]


def getSourceHandler(source_id, source_type):
    if source_type in {RESOURCE.WebApp}:
        return WebappHandler(source_id, source_type)
    if source_type in {RESOURCE.ContainerApp}:
        return ContainerappHandler(source_id, source_type)
    if source_type in {RESOURCE.SpringCloud, RESOURCE.SpringCloudDeprecated}:
        return SpringHandler(source_id, source_type)


# pylint: disable=too-few-public-methods
class SourceHandler:
    source_id = ""
    source_type = ""

    def __init__(self, source_id, source_type: RESOURCE):
        self.source_id = source_id
        self.source_type = source_type.value

    def get_identity_pid(self):
        return


def output_is_none(output):
    return not output.stdout


class SpringHandler(SourceHandler):
    def get_identity_pid(self):
        segments = parse_resource_id(self.source_id)
        sub = segments.get('subscription')
        spring = segments.get('name')
        app = segments.get('child_name_1')
        rg = segments.get('resource_group')
        logger.warning(
            'Checking if Spring Cloud app enables System Identity...')
        identity = run_cli_cmd('az {} app identity show -g {} -s {} -n {} --subscription {}'.format(
            self.source_type, rg, spring, app, sub))
        if (identity is None or identity.get('type') != "SystemAssigned"):
            # assign system identity for spring-cloud
            logger.warning('Enabling Spring Cloud app System Identity...')
            run_cli_cmd(
                'az {} app identity assign -g {} -s {} -n {} --subscription {}'.format(
                    self.source_type, rg, spring, app, sub))

            identity = run_cli_cmd('az {} app identity show -g {} -s {} -n {} --subscription {}'.format(
                self.source_type, rg, spring, app, sub), 15, 5, output_is_none)

        if identity is None:
            raise CLIError(
                "Unable to get system identity of Spring. Please try it later.")
        return identity.get('principalId')


class WebappHandler(SourceHandler):
    def get_identity_pid(self):
        logger.warning('Checking if WebApp enables System Identity...')
        identity = run_cli_cmd(
            'az webapp identity show --ids {}'.format(self.source_id))
        if (identity is None or "SystemAssigned" not in identity.get('type')):
            # assign system identity for spring-cloud
            logger.warning('Enabling WebApp System Identity...')
            run_cli_cmd(
                'az webapp identity assign --ids {}'.format(self.source_id))

            identity = run_cli_cmd(
                'az webapp identity show --ids {}'.format(self.source_id), 15, 5, output_is_none)

        if identity is None:
            raise CLIError(
                "Unable to get system identity of Web App. Please try it later.")
        return identity.get('principalId')


class ContainerappHandler(SourceHandler):
    def get_identity_pid(self):
        logger.warning('Checking if Container App enables System Identity...')
        identity = run_cli_cmd(
            'az containerapp identity show --ids {}'.format(self.source_id))
        if (identity is None or "SystemAssigned" not in identity.get('type')):
            # assign system identity for spring-cloud
            logger.warning('Enabling Container App System Identity...')
            run_cli_cmd(
                'az containerapp identity assign --ids {} --system-assigned'.format(self.source_id))
            identity = run_cli_cmd(
                'az containerapp identity show --ids {}'.format(self.source_id), 15, 5, output_is_none)

        if identity is None:
            raise CLIError(
                "Unable to get system identity of Container App. Please try it later.")
        return identity.get('principalId')
