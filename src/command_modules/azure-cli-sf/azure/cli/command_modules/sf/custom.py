# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-lines

from __future__ import print_function

import os
import sys

# Breaking py2 to py3 change
try:
    from urllib.parse import urlparse, urlencode, urlunparse
except ImportError:
    # pylint: disable=import-error
    from urlparse import urlparse, urlunparse
    # pylint: disable=no-name-in-module
    from urllib import urlencode

import requests
import azure.cli.core.azlogging as azlogging

from azure.cli.core._environment import get_config_dir
from azure.cli.core._config import AzConfig
from azure.cli.core.util import CLIError

# Really the CLI should do this for us but I cannot see how to get it to
CONFIG_PATH = os.path.join(get_config_dir(), "config")
az_config = AzConfig()

logger = azlogging.get_az_logger(__name__)


def sf_create_compose_application(  # pylint: disable=too-many-arguments
        compose_file, application_id, repo_user=None, encrypted=False,
        repo_pass=None, timeout=60):
    # We need to read from a file which makes this a custom command
    # Encrypted param to indicate a password will be prompted
    """
    Creates a Service Fabric application from a Compose file

    :param str application_id:  The id of application to create from
    Compose file. This is typically the full id of the application
    including "fabric:" URI scheme
    :param str compose_file: Path to the Compose file to use
    :param str repo_user: Container repository user name if needed for
    authentication
    :param bool encrypted: If true, indicate to use an encrypted password
    rather than prompting for a plaintext one
    :param str repo_pass: Encrypted container repository password
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value for this
    parameter is 60 seconds.
    """
    from azure.cli.core.util import read_file_content
    from azure.cli.command_modules.sf._factory import cf_sf_client
    from azure.cli.core.prompting import prompt_pass
    # pylint: disable=line-too-long
    from azure.servicefabric.models.create_compose_application_description import (  # noqa: justification, no way to shorten
        CreateComposeApplicationDescription
    )
    from azure.servicefabric.models.repository_credential import (
        RepositoryCredential
    )

    if (any([encrypted, repo_pass]) and
            not all([encrypted, repo_pass, repo_user])):
        raise CLIError(
            "Invalid arguments: [ --application_id --file | "
            "--application_id --file --repo_user | --application_id --file "
            "--repo_user --encrypted --repo_pass ])"
        )

    if repo_user:
        plaintext_pass = prompt_pass("Container repository password: ", False,
                                     "Password for container repository "
                                     "containing container images")
        repo_pass = plaintext_pass

    repo_cred = RepositoryCredential(repo_user, repo_pass, encrypted)

    file_contents = read_file_content(compose_file)

    model = CreateComposeApplicationDescription(application_id, file_contents,
                                                repo_cred)

    sf_client = cf_sf_client(None)
    sf_client.create_compose_application(model, timeout)


def sf_select(endpoint, cert=None,  # pylint: disable=too-many-arguments
              key=None, pem=None, ca=None, no_verify=False):
    """
    Connects to a Service Fabric cluster endpoint.


    If connecting to secure cluster specify a cert (.crt) and key file (.key)
    or a single file with both (.pem). Do not specify both. Optionally, if
    connecting to a secure cluster, specify also a path to a CA bundle file
    or directory of trusted CA certs.

    :param str endpoint: Cluster endpoint URL, including port and HTTP or HTTPS
    prefix
    :param str cert: Path to a client certificate file
    :param str key: Path to client certificate key file
    :param str pem: Path to client certificate, as a .pem file
    :param str ca: Path to CA certs directory to treat as valid or CA bundle
    file
    :param bool no_verify: Disable verification for certificates when using
    HTTPS, note: this is an insecure option and should not be used for
    production environments
    """
    from azure.cli.core._config import set_global_config_value

    usage = ("Valid syntax : --endpoint [ [ --key --cert | --pem ] "
             "[ --ca | --no-verify ] ]")

    if ca and not (pem or all([key, cert])):
        raise CLIError(usage)

    if no_verify and not (pem or all([key, cert])):
        raise CLIError(usage)

    if no_verify and ca:
        raise CLIError(usage)

    if any([cert, key]) and not all([cert, key]):
        raise CLIError(usage)

    if pem and any([cert, key]):
        raise CLIError(usage)

    if pem:
        set_global_config_value("servicefabric", "pem_path", pem)
        set_global_config_value("servicefabric", "security", "pem")
    elif cert:
        set_global_config_value("servicefabric", "cert_path", cert)
        set_global_config_value("servicefabric", "key_path", key)
        set_global_config_value("servicefabric", "security", "cert")
    else:
        set_global_config_value("servicefabric", "security", "none")

    if ca:
        set_global_config_value("servicefabric", "ca_path", ca)

    if no_verify:
        set_global_config_value("servicefabric", "no_verify", "True")
    else:
        set_global_config_value("servicefabric", "no_verify", "False")

    set_global_config_value("servicefabric", "endpoint", endpoint)


def sf_get_verify_setting():
    az_config.config_parser.read(CONFIG_PATH)
    no_verify = az_config.get("servicefabric", "no_verify", fallback="False")
    return no_verify == "True"


def sf_get_ca_cert_info():
    az_config.config_parser.read(CONFIG_PATH)
    ca_cert = az_config.get("servicefabric", "ca_path", fallback=None)
    return ca_cert


def sf_get_connection_endpoint():
    az_config.config_parser.read(CONFIG_PATH)
    return az_config.get("servicefabric", "endpoint", fallback=None)


def sf_get_cert_info():
    az_config.config_parser.read(CONFIG_PATH)
    security_type = str(az_config.get("servicefabric",
                                      "security", fallback=""))
    if security_type == "pem":
        pem_path = az_config.get("servicefabric", "pem_path", fallback=None)
        return pem_path
    elif security_type == "cert":
        cert_path = az_config.get("servicefabric", "cert_path", fallback=None)
        key_path = az_config.get("servicefabric", "key_path", fallback=None)
        return cert_path, key_path
    elif security_type == "none":
        return None
    else:
        raise CLIError("Cluster security type not set")


