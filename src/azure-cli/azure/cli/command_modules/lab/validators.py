# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.command_modules.lab._client_factory import get_devtestlabs_management_client

logger = get_logger(__name__)

# Odata filter for name
ODATA_NAME_FILTER = "name eq '{}'"


def validate_lab_vm_create(cmd, namespace):
    """ Validates parameters for lab vm create and updates namespace. """
    formula = None
    collection = [namespace.image, namespace.formula]
    if not _single(collection):
        raise CLIError("usage error: [--image name --image-type type | --formula name]")
    if namespace.formula and (namespace.image or namespace.image_type):
        raise CLIError("usage error: [--image name --image-type type | --formula name]")

    if namespace.formula:
        formula = _get_formula(cmd.cli_ctx, namespace)

    _validate_location(cmd.cli_ctx, namespace)
    _validate_expiration_date(namespace)
    _validate_other_parameters(namespace, formula)
    validate_artifacts(cmd, namespace)
    _validate_image_argument(cmd.cli_ctx, namespace, formula)
    _validate_network_parameters(cmd.cli_ctx, namespace, formula)
    validate_authentication_type(namespace, formula)


def validate_lab_vm_list(cmd, namespace):
    """ Validates parameters for lab vm list and updates namespace. """
    from msrestazure.tools import resource_id, is_valid_resource_id
    collection = [namespace.filters, namespace.all, namespace.claimable]
    if _any(collection) and not _single(collection):
        raise CLIError("usage error: [--filters FILTER | [[--all | --claimable][--environment ENVIRONMENT]]")

    collection = [namespace.filters, namespace.environment]
    if _any(collection) and not _single(collection):
        raise CLIError("usage error: [--filters FILTER | [[--all | --claimable][--environment ENVIRONMENT]]")

    if namespace.filters:
        return

    # Retrieve all the vms of the lab
    if namespace.all:
        namespace.filters = None
    # Retrieve all the vms claimable by user
    elif namespace.claimable:
        namespace.filters = 'properties/allowClaim'
    # Default to retrieving users vms only
    else:
        # Find out owner object id
        if not namespace.object_id:
            namespace.filters = "Properties/ownerObjectId eq '{}'".format(_get_owner_object_id(cmd.cli_ctx))

    if namespace.environment:
        if not is_valid_resource_id(namespace.environment):
            from azure.cli.core.commands.client_factory import get_subscription_id
            namespace.environment = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                                resource_group=namespace.resource_group_name,
                                                namespace='Microsoft.DevTestLab',
                                                type='labs',
                                                name=namespace.lab_name,
                                                child_type_1='users',
                                                child_name_1=_get_owner_object_id(cmd.cli_ctx),
                                                child_type_2='environments',
                                                child_name_2=namespace.environment)
        if namespace.filters is None:
            namespace.filters = "Properties/environmentId eq '{}'".format(namespace.environment)
        else:
            namespace.filters = "{} and Properties/environmentId eq '{}'".format(namespace.filters,
                                                                                 namespace.environment)


def validate_user_name(namespace):
    namespace.user_name = "@me"


def validate_template_id(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if not is_valid_resource_id(namespace.arm_template):
        if not namespace.artifact_source_name:
            raise CLIError("--artifact-source-name is required when name is "
                           "provided for --arm-template")

        namespace.arm_template = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                             resource_group=namespace.resource_group_name,
                                             namespace='Microsoft.DevTestLab',
                                             type='labs',
                                             name=namespace.lab_name,
                                             child_type_1='artifactSources',
                                             child_name_1=namespace.artifact_source_name,
                                             child_type_2='armTemplates',
                                             child_name_2=namespace.arm_template)


def validate_claim_vm(namespace):
    if namespace.name is None and namespace.lab_name is None or namespace.resource_group_name is None:
        raise CLIError("usage error: --ids IDs | --lab-name LabName --resource-group ResourceGroup --name VMName"
                       " | --lab-name LabName --resource-group ResourceGroup")


