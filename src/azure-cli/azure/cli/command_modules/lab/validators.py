# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from azure.core.exceptions import HttpResponseError
from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ArgumentUsageError

logger = get_logger(__name__)

# Odata filter for name
ODATA_NAME_FILTER = "name eq '{}'"


def validate_lab_vm_create(cmd, args):
    """ Validates parameters for lab vm create and updates args. """
    formula = None
    collection = [args.image, args.formula]
    if not _single(collection):
        raise ArgumentUsageError("usage error: [--image name --image-type type | --formula name]")
    if args.formula and (args.image or args.image_type):
        raise ArgumentUsageError("usage error: [--image name --image-type type | --formula name]")

    if args.formula:
        formula = _get_formula(cmd.cli_ctx, args)
    _validate_location(cmd.cli_ctx, args)
    _validate_expiration_date(args)
    _validate_other_parameters(args, formula)
    validate_artifacts(cmd, args)
    _validate_image_argument(cmd.cli_ctx, args, formula)
    _validate_network_parameters(cmd.cli_ctx, args, formula)
    validate_authentication_type(args, formula)


def validate_lab_vm_list(cmd, args):
    """ Validates parameters for lab vm list and updates args. """
    from azure.mgmt.core.tools import resource_id, is_valid_resource_id
    filters = has_value(args.filters) or False
    environment = has_value(args.environment) or False
    args_all = has_value(args.all) or False
    claimable = has_value(args.claimable) or False

    collection = [filters, args_all, claimable]
    if _any(collection) and not _single(collection):
        raise ArgumentUsageError("usage error: [--filters FILTER | [[--all | --claimable][--environment ENVIRONMENT]]")

    collection = [filters, environment]
    if _any(collection) and not _single(collection):
        raise ArgumentUsageError("usage error: [--filters FILTER | [[--all | --claimable][--environment ENVIRONMENT]]")

    if has_value(args.filters):
        return

    # Retrieve all the vms of the lab
    if args_all and args.all.to_serialized_data() is True:
        args.filters = None
    # Retrieve all the vms claimable by user
    elif claimable and args.claimable.to_serialized_data() is True:
        args.filters = 'properties/allowClaim'
    # Default to retrieving users vms only
    else:
        # Find out owner object id
        if not has_value(args.object_id):
            args.filters = "Properties/ownerObjectId eq '{}'".format(_get_owner_object_id(cmd.cli_ctx))

    if environment:
        if not is_valid_resource_id(args.environment.to_serialized_data()):
            from azure.cli.core.commands.client_factory import get_subscription_id
            args.environment = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                           resource_group=args.resource_group.to_serialized_data(),
                                           args='Microsoft.DevTestLab',
                                           type='labs',
                                           name=args.lab_name.to_serialized_data(),
                                           child_type_1='users',
                                           child_name_1=_get_owner_object_id(cmd.cli_ctx),
                                           child_type_2='environments',
                                           child_name_2=args.environment.to_serialized_data())
        if not filters:
            args.filters = "Properties/environmentId eq '{}'".format(args.environment.to_serialized_data())
        else:
            args.filters = "{} and Properties/environmentId eq '{}'".format(args.filters.to_serialized_data(),
                                                                            args.environment.to_serialized_data())


def validate_claim_vm(namespace):
    if namespace.name is None and namespace.lab_name is None or namespace.resource_group_name is None:
        raise ArgumentUsageError("usage error: --ids IDs | --lab-name LabName --resource-group ResourceGroup "
                                 "--name VMName | --lab-name LabName --resource-group ResourceGroup")


def _get_owner_object_id(cli_ctx):
    from azure.cli.command_modules.role.util import get_current_identity_object_id
    return get_current_identity_object_id(cli_ctx)


# pylint: disable=no-member
def _validate_location(cli_ctx, args):
    """
    Selects the default location of the lab when location is not provided.
    """
    if not has_value(args.location):
        from .custom import LabGet
        result = LabGet(cli_ctx=cli_ctx)(command_args={
            "name": args.lab_name.to_serialized_data(),
            "resource_group": args.resource_group.to_serialized_data()
        })
        args.location = result['location']


