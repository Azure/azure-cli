# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from msrestazure.azure_exceptions import CloudError
from azure.cli.core._util import CLIError
from azure.cli.core.commands.arm import is_valid_resource_id
from ._client_factory import (get_devtestlabs_management_client)
from azure.mgmt.devtestlabs.models.gallery_image_reference import GalleryImageReference
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)
devtestlabs_management_client = get_devtestlabs_management_client(None)


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


def validate_location(namespace):
    """
    Selects the default location of the lab when location is not provided while creating vm.
    """
    if namespace.location is None:
        try:
            lab_operation = devtestlabs_management_client.lab
            lab = lab_operation.get_resource(namespace.resource_group, namespace.lab_name)
            namespace.location = lab.location
        except CloudError as err:
            raise CLIError(err)


def validate_network_parameters(namespace):
    """
    Selects the DevTest Lab's virtual network and subnet if not provided and updates namespace
    """
    from azure.cli.core.commands.client_factory import get_subscription_id
    vnet_operation = devtestlabs_management_client.virtual_network

    if not namespace.vnet_name:
        try:
            lab_vnets = list(vnet_operation.list(namespace.resource_group, namespace.lab_name, top=1))
            if not lab_vnets:
                err = "Unable to find any virtual network in the '{}' lab.".format(namespace.lab_name)
                raise CLIError(err)
            else:
                lab_vnet = lab_vnets[0]
                namespace.vnet_name = lab_vnet.name
                namespace.lab_virtual_network_id = lab_vnet.id
        except CloudError as err:
            raise CLIError(err)
    else:
        namespace.lab_virtual_network_id = '/subscriptions/{}/resourcegroups/{}/providers/microsoft.devtestlab' \
                                           '/labs/{}/virtualnetworks/{}'.format(get_subscription_id(),
                                                                                namespace.resource_group,
                                                                                namespace.lab_name,
                                                                                namespace.vnet_name)

    # Select default subnet for selected vnet when subnet is not provided
    if not namespace.subnet:
        # Get the first subnet of the lab's virtual network
        lab_vnet = vnet_operation.get_resource(namespace.resource_group, namespace.lab_name, namespace.vnet_name)
        namespace.subnet = lab_vnet.subnet_overrides[0].lab_subnet_name

        # Determine value for disallow_public_ip_address based on subnet's use_public_ip_address_permission property
        if lab_vnet.subnet_overrides[0].use_public_ip_address_permission == 'Allow':
            namespace.disallow_public_ip_address = 'false'
        else:
            namespace.disallow_public_ip_address = 'true'


def validate_image_argument(namespace):
    image_type = _parse_image_argument(namespace)
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
        lab_images = list(gallery_image_operation.list(namespace.resource_group, namespace.lab_name, odata_filter))

        if not lab_images:
            err = "Unable to find image name '{}' in the '{}' lab Gallery.".format(namespace.image, namespace.lab_name)
            raise CLIError(err)
        elif len(lab_images) > 1:
            err = "Found more than 1 images with name "'{}'". Please pick one from {}"
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
        err = 'Invalid image "{}". Use a custom image id or pick one from lab Gallery'
        raise CLIError(err.format(namespace.image))


# TODO: Following methods can be extracted into common utils shared by other command modules


def validate_authentication_type(namespace):
    # validate proper arguments supplied based on the authentication type
    if namespace.authentication_type == 'password':
        if namespace.ssh_key:
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