def _get_owner_object_id(cli_ctx):
    from azure.cli.core._profile import Profile
    from azure.graphrbac.models import GraphErrorException
    from azure.graphrbac import GraphRbacManagementClient
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    graph_client = GraphRbacManagementClient(cred,
                                             tenant_id,
                                             base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    subscription = profile.get_subscription()
    try:
        return _get_current_user_object_id(graph_client)
    except GraphErrorException:
        return _get_object_id(graph_client, subscription=subscription)


# pylint: disable=no-member
def _validate_location(cli_ctx, namespace):
    """
    Selects the default location of the lab when location is not provided.
    """
    if namespace.location is None:
        lab_operation = get_devtestlabs_management_client(cli_ctx, None).labs
        lab = lab_operation.get(namespace.resource_group_name, namespace.lab_name)
        namespace.location = lab.location


def _validate_expiration_date(namespace):
    """ Validates expiration date if provided. """

    if namespace.expiration_date:
        import datetime
        import dateutil.parser
        if datetime.datetime.utcnow().date() >= dateutil.parser.parse(namespace.expiration_date).date():
            raise CLIError("Expiration date '{}' must be in future.".format(namespace.expiration_date))


# pylint: disable=no-member
def _validate_network_parameters(cli_ctx, namespace, formula=None):
    """ Updates namespace for virtual network and subnet parameters """
    vnet_operation = get_devtestlabs_management_client(cli_ctx, None).virtual_networks
    lab_vnet = None

    if formula and formula.formula_content:
        if formula.formula_content.lab_virtual_network_id:
            namespace.vnet_name = \
                namespace.vnet_name or \
                formula.formula_content.lab_virtual_network_id.split('/')[-1]
        if formula.formula_content.lab_subnet_name:
            namespace.subnet = \
                namespace.subnet or \
                formula.formula_content.lab_subnet_name
            namespace.disallow_public_ip_address = formula.formula_content.disallow_public_ip_address

    # User did not provide vnet and not selected from formula
    if not namespace.vnet_name:
        lab_vnets = list(vnet_operation.list(namespace.resource_group_name, namespace.lab_name, top=1))
        if not lab_vnets:
            err = "Unable to find any virtual network in the '{}' lab.".format(namespace.lab_name)
            raise CLIError(err)
        lab_vnet = lab_vnets[0]
        namespace.vnet_name = lab_vnet.name
        namespace.lab_virtual_network_id = lab_vnet.id
    # User did provide vnet or has been selected from formula
    else:
        lab_vnet = vnet_operation.get(namespace.resource_group_name, namespace.lab_name, namespace.vnet_name)
        namespace.lab_virtual_network_id = lab_vnet.id

    # User did not provide subnet and not selected from formula
    if not namespace.subnet:
        namespace.subnet = lab_vnet.subnet_overrides[0].lab_subnet_name

    _validate_ip_configuration(namespace, lab_vnet)


# pylint: disable=no-member
def _validate_ip_configuration(namespace, lab_vnet=None):
    """ Updates namespace with network_interface & disallow_public_ip_address """
    from azure.mgmt.devtestlabs.models import NetworkInterfaceProperties, SharedPublicIpAddressConfiguration

    # case 1: User selecting "shared" ip configuration
    if namespace.ip_configuration == 'shared':
        rule = _inbound_rule_from_os(namespace)
        public_ip_config = SharedPublicIpAddressConfiguration(inbound_nat_rules=[rule])
        nic_properties = NetworkInterfaceProperties(shared_public_ip_address_configuration=public_ip_config)
        namespace.network_interface = nic_properties
        namespace.disallow_public_ip_address = True
    # case 2: User selecting "public" ip configuration
    elif namespace.ip_configuration == 'public':
        namespace.disallow_public_ip_address = False
    # case 3: User selecting "private" ip configuration
    elif namespace.ip_configuration == 'private':
        namespace.disallow_public_ip_address = True
    # case 4: User did not select any ip configuration preference
    elif namespace.ip_configuration is None:
        # case 5: lab virtual network was selected from user's option / formula default then use it for look-up
        if lab_vnet:
            # Default to shared ip configuration based on os type only if inbound nat rules exist on the
            # shared configuration of the selected lab's virtual network
            if lab_vnet.subnet_overrides and lab_vnet.subnet_overrides[0].shared_public_ip_address_configuration and \
                    lab_vnet.subnet_overrides[0].shared_public_ip_address_configuration.allowed_ports:
                rule = _inbound_rule_from_os(namespace)
                public_ip_config = SharedPublicIpAddressConfiguration(inbound_nat_rules=[rule])
                nic_properties = NetworkInterfaceProperties(shared_public_ip_address_configuration=public_ip_config)
                namespace.network_interface = nic_properties
                namespace.disallow_public_ip_address = True
            elif lab_vnet.subnet_overrides and lab_vnet.subnet_overrides[0].use_public_ip_address_permission == 'Allow':
                namespace.disallow_public_ip_address = False
            else:
                namespace.disallow_public_ip_address = True
    # case 6: User selecting invalid value for ip configuration
    else:
        raise CLIError("incorrect value for ip-configuration: {}".format(namespace.ip_configuration))


def _inbound_rule_from_os(namespace):
    from azure.mgmt.devtestlabs.models import InboundNatRule
    if namespace.os_type == 'Linux':
        return InboundNatRule(transport_protocol='Tcp', backend_port=22)

    return InboundNatRule(transport_protocol='Tcp', backend_port=3389)


# pylint: disable=no-member
def _validate_image_argument(cli_ctx, namespace, formula=None):
    """ Update namespace for image based on image or formula """
    from azure.mgmt.devtestlabs.models import GalleryImageReference
    if formula and formula.formula_content:
        if formula.formula_content.gallery_image_reference:
            gallery_image_reference = formula.formula_content.gallery_image_reference
            namespace.gallery_image_reference = \
                GalleryImageReference(offer=gallery_image_reference.offer,
                                      publisher=gallery_image_reference.publisher,
                                      os_type=gallery_image_reference.os_type,
                                      sku=gallery_image_reference.sku,
                                      version=gallery_image_reference.version)
            namespace.os_type = gallery_image_reference.os_type
            return
        if formula.formula_content.custom_image_id:
            # Custom image id from the formula is in the form of "customimages/{name}"
            namespace.image = formula.formula_content.custom_image_id.split('/')[-1]
            namespace.image_type = 'custom'

    if namespace.image_type == 'gallery':
        _use_gallery_image(cli_ctx, namespace)
    elif namespace.image_type == 'custom':
        _use_custom_image(cli_ctx, namespace)
    else:
        raise CLIError("incorrect value for image-type: '{}'. Allowed values: gallery or custom"
                       .format(namespace.image_type))


# pylint: disable=no-member
def _use_gallery_image(cli_ctx, namespace):
    """ Retrieve gallery image from lab and update namespace """
    from azure.mgmt.devtestlabs.models import GalleryImageReference
    gallery_image_operation = get_devtestlabs_management_client(cli_ctx, None).gallery_images
    odata_filter = ODATA_NAME_FILTER.format(namespace.image)
    gallery_images = list(gallery_image_operation.list(namespace.resource_group_name,
                                                       namespace.lab_name,
                                                       filter=odata_filter))

    if not gallery_images:
        err = "Unable to find image name '{}' in the '{}' lab Gallery.".format(namespace.image,
                                                                               namespace.lab_name)
        raise CLIError(err)
    if len(gallery_images) > 1:
        err = "Found more than 1 image with name '{}'. Please pick one from {}"
        raise CLIError(err.format(namespace.image, [x.name for x in gallery_images]))
    namespace.gallery_image_reference = \
        GalleryImageReference(offer=gallery_images[0].image_reference.offer,
                              publisher=gallery_images[0].image_reference.publisher,
                              os_type=gallery_images[0].image_reference.os_type,
                              sku=gallery_images[0].image_reference.sku,
                              version=gallery_images[0].image_reference.version)
    namespace.os_type = gallery_images[0].image_reference.os_type


# pylint: disable=no-member
def _use_custom_image(cli_ctx, namespace):
    """ Retrieve custom image from lab and update namespace """
    from msrestazure.tools import is_valid_resource_id
    if is_valid_resource_id(namespace.image):
        namespace.custom_image_id = namespace.image
    else:
        custom_image_operation = get_devtestlabs_management_client(cli_ctx, None).custom_images
        odata_filter = ODATA_NAME_FILTER.format(namespace.image)
        custom_images = list(custom_image_operation.list(namespace.resource_group_name,
                                                         namespace.lab_name,
                                                         filter=odata_filter))
        if not custom_images:
            err = "Unable to find custom image name '{}' in the '{}' lab.".format(namespace.image, namespace.lab_name)
            raise CLIError(err)
        if len(custom_images) > 1:
            err = "Found more than 1 image with name '{}'. Please pick one from {}"
            raise CLIError(err.format(namespace.image, [x.name for x in custom_images]))
        namespace.custom_image_id = custom_images[0].id

        if custom_images[0].vm is not None:
            if custom_images[0].vm.windows_os_info is not None:
                os_type = "Windows"
            else:
                os_type = "Linux"
        elif custom_images[0].vhd is not None:
            os_type = custom_images[0].vhd.os_type
        else:
            raise CLIError("OS type cannot be inferred from the custom image {}".format(custom_images[0].id))

        namespace.os_type = os_type


def _get_formula(cli_ctx, namespace):
    """ Retrieve formula image from lab """
    formula_operation = get_devtestlabs_management_client(cli_ctx, None).formulas
    odata_filter = ODATA_NAME_FILTER.format(namespace.formula)
    formula_images = list(formula_operation.list(namespace.resource_group_name,
                                                 namespace.lab_name,
                                                 filter=odata_filter))
    if not formula_images:
        err = "Unable to find formula name '{}' in the '{}' lab.".format(namespace.formula, namespace.lab_name)
        raise CLIError(err)
    if len(formula_images) > 1:
        err = "Found more than 1 formula with name '{}'. Please pick one from {}"
        raise CLIError(err.format(namespace.formula, [x.name for x in formula_images]))
    return formula_images[0]


# pylint: disable=no-member
def _validate_other_parameters(namespace, formula=None):
    if formula:
        namespace.tags = namespace.tags or formula.tags
        if formula.formula_content:
            namespace.allow_claim = namespace.allow_claim or formula.formula_content.allow_claim
            namespace.artifacts = namespace.artifacts or formula.formula_content.artifacts
            namespace.notes = namespace.notes or formula.formula_content.notes
            namespace.size = namespace.size or formula.formula_content.size
            namespace.disk_type = namespace.disk_type or formula.formula_content.storage_type
            namespace.os_type = formula.os_type


def validate_artifacts(cmd, namespace):
    from msrestazure.tools import resource_id
    if namespace.artifacts:
        from azure.cli.core.commands.client_factory import get_subscription_id
        if hasattr(namespace, 'resource_group'):
            resource_group = namespace.resource_group
        else:
            # some SDK methods have parameter name as 'resource_group_name'
            resource_group = namespace.resource_group_name

        lab_resource_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                      resource_group=resource_group,
                                      namespace='Microsoft.DevTestLab',
                                      type='labs',
                                      name=namespace.lab_name)
        namespace.artifacts = _update_artifacts(namespace.artifacts, lab_resource_id)