def _validate_expiration_date(args):
    """ Validates expiration date if provided. """

    if has_value(args.expiration_date):
        import datetime
        import dateutil.parser
        if datetime.datetime.utcnow() >= dateutil.parser.parse(args.expiration_date.to_serialized_data()):
            raise ArgumentUsageError(
                "Expiration date '{}' must be in future.".format(args.expiration_date.to_serialized_data()))


# pylint: disable=no-member
def _validate_network_parameters(cli_ctx, args, formula=None):
    """ Updates args for virtual network and subnet parameters """
    from .aaz.latest.lab.vnet import List as LabVnetList, Get as LabVnetGet
    lab_vnet = None

    if formula and formula.get('formulaContent'):
        if formula['formulaContent'].get('labVirtualNetworkId'):
            args.vnet_name = \
                args.vnet_name or \
                formula['formulaContent']['labVirtualNetworkId'].split('/')[-1]
        if formula['formulaContent'].get('labSubnetName'):
            args.lab_subnet_name = args.lab_subnet_name or formula['formulaContent']['labSubnetName']
            args.disallow_public_ip_address = formula['formulaContent']['disallowPublicIpAddress']

    # User did not provide vnet and not selected from formula
    if not has_value(args.vnet_name):
        lab_vnets = LabVnetList(cli_ctx=cli_ctx)(command_args={
            "lab_name": args.lab_name.to_serialized_data(),
            "resource_group": args.resource_group.to_serialized_data(),
            "top": 1
        })
        lab_vnets = list(lab_vnets)
        if not lab_vnets:
            err = "Unable to find any virtual network in the '{}' lab.".format(args.lab_name)
            raise HttpResponseError(err)
        lab_vnet = lab_vnets[0]
        args.vnet_name = lab_vnet['name']
        args.lab_virtual_network_id = lab_vnet['id']
    # User did provide vnet or has been selected from formula
    else:
        lab_vnet = LabVnetGet(cli_ctx=cli_ctx)(command_args={
            "lab_name": args.lab_name.to_serialized_data(),
            "name": args.vnet_name.to_serialized_data(),
            "resource_group": args.resource_group.to_serialized_data(),
            "top": 1
        })
        args.lab_virtual_network_id = lab_vnet['id']

    # User did not provide subnet and not selected from formula
    if not has_value(args.subnet):
        args.lab_subnet_name = lab_vnet['subnetOverrides'][0]['labSubnetName']

    _validate_ip_configuration(args, lab_vnet)


# pylint: disable=no-member
def _validate_ip_configuration(args, lab_vnet=None):
    """ Updates args with network_interface & disallow_public_ip_address """
    # case 1: User selecting "shared" ip configuration
    if args.ip_configuration.to_serialized_data() == 'shared':
        rule = _inbound_rule_from_os(args)
        public_ip_config = {'inboundNatRules': [rule]}
        nic_properties = {'sharedPublicIpAddressConfiguration': public_ip_config}
        args.network_interface = nic_properties
        args.disallow_public_ip_address = True
    # case 2: User selecting "public" ip configuration
    elif args.ip_configuration.to_serialized_data() == 'public':
        args.disallow_public_ip_address = False
    # case 3: User selecting "private" ip configuration
    elif args.ip_configuration.to_serialized_data() == 'private':
        args.disallow_public_ip_address = True
    # case 4: User did not select any ip configuration preference
    elif not has_value(args.ip_configuration):
        # case 5: lab virtual network was selected from user's option / formula default then use it for look-up
        if lab_vnet:
            # Default to shared ip configuration based on os type only if inbound nat rules exist on the
            # shared configuration of the selected lab's virtual network
            if lab_vnet.get('subnetOverrides') and \
                    lab_vnet['subnetOverrides'][0].get('sharedPublicIpAddressConfiguration') and \
                    lab_vnet['subnetOverrides'][0]['sharedPublicIpAddressConfiguration'].get('allowedPorts'):
                rule = _inbound_rule_from_os(args)
                public_ip_config = {'inboundNatRules': [rule]}
                nic_properties = {'sharedPublicIpAddressConfiguration': public_ip_config}
                args.network_interface = nic_properties
                args.disallow_public_ip_address = True
            elif lab_vnet.get('subnetOverrides') and lab_vnet['subnetOverrides'][0].get(
                    'usePublicIpAddressPermission') == 'Allow':
                args.disallow_public_ip_address = False
            else:
                args.disallow_public_ip_address = True
    # case 6: User selecting invalid value for ip configuration
    else:
        raise ArgumentUsageError("incorrect value for ip-configuration: {}".format(
            args.ip_configuration.to_serialized_data()))