def sf_upload_app(path, show_progress=False):
    """
    Copies a Service Fabric application package to the image store.


    The cmdlet copies a Service Fabric application package to the image store.
    After copying the application package, use the sf application provision
    cmdlet to register the application type.

    Can optionally display upload progress for each file in the package.
    Upload progress is sent to `stderr`.

    :param str path: The path to your local application package
    :param bool show_progress: Show file upload progress
    """
    abspath = os.path.abspath(path)
    basename = os.path.basename(abspath)
    endpoint = sf_get_connection_endpoint()
    cert = sf_get_cert_info()
    ca_cert = False
    if cert is not None:
        ca_cert = sf_get_ca_cert_info()
    total_files_count = 0
    current_files_count = 0
    total_files_size = 0
    # For py2 we use dictionary instead of nonlocal
    current_files_size = {"size": 0}

    for root, _, files in os.walk(abspath):
        total_files_count += (len(files) + 1)
        for f in files:
            t = os.stat(os.path.join(root, f))
            total_files_size += t.st_size

    def print_progress(size, rel_file_path):
        current_files_size["size"] += size
        if show_progress:
            print(
                "[{}/{}] files, [{}/{}] bytes, {}".format(
                    current_files_count,
                    total_files_count,
                    current_files_size["size"],
                    total_files_size,
                    rel_file_path), file=sys.stderr)

    for root, _, files in os.walk(abspath):
        rel_path = os.path.normpath(os.path.relpath(root, abspath))
        for f in files:
            url_path = (
                os.path.normpath(os.path.join("ImageStore", basename,
                                              rel_path, f))
            ).replace("\\", "/")
            fp = os.path.normpath(os.path.join(root, f))
            with open(fp, 'rb') as file_opened:
                url_parsed = list(urlparse(endpoint))
                url_parsed[2] = url_path
                url_parsed[4] = urlencode(
                    {"api-version": "3.0-preview"})
                url = urlunparse(url_parsed)

                def file_chunk(target_file, rel_path, print_progress):
                    chunk = target_file.read(100000)
                    if chunk != b'':
                        print_progress(len(chunk), rel_path)
                        yield chunk

                fc = file_chunk(file_opened, os.path.normpath(
                    os.path.join(rel_path, f)
                ), print_progress)
                requests.put(url, data=fc, cert=cert,
                             verify=ca_cert)
                current_files_count += 1
                print_progress(0, os.path.normpath(
                    os.path.join(rel_path, f)
                ))
        url_path = (
            os.path.normpath(os.path.join("ImageStore", basename,
                                          rel_path, "_.dir"))
        ).replace("\\", "/")
        url_parsed = list(urlparse(endpoint))
        url_parsed[2] = url_path
        url_parsed[4] = urlencode({"api-version": "3.0-preview"})
        url = urlunparse(url_parsed)
        requests.put(url, cert=cert, verify=ca_cert)
        current_files_count += 1
        print_progress(0, os.path.normpath(os.path.join(rel_path, '_.dir')))

    if show_progress:
        print("[{}/{}] files, [{}/{}] bytes sent".format(
            current_files_count,
            total_files_count,
            current_files_size["size"],
            total_files_size), file=sys.stderr)


def sf_create_app(name,  # pylint: disable=too-many-locals,too-many-arguments
                  app_type, version, parameters=None, min_node_count=0,
                  max_node_count=0, metrics=None, timeout=60):
    """
    Creates a Service Fabric application using the specified description.

    :param str name: Application name
    :param str app_type: Application type
    :param str version: Application version
    :param long min_node_count: The minimum number of nodes where Service
    Fabric will reserve capacity for this application. Note that this does not
    mean that the services of this application will be placed on all of those
    nodes.
    :param long max_node_count: The maximum number of nodes where Service
    Fabric will reserve capacity for this application. Note that this does not
    mean that the services of this application will be placed on all of those
    nodes.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value for this
    parameter is 60 seconds.
    """
    from azure.servicefabric.models.application_description import (
        ApplicationDescription
    )
    from azure.servicefabric.models.application_parameter import (
        ApplicationParameter
    )
    from azure.servicefabric.models.application_capacity_description import (
        ApplicationCapacityDescription
    )
    from azure.servicefabric.models.application_metric_description import (
        ApplicationMetricDescription
    )
    from azure.cli.command_modules.sf._factory import cf_sf_client

    if min_node_count > max_node_count:
        raise CLIError("Note, the minimum node reserve capacity count cannot "
                       "be more than the maximum node count")

    app_params = None
    if parameters:
        app_params = []
        for k in parameters:
            # Create an application parameter for every of these
            p = ApplicationParameter(k, parameters[k])
            app_params.append(p)

    # For simplicity, we assume user pass in valid key names in the list, or
    # ignore the input
    app_metrics = None
    if metrics:
        app_metrics = []
        for k in metrics:
            metric = metrics[k]
            metric_name = metric.get("name", None)
            if metric_name is None:
                raise CLIError("Could not decode required application metric "
                               "name")
            metric_max_cap = metric.get("maximum_capacity", 0)
            metric_reserve_cap = metric.get("reservation_capacity", 0)
            metric_total_cap = metric.get("total_application_capacity", 0)
            metric_desc = ApplicationMetricDescription(metric_name,
                                                       metric_max_cap,
                                                       metric_reserve_cap,
                                                       metric_total_cap)
            app_metrics.append(metric_desc)

    app_cap_desc = ApplicationCapacityDescription(min_node_count,
                                                  max_node_count,
                                                  app_metrics)

    app_desc = ApplicationDescription(name, app_type, version, app_params,
                                      app_cap_desc)

    sf_client = cf_sf_client(None)
    sf_client.create_application(app_desc, timeout)