def _update_artifacts(artifacts, lab_resource_id):
    if not isinstance(artifacts, list):
        raise CLIError("Artifacts must be of type list. Given artifacts: '{}'".format(artifacts))

    result_artifacts = []
    for artifact in artifacts:
        if artifact.__class__.__name__ == "ArtifactInstallProperties":
            if artifact.parameters:
                raise CLIError("Formulas with parameterized artifacts are not supported. Use --artifacts to supply"
                               "artifacts to the virtual machine.")
            artifact_id = _update_artifact_id(artifact.artifact_id, lab_resource_id)
            parameters = []
        else:
            artifact_id = artifact.get('artifact_id', None)
            parameters = artifact.get('parameters', [])

        if artifact_id:
            result_artifact = dict()
            result_artifact['artifact_id'] = _update_artifact_id(artifact_id, lab_resource_id)
            result_artifact['parameters'] = parameters
            result_artifacts.append(result_artifact)
        else:
            raise CLIError("Missing 'artifactId' for artifact: '{}'".format(artifact))
    return result_artifacts


def _update_artifact_id(artifact_id, lab_resource_id):
    from msrestazure.tools import is_valid_resource_id
    if not is_valid_resource_id(artifact_id):
        return "{}{}".format(lab_resource_id, artifact_id)
    return artifact_id


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
        password_usage_error = "incorrect usage for authentication-type 'password': " \
                               "[--admin-username USERNAME] --admin-password PASSWORD | " \
                               "[--admin-username USERNAME] --saved-secret SECRETNAME"
        if namespace.ssh_key or namespace.generate_ssh_keys or (namespace.saved_secret and namespace.admin_password):
            raise ValueError(password_usage_error)

        # Respect user's provided saved secret name for password authentication
        if namespace.saved_secret:
            namespace.admin_password = "[[{}]]".format(namespace.saved_secret)

        if not namespace.admin_password:
            # prompt for admin password if not supplied
            from knack.prompting import prompt_pass, NoTTYException
            try:
                namespace.admin_password = prompt_pass('Admin Password: ', confirm=True)
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')

    elif namespace.authentication_type == 'ssh':
        if namespace.os_type != 'Linux':
            raise CLIError("incorrect authentication-type '{}' for os type '{}'".format(
                namespace.authentication_type, namespace.os_type))

        ssh_usage_error = "incorrect usage for authentication-type 'ssh': " \
                          "[--admin-username USERNAME] | " \
                          "[--admin-username USERNAME] --ssh-key KEY | " \
                          "[--admin-username USERNAME] --generate-ssh-keys | " \
                          "[--admin-username USERNAME] --saved-secret SECRETNAME"
        if namespace.admin_password or (namespace.saved_secret and (namespace.ssh_key or namespace.generate_ssh_keys)):
            raise ValueError(ssh_usage_error)

        # Respect user's provided saved secret name for ssh authentication
        if namespace.saved_secret:
            namespace.ssh_key = "[[{}]]".format(namespace.saved_secret)
        else:
            validate_ssh_key(namespace)
    else:
        raise CLIError("incorrect value for authentication-type: {}".format(namespace.authentication_type))


def validate_ssh_key(namespace):
    import os

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


def _get_current_user_object_id(graph_client):
    from msrestazure.azure_exceptions import CloudError
    try:
        current_user = graph_client.signed_in_user.get()
        if current_user and current_user.object_id:  # pylint:disable=no-member
            return current_user.object_id  # pylint:disable=no-member
    except CloudError:
        pass
    return None


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
        if subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        logger.warning("Unknown user type '%s'", subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '
                       'Azure DevTest Lab does not work with certificate credentials.')
    return None


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "
                       "You can avoid this by specifying object id.", spn)
        return None
    return accounts[0].object_id


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "
                       "You can avoid this by specifying object id.", upn)
        return None
    return accounts[0].object_id
