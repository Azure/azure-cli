from .._logging import logging
from ..main import CONFIG, SESSION
from ..commands import command, description, option

PII_WARNING_TEXT = _(
    'If you choose to continue, Azure command-line interface will cache your '
    'authentication information. Note that this sensitive information will be stored in '
    'plain text on the file system of your computer at {}. Ensure that you take suitable '
    'precautions to protect your computer from unauthorized access in order to minimize the '
    'risk of that information being disclosed.'
    '\nDo you wish to continue: (y/n) '
)

@command('login')
@description('logs you in')
@option('--username -u <username>', _('user name or service principal ID. If multifactor authentication is required, '
                                      'you will be prompted to use the login command without parameters for '
                                      'interactive support.'))
@option('--environment -e <environment>', _('Environment to authenticate against, such as AzureChinaCloud; '
                                            'must support active directory.'))
@option('--password -p <password>', _('user password or service principal secret, will prompt if not given.'))
@option('--service-principal', _('If given, log in as a service principal rather than a user.'))
@option('--certificate-file <certificateFile>', _('A PEM encoded certificate private key file.'))
@option('--thumbprint <thumbprint>', _('A hex encoded thumbprint of the certificate.')) 
@option('--tenant <tenant>', _('Tenant domain or ID to log into.')) 
@option('--quiet -q', _('do not prompt for confirmation of PII storage.')) 
def login(args, unexpected):
    username = args.get('username')
    interactive = bool(username)

    environment_name = args.get('environment') or 'AzureCloud'
    environment = CONFIG['environments'].get(environment_name)
    if not environment:
        raise RuntimeError(_('Unknown environment {0}').format(environment_name))

    tenant = args.get('tenant')
    if args.get('service-principal') and not tenant:
        tenant = input(_('Tenant: '))

    # TODO: PII warning

    password = args.get('password')
    require_password = not args.get('service-principal') or not args.get('certificate-file')
    if not interactive and require_password and not password:
        import getpass
        password = getpass.getpass(_('Password: '))

    if not require_password:
        password = {
            'certificateFile': args['certificate-file'],
            'thumbprint': args.thumbprint,
        }

    if not interactive:
        # TODO: Remove cached token
        SESSION.pop(username + '_token', None)

    # TODO: Perform login
    token = ''

    SESSION[username + '_token'] = token

    # TODO: Get subscriptions
    subscriptions = ['not-a-real-subscription']
    if not subscriptions:
        raise RuntimeError(_("No subscriptions found for this account"))

    active_subscription = subscriptions[0]

    logging.info(_('Setting subscription %s as default'), active_subscription)
    SESSION['active_subscription'] = active_subscription