def sf_upgrade_app(  # pylint: disable=too-many-arguments,too-many-locals
        name, version, parameters, mode="UnmonitoredAuto",
        replica_set_check_timeout=None, force_restart=None,
        failure_action=None, health_check_wait_duration=None,
        health_check_stable_duration=None,
        health_check_retry_timeout=None, upgrade_timeout=None,
        upgrade_domain_timeout=None, warning_as_error=False,
        max_unhealthy_apps=0, default_service_health_policy=None,
        service_health_policy=None, timeout=60):
    """
    Starts upgrading an application in the Service Fabric cluster.

    Validates the supplied application upgrade parameters and starts upgrading
    the application if the parameters are valid.

    :param str name: Application name. The name of the target application,
    including the 'fabric' URI scheme.
    :param str version: The target application type version (found in the
    application manifest) for the application upgrade.
    :param str mode: The mode used to monitor health during a rolling upgrade.
    :param long replica_set_check_timeout: The maximum amount of time to block
    processing of an upgrade domain and prevent loss of availability when
    there are unexpected issues. Measured in seconds.
    :param bool force_restart: Forcefully restart processes during upgrade even
    when the code version has not changed.
    :param str failure_action: The action to perform when a Monitored upgrade
    encounters monitoring policy or health policy violations.
    :param int health_check_wait_duration: The amount of time to wait after
    completing an upgrade domain before applying health policies. Measured in
    milliseconds.
    :param int health_check_stable_duration: The amount of time that the
    application or cluster must remain healthy before the upgrade proceeds
    to the next upgrade domain. Measured in milliseconds.
    :param int health_check_retry_timeout: The amount of time to retry health
    evaluations when the application or cluster is unhealthy before the failure
    action is executed. Measured in milliseconds.
    :param int upgrade_timeout: The amount of time the overall upgrade has to
    complete before FailureAction is executed. Measured in milliseconds.
    :param int upgrade_domain_timeout: The amount of time each upgrade domain
    has to complete before FailureAction is executed. Measured in milliseconds.
    :param bool warning_as_error: Treat health evaluation warnings with the
    same severity as errors.
    :param int max_unhealthy_apps: The maximum allowed percentage of unhealthy
    deployed applications. Represented as a number between 0 and 100.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value for this
    parameter is 60 seconds.
    """
    from azure.servicefabric.models.application_upgrade_description import (
        ApplicationUpgradeDescription
    )
    from azure.servicefabric.models.application_parameter import (
        ApplicationParameter
    )
    from azure.servicefabric.models.monitoring_policy_description import (
        MonitoringPolicyDescription
    )
    from azure.servicefabric.models.application_health_policy import (
        ApplicationHealthPolicy
    )
    from azure.servicefabric.models.service_type_health_policy import (
        ServiceTypeHealthPolicy
    )
    # pylint: disable=line-too-long
    from azure.servicefabric.models.service_type_health_policy_map_item import (  # noqa: justification, no way to shorten
        ServiceTypeHealthPolicyMapItem
    )
    from azure.cli.command_modules.sf._factory import cf_sf_client

    monitoring_policy = MonitoringPolicyDescription(
        failure_action, health_check_wait_duration,
        health_check_stable_duration, health_check_retry_timeout,
        upgrade_timeout, upgrade_domain_timeout
    )

    app_params = None
    if parameters:
        app_params = []
        for k in parameters:
            # Create an application parameter for every of these
            p = ApplicationParameter(k, parameters[k])
            app_params.append(p)

    def_shp = None
    if default_service_health_policy:
        # Extract properties from dict using previously defined names
        shp = default_service_health_policy.get(
            "max_percent_unhealthy_partitions_per_service", 0
        )
        rhp = default_service_health_policy.get(
            "max_percent_unhealthy_replicas_per_partition", 0
        )
        ushp = default_service_health_policy.get(
            "max_percent_unhealthy_services", 0
        )
        def_shp = ServiceTypeHealthPolicy(shp, rhp, ushp)

    map_shp = None
    if service_health_policy:
        map_shp = []
        for st_desc in service_health_policy:
            st_name = st_desc.get("Key", None)
            if st_name is None:
                raise CLIError("Could not find service type name in service "
                               "health policy map")
            st_policy = st_desc.get("Value", None)
            if st_policy is None:
                raise CLIError("Could not find service type policy in service "
                               "health policy map")
            st_shp = st_policy.get(
                "max_percent_unhealthy_partitions_per_service", 0
            )
            st_rhp = st_policy.get(
                "max_percent_unhealthy_replicas_per_partition", 0
            )
            st_ushp = st_policy.get(
                "max_percent_unhealthy_services", 0
            )

            std_policy = ServiceTypeHealthPolicy(st_shp, st_rhp, st_ushp)
            std_list_item = ServiceTypeHealthPolicyMapItem(st_name, std_policy)

            map_shp.append(std_list_item)

    app_health_policy = ApplicationHealthPolicy(warning_as_error,
                                                max_unhealthy_apps, def_shp,
                                                map_shp)

    desc = ApplicationUpgradeDescription(name, version, app_params, "Rolling",
                                         mode, replica_set_check_timeout,
                                         force_restart, monitoring_policy,
                                         app_health_policy)

    sf_client = cf_sf_client(None)
    sf_client.start_application_upgrade(name, desc, timeout)
    # TODO consider additional parameter validation here rather than allowing
    # the gateway to reject it and return failure response


def sup_correlation_scheme(correlated_service, correlation):
    from azure.servicefabric.models.service_correlation_description import (
        ServiceCorrelationDescription
    )

    if (any([correlated_service, correlation]) and
            not all([correlated_service, correlation])):
        raise CLIError("Must specify both a correlation service and "
                       "correlation scheme")
    elif any([correlated_service, correlation]):
        return ServiceCorrelationDescription(correlation, correlated_service)
    else:
        return None


def sup_load_metrics(formatted_metrics):
    from azure.servicefabric.models.service_load_metric_description import (
        ServiceLoadMetricDescription
    )

    r = None
    if formatted_metrics:
        r = []
        for l in formatted_metrics:
            l_name = l.get("name", None)
            if l_name is None:
                raise CLIError("Could not find specified load metric name")
            l_weight = l.get("weight", None)
            l_primary = l.get("primary_default_load", None)
            l_secondary = l.get("secondary_default_load", None)
            l_default = l.get("default_load", None)
            l_desc = ServiceLoadMetricDescription(l_name, l_weight, l_primary,
                                                  l_secondary, l_default)
            r.append(l_desc)

    return r


def sup_placement_policies(formatted_placement_policies):
    # pylint: disable=line-too-long
    from azure.servicefabric.models.service_placement_non_partially_place_service_policy_description import (  # noqa: justification, no way to shorten
        ServicePlacementNonPartiallyPlaceServicePolicyDescription
    )
    # pylint: disable=line-too-long
    from azure.servicefabric.models.service_placement_prefer_primary_domain_policy_description import (  # noqa: justification, no way to shorten
        ServicePlacementPreferPrimaryDomainPolicyDescription
    )
    # pylint: disable=line-too-long
    from azure.servicefabric.models.service_placement_required_domain_policy_description import (  # noqa: justification, no way to shorten
        ServicePlacementRequiredDomainPolicyDescription
    )
    # pylint: disable=line-too-long
    from azure.servicefabric.models.service_placement_require_domain_distribution_policy_description import (  # noqa: justification, no way to shorten
        ServicePlacementRequireDomainDistributionPolicyDescription
    )

    if formatted_placement_policies:
        r = []
        # Not entirely documented but similar to the property names
        for p in formatted_placement_policies:
            p_type = p.get("type", None)
            if p_type is None:
                raise CLIError(
                    "Could not determine type of specified placement policy"
                )
            if p_type not in ["NonPartiallyPlaceService",
                              "PreferPrimaryDomain", "RequireDomain",
                              "RequireDomainDistribution"]:
                raise CLIError("Invalid type of placement policy specified")
            p_domain_name = p.get("domain_name", None)
            if (
                    p_domain_name is None and
                    p_type != "NonPartiallyPlaceService"
            ):
                raise CLIError(
                    "Placement policy type requires target domain name"
                )
            if p_type == "NonPartiallyPlaceService":
                r.append(
                    ServicePlacementNonPartiallyPlaceServicePolicyDescription()
                )
            elif p_type == "PreferPrimaryDomain":
                r.append(
                    ServicePlacementPreferPrimaryDomainPolicyDescription(p_domain_name)  # noqa: justification, no way to shorten
                )
            elif p_type == "RequireDomain":
                r.append(
                    ServicePlacementRequiredDomainPolicyDescription(p_domain_name)  # noqa: justification, no way to shorten
                )
            elif p_type == "RequireDomainDistribution":
                r.append(
                    ServicePlacementRequireDomainDistributionPolicyDescription(p_domain_name)  # noqa: justification, no way to shorten
                )
        return r
    else:
        return None


def sup_validate_move_cost(move_cost):
    if move_cost not in [None, "Zero", "Low", "Medium", "High"]:
        raise CLIError("Invalid move cost specified")


