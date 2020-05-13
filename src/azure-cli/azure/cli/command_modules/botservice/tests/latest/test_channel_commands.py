# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError
import uuid


def create_bot(test_class, resource_group):
    test_class.kwargs.update({
        'botname': test_class.create_random_name(prefix='cli', length=10),
        'endpoint': 'https://www.google.com/api/messages',
        'app_id': str(uuid.uuid4()),
        'setting_name': test_class.create_random_name(prefix='auth', length=10),
        'clientid': 'clientid',
        'password': str(uuid.uuid4())
    })

    test_class.cmd('az bot create -k registration -g {rg} -n {botname} -e {endpoint} --appid {app_id} -p {password}', checks=[
        test_class.check('name', '{botname}'),
        test_class.check('resourceGroup', '{rg}'),
        test_class.check('location', 'global')
    ])


class ChannelTests(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=20)
    def test_webchat_channel(self, resource_group):
        create_bot(self, resource_group)

        # We verify that webchat exists for the bot.
        # We cannot make guarantees on the number of webchat sites, but yes on it being enabled.
        self.cmd('az bot webchat show -g {rg} -n {botname}', checks=[
            self.check('properties.channelName', 'WebChatChannel'),
        ])

        self.cmd('az bot webchat show -g {rg} -n {botname} --with-secrets', checks=[
            self.check('properties.channelName', 'WebChatChannel'),
        ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_skype_channel(self, resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot skype create -g {rg} -n {botname} --enable-calling true --enable-media-cards true --enable-messaging true --enable-video true --calling-web-hook https://www.google.com', checks=[
            self.check('properties.properties.enableMessaging', True),
            self.check('properties.properties.enableMediaCards', True),
            self.check('properties.properties.enableVideo', True)
        ])

        self.cmd('az bot skype show -g {rg} -n {botname}', checks=[
            self.check('properties.properties.enableMessaging', True),
            self.check('properties.properties.enableMediaCards', True),
            self.check('properties.properties.enableVideo', False)
        ])

        self.cmd('az bot skype show -g {rg} -n {botname} --with-secrets', checks=[
            self.check('properties.properties.enableMessaging', True),
            self.check('properties.properties.enableMediaCards', True),
            self.check('properties.properties.enableVideo', False)
        ])

        self.cmd('az bot skype delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_msteams_channel(self, resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot msteams create -g {rg} -n {botname} --enable-calling true --calling-web-hook https://www.google.com', checks=[
            self.check('properties.properties.enableCalling', True),
            self.check('properties.properties.isEnabled', True)
        ])

        self.cmd('az bot msteams show -g {rg} -n {botname}', checks=[
            self.check('properties.properties.enableCalling', True),
            self.check('properties.properties.isEnabled', True)
        ])

        self.cmd('az bot msteams show -g {rg} -n {botname} --with-secrets', checks=[
            self.check('properties.properties.enableCalling', True),
            self.check('properties.properties.isEnabled', True)
        ])

        self.cmd('az bot msteams delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_directline_channel(self, resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True)
        ])

        self.cmd('az bot directline show -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True),
            self.check('properties.properties.sites[0].key', '')
        ])

        self.cmd('az bot directline show -g {rg} -n {botname} --with-secrets', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True)
        ])

        self.cmd('az bot directline delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_update_directline(self, resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True),
            self.check('properties.properties.sites[0].isSecureSiteEnabled', False)
        ])

        origin_url = 'https://mybotsite1.azurewebsites.net'
        self.kwargs.update({'origin_url': origin_url})

        self.cmd('az bot directline update -g {rg} -n {botname} --enable-enhanced-auth --trusted-origins {origin_url} --debug', checks=[
            self.check('properties.properties.sites[0].trustedOrigins[0]', 'https://mybotsite1.azurewebsites.net'),
            self.check('properties.properties.sites[0].isSecureSiteEnabled', True)
        ])