def _inbound_rule_from_os(args):
    if args.os_type.to_serialized_data().lower() == 'linux':
        return {'transportProtocol': 'Tcp', 'backendPort': 22}

    return {'transportProtocol': 'Tcp', 'backendPort': 3389}


# pylint: disable=no-member
def _validate_image_argument(cli_ctx, args, formula=None):
    """ Update args for image based on image or formula """
    if formula and formula.get('formulaContent'):
        if formula['formulaContent'].get('galleryImageReference'):
            gallery_image_reference = formula['formulaContent']['galleryImageReference']
            args.gallery_image_reference = {
                'offer': gallery_image_reference['offer'],
                'publisher': gallery_image_reference['publisher'],
                'os_type': gallery_image_reference['osType'],
                'sku': gallery_image_reference['sku'],
                'version': gallery_image_reference['version']
            }
            args.os_type = gallery_image_reference['osType']
            return
        if formula['formulaContent'].get('customImageId'):
            # Custom image id from the formula is in the form of "customimages/{name}"
            args.image = formula['formulaContent']['customImageId'].split('/')[-1]
            args.image_type = 'custom'

    if args.image_type == 'gallery':
        _use_gallery_image(cli_ctx, args)
    elif args.image_type == 'custom':
        _use_custom_image(cli_ctx, args)
    else:
        raise ArgumentUsageError("incorrect value for image-type: '{}'. Allowed values: gallery or custom".format(
            args.image_type.to_serialized_data()))


# pylint: disable=no-member
def _use_gallery_image(cli_ctx, args):
    """ Retrieve gallery image from lab and update args """
    from .aaz.latest.lab.gallery_image import List as GalleryImageList
    odata_filter = ODATA_NAME_FILTER.format(args.image.to_serialized_data())
    gallery_images = GalleryImageList(cli_ctx=cli_ctx)(command_args={
        "lab_name": args.lab_name.to_serialized_data(),
        "resource_group": args.resource_group.to_serialized_data(),
        "filter": odata_filter
    })
    gallery_images = list(gallery_images)
    if not gallery_images:
        err = "Unable to find image name '{}' in the '{}' lab Gallery.".format(args.image.to_serialized_data(),
                                                                               args.lab_name.to_serialized_data())
        raise HttpResponseError(err)
    if len(gallery_images) > 1:
        err = "Found more than 1 image with name '{}'. Please pick one from {}"
        raise HttpResponseError(err.format(args.image.to_serialized_data(), [x['name'] for x in gallery_images]))
    image_reference = gallery_images[0]['imageReference']
    args.gallery_image_reference = {
        'offer': image_reference['offer'],
        'publisher': image_reference['publisher'],
        'os_type': image_reference['osType'],
        'sku': image_reference['sku'],
        'version': image_reference['version']
    }
    args.os_type = image_reference['osType']