def sup_stateful_flags(rep_restart_wait=None, quorum_loss_wait=None,
                       standby_replica_keep=None):
    f = 0
    if rep_restart_wait is not None:
        f += 1
    if quorum_loss_wait is not None:
        f += 2
    if standby_replica_keep is not None:
        f += 4
    return f


def sup_service_update_flags(  # pylint: disable=too-many-arguments
        target_rep_size=None, instance_count=None, rep_restart_wait=None,
        quorum_loss_wait=None, standby_rep_keep=None, min_rep_size=None,
        placement_constraints=None, placement_policy=None, correlation=None,
        metrics=None, move_cost=None):
    f = 0
    if (target_rep_size is not None) or (instance_count is not None):
        f += 1
    if rep_restart_wait is not None:
        f += 2
    if quorum_loss_wait is not None:
        f += 4
    if standby_rep_keep is not None:
        f += 8
    if min_rep_size is not None:
        f += 16
    if placement_constraints is not None:
        f += 32
    if placement_policy is not None:
        f += 64
    if correlation is not None:
        f += 128
    if metrics is not None:
        f += 256
    if move_cost is not None:
        f += 512
    return f


def sf_create_service(  # pylint: disable=too-many-arguments, too-many-locals
        app_id, name, service_type, stateful=False, stateless=False,
        singleton_scheme=False, named_scheme=False, int_scheme=False,
        named_scheme_list=None, int_scheme_low=None, int_scheme_high=None,
        int_scheme_count=None, constraints=None, correlated_service=None,
        correlation=None, load_metrics=None, placement_policy_list=None,
        move_cost=None, activation_mode=None, dns_name=None,
        target_replica_set_size=None, min_replica_set_size=None,
        replica_restart_wait=None, quorum_loss_wait=None,
        stand_by_replica_keep=None, no_persisted_state=False,
        instance_count=None, timeout=60):
    """
    Creates the specified Service Fabric service from the description.

    :param str app_id: The identity of the parent application. This is
    typically the full id of the application without the 'fabric:' URI scheme.
    :param str name: Name of the service.
    :param bool stateless: Indicates the service is a stateless service.
    :param bool stateful: Indicates the service is a stateful service.
    :param str service_type: Name of the service type.
    :param bool singleton_scheme: Indicates the service should have a single
    partition or be a non-partitioned service.
    :param bool named_scheme: Indicates the service should have multiple named
    partitions.
    :param list of str named_scheme_list: The list of names to partition the
    service across, if using the named partition scheme.
    :param bool int_scheme: Indicates the service should be uniformly
    partitioned across a range of unsigned integers.
    :param str int_scheme_low: The start of the key integer range, if using an
    uniform integer partition scheme.
    :param str int_scheme_high: The end of the key integer range, if using an
    uniform integer partition scheme.
    :param str int_scheme_count: The number of partitions inside the integer
    key range to create, if using an uniform integer partition scheme.
    :param str constraints: The placement constraints as a string. Placement
    constraints are boolean expressions on node properties and allow for
    restricting a service to particular nodes based on the service
    requirements. For example, to place a service on nodes where NodeType
    is blue specify the following:"NodeColor == blue".
    :param str correlation: Correlate the service with an existing service
    using an alignment affinity. Possible values include: 'Invalid',
    'Affinity', 'AlignedAffinity', 'NonAlignedAffinity'.
    :param str correlated_service: Name of the target service to correlate
    with.
    :param str move_cost: Specifies the move cost for the service. Possible
    values are: 'Zero', 'Low', 'Medium', 'High'.
    :param str activation_mode: The activation mode for the service package.
    Possible values include: 'SharedProcess', 'ExclusiveProcess'.
    :param str dns_name: The DNS name of the service to be created. The Service
    Fabric DNS system service must be enabled for this setting.
    :param int target_replica_set_size: The target replica set size as a
    number. This applies to stateful services only.
    :param int min_replica_set_size: The minimum replica set size as a number.
    This applies to stateful services only.
    :param int replica_restart_wait: The duration, in seconds, between when a
    replica goes down and when a new replica is created. This applies to
    stateful services only.
    :param int quorum_loss_wait: The maximum duration, in seconds, for which a
    partition is allowed to be in a state of quorum loss. This applies to
    stateful services only.
    :param int stand_by_replica_keep: The maximum duration, in seconds,  for
    which StandBy replicas will be maintained before being removed. This
    applies to stateful services only.
    :param bool no_persisted_state: If true, this indicates the service has no
    persistent state stored on the local disk, or it only stores state in
    memory.
    :param int instance_count: The instance count. This applies to stateless
    services only.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value for this
    parameter is 60 seconds.
    """
    from azure.servicefabric.models.stateless_service_description import (
        StatelessServiceDescription
    )
    from azure.servicefabric.models.stateful_service_description import (
        StatefulServiceDescription
    )
    from azure.servicefabric.models.named_partition_scheme_description import (
        NamedPartitionSchemeDescription
    )
    # pylint: disable=line-too-long
    from azure.servicefabric.models.singleton_partition_scheme_description import (  # noqa: justification, no way to shorten
        SingletonPartitionSchemeDescription
    )
    # pylint: disable=line-too-long
    from azure.servicefabric.models.uniform_int64_range_partition_scheme_description import (  # noqa: justification, no way to shorten
        UniformInt64RangePartitionSchemeDescription
    )
    from azure.cli.command_modules.sf._factory import cf_sf_client

    # Validate and parse input

    # stateful or stateless
    if sum([stateful, stateless]) != 1:
        raise CLIError("Specify either stateful or stateless for the "
                       "service type")
    # partition scheme
    if stateful and sum([singleton_scheme, named_scheme, int_scheme]) != 1:
        raise CLIError("Specify exactly one partition scheme")
    if named_scheme and not named_scheme_list:
        raise CLIError("When specifying named partition scheme, must include "
                       "list of names")
    if (int_scheme and
            not all([int_scheme_low, int_scheme_high, int_scheme_count])):
        raise CLIError("Must specify the full integer range and partition "
                       "count when using an uniform integer partition scheme")
    if stateless and any([int_scheme, named_scheme]):
        raise CLIError("Stateless services cannot be partitioned")
    if named_scheme:
        part_schema = NamedPartitionSchemeDescription(len(named_scheme_list),
                                                      named_scheme_list)
    elif int_scheme:
        # pylint: disable=redefined-variable-type
        part_schema = UniformInt64RangePartitionSchemeDescription(
            int_scheme_count,
            int_scheme_low,
            int_scheme_high
        )
    else:
        # pylint: disable=redefined-variable-type
        part_schema = SingletonPartitionSchemeDescription()
    # correlation scheme
    correlation_desc = sup_correlation_scheme(correlated_service,
                                              correlation)
    # load metrics
    load_list = sup_load_metrics(load_metrics)
    # service placement policies
    place_policy = sup_placement_policies(placement_policy_list)
    # default move cost
    sup_validate_move_cost(move_cost)
    # activation mode
    if activation_mode not in [None, "SharedProcess", "ExclusiveProcess"]:
        raise CLIError("Invalid activate mode specified")

    # Stateless service
    if stateful and instance_count:
        raise CLIError("Cannot specify instance count for stateful services")
    if stateless and not instance_count:
        raise CLIError("Must specify instance count for stateless services")
    if stateless:
        svc_desc = StatelessServiceDescription(name, service_type,
                                               part_schema, instance_count,
                                               app_id, None, constraints,
                                               correlation_desc, load_list,
                                               place_policy, move_cost,
                                               bool(move_cost),
                                               activation_mode,
                                               dns_name)

    # Stateful service
    if stateful and not all([target_replica_set_size, min_replica_set_size]):
        raise CLIError("Must specify minimum and replica set size for "
                       "stateful services")
    if stateless and any([target_replica_set_size, min_replica_set_size]):
        raise CLIError("Cannot specify replica set sizes for statless "
                       "services")
    if stateful:
        flags = sup_stateful_flags(replica_restart_wait, quorum_loss_wait,
                                   stand_by_replica_keep)
        # pylint: disable=redefined-variable-type
        svc_desc = StatefulServiceDescription(name, service_type,
                                              part_schema,
                                              target_replica_set_size,
                                              min_replica_set_size,
                                              not no_persisted_state,
                                              app_id, None, constraints,
                                              correlation_desc, load_list,
                                              place_policy, move_cost,
                                              bool(move_cost), activation_mode,
                                              dns_name, flags,
                                              replica_restart_wait,
                                              quorum_loss_wait,
                                              stand_by_replica_keep)

    sf_client = cf_sf_client(None)
    sf_client.create_service(app_id, svc_desc, timeout)


