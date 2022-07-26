# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from unittest import mock

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

from knack.util import CLIError


# pylint: disable=too-many-instance-attributes
class DataLakeAnalyticsScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        from .recording_processors import JobIdReplacer, patch_uuid_str
        return super(DataLakeAnalyticsScenarioTest, self).__init__(method_name,
                                                                   recording_processors=JobIdReplacer(),
                                                                   replay_patches=patch_uuid_str)

    @ResourceGroupPreparer(name_prefix='cli_test_adla_catalog_mgmt')
    def test_adla_catalog_mgmt(self, resource_group):

        self.kwargs.update({
            'dls': self.create_random_name('cliadls', 24),
            'dla': self.create_random_name('cliadla', 24),
            'loc': 'eastus2',

            # define catalog item names
            'db': 'catalog_item_1',
            'table': 'catalog_item_2',
            'tvf': 'catalog_item_3',
            'proc': 'catalog_item_4',
            'cred': 'catalog_item_5',
            'cred_username': 'catalog_item_6',
            'cred_pwd': 'catalog_item_7',
            'view': 'catalog_item_8'
        })

        # create ADLS accounts
        self.cmd('dls account create -g {rg} -n {dls} -l {loc} --disable-encryption')
        self.cmd('dla account create -g {rg} -n {dla} -l {loc} --default-data-lake-store {dls}')
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
        catalog_script = catalog_script.format(self.kwargs['db'], self.kwargs['table'], self.kwargs['tvf'], self.kwargs['view'], self.kwargs['proc'])
        self.kwargs['job_id'] = self.cmd('dla job submit -n {{dla}} --job-name "python cli catalog job" --script "{}"'.format(catalog_script)).get_output_in_json()['jobId']
        result = self.cmd('dla job wait -n {dla} --job-id {job_id}').get_output_in_json()
        assert result['result'] == 'Succeeded'

        # get all the catalog items
        # list all DBs
        self.cmd('dla catalog database list -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 2),  # because there is always the master DB
        ])
        # get a specific DB
        self.cmd('dla catalog database show -n {dla} --database-name {db}', checks=[
            self.check('name', '{db}'),
        ])
        # list all schemas
        self.cmd('dla catalog schema list -n {dla} --database-name {db}', checks=[
            self.check('type(@)', 'array'),
        ])
        # get a specific schema
        self.cmd('dla catalog schema show -n {dla} --database-name {db} --schema-name dbo', checks=[
            self.check('name', 'dbo'),
            self.check('databaseName', '{db}'),
        ])
        # list all tables
        self.cmd('dla catalog table list -n {dla} --database-name {db} --schema-name dbo', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # list all tables without specifying schema
        self.cmd('dla catalog table list -n {dla} --database-name {db}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # get a specific table
        self.cmd('dla catalog table show -n {dla} --database-name {db} --schema-name dbo --table-name {table}', checks=[
            self.check('name', '{table}'),
            self.check('databaseName', '{db}'),
            self.check('schemaName', 'dbo'),
        ])
        # list all views
        self.cmd('dla catalog view list -n {dla} --database-name {db} --schema-name dbo', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # list all views without specifying schema
        self.cmd('dla catalog view list -n {dla} --database-name {db}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # get a specific view
        self.cmd('dla catalog view show -n {dla} --database-name {db} --schema-name dbo --view-name {view}', checks=[
            self.check('name', '{view}'),
            self.check('databaseName', '{db}'),
            self.check('schemaName', 'dbo'),
        ])
        # list all procs
        self.cmd('dla catalog procedure list -n {dla} --database-name {db} --schema-name dbo', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # get a specific proc
        self.cmd('dla catalog procedure show -n {dla} --database-name {db} --schema-name dbo --procedure-name {proc}', checks=[
            self.check('name', '{proc}'),
            self.check('databaseName', '{db}'),
            self.check('schemaName', 'dbo'),
        ])
        # list all procs
        self.cmd('dla catalog procedure list -n {dla} --database-name {db} --schema-name dbo', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # get a specific proc
        self.cmd('dla catalog procedure show -n {dla} --database-name {db} --schema-name dbo --procedure-name {proc}', checks=[
            self.check('name', '{proc}'),
            self.check('databaseName', '{db}'),
            self.check('schemaName', 'dbo'),
        ])
        # list all tvfs
        self.cmd('dla catalog tvf list -n {dla} --database-name {db} --schema-name dbo', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # list all tvfs without specifying schema
        self.cmd('dla catalog tvf list -n {dla} --database-name {db}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        # get a specific proc
        self.cmd('dla catalog tvf show -n {dla} --database-name {db} --schema-name dbo --table-valued-function-name {tvf}', checks=[
            self.check('name', '{tvf}'),
            self.check('databaseName', '{db}'),
            self.check('schemaName', 'dbo'),
        ])

        # credential crud
        # create a credential
        self.cmd('dla catalog credential create -n {dla} --database-name {db} --credential-name {cred} --user-name {cred_username} --password {cred_pwd} --uri "http://adl.contoso.com:443"')

        # list credentials
        self.cmd('dla catalog credential list -n {dla} --database-name {db}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])

        # get the specific credential
        self.cmd('dla catalog credential show -n {dla} --database-name {db} --credential-name {cred}', checks=[
            self.check('name', '{cred}'),
        ])

        # delete the specific credential
        self.cmd('dla catalog credential delete -n {dla} --database-name {db} --credential-name {cred}')

        # list credentials and validate they are gone.
        self.cmd('dla catalog credential list -n {dla} --database-name {db}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_adla_job_mgmt')
    def test_adla_job_mgmt(self, resource_group):

        self.kwargs.update({
            'dls': self.create_random_name('cliadls', 24),
            'dla': self.create_random_name('cliadla', 24),
            'loc': 'eastus2',
            # job relation ship variables
            'pipeline_id': '3f9a237a-325e-4ec8-9e10-60222a71354d',
            'pipeline_name': 'py_pipeline_name',
            'pipeline_uri': 'https://begoldsm.contoso.com/jobs',
            'recurrence_id': '58cab1f7-fe29-46ce-89ab-628a1e09c5bf',
            'recurrence_name': 'py_recurrence_name',
            'run_id': 'a3f300fc-4496-40ad-b76d-7696e3723b77'
        })

        # create ADLS accounts
        self.cmd('dls account create -g {rg} -n {dls} -l {loc} --disable-encryption')
        self.cmd('dls account show -g {rg} -n {dls}', checks=[
            self.check('name', '{dls}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('dla account create -g {rg} -n {dla} -l {loc} --default-data-lake-store {dls}')
        self.cmd('dla account show -g {rg} -n {dla}', checks=[
            self.check('name', '{dla}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')
        ])

        # submit job - should work with no relationship params
        result = self.cmd('dla job submit -n {dla} --job-name clijobtest --script "DROP DATABASE IF EXISTS FOO; CREATE DATABASE FOO;"', checks=[
            self.check('name', 'clijobtest'),
        ]).get_output_in_json()
        # cancel job
        self.kwargs['job_id'] = result['jobId']
        self.cmd('dla job cancel -n {dla} --job-id {job_id}')

        # get the job and confirm that it was cancelled
        self.cmd('dla job show -n {dla} --job-id {job_id}', checks=[
            self.check('name', 'clijobtest'),
            self.check('result', 'Cancelled'),
        ])

        # job relationship. Attempt to submit a job with invalid job relationship param combos
        with self.assertRaises(CLIError):
            self.cmd('dla job submit -n {dla} --job-name clijobtest --script "DROP DATABASE IF EXISTS FOO; CREATE DATABASE FOO;" --recurrence-name {recurrence_name}')

        with self.assertRaises(CLIError):
            self.cmd('dla job submit -n {dla} --job-name clijobtest --script "DROP DATABASE IF EXISTS FOO; CREATE DATABASE FOO;" --recurrence-name {recurrence_name} --recurrence-id {recurrence_id} --pipeline-name {pipeline_name}')

        # re-submit job with a fully populated relationship
        result = self.cmd('dla job submit -n {dla} --job-name clijobtest --script "DROP DATABASE IF EXISTS FOO; CREATE DATABASE FOO;" --recurrence-name {recurrence_name} --recurrence-id {recurrence_id} --pipeline-name {pipeline_name} --pipeline-id {pipeline_id} --pipeline-uri {pipeline_uri} --run-id {run_id}',
                          checks=self.check('name', 'clijobtest')).get_output_in_json()

        # wait for the job to finish
        self.kwargs['job_id'] = result['jobId']
        self.cmd('dla job wait -n {dla} --job-id {job_id}', checks=[
            self.check('name', 'clijobtest'),
            self.check('result', 'Succeeded'),
            self.check('related.recurrenceId', '{recurrence_id}'),
            self.check('related.recurrenceName', '{recurrence_name}'),
            self.check('related.pipelineId', '{pipeline_id}'),
            self.check('related.pipelineName', '{pipeline_name}'),
            self.check('related.pipelineUri', '{pipeline_uri}'),
            self.check('related.runId', '{run_id}'),
        ])

        # list all jobs
        self.cmd('dla job list -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 2)
        ])

        # get and list job relationships (recurrence and pipeline)
        result = self.cmd('dla job recurrence list -n {dla}').get_output_in_json()
        assert isinstance(result, list)
        assert len(result) >= 1

        self.cmd('dla job recurrence show -n {dla} --recurrence-id {recurrence_id}', checks=[
            self.check('recurrenceId', '{recurrence_id}'),
            self.check('recurrenceName', '{recurrence_name}'),
        ])

        result = self.cmd('dla job pipeline list -n {dla}').get_output_in_json()
        assert isinstance(result, list)
        assert len(result) >= 1

        result = self.cmd('dla job pipeline show -n {dla} --pipeline-id {pipeline_id}', checks=[
            self.check('pipelineId', '{pipeline_id}'),
            self.check('pipelineName', '{pipeline_name}'),
            self.check('pipelineUri', '{pipeline_uri}'),
        ]).get_output_in_json()

        assert isinstance(result['runs'], list)
        assert len(result['runs']) >= 1

    @ResourceGroupPreparer(name_prefix='cli_test_adla_mgmt')
    def test_adla_account_mgmt(self, resource_group):

        self.kwargs.update({
            'dls1': self.create_random_name('cliadls', 12),
            'dls2': self.create_random_name('cliadls', 12),
            'dla': self.create_random_name('cliadla', 12),
            'wasb': self.create_random_name('cliwasb', 12),
            'loc': 'eastus2',
            # compute policy variables
            'user_policy': 'pycliuserpolicy',
            'user_oid': '181c08fa-7ac8-48a6-a869-342ab74566a4',  # azureclitest
            'group_policy': 'pycligrouppolicy',
            'group_oid': 'f0bec09f-45a4-4c58-ac5b-cf0516d7bc68'  # AzureSDKTeam
        })

        # create ADLS accounts
        self.cmd('dls account create -g {rg} -n {dls1} -l {loc} --disable-encryption')
        self.cmd('dls account create -g {rg} -n {dls2} -l {loc} --disable-encryption')
        self.cmd('storage account create -g {rg} -n {wasb} -l {loc} --sku Standard_GRS')

        result = self.cmd('storage account keys list -g {rg} -n {wasb}').get_output_in_json()
        self.kwargs['wasb_key'] = result[0]['value']
        # test create keyvault with default access policy set
        self.cmd('dla account create -g {rg} -n {dla} -l {loc} --default-data-lake-store {dls1}', checks=[
            self.check('name', '{dla}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('defaultDataLakeStoreAccount', '{dls1}'),
            self.check('type(dataLakeStoreAccounts)', 'array'),
            self.check('length(dataLakeStoreAccounts)', 1),
            self.check('maxDegreeOfParallelism', 30),
            self.check('maxJobCount', 3),
            self.check('queryStoreRetention', 30),
        ])
        self.cmd('dla account show -n {dla} -g {rg}', checks=[
            self.check('name', '{dla}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('defaultDataLakeStoreAccount', '{dls1}'),
            self.check('type(dataLakeStoreAccounts)', 'array'),
            self.check('length(dataLakeStoreAccounts)', 1),
            self.check('maxDegreeOfParallelism', 30),
            self.check('maxJobCount', 3),
            self.check('queryStoreRetention', 30),
        ])
        self.cmd('dla account list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{dla}'),
            self.check('[0].location', '{loc}'),
            self.check('[0].resourceGroup', '{rg}'),
        ])
        result = self.cmd('dla account list').get_output_in_json()
        assert isinstance(result, list)
        assert len(result) >= 1

        # test update acct
        self.cmd('dla account update -g {rg} -n {dla} --firewall-state Enabled --max-degree-of-parallelism 15 --max-job-count 2 --query-store-retention 15 --allow-azure-ips Enabled')
        self.cmd('dla account show -n {dla} -g {rg}', checks=[
            self.check('name', '{dla}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('defaultDataLakeStoreAccount', '{dls1}'),
            self.check('type(dataLakeStoreAccounts)', 'array'),
            self.check('length(dataLakeStoreAccounts)', 1),
            self.check('maxDegreeOfParallelism', 15),
            self.check('maxJobCount', 2),
            self.check('queryStoreRetention', 15)
            # TODO: add validation for firewall rules once they are
            # live in production.
        ])

        # test wasb add, get delete
        self.cmd('dla account blob-storage add -g {rg} -n {dla} --storage-account-name {wasb} --access-key {wasb_key}')
        self.cmd('dla account blob-storage show -g {rg} -n {dla} --storage-account-name {wasb}', checks=[
            self.check('name', '{wasb}')
        ])
        self.cmd('dla account blob-storage list -g {rg} -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        self.cmd('dla account blob-storage delete -g {rg} -n {dla} --storage-account-name {wasb}')
        self.cmd('dla account blob-storage list -g {rg} -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])

        # test adls acct add get, delete
        self.cmd('dla account data-lake-store add -g {rg} -n {dla} --data-lake-store-account-name {dls2}')
        self.cmd('dla account data-lake-store show -g {rg} -n {dla} --data-lake-store-account-name {dls2}', checks=[
            self.check('name', '{dls2}')
        ])
        self.cmd('dla account data-lake-store list -g {rg} -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 2),
        ])
        self.cmd('dla account data-lake-store delete -g {rg} -n {dla} --data-lake-store-account-name {dls2}')
        self.cmd('dla account data-lake-store list -g {rg} -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])

        # test compute policy
        # assert that it throws if I don't specify either of the policy types
        with self.assertRaises(CLIError):
            self.cmd('dla account compute-policy create -g {rg} -n {dla} --compute-policy-name {user_policy} --object-id {user_oid} --object-type User')

        self.cmd('dla account compute-policy create -g {rg} -n {dla} --compute-policy-name {user_policy} --object-id {user_oid} --object-type User --max-dop-per-job 2', checks=[
            self.check('name', '{user_policy}'),
            self.check('objectId', '{user_oid}'),
            self.check('objectType', 'User'),
            self.check('maxDegreeOfParallelismPerJob', 2),
        ])

        # get the policy
        self.cmd('dla account compute-policy show -g {rg} -n {dla} --compute-policy-name {user_policy}', checks=[
            self.check('name', '{user_policy}'),
            self.check('objectId', '{user_oid}'),
            self.check('objectType', 'User'),
            self.check('maxDegreeOfParallelismPerJob', 2),
            self.check('minPriorityPerJob', None),
        ])

        # add the group policy
        self.cmd('dla account compute-policy create -g {rg} -n {dla} --compute-policy-name {group_policy} --object-id {group_oid} --object-type Group --max-dop-per-job 2', checks=[
            self.check('name', '{group_policy}'),
            self.check('objectId', '{group_oid}'),
            self.check('objectType', 'Group'),
            self.check('maxDegreeOfParallelismPerJob', 2),
        ])

        # update the user policy
        self.cmd('dla account compute-policy update -g {rg} -n {dla} --compute-policy-name {user_policy} --min-priority-per-job 2', checks=[
            self.check('name', '{user_policy}'),
            self.check('objectId', '{user_oid}'),
            self.check('objectType', 'User'),
            self.check('maxDegreeOfParallelismPerJob', 2),
            self.check('minPriorityPerJob', 2),
        ])

        # list the policies
        self.cmd('dla account compute-policy list -g {rg} -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 2),
        ])

        # delete the user policy
        self.cmd('dla account compute-policy delete -g {rg} -n {dla} --compute-policy-name {user_policy}')

        # list again and verify there is one less policy
        self.cmd('dla account compute-policy list -g {rg} -n {dla}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])

        # test account deletion
        self.cmd('dla account delete -g {rg} -n {dla}')
        self.cmd('dla account list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])
