# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def add_tags(command, tags):
    return command + ' --tags {}'.format(tags)


class CdnScenarioMixin(object):
    def profile_create_cmd(self, group, name, tags=None, checks=None, options=None):
        command = 'cdn profile create -g {} -n {}'.format(group, name)
        if tags:
            command = command + ' --tags {}'.format(tags)
        if options:
            command = command + ' ' + options
        return self.cmd(command, checks)

    def profile_update_cmd(self, group, name, tags=None, checks=None):
        command = 'cdn profile update -g {} -n {}'.format(group, name)
        if tags:
            command = command + ' --tags {}'.format(tags)
        return self.cmd(command, checks)

    def profile_list_cmd(self, group, checks=None):
        command = 'cdn profile list -g {}'.format(group)
        return self.cmd(command, checks)

    def profile_delete_cmd(self, group, name, checks=None):
        command = 'cdn profile delete -g {} -n {}'.format(group, name)
        return self.cmd(command, checks)

    def endpoint_create_cmd(self, group, name, profile_name, origin, tags=None, checks=None):
        cmd_txt = 'cdn endpoint create -g {} -n {} --profile-name {} --origin {}'
        command = cmd_txt.format(group,
                                 name,
                                 profile_name,
                                 origin)
        if tags:
            command = add_tags(command, tags)

        return self.cmd(command, checks)

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

    def custom_domain_create_cmd(self, group, endpoint_name, profile_name, name, host_name,
                                 checks=None):
        msg = 'cdn custom-domain create -g {} -n {} --endpoint-name {} ' \
              '--profile-name {} --host-name {}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name,
                             host_name)
        return self.cmd(command, checks)

    def custom_domain_list_cmd(self, group, endpoint_name, profile_name, checks=None):
        msg = 'cdn custom-domain list -g {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)

    def custom_domain_show_cmd(self, group, endpoint_name, profile_name, name, checks=None):
        msg = 'cdn custom-domain show -g {} -n {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)

    def custom_domain_delete_cmd(self, group, endpoint_name, profile_name, name, checks=None):
        msg = 'cdn custom-domain delete -g {} -n {} --endpoint-name {} --profile-name {}'
        command = msg.format(group,
                             name,
                             endpoint_name,
                             profile_name)
        return self.cmd(command, checks)