def sf_update_service(service_id,  # pylint: disable=too-many-arguments
                      stateless=False, stateful=False,
                      constraints=None,
                      correlation=None, correlated_service=None,
                      load_metrics=None, placement_policy_list=None,
                      move_cost=None, target_replica_set_size=None,
                      min_replica_set_size=None, replica_restart_wait=None,
                      quorum_loss_wait=None, stand_by_replica_keep=None,
                      instance_count=None, timeout=60):
    """
    Updates the specified service using the given update description.

    :param str service_id: Target service to update. This is typically the full
    id of the service without the 'fabric:' URI scheme.
    :param bool stateless: Indicates the target service is a stateless service.
    :param bool stateful: Indicates the target service is a stateful service.
    :param str constraints: The placement constraints as a string. Placement
    constraints are boolean expressions on node properties and allow for
    restricting a service to particular nodes based on the service
    requirements. For example, to place a service on nodes where NodeType is
    blue specify the following:"NodeColor == blue".
    :param str correlation: Correlate the service with an existing service
    using an alignment affinity. Possible values include: 'Invalid',
    'Affinity', 'AlignedAffinity', 'NonAlignedAffinity'.
    :param str correlated_service: Name of the target service to correlate
    with.
    :param str move_cost: Specifies the move cost for the service. Possible
    values are: 'Zero', 'Low', 'Medium', 'High'.
    :param int target_replica_set_size: The target replica set size as a
    number. This applies to stateful services only.
    :param int min_replica_set_size: The minimum replica set size as a number.
    This applies to stateful services only.
    :param int replica_restart_wait: The duration, in seconds, between when a
    replica goes down and when a new replica is created. This applies to
    stateful services only.
    :param int quorum_loss_wait: The maximum duration, in seconds, for which a
    partition is allowed to be in a state of quorum loss. This applies to
    stateful services only.
    :param int stand_by_replica_keep: The maximum duration, in seconds,  for
    which StandBy replicas will be maintained before being removed. This
    applies to stateful services only.
    :param int instance_count: The instance count. This applies to stateless
    services only.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value for this
    parameter is 60 seconds.
    """
    # TODO a few of these parameters are shared across commands, should be
    # moved to not be bound to individual commands
    # TODO Validation for replica numbers inputs

    # pylint: disable=line-too-long
    from azure.servicefabric.models.stateful_service_update_description import (  # noqa: justification, no way to shorten
        StatefulServiceUpdateDescription
    )
    from azure.servicefabric.models.stateless_service_description import (
        StatelessServiceDescription
    )
    from azure.cli.command_modules.sf._factory import cf_sf_client

    if sum([stateless, stateful]) != 1:
        raise CLIError("Must specify either stateful or stateless, not both")

    corre = sup_correlation_scheme(correlated_service, correlation)
    load_list = sup_load_metrics(load_metrics)
    place_policy = sup_placement_policies(placement_policy_list)

    if move_cost is not None:
        sup_validate_move_cost(move_cost)

    flags = sup_service_update_flags(target_replica_set_size, instance_count,
                                     replica_restart_wait, quorum_loss_wait,
                                     stand_by_replica_keep,
                                     min_replica_set_size, constraints,
                                     place_policy, corre, load_list,
                                     move_cost)

    sud = None
    if stateful:
        if instance_count is not None:
            CLIError("Cannot specify instance count for a stateful service")

        sud = StatefulServiceUpdateDescription(flags, constraints, corre,
                                               load_list, place_policy,
                                               move_cost,
                                               target_replica_set_size,
                                               min_replica_set_size,
                                               replica_restart_wait,
                                               quorum_loss_wait,
                                               stand_by_replica_keep)

    if stateless:
        if target_replica_set_size is not None:
            CLIError(
                "Cannot specify target replica set size for stateless service"
            )
        if min_replica_set_size is not None:
            CLIError(
                "Cannot specify minimum replica set size for stateless service"
            )
        if replica_restart_wait is not None:
            CLIError(
                "Cannot specify replica restart wait duration for stateless "
                "service"
            )
        if quorum_loss_wait is not None:
            CLIError(
                "Cannot specify quorum loss wait duration for stateless "
                "service"
            )
        if stand_by_replica_keep is not None:
            CLIError(
                "Cannot specify standby replica keep duration for stateless "
                "service"
            )
        # pylint: disable=redefined-variable-type
        sud = StatelessServiceDescription(flags, constraints, corre, load_list,
                                          place_policy, move_cost,
                                          instance_count)

    sf_client = cf_sf_client(None)
    sf_client.update_service(service_id, sud, timeout)


