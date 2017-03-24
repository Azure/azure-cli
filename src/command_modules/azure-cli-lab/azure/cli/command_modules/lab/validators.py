# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import dateutil.parser

from msrestazure.azure_exceptions import CloudError
from azure.cli.core._util import CLIError
from azure.cli.core.commands.arm import resource_id, is_valid_resource_id
from ._client_factory import (get_devtestlabs_management_client)
from .sdk.devtestlabs.models.gallery_image_reference import GalleryImageReference
from azure.graphrbac import GraphRbacManagementClient
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)
devtestlabs_management_client = get_devtestlabs_management_client(None)

# Message for using defaults
DEFAULT_MESSAGE_FORMAT = 'Using %s : %s'


def get_complex_argument_processor(expanded_arguments, assigned_arg, model_type):
    """
    Return a validator which will aggregate multiple arguments to one complex argument.
    """
    def _expension_valiator_impl(namespace):
        """
        The validator create a argument of a given type from a specific set of arguments from CLI
        command.
        :param namespace: The argparse namespace represents the CLI arguments.
        :return: The argument of specific type.
        """
        ns = vars(namespace)
        kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))

        setattr(namespace, assigned_arg, model_type(**kwargs))

    return _expension_valiator_impl


def validate_lab_vm_create(namespace):
    """ Validates parameters for lab vm create and updates namespace. """
    formula = None
    if namespace.formula is True:
        formula = _get_formula(namespace)

    _validate_location(namespace)
    _validate_expiration_date(namespace)
    _validate_image_argument(namespace, formula)
    validate_authentication_type(namespace, formula)
    _validate_network_parameters(namespace, formula)
    _validate_other_parameters(namespace, formula)


def validate_lab_vm_list(namespace):
    """ Validates parameters for lab vm list and updates namespace. """
    collection = [namespace.filters, namespace.my_vms, namespace.claimable]
    if not _single(collection):
        raise CLIError("usage error: [--filters FILTER | --my-vms | --claimable]")

    if namespace.my_vms:
        # Find out owner object id
        from azure.cli.core._profile import Profile, CLOUD
        profile = Profile()
        cred, _, tenant_id = profile.get_login_credentials(
            resource=CLOUD.endpoints.active_directory_graph_resource_id)
        graph_client = GraphRbacManagementClient(cred,
                                                 tenant_id,
                                                 base_url=CLOUD.endpoints.active_directory_graph_resource_id)
        subscription = profile.get_subscription()
        object_id = namespace.object_id or _get_object_id(graph_client, subscription=subscription)
        namespace.filters = "Properties/ownerObjectId eq '{}'".format(object_id)
    elif namespace.claimable:
        namespace.filters = 'properties/allowClaim'
    else:
        namespace.filters = namespace.filters


def _get_formula(namespace):
    """ Get formula from the lab """
    formula_operation = devtestlabs_management_client.formula
    return formula_operation.get_resource(namespace.resource_group, namespace.lab_name, namespace.image)


def _validate_location(namespace):
    """
    Selects the default location of the lab when location is not provided.
    """
    if namespace.location is None:
        lab_operation = devtestlabs_management_client.lab
        lab = lab_operation.get_resource(namespace.resource_group, namespace.lab_name)
        namespace.location = lab.location


def _validate_expiration_date(namespace):
    """ Validates expiration date if provided. """

    if namespace.expiration_date:
        if datetime.datetime.utcnow().date() >= dateutil.parser.parse(namespace.expiration_date).date():
            raise CLIError("Expiration date '{}' must be in future.".format(namespace.expiration_date))