# pylint: disable=no-member
def _use_custom_image(cli_ctx, args):
    """ Retrieve custom image from lab and update args """
    from azure.mgmt.core.tools import is_valid_resource_id
    if is_valid_resource_id(args.image.to_serialized_data()):
        args.custom_image_id = args.image
    else:
        from .aaz.latest.lab.custom_image import List as CustomImageList
        odata_filter = ODATA_NAME_FILTER.format(args.image.to_serialized_data())
        custom_images = CustomImageList(cli_ctx=cli_ctx)(command_args={
            "lab_name": args.lab_name.to_serialized_data(),
            "resource_group": args.resource_group.to_serialized_data(),
            "filter": odata_filter
        })
        custom_images = list(custom_images)
        if not custom_images:
            err = "Unable to find custom image name '{}' in the '{}' lab.".format(args.image.to_serialized_data(),
                                                                                  args.lab_name.to_serialized_data())
            raise HttpResponseError(err)
        if len(custom_images) > 1:
            err = "Found more than 1 image with name '{}'. Please pick one from {}"
            raise HttpResponseError(err.format(args.image.to_serialized_data(), [x['name'] for x in custom_images]))
        args.custom_image_id = custom_images[0]['id']

        if custom_images[0].get('vm'):
            if custom_images[0]['vm'].get('windowsOsInfo'):
                os_type = "Windows"
            else:
                os_type = "Linux"
        elif custom_images[0].get('vhd'):
            os_type = custom_images[0]['vhd']['os_type']
        else:
            raise HttpResponseError("OS type cannot be inferred from the custom image {}".format(custom_images[0].id))

        args.os_type = os_type


def _get_formula(cli_ctx, args):
    """ Retrieve formula image from lab """
    from .aaz.latest.lab.formula import List as FormulaList
    odata_filter = ODATA_NAME_FILTER.format(args.formula)
    formula_images = FormulaList(cli_ctx=cli_ctx)(command_args={
        "lab_name": args.lab_name.to_serialized_data(),
        "resource_group": args.resource_group.to_serialized_data(),
        "filter": odata_filter
    })
    formula_images = list(formula_images)
    if not formula_images:
        err = "Unable to find formula name '{}' in the '{}' lab.".format(args.formula, args.lab_name)
        raise HttpResponseError(err)
    if len(formula_images) > 1:
        err = "Found more than 1 formula with name '{}'. Please pick one from {}"
        raise HttpResponseError(err.format(args.formula, [x.name for x in formula_images]))
    return formula_images[0]


# pylint: disable=no-member
def _validate_other_parameters(args, formula=None):
    if formula:
        args.tags = args.tags or formula['tags']
        if formula['formulaContent']:
            if has_value(args.allow_claim):
                args.allow_claim = args.allow_claim
            else:
                args.allow_claim = formula['formulaContent']['allowClaim']
            args.artifacts_org = args.artifacts_org or formula['formulaContent']['artifacts']
            args.notes = args.notes or formula['formulaContent']['notes']
            args.size = args.size or formula['formulaContent']['size']
            args.storage_type = args.storage_type or formula['formulaContent']['storageType']
            args.os_type = formula['osType']


def validate_artifacts(cmd, args):
    from azure.mgmt.core.tools import resource_id
    if has_value(args.artifacts_org):
        from azure.cli.core.commands.client_factory import get_subscription_id
        resource_group = args.resource_group.to_serialized_data()
        lab_resource_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                      resource_group=resource_group,
                                      namespace='Microsoft.DevTestLab',
                                      type='labs',
                                      name=args.lab_name.to_serialized_data())
        args.artifacts_org = _update_artifacts(args.artifacts_org.to_serialized_data(), lab_resource_id)


def _update_artifacts(artifacts, lab_resource_id):
    if not isinstance(artifacts, list):
        raise ArgumentUsageError("Artifacts must be of type list. Given artifacts: '{}'".format(artifacts))

    result_artifacts = []
    for artifact in artifacts:
        if artifact.__class__.__name__ == "ArtifactInstallProperties":
            if artifact.parameters:
                raise ArgumentUsageError("Formulas with parameterized artifacts are not supported."
                                         " Use --artifacts to supply artifacts to the virtual machine.")
            artifact_id = _update_artifact_id(artifact.artifact_id, lab_resource_id)
            parameters = []
        else:
            artifact_id = artifact.get('artifact_id', None)
            parameters = artifact.get('parameters', [])

        if artifact_id:
            result_artifact = {}
            result_artifact['artifact_id'] = _update_artifact_id(artifact_id, lab_resource_id)
            result_artifact['parameters'] = parameters
            result_artifacts.append(result_artifact)
        else:
            raise ArgumentUsageError("Missing 'artifactId' for artifact: '{}'".format(artifact))
    return result_artifacts


