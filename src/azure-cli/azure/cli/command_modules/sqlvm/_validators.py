# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
import json
from azure.mgmt.core.tools import resource_id, is_valid_resource_id
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    MutuallyExclusiveArgumentError
)
from azure.cli.core.commands.client_factory import get_subscription_id

from knack.log import get_logger
logger = get_logger(__name__)


# pylint: disable=too-many-statements,line-too-long
def validate_sqlvm_group(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the group is in the same resource group.
    '''
    group = namespace.sql_virtual_machine_group_resource_id

    if group and not is_valid_resource_id(group):
        namespace.sql_virtual_machine_group_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.SqlVirtualMachine', type='sqlVirtualMachineGroups',
            name=group
        )


# pylint: disable=too-many-statements,line-too-long
def validate_sqlvm_list(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the vm is in the same resource group.
    '''
    vms = namespace.sql_virtual_machine_instances

    for n, sqlvm in enumerate(vms):
        if sqlvm and not is_valid_resource_id(sqlvm):
            # add the correct resource id
            namespace.sql_virtual_machine_instances[n] = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.SqlVirtualMachine', type='sqlVirtualMachines',
                name=sqlvm
            )


# pylint: disable=too-many-statements,line-too-long
def validate_load_balancer(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the load balancer is in the same group.
    '''
    lb = namespace.load_balancer_resource_id

    if not is_valid_resource_id(lb):
        namespace.load_balancer_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network', type='loadBalancers',
            name=lb
        )


# pylint: disable=too-many-statements,line-too-long
def validate_public_ip_address(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the public ip address is in the same group.
    '''
    public_ip = namespace.public_ip_address_resource_id

    if public_ip and not is_valid_resource_id(public_ip):
        namespace.public_ip_address_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network', type='publicIPAddresses',
            name=public_ip
        )


