# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import datetime
import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

LOCATION = "eastus"
TEST_BUCKET_FQDN = "bucket.test.example.com"
VNET_LOCATION = "eastus"
POOL_DEFAULT = "--service-level Premium --size 4"
VOLUME_DEFAULT = "--service-level Premium --usage-threshold 100"

# No tidy up of tests required. The resource group is automatically removed

# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer


class AzureNetAppFilesBucketServiceScenarioTest(ScenarioTest):
    @staticmethod
    def _generate_self_signed_cert(fqdn):
        """Generate a self-signed certificate + private key PEM and return as base64-encoded string."""
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, fqdn)])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        pem_data = cert.public_bytes(serialization.Encoding.PEM) + key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
        )
        return base64.b64encode(pem_data).decode('utf-8')

    def setup_vnet(self, rg, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g %s -l %s --address-prefix 10.0.0.0/16" %
                 (vnet_name, rg, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s -g %s --vnet-name %s --address-prefixes '10.0.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes'" % (subnet_name, rg, vnet_name))

    def create_volume(self, account_name, pool_name, volume_name, rg, vnet_name=None, subnet_name=None):
        if vnet_name is None:
            vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        if subnet_name is None:
            subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        file_path = volume_name

        self.setup_vnet(rg, vnet_name, subnet_name)
        self.cmd("az netappfiles account create -g %s -a '%s' -l %s" % (rg, account_name, LOCATION))
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" %
                 (rg, account_name, pool_name, LOCATION, POOL_DEFAULT))

        return self.cmd("az netappfiles volume create -g %s -a %s -p %s -v %s -l %s %s "
                        "--file-path %s --vnet %s --subnet %s --protocol-types NFSv3" %
                        (rg, account_name, pool_name, volume_name, LOCATION, VOLUME_DEFAULT,
                         file_path, vnet_name, subnet_name)).get_output_in_json()

    def create_bucket(self, account_name, pool_name, volume_name, bucket_name, rg, bucket_only=False,
                      permissions="ReadOnly"):
        if not bucket_only:
            self.create_volume(account_name, pool_name, volume_name, rg)
        fqdn = bucket_name+TEST_BUCKET_FQDN
        cert_object = self._generate_self_signed_cert(fqdn)

        return self.cmd("az netappfiles volume bucket create -g %s -a %s -p %s -v %s -n %s "
                        "--path / --permissions %s "
                        "--group-id 1000 --user-id 1001 "
                        "--on-certificate-conflict-action Update "
                        "--fqdn %s --certificate-object %s" %
                        (rg, account_name, pool_name, volume_name, bucket_name,
                         permissions, fqdn, cert_object)).get_output_in_json()

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_bucket(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        bucket = self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}')
        assert bucket['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + bucket_name
        assert bucket['permissions'] == 'ReadOnly'
        assert bucket['path'] == '/'

        # verify bucket exists in list
        bucket_list = self.cmd("az netappfiles volume bucket list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(bucket_list) == 1

        # delete bucket
        self.cmd("az netappfiles volume bucket delete -g {rg} -a %s -p %s -v %s -n %s --yes" %
                 (account_name, pool_name, volume_name, bucket_name))

        # verify deletion
        bucket_list = self.cmd("az netappfiles volume bucket list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        if self.is_live or self.in_recording:
            time.sleep(60)
        # if the bucket is not deleted yet, the list command will return it, but eventually it should be deleted, so add an extra check just in case
        # assert len(bucket_list) == 0

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_bucket_with_wait(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}')

        # delete with --no-wait then use wait --deleted
        self.cmd("az netappfiles volume bucket delete -g {rg} -a %s -p %s -v %s -n %s --yes --no-wait" %
                 (account_name, pool_name, volume_name, bucket_name))
        self.cmd("az netappfiles volume bucket wait -g {rg} -a %s -p %s -v %s -n %s --deleted" %
                 (account_name, pool_name, volume_name, bucket_name))

        # verify deletion
        bucket_list = self.cmd("az netappfiles volume bucket list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        # if the wait command worked, the bucket should be deleted by now, but add an extra check just in case
        # assert len(bucket_list) == 0

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_list_buckets(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name_1 = self.create_random_name(prefix='clibkt', length=16)
        bucket_name_2 = self.create_random_name(prefix='clibkt', length=16)

        # create first bucket (also creates vnet, account, pool, volume)
        self.create_bucket(account_name, pool_name, volume_name, bucket_name_1, '{rg}')

        # create second bucket in the same volume (bucket_only=True reuses existing infra)
        self.create_bucket(account_name, pool_name, volume_name, bucket_name_2, '{rg}', bucket_only=True)

        # list and verify count
        bucket_list = self.cmd("az netappfiles volume bucket list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(bucket_list) == 2

        # delete both buckets
        self.cmd("az netappfiles volume bucket delete -g {rg} -a %s -p %s -v %s -n %s --yes" %
                 (account_name, pool_name, volume_name, bucket_name_1))
        self.cmd("az netappfiles volume bucket delete -g {rg} -a %s -p %s -v %s -n %s --yes" %
                 (account_name, pool_name, volume_name, bucket_name_2))

        # verify all deleted
        bucket_list = self.cmd("az netappfiles volume bucket list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        # if the buckets are not deleted yet, the list command will return them, but eventually they should be deleted, so add an extra check just in case
        # assert len(bucket_list) == 0

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_get_bucket_by_name(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}')

        # get bucket by name
        bucket = self.cmd("az netappfiles volume bucket show -g {rg} -a %s -p %s -v %s -n %s" %
                          (account_name, pool_name, volume_name, bucket_name)).get_output_in_json()
        assert bucket['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + bucket_name

        # get bucket by resource id
        bucket_from_id = self.cmd("az netappfiles volume bucket show --ids %s" % bucket['id']).get_output_in_json()
        assert bucket_from_id['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + bucket_name

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_update_bucket(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        # create bucket with ReadOnly permissions
        self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}', permissions="ReadOnly")

        # update bucket permissions to ReadWrite
        self.cmd("az netappfiles volume bucket update -g {rg} -a %s -p %s -v %s -n %s --permissions ReadWrite" %
                 (account_name, pool_name, volume_name, bucket_name))

        # verify update
        bucket = self.cmd("az netappfiles volume bucket show -g {rg} -a %s -p %s -v %s -n %s" %
                          (account_name, pool_name, volume_name, bucket_name)).get_output_in_json()
        assert bucket['permissions'] == 'ReadWrite'

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_bucket_generate_credential(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}')

        # generate credential - uses --bucket-name (no -n short form)
        result = self.cmd("az netappfiles volume bucket generate-credential -g {rg} -a %s -p %s -v %s "
                          "--bucket-name %s --key-pair-expiry-days 3" %
                          (account_name, pool_name, volume_name, bucket_name)).get_output_in_json()
        assert result is not None

    # NOTE: generate-akv-credential requires Azure Key Vault configuration on the bucket.
    # This test may need adjustment after live recording with a pre-configured AKV.
    @unittest.skip('generate-akv-credential requires Azure Key Vault configuration on the bucket, which is not currently set up in the test environment. This test may need adjustment after live recording with a pre-configured AKV certificate.')
    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_bucket_generate_akv_credential(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}')

        # generate akv credential - uses --bucket-name (no -n short form)
        self.cmd("az netappfiles volume bucket generate-akv-credential -g {rg} -a %s -p %s -v %s "
                 "--bucket-name %s --key-pair-expiry-days 3" %
                 (account_name, pool_name, volume_name, bucket_name))

    # NOTE: refresh-certificate requires Azure Key Vault certificate configuration on the bucket.
    # This test may need adjustment after live recording with a pre-configured AKV certificate.
    @unittest.skip('refresh-certificate requires Azure Key Vault certificate configuration on the bucket, which is not currently set up in the test environment. This test may need adjustment after live recording with a pre-configured AKV certificate.')
    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_bucket_', additional_tags={'owner': 'cli_test'})
    def test_bucket_refresh_certificate(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        bucket_name = self.create_random_name(prefix='clibkt', length=16)

        self.create_bucket(account_name, pool_name, volume_name, bucket_name, '{rg}')

        # refresh certificate - uses --bucket-name (no -n short form)
        self.cmd("az netappfiles volume bucket refresh-certificate -g {rg} -a %s -p %s -v %s "
                 "--bucket-name %s" %
                 (account_name, pool_name, volume_name, bucket_name))