def _validate_network_parameters(namespace, formula=None):
    """ Selects lab's virtual network and subnet if not provided and updates namespace """
    from azure.cli.core.commands.client_factory import get_subscription_id
    vnet_operation = devtestlabs_management_client.virtual_network

    if formula and formula.formula_content:
        if formula.formula_content.lab_virtual_network_id:
            namespace.vnet_name = namespace.vnet_name or formula.formula_content.lab_virtual_network_id.split('/')[-1]
            logger.warning(DEFAULT_MESSAGE_FORMAT, 'vnet_name', namespace.vnet_name)
        if formula.formula_content.lab_virtual_network_id:
            namespace.subnet = namespace.subnet or formula.formula_content.lab_subnet_name
            namespace.disallow_public_ip_address = namespace.disallow_public_ip_address or formula.formula_content.disallow_public_ip_address
            logger.warning(DEFAULT_MESSAGE_FORMAT, 'lab_subnet_name', namespace.subnet)

    if not namespace.vnet_name:
        lab_vnets = list(vnet_operation.list(namespace.resource_group, namespace.lab_name, top=1))
        if not lab_vnets:
            err = "Unable to find any virtual network in the '{}' lab.".format(namespace.lab_name)
            raise CLIError(err)
        else:
            lab_vnet = lab_vnets[0]
            namespace.vnet_name = lab_vnet.name
            namespace.lab_virtual_network_id = lab_vnet.id
    else:
        namespace.lab_virtual_network_id = resource_id(subscription=get_subscription_id(),
                                                       resource_group=namespace.resource_group,
                                                       namespace='microsoft.devtestlab',
                                                       type='labs',
                                                       name=namespace.lab_name,
                                                       child_type='virtualnetworks',
                                                       child_name=namespace.vnet_name)

    # Select default subnet for selected vnet when subnet is not provided
    if not namespace.subnet:
        # Get the first subnet of the lab's virtual network
        lab_vnet = vnet_operation.get_resource(namespace.resource_group, namespace.lab_name, namespace.vnet_name)
        namespace.subnet = lab_vnet.subnet_overrides[0].lab_subnet_name

        # Determine value for disallow_public_ip_address based on subnet's use_public_ip_address_permission property
        if lab_vnet.subnet_overrides[0].use_public_ip_address_permission == 'Allow':
            namespace.disallow_public_ip_address = False
        else:
            namespace.disallow_public_ip_address = True


def _validate_image_argument(namespace, formula=None):
    image_type = None
    if formula:
        if formula.formula_content and formula.formula_content.gallery_image_reference:
            namespace.os_offer = formula.formula_content.gallery_image_reference.offer
            namespace.os_publisher = formula.formula_content.gallery_image_reference.publisher
            namespace.os_type = formula.formula_content.gallery_image_reference.os_type
            namespace.os_sku = formula.formula_content.gallery_image_reference.sku
            namespace.os_version = formula.formula_content.gallery_image_reference.version
            image_type = 'gallery_image'
        elif formula.formula_content and formula.formula_content.custom_image_id:
            namespace.custom_image_id = namespace.image
            image_type = 'image_id'

    image_type = image_type or _parse_image_argument(namespace)

    if image_type == 'gallery_image':
        namespace.gallery_image_reference = GalleryImageReference(offer=namespace.os_offer,
                                                                  publisher=namespace.os_publisher,
                                                                  os_type=namespace.os_type,
                                                                  sku=namespace.os_sku,
                                                                  version=namespace.os_version)
        namespace.notes = namespace.notes or namespace.image
    else:
        namespace.custom_image_id = namespace.image


def _parse_image_argument(namespace):
    # 1 - check if a fully-qualified ID (assumes it is an image ID)
    if is_valid_resource_id(namespace.image):
        return 'image_id'

    # 2 - check if an existing lab Gallery Image Reference
    try:
        gallery_image_operation = devtestlabs_management_client.gallery_image
        odata_filter = "name eq '{}'".format(namespace.image)
        lab_images = list(gallery_image_operation.list(namespace.resource_group, namespace.lab_name, filter=odata_filter))

        if not lab_images:
            err = "Unable to find image name '{}' in the '{}' lab Gallery.".format(namespace.image, namespace.lab_name)
            raise CLIError(err)
        elif len(lab_images) > 1:
            err = "Found more than 1 image with name "'{}'". Please pick one from {}"
            raise CLIError(err.format(namespace.image, [x['name'] for x in lab_images]))
        else:
            image = lab_images[0]
            namespace.os_offer = image.image_reference.offer
            namespace.os_publisher = image.image_reference.publisher
            namespace.os_sku = image.image_reference.sku
            namespace.os_type = image.image_reference.os_type
            namespace.os_version = image.image_reference.version
        return 'gallery_image'
    except CloudError:
        err = "Invalid image "'{}'". Use a custom image id or pick one from lab Gallery"
        raise CLIError(err.format(namespace.image))