def sf_start_chaos(  # pylint: disable=too-many-arguments
        time_to_run="4294967295", max_cluster_stabilization=60,
        max_concurrent_faults=1, disable_move_replica_faults=False,
        wait_time_between_faults=20,
        wait_time_between_iterations=30, warning_as_error=False,
        max_percent_unhealthy_nodes=0,
        max_percent_unhealthy_applications=0,
        application_type_health_policy_map=None, timeout=60):
    """
    If Chaos is not already running in the cluster, starts running Chaos with
    the specified in Chaos parameters.

    :param str time_to_run: Total time (in seconds) for which Chaos will run
    before automatically stopping. The maximum allowed value is 4,294,967,295
    (System.UInt32.MaxValue).
    :param long max_cluster_stabilization: The maximum amount of time to wait
    for all cluster entities to become stable and healthy.
    :param long max_concurrent_faults: The maximum number of concurrent faults
    induced per iteration.
    :param bool disable_move_replica_faults: Disables the move primary and move
    secondary faults.
    :param long wait_time_between_faults: Wait time (in seconds) between
    consecutive faults within a single iteration.
    :param long wait_time_between_iterations: Time-separation (in seconds)
    between two consecutive iterations of Chaos.
    :param bool warning_as_error: When evaluating cluster health during
    Chaos, treat warnings with the same severity as errors.
    :param int max_percent_unhealthy_nodes: When evaluating cluster health
    during Chaos, the maximum allowed percentage of unhealthy nodes before
    reporting an error.
    :param int max_percent_unhealthy_applications: When evaluating cluster
    health during Chaos, the maximum allowed percentage of unhealthy
    applications before reporting an error.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value for this
    parameter is 60 seconds.
    """
    # pylint: disable=line-too-long
    from azure.servicefabric.models.application_type_health_policy_map_item import (  # noqa: justification, no way to shorten
        ApplicationTypeHealthPolicyMapItem
    )
    from azure.servicefabric.models.chaos_parameters import ChaosParameters
    from azure.servicefabric.models.cluster_health_policy import (
        ClusterHealthPolicy
    )
    from azure.cli.command_modules.sf._factory import cf_sf_client

    health_map = None
    if application_type_health_policy_map:
        health_map = []
        for m in application_type_health_policy_map:
            name = m.get("key", None)
            percent_unhealthy = m.get("value", None)
            if name is None:
                raise CLIError(
                    "Cannot find application type health policy map name"
                )
            if percent_unhealthy is None:
                raise CLIError(
                    "Cannot find application type health policy map unhealthy "
                    "percent"
                )
            r = ApplicationTypeHealthPolicyMapItem(name, percent_unhealthy)
            health_map.append(r)

    health_policy = ClusterHealthPolicy(warning_as_error,
                                        max_percent_unhealthy_nodes,
                                        max_percent_unhealthy_applications,
                                        health_map)

    # Does not support Chaos Context currently
    chaos_params = ChaosParameters(time_to_run, max_cluster_stabilization,
                                   max_concurrent_faults,
                                   not disable_move_replica_faults,
                                   wait_time_between_faults,
                                   wait_time_between_iterations,
                                   health_policy,
                                   None)

    sf_client = cf_sf_client(None)
    sf_client.start_chaos(chaos_params, timeout)


def sf_report_app_health(application_id,  # pylint: disable=too-many-arguments
                         source_id, health_property,
                         health_state, ttl=None, description=None,
                         sequence_number=None, remove_when_expired=None,
                         timeout=60):
    """
    Sends a health report on the Service Fabric application.

    Reports health state of the specified Service Fabric application. The
    report must contain the information about the source of the health report
    and property on which it is reported. The report is sent to a Service
    Fabric gateway Application, which forwards to the health store. The report
    may be accepted by the gateway, but rejected by the health store after
    extra validation. For example, the health store may reject the report
    because of an invalid parameter, like a stale sequence number. To see
    whether the report was applied in the health store, check that the report
    appears in the HealthEvents section.

    :param str application_id: The identity of the application. This is
    typically the full name of the application without the 'fabric:' URI
    scheme.
    :param str source_id: The source name which identifies the
    client/watchdog/system component which generated the health information.
    :param str health_property: The property of the health information. An
    entity can have health reports for different properties. The property is a
    string and not a fixed enumeration to allow the reporter flexibility to
    categorize the state condition that triggers the report. For example, a
    reporter with SourceId "LocalWatchdog" can monitor the state of the
    available disk on a node, so it can report "AvailableDisk" property on
    that node. The same reporter can monitor the node connectivity, so it can
    report a property "Connectivity" on the same node. In the health store,
    these reports are treated as separate health events for the specified node.
    Together with the SourceId, the property uniquely identifies the health
    information.
    :param str health_state: Possible values include: 'Invalid', 'Ok',
    'Warning', 'Error', 'Unknown'
    :param int ttl: The duration, in milliseconds, for which this health report
    is valid. When clients report periodically, they should send reports with
    higher frequency than time to live. If not specified, time to live defaults
    to infinite value.
    :param str sequence_number: The sequence number for this health report as a
    numeric string. The report sequence number is used by the health store to
    detect stale reports. If not specified, a sequence number is auto-generated
    by the health client when a report is added.
    :param str description: The description of the health information. It
    represents free text used to add human readable information about the
    report. The maximum string length for the description is 4096 characters.
    If the provided string is longer, it will be automatically truncated.
    When truncated, the last characters of the description contain a marker
    "[Truncated]", and total string size is 4096 characters. The presence of
    the marker indicates to users that truncation occurred. Note that when
    truncated, the description has less than 4096 characters from the original
    string.
    :param bool remove_when_expired: Value that indicates whether the report is
    removed from health store when it expires. If set to true, the report is
    removed from the health store after it expires. If set to false, the report
    is treated as an error when expired. The value of this property is false by
    default. When clients report periodically, they should set this value to
    false (default). This way, is the reporter has issues (eg. deadlock) and
    can't report, the entity is evaluated at error when the health report
    expires. This flags the entity as being in Error health state.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value
    for this parameter is 60 seconds.
    """

    from azure.servicefabric.models.health_information import HealthInformation
    from azure.cli.command_modules.sf._factory import cf_sf_client

    info = HealthInformation(source_id, health_property, health_state, ttl,
                             description, sequence_number, remove_when_expired)

    sf_client = cf_sf_client(None)
    sf_client.report_application_health(application_id, info, timeout)


