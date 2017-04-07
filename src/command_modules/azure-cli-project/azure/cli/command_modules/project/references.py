
import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.documentdb._client_factory import cf_documentdb
from azure.cli.core._util import CLIError


def _create_environment_var_name(reference_name, suffix):
    """
    Creates the environment variable name using
    the reference name and suffix.
    """
    reference_name = reference_name.replace('-', '_')
    return '{}_{}'.format(reference_name, suffix).upper()


def get_secret_name(service_name, reference_name):
    """
    Gets the secret name for provided service and
    reference name
    """
    return '{}-{}'.format(service_name, reference_name).lower()


def _label_secret(secret_name, label):
    """
    Adds a label to Kubernetes secret
    """
    # Label it with run=service_name
    label_command = 'kubectl label secret {} {}'.format(
        secret_name, label)
    utils.execute_command(label_command)


def _add_run_label(secret_name, service_name):
    """
    Labels the secret with run=service_name
    """
    _label_secret(secret_name, 'run={}'.format(service_name))


def create_documentdb_reference(service_name, reference_name, connection_string):
    """
    Creates a secret on Kubernetes that stores
    the connection string and is labeled with run=service_name
    Returns the list of environment variable names
    """
    secret_name = get_secret_name(service_name, reference_name)
    environment_variable_name = _create_environment_var_name(
        reference_name, 'connection_string')

    # Create the secret
    command = 'kubectl create secret generic {} --from-literal={}={}'.format(
        secret_name, environment_variable_name, connection_string)
    utils.execute_command(command)

    # Label it with run=service_name
    _add_run_label(secret_name, service_name)
    return [environment_variable_name]


def create_sqlserver_reference(service_name, reference_name, admin_login, admin_password, fqdn):
    """
    Creates a secret on Kubernetes for SQL server that stores
    the administrator login, password and fully qualified domain name
    Returns the list of environment variable names
    """
    secret_name = get_secret_name(service_name, reference_name)

    admin_login_var = _create_environment_var_name(
        reference_name, 'admin_login')
    admin_password_var = _create_environment_var_name(
        reference_name, 'admin_password')
    fqdn_var = _create_environment_var_name(reference_name, 'fqdn')

    command = 'kubectl create secret generic {}\
               --from-literal={}={}\
               --from-literal={}={}\
               --from-literal={}={}'.format(secret_name,
                                            admin_login_var, admin_login,
                                            admin_password_var, admin_password,
                                            fqdn_var, fqdn)
    utils.execute_command(command)

    # Label it with run=service_name
    _add_run_label(secret_name, 'run={}'.format(service_name))
    return [admin_login_var,
            admin_password_var,
            fqdn_var]


def remove_reference(service_name, reference_name):
    """
    Removes the reference by deleting the created secret and
    removing it from the project settings file.
    """
    project_settings = settings.Project()
    project_settings.remove_reference(service_name, reference_name)
    command = 'kubectl delete secret {}'.format(
        get_secret_name(service_name, reference_name))
    utils.execute_command(command, ignore_failure=True)


def get_sql_management_client(_):
    """
    Gets the SQL management client
    """
    from azure.mgmt.sql import SqlManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(SqlManagementClient)


def get_reference_type(resource_group, resource_name):
    """
    Gets the reference type from the provided
    resource group and name
    """
    instance = None
    try:
        docdb_client = cf_documentdb().database_accounts
        instance = docdb_client.get(resource_group, resource_name)
        return instance, docdb_client
    except Exception as exc:
        pass

    try:
        sql_servers = get_sql_management_client(None).servers
        instance = sql_servers.get(resource_group, resource_name)
        return instance, sql_servers
    except Exception as exc:
        raise CLIError(exc)

    return None, None
