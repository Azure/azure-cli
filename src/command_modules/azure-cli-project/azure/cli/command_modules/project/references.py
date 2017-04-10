
import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.documentdb._client_factory import cf_documentdb
from azure.cli.core._util import CLIError
from azure.cli.core.prompting import prompt, prompt_pass


def _create_environment_var_name(reference_name, suffix=None):
    """
    Creates the environment variable name using
    the reference name and suffix.
    """
    reference_name = reference_name.replace('-', '_')
    if suffix:
        return '{}_{}'.format(reference_name, suffix).upper()
    else:
        return reference_name.upper()


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


def reference_exists(service_name, reference_name):
    """
    Checks if secret for provided service
    and reference exists or not.
    """
    secret_name = get_secret_name(service_name, reference_name)
    command = "kubectl get secret {}".format(secret_name)
    exit_code = utils.execute_command(command)
    return exit_code == 0


def _get_dictionary(input_string):
    """
    Parses the input string (e.g. VAR1=VALUE1 VAR2=VALUE2 ...)
    and returns the dictionary of key/value pairs
    """
    return_dict = {}
    for entry in input_string:
        parts = entry.split('=', 1)
        if len(parts) == 1:
            raise CLIError(
                'usage error: --env-variables KEY=VALUE KEY=VALUE ...')
        return_dict[parts[0]] = parts[1]
    return return_dict


def add_reference(service_name, target_group, target_name, reference_name, env_variables):
    """
    Adds a references to an Azure resource
    """
    instance_type = None
    created_variables = []

    # If target_group and target_name are not set
    # it means we are dealing with a generic reference
    if not target_group and not target_name:
        instance_type = 'Generic'
        if not env_variables:
            raise CLIError('Environment variables were not provided')
        dict_vars = _get_dictionary(env_variables)
        created_variables = _create_custom_reference(
            service_name, reference_name, dict_vars)
    else:
        instance, client = get_reference_type(target_group, target_name)
        instance_type = instance.type
        if instance_type == 'Microsoft.DocumentDB/databaseAccounts':
            results = client.list_connection_strings(
                target_group, target_name)
            if len(results.connection_strings) <= 0:
                raise CLIError('No connection strings found')
            connection_string = results.connection_strings[0].connection_string
            created_variables = create_connection_string_reference(
                service_name, reference_name, connection_string)
        elif instance_type == 'Microsoft.Sql/servers':
            sql_admin_login = instance.administrator_login
            if not sql_admin_login:
                sql_admin_login = prompt('Administrator login:')
            sql_admin_password = instance.administrator_login_password
            if not sql_admin_password:
                sql_admin_password = prompt_pass('Password:')
            fqdn = instance.fully_qualified_domain_name
            created_variables = create_username_password_reference(
                service_name, reference_name, sql_admin_login, sql_admin_password, fqdn)
        elif instance_type == 'Microsoft.ServiceBus':
            connection_string = instance.list_keys(
                target_group, target_name, 'RootManageSharedAccessKey').primary_connection_string
            created_variables = create_connection_string_reference(
                service_name, reference_name, connection_string)
        else:
            raise CLIError('Could not determine the reference type')

    project_settings = settings.Project()
    project_settings.add_reference(service_name, reference_name, instance_type)
    return created_variables, instance_type


def _create_custom_reference(service_name, reference_name, key_value_pairs):
    """
    Creates a custom reference, stores the key value pairs
    in the Kubernetes secret, labels the secret with service name
    and returns the array of environment variable names that were added
    """
    secret_name = get_secret_name(service_name, reference_name)

    env_variables = []
    literals = []
    for key, value in key_value_pairs.items():
        env_variables.append(key)
        literals.append('--from-literal={}={}'.format(key, value))

    command = 'kubectl create secret generic {} {}'.format(
        secret_name, ' '.join(literals))
    utils.execute_command(command)
    _add_run_label(secret_name, service_name)

    return env_variables


def create_connection_string_reference(service_name, reference_name, connection_string):
    """
    Creates a secret on Kubernetes that stores
    the connection string and is labeled with run=service_name
    Returns the list of environment variable names
    """
    environment_variable_name = _create_environment_var_name(
        reference_name, 'connection_string')

    pairs = {environment_variable_name: connection_string}
    _create_custom_reference(service_name, reference_name, pairs)

    return [environment_variable_name]


def create_username_password_reference(service_name, reference_name, admin_login, admin_password, fqdn):
    """
    Creates a secret on Kubernetes that stores
    the administrator login, password and fully qualified domain name
    Returns the list of environment variable names
    """
    admin_login_var = _create_environment_var_name(
        reference_name, 'admin_login')
    admin_password_var = _create_environment_var_name(
        reference_name, 'admin_password')
    fqdn_var = _create_environment_var_name(reference_name, 'fqdn')

    pairs = {admin_login_var: admin_login,
             admin_password_var: admin_password, fqdn_var: fqdn}
    environment_variables = _create_custom_reference(
        service_name, reference_name, pairs)

    return environment_variables


def remove_reference(service_name, reference_name):
    """
    Removes the reference by deleting the created secret and
    removing it from the project settings file.
    """
    project_settings = settings.Project()
    project_settings.remove_reference(service_name, reference_name)
    command = 'kubectl delete secret {}'.format(
        get_secret_name(service_name, reference_name))
    utils.execute_command(command)


def get_sql_management_client(_):
    """
    Gets the SQL management client
    """
    from azure.mgmt.sql import SqlManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(SqlManagementClient)


def get_service_bus_management_client(_):
    """
    Gets the Service Bus management client
    """
    from azure.mgmt.servicebus import ServiceBusManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ServiceBusManagementClient)


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
        pass

    try:
        from azure.mgmt.servicebus.operations import NamespacesOperations
        namespaces = get_service_bus_management_client(None).namespaces
        NamespacesOperations.type = property(
            lambda self: 'Microsoft.ServiceBus')
        return namespaces, namespaces
    except Exception as exc:
        raise CLIError(exc)

    return None, None
