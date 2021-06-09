# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from .scenario_mixin import add_tags


def _add_paramter_if_needed(command, paramter_name, parameter_value):
    if parameter_value is not None:
        return f'{command} --{paramter_name} {parameter_value}'

    return command


# pylint: disable=too-many-public-methods
class CdnAfdScenarioMixin:
    def afd_profile_create_cmd(self, resource_group_name, profile_name, tags=None, checks=None, options=None,
                               sku="Standard_AzureFrontDoor", expect_failure=False):
        command = f'afd profile create -g {resource_group_name} --profile-name {profile_name} --sku {sku}'
        if tags:
            command = command + ' --tags {}'.format(tags)
        if options:
            command = command + ' ' + options

        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_profile_update_cmd(self, group, name, tags=None, checks=None):
        command = 'afd profile update -g {} --profile-name {}'.format(group, name)
        if tags:
            command = command + ' --tags {}'.format(tags)
        return self.cmd(command, checks)

    def afd_profile_list_cmd(self, group, checks=None):
        command = 'afd profile list -g {}'.format(group)
        return self.cmd(command, checks)

    def afd_profile_show_cmd(self, group, name, checks=None):
        command = f'afd profile show -g {group} --profile-name {name}'
        return self.cmd(command, checks)

    def afd_profile_delete_cmd(self, group, name, checks=None):
        command = 'afd profile delete -g {} --profile-name {}'.format(group, name)
        return self.cmd(command, checks)

    def afd_endpoint_create_cmd(self, resource_group_name, profile_name, endpoint_name,
                                origin_response_timeout_seconds, enabled_state,
                                tags=None, checks=None):
        cmd = f'afd endpoint create -g {resource_group_name} --endpoint-name {endpoint_name} ' \
              f'--profile-name {profile_name} --origin-response-timeout-seconds {origin_response_timeout_seconds} ' \
              f'--enabled-state {enabled_state}'

        if tags:
            cmd = add_tags(cmd, tags)

        return self.cmd(cmd, checks)

    def afd_endpoint_update_cmd(self, resource_group_name, profile_name, endpoint_name,
                                origin_response_timeout_seconds=None,
                                enabled_state=None, tags=None, checks=None, options=None):
        command = f'afd endpoint update -g {resource_group_name} --endpoint-name {endpoint_name} ' \
                  f'--profile-name {profile_name}'
        if tags:
            command = add_tags(command, tags)

        command = _add_paramter_if_needed(command, "origin-response-timeout-seconds", origin_response_timeout_seconds)
        command = _add_paramter_if_needed(command, "enabled-state", enabled_state)

        if options:
            command = command + ' ' + options

        return self.cmd(command, checks)

    def afd_endpoint_show_cmd(self, resource_group_name, profile_name, endpoint_name, checks=None, options=None):
        command = f'afd endpoint show -g {resource_group_name} --endpoint-name {endpoint_name} ' \
                  f'--profile-name {profile_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_endpoint_purge_cmd(self, resource_group_name, endpoint_name, profile_name, content_paths,
                               domains=None, checks=None):
        command = f'afd endpoint purge -g {resource_group_name} --endpoint-name {endpoint_name} ' \
                  f'--profile-name {profile_name} --content-paths {" ".join(content_paths)}'

        if domains:
            command = command + ' ' + f'--domains {" ".join(domains)}'
        return self.cmd(command, checks)

    def afd_rule_set_add_cmd(self, resource_group_name, rule_set_name, profile_name, checks=None):
        command = f'az afd rule-set create -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name}'

        return self.cmd(command, checks)

    def afd_rule_set_delete_cmd(self, resource_group_name, rule_set_name, profile_name, checks=None):
        command = f'az afd rule-set delete -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --yes'

        return self.cmd(command, checks)

    def afd_rule_set_list_cmd(self, resource_group_name, profile_name, checks=None, expect_failure=False):
        command = f'az afd rule-set list -g {resource_group_name} --profile-name {profile_name}'

        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_rule_set_show_cmd(self, resource_group_name, rule_set_name, profile_name, checks=None,
                              expect_failure=False):
        command = f'az afd rule-set show -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name}'

        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_rule_list_cmd(self, resource_group_name, rule_set_name, profile_name, checks=None, expect_failure=False):
        command = f'az afd rule list -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name}'

        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_rule_show_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, checks=None):
        command = f'az afd rule show -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name}'

        return self.cmd(command, checks)

    def afd_rule_add_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, options=None, checks=None):
        command = f'az afd rule create -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name}'

        if options:
            command = command + ' ' + options

        return self.cmd(command, checks)

    def afd_rule_add_condition_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, checks=None,
                                   options=None):
        command = f'afd rule condition add -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_rule_add_action_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, checks=None,
                                options=None):
        command = f'afd rule action add -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_rule_delete_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, checks=None,
                            options=None):
        command = f'afd rule delete -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name} --yes'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_rule_remove_condition_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, index,
                                      checks=None, options=None):
        command = f'afd rule condition remove -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name} --index {index}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_rule_remove_action_cmd(self, resource_group_name, rule_set_name, rule_name, profile_name, index,
                                   checks=None, options=None):
        command = f'afd rule action remove -g {resource_group_name} --rule-set-name {rule_set_name} ' \
                  f'--profile-name {profile_name} --rule-name {rule_name} --index {index}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_endpoint_list_cmd(self, resource_group_name, profile_name, checks=None, expect_failure=False):
        command = f'afd endpoint list -g {resource_group_name} --profile-name {profile_name}'
        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_endpoint_delete_cmd(self, resource_group_name, endpoint_name, profile_name, checks=None):
        command = f'afd endpoint delete -g {resource_group_name} --endpoint-name {endpoint_name} ' \
                  f'--profile-name {profile_name} --yes'
        return self.cmd(command, checks)

    def afd_secret_create_cmd(self, resource_group_name, profile_name, secret_name, secret_source,
                              use_latest_version, secret_version, checks=None):
        cmd = f'afd secret create -g {resource_group_name} --profile-name {profile_name} ' \
              f'--secret-name {secret_name} --secret-source {secret_source} --use-latest-version {use_latest_version}'

        if secret_version:
            cmd += f' --secret-version={secret_version}'

        return self.cmd(cmd, checks)

    def afd_secret_update_cmd(self, resource_group_name, profile_name, secret_name, secret_source=None,
                              use_latest_version=None, secret_version=None, checks=None):
        cmd = f'afd secret update -g {resource_group_name} --profile-name {profile_name} ' \
              f'--secret-name {secret_name}'

        if secret_version:
            cmd += f' --secret-version={secret_version}'

        if use_latest_version:
            cmd += f' --use-latest-version {use_latest_version}'

        if secret_source:
            cmd += f' --secret-source {secret_source}'

        return self.cmd(cmd, checks)

    def afd_secret_list_cmd(self, resource_group_name, profile_name, checks=None, expect_failure=False):
        command = f'afd secret list -g {resource_group_name} --profile-name {profile_name}'
        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_secret_show_cmd(self, resource_group_name, profile_name, secret_name, checks=None):
        command = f'afd secret show -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--secret-name {secret_name}'
        return self.cmd(command, checks)

    def afd_secret_delete_cmd(self, resource_group_name, profile_name, secret_name, checks=None):
        command = f'afd secret delete -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--secret-name {secret_name} --yes'
        return self.cmd(command, checks)

    def afd_custom_domain_create_cmd(self, resource_group_name, profile_name, custom_domain_name,
                                     host_name, certificate_type, minimum_tls_version,
                                     azure_dns_zone=None, secret=None, checks=None):
        cmd = f'afd custom-domain create -g {resource_group_name} --profile-name {profile_name} ' \
              f'--custom-domain-name {custom_domain_name} --host-name {host_name} ' \
              f'--certificate-type {certificate_type} --minimum-tls-version {minimum_tls_version}'

        if azure_dns_zone:
            cmd += f' --azure-dns-zone={azure_dns_zone}'
        if secret:
            cmd += f' --secret={secret}'

        return self.cmd(cmd, checks)

    def afd_custom_domain_update_cmd(self, resource_group_name, profile_name, custom_domain_name,
                                     certificate_type=None, minimum_tls_version=None,
                                     azure_dns_zone=None, secret=None, checks=None):
        cmd = f'afd custom-domain update -g {resource_group_name} --profile-name {profile_name} ' \
              f'--custom-domain-name {custom_domain_name} ' \
              f'--certificate-type {certificate_type} --minimum-tls-version {minimum_tls_version}'

        if azure_dns_zone:
            cmd += f' --azure-dns-zone={azure_dns_zone}'
        if secret:
            cmd += f' --secret={secret}'

        return self.cmd(cmd, checks)

    def afd_custom_domain_list_cmd(self, resource_group_name, profile_name, checks=None, expect_failure=False):
        command = f'afd custom-domain list -g {resource_group_name} --profile-name {profile_name}'
        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_custom_domain_show_cmd(self, resource_group_name, profile_name, custom_domain_name, checks=None):
        command = f'afd custom-domain show -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--custom-domain-name {custom_domain_name}'
        return self.cmd(command, checks)

    def afd_custom_domain_delete_cmd(self, resource_group_name, profile_name, custom_domain_name, checks=None):
        command = f'afd custom-domain delete -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--custom-domain-name {custom_domain_name} --yes'
        return self.cmd(command, checks)

    def afd_security_policy_create_cmd(self, resource_group_name, profile_name, security_policy_name, domains,
                                       waf_policy, checks=None):
        cmd = f'afd security-policy create -g {resource_group_name} --profile-name {profile_name} ' \
              f'--security-policy-name {security_policy_name} --waf-policy {waf_policy}'
        if domains:
            cmd += " --domains " + " ".join(domains)

        return self.cmd(cmd, checks)

    def afd_security_policy_update_cmd(self, resource_group_name, profile_name, security_policy_name, domains=None,
                                       waf_policy=None, checks=None):
        cmd = f'afd security-policy update -g {resource_group_name} --profile-name {profile_name} ' \
              f'--security-policy-name {security_policy_name}'
        if domains:
            cmd += " --domains " + " ".join(domains)

        if waf_policy:
            cmd += f" --waf-policy {waf_policy}"

        return self.cmd(cmd, checks)

    def afd_security_policy_list_cmd(self, resource_group_name, profile_name, checks=None, expect_failure=False):
        command = f'afd security-policy list -g {resource_group_name} --profile-name {profile_name}'
        return self.cmd(command, checks, expect_failure=expect_failure)

    def afd_security_policy_show_cmd(self, resource_group_name, profile_name, security_policy_name, checks=None):
        command = f'afd security-policy show -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--security-policy-name {security_policy_name}'
        return self.cmd(command, checks)

    def afd_security_policy_delete_cmd(self, resource_group_name, profile_name, security_policy_name, checks=None):
        command = f'afd security-policy delete -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--security-policy-name {security_policy_name} --yes'
        return self.cmd(command, checks)

    def afd_origin_group_list_cmd(self, resource_group_name, profile_name, checks=None):
        command = f'afd origin-group list -g {resource_group_name} --profile-name {profile_name}'
        return self.cmd(command, checks)

    def afd_origin_group_show_cmd(self, resource_group_name, profile_name, origin_group_name, checks=None):
        command = f'afd origin-group show -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name}'
        return self.cmd(command, checks)

    def afd_origin_group_delete_cmd(self, resource_group_name, profile_name, origin_group_name, checks=None):
        command = f'afd origin-group delete -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name} --yes'
        return self.cmd(command, checks)

    def afd_origin_group_create_cmd(self, resource_group_name, profile_name, origin_group_name,
                                    options=None, checks=None):
        command = f'afd origin-group create -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_origin_group_update_cmd(self, resource_group_name, profile_name, origin_group_name,
                                    options=None, checks=None):
        command = f'afd origin-group update -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_origin_list_cmd(self, resource_group_name, profile_name, origin_group_name, checks=None):
        command = f'afd origin list -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name}'
        return self.cmd(command, checks)

    def afd_origin_show_cmd(self, resource_group_name, profile_name, origin_group_name, origin_name, checks=None):
        command = f'afd origin show -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name} --origin-name {origin_name}'
        return self.cmd(command, checks)

    def afd_origin_delete_cmd(self, resource_group_name, profile_name, origin_group_name, origin_name, checks=None):
        command = f'afd origin delete -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name} --origin-name {origin_name} --yes'
        return self.cmd(command, checks)

    def afd_origin_create_cmd(self, resource_group_name, profile_name, origin_group_name, origin_name,
                              options=None, checks=None):
        command = f'afd origin create -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name} --origin-name {origin_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_origin_update_cmd(self, resource_group_name, profile_name, origin_group_name, origin_name,
                              options=None, checks=None):
        command = f'afd origin update -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--origin-group-name {origin_group_name} --origin-name {origin_name}'

        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_route_list_cmd(self, resource_group_name, profile_name, endpoint_name, checks=None):
        command = f'afd route list -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--endpoint-name {endpoint_name}'
        return self.cmd(command, checks)

    def afd_route_show_cmd(self, resource_group_name, profile_name, endpoint_name, route_name, checks=None):
        command = f'afd route show -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--endpoint-name {endpoint_name} --route-name {route_name}'
        return self.cmd(command, checks)

    def afd_route_delete_cmd(self, resource_group_name, profile_name, endpoint_name, route_name, checks=None):
        command = f'afd route delete -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--endpoint-name {endpoint_name} --route-name {route_name} --yes'
        return self.cmd(command, checks)

    def afd_route_create_cmd(self, resource_group_name, profile_name, endpoint_name, route_name,
                             options=None, checks=None):
        command = f'afd route create -g {resource_group_name} --profile-name {profile_name} ' \
                  f'--endpoint-name {endpoint_name} --route-name {route_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def afd_route_update_cmd(self, resource_group_name, profile_name, endpoint_name, route_name,
                             options=None, checks=None):
        command = f'afd route update -g {resource_group_name} --profile-name {profile_name}' \
                  f' --route-name {route_name} --endpoint-name {endpoint_name}'
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def is_playback_mode(self):
        return self.get_subscription_id() == '00000000-0000-0000-0000-000000000000'
