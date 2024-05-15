# Azure CLI Hdinsightonaks Extension #
This is an extension to Azure CLI to manage Hdinsightonaks resources.

## How to use ##

Install this extension using the below CLI command

```sh
az extension add --name hdinsightonaks
```

### Included Features ###

#### List a list of available cluster pool versions ####

```sh
az hdinsight-on-aks list-available-cluster-pool-version -l westus3
```

#### Get all hdinsightonaks available-cluster version ####

```sh
az hdinsight-on-aks list-available-cluster-version -l westus3
```

#### Check the availability of the cluster name ####

```sh
az hdinsight-on-aks check-name-availability -l westus3 \
 --name cliclusterpool/clicluster \
 --type Microsoft.HDInsight/clusterPools/clusters
```

#### Create a Trino cluster ####

```sh
$node-profile = az hdinsight-on-aks cluster node-profile create --count 5 --node-type Worker --vm-size Standard_D8d_v5
az hdinsight-on-aks cluster create -n clustername --cluster-pool-name \
 clusterpoolname -g resourcesGroup -l westus3 --assigned-identity-object-id \
 00000000-0000-0000-0000-000000000000 \
 --assigned-identity-client-id 00000000-0000-0000-0000-000000000000 \
 --authorization-user-id 00000000-0000-0000-0000-000000000000 \
 --assigned-identity-id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/PSGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/yourmsi \
 --cluster-type Trino --cluster-version 1.0.6 --oss-version 0.410.0 \
 --nodes $node-profile
```

#### Delete a cluster ####

```sh
az hdinsight-on-aks cluster delete -n testcluster --cluster-pool-name testpool -g RG
```

#### List the HDInsight cluster pools under a resource group ####

```sh
az hdinsight-on-aks cluster list --cluster-pool-name testpool -g RG
```

#### List the config dump of all services running in cluster ####

```sh
az hdinsight-on-aks cluster list-service-config --cluster-name testcluster --cluster-pool-name testpool -g RG
```

#### Resize an existing Cluster ####

```sh
az hdinsight-on-aks cluster resize --cluster-name testcluster --cluster-pool-name testpool -g RG -l westus3 --target-worker-node-count 6
```
#### Get a HDInsight cluster ####

```sh
az hdinsight-on-aks cluster show -n testcluster --cluster-pool-name testpool -g RG
```

#### Get the status of a cluster instance ####

```sh
az hdinsight-on-aks cluster show-instance-view --cluster-name testcluster --cluster-pool-name testpool -g RG
```

#### Update a cluster ####

```sh
az hdinsight-on-aks cluster update -n testpsspark --cluster-pool-name ps-test-pool \
 -g Group --service-configs-profiles @config.json
```

#### List jobs of HDInsight on AKS cluster ####

```sh
az hdinsight-on-aks cluster job list --cluster-name testcluster --cluster-pool-name testpool -g RG
```

#### Operations on jobs of HDInsight on AKS cluster ####

```sh
$jobProperty = az hdinsight-on-aks cluster flink-job create --action NEW --job-name job1 --entry-class com.microsoft.hilo.flink.job.streaming.SleepJob --job-jar-directory abfs://flinkjob@hilosa.dfs.core.windows.net/jars --flink-configuration '{\"parallelism\":\"1\"}' --args test --jar-name jarname --job-name test1
az hdinsight-on-aks cluster job run --cluster-name testcluster --cluster-pool-name testpool -g RG--flink-job $jobProperty
```

#### Create a cluster pool ####

```sh
az hdinsight-on-aks clusterpool create -g RG -n poolName -l westus3 --workernode-size Standard_E4s_v3
```

#### Delete a Cluster Pool ####

```sh
az hdinsight-on-aks clusterpool delete -g RG -n testcluster
```

#### List the list of Cluster Pools within a Subscription ####

```sh
az hdinsight-on-aks clusterpool list
```

#### Get a cluster pool ####

```sh
az hdinsight-on-aks clusterpool show -g RG -n testpool
```

#### Update a cluster pool ####

```sh
az hdinsight-on-aks clusterpool update -g RG -n testpool --enable-log-analytics \
 --log-analytic-workspace-id "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/RG/providers/microsoft.operationalinsights/workspaces/yourworkspace"
```
