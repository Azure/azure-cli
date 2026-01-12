# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, too-many-statements, consider-using-f-string

from knack.arguments import CLIArgumentType
from knack.deprecation import Deprecated

from azure.cli.core.commands.parameters import (resource_group_name_type,
                                                get_location_type,
                                                file_type,
                                                get_three_state_flag, get_enum_type, tags_type)

from ._validators import (validate_memory, validate_cpu, validate_managed_env_name_or_id, validate_registry_server,
                          validate_registry_user, validate_registry_pass, validate_target_port,
                          validate_storage_name_or_id, validate_cors_max_age, validate_allow_insecure)
from ._constants import UNAUTHENTICATED_CLIENT_ACTION, FORWARD_PROXY_CONVENTION, MAXIMUM_CONTAINER_APP_NAME_LENGTH, LOG_TYPE_CONSOLE, LOG_TYPE_SYSTEM


def load_arguments(self, _):

    name_type = CLIArgumentType(options_list=['--name', '-n'])

    with self.argument_context('containerapp') as c:
        # Base arguments
        c.argument('name', name_type, metavar='NAME', id_part='name', help=f"The name of the Containerapp. A name must consist of lower case alphanumeric characters or '-', start with a letter, end with an alphanumeric character, cannot have '--', and must be less than {MAXIMUM_CONTAINER_APP_NAME_LENGTH} characters.")
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.ignore('disable_warnings')

    with self.argument_context('containerapp') as c:
        c.argument('tags', arg_type=tags_type)
        c.argument('managed_env', validator=validate_managed_env_name_or_id, options_list=['--environment'], help="Name or resource ID of the container app's environment.")
        c.argument('yaml', type=file_type, help='Path to a .yaml file with the configuration of a container app. All other parameters will be ignored. For an example, see  https://learn.microsoft.com/azure/container-apps/azure-resource-manager-api-spec#examples')

    with self.argument_context('containerapp exec') as c:
        c.argument('container', help="The name of the container to ssh into")
        c.argument('replica', help="The name of the replica to ssh into. List replicas with 'az containerapp replica list'. A replica may not exist if there is not traffic to your app.")
        c.argument('revision', help="The name of the container app revision to ssh into. Defaults to the latest revision.")
        c.argument('startup_command', options_list=["--command"], help="The startup command (bash, zsh, sh, etc.).")
        c.argument('name', name_type, id_part=None, help="The name of the Containerapp.")
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None)

    with self.argument_context('containerapp logs show') as c:
        c.argument('follow', help="Print logs in real time if present.", arg_type=get_three_state_flag())
        c.argument('tail', help="The number of past logs to print (0-300)", type=int, default=20)
        c.argument('container', help="The name of the container")
        c.argument('output_format', options_list=["--format"], help="Log output format", arg_type=get_enum_type(["json", "text"]), default="json")
        c.argument('replica', help="The name of the replica. List replicas with 'az containerapp replica list'. A replica may not exist if there is not traffic to your app.")
        c.argument('revision', help="The name of the container app revision. Defaults to the latest revision.")
        c.argument('name', name_type, id_part=None, help="The name of the Containerapp.")
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None)
        c.argument('kind', options_list=["--type", "-t"], help="Type of logs to stream", arg_type=get_enum_type([LOG_TYPE_CONSOLE, LOG_TYPE_SYSTEM]), default=LOG_TYPE_CONSOLE)

    with self.argument_context('containerapp env logs show') as c:
        c.argument('follow', help="Print logs in real time if present.", arg_type=get_three_state_flag())
        c.argument('tail', help="The number of past logs to print (0-300)", type=int, default=20)

    # Replica
    with self.argument_context('containerapp replica') as c:
        c.argument('replica', help="The name of the replica. ")
        c.argument('revision', help="The name of the container app revision. Defaults to the latest revision.")
        c.argument('name', name_type, id_part=None, help="The name of the Containerapp.")
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None)

    # Container
    with self.argument_context('containerapp', arg_group='Container') as c:
        c.argument('container_name', help="Name of the container.")
        c.argument('cpu', type=float, validator=validate_cpu, help="Required CPU in cores from 0.25 - 2.0, e.g. 0.5")
        c.argument('memory', validator=validate_memory, help="Required memory from 0.5 - 4.0 ending with \"Gi\", e.g. 1.0Gi")
        c.argument('env_vars', nargs='*', help="A list of environment variable(s) for the container. Space-separated values in 'key=value' format. Empty string to clear existing values. Prefix value with 'secretref:' to reference a secret.")
        c.argument('startup_command', nargs='*', options_list=['--command'], help="A list of supported commands on the container that will executed during startup. Space-separated values e.g. \"/bin/queue\" \"mycommand\". Empty string to clear existing values")
        c.argument('args', nargs='*', help="A list of container startup command argument(s). Space-separated values e.g. \"-c\" \"mycommand\". Empty string to clear existing values")
        c.argument('revision_suffix', help='User friendly suffix that is appended to the revision name')

    # Env vars
    with self.argument_context('containerapp', arg_group='Environment variables') as c:
        c.argument('set_env_vars', nargs='*', help="Add or update environment variable(s) in container. Existing environment variables are not modified. Space-separated values in 'key=value' format. If stored as a secret, value must start with 'secretref:' followed by the secret name.")
        c.argument('remove_env_vars', nargs='*', help="Remove environment variable(s) from container. Space-separated environment variable names.")
        c.argument('replace_env_vars', nargs='*', help="Replace environment variable(s) in container. Other existing environment variables are removed. Space-separated values in 'key=value' format. If stored as a secret, value must start with 'secretref:' followed by the secret name.")
        c.argument('remove_all_env_vars', help="Remove all environment variable(s) from container..")

    # Scale
    with self.argument_context('containerapp', arg_group='Scale') as c:
        c.argument('min_replicas', type=int, help="The minimum number of replicas.")
        c.argument('max_replicas', type=int, help="The maximum number of replicas.")
        c.argument('scale_rule_name', options_list=['--scale-rule-name', '--srn'], help="The name of the scale rule.")
        c.argument('scale_rule_type', options_list=['--scale-rule-type', '--srt'], help="The type of the scale rule. Default: http. For more information please visit https://learn.microsoft.com/azure/container-apps/scale-app#scale-triggers")
        c.argument('scale_rule_http_concurrency', type=int, options_list=['--scale-rule-http-concurrency', '--srhc', '--srtc', '--scale-rule-tcp-concurrency'], help="The maximum number of concurrent requests before scale out. Only supported for http and tcp scale rules.")
        c.argument('scale_rule_metadata', nargs="+", options_list=['--scale-rule-metadata', '--srm'], help="Scale rule metadata. Metadata must be in format \"{key}={value} {key}={value} ...\".")
        c.argument('scale_rule_auth', nargs="+", options_list=['--scale-rule-auth', '--sra'], help="Scale rule auth parameters. Auth parameters must be in format \"{triggerParameter}={secretRef} {triggerParameter}={secretRef} ...\".")

    # Dapr
    with self.argument_context('containerapp', arg_group='Dapr') as c:
        c.argument('dapr_enabled', options_list=['--enable-dapr'], default=False, arg_type=get_three_state_flag(), help="Boolean indicating if the Dapr side car is enabled.")
        c.argument('dapr_app_port', type=int, help="The port Dapr uses to talk to the application.")
        c.argument('dapr_app_id', help="The Dapr application identifier.")
        c.argument('dapr_app_protocol', arg_type=get_enum_type(['http', 'grpc']), help="The protocol Dapr uses to talk to the application.")
        c.argument('dapr_http_read_buffer_size', options_list=['--dapr-http-read-buffer-size', '--dhrbs'], type=int, help="Dapr max size of http header read buffer in KB to handle when sending multi-KB headers..")
        c.argument('dapr_http_max_request_size', options_list=['--dapr-http-max-request-size', '--dhmrs'], type=int, help="Increase max size of request body http and grpc servers parameter in MB to handle uploading of big files.")
        c.argument('dapr_log_level', arg_type=get_enum_type(["info", "debug", "warn", "error"]), help="Set the log level for the Dapr sidecar.")
        c.argument('dapr_enable_api_logging', options_list=['--dapr-enable-api-logging', '--dal'], help="Enable API logging for the Dapr sidecar.")

    # Configuration
    with self.argument_context('containerapp', arg_group='Configuration') as c:
        c.argument('revisions_mode', arg_type=get_enum_type(['single', 'multiple']), help="The active revisions mode for the container app.")
        c.argument('registry_server', validator=validate_registry_server, help="The container registry server hostname, e.g. myregistry.azurecr.io.")
        c.argument('registry_pass', validator=validate_registry_pass, options_list=['--registry-password'], help="The password to log in to container registry. If stored as a secret, value must start with \'secretref:\' followed by the secret name.")
        c.argument('registry_user', validator=validate_registry_user, options_list=['--registry-username'], help="The username to log in to container registry.")
        c.argument('secrets', nargs='*', options_list=['--secrets', '-s'], help="A list of secret(s) for the container app. Space-separated values in 'key=value' format.")
        c.argument('registry_identity', help="A Managed Identity to authenticate with the registry server instead of username/password. Use a resource ID or 'system' for user-defined and system-defined identities, respectively. The registry must be an ACR. If possible, an 'acrpull' role assignemnt will be created for the identity automatically.")

    # Ingress
    with self.argument_context('containerapp', arg_group='Ingress') as c:
        c.argument('ingress', default=None, arg_type=get_enum_type(['internal', 'external']), help="The ingress type.")
        c.argument('target_port', type=int, validator=validate_target_port, help="The application port used for ingress traffic.")
        c.argument('transport', arg_type=get_enum_type(['auto', 'http', 'http2', 'tcp']), help="The transport protocol used for ingress traffic.")
        c.argument('exposed_port', type=int, help="Additional exposed port. Only supported by tcp transport protocol. Must be unique per environment if the app ingress is external.")

    with self.argument_context('containerapp create') as c:
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help="Name of the workload profile to run the app on.")
        c.argument('secret_volume_mount', help="Path to mount all secrets e.g. mnt/secrets")
        c.argument('termination_grace_period', type=int, options_list=['--termination-grace-period', '--tgp'], help="Duration in seconds a replica is given to gracefully shut down before it is forcefully terminated. (Default: 30)")
        c.argument('allow_insecure', validator=validate_allow_insecure, arg_type=get_three_state_flag(), help='Allow insecure connections for ingress traffic.')

    with self.argument_context('containerapp create', arg_group='Identity') as c:
        c.argument('user_assigned', nargs='+', help="Space-separated user identities to be assigned.")
        c.argument('system_assigned', help="Boolean indicating whether to assign system-assigned identity.")

    with self.argument_context('containerapp create', arg_group='Container') as c:
        c.argument('image', options_list=['--image', '-i'], help="Container image, e.g. publisher/image-name:tag.")

    with self.argument_context('containerapp show') as c:
        c.argument('show_secrets', help="Show Containerapp secrets.", action='store_true')

    with self.argument_context('containerapp update', arg_group='Container') as c:
        c.argument('image', options_list=['--image', '-i'], help="Container image, e.g. publisher/image-name:tag.")
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help='The friendly name for the workload profile')
        c.argument('secret_volume_mount', help="Path to mount all secrets e.g. mnt/secrets")
        c.argument('termination_grace_period', type=int, options_list=['--termination-grace-period', '--tgp'], help="Duration in seconds a replica is given to gracefully shut down before it is forcefully terminated. (Default: 30)")

    with self.argument_context('containerapp scale') as c:
        c.argument('min_replicas', type=int, help="The minimum number of replicas.")
        c.argument('max_replicas', type=int, help="The maximum number of replicas.")

    with self.argument_context('containerapp env') as c:
        c.argument('name', name_type, help='Name of the Container Apps environment.')
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help='Location of resource. Examples: eastus2, northeurope')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('containerapp env', arg_group='Monitoring') as c:
        c.argument('logs_destination', arg_type=get_enum_type(["log-analytics", "azure-monitor", "none"]), help='Logs destination.')
        c.argument('logs_customer_id', options_list=['--logs-workspace-id'], help='Workspace ID of the Log Analytics workspace to send diagnostics logs to. Only works with logs destination "log-analytics". You can use \"az monitor log-analytics workspace create\" to create one. Extra billing may apply.')
        c.argument('logs_key', options_list=['--logs-workspace-key'], help='Log Analytics workspace key to configure your Log Analytics workspace. Only works with logs destination "log-analytics". You can use \"az monitor log-analytics workspace get-shared-keys\" to retrieve the key.')
        c.argument('storage_account', validator=validate_storage_name_or_id, help="Name or resource ID of the storage account used for Azure Monitor. If this value is provided, Azure Monitor Diagnostic Settings will be created automatically.")

    with self.argument_context('containerapp env', arg_group='Dapr') as c:
        c.argument('instrumentation_key', options_list=['--dapr-instrumentation-key'], help='Application Insights instrumentation key used by Dapr to export Service to Service communication telemetry', deprecate_info=c.deprecate(hide=True))
        c.argument('dapr_connection_string', options_list=['--dapr-connection-string', '-d'], help='Application Insights connection string used by Dapr to export service to service communication telemetry.')

    with self.argument_context('containerapp env update', arg_group='Dapr') as c:
        c.argument('dapr_connection_string', options_list=['--dapr-connection-string', '-d'], help='Application Insights connection string used by Dapr to export service to service communication telemetry. Use "none" to remove it.')

    with self.argument_context('containerapp env', arg_group='Virtual Network') as c:
        c.argument('infrastructure_subnet_resource_id', options_list=['--infrastructure-subnet-resource-id', '-s'], help='Resource ID of a subnet for infrastructure components and user app containers.')
        c.argument('infrastructure_resource_group', options_list=['--infrastructure-resource-group', '-i'], help='Name for resource group that will contain infrastructure resources. If not provided, a resource group name will be generated.')
        c.argument('docker_bridge_cidr', options_list=['--docker-bridge-cidr'], help='CIDR notation IP range assigned to the Docker bridge. It must not overlap with any Subnet IP ranges or the IP range defined in Platform Reserved CIDR, if defined', deprecate_info=Deprecated(self.cli_ctx, target='--docker-bridge-cidr', hide=True, message_func=lambda x: "Option '--docker-bridge-cidr' has been deprecated and will be removed in the Ignite 2024"))
        c.argument('platform_reserved_cidr', options_list=['--platform-reserved-cidr'], help='IP range in CIDR notation that can be reserved for environment infrastructure IP addresses. It must not overlap with any other Subnet IP ranges')
        c.argument('platform_reserved_dns_ip', options_list=['--platform-reserved-dns-ip'], help='An IP address from the IP range defined by Platform Reserved CIDR that will be reserved for the internal DNS server.')
        c.argument('internal_only', arg_type=get_three_state_flag(), options_list=['--internal-only'], help='Boolean indicating the environment only has an internal load balancer. These environments do not have a public static IP resource, therefore must provide infrastructureSubnetResourceId if enabling this property')

    with self.argument_context('containerapp env', arg_group='Custom Domain') as c:
        c.argument('hostname', options_list=['--custom-domain-dns-suffix', '--dns-suffix'], help='The DNS suffix for the environment\'s custom domain.')
        c.argument('certificate_file', options_list=['--custom-domain-certificate-file', '--certificate-file'], help='The filepath of the certificate file (.pfx or .pem) for the environment\'s custom domain. To manage certificates for container apps, use `az containerapp env certificate`.')
        c.argument('certificate_password', options_list=['--custom-domain-certificate-password', '--certificate-password'], help='The certificate file password for the environment\'s custom domain.')

    with self.argument_context('containerapp env', arg_group='Peer Authentication') as c:
        c.argument('mtls_enabled', arg_type=get_three_state_flag(), options_list=['--enable-mtls'], help='Boolean indicating if mTLS peer authentication is enabled for the environment.')

    with self.argument_context('containerapp env', arg_group='Peer Traffic Configuration') as c:
        c.argument('p2p_encryption_enabled', arg_type=get_three_state_flag(), options_list=['--enable-peer-to-peer-encryption'], help='Boolean indicating whether the peer-to-peer traffic encryption is enabled for the environment.')

    with self.argument_context('containerapp env create') as c:
        c.argument('zone_redundant', options_list=["--zone-redundant", "-z"], help="Enable zone redundancy on the environment. Cannot be used without --infrastructure-subnet-resource-id. If used with --location, the subnet's location must match")
        c.argument('enable_workload_profiles', arg_type=get_three_state_flag(), options_list=["--enable-workload-profiles", "-w"], help="Boolean indicating if the environment is enabled to have workload profiles")

    with self.argument_context('containerapp env update') as c:
        c.argument('name', name_type, help='Name of the Container Apps environment.')
        c.argument('tags', arg_type=tags_type)
        # c.argument('plan', help="The sku of the containerapp environment. Downgrading from premium to consumption is not supported. Environment must have a subnet to be upgraded to premium sku.", arg_type=get_enum_type(['consumption', 'premium', None], default=None))
        c.argument('workload_profile_type', help='The type of workload profile to add or update in this environment, --workload-profile-name required')
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help='The friendly name for the workload profile')
        c.argument('min_nodes', help='The minimum nodes for this workload profile, --workload-profile-name required')
        c.argument('max_nodes', help='The maximum nodes for this workload profile, --workload-profile-name required')

    with self.argument_context('containerapp env delete') as c:
        c.argument('name', name_type, help='Name of the Container Apps Environment.')

    with self.argument_context('containerapp env show') as c:
        c.argument('name', name_type, help='Name of the Container Apps Environment.')

    with self.argument_context('containerapp env certificate upload') as c:
        c.argument('certificate_file', options_list=['--certificate-file', '-f'], help='The filepath of the .pfx or .pem file')
        c.argument('certificate_name', options_list=['--certificate-name', '-c'], help='Name of the certificate which should be unique within the Container Apps environment.')
        c.argument('certificate_password', options_list=['--password', '-p'], help='The certificate file password')
        c.argument('prompt', options_list=['--show-prompt'], action='store_true', help='Show prompt to upload an existing certificate.')

    with self.argument_context('containerapp env certificate create') as c:
        c.argument('hostname', options_list=['--hostname'], help='The custom domain name.')
        c.argument('certificate_name', options_list=['--certificate-name', '-c'], help='Name of the managed certificate which should be unique within the Container Apps environment.')
        c.argument('validation_method', arg_type=get_enum_type(['HTTP', 'CNAME', 'TXT']), options_list=['--validation-method', '-v'], help='Validation method of custom domain ownership.')

    with self.argument_context('containerapp env certificate list') as c:
        c.argument('name', id_part=None)
        c.argument('certificate', options_list=['--certificate', '-c'], help='Name or resource id of the certificate.')
        c.argument('thumbprint', options_list=['--thumbprint', '-t'], help='Thumbprint of the certificate.')
        c.argument('managed_certificates_only', options_list=['--managed-certificates-only', '-m'], help='List managed certificates only.', action='store_true', is_preview=True)
        c.argument('private_key_certificates_only', options_list=['--private-key-certificates-only', '-p'], help='List private-key certificates only.', action='store_true', is_preview=True)

    with self.argument_context('containerapp env certificate delete') as c:
        c.argument('certificate', options_list=['--certificate', '-c'], help='Name or resource id of the certificate.')
        c.argument('thumbprint', options_list=['--thumbprint', '-t'], help='Thumbprint of the certificate.')

    with self.argument_context('containerapp env storage') as c:
        c.argument('name', id_part=None)
        c.argument('storage_name', help="Name of the storage.")
        c.argument('access_mode', id_part=None, arg_type=get_enum_type(["ReadWrite", "ReadOnly"]), help="Access mode for the AzureFile storage.")
        c.argument('azure_file_account_key', options_list=["--azure-file-account-key", "--storage-account-key", "-k"], help="Key of the AzureFile storage account.")
        c.argument('azure_file_share_name', options_list=["--azure-file-share-name", "--file-share", "-f"], help="Name of the share on the AzureFile storage.")
        c.argument('azure_file_account_name', options_list=["--azure-file-account-name", "--account-name", "-a"], help="Name of the AzureFile storage account.")

    with self.argument_context('containerapp identity') as c:
        c.argument('user_assigned', nargs='+', help="Space-separated user identities.")
        c.argument('system_assigned', help="Boolean indicating whether to assign system-assigned identity.")

    with self.argument_context('containerapp identity remove') as c:
        c.argument('user_assigned', nargs='*', help="Space-separated user identities. If no user identities are specified, all user identities will be removed.")

    with self.argument_context('containerapp github-action add') as c:
        c.argument('repo_url', help='The GitHub repository to which the workflow file will be added. In the format: `https://github.com/<owner>/<repository-name>`')
        c.argument('token', help='A Personal Access Token with write access to the specified repository. For more information: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line')
        c.argument('branch', options_list=['--branch', '-b'], help='The branch of the Github repo. Assumed to be the Github repo\'s default branch if not specified.')
        c.argument('login_with_github', help='Interactively log in with Github to retrieve the Personal Access Token')
        c.argument('registry_url', help='The container registry server, e.g. myregistry.azurecr.io')
        c.argument('registry_username', help='The username of the registry. If using Azure Container Registry, we will try to infer the credentials if not supplied')
        c.argument('registry_password', help='The password of the registry. If using Azure Container Registry, we will try to infer the credentials if not supplied')
        c.argument('context_path', help='Path in the repo from which to run the docker build. Defaults to "./"')
        c.argument('service_principal_client_id', help='The service principal client ID. ')
        c.argument('service_principal_client_secret', help='The service principal client secret.')
        c.argument('service_principal_tenant_id', help='The service principal tenant ID.')
        c.argument('image', options_list=['--image', '-i'], help="Container image name that the Github Action should use. Defaults to the Container App name.")
        c.ignore('trigger_existing_workflow')

    with self.argument_context('containerapp github-action delete') as c:
        c.argument('token', help='A Personal Access Token with write access to the specified repository. For more information: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line')
        c.argument('login_with_github', help='Interactively log in with Github to retrieve the Personal Access Token')

    with self.argument_context('containerapp revision') as c:
        c.argument('revision_name', options_list=['--revision'], help='Name of the revision.')
        c.argument('all', help='Show inactive revisions.', action='store_true')

    with self.argument_context('containerapp revision copy') as c:
        c.argument('from_revision', help='Revision to copy from. Default: latest revision.')
        c.argument('image', options_list=['--image', '-i'], help="Container image, e.g. publisher/image-name:tag.")
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help='The friendly name for the workload profile')

    with self.argument_context('containerapp revision label') as c:
        c.argument('name', id_part=None)
        c.argument('revision', help='Name of the revision.')
        c.argument('label', help='Name of the label.')
        c.argument('yes', options_list=['--no-prompt', '--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')

    with self.argument_context('containerapp revision label') as c:
        c.argument('source_label', options_list=['--source'], help='Source label to be swapped.')
        c.argument('target_label', options_list=['--target'], help='Target label to be swapped to.')

    with self.argument_context('containerapp ingress') as c:
        c.argument('allow_insecure', arg_type=get_three_state_flag(), help='Allow insecure connections for ingress traffic.')
        c.argument('type', arg_type=get_enum_type(['internal', 'external']), help="The ingress type.")
        c.argument('transport', arg_type=get_enum_type(['auto', 'http', 'http2', 'tcp']), help="The transport protocol used for ingress traffic.")
        c.argument('target_port', type=int, validator=validate_target_port, help="The application port used for ingress traffic.")
        c.argument('exposed_port', type=int, help="Additional exposed port. Only supported by tcp transport protocol. Must be unique per environment if the app ingress is external.")

    with self.argument_context('containerapp ingress access-restriction') as c:
        c.argument('action', arg_type=get_enum_type(['Allow', 'Deny']), help='Whether the IP security restriction allows or denies access. All restrictions must be use the same action. If no restrictions are set, all traffic is allowed.')
        c.argument('rule_name', help="The IP security restriction name.")
        c.argument('description', help="The description of the IP security restriction.")
        c.argument('ip_address', help="The address range of the IP security restriction in IPv4 CIDR notation. (for example, '198.51.100.14/24')")

    with self.argument_context('containerapp ingress access-restriction list') as c:
        c.argument('name', id_part=None)

    with self.argument_context('containerapp ingress traffic') as c:
        c.argument('revision_weights', nargs='+', options_list=['--revision-weight', c.deprecate(target='--traffic-weight', redirect='--revision-weight')], help="A list of revision weight(s) for the container app. Space-separated values in 'revision_name=weight' format. For latest revision, use 'latest=weight'")
        c.argument('label_weights', nargs='+', options_list=['--label-weight'], help="A list of label weight(s) for the container app. Space-separated values in 'label_name=weight' format.")

    with self.argument_context('containerapp ingress sticky-sessions') as c:
        c.argument('affinity', arg_type=get_enum_type(['sticky', 'none']), help='Whether the affinity for the container app is Sticky or None.')

    with self.argument_context('containerapp ingress cors') as c:
        c.argument('allowed_origins', nargs='*', options_list=['--allowed-origins', '-r'], help="A list of allowed origin(s) for the container app. Values are space-separated. Empty string to clear existing values.")
        c.argument('allowed_methods', nargs='*', options_list=['--allowed-methods', '-m'], help="A list of allowed method(s) for the container app. Values are space-separated. Empty string to clear existing values.")
        c.argument('allowed_headers', nargs='*', options_list=['--allowed-headers', '-a'], help="A list of allowed header(s) for the container app. Values are space-separated. Empty string to clear existing values.")
        c.argument('expose_headers', nargs='*', options_list=['--expose-headers', '-e'], help="A list of expose header(s) for the container app. Values are space-separated. Empty string to clear existing values.")
        c.argument('allow_credentials', options_list=['--allow-credentials'], arg_type=get_three_state_flag(), help='Whether the credential is allowed for the container app.')
        c.argument('max_age', nargs='?', const='', validator=validate_cors_max_age, help="The maximum age of the allowed origin in seconds. Only postive integer or empty string are allowed. Empty string resets max_age to null.")

    with self.argument_context('containerapp secret') as c:
        c.argument('secrets', nargs='+', options_list=['--secrets', '-s'], help="A list of secret(s) for the container app. Space-separated values in 'key=value' or 'key=keyvaultref:keyvaulturl,identityref:identity' format (where 'key' cannot be longer than 20 characters. For 'identityref', Use 'system' for a system-defined identity or a resource id for a user-defined identity).")
        c.argument('secret_name', help="The name of the secret to show.")
        c.argument('secret_names', nargs='+', help="A list of secret(s) for the container app. Space-separated secret values names.")
        c.argument('show_values', help='Show the secret values.')
        c.ignore('disable_max_length')

    with self.argument_context('containerapp env dapr-component') as c:
        c.argument('dapr_component_name', help="The Dapr component name.")
        c.argument('environment_name', options_list=['--name', '-n'], help="The environment name.")
        c.argument('yaml', type=file_type, help='Path to a .yaml file with the configuration of a Dapr component. All other parameters will be ignored. For an example, see https://learn.microsoft.com/en-us/azure/container-apps/dapr-overview?tabs=bicep1%2Cyaml#component-schema')

    with self.argument_context('containerapp revision set-mode') as c:
        c.argument('mode', arg_type=get_enum_type(['single', 'multiple']), help="The active revisions mode for the container app.")

    with self.argument_context('containerapp registry') as c:
        c.argument('server', help="The container registry server, e.g. myregistry.azurecr.io")
        c.argument('username', help='The username of the registry. If using Azure Container Registry, we will try to infer the credentials if not supplied')
        c.argument('password', help='The password of the registry. If using Azure Container Registry, we will try to infer the credentials if not supplied')
        c.argument('identity', help="The managed identity with which to authenticate to the Azure Container Registry (instead of username/password). Use 'system' for a system-defined identity or a resource id for a user-defined identity. The managed identity should have been assigned acrpull permissions on the ACR before deployment (use 'az role assignment create --role acrpull ...').")

    with self.argument_context('containerapp registry list') as c:
        c.argument('name', id_part=None)

    with self.argument_context('containerapp secret list') as c:
        c.argument('name', id_part=None)

    with self.argument_context('containerapp revision list') as c:
        c.argument('name', id_part=None)

    with self.argument_context('containerapp up') as c:
        c.argument('resource_group_name', configured_default='resource_group_name', id_part=None)
        c.argument('location', configured_default='location')
        c.argument('name', configured_default='name', id_part=None)
        c.argument('managed_env', configured_default='managed_env')
        c.argument('registry_server', configured_default='registry_server')
        c.argument('source', help='Local directory path containing the application source and Dockerfile for building the container image. Preview: If no Dockerfile is present, a container image is generated using buildpacks. If Docker is not running or buildpacks cannot be used, Oryx will be used to generate the image. See the supported Oryx runtimes here: https://github.com/microsoft/Oryx/blob/main/doc/supportedRuntimeVersions.md.')
        c.argument('image', options_list=['--image', '-i'], help="Container image, e.g. publisher/image-name:tag.")
        c.argument('browse', help='Open the app in a web browser after creation and deployment, if possible.')
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help='The friendly name for the workload profile')

    with self.argument_context('containerapp up', arg_group='Log Analytics (Environment)') as c:
        c.argument('logs_customer_id', options_list=['--logs-workspace-id'], help='Workspace ID of the Log Analytics workspace to send diagnostics logs to. You can use \"az monitor log-analytics workspace create\" to create one. Extra billing may apply.')
        c.argument('logs_key', options_list=['--logs-workspace-key'], help='Log Analytics workspace key to configure your Log Analytics workspace. You can use \"az monitor log-analytics workspace get-shared-keys\" to retrieve the key.')
        c.ignore('no_wait')

    with self.argument_context('containerapp up', arg_group='Github Repo') as c:
        c.argument('repo', help='Create an app via Github Actions. In the format: `https://github.com/<owner>/<repository-name>` or `<owner>/<repository-name>`')
        c.argument('token', help='A Personal Access Token with write access to the specified repository. For more information: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line. If not provided or not found in the cache (and using --repo), a browser page will be opened to authenticate with Github.')
        c.argument('branch', options_list=['--branch', '-b'], help='The branch of the Github repo. Assumed to be the Github repo\'s default branch if not specified.')
        c.argument('context_path', help='Path in the repo from which to run the docker build. Defaults to "./". Dockerfile is assumed to be named "Dockerfile" and in this directory.')
        c.argument('service_principal_client_id', help='The service principal client ID. Used by Github Actions to authenticate with Azure.', options_list=["--service-principal-client-id", "--sp-cid"])
        c.argument('service_principal_client_secret', help='The service principal client secret. Used by Github Actions to authenticate with Azure.', options_list=["--service-principal-client-secret", "--sp-sec"])
        c.argument('service_principal_tenant_id', help='The service principal tenant ID. Used by Github Actions to authenticate with Azure.', options_list=["--service-principal-tenant-id", "--sp-tid"])

    with self.argument_context('containerapp auth') as c:
        # subgroup update
        c.argument('client_id', help='The Client ID of the app used for login.')
        c.argument('client_secret', help='The client secret.')
        c.argument('client_secret_setting_name', options_list=['--client-secret-name'], help='The app secret name that contains the client secret of the relying party application.')
        c.argument('issuer', help='The OpenID Connect Issuer URI that represents the entity which issues access tokens for this application.')
        c.argument('allowed_token_audiences', options_list=['--allowed-token-audiences', '--allowed-audiences'], help='The configuration settings of the allowed list of audiences from which to validate the JWT token.')
        c.argument('client_secret_certificate_thumbprint', options_list=['--thumbprint', '--client-secret-certificate-thumbprint'], help='Alternative to AAD Client Secret, thumbprint of a certificate used for signing purposes')
        c.argument('client_secret_certificate_san', options_list=['--san', '--client-secret-certificate-san'], help='Alternative to AAD Client Secret and thumbprint, subject alternative name of a certificate used for signing purposes')
        c.argument('client_secret_certificate_issuer', options_list=['--certificate-issuer', '--client-secret-certificate-issuer'], help='Alternative to AAD Client Secret and thumbprint, issuer of a certificate used for signing purposes')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')
        c.argument('tenant_id', help='The tenant id of the application.')
        c.argument('app_id', help='The App ID of the app used for login.')
        c.argument('app_secret', help='The app secret.')
        c.argument('app_secret_setting_name', options_list=['--app-secret-name', '--secret-name'], help='The app secret name that contains the app secret.')
        c.argument('graph_api_version', help='The version of the Facebook api to be used while logging in.')
        c.argument('scopes', help='A list of the scopes that should be requested while authenticating.')
        c.argument('consumer_key', help='The OAuth 1.0a consumer key of the Twitter application used for sign-in.')
        c.argument('consumer_secret', help='The consumer secret.')
        c.argument('consumer_secret_setting_name', options_list=['--consumer-secret-name', '--secret-name'], help='The consumer secret name that contains the app secret.')
        c.argument('provider_name', required=True, help='The name of the custom OpenID Connect provider.')
        c.argument('openid_configuration', help='The endpoint that contains all the configuration endpoints for the provider.')
        c.argument('token_store', arg_type=get_three_state_flag(), help='Boolean indicating if token store is enabled for the app.')
        c.argument('sas_url_secret', help='The blob storage SAS URL to be used for token store.')
        c.argument('sas_url_secret_name', help='The secret name that contains blob storage SAS URL to be used for token store.')

        # auth update
        c.argument('set_string', options_list=['--set'], help='Value of a specific field within the configuration settings for the Azure App Service Authentication / Authorization feature.')
        c.argument('config_file_path', help='The path of the config file containing auth settings if they come from a file.')
        c.argument('unauthenticated_client_action', options_list=['--unauthenticated-client-action', '--action'], arg_type=get_enum_type(UNAUTHENTICATED_CLIENT_ACTION), help='The action to take when an unauthenticated client attempts to access the app.')
        c.argument('redirect_provider', help='The default authentication provider to use when multiple providers are configured.')
        c.argument('require_https', arg_type=get_three_state_flag(), help='false if the authentication/authorization responses not having the HTTPS scheme are permissible; otherwise, true.')
        c.argument('proxy_convention', arg_type=get_enum_type(FORWARD_PROXY_CONVENTION), help='The convention used to determine the url of the request made.')
        c.argument('proxy_custom_host_header', options_list=['--proxy-custom-host-header', '--custom-host-header'], help='The name of the header containing the host of the request.')
        c.argument('proxy_custom_proto_header', options_list=['--proxy-custom-proto-header', '--custom-proto-header'], help='The name of the header containing the scheme of the request.')
        c.argument('excluded_paths', help='The list of paths that should be excluded from authentication rules.')
        c.argument('enabled', arg_type=get_three_state_flag(), help='true if the Authentication / Authorization feature is enabled for the current app; otherwise, false.')
        c.argument('runtime_version', help='The RuntimeVersion of the Authentication / Authorization feature in use for the current app.')

    with self.argument_context('containerapp ssl upload') as c:
        c.argument('hostname', help='The custom domain name.')
        c.argument('environment', options_list=['--environment', '-e'], help='Name or resource id of the Container App environment.')
        c.argument('certificate_file', options_list=['--certificate-file', '-f'], help='The filepath of the .pfx or .pem file')
        c.argument('certificate_password', options_list=['--password', '-p'], help='The certificate file password')
        c.argument('certificate_name', options_list=['--certificate-name', '-c'], help='Name of the certificate which should be unique within the Container Apps environment.')

    with self.argument_context('containerapp hostname bind') as c:
        c.argument('hostname', help='The custom domain name.')
        c.argument('thumbprint', options_list=['--thumbprint', '-t'], help='Thumbprint of the certificate.')
        c.argument('certificate', options_list=['--certificate', '-c'], help='Name or resource id of the certificate.')
        c.argument('environment', options_list=['--environment', '-e'], help='Name or resource id of the Container App environment.')
        c.argument('validation_method', options_list=['--validation-method', '-v'], help='Validation method of custom domain ownership.')

    with self.argument_context('containerapp hostname add') as c:
        c.argument('hostname', help='The custom domain name.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('containerapp hostname list') as c:
        c.argument('name', id_part=None)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('containerapp hostname delete') as c:
        c.argument('hostname', help='The custom domain name.')

    # Compose
    with self.argument_context('containerapp compose create') as c:
        c.argument('environment', options_list=['--environment', '-e'], help='Name or resource id of the Container App environment.')
        c.argument('compose_file_path', options_list=['--compose-file-path', '-f'], help='Path to a Docker Compose file with the configuration to import to Azure Container Apps.')
        c.argument('transport_mapping', options_list=['--transport-mapping', c.deprecate(target='--transport', redirect='--transport-mapping')], action='append', nargs='+', help="Transport options per Container App instance (servicename=transportsetting).")

    with self.argument_context('containerapp env workload-profile') as c:
        c.argument('env_name', options_list=['--name', '-n'], help="The name of the Container App environment")
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help='The friendly name for the workload profile')

    with self.argument_context('containerapp env workload-profile add') as c:
        c.argument('workload_profile_type', help="The type of workload profile to add to this environment. Run `az containerapp env workload-profile list-supported -l <region>` to check the options for your region.")
        c.argument('min_nodes', help="The minimum node count for the workload profile")
        c.argument('max_nodes', help="The maximum node count for the workload profile")

    with self.argument_context('containerapp env workload-profile update') as c:
        c.argument('min_nodes', help="The minimum node count for the workload profile")
        c.argument('max_nodes', help="The maximum node count for the workload profile")

    # Container App job
    with self.argument_context('containerapp job') as c:
        c.argument('name', name_type, metavar='NAME', id_part='name', help=f"The name of the Container Apps Job. A name must consist of lower case alphanumeric characters or '-', start with a letter, end with an alphanumeric character, cannot have '--', and must be less than {MAXIMUM_CONTAINER_APP_NAME_LENGTH} characters.")
        c.argument('cron_expression', help='Cron expression. Only supported for trigger type "Schedule"')
        c.argument('image', help="Container image, e.g. publisher/image-name:tag.")
        c.argument('replica_completion_count', type=int, options_list=['--replica-completion-count', '--rcc'], help='Number of replicas that need to complete successfully for execution to succeed.')
        c.argument('replica_retry_limit', type=int, help='Maximum number of retries before the replica fails.')
        c.argument('replica_timeout', type=int, help='Maximum number of seconds a replica can execute.')
        c.argument('parallelism', type=int, help='Maximum number of replicas to run per execution.')
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help='The friendly name for the workload profile')
        c.argument('min_executions', type=int, help="Minimum number of job executions that are created for a trigger, default 0.")
        c.argument('max_executions', type=int, help="Maximum number of job executions that are created for a trigger, default 100.")
        c.argument('polling_interval', type=int, help="Interval to check each event source in seconds. Defaults to 30s.", default=30)

    with self.argument_context('containerapp job create') as c:
        c.argument('system_assigned', options_list=['--mi-system-assigned', c.deprecate(target='--system-assigned', redirect='--mi-system-assigned', hide=True)], help='Boolean indicating whether to assign system-assigned identity.', action='store_true')
        c.argument('trigger_type', help='Trigger type. Schedule | Event | Manual')
        c.argument('user_assigned', options_list=['--mi-user-assigned', c.deprecate(target='--user-assigned', redirect='--mi-user-assigned', hide=True)], nargs='+', help='Space-separated user identities to be assigned.')

    with self.argument_context('containerapp job', arg_group='Scale') as c:
        c.argument('min_executions', type=int, help="Minimum number of job executions to run per polling interval.")
        c.argument('max_executions', type=int, help="Maximum number of job executions to run per polling interval.")
        c.argument('polling_interval', type=int, help="Interval to check each event source in seconds. Defaults to 30s.")
        c.argument('scale_rule_type', options_list=['--scale-rule-type', '--srt'], help="The type of the scale rule.")

    with self.argument_context('containerapp job stop') as c:
        c.argument('job_execution_name', help='name of the specific job execution which needs to be stopped.')
        c.argument('execution_name_list', help='comma separated list of job execution names.', deprecate_info=Deprecated(self.cli_ctx, target='--execution_name_list', hide=True, message_func=lambda x: "Option 'execution-name-list' has been deprecated and will be removed in the next Cli version"))

    with self.argument_context('containerapp job execution') as c:
        c.argument('name', id_part=None)
        c.argument('job_execution_name', help='name of the specific job execution.')

    with self.argument_context('containerapp job secret') as c:
        c.argument('secrets', nargs='+', options_list=['--secrets', '-s'], help="A list of secret(s) for the container app job. Space-separated values in 'key=value' or 'key=keyvaultref:keyvaulturl,identityref:identity' format (where 'key' cannot be longer than 20 characters).")
        c.argument('name', id_part=None, help="The name of the container app job for which the secret needs to be retrieved.")
        c.argument('secret_name', id_part=None, help="The name of the secret to show.")
        c.argument('secret_names', id_part=None, nargs='+', help="A list of secret(s) for the container app job. Space-separated secret values names.")
        c.argument('show_values', action='store_true', help='Show the secret values.')
        c.ignore('disable_max_length')

    with self.argument_context('containerapp job identity') as c:
        c.argument('user_assigned', nargs='+', help="Space-separated user identities.")
        c.argument('system_assigned', help="Boolean indicating whether to assign system-assigned identity.", action='store_true')

    with self.argument_context('containerapp job identity remove') as c:
        c.argument('user_assigned', nargs='*', help="Space-separated user identities. If no user identities are specified, all user identities will be removed.")

    with self.argument_context('containerapp job registry') as c:
        c.argument('server', help="The container registry server, e.g. myregistry.azurecr.io")
        c.argument('username', help='The username of the registry. If using Azure Container Registry, we will try to infer the credentials if not supplied')
        c.argument('password', help='The password of the registry. If using Azure Container Registry, we will try to infer the credentials if not supplied')
        c.argument('identity', help="The managed identity with which to authenticate to the Azure Container Registry (instead of username/password). Use 'system' for a system-defined identity or a resource id for a user-defined identity. The managed identity should have been assigned acrpull permissions on the ACR before deployment (use 'az role assignment create --role acrpull ...').")

    with self.argument_context('containerapp job registry list') as c:
        c.argument('name', id_part=None)

    with self.argument_context('containerapp env http-route-config') as c:
        c.argument('http_route_config_name', options_list=['--http-route-config-name', '-r'], help="The name of the http route configuration.")
        c.argument('yaml', help="The path to the YAML input file.")
        c.argument('name', id_part=None)

    with self.argument_context('containerapp env premium-ingress') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None)
        c.argument('name', options_list=['--name', '-n'], help="The name of the managed environment.")
        c.argument('workload_profile_name', options_list=['--workload-profile-name', '-w'], help="The workload profile to run ingress replicas on. This profile must not be shared with any container app or job.")
        c.argument('termination_grace_period', options_list=['--termination-grace-period', '-t'], type=int, help="Time in seconds to drain requests during ingress shutdown. Default 500, minimum 0, maximum 3600.")
        c.argument('request_idle_timeout', type=int, help="Timeout in minutes for idle requests. Default 4, minimum 4, maximum 30.")
        c.argument('header_count_limit', type=int, help="Limit of http headers per request. Default 100, minimum 1.")
