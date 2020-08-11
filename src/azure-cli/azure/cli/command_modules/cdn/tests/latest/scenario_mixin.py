# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def add_tags(command, tags):
    return command + ' --tags {}'.format(tags)


# pylint: disable=too-many-public-methods
class CdnScenarioMixin:
    def profile_create_cmd(self, group, name, tags=None, checks=None, options=None, sku=None):
        command = 'cdn profile create -g {} -n {}'.format(group, name)
        if tags:
            command = command + ' --tags {}'.format(tags)
        if options:
            command = command + ' ' + options
        if sku:
            command = command + ' --sku {}'.format(sku)
        return self.cmd(command, checks)

    def profile_update_cmd(self, group, name, tags=None, checks=None):
        command = 'cdn profile update -g {} -n {}'.format(group, name)
        if tags:
            command = command + ' --tags {}'.format(tags)
        return self.cmd(command, checks)

    def profile_list_cmd(self, group, checks=None):
        command = 'cdn profile list -g {}'.format(group)
        return self.cmd(command, checks)

    def profile_show_cmd(self, group, name, checks=None):
        command = f'cdn profile show -g {group} -n {name}'
        return self.cmd(command, checks)

    def profile_delete_cmd(self, group, name, checks=None):
        command = 'cdn profile delete -g {} -n {}'.format(group, name)
        return self.cmd(command, checks)

    def endpoint_create_cmd(self, group, name, profile_name, origin, private_link_id=None, private_link_location=None,
                            private_link_message=None, tags=None, checks=None):
        cmd = f'cdn endpoint create -g {group} -n {name} --profile-name {profile_name} --origin {origin} 80 443 '

        if private_link_id:
            cmd += f' \'{private_link_id}\''
        if private_link_location:
            cmd += f' \'{private_link_location}\''
        if private_link_message:
            cmd += f' \'{private_link_message}\''
        if tags:
            cmd = add_tags(cmd, tags)

        return self.cmd(cmd, checks)

    def endpoint_update_cmd(self, group, name, profile_name, tags=None, checks=None, options=None):
        command = 'cdn endpoint update -g {} -n {} --profile-name {}'.format(group,
                                                                             name,
                                                                             profile_name)
        if tags:
            command = add_tags(command, tags)

        if options:
            command = command + ' ' + options

        return self.cmd(command, checks)

    def endpoint_start_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint start -g {} -n {} --profile-name {}'.format(group,
                                                                            name,
                                                                            profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_stop_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint stop -g {} -n {} --profile-name {}'.format(group,
                                                                           name,
                                                                           profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_show_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint show -g {} -n {} --profile-name {}'.format(group,
                                                                           name,
                                                                           profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_load_cmd(self, group, name, profile_name, content_paths, checks=None):
        msg = 'cdn endpoint load -g {} -n {} --profile-name {} --content-paths {}'
        command = msg.format(group,
                             name,
                             profile_name,
                             ' '.join(content_paths))
        return self.cmd(command, checks)

    def endpoint_add_rule_cmd(self, group, name, profile_name, checks=None):
        msg = 'az cdn endpoint rule add -g {} -n {} --profile-name {} --order 1 --rule-name r1\
               --match-variable RemoteAddress --operator GeoMatch --match-values "TH"\
               --action-name CacheExpiration --cache-behavior BypassCache'
        command = msg.format(group,
                             name,
                             profile_name)
        return self.cmd(command, checks)

    def endpoint_add_condition_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint rule condition add -g {} -n {} --profile-name {}'.format(group,
                                                                                         name,
                                                                                         profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_add_action_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint rule action add -g {} -n {} --profile-name {}'.format(group,
                                                                                      name,
                                                                                      profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_remove_rule_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint rule remove -g {} -n {} --profile-name {}'.format(group,
                                                                                  name,
                                                                                  profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_remove_condition_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint rule condition remove -g {} -n {} --profile-name {}'.format(group,
                                                                                            name,
                                                                                            profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_remove_action_cmd(self, group, name, profile_name, checks=None, options=None):
        command = 'cdn endpoint rule action remove -g {} -n {} --profile-name {}'.format(group,
                                                                                         name,
                                                                                         profile_name)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def endpoint_purge_cmd(self, group, name, profile_name, content_paths, checks=None):
        msg = 'cdn endpoint purge -g {} -n {} --profile-name {} --content-paths {}'
        command = msg.format(group,
                             name,
                             profile_name,
                             ' '.join(content_paths))
        return self.cmd(command, checks)

    def endpoint_list_cmd(self, group, profile_name, checks=None, expect_failure=False):
        command = 'cdn endpoint list -g {} --profile-name {}'.format(group, profile_name)
        return self.cmd(command, checks, expect_failure=expect_failure)

    def endpoint_delete_cmd(self, group, name, profile_name, checks=None):
        command = 'cdn endpoint delete -g {} -n {} --profile-name {}'.format(group,
                                                                             name,
                                                                             profile_name)
        return self.cmd(command, checks)

    def origin_update_cmd(self, group, origin_name, endpoint_name, profile_name, http_port='80', https_port='443',
                          private_link_id=None, private_link_location=None, private_link_message=None, tags=None,
                          checks=None):

        cmd = f'cdn origin update -g {group} --endpoint-name {endpoint_name} --profile-name {profile_name} ' \
              f'-n {origin_name} --http-port={http_port} --https-port={https_port}'

        if private_link_id:
            cmd += f' --private-link-resource-id={private_link_id}'
        if private_link_location:
            cmd += f' --private-link-location={private_link_location}'
        if private_link_message:
            cmd += f' \'--private-link-approval-message={private_link_message}\''
        if tags:
            cmd = add_tags(cmd, tags)
        return self.cmd(cmd, checks)

    def origin_list_cmd(self, group, endpoint_name, profile_name, checks=None):
        msg = 'cdn origin list -g {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)

    def origin_show_cmd(self, group, endpoint_name, profile_name, name, checks=None):
        msg = 'cdn origin show -g {} -n {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)

    def custom_domain_show_cmd(self, group, profile_name, endpoint_name, name, checks=None):
        msg = 'cdn custom-domain show -g {} -n {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)

    def custom_domain_list_cmd(self, group, profile_name, endpoint_name, checks=None):
        msg = 'cdn custom-domain list -g {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)

    def custom_domain_create_cmd(self, group, profile_name, endpoint_name, name, hostname, location=None,
                                 tags=None, checks=None):
        msg = 'cdn custom-domain create -g {} -n {} --endpoint-name {} --profile-name {} --hostname={}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name,
                             hostname)
        if location is not None:
            command += ' -l ' + location
        if tags is not None:
            command += " --tags '" + ' '.join(['{}={}'.format(key, val) for key, val in tags]) + "'"

        return self.cmd(command, checks)

    def custom_domain_delete_cmd(self, group, profile_name, endpoint_name, name, checks=None):
        msg = 'cdn custom-domain delete -g {} -n {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name)

        return self.cmd(command, checks)

    def custom_domain_enable_https_command(self, group, profile_name, endpoint_name, name,
                                           user_cert_subscription_id=None,
                                           user_cert_group_name=None, user_cert_vault_name=None,
                                           user_cert_secret_name=None, user_cert_secret_version=None,
                                           user_cert_protocol_type=None, min_tls_version=None,
                                           checks=None):
        command = f'cdn custom-domain enable-https -g {group} -n {name} ' \
                  f'--endpoint-name {endpoint_name} --profile-name {profile_name}'

        if min_tls_version is not None:
            command += f' --min-tls-version={min_tls_version}'
        if user_cert_subscription_id is not None:
            command += f' --user-cert-subscription-id={user_cert_subscription_id}'
        if user_cert_group_name is not None:
            command += f' --user-cert-group-name={user_cert_group_name}'
        if user_cert_vault_name is not None:
            command += f' --user-cert-vault-name={user_cert_vault_name}'
        if user_cert_secret_name is not None:
            command += f' --user-cert-secret-name={user_cert_secret_name}'
        if user_cert_secret_version is not None:
            command += f' --user-cert-secret-version={user_cert_secret_version}'
        if user_cert_protocol_type is not None:
            command += f' --user-cert-protocol-type={user_cert_protocol_type}'

        return self.cmd(command, checks)

    def custom_domain_disable_https_cmd(self, group, profile_name, endpoint_name, name, checks=None):
        return self.cmd(f'cdn custom-domain disable-https -g {group} -n {name} '
                        f'--endpoint-name {endpoint_name} --profile-name {profile_name}',
                        checks)

    def byoc_create_keyvault_cert(self, group_name, key_vault_name, cert_name):
        from os import path

        # Build the path to the policy json file in the CDN module's test directory.
        test_dir = path.dirname(path.realpath(__file__))
        default_cert_policy = path.join(test_dir, "byoc_cert_policy.json")

        self.cmd(f'keyvault create --location westus2 --name {key_vault_name} -g {group_name}')
        return self.cmd(f'keyvault certificate create --vault-name {key_vault_name} '
                        f'-n {cert_name} --policy "@{default_cert_policy}"')

    def byoc_get_keyvault_cert_versions(self, key_vault_name, cert_name):
        return self.cmd(f'keyvault certificate list-versions --vault-name {key_vault_name} -n {cert_name}')

    def is_playback_mode(self):
        return self.get_subscription_id() == '00000000-0000-0000-0000-000000000000'
