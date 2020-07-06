
# Design Specification

## Introduction

Most `show` or `list` commands return a json output which may be quite long and difficult to understand. So `az` provide `--query` argument to filter the output with JMESPath string. But JMESPath language is different from any other programming language. So writing a JMESPath string is a hard job for beginner.

The main purpose of this project is to automatically generate JMESPath query string based on command output. We add a global argument `--query-recommend` for `az` command. When you add this argument to any command, we will pre-run this command, and then analyze command output. Finally give you a list of JMESPath query string that you can use. Then you just need to copy the recommendations and get the filtered results. Also you can custom your query string based on the recommendations. 

We plan to generate various kinds of recommendations.

## Basic

* select a key

This query allows you to select ids or resources groups from a list of vms or other resources. Use sub-expression to query nested values should also work fine. Example queries are:


```shell
$ az vm list --query-recommend
--query [].resourceGroup: Get all available resourceGroup in you subscription
--query [].storageProfile.osDisk.osType: Get all available osType in you subscription
```

* select specific number os results

This query allows you to only select a specific number of results.

```shell
$ az vm list --query-recommend
--query [:3]: Get first 3 elements
--query [:3].resourceGroup: Get resourceGroup of first 3 elements
```


* filter with conditions

This query allows you to use a filter expression to filter the results. We will only print out the results that satisfied the condition. Multiple conditions can join each other with `&&` or `||` operator.

```shell
$ az vm list --query-recommend
--query [?tag=='MyTAG']: Get all results whose tag is 'MyTAG'
--query [?tag=='MyTAG' && location='eastus']: Get all results whose tag is 'MyTAG' and location is 'eastus'
```

* multi-select/multi-hash

This operation will help you to create a new json from current output.

```shell
$ az vm list --query-recommend
--query [].{RG:resourceGroup, TAG:tag, os:storageProfile.osDisk.osType}: Return resourcesGroup, tag and osType info
```

* function support

Use kind of functions to make query much powerful.

```shell
$ az vm list --query-recommend
--query length([?resourceGroup=='MyGroup']): show the number of vms under MyGroup
```

## Intermediate
`--query-recommend` will accept a list of key words, and we can give suggestions based on these key words.
For example, when you type `az vm list --query-recommend tag`, we assume that you're interested in TAG field. So we will recommend queries related with tag. Contains should also be supported. Here are some expected outputs:

```shell
$ az vm list --query-recommend tag
--query [].tag: to show all tags in the list
--query [?tag=='MyTAG']: this query will only show VMs with 'MyTAG'
--query [?tag=='MyTAG'].{id:id, RG:resourceGroup}: this query will give you more specific fields
```
