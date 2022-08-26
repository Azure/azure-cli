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
    tenant_id = Profile(cli_ctx=cli_ctx).get_subscription().get("tenantId")
    login_user = Profile(cli_ctx=cli_ctx).get_current_account_user()
    # Get login user info
    user_info = run_cli_cmd('az ad user show --id {}'.format(login_user))
    user_object_id = user_info.get('objectId') if user_info.get('objectId') is not None \
        else user_info.get('id')
    if user_object_id is None:
        raise Exception(
            "no object id found for user {}".format(login_user))

    # return if connection is not for db mi
    if auth_info['auth_type'] not in {'systemAssignedIdentity'} \
        or target_type not in {
            RESOURCE.Postgres,
            RESOURCE.PostgresFlexible,
            # RESOURCE.Mysql,
            # RESOURCE.MysqlFlexible,
            # RESOURCE.Sql
    }:
        return
    # enable source mi
    identity = None
    if source_type in {RESOURCE.SpringCloudDeprecated, RESOURCE.SpringCloud}:
        identity = get_springcloud_identity(source_id, source_type.value)
    elif source_type in {RESOURCE.WebApp}:
        identity = get_webapp_identity(source_id)
    elif source_type in {RESOURCE.ContainerApp}:
        identity = get_containerapp_identity(source_id)
    object_id = identity.get('principalId')
    identity_info = run_cli_cmd(
        'az ad sp show --id {0}'.format(object_id))
    client_id = identity_info.get('appId')
    aad_user = identity_info.get('displayName') or generate_random_string(
        prefix="aad_" + target_type.value + '_')

    # enable target aad authentication
    enable_target_aad_auth(cmd, target_id, target_type, tenant_id)

    # Set login user as db aad admin
    if target_type == RESOURCE.Postgres:
        set_user_admin_if_not(target_id, target_type,
                              login_user, user_object_id)
    elif target_type == RESOURCE.PostgresFlexible:
        set_user_admin_pg_flex(cmd, target_id, target_type,
                               login_user, user_object_id, tenant_id)

    # create an aad user in db
    if(target_type in {RESOURCE.Postgres, RESOURCE.PostgresFlexible} and auth_info['auth_type'] == 'systemAssignedIdentity'):
        create_aad_user_in_pg(cli_ctx, target_id,
                              target_type, aad_user, client_id)

    return {
        'auth_type': 'secret',
        'name': aad_user,
        'secret_info': {
            'secret_type': 'rawValue'
        }
    }


def enable_target_aad_auth(cmd, target_id, target_type, tenant_id):
    if target_type == RESOURCE.PostgresFlexible:
        # enable pg aad auth
        # location: "Southeast Asia"

        target_segments = parse_resource_id(target_id)
        sub = target_segments.get('subscription')
        rg = target_segments.get('resource_group')
        server = target_segments.get('name')
        master_template = ArmTemplateBuilder()
        master_template.add_resource({
            'type': "Microsoft.DBforPostgreSQL/flexibleServers",
            'apiVersion': '2022-03-08-privatepreview',
            'name': server,
            'location': "East US",
            'properties': {
                'authConfig': {
                    'activeDirectoryAuthEnabled': True,
                    'tenantId': tenant_id
                },
                'createMode': "Update"
            },
        })

        template = master_template.build()
        # parameters = master_template.build_parameters()

        # deploy ARM template
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
            client.begin_create_or_update(rg, deployment_name, deployment))


def set_user_admin_pg_flex(cmd, target_id, target_type, login_user, user_object_id, tenant_id):

    if target_type == RESOURCE.PostgresFlexible:
        target_segments = parse_resource_id(target_id)
        sub = target_segments.get('subscription')
        rg = target_segments.get('resource_group')
        server = target_segments.get('name')
        master_template = ArmTemplateBuilder()
        master_template.add_resource({
            'type': "Microsoft.DBforPostgreSQL/flexibleServers/administrators",
            'apiVersion': '2022-03-08-privatepreview',
            'name': server+"/"+user_object_id,
            'location': "East US",
            'properties': {
                'principalName': login_user,
                'principalType': 'User',
                'tenantId': tenant_id,
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
            client.begin_create_or_update(rg, deployment_name, deployment))


def set_user_admin_if_not(target_id, target_type, login_user, user_object_id):
    target_segments = parse_resource_id(target_id)
    sub = target_segments.get('subscription')
    rg = target_segments.get('resource_group')
    server = target_segments.get('name')
    is_admin = True
    # pylint: disable=not-an-iterable

    admins = run_cli_cmd(
        'az postgres server ad-admin list --ids {}'.format(target_id))
    is_admin = any(ad.get('sid') == user_object_id for ad in admins)
    if not is_admin:
        logger.warning('Setting current user as database server AAD admin:'
                       ' user=%s object id=%s', login_user, user_object_id)
        run_cli_cmd('az postgres server ad-admin create -g {} --server-name {} --display-name {} --object-id {}'
                    ' --subscription {}'.format(rg, server, login_user, user_object_id, sub)).get('objectId')

# pylint: disable=unused-argument, not-an-iterable, too-many-statements


def set_target_firewall(target_id, target_type, add_new_rule, ipname, deny_public_access=False):
    if target_type == RESOURCE.Postgres:
        target_segments = parse_resource_id(target_id)
        sub = target_segments.get('subscription')
        rg = target_segments.get('resource_group')
        server = target_segments.get('name')
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
                    rg, server, ipname, sub)
            )
            return target.get('publicNetworkAccess') == "Disabled"

        # logger.warning("Remove database server firewall rules to recover...")
        # run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        # if deny_public_access:
        #     run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))