def _update_artifact_id(artifact_id, lab_resource_id):
    from azure.mgmt.core.tools import is_valid_resource_id
    if not is_valid_resource_id(artifact_id):
        return "{}{}".format(lab_resource_id, artifact_id)
    return artifact_id


# TODO: Following methods are carried over from other command modules
def validate_authentication_type(args, formula=None):
    if formula and formula.get('formulaContent'):
        if formula['formulaContent']['isAuthenticationWithSshKey'] is True:
            args.authentication_type = 'ssh'
            args.ssh_key = formula['formulaContent']['sshKey']
        elif formula['formulaContent']['isAuthenticationWithSshKey'] is False:
            args.user_name = formula['formulaContent']['userName']
            args.password = formula['formulaContent']['password']
            args.authentication_type = 'password'

    # validate proper arguments supplied based on the authentication type
    if args.authentication_type.to_serialized_data() == 'password':
        password_usage_error = "incorrect usage for authentication-type 'password': " \
                               "[--admin-username USERNAME] --admin-password PASSWORD | " \
                               "[--admin-username USERNAME] --saved-secret SECRETNAME"
        if has_value(args.ssh_key) or args.generate_ssh_keys or \
                (has_value(args.saved_secret) and has_value(args.password)):
            raise ArgumentUsageError(password_usage_error)

        # Respect user's provided saved secret name for password authentication
        if has_value(args.saved_secret):
            args.password = "[[{}]]".format(args.saved_secret.to_serialized_data())

        if not args.password:
            # prompt for admin password if not supplied
            from knack.prompting import prompt_pass, NoTTYException
            try:
                args.password = prompt_pass('Admin Password: ', confirm=True)
            except NoTTYException:
                raise ArgumentUsageError('Please specify both username and password in non-interactive mode.')

    elif args.authentication_type.to_serialized_data() == 'ssh':
        if args.os_type.to_serialized_data().lower() != 'linux':
            raise ArgumentUsageError("incorrect authentication-type '{}' for os type '{}'".format(
                args.authentication_type.to_serialized_data(), args.os_type.to_serialized_data()))

        ssh_usage_error = "incorrect usage for authentication-type 'ssh': " \
                          "[--admin-username USERNAME] | " \
                          "[--admin-username USERNAME] --ssh-key KEY | " \
                          "[--admin-username USERNAME] --generate-ssh-keys | " \
                          "[--admin-username USERNAME] --saved-secret SECRETNAME"
        if has_value(args.password) or (has_value(args.saved_secret) and
                                        (has_value(args.ssh_key) or args.generate_ssh_keys)):
            raise ArgumentUsageError(ssh_usage_error)

        # Respect user's provided saved secret name for ssh authentication
        if has_value(args.saved_secret):
            args.ssh_key = "[[{}]]".format(args.saved_secret.to_serialized_data())
        else:
            validate_ssh_key(args)
    else:
        raise ArgumentUsageError("incorrect value for authentication-type: {}".format(
            args.authentication_type.to_serialized_data()))


def validate_ssh_key(args):
    import os

    string_or_file = (args.ssh_key.to_serialized_data() or
                      os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub'))
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not _is_valid_ssh_rsa_public_key(content):
        if args.generate_ssh_keys:
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
            raise ArgumentUsageError('An RSA key file or key value must be supplied to SSH Key Value. '
                                     'You can use --generate-ssh-keys to let CLI generate one for you')
    args.ssh_key = content


def _generate_ssh_keys(private_key_filepath, public_key_filepath):
    import os
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
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression
    # A "good enough" check is to see if the key starts with the correct header.
    import struct
    import base64
    parts = openssh_pubkey.split()
    if len(parts) < 2:
        return False
    key_type = parts[0]
    key_string = parts[1]

    data = base64.b64decode(key_string)
    int_len = 4
    str_len = struct.unpack('>I', data[:int_len])[0]  # this should return 7
    return data[int_len:int_len + str_len] == key_type.encode()


def _single(collection):
    return len([x for x in collection if x]) == 1


def _any(collection):
    return len([x for x in collection if x]) > 0
