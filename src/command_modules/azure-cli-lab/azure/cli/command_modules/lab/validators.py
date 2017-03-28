# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import dateutil.parser
from azure.cli.core._util import CLIError
from azure.cli.core.commands.arm import resource_id, is_valid_resource_id
from ._client_factory import (get_devtestlabs_management_client)
from .sdk.devtestlabs.models.gallery_image_reference import GalleryImageReference
from azure.graphrbac import GraphRbacManagementClient
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)

# pylint: disable=line-too-long

# Odata filter for startswith
ODATA_STARTS_WITH_FILTER = "startswith(name, '{}')"


def validate_lab_vm_create(namespace):
    """ Validates parameters for lab vm create and updates namespace. """
    formula = None

    collection = [namespace.image, namespace.formula]
    if not _single(collection):
        raise CLIError("usage error: [--image name --image-type type | --formula name]")
    if namespace.formula and (namespace.image or namespace.image_type):
        raise CLIError("usage error: [--image name --image-type type | --formula name]")

    if namespace.formula:
        formula = _get_formula(namespace)

    _validate_location(namespace)
    _validate_expiration_date(namespace)
    _validate_image_argument(namespace, formula)
    _validate_network_parameters(namespace, formula)
    _validate_other_parameters(namespace, formula)
    validate_authentication_type(namespace, formula)


def validate_lab_vm_list(namespace):
    """ Validates parameters for lab vm list and updates namespace. """
    collection = [namespace.filters, namespace.all, namespace.claimable]
    if _any(collection) and not _single(collection):
        raise CLIError("usage error: [--filters FILTER | --all | --claimable]")

    # Retrieve all the vms of the lab
    if namespace.all:
        namespace.filters = None
    # Retrieve all the vms claimable by user
    elif namespace.claimable:
        namespace.filters = 'properties/allowClaim'
    # Default to retrieving users vms only
    else:
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


def _devtestlabs_management_client():
    return get_devtestlabs_management_client(None)


# pylint: disable=no-member
def _validate_location(namespace):
    """
    Selects the default location of the lab when location is not provided.
    """
    if namespace.location is None:
        lab_operation = _devtestlabs_management_client.lab
        lab = lab_operation.get_resource(namespace.resource_group, namespace.lab_name)
        namespace.location = lab.location


def _validate_expiration_date(namespace):
    """ Validates expiration date if provided. """

    if namespace.expiration_date:
        if datetime.datetime.utcnow().date() >= dateutil.parser.parse(namespace.expiration_date).date():
            raise CLIError("Expiration date '{}' must be in future.".format(namespace.expiration_date))


# pylint: disable=no-member
def _validate_network_parameters(namespace, formula=None):
    """ Updates namespace for virtual network and subnet parameters """
    from azure.cli.core.commands.client_factory import get_subscription_id
    vnet_operation = _devtestlabs_management_client.virtual_network

    if formula and formula.formula_content:
        if formula.formula_content.lab_virtual_network_id:
            namespace.vnet_name = \
                namespace.vnet_name or \
                formula.formula_content.lab_virtual_network_id.split('/')[-1]
        if formula.formula_content.lab_virtual_network_id:
            namespace.subnet = \
                namespace.subnet or \
                formula.formula_content.lab_subnet_name
            namespace.disallow_public_ip_address = \
                namespace.disallow_public_ip_address or \
                formula.formula_content.disallow_public_ip_address

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

    # Select default subnet for selected virtual network when subnet is not provided
    if not namespace.subnet:
        # Get the first subnet of the lab's virtual network
        lab_vnet = vnet_operation.get_resource(namespace.resource_group,
                                               namespace.lab_name,
                                               namespace.vnet_name)
        namespace.subnet = lab_vnet.subnet_overrides[0].lab_subnet_name

        # Determine value for disallow_public_ip_address based on subnet's
        # use_public_ip_address_permission property
        if lab_vnet.subnet_overrides[0].use_public_ip_address_permission == 'Allow':
            namespace.disallow_public_ip_address = False
        else:
            namespace.disallow_public_ip_address = True