def create_aad_user_in_pg(cli_ctx, target_id, target_type, aad_user, client_id):
    import pkg_resources
    installed_packages = pkg_resources.working_set
    psyinstalled = any(('psycopg2') in d.key.lower()
                       for d in installed_packages)
    if not psyinstalled:
        _install_deps_for_psycopg2()
        import pip
        pip.main(['install', 'psycopg2-binary'])

    import psycopg2

    # pylint: disable=protected-access
    profile = Profile(cli_ctx=cli_ctx)

    # Update connection string information
    target_segments = parse_resource_id(target_id)
    dbserver = target_segments.get('name')
    host = "{0}.postgres.database.azure.com".format(dbserver)
    dbname = target_segments.get('child_name_1')
    user = profile.get_current_account_user() + '@' + \
        dbserver if target_type == RESOURCE.Postgres else profile.get_current_account_user()
    password = run_cli_cmd(
        'az account get-access-token --resource-type oss-rdbms').get('accessToken')
    sslmode = "require"

    ipname = None

    # Construct connection string
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(
        host, user, dbname, password, sslmode)
    try:
        logger.warning("Connecting to database...")
        conn = psycopg2.connect(conn_string)
    except psycopg2.Error:
        # add new firewall rule
        ipname = generate_random_string(prefix='svc_')
        deny_public_access = set_target_firewall(
            target_id, target_type, True, ipname)
        try:
            conn = psycopg2.connect(conn_string)
        except psycopg2.Error as e:
            raise e
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        logger.warning("Adding new AAD user %s to database...", aad_user)
        if target_type == RESOURCE.Postgres:
            cursor.execute(
                "SET aad_validate_oids_in_tenant = off; \
                drop role IF EXISTS \"{}\"; \
                CREATE ROLE \"{}\" WITH LOGIN PASSWORD '{}' IN ROLE azure_ad_user;".format(aad_user, aad_user, client_id))
        elif target_type == RESOURCE.PostgresFlexible:
            cursor.execute("drop role IF EXISTS \"{}\"; \
            select * from pgaadauth_create_principal_with_oid('{}', '{}', 'ServicePrincipal', false, false);".format(aad_user, aad_user, client_id))
    except psycopg2.Error as e:  # role "aad_user" already exists
        logger.warning(e)
        conn.commit()

    if target_type == RESOURCE.Postgres:
        try:
            logger.warning(
                "Grant read and write privileges of database %s to %s ...", dbname, aad_user)
            cursor.execute(
                "GRANT ALL PRIVILEGES ON DATABASE {} TO \"{}\"; \
                GRANT ALL ON ALL TABLES IN SCHEMA public TO \"{}\";".format(dbname, aad_user, aad_user))
        except psycopg2.Error as e:
            logger.warning(e)
            conn.commit()

    # Clean up
    conn.commit()
    cursor.close()
    conn.close()
    # remove firewall rule
    if ipname is not None:
        try:
            set_target_firewall(target_id, target_type,
                                False, ipname, deny_public_access)
        # pylint: disable=bare-except
        except:
            pass
            # logger.warning('Please manually delete firewall rule %s to avoid security issue', ipname)
    logger.warning("Creating service connection to postgresql ...")


def get_springcloud_identity(source_id, source_type):
    segments = parse_resource_id(source_id)
    sub = segments.get('subscription')
    spring = segments.get('name')
    app = segments.get('child_name_1')
    rg = segments.get('resource_group')
    logger.warning('Checking if Spring Cloud app enables System Identity...')
    identity = run_cli_cmd(
        'az {} app show -g {} -s {} -n {} --subscription {}'.format(source_type, rg, spring, app, sub)).get('identity')
    if (identity is None or identity.get('type') != "SystemAssigned"):
        # assign system identity for spring-cloud
        logger.warning('Enabling Spring Cloud app System Identity...')
        run_cli_cmd(
            'az {} app identity assign -g {} -s {} -n {} --subscription {}'.format(source_type, rg, spring, app, sub))
        cnt = 0
        while (identity is None and cnt < 5):
            identity = run_cli_cmd('az {} app show -g {} -s {} -n {} --subscription {}'
                                   .format(source_type, rg, spring, app, sub)).get('identity')
            time.sleep(3)
            cnt += 1
    return identity


def get_webapp_identity(source_id):
    logger.warning('Checking if WebApp enables System Identity...')
    identity = run_cli_cmd(
        'az webapp show --ids {}'.format(source_id)).get('identity')
    if (identity is None or "SystemAssigned" not in identity.get('type')):
        # assign system identity for spring-cloud
        logger.warning('Enabling WebApp System Identity...')
        run_cli_cmd('az webapp identity assign --ids {}'.format(source_id))
        cnt = 0
        while (identity is None and cnt < 5):
            identity = run_cli_cmd(
                'az webapp identity show --ids {}'.format(source_id)).get('identity')
            time.sleep(3)
            cnt += 1
    return identity


def get_containerapp_identity(source_id):
    logger.warning('Checking if Container App enables System Identity...')
    identity = run_cli_cmd(
        'az containerapp show --ids {}'.format(source_id)).get('identity')
    if (identity is None or "SystemAssigned" not in identity.get('type')):
        # assign system identity for spring-cloud
        logger.warning('Enabling Container App System Identity...')
        run_cli_cmd(
            'az containerapp identity assign --ids {} --system-assigned'.format(source_id))
        cnt = 0
        while (identity is None and cnt < 5):
            identity = run_cli_cmd(
                'az containerapp identity show --ids {}'.format(source_id)).get('identity')
            time.sleep(3)
            cnt += 1
    return identity