# pylint: disable=too-many-statements,line-too-long
def validate_subnet(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the public ip address is in the same group.
    '''
    subnet = namespace.subnet_resource_id
    vnet = namespace.vnet_name

    if vnet and '/' in vnet:
        raise InvalidArgumentValueError("incorrect usage: --subnet ID | --subnet NAME --vnet-name NAME")

    subnet_is_id = is_valid_resource_id(subnet)
    if (subnet_is_id and vnet) or (not subnet_is_id and not vnet):
        raise MutuallyExclusiveArgumentError("incorrect usage: --subnet ID | --subnet NAME --vnet-name NAME")

    if not subnet_is_id and vnet:
        namespace.subnet_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network', type='virtualNetworks',
            name=vnet, child_type_1='subnets',
            child_name_1=subnet
        )


# pylint: disable=too-many-statements,line-too-long
def validate_sqlmanagement(namespace):
    '''
    Validates if sql management mode provided, the offer type and sku type has to be provided.
    '''
    sql_mgmt_mode = namespace.sql_management_mode

    if (sql_mgmt_mode == "NoAgent" and (namespace.sql_image_sku is None or namespace.sql_image_offer is None)):
        raise RequiredArgumentMissingError("usage error: --sql-mgmt-type NoAgent --image-sku NAME --image-offer NAME")


# pylint: disable=too-many-statements,line-too-long
def validate_least_privilege_mode(namespace):
    '''
    Validates if least privilege mode provided, management mode is Full
    '''
    least_privilege_mode = namespace.least_privilege_mode

    if (least_privilege_mode == "Enabled" and (namespace.sql_management_mode is None or namespace.sql_management_mode != "Full")):
        raise RequiredArgumentMissingError("usage error: --least-privilege-mode Enabled --sql-mgmt-type Full")


# pylint: disable=too-many-statements,line-too-long
def validate_expand(namespace):
    '''
    Concatenates expand parameters
    '''
    if namespace.expand is not None:
        namespace.expand = ",".join(namespace.expand)


# pylint: disable=too-many-statements,line-too-long
def validate_assessment(namespace):
    '''
    Validates assessment settings
    '''
    enable_assessment = namespace.enable_assessment
    enable_assessment_schedule = namespace.enable_assessment_schedule
    assessment_weekly_interval = namespace.assessment_weekly_interval
    assessment_monthly_occurrence = namespace.assessment_monthly_occurrence
    assessment_day_of_week = namespace.assessment_day_of_week
    assessment_start_time_local = namespace.assessment_start_time_local

    is_assessment_schedule_provided = False
    if (assessment_weekly_interval is not None or
            assessment_weekly_interval is not None or assessment_monthly_occurrence is not None or
            assessment_day_of_week is not None or assessment_start_time_local is not None):
        is_assessment_schedule_provided = True

    # Should we add new validations for workspace rg, name, agent rg here?
    # Validate conflicting settings
    if (enable_assessment_schedule is False and is_assessment_schedule_provided):
        raise InvalidArgumentValueError("Assessment schedule settings cannot be provided while enable-assessment-schedule is False")

    # Validate conflicting settings
    if (enable_assessment is False and is_assessment_schedule_provided):
        raise InvalidArgumentValueError("Assessment schedule settings cannot be provided while enable-assessment is False")

    # Validate necessary fields for Assessment schedule
    if is_assessment_schedule_provided:
        if (assessment_weekly_interval is not None and assessment_monthly_occurrence is not None):
            raise MutuallyExclusiveArgumentError("Both assessment-weekly-interval and assessment-montly-occurrence cannot be provided at the same time for Assessment schedule")
        if (assessment_weekly_interval is None and assessment_monthly_occurrence is None):
            raise RequiredArgumentMissingError("Either assessment-weekly-interval or assessment-montly-occurrence must be provided for Assessment schedule")
        if assessment_day_of_week is None:
            raise RequiredArgumentMissingError("assessment-day-of-week must be provided for Assessment schedule")
        if assessment_start_time_local is None:
            raise RequiredArgumentMissingError("assessment-start-time-local must be provided for Assessment schedule")


# pylint: disable=too-many-statements,line-too-long
def validate_assessment_start_time_local(namespace):
    '''
    Validates assessment start time format
    '''
    assessment_start_time_local = namespace.assessment_start_time_local

    TIME_FORMAT = '%H:%M'
    if assessment_start_time_local:
        try:
            datetime.strptime(assessment_start_time_local, TIME_FORMAT)
        except ValueError:
            raise InvalidArgumentValueError("assessment-start-time-local input '{}' is not valid time. Valid example: 19:30".format(assessment_start_time_local))


# pylint: disable=too-many-statements,line-too-long
def validate_azure_ad_authentication(cmd, namespace):
    """ Validates Azure AD authentication.

        :param cli_ctx: The CLI context.
        :type cli_ctx: AzCli.
        :param namespace: The argparse namespace represents the arguments.
        :type namespace: argpase.Namespace.
    """

    skip_client_validation = False
    if hasattr(namespace, "skip_client_validation"):
        skip_client_validation = getattr(namespace, "skip_client_validation")

    if skip_client_validation is True:
        logger.warning('Skipping client-side validation ...')
        return

    logger.debug("Validate Azure AD authentication from client-side:")

    # SQL VM Azure AD authentication is currently only supported on Azure Public Cloud
    from azure.cli.core.cloud import AZURE_PUBLIC_CLOUD
    if cmd.cli_ctx.cloud.name != AZURE_PUBLIC_CLOUD.name:
        raise InvalidArgumentValueError("Azure AD authentication is not supported in {}".format(cmd.ctx_cli.cloud.name))

    # validate the SQL VM supports Azure AD authentication, i.e. it is on Windows platform and is SQL 2022 or later
    # this validation will take place in RP call

    # validate the MSI is valid on the Azure virtual machine
    principal_id = _validate_msi_valid_on_vm(cmd.cli_ctx, namespace)
    logger.debug("Validate Azure AD authentication: the managed identity is valid with a principalId %s.", principal_id)

    # validate the MSI has appropriate permission to query Microsoft Graph API
    _validate_msi_with_enough_permission(cmd.cli_ctx, principal_id)
    logger.debug("Validate Azure AD authentication: the managed identity has required Graph API permission.")


def _validate_msi_valid_on_vm(cli_ctx, namespace):
    """ Validate the MSI is valid on the Azure virtual machine return the principalId of the MSI

        :param cli_ctx: The CLI context.
        :type cli_ctx: AzCli.
        :param namespace: The argparse namespace represents the arguments.
        :type namespace: argpase.Namespace.

        :return: The principalId of the MSI if found on this VM.
        :rtype: str
    """
    logger.debug("Validate Azure AD authentication regarding the validity of the managed identity.")

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    compute_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE)

    # Retrieve the vm instance. This is a rest call to the server and deserialization afterwards
    # therefore there is a greater chance to encouter an exception. Instead of poping the exception
    # to the caller directly, we will throw our own InvalidArgumentValueError with more context
    # information.
    try:
        # Azure virtual machine has the same name as the SQL VM
        vm = compute_client.virtual_machines.get(namespace.resource_group_name, namespace.sql_virtual_machine_name)
    except Exception as ex:
        raise InvalidArgumentValueError("Unable to validate Azure AD authentication due to retrieving the Azure virtual machine instance encountering an error: {}.".format(ex)) from ex

    # The system-assigned MSI case.
    if namespace.msi_client_id is None:
        if vm.identity is None or not hasattr(vm.identity, 'principal_id') or getattr(vm.identity, 'principal_id') is None:
            az_error = InvalidArgumentValueError("Enable Azure AD authentication with system-assigned managed identity but the system-assigned managed identity is not enabled on this Azure virtual machine.")
            az_error.set_recommendation("Enable the system-assigned managed identity on the Azure virtual machine: {}.".format(namespace.sql_virtual_machine_name))
            raise az_error

        return vm.identity.principal_id

    # The user-assigned MSI case.
    if vm.identity is None or not hasattr(vm.identity, 'user_assigned_identities') or getattr(vm.identity, 'user_assigned_identities') is None:
        az_error = InvalidArgumentValueError("Enable Azure AD authentication with user-assigned managed identity {}, but the managed identity is not attached to this Azure virtual machine.".format(namespace.msi_client_id))
        az_error.set_recommendation("Attach the user-assigned managed identity {} to the Azure virtual machine {}.".format(namespace.msi_client_id, namespace.sql_virtual_machine_name))
        raise az_error

    for umi in vm.identity.user_assigned_identities.values():
        if umi.client_id == namespace.msi_client_id:
            return umi.principal_id

    az_error = InvalidArgumentValueError("Enable Azure AD authentication with user-assigned managed identity {}, but the managed identity is not attached to this Azure virtual machine.".format(namespace.msi_client_id))
    az_error.set_recommendation("Attach the user-assigned managed identity {} to the Azure virtual machine {}.".format(namespace.msi_client_id, namespace.sql_virtual_machine_name))
    raise az_error


# Validate the MSI has appropriate permissions to query Microsoft Graph API.
USER_READ_ALL = "User.Read.All"
APPLICATION_READ_ALL = "Application.Read.All"
GROUP_MEMBER_READ_ALL = "GroupMember.Read.All"


def _validate_msi_with_enough_permission(cli_ctx, principal_id):
    """ Validate the MSI has enough permissions to query Microsoft Graph API, which are needed for SQL server to
        carry out the Azure AD authentication.

        :param cli_ctx: The CLI context.
        :type cli_ctx: AzCli.
        :param principal_id: The principalId of the MSI.
        :type principal_id: str.
    """
    logger.debug("Validate Azure AD authentication regarding required Graph API permission.")

    directory_roles = _directory_role_list(cli_ctx, principal_id)

    # If the MSI is assigned the "Directory Readers" role, it has enough permissions.
    if any(role["displayName"] == "Directory Readers" for role in directory_roles):
        return

    # If the MSI is not assigned the "Directory Readers" role, check the app roles.
    # Retrieve the app role Id for User.Read.All, Application.Read.All, GroupMember.Read.All roles.
    app_role_id_map = _find_role_id(cli_ctx)
    logger.debug("Validate Azure AD authentication: app role to app role Id map:%s.", str(app_role_id_map))

    # Retrieve all the role assignments assigned to the MSI
    app_role_assignments = _app_role_assignment_list(cli_ctx, principal_id)
    all_assigned_role_ids = [assignment["appRoleId"] for assignment in app_role_assignments]

    # Find all the missing roles.
    required_role_names = [USER_READ_ALL, APPLICATION_READ_ALL, GROUP_MEMBER_READ_ALL]
    missing_roles = [role_name for role_name in required_role_names if app_role_id_map[role_name] not in all_assigned_role_ids]

    if len(missing_roles) > 0:
        az_error = InvalidArgumentValueError("The managed identity is lack of the following roles for Azure AD authentication: {}.".format(", ".join(missing_roles)))
        az_error.set_recommendation("Grant the managed identity EITHER the Directory.Readers role OR the three App roles 'User.Read.All', 'Application.Read.All', 'GroupMember.Read.All'")
        raise az_error


MICROSOFT_GRAPH_API_ERROR = "Unable to validate the permission of MSI due to querying Microsoft Graph API encountered error: {}."


def _send(cli_ctx, method, url, param=None, body=None):
    """ Send the HTTP requet to the url
        Copied from src/azure-cli/azure/cli/command_modules/role/_msgrpah/_graph_client.py with minor modification

        :param cli_ctx: The CLI context.
        :type cli_ctx: AzCli.
        :param method: The HTTP method.
        :type method: str.
        :param url: The target HTTP url.
        :type url: str.
        :param param: The HTTP query parameters.
        :type param: str.
        :param body: The HTTP body as python object.
        :type body: object.
    """

    from azure.cli.core.util import send_raw_request

    # Get the Microsoft Graph API endpoint from CLI metadata
    # https://graph.microsoft.com/ (AzureCloud)
    graph_endpoint = cli_ctx.cloud.endpoints.microsoft_graph_resource_id.rstrip('/')
    graph_resource = cli_ctx.cloud.endpoints.microsoft_graph_resource_id

    # Microsoft Graph API version to use
    MICROSOFT_GRAPH_API_VERSION = "v1.0"
    url = f'{graph_endpoint}/{MICROSOFT_GRAPH_API_VERSION}{url}'

    if body:
        body = json.dumps(body)

    list_result = []
    is_list_result = False

    while True:
        try:
            r = send_raw_request(cli_ctx, method, url, resource=graph_resource, uri_parameters=param, body=body)
        except Exception as ex:
            raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(ex)) from ex

        if r.text:
            if 'InternalServerError' in r.text:
                return None

            dic = r.json()

            # The result is a list. Add value to list_result.
            if 'value' in dic:
                is_list_result = True
                list_result.extend(dic['value'])

            # Follow nextLink if available
            if '@odata.nextLink' in dic:
                url = dic['@odata.nextLink']
                continue

            # Result a list
            if is_list_result:
                # 'value' can be empty list [], so we can't determine if the result is a list only by
                # bool(list_result)
                return list_result

            # Return a single object
            return r.json()
        return None


# https://graph.microsoft.com/v1.0/servicePrincipals/{principalId}/transitiveMemberOf/microsoft.graph.directoryRole
# retrieve all directory role assigned to a service principal
def _directory_role_list(cli_ctx, principal_id):
    logger.debug("Retrieving transitive directory roles of a MSI from Graph API with server side filtering.")
    DIRECTORY_ROLE_URL = "/servicePrincipals/{}/transitiveMemberOf/microsoft.graph.directoryRole"
    try:
        role_list = _send(cli_ctx, "GET", DIRECTORY_ROLE_URL.format(principal_id))
        if role_list is None:
            logger.warning("Graph API server side filtering failed, Retry retrieving transitive directory roles of a MSI from Graph API with client side filtering. It is NOT a failure.")
            role_list = _directory_role_list2(cli_ctx, principal_id)
        return role_list
    except Exception as ex:
        raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(ex)) from ex


# https://graph.microsoft.com/v1.0/servicePrincipals/{principalId}/transitiveMemberOf
# Currently there is a bug in Graph API that causes internal server error in the Graph API service side filtering
# when the MSI is a member of an AAD group. The ICM incident is as below:
# https://portal.microsofticm.com/imp/v3/incidents/details/392112435/home
#
# This method is doing the same thing as _directory_role_list but via client side filtering.
def _directory_role_list2(cli_ctx, principal_id):
    DIRECTORY_ROLE_CLIENT_FILTERING_URL = "/servicePrincipals/{}/transitiveMemberOf"
    try:
        role_list = _send(cli_ctx, "GET", DIRECTORY_ROLE_CLIENT_FILTERING_URL.format(principal_id))

        # Filter out the directory role
        return [role for role in role_list if role["@odata.type"] == "#microsoft.graph.directoryRole"]
    except Exception as ex:
        raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(ex)) from ex


# https://graph.microsoft.com/v1.0/servicePrincipals/{principalId}/appRoleAssignments
# retrieve all app role assignments to a service principal
def _app_role_assignment_list(cli_ctx, principal_id):
    APP_ROLE_ASSIGNMENT_URL = "/servicePrincipals/{}/appRoleAssignments"
    try:
        return _send(cli_ctx, "GET", APP_ROLE_ASSIGNMENT_URL.format(principal_id))
    except Exception as ex:
        raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(ex)) from ex


# https://graph.microsoft.com/v1.0/servicePrincipals?$filter=displayName%20eq%20'Microsoft%20Graph'
# this is a best effor retrieval
def _find_role_id(cli_ctx):
    """ Find the appRoleId for the following three app roles User.Read.All, Application.Read.All, GroupMember.Read.All.

        :param cli_ctx: The CLI context.
        :type cli_ctx: AzCli.

        :return: The app role name to appRoleId map
        :rtype: dict
    """
    app_role_id_map = {}

    MICROSOFT_GRAPH_URL = "/servicePrincipals?$filter=displayName%20eq%20'Microsoft%20Graph'"
    try:
        service_principals = _send(cli_ctx, "GET", MICROSOFT_GRAPH_URL)
    except Exception as ex:  # pylint: disable=broad-except
        raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(ex)) from ex

    # If we failed to find the Microsoft Graph service application, fail the validation.
    # This in fact shoud not happen.
    if service_principals is None or len(service_principals) == 0:
        error_message = "Querying Microsoft Graph API failed to find the service principal of Microsoft Graph Application"
        raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(error_message))

    app_roles = service_principals[0]['appRoles']
    for app_role in app_roles:
        if app_role["value"] == USER_READ_ALL:
            app_role_id_map[USER_READ_ALL] = app_role["id"]
        elif app_role["value"] == APPLICATION_READ_ALL:
            app_role_id_map[APPLICATION_READ_ALL] = app_role["id"]
        elif app_role["value"] == GROUP_MEMBER_READ_ALL:
            app_role_id_map[GROUP_MEMBER_READ_ALL] = app_role["id"]

    # If we failed to find all role definitions, fail the validation.
    # This in fact shoud not happen.
    if len(app_role_id_map) < 3:
        requird_role_defs = [USER_READ_ALL, APPLICATION_READ_ALL, GROUP_MEMBER_READ_ALL]
        missing_role_defs = [role for role in requird_role_defs if role not in app_role_id_map]
        error_message = "Querying Microsoft Graph API failed to find the following roles: %s.", ", ".join(missing_role_defs)
        logger.warning(error_message)

        raise InvalidArgumentValueError(MICROSOFT_GRAPH_API_ERROR.format(error_message))

    return app_role_id_map