def sf_report_svc_health(service_id,  # pylint: disable=too-many-arguments
                         source_id, health_property, health_state,
                         ttl=None, description=None, sequence_number=None,
                         remove_when_expired=None, timeout=60):
    """
    Sends a health report on the Service Fabric service.

    Reports health state of the specified Service Fabric service. The
    report must contain the information about the source of the health
    report and property on which it is reported.
    The report is sent to a Service Fabric gateway Service, which forwards
    to the health store.
    The report may be accepted by the gateway, but rejected by the health
    store after extra validation.
    For example, the health store may reject the report because of an
    invalid parameter, like a stale sequence number.
    To see whether the report was applied in the health store, run
    GetServiceHealth and check that the report appears in the
    HealthEvents section.

    :param str service_id: The identity of the service. This is typically the
    full name of the service without the 'fabric:' URI scheme.
    :param str source_id: The source name which identifies the
    client/watchdog/system component which generated the health information.
    :param str health_property: The property of the health information. An
    entity can have health reports for different properties. The property is a
    string and not a fixed enumeration to allow the reporter flexibility to
    categorize the state condition that triggers the report. For example, a
    reporter with SourceId "LocalWatchdog" can monitor the state of the
    available disk on a node, so it can report "AvailableDisk" property on
    that node. The same reporter can monitor the node connectivity, so it can
    report a property "Connectivity" on the same node. In the health store,
    these reports are treated as separate health events for the specified node.
    Together with the SourceId, the property uniquely identifies the health
    information.
    :param str health_state: Possible values include: 'Invalid', 'Ok',
    'Warning', 'Error', 'Unknown'
    :param int ttl: The duration, in milliseconds, for which this health report
    is valid. When clients report periodically, they should send reports with
    higher frequency than time to live. If not specified, time to live defaults
    to infinite value.
    :param str description: The description of the health information. It
    represents free text used to add human readable information about the
    report. The maximum string length for the description is 4096 characters.
    If the provided string is longer, it will be automatically truncated.
    When truncated, the last characters of the description contain a marker
    "[Truncated]", and total string size is 4096 characters. The presence of
    the marker indicates to users that truncation occurred. Note that when
    truncated, the description has less than 4096 characters from the original
    string.
    :param str sequence_number: The sequence number for this health report as a
    numeric string. The report sequence number is used by the health store to
    detect stale reports. If not specified, a sequence number is auto-generated
    by the health client when a report is added.
    :param bool remove_when_expired: Value that indicates whether the report is
    removed from health store when it expires. If set to true, the report is
    removed from the health store after it expires. If set to false, the report
    is treated as an error when expired. The value of this property is false by
    default. When clients report periodically, they should set this value to
    false (default). This way, is the reporter has issues (eg. deadlock) and
    can't report, the entity is evaluated at error when the health report
    expires. This flags the entity as being in Error health state.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value
    for this parameter is 60 seconds.
    """

    # TODO Move common HealthInformation params to _params

    from azure.servicefabric.models.health_information import HealthInformation
    from azure.cli.command_modules.sf._factory import cf_sf_client

    info = HealthInformation(source_id, health_property, health_state, ttl,
                             description, sequence_number, remove_when_expired)

    sf_client = cf_sf_client(None)
    sf_client.report_service_health(service_id, info, timeout)


def sf_report_partition_health(  # pylint: disable=too-many-arguments
        partition_id, source_id, health_property, health_state, ttl=None,
        description=None, sequence_number=None, remove_when_expired=None,
        timeout=60):
    """
    Sends a health report on the Service Fabric partition.

    Reports health state of the specified Service Fabric partition. The
    report must contain the information about the source of the health
    report and property on which it is reported.
    The report is sent to a Service Fabric gateway Partition, which
    forwards to the health store.
    The report may be accepted by the gateway, but rejected by the health
    store after extra validation.
    For example, the health store may reject the report because of an
    invalid parameter, like a stale sequence number.
    To see whether the report was applied in the health store, run
    GetPartitionHealth and check that the report appears in the
    HealthEvents section.

    :param str partition_id: The identity of the partition.
    :param str source_id: The source name which identifies the
    client/watchdog/system component which generated the health information.
    :param str health_property: The property of the health information. An
    entity can have health reports for different properties. The property is a
    string and not a fixed enumeration to allow the reporter flexibility to
    categorize the state condition that triggers the report. For example, a
    reporter with SourceId "LocalWatchdog" can monitor the state of the
    available disk on a node, so it can report "AvailableDisk" property on
    that node. The same reporter can monitor the node connectivity, so it can
    report a property "Connectivity" on the same node. In the health store,
    these reports are treated as separate health events for the specified node.
    Together with the SourceId, the property uniquely identifies the health
    information.
    :param str health_state: Possible values include: 'Invalid', 'Ok',
    'Warning', 'Error', 'Unknown'
    :param int ttl: The duration, in milliseconds, for which this health report
    is valid. When clients report periodically, they should send reports with
    higher frequency than time to live. If not specified, time to live defaults
    to infinite value.
    :param str description: The description of the health information. It
    represents free text used to add human readable information about the
    report. The maximum string length for the description is 4096 characters.
    If the provided string is longer, it will be automatically truncated.
    When truncated, the last characters of the description contain a marker
    "[Truncated]", and total string size is 4096 characters. The presence of
    the marker indicates to users that truncation occurred. Note that when
    truncated, the description has less than 4096 characters from the original
    string.
    :param str sequence_number: The sequence number for this health report as a
    numeric string. The report sequence number is used by the health store to
    detect stale reports. If not specified, a sequence number is auto-generated
    by the health client when a report is added.
    :param bool remove_when_expired: Value that indicates whether the report is
    removed from health store when it expires. If set to true, the report is
    removed from the health store after it expires. If set to false, the report
    is treated as an error when expired. The value of this property is false by
    default. When clients report periodically, they should set this value to
    false (default). This way, is the reporter has issues (eg. deadlock) and
    can't report, the entity is evaluated at error when the health report
    expires. This flags the entity as being in Error health state.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value
    for this parameter is 60 seconds.
    """

    # TODO Move common HealthInformation params to _params

    from azure.servicefabric.models.health_information import HealthInformation
    from azure.cli.command_modules.sf._factory import cf_sf_client

    info = HealthInformation(source_id, health_property, health_state, ttl,
                             description, sequence_number, remove_when_expired)

    sf_client = cf_sf_client(None)
    sf_client.report_partition_health(partition_id, info, timeout)


