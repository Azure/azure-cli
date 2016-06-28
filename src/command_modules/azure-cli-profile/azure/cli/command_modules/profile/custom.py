# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use
#TODO: update adal-python to support it
#from azure.cli._debug import should_disable_connection_verify
import datetime
import uuid
from dateutil.relativedelta import relativedelta

from adal.adal_error import AdalError

from azure.graphrbac.models import (ApplicationCreateParameters,
                                    ApplicationUpdateParameters,
                                    PasswordCredential)
from azure.graphrbac import GraphRbacManagementClient

from azure.cli._profile import Profile
from azure.cli._util import CLIError
import azure.cli._logging as _logging

logger = _logging.get_az_logger(__name__)

def load_subscriptions():
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions()
    return subscriptions

def list_subscriptions():
    '''List the imported subscriptions.'''
    subscriptions = load_subscriptions()
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    return subscriptions

def set_active_subscription(subscription_name_or_id):
    '''Set the current subscription'''
    if not id:
        raise CLIError('Please provide subscription id or unique name.')
    profile = Profile()
    profile.set_active_subscription(subscription_name_or_id)

def account_clear():
    '''Clear all stored subscriptions. To clear individual, use \'logout\''''
    profile = Profile()
    profile.logout_all()

def login(username=None, password=None, service_principal=None, tenant=None):
    '''Log in to an Azure subscription using Active Directory Organization Id'''
    interactive = False

    if username:
        if not password:
            import getpass
            password = getpass.getpass('Password: ')
    else:
        interactive = True

    profile = Profile()
    try:
        subscriptions = profile.find_subscriptions_on_login(
            interactive,
            username,
            password,
            service_principal,
            tenant)
    except AdalError as err:
        raise CLIError(err)
    return list(subscriptions)

def logout(username):
    '''Log out from Azure subscription using Active Directory.'''
    profile = Profile()
    profile.logout(username)

def list_location():
    from azure.cli.commands.parameters import get_subscription_locations
    return get_subscription_locations()

def create_service_principal(name=None, secret=None, years=1):
    '''create a service principal you can use with login command

    :param str name: an unique uri. If missing, the command will generate one.
    :param str secret: the secret used to login. If missing, command will generate one.
    :param str years: Years the secret will be valid.
    '''
    start_date = datetime.datetime.now()
    app_display_name = 'azure-cli-' + start_date.strftime('%Y-%m-%d-%H-%M-%S')
    if name is None:
        name = 'http://' + app_display_name

    key_id = str(uuid.uuid4())
    end_date = start_date + relativedelta(years=years)
    secret = secret or str(uuid.uuid4())
    app_cred = PasswordCredential(start_date, end_date, key_id, secret)
    app_create_param = ApplicationCreateParameters(False, app_display_name,
                                                   'http://'+app_display_name, [name],
                                                   password_credentials=[app_cred])

    profile = Profile()
    cred, _, tenant = profile.get_login_credentials(for_graph_client=True)

    client = GraphRbacManagementClient(cred, tenant)

    #pylint: disable=no-member
    aad_application = client.applications.create(app_create_param)
    aad_sp = client.service_principals.create(aad_application.app_id, True)

    _build_output_content(name, aad_sp.object_id, secret, tenant)

def reset_service_principal_credential(name, secret=None, years=1):
    '''reset credential, on expiration or you forget it.

    :param str name: the uri representing the name of the service principal
    :param str secret: the secret used to login. If missing, command will generate one.
    :param str years: Years the secret will be valid.
    '''
    profile = Profile()
    cred, _, tenant = profile.get_login_credentials(for_graph_client=True)
    client = GraphRbacManagementClient(cred, tenant)

    #pylint: disable=no-member

    #look for the existing application
    query_exp = 'identifierUris/any(x:x eq \'{}\')'.format(name)
    aad_apps = list(client.applications.list(filter=query_exp))
    if not aad_apps:
        raise CLIError('can\'t find a graph application matching \'{}\''.format(name))
    #no need to check 2+ matches, as app id uri is unique
    app = aad_apps[0]

    #look for the existing service principal
    query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format(name)
    aad_sps = list(client.service_principals.list(filter=query_exp))
    if not aad_sps:
        raise CLIError('can\'t find an service principal matching \'{}\''.format(name))
    sp_object_id = aad_sps[0].object_id

    #build a new password credential and patch it
    secret = secret or str(uuid.uuid4())
    start_date = datetime.datetime.now()
    end_date = start_date + relativedelta(years=years)
    key_id = str(uuid.uuid4())
    app_cred = PasswordCredential(start_date, end_date, key_id, secret)
    app_create_param = ApplicationUpdateParameters(password_credentials=[app_cred])

    client.applications.patch(app.object_id, app_create_param)

    _build_output_content(name, sp_object_id, secret, tenant)

def _build_output_content(sp_name, sp_object_id, secret, tenant):
    logger.warning("Service principal has been configured with name: '%s', secret: '%s'",
                   sp_name, secret)
    logger.warning('Useful commands to manage azure:')
    logger.warning('  Assign a role: "az role assignment create --object-id %s --role Contributor"',
                   sp_object_id)
    logger.warning('  Log in: "az login --service-principal -u %s -p %s --tenant %s"',
                   sp_name, secret, tenant)
    logger.warning('  Reset credentials: "az account reset-sp-credentials --name %s"',
                   sp_name)