# pylint: disable=no-member
def _validate_image_argument(namespace, formula=None):
    """ Update namespace for image based on image or formula """
    if formula and formula.formula_content:
        if formula.formula_content.gallery_image_reference:
            gallery_image_reference = formula.formula_content.gallery_image_reference
            namespace.gallery_image_reference = \
                GalleryImageReference(offer=gallery_image_reference.offer,
                                      publisher=gallery_image_reference.publisher,
                                      os_type=gallery_image_reference.os_type,
                                      sku=gallery_image_reference.sku,
                                      version=gallery_image_reference.version)
            return
        elif formula.formula_content.custom_image_id:
            namespace.image = formula.formula_content.custom_image_id.split('/')[-1]
            namespace.image_type = 'custom'

    if namespace.image_type == 'gallery':
        _use_gallery_image(namespace)
    elif namespace.image_type == 'custom':
        _use_custom_image(namespace)
    else:
        raise CLIError("incorrect value for image-type: '{}'. Allowed values: gallery or custom"
                       .format(namespace.image_type))


# pylint: disable=no-member
def _use_gallery_image(namespace):
    """ Retrieve gallery image from lab and update namespace """
    gallery_image_operation = _devtestlabs_management_client.gallery_image
    odata_filter = ODATA_STARTS_WITH_FILTER.format(namespace.image)
    gallery_images = list(gallery_image_operation.list(namespace.resource_group,
                                                       namespace.lab_name,
                                                       filter=odata_filter))

    if not gallery_images:
        err = "Unable to find image name '{}' in the '{}' lab Gallery.".format(namespace.image,
                                                                               namespace.lab_name)
        raise CLIError(err)
    elif len(gallery_images) > 1:
        err = "Found more than 1 image with name '{}'. Please pick one from {}"
        raise CLIError(err.format(namespace.image, [x.name for x in gallery_images]))
    else:
        namespace.gallery_image_reference = \
            GalleryImageReference(offer=gallery_images[0].image_reference.offer,
                                  publisher=gallery_images[0].image_reference.publisher,
                                  os_type=gallery_images[0].image_reference.os_type,
                                  sku=gallery_images[0].image_reference.sku,
                                  version=gallery_images[0].image_reference.version)


# pylint: disable=no-member
def _use_custom_image(namespace):
    """ Retrieve custom image from lab and update namespace """
    if is_valid_resource_id(namespace.image):
        namespace.custom_image_id = namespace.image
    else:
        custom_image_operation = _devtestlabs_management_client.custom_image
        odata_filter = ODATA_STARTS_WITH_FILTER.format(namespace.image)
        custom_images = list(custom_image_operation.list(namespace.resource_group,
                                                         namespace.lab_name,
                                                         filter=odata_filter))
        if not custom_images:
            err = "Unable to find custom image name '{}' in the '{}' lab.".format(namespace.image, namespace.lab_name)
            raise CLIError(err)
        elif len(custom_images) > 1:
            err = "Found more than 1 image with name '{}'. Please pick one from {}"
            raise CLIError(err.format(namespace.image, [x.name for x in custom_images]))
        else:
            namespace.custom_image_id = custom_images[0].id


def _get_formula(namespace):
    """ Retrieve formula image from lab """
    formula_operation = _devtestlabs_management_client.formula
    odata_filter = ODATA_STARTS_WITH_FILTER.format(namespace.formula)
    formula_images = list(formula_operation.list(namespace.resource_group,
                                                 namespace.lab_name,
                                                 filter=odata_filter))
    if not formula_images:
        err = "Unable to find formula name '{}' in the '{}' lab.".format(namespace.formula, namespace.lab_name)
        raise CLIError(err)
    elif len(formula_images) > 1:
        err = "Found more than 1 formula with name '{}'. Please pick one from {}"
        raise CLIError(err.format(namespace.formula, [x.name for x in formula_images]))
    return formula_images[0]


def _validate_other_parameters(namespace, formula=None):
    if formula:
        namespace.tags = namespace.tags or formula.tags
        if formula.formula_content:
            namespace.allow_claim = namespace.allow_claim or formula.formula_content.allow_claim
            namespace.artifacts = namespace.artifacts or formula.formula_content.artifacts
            namespace.notes = namespace.notes or formula.formula_content.notes
            namespace.size = namespace.size or formula.formula_content.size
            namespace.disk_type = namespace.disk_type or formula.formula_content.storage_type


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


def _any(collection):
    return len([x for x in collection if x]) > 0


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