def sf_report_replica_health(  # pylint: disable=too-many-arguments
        partition_id, replica_id, source_id, health_state, health_property,
        service_kind="Stateful", ttl=None, description=None,
        sequence_number=None, remove_when_expired=None, timeout=60):
    """
    Sends a health report on the Service Fabric replica.

    Reports health state of the specified Service Fabric replica. The
    report must contain the information about the source of the health
    report and property on which it is reported.
    The report is sent to a Service Fabric gateway Replica, which forwards
    to the health store.
    The report may be accepted by the gateway, but rejected by the health
    store after extra validation.
    For example, the health store may reject the report because of an
    invalid parameter, like a stale sequence number.
    To see whether the report was applied in the health store, run
    GetReplicaHealth and check that the report appears in the
    HealthEvents section.

    :param str partition_id: The identity of the partition.
    :param str replica_id: The identifier of the replica.
    :param str source_id: The source name which identifies the
    client/watchdog/system component which generated the health information.
    :param str health_property: The property of the health information. An
    entity can have health reports for different properties. The property is a
    string and not a fixed enumeration to allow the reporter flexibility to
    categorize the state condition that triggers the report. For example, a
    reporter with SourceId "LocalWatchdog" can monitor the state of the
    available disk on a node, so it can report "AvailableDisk" property on
    that node. The same reporter can monitor the node connectivity, so it can
    report a property "Connectivity" on the same node. In the health store,
    these reports are treated as separate health events for the specified node.
    Together with the SourceId, the property uniquely identifies the health
    information.
    :param str health_state: Possible values include: 'Invalid', 'Ok',
    'Warning', 'Error', 'Unknown'
    :param str service_kind: The kind of service replica (Stateless or
    Stateful) for which the health is being reported. Following are the
    possible values.
    - Stateless - Does not use Service Fabric to make its state highly
    available or reliable. The value is 1
    - Stateful - Uses Service Fabric to make its state or part of its
    state highly available and reliable. The value is 2.
    :param int ttl: The duration, in milliseconds, for which this health report
    is valid. When clients report periodically, they should send reports with
    higher frequency than time to live. If not specified, time to live defaults
    to infinite value.
    :param str description: The description of the health information. It
    represents free text used to add human readable information about the
    report. The maximum string length for the description is 4096 characters.
    If the provided string is longer, it will be automatically truncated.
    When truncated, the last characters of the description contain a marker
    "[Truncated]", and total string size is 4096 characters. The presence of
    the marker indicates to users that truncation occurred. Note that when
    truncated, the description has less than 4096 characters from the original
    string.
    :param str sequence_number: The sequence number for this health report as a
    numeric string. The report sequence number is used by the health store to
    detect stale reports. If not specified, a sequence number is auto-generated
    by the health client when a report is added.
    :param bool remove_when_expired: Value that indicates whether the report is
    removed from health store when it expires. If set to true, the report is
    removed from the health store after it expires. If set to false, the report
    is treated as an error when expired. The value of this property is false by
    default. When clients report periodically, they should set this value to
    false (default). This way, is the reporter has issues (eg. deadlock) and
    can't report, the entity is evaluated at error when the health report
    expires. This flags the entity as being in Error health state.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value
    for this parameter is 60 seconds.
    """

    # TODO Move common HealthInformation params to _params

    from azure.servicefabric.models.health_information import HealthInformation
    from azure.cli.command_modules.sf._factory import cf_sf_client

    info = HealthInformation(source_id, health_property, health_state, ttl,
                             description, sequence_number, remove_when_expired)

    sf_client = cf_sf_client(None)
    sf_client.report_replica_health(partition_id, replica_id, info,
                                    service_kind, timeout)


def sf_report_node_health(node_name,  # pylint: disable=too-many-arguments
                          source_id, health_property, health_state,
                          ttl=None, description=None, sequence_number=None,
                          remove_when_expired=None, timeout=60):
    """
    Sends a health report on the Service Fabric node.

    Reports health state of the specified Service Fabric node. The report
    must contain the information about the source of the health report
    and property on which it is reported.
    The report is sent to a Service Fabric gateway node, which forwards to
    the health store.
    The report may be accepted by the gateway, but rejected by the health
    store after extra validation.
    For example, the health store may reject the report because of an
    invalid parameter, like a stale sequence number.
    To see whether the report was applied in the health store, run
    GetNodeHealth and check that the report appears in the HealthEvents
    section.

    :param str node_name: The name of the node.
    :param str source_id: The source name which identifies the
    client/watchdog/system component which generated the health information.
    :param str health_property: The property of the health information. An
    entity can have health reports for different properties. The property is a
    string and not a fixed enumeration to allow the reporter flexibility to
    categorize the state condition that triggers the report. For example, a
    reporter with SourceId "LocalWatchdog" can monitor the state of the
    available disk on a node, so it can report "AvailableDisk" property on
    that node. The same reporter can monitor the node connectivity, so it can
    report a property "Connectivity" on the same node. In the health store,
    these reports are treated as separate health events for the specified node.
    Together with the SourceId, the property uniquely identifies the health
    information.
    :param str health_state: Possible values include: 'Invalid', 'Ok',
    'Warning', 'Error', 'Unknown'
    :param int ttl: The duration, in milliseconds, for which this health report
    is valid. When clients report periodically, they should send reports with
    higher frequency than time to live. If not specified, time to live defaults
    to infinite value.
    :param str description: The description of the health information. It
    represents free text used to add human readable information about the
    report. The maximum string length for the description is 4096 characters.
    If the provided string is longer, it will be automatically truncated.
    When truncated, the last characters of the description contain a marker
    "[Truncated]", and total string size is 4096 characters. The presence of
    the marker indicates to users that truncation occurred. Note that when
    truncated, the description has less than 4096 characters from the original
    string.
    :param str sequence_number: The sequence number for this health report as a
    numeric string. The report sequence number is used by the health store to
    detect stale reports. If not specified, a sequence number is auto-generated
    by the health client when a report is added.
    :param bool remove_when_expired: Value that indicates whether the report is
    removed from health store when it expires. If set to true, the report is
    removed from the health store after it expires. If set to false, the report
    is treated as an error when expired. The value of this property is false by
    default. When clients report periodically, they should set this value to
    false (default). This way, is the reporter has issues (eg. deadlock) and
    can't report, the entity is evaluated at error when the health report
    expires. This flags the entity as being in Error health state.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing to
    wait for the requested operation to complete. The default value
    for this parameter is 60 seconds.
    """

    # TODO Move common HealthInformation params to _params

    from azure.servicefabric.models.health_information import HealthInformation
    from azure.cli.command_modules.sf._factory import cf_sf_client

    info = HealthInformation(source_id, health_property, health_state, ttl,
                             description, sequence_number, remove_when_expired)

    sf_client = cf_sf_client(None)
    sf_client.report_node_health(node_name, info, timeout)


def sf_service_package_upload(node_name,  # pylint: disable=too-many-arguments
                              service_manifest_name,
                              application_type_name, application_type_version,
                              share_policy=None, timeout=60):
    """
    Downloads packages associated with specified service manifest to the image
    cache on specified node.

    :param str node_name: The name of the node.
    :param str service_manifest_name: The name of service manifest associated
    with the packages that will be downloaded.
    :param str application_type_name: The name of the application manifest for
    the corresponding requested service manifest.
    :param str application_type_version: The version of the application
    manifest for the corresponding requested service manifest.
    :param long timeout: The server timeout for performing the operation in
    seconds. This specifies the time duration that the client is willing
    to wait for the requested operation to complete. The default value
    for this parameter is 60 seconds.
    """
    # pylint: disable=line-too-long
    from azure.servicefabric.models.deploy_service_package_to_node_description import (  # noqa: justification, no way to shorten
        DeployServicePackageToNodeDescription
    )
    from azure.servicefabric.models.package_sharing_policy_info import (
        PackageSharingPolicyInfo
    )
    from azure.cli.command_modules.sf._factory import cf_sf_client

    list_psps = None
    if share_policy:
        list_psps = []
        for p in share_policy:
            policy_name = p.get("name", None)
            if policy_name is None:
                raise CLIError("Could not find name of sharing policy element")
            policy_scope = p.get("scope", None)
            if policy_scope not in ["None", "All", "Code", "Config", "Data"]:
                raise CLIError("Invalid policy scope specified")
            list_psps.append(PackageSharingPolicyInfo(policy_name,
                                                      policy_scope))

    desc = DeployServicePackageToNodeDescription(service_manifest_name,
                                                 application_type_name,
                                                 application_type_version,
                                                 node_name, list_psps)
    sf_client = cf_sf_client(None)
    sf_client.deployed_service_package_to_node(node_name, desc, timeout)