class DirectLineSitesTests(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_directline_site_create(self, resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True),
            self.check('properties.properties.sites[0].isSecureSiteEnabled', False)
        ])

        site_name = 'mybotsite1'
        origin_url = 'https://{}.azurewebsites.net'.format(site_name)
        self.kwargs.update({'origin_url': origin_url})
        self.kwargs.update({'site_name': site_name})

        response = self.cmd('az bot directline site create -g {rg} -n {botname} --is-enabled false --enable-enhanced-auth --trusted-origins {origin_url} --site-name {site_name}').get_output_in_json()

        self.assertTrue(response['properties'] is not None)
        self.assertTrue(response['properties']['properties'] is not None)
        self.assertTrue(response['properties']['properties']['sites'] is not None)
        sites = response['properties']['properties']['sites']

        self.assertEqual(len(sites), 2)

        selected_sites = [site for site in sites if site['siteName'] == site_name]
        self.assertTrue(selected_sites, 'site not found')
        site = selected_sites[0]
        self.assertTrue(site['trustedOrigins'])
        self.assertTrue(site['trustedOrigins'][0] == origin_url)
        self.assertFalse(site['isEnabled'])
        self.assertTrue(site['isSecureSiteEnabled'])
        self.assertTrue(site['isV3Enabled'])

        # Add a third site with different parameters
        site_name = 'mybotsite2'
        origin_url = 'https://{}.azurewebsites.net'.format(site_name)
        self.kwargs.update({'origin_url': origin_url})
        self.kwargs.update({'site_name': site_name})

        response = self.cmd('az bot directline site create -g {rg} -n {botname} --trusted-origins {origin_url} --site-name {site_name}').get_output_in_json()

        self.assertTrue(response['properties'] is not None)
        self.assertTrue(response['properties']['properties'] is not None)
        self.assertTrue(response['properties']['properties']['sites'] is not None)
        sites = response['properties']['properties']['sites']

        self.assertEqual(len(sites), 3)

        selected_sites = [site for site in sites if site['siteName'] == site_name]
        self.assertTrue(selected_sites, 'site not found')
        site = selected_sites[0]
        self.assertTrue(site['trustedOrigins'])
        self.assertTrue(site['trustedOrigins'][0] == origin_url)
        self.assertTrue(site['isEnabled'])
        self.assertFalse(site['isSecureSiteEnabled'])

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_directline_site_update(self, resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True),
            self.check('properties.properties.sites[0].isSecureSiteEnabled', False)
        ])

        site_name = 'Default Site'
        origin_url = 'https://{}.azurewebsites.net'.format(site_name.replace(' ', ''))
        self.kwargs.update({'origin_url': origin_url})
        self.kwargs.update({'site_name': site_name})

        response = self.cmd('az bot directline site update -g {rg} -n {botname} --is-enabled false --enable-enhanced-auth --trusted-origins {origin_url} --site-name "{site_name}"').get_output_in_json()

        self.assertTrue(response['properties'] is not None)
        self.assertTrue(response['properties']['properties'] is not None)
        self.assertTrue(response['properties']['properties']['sites'] is not None)
        sites = response['properties']['properties']['sites']

        self.assertEqual(len(sites), 1)
        selected_sites = [site for site in sites if site['siteName'] == site_name]
        self.assertTrue(selected_sites, 'site not found')
        site = selected_sites[0]
        self.assertTrue(site['trustedOrigins'])
        self.assertTrue(site['trustedOrigins'][0] == origin_url)
        self.assertFalse(site['isEnabled'])
        self.assertTrue(site['isSecureSiteEnabled'])
        self.assertTrue(site['isV3Enabled'])

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_directline_site_update_should_raise_error_for_missing_site(self,
                                                                                   resource_group):
        create_bot(self, resource_group)
        self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site'),
            self.check('properties.properties.sites[0].isEnabled', True),
            self.check('properties.properties.sites[0].isSecureSiteEnabled', False)
        ])

        site_name = 'mybotsite1'
        origin_url = 'https://{}.azurewebsites.net'.format(site_name)
        self.kwargs.update({'origin_url': origin_url})
        self.kwargs.update({'site_name': site_name})

        try:
            self.cmd('az bot directline site update -g {rg} -n {botname} --is-enabled false --enable-enhanced-auth --trusted-origins {origin_url} --site-name {site_name}')
            raise AssertionError('should have thrown an error.')
        except CLIError as cli_error:
            expected_error = "Direct Line site \"{}\" not found. First create Direct Line site via " \
                             "\"bot directline site create\"".format(site_name)
            self.assertEqual(cli_error.__str__(), expected_error)
        except AssertionError:
            raise AssertionError('should have thrown a CLIError for updating missing site.')