def _validate_other_parameters(namespace, formula):
    if formula:
        namespace.tags = formula.tags
        if formula.formula_content:
            namespace.allow_claim = namespace.allow_claim or formula.formula_content.allow_claim
            namespace.artifacts = namespace.artifacts or formula.formula_content.artifacts
            namespace.notes = namespace.notes or formula.formula_content.notes
            namespace.size = namespace.size or formula.formula_content.size
            logger.warning(DEFAULT_MESSAGE_FORMAT, 'artifacts', namespace.artifacts)


# TODO: Following methods are carried over from other command modules
def validate_authentication_type(namespace, formula=None):
    if formula and formula.formula_content:
        if formula.formula_content.is_authentication_with_ssh_key is True:
            namespace.authentication_type = 'ssh'
            namespace.ssh_key = formula.formula_content.ssh_key
        elif formula.formula_content.is_authentication_with_ssh_key is False:
            namespace.admin_username = formula.formula_content.user_name
            namespace.admin_password = formula.formula_content.password
            namespace.authentication_type = 'password'

    # validate proper arguments supplied based on the authentication type
    if namespace.authentication_type == 'password':
        if namespace.ssh_key or namespace.generate_ssh_keys:
            raise ValueError(
                "incorrect usage for authentication-type 'password': "
                "[--admin-username USERNAME] --admin-password PASSWORD")

        if not namespace.admin_password:
            # prompt for admin password if not supplied
            from azure.cli.core.prompting import prompt_pass, NoTTYException
            try:
                namespace.admin_password = prompt_pass('Admin Password: ', confirm=True)
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')

    elif namespace.authentication_type == 'ssh':
        if namespace.admin_password:
            raise ValueError('Admin password cannot be used with SSH authentication type')

        validate_ssh_key(namespace)
    else:
        raise CLIError("incorrect value for authentication-type: {}".format(namespace.authentication_type))


def validate_ssh_key(namespace):
    string_or_file = (namespace.ssh_key or
                      os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub'))
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not _is_valid_ssh_rsa_public_key(content):
        if namespace.generate_ssh_keys:
            # figure out appropriate file names:
            # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
            public_key_filepath = string_or_file
            if public_key_filepath[-4:].lower() == '.pub':
                private_key_filepath = public_key_filepath[:-4]
            else:
                private_key_filepath = public_key_filepath + '.private'
            content = _generate_ssh_keys(private_key_filepath, public_key_filepath)
            logger.warning('Created SSH key files: %s,%s',
                           private_key_filepath, public_key_filepath)
        else:
            raise CLIError('An RSA key file or key value must be supplied to SSH Key Value. '
                           'You can use --generate-ssh-keys to let CLI generate one for you')
    namespace.ssh_key = content


def _generate_ssh_keys(private_key_filepath, public_key_filepath):
    import paramiko

    ssh_dir, _ = os.path.split(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        os.chmod(ssh_dir, 0o700)

    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(private_key_filepath)
    os.chmod(private_key_filepath, 0o600)

    with open(public_key_filepath, 'w') as public_key_file:
        public_key = '%s %s' % (key.get_name(), key.get_base64())
        public_key_file.write(public_key)
    os.chmod(public_key_filepath, 0o644)

    return public_key


def _is_valid_ssh_rsa_public_key(openssh_pubkey):
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression # pylint: disable=line-too-long
    # A "good enough" check is to see if the key starts with the correct header.
    import struct
    try:
        from base64 import decodebytes as base64_decode
    except ImportError:
        # deprecated and redirected to decodebytes in Python 3
        from base64 import decodestring as base64_decode
    parts = openssh_pubkey.split()
    if len(parts) < 2:
        return False
    key_type = parts[0]
    key_string = parts[1]

    data = base64_decode(key_string.encode())  # pylint:disable=deprecated-method
    int_len = 4
    str_len = struct.unpack('>I', data[:int_len])[0]  # this should return 7
    return data[int_len:int_len + str_len] == key_type.encode()


def _single(collection):
    return len([x for x in collection if x]) == 1


def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)


def _get_object_id_from_subscription(graph_client, subscription):
    if subscription['user']:
        if subscription['user']['type'] == 'user':
            return _get_object_id_by_upn(graph_client, subscription['user']['name'])
        elif subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        else:
            logger.warning("Unknown user type '%s'", subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '
                       'Azure DevTest Lab does not work with certificate credentials.')


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "
                       "You can avoid this by specifying object id.", spn)
        return
    return accounts[0].object_id


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "
                       "You can avoid this by specifying object id.", upn)
        return
    return accounts[0].object_id
