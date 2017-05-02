# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=method-hidden
# pylint: disable=line-too-long
# pylint: disable=bad-continuation
from __future__ import print_function

try:
    import unittest.mock as mock
except ImportError:
    import mock

from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck)


def _mock_get_uuid_str():
    return '00000000-0000-0000-0000-000000000000'


# pylint: disable=too-many-instance-attributes
class DataLakeAnalyticsCatalogScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeAnalyticsCatalogScenarioTest, self).__init__(__file__, test_method, resource_group='test-adla-catalog-mgmt')
        self.adls_name = 'cliadls123442'
        self.adla_name = 'cliadla123442'
        self.location = 'eastus2'

        # define catalog item names
        self.db_name = 'catalog_item_1'
        self.table_name = 'catalog_item_2'
        self.tvf_name = 'catalog_item_3'
        self.proc_name = 'catalog_item_4'
        self.cred_name = 'catalog_item_5'
        self.cred_user_name = 'catalog_item_6'
        self.cred_user_pwd = 'catalog_item_7'
        self.view_name = 'catalog_item_8'

    def test_dla_catalog_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsCatalogScenarioTest, self).set_up()
        # create ADLS accounts
        self.cmd('dls account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_name, self.location))
        self.cmd('dla account create -g {} -n {} -l {} --default-data-lake-store {}'.format(self.resource_group, self.adla_name, self.location, self.adls_name))
        # run job to construct catalog
        catalog_script = '''DROP DATABASE IF EXISTS {0};
CREATE DATABASE {0};
CREATE TABLE {0}.dbo.{1} (
  UserId int,
  Start DateTime,
  Region string,
  Query string,
  Duration int,
  Urls string,
  ClickedUrls string,
  INDEX idx1 CLUSTERED (Region ASC)
    PARTITIONED BY (UserId) HASH (Region));
ALTER TABLE {0}.dbo.{1} ADD IF NOT EXISTS PARTITION (1);
DROP FUNCTION IF EXISTS {0}.dbo.{2};
CREATE FUNCTION {0}.dbo.{2}()
  RETURNS @result TABLE (
    s_date DateTime,
    s_time string,
    s_sitename string,
    cs_method string,
    cs_uristem string,
    cs_uriquery string,
    s_port int,
    cs_username string,
    c_ip string,
    cs_useragent string,
    cs_cookie string,
    cs_referer string,
    cs_host string,
    sc_status int,
    sc_substatus int,
    sc_win32status int,
    sc_bytes int,
    cs_bytes int,
    s_timetaken int) AS
      BEGIN
        @result = EXTRACT
          s_date DateTime,
          s_time string,
          s_sitename string,
          cs_method string,
          cs_uristem string,
          cs_uriquery string,
          s_port int,
          cs_username string,
          c_ip string,
          cs_useragent string,
          cs_cookie string,
          cs_referer string,
          cs_host string,
          sc_status int,
          sc_substatus int,
          sc_win32status int,
          sc_bytes int,
          cs_bytes int,
          s_timetaken int FROM \\"@/Samples/Data/WebLog.log\\" USING Extractors.Text(delimiter:' ');
        RETURN;
    END;
CREATE VIEW {0}.dbo.{3} AS SELECT * FROM (VALUES(1,2),(2,4)) AS T(a, b);
CREATE PROCEDURE {0}.dbo.{4}() AS BEGIN CREATE VIEW {0}.dbo.{3} AS SELECT * FROM (VALUES(1,2),(2,4)) AS T(a, b); END;'''
        catalog_script = catalog_script.format(self.db_name, self.table_name, self.tvf_name, self.view_name, self.proc_name)
        result = self.cmd('dla job submit -n {} --job-name "{}" --script "{}"'.format(self.adla_name, 'python cli catalog job', catalog_script))
        result = self.cmd('dla job wait -n {} --job-id {}'.format(self.adla_name, result['jobId']))
        assert result['result'] == 'Succeeded'

    def body(self):
        adla = self.adla_name
        # get all the catalog items
        # list all DBs
        self.cmd('dla catalog database list -n {}'.format(adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 2),  # because there is always the master DB
        ])
        # get a specific DB
        self.cmd('dla catalog database show -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('name', self.db_name),
        ])
        # list all schemas
        self.cmd('dla catalog schema list -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
        ])
        # get a specific schema
        self.cmd('dla catalog schema show -n {} --database-name {} --schema-name dbo'.format(adla, self.db_name), checks=[
            JMESPathCheck('name', 'dbo'),
            JMESPathCheck('databaseName', self.db_name),
        ])
        # list all tables
        self.cmd('dla catalog table list -n {} --database-name {} --schema-name dbo'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # list all tables without specifying schema
        self.cmd('dla catalog table list -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # get a specific table
        self.cmd('dla catalog table show -n {} --database-name {} --schema-name dbo --table-name {}'.format(adla, self.db_name, self.table_name), checks=[
            JMESPathCheck('name', self.table_name),
            JMESPathCheck('databaseName', self.db_name),
            JMESPathCheck('schemaName', 'dbo'),
        ])
        # list all views
        self.cmd('dla catalog view list -n {} --database-name {} --schema-name dbo'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # list all views without specifying schema
        self.cmd('dla catalog view list -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # get a specific view
        self.cmd('dla catalog view show -n {} --database-name {} --schema-name dbo --view-name {}'.format(adla, self.db_name, self.view_name), checks=[
            JMESPathCheck('name', self.view_name),
            JMESPathCheck('databaseName', self.db_name),
            JMESPathCheck('schemaName', 'dbo'),
        ])
        # list all procs
        self.cmd('dla catalog procedure list -n {} --database-name {} --schema-name dbo'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # get a specific proc
        self.cmd('dla catalog procedure show -n {} --database-name {} --schema-name dbo --procedure-name {}'.format(adla, self.db_name, self.proc_name), checks=[
            JMESPathCheck('name', self.proc_name),
            JMESPathCheck('databaseName', self.db_name),
            JMESPathCheck('schemaName', 'dbo'),
        ])
        # list all procs
        self.cmd('dla catalog procedure list -n {} --database-name {} --schema-name dbo'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # get a specific proc
        self.cmd('dla catalog procedure show -n {} --database-name {} --schema-name dbo --procedure-name {}'.format(adla, self.db_name, self.proc_name), checks=[
            JMESPathCheck('name', self.proc_name),
            JMESPathCheck('databaseName', self.db_name),
            JMESPathCheck('schemaName', 'dbo'),
        ])
        # list all tvfs
        self.cmd('dla catalog tvf list -n {} --database-name {} --schema-name dbo'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # list all tvfs without specifying schema
        self.cmd('dla catalog tvf list -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # get a specific proc
        self.cmd('dla catalog tvf show -n {} --database-name {} --schema-name dbo --table-valued-function-name {}'.format(adla, self.db_name, self.tvf_name), checks=[
            JMESPathCheck('name', self.tvf_name),
            JMESPathCheck('databaseName', self.db_name),
            JMESPathCheck('schemaName', 'dbo'),
        ])

        # credential crud
        # create a credential
        self.cmd('dla catalog credential create -n {} --database-name {} --credential-name {} --user-name {} --password {} --uri "http://adl.contoso.com:443"'.format(adla, self.db_name, self.cred_name, self.cred_user_name, self.cred_user_pwd))

        # list credentials
        self.cmd('dla catalog credential list -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])

        # get the specific credential
        self.cmd('dla catalog credential show -n {} --database-name {} --credential-name {}'.format(adla, self.db_name, self.cred_name), checks=[
            JMESPathCheck('name', self.cred_name),
        ])

        # delete the specific credential
        self.cmd('dla catalog credential delete -n {} --database-name {} --credential-name {}'.format(adla, self.db_name, self.cred_name))

        # list credentials and validate they are gone.
        self.cmd('dla catalog credential list -n {} --database-name {}'.format(adla, self.db_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])


class DataLakeAnalyticsJobScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DataLakeAnalyticsJobScenarioTest, self).__init__(__file__, test_method, resource_group='test-adla-job-mgmt')
        self.adls_name = 'cliadls1234533'
        self.adla_name = 'cliadla1234533'
        self.location = 'eastus2'

    def test_dla_job_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsJobScenarioTest, self).set_up()

    @mock.patch('azure.cli.command_modules.dla.custom._get_uuid_str',
                _mock_get_uuid_str)
    def _execute_playback(self):
        return super(DataLakeAnalyticsJobScenarioTest, self)._execute_playback()

    def body(self):
        rg = self.resource_group
        adla = self.adla_name
        loc = self.location
        # create ADLS accounts
        self.cmd('dls account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_name, loc))
        self.cmd('dls account show -g {} -n {}'.format(self.resource_group, self.adls_name), checks=[
            JMESPathCheck('name', self.adls_name),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg)
        ])

        self.cmd('dla account create -g {} -n {} -l {} --default-data-lake-store {}'.format(self.resource_group, adla, loc, self.adls_name))
        self.cmd('dla account show -g {} -n {}'.format(self.resource_group, self.adla_name), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg)
        ])

        # submit job
        result = self.cmd('dla job submit -n {} --job-name clijobtest --script "DROP DATABASE IF EXISTS FOO; CREATE DATABASE FOO;"'.format(adla), checks=[
            JMESPathCheck('name', 'clijobtest'),
        ])
        # cancel job
        job_id = result['jobId']
        self.cmd('dla job cancel -n {} --job-id {}'.format(adla, job_id))

        # get the job and confirm that it was cancelled
        self.cmd('dla job show -n {} --job-id {}'.format(adla, job_id), checks=[
            JMESPathCheck('name', 'clijobtest'),
            JMESPathCheck('result', 'Cancelled'),
        ])
        # re-submit job
        result = self.cmd('dla job submit -n {} --job-name clijobtest --script "DROP DATABASE IF EXISTS FOO; CREATE DATABASE FOO;"'.format(adla), checks=[
            JMESPathCheck('name', 'clijobtest'),
        ])

        # wait for the job to finish
        job_id = result['jobId']
        result = self.cmd('dla job wait -n {} --job-id {}'.format(adla, job_id), checks=[
            JMESPathCheck('name', 'clijobtest'),
            JMESPathCheck('result', 'Succeeded'),
        ])

        # list all jobs
        self.cmd('dla job list -n {}'.format(adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 2)
        ])


class DataLakeAnalyticsAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeAnalyticsAccountScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adla-mgmt')
        self.adls_names = ['cliadls123450', 'cliadls123451']
        self.adla_name = 'cliadla123450'
        self.wasb_name = 'cliadlwasb123450'
        self.location = 'eastus2'

    def test_dla_account_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsAccountScenarioTest, self).set_up()
        # create ADLS accounts
        self.cmd('dls account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[0], self.location))
        self.cmd('dls account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[1], self.location))
        self.cmd('storage account create -g {} -n {} -l {} --sku Standard_GRS'.format(self.resource_group, self.wasb_name, self.location))

    def body(self):
        rg = self.resource_group
        adls1 = self.adls_names[0]
        adls2 = self.adls_names[1]
        adla = self.adla_name
        loc = self.location
        result = self.cmd('storage account keys list -g {} -n {}'.format(self.resource_group, self.wasb_name))
        wasb_key = result[0]['value']
        # test create keyvault with default access policy set
        self.cmd('dla account create -g {} -n {} -l {} --default-data-lake-store {}'.format(rg, adla, loc, adls1), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('defaultDataLakeStoreAccount', adls1),
            JMESPathCheck('type(dataLakeStoreAccounts)', 'array'),
            JMESPathCheck('length(dataLakeStoreAccounts)', 1),
            JMESPathCheck('maxDegreeOfParallelism', 30),
            JMESPathCheck('maxJobCount', 3),
            JMESPathCheck('queryStoreRetention', 30),
        ])
        self.cmd('dla account show -n {} -g {}'.format(adla, rg), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('defaultDataLakeStoreAccount', adls1),
            JMESPathCheck('type(dataLakeStoreAccounts)', 'array'),
            JMESPathCheck('length(dataLakeStoreAccounts)', 1),
            JMESPathCheck('maxDegreeOfParallelism', 30),
            JMESPathCheck('maxJobCount', 3),
            JMESPathCheck('queryStoreRetention', 30),
        ])
        self.cmd('dla account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', adla),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])
        result = self.cmd('dla account list')
        assert isinstance(result, list)
        assert len(result) >= 1

        # test update acct
        self.cmd('dla account update -g {} -n {} --firewall-state Enabled --max-degree-of-parallelism 15 --max-job-count 2 --query-store-retention 15 --allow-azure-ips Enabled'.format(rg, adla))
        self.cmd('dla account show -n {} -g {}'.format(adla, rg), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('defaultDataLakeStoreAccount', adls1),
            JMESPathCheck('type(dataLakeStoreAccounts)', 'array'),
            JMESPathCheck('length(dataLakeStoreAccounts)', 1),
            JMESPathCheck('maxDegreeOfParallelism', 15),
            JMESPathCheck('maxJobCount', 2),
            JMESPathCheck('queryStoreRetention', 15)
            # TODO: add validation for firewall rules once they are
            # live in production.
        ])

        # test adls acct add get, delete
        self.cmd('dla account data-lake-store add -g {} -n {} --data-lake-store-account-name {}'.format(rg, adla, adls2))
        self.cmd('dla account data-lake-store show -g {} -n {} --data-lake-store-account-name {}'.format(rg, adla, adls2), checks=[
            JMESPathCheck('name', adls2)
        ])
        self.cmd('dla account data-lake-store list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 2),
        ])
        self.cmd('dla account data-lake-store delete -g {} -n {} --data-lake-store-account-name {}'.format(rg, adla, adls2))
        self.cmd('dla account data-lake-store list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # test wasb add, get delete
        self.cmd('dla account blob-storage add -g {} -n {} --storage-account-name {} --access-key {}'.format(rg, adla, self.wasb_name, wasb_key))
        self.cmd('dla account blob-storage show -g {} -n {} --storage-account-name {}'.format(rg, adla, self.wasb_name), checks=[
            JMESPathCheck('name', self.wasb_name)
        ])
        self.cmd('dla account blob-storage list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        self.cmd('dla account blob-storage delete -g {} -n {} --storage-account-name {}'.format(rg, adla, self.wasb_name))
        self.cmd('dla account blob-storage list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
        # test account deletion
        self.cmd('dla account delete -g {} -n {}'.format(rg, adla))
        self.cmd('dla account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
