
import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.documentdb._client_factory import cf_documentdb
from azure.cli.core._util import CLIError


def get_environment_var_name(service_name, reference_name):
    """
    Gets the environment variable name for a reference
    """
    return '{}_{}_connection_string'.format(service_name.replace('-', '_'), reference_name).upper()


def get_secret_name(service_name, reference_name):
    """
    Gets the secret name for provided service and
    reference name
    """
    return '{}-{}'.format(service_name, reference_name).lower()


def create_connection_string(service_name, reference_name, connection_string):
    """
    Creates a secret on Kubernetes that stores
    the connection string and is labeled with run=service_name
    """
    secret_name = get_secret_name(service_name, reference_name)
    environment_variable_name = get_environment_var_name(
        service_name, reference_name)

    # Create the secret
    command = 'kubectl create secret generic {} --from-literal={}={}'.format(
        secret_name, environment_variable_name, connection_string)
    utils.execute_command(command)

    # Label it with run=service_name
    label_command = 'kubectl label secret {} run={}'.format(
        secret_name, service_name)
    utils.execute_command(label_command)


def remove_reference(service_name, reference_name):
    """
    Removes the reference by deleting the created secret
    and removing it from the project settings file.
    """
    project_settings = settings.Project()
    project_settings.remove_reference(service_name, reference_name)
    command = 'kubectl delete secret {}'.format(
        get_secret_name(service_name, reference_name))
    utils.execute_command(command, ignore_failure=True)


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
        raise CLIError(exc)

    return None, None
