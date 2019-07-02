# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import



helps['apimgmt api'] = """
    type: group
    short-summary: Commands to manage Api.
"""

helps['apimgmt api create'] = """
    type: command
    short-summary: create a apimgmt api.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiUsingOai3Import
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id petstore --path petstore --value https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml --format openapi-link
      - name: ApiManagementCreateApiUsingSwaggerImport
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id petstore --path petstore --value http://petstore.swagger.io/v2/swagger.json --format swagger-link-json
      - name: ApiManagementCreateApiUsingWadlImport
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id petstore --path collector --value https://developer.cisco.com/media/wae-release-6-2-api-reference/wae-collector-rest-api/application.wadl --format wadl-link-json
      - name: ApiManagementCreateSoapToRestApiUsingWsdlImport
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id soapApi --path currency --value http://www.webservicex.net/CurrencyConvertor.asmx?WSDL --format wsdl-link
      - name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id soapApi --path currency --value http://www.webservicex.net/CurrencyConvertor.asmx?WSDL --format wsdl-link --api-type soap
      - name: ApiManagementCreateApi
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id tempgroup --description apidescription5200 --display-name apiname1463 --service-url http://newechoapi.cloudapp.net/api --path newapiPath
      - name: ApiManagementCreateApiRevisionFromExistingApi
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id echo-api;rev=3 --api-revision_description Creating a Revision of an existing API --source-api_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apis/{{ api_name }} --service-url http://echoapi.cloudapp.net/apiv3 --path echo
      - name: ApiManagementCreateApiNewVersionUsingExistingApi
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id echoapiv3 --description Create Echo API into a new Version using Existing Version Set and Copy all Operations. --api-version v4 --is-current true --api-version_set_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apiVersionSets/{{ api_version_set_name }} --subscription-required true --source-api_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apis/{{ api_name }} --display-name Echo API2 --service-url http://echoapi.cloudapp.net/api --path echo2
      - name: ApiManagementCreateApiClone
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id echo-api2 --description Copy of Existing Echo Api including Operations. --is-current true --subscription-required true --source-api_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apis/{{ api_name }} --display-name Echo API2 --service-url http://echoapi.cloudapp.net/api --path echo2
      - name: ApiManagementCreateApiWithOpenIdConnect
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id tempgroup --description This is a sample server Petstore server.  You can find out more about Swagger at [http://swagger.io](http://swagger.io) or on [irc.freenode.net, #swagger](http://swagger.io/irc/).  For this sample, you can use the api key `special-key` to test the authorization filters. --display-name Swagger Petstore --service-url http://petstore.swagger.io/v2 --path petstore
      - name: ApiManagementUpdateApi
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id echo-api --display-name Echo API New --service-url http://echoapi.cloudapp.net/api2 --path newecho
      - name: ApiManagementDeleteApi
        text: apimgmt api create  --resource-group rg1 --service-name apimService1 --api-id echo-api
"""

helps['apimgmt api update'] = """
    type: command
    short-summary: update a apimgmt api.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiUsingOai3Import
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id petstore --path petstore --value https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml --format openapi-link
      - name: ApiManagementCreateApiUsingSwaggerImport
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id petstore --path petstore --value http://petstore.swagger.io/v2/swagger.json --format swagger-link-json
      - name: ApiManagementCreateApiUsingWadlImport
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id petstore --path collector --value https://developer.cisco.com/media/wae-release-6-2-api-reference/wae-collector-rest-api/application.wadl --format wadl-link-json
      - name: ApiManagementCreateSoapToRestApiUsingWsdlImport
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id soapApi --path currency --value http://www.webservicex.net/CurrencyConvertor.asmx?WSDL --format wsdl-link
      - name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id soapApi --path currency --value http://www.webservicex.net/CurrencyConvertor.asmx?WSDL --format wsdl-link --api-type soap
      - name: ApiManagementCreateApi
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id tempgroup --description apidescription5200 --display-name apiname1463 --service-url http://newechoapi.cloudapp.net/api --path newapiPath
      - name: ApiManagementCreateApiRevisionFromExistingApi
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id echo-api;rev=3 --api-revision_description Creating a Revision of an existing API --source-api_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apis/{{ api_name }} --service-url http://echoapi.cloudapp.net/apiv3 --path echo
      - name: ApiManagementCreateApiNewVersionUsingExistingApi
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id echoapiv3 --description Create Echo API into a new Version using Existing Version Set and Copy all Operations. --api-version v4 --is-current true --api-version_set_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apiVersionSets/{{ api_version_set_name }} --subscription-required true --source-api_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apis/{{ api_name }} --display-name Echo API2 --service-url http://echoapi.cloudapp.net/api --path echo2
      - name: ApiManagementCreateApiClone
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id echo-api2 --description Copy of Existing Echo Api including Operations. --is-current true --subscription-required true --source-api_id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/apis/{{ api_name }} --display-name Echo API2 --service-url http://echoapi.cloudapp.net/api --path echo2
      - name: ApiManagementCreateApiWithOpenIdConnect
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id tempgroup --description This is a sample server Petstore server.  You can find out more about Swagger at [http://swagger.io](http://swagger.io) or on [irc.freenode.net, #swagger](http://swagger.io/irc/).  For this sample, you can use the api key `special-key` to test the authorization filters. --display-name Swagger Petstore --service-url http://petstore.swagger.io/v2 --path petstore
      - name: ApiManagementUpdateApi
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id echo-api --display-name Echo API New --service-url http://echoapi.cloudapp.net/api2 --path newecho
      - name: ApiManagementDeleteApi
        text: apimgmt api update  --resource-group rg1 --service-name apimService1 --api-id echo-api
"""

helps['apimgmt api delete'] = """
    type: command
    short-summary: delete a apimgmt api.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiUsingOai3Import
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id petstore
      - name: ApiManagementCreateApiUsingSwaggerImport
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id petstore
      - name: ApiManagementCreateApiUsingWadlImport
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id petstore
      - name: ApiManagementCreateSoapToRestApiUsingWsdlImport
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id soapApi
      - name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id soapApi
      - name: ApiManagementCreateApi
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id tempgroup
      - name: ApiManagementCreateApiRevisionFromExistingApi
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id echo-api;rev=3
      - name: ApiManagementCreateApiNewVersionUsingExistingApi
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id echoapiv3
      - name: ApiManagementCreateApiClone
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id echo-api2
      - name: ApiManagementCreateApiWithOpenIdConnect
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id tempgroup
      - name: ApiManagementUpdateApi
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id echo-api
      - name: ApiManagementDeleteApi
        text: apimgmt api delete  --resource-group rg1 --service-name apimService1 --api-id echo-api
"""

helps['apimgmt api list'] = """
    type: command
    short-summary: list a apimgmt api.
    examples:
# list_by_tags -- list
      - name: ApiManagementCreateApiUsingOai3Import
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiUsingSwaggerImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiUsingWadlImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateSoapToRestApiUsingWsdlImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiRevisionFromExistingApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiNewVersionUsingExistingApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiClone
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiWithOpenIdConnect
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
# list_by_service -- list
      - name: ApiManagementCreateApiUsingOai3Import
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiUsingSwaggerImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiUsingWadlImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateSoapToRestApiUsingWsdlImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiRevisionFromExistingApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiNewVersionUsingExistingApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiClone
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateApiWithOpenIdConnect
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteApi
        text: apimgmt api list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt api show'] = """
    type: command
    short-summary: show a apimgmt api.
    examples:
# get -- show
      - name: ApiManagementCreateApiUsingOai3Import
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id petstore
      - name: ApiManagementCreateApiUsingSwaggerImport
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id petstore
      - name: ApiManagementCreateApiUsingWadlImport
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id petstore
      - name: ApiManagementCreateSoapToRestApiUsingWsdlImport
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id soapApi
      - name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id soapApi
      - name: ApiManagementCreateApi
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id tempgroup
      - name: ApiManagementCreateApiRevisionFromExistingApi
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id echo-api;rev=3
      - name: ApiManagementCreateApiNewVersionUsingExistingApi
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id echoapiv3
      - name: ApiManagementCreateApiClone
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id echo-api2
      - name: ApiManagementCreateApiWithOpenIdConnect
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id tempgroup
      - name: ApiManagementUpdateApi
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id echo-api
      - name: ApiManagementDeleteApi
        text: apimgmt api show  --resource-group rg1 --service-name apimService1 --api-id echo-api
"""

helps['apimgmt api release'] = """
    type: group
    short-summary: Commands to manage ApiRelease.
"""

helps['apimgmt api release create'] = """
    type: command
    short-summary: create a apimgmt api release.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiRelease
        text: apimgmt api release create  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev --notes yahooagain
      - name: ApiManagementUpdateApiRelease
        text: apimgmt api release create  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev --notes yahooagain
      - name: ApiManagementDeleteApiRelease
        text: apimgmt api release create  --resource-group rg1 --service-name apimService1 --api-id 5a5fcc09124a7fa9b89f2f1d --release-id testrev
"""

helps['apimgmt api release update'] = """
    type: command
    short-summary: update a apimgmt api release.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiRelease
        text: apimgmt api release update  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev --notes yahooagain
      - name: ApiManagementUpdateApiRelease
        text: apimgmt api release update  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev --notes yahooagain
      - name: ApiManagementDeleteApiRelease
        text: apimgmt api release update  --resource-group rg1 --service-name apimService1 --api-id 5a5fcc09124a7fa9b89f2f1d --release-id testrev
"""

helps['apimgmt api release delete'] = """
    type: command
    short-summary: delete a apimgmt api release.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiRelease
        text: apimgmt api release delete  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev
      - name: ApiManagementUpdateApiRelease
        text: apimgmt api release delete  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev
      - name: ApiManagementDeleteApiRelease
        text: apimgmt api release delete  --resource-group rg1 --service-name apimService1 --api-id 5a5fcc09124a7fa9b89f2f1d --release-id testrev
"""

helps['apimgmt api release list'] = """
    type: command
    short-summary: list a apimgmt api release.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiRelease
        text: apimgmt api release list  --resource-group rg1 --service-name apimService1 --api-id a1
      - name: ApiManagementUpdateApiRelease
        text: apimgmt api release list  --resource-group rg1 --service-name apimService1 --api-id a1
      - name: ApiManagementDeleteApiRelease
        text: apimgmt api release list  --resource-group rg1 --service-name apimService1 --api-id 5a5fcc09124a7fa9b89f2f1d
"""

helps['apimgmt api release show'] = """
    type: command
    short-summary: show a apimgmt api release.
    examples:
# get -- show
      - name: ApiManagementCreateApiRelease
        text: apimgmt api release show  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev
      - name: ApiManagementUpdateApiRelease
        text: apimgmt api release show  --resource-group rg1 --service-name apimService1 --api-id a1 --release-id testrev
      - name: ApiManagementDeleteApiRelease
        text: apimgmt api release show  --resource-group rg1 --service-name apimService1 --api-id 5a5fcc09124a7fa9b89f2f1d --release-id testrev
"""

helps['apimgmt api operation'] = """
    type: group
    short-summary: Commands to manage ApiOperation.
"""

helps['apimgmt api operation create'] = """
    type: command
    short-summary: create a apimgmt api operation.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiOperation
        text: apimgmt api operation create  --resource-group rg1 --service-name apimService1 --api-id PetStoreTemplate2 --operation-id newoperations --description This can only be done by the logged in user. --display-name createUser2 --method POST --url-template /user1
      - name: ApiManagementUpdateApiOperation
        text: apimgmt api operation create  --resource-group rg1 --service-name apimService1 --api-id echo-api --operation-id operationId --display-name Retrieve resource --method GET --url-template /resource
      - name: ApiManagementDeleteApiOperation
        text: apimgmt api operation create  --resource-group rg1 --service-name apimService1 --api-id 57d2ef278aa04f0888cba3f3 --operation-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api operation update'] = """
    type: command
    short-summary: update a apimgmt api operation.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiOperation
        text: apimgmt api operation update  --resource-group rg1 --service-name apimService1 --api-id PetStoreTemplate2 --operation-id newoperations --description This can only be done by the logged in user. --display-name createUser2 --method POST --url-template /user1
      - name: ApiManagementUpdateApiOperation
        text: apimgmt api operation update  --resource-group rg1 --service-name apimService1 --api-id echo-api --operation-id operationId --display-name Retrieve resource --method GET --url-template /resource
      - name: ApiManagementDeleteApiOperation
        text: apimgmt api operation update  --resource-group rg1 --service-name apimService1 --api-id 57d2ef278aa04f0888cba3f3 --operation-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api operation delete'] = """
    type: command
    short-summary: delete a apimgmt api operation.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiOperation
        text: apimgmt api operation delete  --resource-group rg1 --service-name apimService1 --api-id PetStoreTemplate2 --operation-id newoperations
      - name: ApiManagementUpdateApiOperation
        text: apimgmt api operation delete  --resource-group rg1 --service-name apimService1 --api-id echo-api --operation-id operationId
      - name: ApiManagementDeleteApiOperation
        text: apimgmt api operation delete  --resource-group rg1 --service-name apimService1 --api-id 57d2ef278aa04f0888cba3f3 --operation-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api operation list'] = """
    type: command
    short-summary: list a apimgmt api operation.
    examples:
# list_by_api -- list
      - name: ApiManagementCreateApiOperation
        text: apimgmt api operation list  --resource-group rg1 --service-name apimService1 --api-id PetStoreTemplate2
      - name: ApiManagementUpdateApiOperation
        text: apimgmt api operation list  --resource-group rg1 --service-name apimService1 --api-id echo-api
      - name: ApiManagementDeleteApiOperation
        text: apimgmt api operation list  --resource-group rg1 --service-name apimService1 --api-id 57d2ef278aa04f0888cba3f3
"""

helps['apimgmt api operation show'] = """
    type: command
    short-summary: show a apimgmt api operation.
    examples:
# get -- show
      - name: ApiManagementCreateApiOperation
        text: apimgmt api operation show  --resource-group rg1 --service-name apimService1 --api-id PetStoreTemplate2 --operation-id newoperations
      - name: ApiManagementUpdateApiOperation
        text: apimgmt api operation show  --resource-group rg1 --service-name apimService1 --api-id echo-api --operation-id operationId
      - name: ApiManagementDeleteApiOperation
        text: apimgmt api operation show  --resource-group rg1 --service-name apimService1 --api-id 57d2ef278aa04f0888cba3f3 --operation-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api operation policy'] = """
    type: group
    short-summary: Commands to manage ApiOperationPolicy.
"""

helps['apimgmt api operation policy create'] = """
    type: command
    short-summary: create a apimgmt api operation policy.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiOperationPolicy
        text: apimgmt api operation policy create  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --operation-id 5600b57e7e8880006a080001 --policy-id policy --value <policies> <inbound /> <backend>    <forward-request />  </backend>  <outbound /></policies> --format xml
      - name: ApiManagementDeleteApiOperationPolicy
        text: apimgmt api operation policy create  --resource-group rg1 --service-name apimService1 --api-id testapi --operation-id testoperation --policy-id policy
"""

helps['apimgmt api operation policy update'] = """
    type: command
    short-summary: update a apimgmt api operation policy.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiOperationPolicy
        text: apimgmt api operation policy update  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --operation-id 5600b57e7e8880006a080001 --policy-id policy --value <policies> <inbound /> <backend>    <forward-request />  </backend>  <outbound /></policies> --format xml
      - name: ApiManagementDeleteApiOperationPolicy
        text: apimgmt api operation policy update  --resource-group rg1 --service-name apimService1 --api-id testapi --operation-id testoperation --policy-id policy
"""

helps['apimgmt api operation policy delete'] = """
    type: command
    short-summary: delete a apimgmt api operation policy.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiOperationPolicy
        text: apimgmt api operation policy delete  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --operation-id 5600b57e7e8880006a080001 --policy-id policy
      - name: ApiManagementDeleteApiOperationPolicy
        text: apimgmt api operation policy delete  --resource-group rg1 --service-name apimService1 --api-id testapi --operation-id testoperation --policy-id policy
"""

helps['apimgmt api operation policy list'] = """
    type: command
    short-summary: list a apimgmt api operation policy.
    examples:
# list_by_operation -- list
      - name: ApiManagementCreateApiOperationPolicy
        text: apimgmt api operation policy list  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --operation-id 5600b57e7e8880006a080001
      - name: ApiManagementDeleteApiOperationPolicy
        text: apimgmt api operation policy list  --resource-group rg1 --service-name apimService1 --api-id testapi --operation-id testoperation
"""

helps['apimgmt api operation policy show'] = """
    type: command
    short-summary: show a apimgmt api operation policy.
    examples:
# get -- show
      - name: ApiManagementCreateApiOperationPolicy
        text: apimgmt api operation policy show  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --operation-id 5600b57e7e8880006a080001 --format xml --policy-id policy
      - name: ApiManagementDeleteApiOperationPolicy
        text: apimgmt api operation policy show  --resource-group rg1 --service-name apimService1 --api-id testapi --operation-id testoperation --policy-id policy
"""

helps['apimgmt tag'] = """
    type: group
    short-summary: Commands to manage Tag.
"""

helps['apimgmt tag create'] = """
    type: command
    short-summary: create a apimgmt tag.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateTag
        text: apimgmt tag create  --resource-group rg1 --service-name apimService1 --tag-id tagId1 --display-name tag1
      - name: ApiManagementUpdateTag
        text: apimgmt tag create  --resource-group rg1 --service-name apimService1 --tag-id temptag --display-name temp tag
      - name: ApiManagementDeleteTag
        text: apimgmt tag create  --resource-group rg1 --service-name apimService1 --tag-id tagId1
"""

helps['apimgmt tag update'] = """
    type: command
    short-summary: update a apimgmt tag.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateTag
        text: apimgmt tag update  --resource-group rg1 --service-name apimService1 --tag-id tagId1 --display-name tag1
      - name: ApiManagementUpdateTag
        text: apimgmt tag update  --resource-group rg1 --service-name apimService1 --tag-id temptag --display-name temp tag
      - name: ApiManagementDeleteTag
        text: apimgmt tag update  --resource-group rg1 --service-name apimService1 --tag-id tagId1
"""

helps['apimgmt tag delete'] = """
    type: command
    short-summary: delete a apimgmt tag.
    examples:
# delete -- delete
      - name: ApiManagementCreateTag
        text: apimgmt tag delete  --resource-group rg1 --service-name apimService1 --tag-id tagId1
      - name: ApiManagementUpdateTag
        text: apimgmt tag delete  --resource-group rg1 --service-name apimService1 --tag-id temptag
      - name: ApiManagementDeleteTag
        text: apimgmt tag delete  --resource-group rg1 --service-name apimService1 --tag-id tagId1
"""

helps['apimgmt tag list'] = """
    type: command
    short-summary: list a apimgmt tag.
    examples:
# list_by_operation -- list
      - name: ApiManagementCreateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
# list_by_product -- list
      - name: ApiManagementCreateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
# list_by_api -- list
      - name: ApiManagementCreateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
# list_by_service -- list
      - name: ApiManagementCreateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteTag
        text: apimgmt tag list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt tag show'] = """
    type: command
    short-summary: show a apimgmt tag.
    examples:
# get -- show
      - name: ApiManagementCreateTag
        text: apimgmt tag show  --resource-group rg1 --service-name apimService1 --tag-id tagId1
      - name: ApiManagementUpdateTag
        text: apimgmt tag show  --resource-group rg1 --service-name apimService1 --tag-id temptag
      - name: ApiManagementDeleteTag
        text: apimgmt tag show  --resource-group rg1 --service-name apimService1 --tag-id tagId1
"""

helps['apimgmt api policy'] = """
    type: group
    short-summary: Commands to manage ApiPolicy.
"""

helps['apimgmt api policy create'] = """
    type: command
    short-summary: create a apimgmt api policy.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiPolicy
        text: apimgmt api policy create  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy --value <policies> <inbound /> <backend>    <forward-request />  </backend>  <outbound /></policies> --format xml
      - name: ApiManagementCreateApiPolicyNonXmlEncoded
        text: apimgmt api policy create  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy --value <policies>
     <inbound>
     <base />
  <set-header name="newvalue" exists-action="override">
   <value>"@(context.Request.Headers.FirstOrDefault(h => h.Ke=="Via"))" </value>
    </set-header>
  </inbound>
      </policies> --format rawxml
      - name: ApiManagementDeleteApiPolicy
        text: apimgmt api policy create  --resource-group rg1 --service-name apimService1 --api-id loggerId --policy-id policy
"""

helps['apimgmt api policy update'] = """
    type: command
    short-summary: update a apimgmt api policy.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiPolicy
        text: apimgmt api policy update  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy --value <policies> <inbound /> <backend>    <forward-request />  </backend>  <outbound /></policies> --format xml
      - name: ApiManagementCreateApiPolicyNonXmlEncoded
        text: apimgmt api policy update  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy --value <policies>
     <inbound>
     <base />
  <set-header name="newvalue" exists-action="override">
   <value>"@(context.Request.Headers.FirstOrDefault(h => h.Ke=="Via"))" </value>
    </set-header>
  </inbound>
      </policies> --format rawxml
      - name: ApiManagementDeleteApiPolicy
        text: apimgmt api policy update  --resource-group rg1 --service-name apimService1 --api-id loggerId --policy-id policy
"""

helps['apimgmt api policy delete'] = """
    type: command
    short-summary: delete a apimgmt api policy.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiPolicy
        text: apimgmt api policy delete  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy
      - name: ApiManagementCreateApiPolicyNonXmlEncoded
        text: apimgmt api policy delete  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy
      - name: ApiManagementDeleteApiPolicy
        text: apimgmt api policy delete  --resource-group rg1 --service-name apimService1 --api-id loggerId --policy-id policy
"""

helps['apimgmt api policy list'] = """
    type: command
    short-summary: list a apimgmt api policy.
    examples:
# list_by_api -- list
      - name: ApiManagementCreateApiPolicy
        text: apimgmt api policy list  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001
      - name: ApiManagementCreateApiPolicyNonXmlEncoded
        text: apimgmt api policy list  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001
      - name: ApiManagementDeleteApiPolicy
        text: apimgmt api policy list  --resource-group rg1 --service-name apimService1 --api-id loggerId
"""

helps['apimgmt api policy show'] = """
    type: command
    short-summary: show a apimgmt api policy.
    examples:
# get -- show
      - name: ApiManagementCreateApiPolicy
        text: apimgmt api policy show  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy --format xml
      - name: ApiManagementCreateApiPolicyNonXmlEncoded
        text: apimgmt api policy show  --resource-group rg1 --service-name apimService1 --api-id 5600b57e7e8880006a040001 --policy-id policy --format rawxml
      - name: ApiManagementDeleteApiPolicy
        text: apimgmt api policy show  --resource-group rg1 --service-name apimService1 --api-id loggerId --policy-id policy
"""

helps['apimgmt api schema'] = """
    type: group
    short-summary: Commands to manage ApiSchema.
"""

helps['apimgmt api schema create'] = """
    type: command
    short-summary: create a apimgmt api schema.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiSchema
        text: apimgmt api schema create  --resource-group rg1 --service-name apimService1 --api-id 59d6bb8f1f7fab13dc67ec9b --schema-id ec12520d-9d48-4e7b-8f39-698ca2ac63f1 --content-type application/vnd.ms-azure-apim.xsd+xml
      - name: ApiManagementDeleteApiSchema
        text: apimgmt api schema create  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --schema-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api schema update'] = """
    type: command
    short-summary: update a apimgmt api schema.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiSchema
        text: apimgmt api schema update  --resource-group rg1 --service-name apimService1 --api-id 59d6bb8f1f7fab13dc67ec9b --schema-id ec12520d-9d48-4e7b-8f39-698ca2ac63f1 --content-type application/vnd.ms-azure-apim.xsd+xml
      - name: ApiManagementDeleteApiSchema
        text: apimgmt api schema update  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --schema-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api schema delete'] = """
    type: command
    short-summary: delete a apimgmt api schema.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiSchema
        text: apimgmt api schema delete  --resource-group rg1 --service-name apimService1 --api-id 59d6bb8f1f7fab13dc67ec9b --schema-id ec12520d-9d48-4e7b-8f39-698ca2ac63f1
      - name: ApiManagementDeleteApiSchema
        text: apimgmt api schema delete  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --schema-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api schema list'] = """
    type: command
    short-summary: list a apimgmt api schema.
    examples:
# list_by_api -- list
      - name: ApiManagementCreateApiSchema
        text: apimgmt api schema list  --resource-group rg1 --service-name apimService1 --api-id 59d6bb8f1f7fab13dc67ec9b
      - name: ApiManagementDeleteApiSchema
        text: apimgmt api schema list  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650
"""

helps['apimgmt api schema show'] = """
    type: command
    short-summary: show a apimgmt api schema.
    examples:
# get -- show
      - name: ApiManagementCreateApiSchema
        text: apimgmt api schema show  --resource-group rg1 --service-name apimService1 --api-id 59d6bb8f1f7fab13dc67ec9b --schema-id ec12520d-9d48-4e7b-8f39-698ca2ac63f1
      - name: ApiManagementDeleteApiSchema
        text: apimgmt api schema show  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --schema-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api diagnostic'] = """
    type: group
    short-summary: Commands to manage ApiDiagnostic.
"""

helps['apimgmt api diagnostic create'] = """
    type: command
    short-summary: create a apimgmt api diagnostic.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiDiagnostic
        text: apimgmt api diagnostic create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/applicationinsights
      - name: ApiManagementUpdateApiDiagnostic
        text: apimgmt api diagnostic create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/applicationinsights
      - name: ApiManagementDeleteApiDiagnostic
        text: apimgmt api diagnostic create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
"""

helps['apimgmt api diagnostic update'] = """
    type: command
    short-summary: update a apimgmt api diagnostic.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiDiagnostic
        text: apimgmt api diagnostic update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/applicationinsights
      - name: ApiManagementUpdateApiDiagnostic
        text: apimgmt api diagnostic update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/applicationinsights
      - name: ApiManagementDeleteApiDiagnostic
        text: apimgmt api diagnostic update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
"""

helps['apimgmt api diagnostic delete'] = """
    type: command
    short-summary: delete a apimgmt api diagnostic.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiDiagnostic
        text: apimgmt api diagnostic delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
      - name: ApiManagementUpdateApiDiagnostic
        text: apimgmt api diagnostic delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
      - name: ApiManagementDeleteApiDiagnostic
        text: apimgmt api diagnostic delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
"""

helps['apimgmt api diagnostic list'] = """
    type: command
    short-summary: list a apimgmt api diagnostic.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiDiagnostic
        text: apimgmt api diagnostic list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a
      - name: ApiManagementUpdateApiDiagnostic
        text: apimgmt api diagnostic list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a
      - name: ApiManagementDeleteApiDiagnostic
        text: apimgmt api diagnostic list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a
"""

helps['apimgmt api diagnostic show'] = """
    type: command
    short-summary: show a apimgmt api diagnostic.
    examples:
# get -- show
      - name: ApiManagementCreateApiDiagnostic
        text: apimgmt api diagnostic show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
      - name: ApiManagementUpdateApiDiagnostic
        text: apimgmt api diagnostic show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
      - name: ApiManagementDeleteApiDiagnostic
        text: apimgmt api diagnostic show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --diagnostic-id applicationinsights
"""

helps['apimgmt api issue'] = """
    type: group
    short-summary: Commands to manage ApiIssue.
"""

helps['apimgmt api issue create'] = """
    type: command
    short-summary: create a apimgmt api issue.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiIssue
        text: apimgmt api issue create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --created-date 2018-02-01T22:21:20.467Z --state open --title New API issue --description New API issue description --user-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{ user_name }}
      - name: ApiManagementUpdateApiIssue
        text: apimgmt api issue create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --state closed
      - name: ApiManagementDeleteApiIssue
        text: apimgmt api issue create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api issue update'] = """
    type: command
    short-summary: update a apimgmt api issue.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiIssue
        text: apimgmt api issue update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --created-date 2018-02-01T22:21:20.467Z --state open --title New API issue --description New API issue description --user-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{ user_name }}
      - name: ApiManagementUpdateApiIssue
        text: apimgmt api issue update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --state closed
      - name: ApiManagementDeleteApiIssue
        text: apimgmt api issue update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api issue delete'] = """
    type: command
    short-summary: delete a apimgmt api issue.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiIssue
        text: apimgmt api issue delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
      - name: ApiManagementUpdateApiIssue
        text: apimgmt api issue delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
      - name: ApiManagementDeleteApiIssue
        text: apimgmt api issue delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api issue list'] = """
    type: command
    short-summary: list a apimgmt api issue.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiIssue
        text: apimgmt api issue list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a
      - name: ApiManagementUpdateApiIssue
        text: apimgmt api issue list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a
      - name: ApiManagementDeleteApiIssue
        text: apimgmt api issue list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a
"""

helps['apimgmt api issue show'] = """
    type: command
    short-summary: show a apimgmt api issue.
    examples:
# get -- show
      - name: ApiManagementCreateApiIssue
        text: apimgmt api issue show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
      - name: ApiManagementUpdateApiIssue
        text: apimgmt api issue show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
      - name: ApiManagementDeleteApiIssue
        text: apimgmt api issue show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api issue comment'] = """
    type: group
    short-summary: Commands to manage ApiIssueComment.
"""

helps['apimgmt api issue comment create'] = """
    type: command
    short-summary: create a apimgmt api issue comment.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiIssueComment
        text: apimgmt api issue comment create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb --text Issue comment. --created-date 2018-02-01T22:21:20.467Z --user-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{ user_name }}
      - name: ApiManagementDeleteApiIssueComment
        text: apimgmt api issue comment create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb
"""

helps['apimgmt api issue comment update'] = """
    type: command
    short-summary: update a apimgmt api issue comment.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiIssueComment
        text: apimgmt api issue comment update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb --text Issue comment. --created-date 2018-02-01T22:21:20.467Z --user-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{ user_name }}
      - name: ApiManagementDeleteApiIssueComment
        text: apimgmt api issue comment update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb
"""

helps['apimgmt api issue comment delete'] = """
    type: command
    short-summary: delete a apimgmt api issue comment.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiIssueComment
        text: apimgmt api issue comment delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb
      - name: ApiManagementDeleteApiIssueComment
        text: apimgmt api issue comment delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb
"""

helps['apimgmt api issue comment list'] = """
    type: command
    short-summary: list a apimgmt api issue comment.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiIssueComment
        text: apimgmt api issue comment list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
      - name: ApiManagementDeleteApiIssueComment
        text: apimgmt api issue comment list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api issue comment show'] = """
    type: command
    short-summary: show a apimgmt api issue comment.
    examples:
# get -- show
      - name: ApiManagementCreateApiIssueComment
        text: apimgmt api issue comment show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb
      - name: ApiManagementDeleteApiIssueComment
        text: apimgmt api issue comment show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --comment-id 599e29ab193c3c0bd0b3e2fb
"""

helps['apimgmt api issue attachment'] = """
    type: group
    short-summary: Commands to manage ApiIssueAttachment.
"""

helps['apimgmt api issue attachment create'] = """
    type: command
    short-summary: create a apimgmt api issue attachment.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiIssueAttachment
        text: apimgmt api issue attachment create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3 --title Issue attachment. --content-format image/jpeg --content IEJhc2U2NA==
      - name: ApiManagementDeleteApiIssueAttachment
        text: apimgmt api issue attachment create  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3
"""

helps['apimgmt api issue attachment update'] = """
    type: command
    short-summary: update a apimgmt api issue attachment.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiIssueAttachment
        text: apimgmt api issue attachment update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3 --title Issue attachment. --content-format image/jpeg --content IEJhc2U2NA==
      - name: ApiManagementDeleteApiIssueAttachment
        text: apimgmt api issue attachment update  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3
"""

helps['apimgmt api issue attachment delete'] = """
    type: command
    short-summary: delete a apimgmt api issue attachment.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiIssueAttachment
        text: apimgmt api issue attachment delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3
      - name: ApiManagementDeleteApiIssueAttachment
        text: apimgmt api issue attachment delete  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3
"""

helps['apimgmt api issue attachment list'] = """
    type: command
    short-summary: list a apimgmt api issue attachment.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiIssueAttachment
        text: apimgmt api issue attachment list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
      - name: ApiManagementDeleteApiIssueAttachment
        text: apimgmt api issue attachment list  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc
"""

helps['apimgmt api issue attachment show'] = """
    type: command
    short-summary: show a apimgmt api issue attachment.
    examples:
# get -- show
      - name: ApiManagementCreateApiIssueAttachment
        text: apimgmt api issue attachment show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3
      - name: ApiManagementDeleteApiIssueAttachment
        text: apimgmt api issue attachment show  --resource-group rg1 --service-name apimService1 --api-id 57d1f7558aa04f15146d9d8a --issue-id 57d2ef278aa04f0ad01d6cdc --attachment-id 57d2ef278aa04f0888cba3f3
"""

helps['apimgmt api tagdescription'] = """
    type: group
    short-summary: Commands to manage ApiTagDescription.
"""

helps['apimgmt api tagdescription create'] = """
    type: command
    short-summary: create a apimgmt api tagdescription.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiTagDescription
        text: apimgmt api tagdescription create  --resource-group rg1 --service-name apimService1 --api-id 5931a75ae4bbd512a88c680b --tag-id tagId1 --description Some description that will be displayed for operation's tag if the tag is assigned to operation of the API --external-docs_url http://some.url/additionaldoc --external-docs_description Description of the external docs resource
      - name: ApiManagementDeleteApiTagDescription
        text: apimgmt api tagdescription create  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --tag-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api tagdescription update'] = """
    type: command
    short-summary: update a apimgmt api tagdescription.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiTagDescription
        text: apimgmt api tagdescription update  --resource-group rg1 --service-name apimService1 --api-id 5931a75ae4bbd512a88c680b --tag-id tagId1 --description Some description that will be displayed for operation's tag if the tag is assigned to operation of the API --external-docs_url http://some.url/additionaldoc --external-docs_description Description of the external docs resource
      - name: ApiManagementDeleteApiTagDescription
        text: apimgmt api tagdescription update  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --tag-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api tagdescription delete'] = """
    type: command
    short-summary: delete a apimgmt api tagdescription.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiTagDescription
        text: apimgmt api tagdescription delete  --resource-group rg1 --service-name apimService1 --api-id 5931a75ae4bbd512a88c680b --tag-id tagId1
      - name: ApiManagementDeleteApiTagDescription
        text: apimgmt api tagdescription delete  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --tag-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt api tagdescription list'] = """
    type: command
    short-summary: list a apimgmt api tagdescription.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiTagDescription
        text: apimgmt api tagdescription list  --resource-group rg1 --service-name apimService1 --api-id 5931a75ae4bbd512a88c680b
      - name: ApiManagementDeleteApiTagDescription
        text: apimgmt api tagdescription list  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650
"""

helps['apimgmt api tagdescription show'] = """
    type: command
    short-summary: show a apimgmt api tagdescription.
    examples:
# get -- show
      - name: ApiManagementCreateApiTagDescription
        text: apimgmt api tagdescription show  --resource-group rg1 --service-name apimService1 --api-id 5931a75ae4bbd512a88c680b --tag-id tagId1
      - name: ApiManagementDeleteApiTagDescription
        text: apimgmt api tagdescription show  --resource-group rg1 --service-name apimService1 --api-id 59d5b28d1f7fab116c282650 --tag-id 59d5b28e1f7fab116402044e
"""

helps['apimgmt apiversionset'] = """
    type: group
    short-summary: Commands to manage ApiVersionSet.
"""

helps['apimgmt apiversionset create'] = """
    type: command
    short-summary: create a apimgmt apiversionset.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateApiVersionSet
        text: apimgmt apiversionset create  --resource-group rg1 --service-name apimService1 --version-set_id api1 --description Version configuration --display-name api set 1 --versioning-scheme Segment
      - name: ApiManagementUpdateApiVersionSet
        text: apimgmt apiversionset create  --resource-group rg1 --service-name apimService1 --version-set_id api1 --description Version configuration --display-name api set 1 --versioning-scheme Segment
      - name: ApiManagementDeleteApiVersionSet
        text: apimgmt apiversionset create  --resource-group rg1 --service-name apimService1 --version-set_id a1
"""

helps['apimgmt apiversionset update'] = """
    type: command
    short-summary: update a apimgmt apiversionset.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateApiVersionSet
        text: apimgmt apiversionset update  --resource-group rg1 --service-name apimService1 --version-set_id api1 --description Version configuration --display-name api set 1 --versioning-scheme Segment
      - name: ApiManagementUpdateApiVersionSet
        text: apimgmt apiversionset update  --resource-group rg1 --service-name apimService1 --version-set_id api1 --description Version configuration --display-name api set 1 --versioning-scheme Segment
      - name: ApiManagementDeleteApiVersionSet
        text: apimgmt apiversionset update  --resource-group rg1 --service-name apimService1 --version-set_id a1
"""

helps['apimgmt apiversionset delete'] = """
    type: command
    short-summary: delete a apimgmt apiversionset.
    examples:
# delete -- delete
      - name: ApiManagementCreateApiVersionSet
        text: apimgmt apiversionset delete  --resource-group rg1 --service-name apimService1 --version-set_id api1
      - name: ApiManagementUpdateApiVersionSet
        text: apimgmt apiversionset delete  --resource-group rg1 --service-name apimService1 --version-set_id api1
      - name: ApiManagementDeleteApiVersionSet
        text: apimgmt apiversionset delete  --resource-group rg1 --service-name apimService1 --version-set_id a1
"""

helps['apimgmt apiversionset list'] = """
    type: command
    short-summary: list a apimgmt apiversionset.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateApiVersionSet
        text: apimgmt apiversionset list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateApiVersionSet
        text: apimgmt apiversionset list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteApiVersionSet
        text: apimgmt apiversionset list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt apiversionset show'] = """
    type: command
    short-summary: show a apimgmt apiversionset.
    examples:
# get -- show
      - name: ApiManagementCreateApiVersionSet
        text: apimgmt apiversionset show  --resource-group rg1 --service-name apimService1 --version-set_id api1
      - name: ApiManagementUpdateApiVersionSet
        text: apimgmt apiversionset show  --resource-group rg1 --service-name apimService1 --version-set_id api1
      - name: ApiManagementDeleteApiVersionSet
        text: apimgmt apiversionset show  --resource-group rg1 --service-name apimService1 --version-set_id a1
"""

helps['apimgmt authorizationserver'] = """
    type: group
    short-summary: Commands to manage AuthorizationServer.
"""

helps['apimgmt authorizationserver create'] = """
    type: command
    short-summary: create a apimgmt authorizationserver.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateAuthorizationServer
        text: apimgmt authorizationserver create  --resource-group rg1 --service-name apimService1 --authsid newauthServer --description test server --token-endpoint https://www.contoso.com/oauth2/token --support-state true --default-scope read write --client-secret 2 --resource-owner_username un --resource-owner_password pwd --display-name test2 --client-registration_endpoint https://www.contoso.com/apps --authorization-endpoint https://www.contoso.com/oauth2/auth --client-id 1
      - name: ApiManagementUpdateAuthorizationServer
        text: apimgmt authorizationserver create  --resource-group rg1 --service-name apimService1 --authsid newauthServer --client-secret updated --client-id update
      - name: ApiManagementDeleteAuthorizationServer
        text: apimgmt authorizationserver create  --resource-group rg1 --service-name apimService1 --authsid newauthServer2
"""

helps['apimgmt authorizationserver update'] = """
    type: command
    short-summary: update a apimgmt authorizationserver.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateAuthorizationServer
        text: apimgmt authorizationserver update  --resource-group rg1 --service-name apimService1 --authsid newauthServer --description test server --token-endpoint https://www.contoso.com/oauth2/token --support-state true --default-scope read write --client-secret 2 --resource-owner_username un --resource-owner_password pwd --display-name test2 --client-registration_endpoint https://www.contoso.com/apps --authorization-endpoint https://www.contoso.com/oauth2/auth --client-id 1
      - name: ApiManagementUpdateAuthorizationServer
        text: apimgmt authorizationserver update  --resource-group rg1 --service-name apimService1 --authsid newauthServer --client-secret updated --client-id update
      - name: ApiManagementDeleteAuthorizationServer
        text: apimgmt authorizationserver update  --resource-group rg1 --service-name apimService1 --authsid newauthServer2
"""

helps['apimgmt authorizationserver delete'] = """
    type: command
    short-summary: delete a apimgmt authorizationserver.
    examples:
# delete -- delete
      - name: ApiManagementCreateAuthorizationServer
        text: apimgmt authorizationserver delete  --resource-group rg1 --service-name apimService1 --authsid newauthServer
      - name: ApiManagementUpdateAuthorizationServer
        text: apimgmt authorizationserver delete  --resource-group rg1 --service-name apimService1 --authsid newauthServer
      - name: ApiManagementDeleteAuthorizationServer
        text: apimgmt authorizationserver delete  --resource-group rg1 --service-name apimService1 --authsid newauthServer2
"""

helps['apimgmt authorizationserver list'] = """
    type: command
    short-summary: list a apimgmt authorizationserver.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateAuthorizationServer
        text: apimgmt authorizationserver list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateAuthorizationServer
        text: apimgmt authorizationserver list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteAuthorizationServer
        text: apimgmt authorizationserver list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt authorizationserver show'] = """
    type: command
    short-summary: show a apimgmt authorizationserver.
    examples:
# get -- show
      - name: ApiManagementCreateAuthorizationServer
        text: apimgmt authorizationserver show  --resource-group rg1 --service-name apimService1 --authsid newauthServer
      - name: ApiManagementUpdateAuthorizationServer
        text: apimgmt authorizationserver show  --resource-group rg1 --service-name apimService1 --authsid newauthServer
      - name: ApiManagementDeleteAuthorizationServer
        text: apimgmt authorizationserver show  --resource-group rg1 --service-name apimService1 --authsid newauthServer2
"""

helps['apimgmt backend'] = """
    type: group
    short-summary: Commands to manage Backend.
"""

helps['apimgmt backend create'] = """
    type: command
    short-summary: create a apimgmt backend.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateBackendServiceFabric
        text: apimgmt backend create  --resource-group rg1 --service-name apimService1 --backend-id sfbackend --description Service Fabric Test App 1 --url fabric:/mytestapp/mytestservice --protocol http
      - name: ApiManagementCreateBackendProxyBackend
        text: apimgmt backend create  --resource-group rg1 --service-name apimService1 --backend-id proxybackend --description description5308 --url https://backendname2644/ --protocol http
      - name: ApiManagementUpdateBackend
        text: apimgmt backend create  --resource-group rg1 --service-name apimService1 --backend-id proxybackend --description description5308
      - name: ApiManagementDeleteBackend
        text: apimgmt backend create  --resource-group rg1 --service-name apimService1 --backend-id sfbackend
"""

helps['apimgmt backend update'] = """
    type: command
    short-summary: update a apimgmt backend.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateBackendServiceFabric
        text: apimgmt backend update  --resource-group rg1 --service-name apimService1 --backend-id sfbackend --description Service Fabric Test App 1 --url fabric:/mytestapp/mytestservice --protocol http
      - name: ApiManagementCreateBackendProxyBackend
        text: apimgmt backend update  --resource-group rg1 --service-name apimService1 --backend-id proxybackend --description description5308 --url https://backendname2644/ --protocol http
      - name: ApiManagementUpdateBackend
        text: apimgmt backend update  --resource-group rg1 --service-name apimService1 --backend-id proxybackend --description description5308
      - name: ApiManagementDeleteBackend
        text: apimgmt backend update  --resource-group rg1 --service-name apimService1 --backend-id sfbackend
"""

helps['apimgmt backend delete'] = """
    type: command
    short-summary: delete a apimgmt backend.
    examples:
# delete -- delete
      - name: ApiManagementCreateBackendServiceFabric
        text: apimgmt backend delete  --resource-group rg1 --service-name apimService1 --backend-id sfbackend
      - name: ApiManagementCreateBackendProxyBackend
        text: apimgmt backend delete  --resource-group rg1 --service-name apimService1 --backend-id proxybackend
      - name: ApiManagementUpdateBackend
        text: apimgmt backend delete  --resource-group rg1 --service-name apimService1 --backend-id proxybackend
      - name: ApiManagementDeleteBackend
        text: apimgmt backend delete  --resource-group rg1 --service-name apimService1 --backend-id sfbackend
"""

helps['apimgmt backend list'] = """
    type: command
    short-summary: list a apimgmt backend.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateBackendServiceFabric
        text: apimgmt backend list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateBackendProxyBackend
        text: apimgmt backend list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateBackend
        text: apimgmt backend list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteBackend
        text: apimgmt backend list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt backend show'] = """
    type: command
    short-summary: show a apimgmt backend.
    examples:
# get -- show
      - name: ApiManagementCreateBackendServiceFabric
        text: apimgmt backend show  --resource-group rg1 --service-name apimService1 --backend-id sfbackend
      - name: ApiManagementCreateBackendProxyBackend
        text: apimgmt backend show  --resource-group rg1 --service-name apimService1 --backend-id proxybackend
      - name: ApiManagementUpdateBackend
        text: apimgmt backend show  --resource-group rg1 --service-name apimService1 --backend-id proxybackend
      - name: ApiManagementDeleteBackend
        text: apimgmt backend show  --resource-group rg1 --service-name apimService1 --backend-id sfbackend
"""

helps['apimgmt cache'] = """
    type: group
    short-summary: Commands to manage Cache.
"""

helps['apimgmt cache create'] = """
    type: command
    short-summary: create a apimgmt cache.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateCache
        text: apimgmt cache create  --resource-group rg1 --service-name apimService1 --cache-id westindia --description Redis cache instances in West India --connection-string contoso5.redis.cache.windows.net,ssl=true,password=... --resource-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.Cache/Redis/{{ redis_name }}
      - name: ApiManagementUpdateCache
        text: apimgmt cache create  --resource-group rg1 --service-name apimService1 --cache-id westindia --description Update Cache in west India
      - name: ApiManagementDeleteCache
        text: apimgmt cache create  --resource-group rg1 --service-name apimService1 --cache-id southindia
"""

helps['apimgmt cache update'] = """
    type: command
    short-summary: update a apimgmt cache.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateCache
        text: apimgmt cache update  --resource-group rg1 --service-name apimService1 --cache-id westindia --description Redis cache instances in West India --connection-string contoso5.redis.cache.windows.net,ssl=true,password=... --resource-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.Cache/Redis/{{ redis_name }}
      - name: ApiManagementUpdateCache
        text: apimgmt cache update  --resource-group rg1 --service-name apimService1 --cache-id westindia --description Update Cache in west India
      - name: ApiManagementDeleteCache
        text: apimgmt cache update  --resource-group rg1 --service-name apimService1 --cache-id southindia
"""

helps['apimgmt cache delete'] = """
    type: command
    short-summary: delete a apimgmt cache.
    examples:
# delete -- delete
      - name: ApiManagementCreateCache
        text: apimgmt cache delete  --resource-group rg1 --service-name apimService1 --cache-id westindia
      - name: ApiManagementUpdateCache
        text: apimgmt cache delete  --resource-group rg1 --service-name apimService1 --cache-id westindia
      - name: ApiManagementDeleteCache
        text: apimgmt cache delete  --resource-group rg1 --service-name apimService1 --cache-id southindia
"""

helps['apimgmt cache list'] = """
    type: command
    short-summary: list a apimgmt cache.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateCache
        text: apimgmt cache list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateCache
        text: apimgmt cache list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteCache
        text: apimgmt cache list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt cache show'] = """
    type: command
    short-summary: show a apimgmt cache.
    examples:
# get -- show
      - name: ApiManagementCreateCache
        text: apimgmt cache show  --resource-group rg1 --service-name apimService1 --cache-id westindia
      - name: ApiManagementUpdateCache
        text: apimgmt cache show  --resource-group rg1 --service-name apimService1 --cache-id westindia
      - name: ApiManagementDeleteCache
        text: apimgmt cache show  --resource-group rg1 --service-name apimService1 --cache-id southindia
"""

helps['apimgmt certificate'] = """
    type: group
    short-summary: Commands to manage Certificate.
"""

helps['apimgmt certificate create'] = """
    type: command
    short-summary: create a apimgmt certificate.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateCertificate
        text: apimgmt certificate create  --resource-group rg1 --service-name apimService1 --certificate-id tempcert --data ****************Base 64 Encoded Certificate ******************************* --password ****Certificate Password******
      - name: ApiManagementDeleteCertificate
        text: apimgmt certificate create  --resource-group rg1 --service-name apimService1 --certificate-id tempcert
"""

helps['apimgmt certificate update'] = """
    type: command
    short-summary: update a apimgmt certificate.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateCertificate
        text: apimgmt certificate update  --resource-group rg1 --service-name apimService1 --certificate-id tempcert --data ****************Base 64 Encoded Certificate ******************************* --password ****Certificate Password******
      - name: ApiManagementDeleteCertificate
        text: apimgmt certificate update  --resource-group rg1 --service-name apimService1 --certificate-id tempcert
"""

helps['apimgmt certificate delete'] = """
    type: command
    short-summary: delete a apimgmt certificate.
    examples:
# delete -- delete
      - name: ApiManagementCreateCertificate
        text: apimgmt certificate delete  --resource-group rg1 --service-name apimService1 --certificate-id tempcert
      - name: ApiManagementDeleteCertificate
        text: apimgmt certificate delete  --resource-group rg1 --service-name apimService1 --certificate-id tempcert
"""

helps['apimgmt certificate list'] = """
    type: command
    short-summary: list a apimgmt certificate.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateCertificate
        text: apimgmt certificate list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteCertificate
        text: apimgmt certificate list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt certificate show'] = """
    type: command
    short-summary: show a apimgmt certificate.
    examples:
# get -- show
      - name: ApiManagementCreateCertificate
        text: apimgmt certificate show  --resource-group rg1 --service-name apimService1 --certificate-id tempcert
      - name: ApiManagementDeleteCertificate
        text: apimgmt certificate show  --resource-group rg1 --service-name apimService1 --certificate-id tempcert
"""

helps['apimgmt'] = """
    type: group
    short-summary: Commands to manage ApiManagementService.
"""

helps['apimgmt create'] = """
    type: command
    short-summary: create a apimgmt.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateService
        text: apimgmt create  --resource-group rg1 --name apimService1 --publisher-email apim@autorestsdk.com --publisher-name autorestsdk --sku-name Developer --sku-capacity 1 --location Central US
      - name: ApiManagementCreateMultiRegionServiceWithCustomHostname
        text: apimgmt create  --resource-group rg1 --name apimService1 --virtual-network_type External --publisher-email admin@live.com --publisher-name contoso --sku-name Premium --sku-capacity 1 --location Central US
      - name: ApiManagementCreateServiceHavingMsi
        text: apimgmt create  --resource-group rg1 --name apimService1 --publisher-email apim@autorestsdk.com --publisher-name autorestsdk --sku-name Consumption --location West US
      - name: ApiManagementCreateServiceWithSystemCertificates
        text: apimgmt create  --resource-group rg1 --name apimService1 --publisher-email apim@autorestsdk.com --publisher-name autorestsdk --sku-name Basic --sku-capacity 1 --location Central US
      - name: ApiManagementUpdateServiceDisableTls10
        text: apimgmt create  --resource-group rg1 --name apimService1
      - name: ApiManagementUpdateServicePublisherDetails
        text: apimgmt create  --resource-group rg1 --name apimService1 --publisher-email foobar@live.com --publisher-name Contoso Vnext
      - name: ApiManagementServiceDeleteService
        text: apimgmt create  --resource-group rg1 --name apimService1
"""

helps['apimgmt update'] = """
    type: command
    short-summary: update a apimgmt.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateService
        text: apimgmt update  --resource-group rg1 --name apimService1 --publisher-email apim@autorestsdk.com --publisher-name autorestsdk --sku-name Developer --sku-capacity 1 --location Central US
      - name: ApiManagementCreateMultiRegionServiceWithCustomHostname
        text: apimgmt update  --resource-group rg1 --name apimService1 --virtual-network_type External --publisher-email admin@live.com --publisher-name contoso --sku-name Premium --sku-capacity 1 --location Central US
      - name: ApiManagementCreateServiceHavingMsi
        text: apimgmt update  --resource-group rg1 --name apimService1 --publisher-email apim@autorestsdk.com --publisher-name autorestsdk --sku-name Consumption --location West US
      - name: ApiManagementCreateServiceWithSystemCertificates
        text: apimgmt update  --resource-group rg1 --name apimService1 --publisher-email apim@autorestsdk.com --publisher-name autorestsdk --sku-name Basic --sku-capacity 1 --location Central US
      - name: ApiManagementUpdateServiceDisableTls10
        text: apimgmt update  --resource-group rg1 --name apimService1
      - name: ApiManagementUpdateServicePublisherDetails
        text: apimgmt update  --resource-group rg1 --name apimService1 --publisher-email foobar@live.com --publisher-name Contoso Vnext
      - name: ApiManagementServiceDeleteService
        text: apimgmt update  --resource-group rg1 --name apimService1
"""

helps['apimgmt delete'] = """
    type: command
    short-summary: delete a apimgmt.
    examples:
# delete -- delete
      - name: ApiManagementCreateService
        text: apimgmt delete  --resource-group rg1 --name apimService1
      - name: ApiManagementCreateMultiRegionServiceWithCustomHostname
        text: apimgmt delete  --resource-group rg1 --name apimService1
      - name: ApiManagementCreateServiceHavingMsi
        text: apimgmt delete  --resource-group rg1 --name apimService1
      - name: ApiManagementCreateServiceWithSystemCertificates
        text: apimgmt delete  --resource-group rg1 --name apimService1
      - name: ApiManagementUpdateServiceDisableTls10
        text: apimgmt delete  --resource-group rg1 --name apimService1
      - name: ApiManagementUpdateServicePublisherDetails
        text: apimgmt delete  --resource-group rg1 --name apimService1
      - name: ApiManagementServiceDeleteService
        text: apimgmt delete  --resource-group rg1 --name apimService1
"""

helps['apimgmt list'] = """
    type: command
    short-summary: list a apimgmt.
    examples:
# list_by_resource_group -- list
      - name: ApiManagementCreateService
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementCreateMultiRegionServiceWithCustomHostname
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementCreateServiceHavingMsi
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementCreateServiceWithSystemCertificates
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementUpdateServiceDisableTls10
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementUpdateServicePublisherDetails
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementServiceDeleteService
        text: apimgmt list  --resource-group rg1
# list -- list
      - name: ApiManagementCreateService
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementCreateMultiRegionServiceWithCustomHostname
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementCreateServiceHavingMsi
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementCreateServiceWithSystemCertificates
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementUpdateServiceDisableTls10
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementUpdateServicePublisherDetails
        text: apimgmt list  --resource-group rg1
      - name: ApiManagementServiceDeleteService
        text: apimgmt list  --resource-group rg1
"""

helps['apimgmt show'] = """
    type: command
    short-summary: show a apimgmt.
    examples:
# get -- show
      - name: ApiManagementCreateService
        text: apimgmt show  --resource-group rg1 --name apimService1
      - name: ApiManagementCreateMultiRegionServiceWithCustomHostname
        text: apimgmt show  --resource-group rg1 --name apimService1
      - name: ApiManagementCreateServiceHavingMsi
        text: apimgmt show  --resource-group rg1 --name apimService1
      - name: ApiManagementCreateServiceWithSystemCertificates
        text: apimgmt show  --resource-group rg1 --name apimService1
      - name: ApiManagementUpdateServiceDisableTls10
        text: apimgmt show  --resource-group rg1 --name apimService1
      - name: ApiManagementUpdateServicePublisherDetails
        text: apimgmt show  --resource-group rg1 --name apimService1
      - name: ApiManagementServiceDeleteService
        text: apimgmt show  --resource-group rg1 --name apimService1
"""

helps['apimgmt diagnostic'] = """
    type: group
    short-summary: Commands to manage Diagnostic.
"""

helps['apimgmt diagnostic create'] = """
    type: command
    short-summary: create a apimgmt diagnostic.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateDiagnostic
        text: apimgmt diagnostic create  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/azuremonitor
      - name: ApiManagementUpdateDiagnostic
        text: apimgmt diagnostic create  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/applicationinsights
      - name: ApiManagementDeleteDiagnostic
        text: apimgmt diagnostic create  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
"""

helps['apimgmt diagnostic update'] = """
    type: command
    short-summary: update a apimgmt diagnostic.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateDiagnostic
        text: apimgmt diagnostic update  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/azuremonitor
      - name: ApiManagementUpdateDiagnostic
        text: apimgmt diagnostic update  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights --always-log allErrors --logger-id /loggers/applicationinsights
      - name: ApiManagementDeleteDiagnostic
        text: apimgmt diagnostic update  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
"""

helps['apimgmt diagnostic delete'] = """
    type: command
    short-summary: delete a apimgmt diagnostic.
    examples:
# delete -- delete
      - name: ApiManagementCreateDiagnostic
        text: apimgmt diagnostic delete  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
      - name: ApiManagementUpdateDiagnostic
        text: apimgmt diagnostic delete  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
      - name: ApiManagementDeleteDiagnostic
        text: apimgmt diagnostic delete  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
"""

helps['apimgmt diagnostic list'] = """
    type: command
    short-summary: list a apimgmt diagnostic.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateDiagnostic
        text: apimgmt diagnostic list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateDiagnostic
        text: apimgmt diagnostic list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteDiagnostic
        text: apimgmt diagnostic list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt diagnostic show'] = """
    type: command
    short-summary: show a apimgmt diagnostic.
    examples:
# get -- show
      - name: ApiManagementCreateDiagnostic
        text: apimgmt diagnostic show  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
      - name: ApiManagementUpdateDiagnostic
        text: apimgmt diagnostic show  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
      - name: ApiManagementDeleteDiagnostic
        text: apimgmt diagnostic show  --resource-group rg1 --service-name apimService1 --diagnostic-id applicationinsights
"""

helps['apimgmt template'] = """
    type: group
    short-summary: Commands to manage EmailTemplate.
"""

helps['apimgmt template create'] = """
    type: command
    short-summary: create a apimgmt template.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateEmailTemplate
        text: apimgmt template create  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage --subject Your request for $IssueName was successfully received.
      - name: ApiManagementUpdateEmailTemplate
        text: apimgmt template create  --resource-group rg1 --service-name apimService1 --name applicationApprovedNotificationMessage --subject Your application $AppName is published in the gallery --body <!DOCTYPE html >
<html>
  <head />
  <body>
    <p style="font-size:12pt;font-family:'Segoe UI'">Dear $DevFirstName $DevLastName,</p>
    <p style="font-size:12pt;font-family:'Segoe UI'">
          We are happy to let you know that your request to publish the $AppName application in the gallery has been approved. Your application has been published and can be viewed <a href="http://$DevPortalUrl/Applications/Details/$AppId">here</a>.
        </p>
    <p style="font-size:12pt;font-family:'Segoe UI'">Best,</p>
    <p style="font-size:12pt;font-family:'Segoe UI'">The $OrganizationName API Team</p>
  </body>
</html>
      - name: ApiManagementDeleteEmailTemplate
        text: apimgmt template create  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage
"""

helps['apimgmt template update'] = """
    type: command
    short-summary: update a apimgmt template.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateEmailTemplate
        text: apimgmt template update  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage --subject Your request for $IssueName was successfully received.
      - name: ApiManagementUpdateEmailTemplate
        text: apimgmt template update  --resource-group rg1 --service-name apimService1 --name applicationApprovedNotificationMessage --subject Your application $AppName is published in the gallery --body <!DOCTYPE html >
<html>
  <head />
  <body>
    <p style="font-size:12pt;font-family:'Segoe UI'">Dear $DevFirstName $DevLastName,</p>
    <p style="font-size:12pt;font-family:'Segoe UI'">
          We are happy to let you know that your request to publish the $AppName application in the gallery has been approved. Your application has been published and can be viewed <a href="http://$DevPortalUrl/Applications/Details/$AppId">here</a>.
        </p>
    <p style="font-size:12pt;font-family:'Segoe UI'">Best,</p>
    <p style="font-size:12pt;font-family:'Segoe UI'">The $OrganizationName API Team</p>
  </body>
</html>
      - name: ApiManagementDeleteEmailTemplate
        text: apimgmt template update  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage
"""

helps['apimgmt template delete'] = """
    type: command
    short-summary: delete a apimgmt template.
    examples:
# delete -- delete
      - name: ApiManagementCreateEmailTemplate
        text: apimgmt template delete  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage
      - name: ApiManagementUpdateEmailTemplate
        text: apimgmt template delete  --resource-group rg1 --service-name apimService1 --name applicationApprovedNotificationMessage
      - name: ApiManagementDeleteEmailTemplate
        text: apimgmt template delete  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage
"""

helps['apimgmt template list'] = """
    type: command
    short-summary: list a apimgmt template.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateEmailTemplate
        text: apimgmt template list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateEmailTemplate
        text: apimgmt template list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteEmailTemplate
        text: apimgmt template list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt template show'] = """
    type: command
    short-summary: show a apimgmt template.
    examples:
# get -- show
      - name: ApiManagementCreateEmailTemplate
        text: apimgmt template show  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage
      - name: ApiManagementUpdateEmailTemplate
        text: apimgmt template show  --resource-group rg1 --service-name apimService1 --name applicationApprovedNotificationMessage
      - name: ApiManagementDeleteEmailTemplate
        text: apimgmt template show  --resource-group rg1 --service-name apimService1 --name newIssueNotificationMessage
"""

helps['apimgmt group'] = """
    type: group
    short-summary: Commands to manage Group.
"""

helps['apimgmt group create'] = """
    type: command
    short-summary: create a apimgmt group.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateGroup
        text: apimgmt group create  --resource-group rg1 --service-name apimService1 --group-id tempgroup --display-name temp group
      - name: ApiManagementCreateGroupExternal
        text: apimgmt group create  --resource-group rg1 --service-name apimService1 --group-id aadGroup --display-name NewGroup (samiraad.onmicrosoft.com) --description new group to test --type external --external-id aad://samiraad.onmicrosoft.com/groups/83cf2753-5831-4675-bc0e-2f8dc067c58d
      - name: ApiManagementUpdateGroup
        text: apimgmt group create  --resource-group rg1 --service-name apimService1 --group-id tempgroup --display-name temp group
      - name: ApiManagementDeleteGroup
        text: apimgmt group create  --resource-group rg1 --service-name apimService1 --group-id aadGroup
"""

helps['apimgmt group update'] = """
    type: command
    short-summary: update a apimgmt group.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateGroup
        text: apimgmt group update  --resource-group rg1 --service-name apimService1 --group-id tempgroup --display-name temp group
      - name: ApiManagementCreateGroupExternal
        text: apimgmt group update  --resource-group rg1 --service-name apimService1 --group-id aadGroup --display-name NewGroup (samiraad.onmicrosoft.com) --description new group to test --type external --external-id aad://samiraad.onmicrosoft.com/groups/83cf2753-5831-4675-bc0e-2f8dc067c58d
      - name: ApiManagementUpdateGroup
        text: apimgmt group update  --resource-group rg1 --service-name apimService1 --group-id tempgroup --display-name temp group
      - name: ApiManagementDeleteGroup
        text: apimgmt group update  --resource-group rg1 --service-name apimService1 --group-id aadGroup
"""

helps['apimgmt group delete'] = """
    type: command
    short-summary: delete a apimgmt group.
    examples:
# delete -- delete
      - name: ApiManagementCreateGroup
        text: apimgmt group delete  --resource-group rg1 --service-name apimService1 --group-id tempgroup
      - name: ApiManagementCreateGroupExternal
        text: apimgmt group delete  --resource-group rg1 --service-name apimService1 --group-id aadGroup
      - name: ApiManagementUpdateGroup
        text: apimgmt group delete  --resource-group rg1 --service-name apimService1 --group-id tempgroup
      - name: ApiManagementDeleteGroup
        text: apimgmt group delete  --resource-group rg1 --service-name apimService1 --group-id aadGroup
"""

helps['apimgmt group list'] = """
    type: command
    short-summary: list a apimgmt group.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateGroup
        text: apimgmt group list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateGroupExternal
        text: apimgmt group list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateGroup
        text: apimgmt group list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteGroup
        text: apimgmt group list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt group show'] = """
    type: command
    short-summary: show a apimgmt group.
    examples:
# get -- show
      - name: ApiManagementCreateGroup
        text: apimgmt group show  --resource-group rg1 --service-name apimService1 --group-id tempgroup
      - name: ApiManagementCreateGroupExternal
        text: apimgmt group show  --resource-group rg1 --service-name apimService1 --group-id aadGroup
      - name: ApiManagementUpdateGroup
        text: apimgmt group show  --resource-group rg1 --service-name apimService1 --group-id tempgroup
      - name: ApiManagementDeleteGroup
        text: apimgmt group show  --resource-group rg1 --service-name apimService1 --group-id aadGroup
"""

helps['apimgmt group user'] = """
    type: group
    short-summary: Commands to manage GroupUser.
"""

helps['apimgmt group user create'] = """
    type: command
    short-summary: create a apimgmt group user.
    examples:
# create -- create
      - name: ApiManagementCreateGroupUser
        text: apimgmt group user create  --resource-group rg1 --service-name apimService1 --group-id tempgroup --user-id 59307d350af58404d8a26300
      - name: ApiManagementDeleteGroupUser
        text: apimgmt group user create  --resource-group rg1 --service-name apimService1 --group-id templategroup --user-id 59307d350af58404d8a26300
"""

helps['apimgmt group user delete'] = """
    type: command
    short-summary: delete a apimgmt group user.
    examples:
# delete -- delete
      - name: ApiManagementCreateGroupUser
        text: apimgmt group user delete  --resource-group rg1 --service-name apimService1 --group-id tempgroup --user-id 59307d350af58404d8a26300
      - name: ApiManagementDeleteGroupUser
        text: apimgmt group user delete  --resource-group rg1 --service-name apimService1 --group-id templategroup --user-id 59307d350af58404d8a26300
"""

helps['apimgmt group user list'] = """
    type: command
    short-summary: list a apimgmt group user.
    examples:
# list -- list
      - name: ApiManagementCreateGroupUser
        text: apimgmt group user list  --resource-group rg1 --service-name apimService1 --group-id tempgroup
      - name: ApiManagementDeleteGroupUser
        text: apimgmt group user list  --resource-group rg1 --service-name apimService1 --group-id templategroup
"""

helps['apimgmt identityprovider'] = """
    type: group
    short-summary: Commands to manage IdentityProvider.
"""

helps['apimgmt identityprovider create'] = """
    type: command
    short-summary: create a apimgmt identityprovider.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateIdentityProvider
        text: apimgmt identityprovider create  --resource-group rg1 --service-name apimService1 --name facebook --client-id facebookid --client-secret facebookapplicationsecret
      - name: ApiManagementUpdateIdentityProvider
        text: apimgmt identityprovider create  --resource-group rg1 --service-name apimService1 --name facebook --client-id updatedfacebookid --client-secret updatedfacebooksecret
      - name: ApiManagementDeleteIdentityProvider
        text: apimgmt identityprovider create  --resource-group rg1 --service-name apimService1 --name aad
"""

helps['apimgmt identityprovider update'] = """
    type: command
    short-summary: update a apimgmt identityprovider.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateIdentityProvider
        text: apimgmt identityprovider update  --resource-group rg1 --service-name apimService1 --name facebook --client-id facebookid --client-secret facebookapplicationsecret
      - name: ApiManagementUpdateIdentityProvider
        text: apimgmt identityprovider update  --resource-group rg1 --service-name apimService1 --name facebook --client-id updatedfacebookid --client-secret updatedfacebooksecret
      - name: ApiManagementDeleteIdentityProvider
        text: apimgmt identityprovider update  --resource-group rg1 --service-name apimService1 --name aad
"""

helps['apimgmt identityprovider delete'] = """
    type: command
    short-summary: delete a apimgmt identityprovider.
    examples:
# delete -- delete
      - name: ApiManagementCreateIdentityProvider
        text: apimgmt identityprovider delete  --resource-group rg1 --service-name apimService1 --name facebook
      - name: ApiManagementUpdateIdentityProvider
        text: apimgmt identityprovider delete  --resource-group rg1 --service-name apimService1 --name facebook
      - name: ApiManagementDeleteIdentityProvider
        text: apimgmt identityprovider delete  --resource-group rg1 --service-name apimService1 --name aad
"""

helps['apimgmt identityprovider list'] = """
    type: command
    short-summary: list a apimgmt identityprovider.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateIdentityProvider
        text: apimgmt identityprovider list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateIdentityProvider
        text: apimgmt identityprovider list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteIdentityProvider
        text: apimgmt identityprovider list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt identityprovider show'] = """
    type: command
    short-summary: show a apimgmt identityprovider.
    examples:
# get -- show
      - name: ApiManagementCreateIdentityProvider
        text: apimgmt identityprovider show  --resource-group rg1 --service-name apimService1 --name facebook
      - name: ApiManagementUpdateIdentityProvider
        text: apimgmt identityprovider show  --resource-group rg1 --service-name apimService1 --name facebook
      - name: ApiManagementDeleteIdentityProvider
        text: apimgmt identityprovider show  --resource-group rg1 --service-name apimService1 --name aad
"""

helps['apimgmt logger'] = """
    type: group
    short-summary: Commands to manage Logger.
"""

helps['apimgmt logger create'] = """
    type: command
    short-summary: create a apimgmt logger.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateEHLogger
        text: apimgmt logger create  --resource-group rg1 --service-name apimService1 --logger-id loggerId --logger-type azureEventHub --description adding a new logger
      - name: ApiManagementCreateAILogger
        text: apimgmt logger create  --resource-group rg1 --service-name apimService1 --logger-id loggerId --logger-type applicationInsights --description adding a new logger
      - name: ApiManagementUpdateLogger
        text: apimgmt logger create  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementDeleteLogger
        text: apimgmt logger create  --resource-group rg1 --service-name apimService1 --logger-id loggerId
"""

helps['apimgmt logger update'] = """
    type: command
    short-summary: update a apimgmt logger.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateEHLogger
        text: apimgmt logger update  --resource-group rg1 --service-name apimService1 --logger-id loggerId --logger-type azureEventHub --description adding a new logger
      - name: ApiManagementCreateAILogger
        text: apimgmt logger update  --resource-group rg1 --service-name apimService1 --logger-id loggerId --logger-type applicationInsights --description adding a new logger
      - name: ApiManagementUpdateLogger
        text: apimgmt logger update  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementDeleteLogger
        text: apimgmt logger update  --resource-group rg1 --service-name apimService1 --logger-id loggerId
"""

helps['apimgmt logger delete'] = """
    type: command
    short-summary: delete a apimgmt logger.
    examples:
# delete -- delete
      - name: ApiManagementCreateEHLogger
        text: apimgmt logger delete  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementCreateAILogger
        text: apimgmt logger delete  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementUpdateLogger
        text: apimgmt logger delete  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementDeleteLogger
        text: apimgmt logger delete  --resource-group rg1 --service-name apimService1 --logger-id loggerId
"""

helps['apimgmt logger list'] = """
    type: command
    short-summary: list a apimgmt logger.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateEHLogger
        text: apimgmt logger list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementCreateAILogger
        text: apimgmt logger list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateLogger
        text: apimgmt logger list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteLogger
        text: apimgmt logger list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt logger show'] = """
    type: command
    short-summary: show a apimgmt logger.
    examples:
# get -- show
      - name: ApiManagementCreateEHLogger
        text: apimgmt logger show  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementCreateAILogger
        text: apimgmt logger show  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementUpdateLogger
        text: apimgmt logger show  --resource-group rg1 --service-name apimService1 --logger-id loggerId
      - name: ApiManagementDeleteLogger
        text: apimgmt logger show  --resource-group rg1 --service-name apimService1 --logger-id loggerId
"""

helps['apimgmt notification'] = """
    type: group
    short-summary: Commands to manage Notification.
"""

helps['apimgmt notification create'] = """
    type: command
    short-summary: create a apimgmt notification.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateNotification
        text: apimgmt notification create  --resource-group rg1 --service-name apimService1 --name RequestPublisherNotificationMessage
"""

helps['apimgmt notification update'] = """
    type: command
    short-summary: update a apimgmt notification.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateNotification
        text: apimgmt notification update  --resource-group rg1 --service-name apimService1 --name RequestPublisherNotificationMessage
"""

helps['apimgmt notification list'] = """
    type: command
    short-summary: list a apimgmt notification.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateNotification
        text: apimgmt notification list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt notification show'] = """
    type: command
    short-summary: show a apimgmt notification.
    examples:
# get -- show
      - name: ApiManagementCreateNotification
        text: apimgmt notification show  --resource-group rg1 --service-name apimService1 --name RequestPublisherNotificationMessage
"""

helps['apimgmt notification recipientuser'] = """
    type: group
    short-summary: Commands to manage NotificationRecipientUser.
"""

helps['apimgmt notification recipientuser create'] = """
    type: command
    short-summary: create a apimgmt notification recipientuser.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateNotificationRecipientUser
        text: apimgmt notification recipientuser create  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --user-id 576823d0a40f7e74ec07d642
      - name: ApiManagementDeleteNotificationRecipientUser
        text: apimgmt notification recipientuser create  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --user-id 576823d0a40f7e74ec07d642
"""

helps['apimgmt notification recipientuser update'] = """
    type: command
    short-summary: update a apimgmt notification recipientuser.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateNotificationRecipientUser
        text: apimgmt notification recipientuser update  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --user-id 576823d0a40f7e74ec07d642
      - name: ApiManagementDeleteNotificationRecipientUser
        text: apimgmt notification recipientuser update  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --user-id 576823d0a40f7e74ec07d642
"""

helps['apimgmt notification recipientuser delete'] = """
    type: command
    short-summary: delete a apimgmt notification recipientuser.
    examples:
# delete -- delete
      - name: ApiManagementCreateNotificationRecipientUser
        text: apimgmt notification recipientuser delete  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --user-id 576823d0a40f7e74ec07d642
      - name: ApiManagementDeleteNotificationRecipientUser
        text: apimgmt notification recipientuser delete  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --user-id 576823d0a40f7e74ec07d642
"""

helps['apimgmt notification recipientuser list'] = """
    type: command
    short-summary: list a apimgmt notification recipientuser.
    examples:
# list_by_notification -- list
      - name: ApiManagementCreateNotificationRecipientUser
        text: apimgmt notification recipientuser list  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage
      - name: ApiManagementDeleteNotificationRecipientUser
        text: apimgmt notification recipientuser list  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage
"""

helps['apimgmt notification recipientemail'] = """
    type: group
    short-summary: Commands to manage NotificationRecipientEmail.
"""

helps['apimgmt notification recipientemail create'] = """
    type: command
    short-summary: create a apimgmt notification recipientemail.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateNotificationRecipientEmail
        text: apimgmt notification recipientemail create  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --email foobar@live.com
      - name: ApiManagementDeleteNotificationRecipientEmail
        text: apimgmt notification recipientemail create  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --email contoso@live.com
"""

helps['apimgmt notification recipientemail update'] = """
    type: command
    short-summary: update a apimgmt notification recipientemail.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateNotificationRecipientEmail
        text: apimgmt notification recipientemail update  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --email foobar@live.com
      - name: ApiManagementDeleteNotificationRecipientEmail
        text: apimgmt notification recipientemail update  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --email contoso@live.com
"""

helps['apimgmt notification recipientemail delete'] = """
    type: command
    short-summary: delete a apimgmt notification recipientemail.
    examples:
# delete -- delete
      - name: ApiManagementCreateNotificationRecipientEmail
        text: apimgmt notification recipientemail delete  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --email foobar@live.com
      - name: ApiManagementDeleteNotificationRecipientEmail
        text: apimgmt notification recipientemail delete  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage --email contoso@live.com
"""

helps['apimgmt notification recipientemail list'] = """
    type: command
    short-summary: list a apimgmt notification recipientemail.
    examples:
# list_by_notification -- list
      - name: ApiManagementCreateNotificationRecipientEmail
        text: apimgmt notification recipientemail list  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage
      - name: ApiManagementDeleteNotificationRecipientEmail
        text: apimgmt notification recipientemail list  --resource-group rg1 --service-name apimService1 --notification-name RequestPublisherNotificationMessage
"""

helps['apimgmt openidconnectprovider'] = """
    type: group
    short-summary: Commands to manage OpenIdConnectProvider.
"""

helps['apimgmt openidconnectprovider create'] = """
    type: command
    short-summary: create a apimgmt openidconnectprovider.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateOpenIdConnectProvider
        text: apimgmt openidconnectprovider create  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3 --display-name templateoidprovider3 --metadata-endpoint https://oidprovider-template3.net --client-id oidprovidertemplate3
      - name: ApiManagementUpdateOpenIdConnectProvider
        text: apimgmt openidconnectprovider create  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect2 --client-secret updatedsecret
      - name: ApiManagementDeleteOpenIdConnectProvider
        text: apimgmt openidconnectprovider create  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3
"""

helps['apimgmt openidconnectprovider update'] = """
    type: command
    short-summary: update a apimgmt openidconnectprovider.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateOpenIdConnectProvider
        text: apimgmt openidconnectprovider update  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3 --display-name templateoidprovider3 --metadata-endpoint https://oidprovider-template3.net --client-id oidprovidertemplate3
      - name: ApiManagementUpdateOpenIdConnectProvider
        text: apimgmt openidconnectprovider update  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect2 --client-secret updatedsecret
      - name: ApiManagementDeleteOpenIdConnectProvider
        text: apimgmt openidconnectprovider update  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3
"""

helps['apimgmt openidconnectprovider delete'] = """
    type: command
    short-summary: delete a apimgmt openidconnectprovider.
    examples:
# delete -- delete
      - name: ApiManagementCreateOpenIdConnectProvider
        text: apimgmt openidconnectprovider delete  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3
      - name: ApiManagementUpdateOpenIdConnectProvider
        text: apimgmt openidconnectprovider delete  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect2
      - name: ApiManagementDeleteOpenIdConnectProvider
        text: apimgmt openidconnectprovider delete  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3
"""

helps['apimgmt openidconnectprovider list'] = """
    type: command
    short-summary: list a apimgmt openidconnectprovider.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateOpenIdConnectProvider
        text: apimgmt openidconnectprovider list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateOpenIdConnectProvider
        text: apimgmt openidconnectprovider list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteOpenIdConnectProvider
        text: apimgmt openidconnectprovider list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt openidconnectprovider show'] = """
    type: command
    short-summary: show a apimgmt openidconnectprovider.
    examples:
# get -- show
      - name: ApiManagementCreateOpenIdConnectProvider
        text: apimgmt openidconnectprovider show  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3
      - name: ApiManagementUpdateOpenIdConnectProvider
        text: apimgmt openidconnectprovider show  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect2
      - name: ApiManagementDeleteOpenIdConnectProvider
        text: apimgmt openidconnectprovider show  --resource-group rg1 --service-name apimService1 --opid templateOpenIdConnect3
"""

helps['apimgmt policy'] = """
    type: group
    short-summary: Commands to manage Policy.
"""

helps['apimgmt policy create'] = """
    type: command
    short-summary: create a apimgmt policy.
    examples:
# create_or_update -- create
      - name: ApiManagementCreatePolicy
        text: apimgmt policy create  --resource-group rg1 --service-name apimService1 --policy-id policy --value <policies>
  <inbound />
  <backend>
    <forward-request />
  </backend>
  <outbound />
</policies> --format xml
      - name: ApiManagementDeletePolicy
        text: apimgmt policy create  --resource-group rg1 --service-name apimService1 --policy-id policy
"""

helps['apimgmt policy update'] = """
    type: command
    short-summary: update a apimgmt policy.
    examples:
# create_or_update -- update
      - name: ApiManagementCreatePolicy
        text: apimgmt policy update  --resource-group rg1 --service-name apimService1 --policy-id policy --value <policies>
  <inbound />
  <backend>
    <forward-request />
  </backend>
  <outbound />
</policies> --format xml
      - name: ApiManagementDeletePolicy
        text: apimgmt policy update  --resource-group rg1 --service-name apimService1 --policy-id policy
"""

helps['apimgmt policy delete'] = """
    type: command
    short-summary: delete a apimgmt policy.
    examples:
# delete -- delete
      - name: ApiManagementCreatePolicy
        text: apimgmt policy delete  --resource-group rg1 --service-name apimService1 --policy-id policy
      - name: ApiManagementDeletePolicy
        text: apimgmt policy delete  --resource-group rg1 --service-name apimService1 --policy-id policy
"""

helps['apimgmt policy list'] = """
    type: command
    short-summary: list a apimgmt policy.
    examples:
# list_by_service -- list
      - name: ApiManagementCreatePolicy
        text: apimgmt policy list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeletePolicy
        text: apimgmt policy list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt policy show'] = """
    type: command
    short-summary: show a apimgmt policy.
    examples:
# get -- show
      - name: ApiManagementCreatePolicy
        text: apimgmt policy show  --resource-group rg1 --service-name apimService1 --policy-id policy --format xml
      - name: ApiManagementDeletePolicy
        text: apimgmt policy show  --resource-group rg1 --service-name apimService1 --policy-id policy
"""

helps['apimgmt portalsetting'] = """
    type: group
    short-summary: Commands to manage SignInSetting.
"""

helps['apimgmt portalsetting create'] = """
    type: command
    short-summary: create a apimgmt portalsetting.
    examples:
# create_or_update -- create
      - name: ApiManagementPortalSettingsUpdateSignIn
        text: apimgmt portalsetting create  --resource-group rg1 --name apimService1 --enabled true
      - name: ApiManagementPortalSettingsUpdateSignIn
        text: apimgmt portalsetting create  --resource-group rg1 --name apimService1 --enabled true
"""

helps['apimgmt portalsetting update'] = """
    type: command
    short-summary: update a apimgmt portalsetting.
    examples:
# create_or_update -- update
      - name: ApiManagementPortalSettingsUpdateSignIn
        text: apimgmt portalsetting update  --resource-group rg1 --name apimService1 --enabled true
      - name: ApiManagementPortalSettingsUpdateSignIn
        text: apimgmt portalsetting update  --resource-group rg1 --name apimService1 --enabled true
"""

helps['apimgmt portalsetting show'] = """
    type: command
    short-summary: show a apimgmt portalsetting.
    examples:
# get -- show
      - name: ApiManagementPortalSettingsUpdateSignIn
        text: apimgmt portalsetting show  --resource-group rg1 --name apimService1
      - name: ApiManagementPortalSettingsUpdateSignIn
        text: apimgmt portalsetting show  --resource-group rg1 --name apimService1
"""

helps['apimgmt portalsetting'] = """
    type: group
    short-summary: Commands to manage SignUpSetting.
"""

helps['apimgmt portalsetting create'] = """
    type: command
    short-summary: create a apimgmt portalsetting.
    examples:
# create_or_update -- create
      - name: ApiManagementPortalSettingsUpdateSignUp
        text: apimgmt portalsetting create  --resource-group rg1 --name apimService1 --enabled true
      - name: ApiManagementPortalSettingsUpdateSignUp
        text: apimgmt portalsetting create  --resource-group rg1 --name apimService1 --enabled true
"""

helps['apimgmt portalsetting update'] = """
    type: command
    short-summary: update a apimgmt portalsetting.
    examples:
# create_or_update -- update
      - name: ApiManagementPortalSettingsUpdateSignUp
        text: apimgmt portalsetting update  --resource-group rg1 --name apimService1 --enabled true
      - name: ApiManagementPortalSettingsUpdateSignUp
        text: apimgmt portalsetting update  --resource-group rg1 --name apimService1 --enabled true
"""

helps['apimgmt portalsetting show'] = """
    type: command
    short-summary: show a apimgmt portalsetting.
    examples:
# get -- show
      - name: ApiManagementPortalSettingsUpdateSignUp
        text: apimgmt portalsetting show  --resource-group rg1 --name apimService1
      - name: ApiManagementPortalSettingsUpdateSignUp
        text: apimgmt portalsetting show  --resource-group rg1 --name apimService1
"""

helps['apimgmt portalsetting'] = """
    type: group
    short-summary: Commands to manage DelegationSetting.
"""

helps['apimgmt portalsetting create'] = """
    type: command
    short-summary: create a apimgmt portalsetting.
    examples:
# create_or_update -- create
      - name: ApiManagementPortalSettingsUpdateDelegation
        text: apimgmt portalsetting create  --resource-group rg1 --name apimService1 --url http://contoso.com/delegation --validation-key nVF7aKIvr9mV/RM5lOD0sYoi8ThXTRHQP7o66hvUmjCDkPKR3qxPu/otJcNciz2aQdqPuzJH3ECG4TU2yZjQ7Q==
      - name: ApiManagementPortalSettingsUpdateDelegation
        text: apimgmt portalsetting create  --resource-group rg1 --name apimService1 --url http://contoso.com/delegation --validation-key nVF7aKIvr9mV/RM5lOD0sYoi8ThXTRHQP7o66hvUmjCDkPKR3qxPu/otJcNciz2aQdqPuzJH3ECG4TU2yZjQ7Q==
"""

helps['apimgmt portalsetting update'] = """
    type: command
    short-summary: update a apimgmt portalsetting.
    examples:
# create_or_update -- update
      - name: ApiManagementPortalSettingsUpdateDelegation
        text: apimgmt portalsetting update  --resource-group rg1 --name apimService1 --url http://contoso.com/delegation --validation-key nVF7aKIvr9mV/RM5lOD0sYoi8ThXTRHQP7o66hvUmjCDkPKR3qxPu/otJcNciz2aQdqPuzJH3ECG4TU2yZjQ7Q==
      - name: ApiManagementPortalSettingsUpdateDelegation
        text: apimgmt portalsetting update  --resource-group rg1 --name apimService1 --url http://contoso.com/delegation --validation-key nVF7aKIvr9mV/RM5lOD0sYoi8ThXTRHQP7o66hvUmjCDkPKR3qxPu/otJcNciz2aQdqPuzJH3ECG4TU2yZjQ7Q==
"""

helps['apimgmt portalsetting show'] = """
    type: command
    short-summary: show a apimgmt portalsetting.
    examples:
# get -- show
      - name: ApiManagementPortalSettingsUpdateDelegation
        text: apimgmt portalsetting show  --resource-group rg1 --name apimService1
      - name: ApiManagementPortalSettingsUpdateDelegation
        text: apimgmt portalsetting show  --resource-group rg1 --name apimService1
"""

helps['apimgmt product'] = """
    type: group
    short-summary: Commands to manage Product.
"""

helps['apimgmt product create'] = """
    type: command
    short-summary: create a apimgmt product.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateProduct
        text: apimgmt product create  --resource-group rg1 --service-name apimService1 --product-id testproduct --display-name Test Template ProductName 4
      - name: ApiManagementUpdateProduct
        text: apimgmt product create  --resource-group rg1 --service-name apimService1 --product-id testproduct --display-name Test Template ProductName 4
      - name: ApiManagementDeleteProduct
        text: apimgmt product create  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product update'] = """
    type: command
    short-summary: update a apimgmt product.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateProduct
        text: apimgmt product update  --resource-group rg1 --service-name apimService1 --product-id testproduct --display-name Test Template ProductName 4
      - name: ApiManagementUpdateProduct
        text: apimgmt product update  --resource-group rg1 --service-name apimService1 --product-id testproduct --display-name Test Template ProductName 4
      - name: ApiManagementDeleteProduct
        text: apimgmt product update  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product delete'] = """
    type: command
    short-summary: delete a apimgmt product.
    examples:
# delete -- delete
      - name: ApiManagementCreateProduct
        text: apimgmt product delete  --resource-group rg1 --service-name apimService1 --product-id testproduct
      - name: ApiManagementUpdateProduct
        text: apimgmt product delete  --resource-group rg1 --service-name apimService1 --product-id testproduct
      - name: ApiManagementDeleteProduct
        text: apimgmt product delete  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product list'] = """
    type: command
    short-summary: list a apimgmt product.
    examples:
# list_by_tags -- list
      - name: ApiManagementCreateProduct
        text: apimgmt product list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateProduct
        text: apimgmt product list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteProduct
        text: apimgmt product list  --resource-group rg1 --service-name apimService1
# list_by_service -- list
      - name: ApiManagementCreateProduct
        text: apimgmt product list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateProduct
        text: apimgmt product list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteProduct
        text: apimgmt product list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt product show'] = """
    type: command
    short-summary: show a apimgmt product.
    examples:
# get -- show
      - name: ApiManagementCreateProduct
        text: apimgmt product show  --resource-group rg1 --service-name apimService1 --product-id testproduct
      - name: ApiManagementUpdateProduct
        text: apimgmt product show  --resource-group rg1 --service-name apimService1 --product-id testproduct
      - name: ApiManagementDeleteProduct
        text: apimgmt product show  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product api'] = """
    type: group
    short-summary: Commands to manage ProductApi.
"""

helps['apimgmt product api create'] = """
    type: command
    short-summary: create a apimgmt product api.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateProductApi
        text: apimgmt product api create  --resource-group rg1 --service-name apimService1 --product-id testproduct --api-id echo-api
      - name: ApiManagementDeleteProductApi
        text: apimgmt product api create  --resource-group rg1 --service-name apimService1 --product-id testproduct --api-id echo-api
"""

helps['apimgmt product api update'] = """
    type: command
    short-summary: update a apimgmt product api.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateProductApi
        text: apimgmt product api update  --resource-group rg1 --service-name apimService1 --product-id testproduct --api-id echo-api
      - name: ApiManagementDeleteProductApi
        text: apimgmt product api update  --resource-group rg1 --service-name apimService1 --product-id testproduct --api-id echo-api
"""

helps['apimgmt product api delete'] = """
    type: command
    short-summary: delete a apimgmt product api.
    examples:
# delete -- delete
      - name: ApiManagementCreateProductApi
        text: apimgmt product api delete  --resource-group rg1 --service-name apimService1 --product-id testproduct --api-id echo-api
      - name: ApiManagementDeleteProductApi
        text: apimgmt product api delete  --resource-group rg1 --service-name apimService1 --product-id testproduct --api-id echo-api
"""

helps['apimgmt product api list'] = """
    type: command
    short-summary: list a apimgmt product api.
    examples:
# list_by_product -- list
      - name: ApiManagementCreateProductApi
        text: apimgmt product api list  --resource-group rg1 --service-name apimService1 --product-id testproduct
      - name: ApiManagementDeleteProductApi
        text: apimgmt product api list  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product group'] = """
    type: group
    short-summary: Commands to manage ProductGroup.
"""

helps['apimgmt product group create'] = """
    type: command
    short-summary: create a apimgmt product group.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateProductGroup
        text: apimgmt product group create  --resource-group rg1 --service-name apimService1 --product-id testproduct --group-id templateGroup
      - name: ApiManagementDeleteProductGroup
        text: apimgmt product group create  --resource-group rg1 --service-name apimService1 --product-id testproduct --group-id templateGroup
"""

helps['apimgmt product group update'] = """
    type: command
    short-summary: update a apimgmt product group.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateProductGroup
        text: apimgmt product group update  --resource-group rg1 --service-name apimService1 --product-id testproduct --group-id templateGroup
      - name: ApiManagementDeleteProductGroup
        text: apimgmt product group update  --resource-group rg1 --service-name apimService1 --product-id testproduct --group-id templateGroup
"""

helps['apimgmt product group delete'] = """
    type: command
    short-summary: delete a apimgmt product group.
    examples:
# delete -- delete
      - name: ApiManagementCreateProductGroup
        text: apimgmt product group delete  --resource-group rg1 --service-name apimService1 --product-id testproduct --group-id templateGroup
      - name: ApiManagementDeleteProductGroup
        text: apimgmt product group delete  --resource-group rg1 --service-name apimService1 --product-id testproduct --group-id templateGroup
"""

helps['apimgmt product group list'] = """
    type: command
    short-summary: list a apimgmt product group.
    examples:
# list_by_product -- list
      - name: ApiManagementCreateProductGroup
        text: apimgmt product group list  --resource-group rg1 --service-name apimService1 --product-id testproduct
      - name: ApiManagementDeleteProductGroup
        text: apimgmt product group list  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product policy'] = """
    type: group
    short-summary: Commands to manage ProductPolicy.
"""

helps['apimgmt product policy create'] = """
    type: command
    short-summary: create a apimgmt product policy.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateProductPolicy
        text: apimgmt product policy create  --resource-group rg1 --service-name apimService1 --product-id 5702e97e5157a50f48dce801 --policy-id policy --value <policies>
  <inbound>
    <rate-limit calls="{{call-count}}" renewal-period="15"></rate-limit>
    <log-to-eventhub logger-id="16">
                      @( string.Join(",", DateTime.UtcNow, context.Deployment.ServiceName, context.RequestId, context.Request.IpAddress, context.Operation.Name) ) 
                  </log-to-eventhub>
    <quota-by-key calls="40" counter-key="cc" renewal-period="3600" increment-count="@(context.Request.Method == &quot;POST&quot; ? 1:2)" />
    <base />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
</policies> --format xml
      - name: ApiManagementDeleteProductPolicy
        text: apimgmt product policy create  --resource-group rg1 --service-name apimService1 --product-id testproduct --policy-id policy
"""

helps['apimgmt product policy update'] = """
    type: command
    short-summary: update a apimgmt product policy.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateProductPolicy
        text: apimgmt product policy update  --resource-group rg1 --service-name apimService1 --product-id 5702e97e5157a50f48dce801 --policy-id policy --value <policies>
  <inbound>
    <rate-limit calls="{{call-count}}" renewal-period="15"></rate-limit>
    <log-to-eventhub logger-id="16">
                      @( string.Join(",", DateTime.UtcNow, context.Deployment.ServiceName, context.RequestId, context.Request.IpAddress, context.Operation.Name) ) 
                  </log-to-eventhub>
    <quota-by-key calls="40" counter-key="cc" renewal-period="3600" increment-count="@(context.Request.Method == &quot;POST&quot; ? 1:2)" />
    <base />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
</policies> --format xml
      - name: ApiManagementDeleteProductPolicy
        text: apimgmt product policy update  --resource-group rg1 --service-name apimService1 --product-id testproduct --policy-id policy
"""

helps['apimgmt product policy delete'] = """
    type: command
    short-summary: delete a apimgmt product policy.
    examples:
# delete -- delete
      - name: ApiManagementCreateProductPolicy
        text: apimgmt product policy delete  --resource-group rg1 --service-name apimService1 --product-id 5702e97e5157a50f48dce801 --policy-id policy
      - name: ApiManagementDeleteProductPolicy
        text: apimgmt product policy delete  --resource-group rg1 --service-name apimService1 --product-id testproduct --policy-id policy
"""

helps['apimgmt product policy list'] = """
    type: command
    short-summary: list a apimgmt product policy.
    examples:
# list_by_product -- list
      - name: ApiManagementCreateProductPolicy
        text: apimgmt product policy list  --resource-group rg1 --service-name apimService1 --product-id 5702e97e5157a50f48dce801
      - name: ApiManagementDeleteProductPolicy
        text: apimgmt product policy list  --resource-group rg1 --service-name apimService1 --product-id testproduct
"""

helps['apimgmt product policy show'] = """
    type: command
    short-summary: show a apimgmt product policy.
    examples:
# get -- show
      - name: ApiManagementCreateProductPolicy
        text: apimgmt product policy show  --resource-group rg1 --service-name apimService1 --product-id 5702e97e5157a50f48dce801 --policy-id policy --format xml
      - name: ApiManagementDeleteProductPolicy
        text: apimgmt product policy show  --resource-group rg1 --service-name apimService1 --product-id testproduct --policy-id policy
"""

helps['apimgmt property'] = """
    type: group
    short-summary: Commands to manage Property.
"""

helps['apimgmt property create'] = """
    type: command
    short-summary: create a apimgmt property.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateProperty
        text: apimgmt property create  --resource-group rg1 --service-name apimService1 --prop-id testprop2 --secret true --display-name prop3name --value propValue
      - name: ApiManagementUpdateProperty
        text: apimgmt property create  --resource-group rg1 --service-name apimService1 --prop-id testprop2 --secret true
      - name: ApiManagementDeleteProperty
        text: apimgmt property create  --resource-group rg1 --service-name apimService1 --prop-id testprop2
"""

helps['apimgmt property update'] = """
    type: command
    short-summary: update a apimgmt property.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateProperty
        text: apimgmt property update  --resource-group rg1 --service-name apimService1 --prop-id testprop2 --secret true --display-name prop3name --value propValue
      - name: ApiManagementUpdateProperty
        text: apimgmt property update  --resource-group rg1 --service-name apimService1 --prop-id testprop2 --secret true
      - name: ApiManagementDeleteProperty
        text: apimgmt property update  --resource-group rg1 --service-name apimService1 --prop-id testprop2
"""

helps['apimgmt property delete'] = """
    type: command
    short-summary: delete a apimgmt property.
    examples:
# delete -- delete
      - name: ApiManagementCreateProperty
        text: apimgmt property delete  --resource-group rg1 --service-name apimService1 --prop-id testprop2
      - name: ApiManagementUpdateProperty
        text: apimgmt property delete  --resource-group rg1 --service-name apimService1 --prop-id testprop2
      - name: ApiManagementDeleteProperty
        text: apimgmt property delete  --resource-group rg1 --service-name apimService1 --prop-id testprop2
"""

helps['apimgmt property list'] = """
    type: command
    short-summary: list a apimgmt property.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateProperty
        text: apimgmt property list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateProperty
        text: apimgmt property list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteProperty
        text: apimgmt property list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt property show'] = """
    type: command
    short-summary: show a apimgmt property.
    examples:
# get -- show
      - name: ApiManagementCreateProperty
        text: apimgmt property show  --resource-group rg1 --service-name apimService1 --prop-id testprop2
      - name: ApiManagementUpdateProperty
        text: apimgmt property show  --resource-group rg1 --service-name apimService1 --prop-id testprop2
      - name: ApiManagementDeleteProperty
        text: apimgmt property show  --resource-group rg1 --service-name apimService1 --prop-id testprop2
"""

helps['apimgmt subscription'] = """
    type: group
    short-summary: Commands to manage Subscription.
"""

helps['apimgmt subscription create'] = """
    type: command
    short-summary: create a apimgmt subscription.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateSubscription
        text: apimgmt subscription create  --resource-group rg1 --service-name apimService1 --sid testsub --owner-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{ user_name }} --scope /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/products/{{ product_name }} --display-name testsub
      - name: ApiManagementUpdateSubscription
        text: apimgmt subscription create  --resource-group rg1 --service-name apimService1 --sid testsub --display-name testsub
      - name: ApiManagementDeleteSubscription
        text: apimgmt subscription create  --resource-group rg1 --service-name apimService1 --sid testsub
"""

helps['apimgmt subscription update'] = """
    type: command
    short-summary: update a apimgmt subscription.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateSubscription
        text: apimgmt subscription update  --resource-group rg1 --service-name apimService1 --sid testsub --owner-id /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{ user_name }} --scope /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/products/{{ product_name }} --display-name testsub
      - name: ApiManagementUpdateSubscription
        text: apimgmt subscription update  --resource-group rg1 --service-name apimService1 --sid testsub --display-name testsub
      - name: ApiManagementDeleteSubscription
        text: apimgmt subscription update  --resource-group rg1 --service-name apimService1 --sid testsub
"""

helps['apimgmt subscription delete'] = """
    type: command
    short-summary: delete a apimgmt subscription.
    examples:
# delete -- delete
      - name: ApiManagementCreateSubscription
        text: apimgmt subscription delete  --resource-group rg1 --service-name apimService1 --sid testsub
      - name: ApiManagementUpdateSubscription
        text: apimgmt subscription delete  --resource-group rg1 --service-name apimService1 --sid testsub
      - name: ApiManagementDeleteSubscription
        text: apimgmt subscription delete  --resource-group rg1 --service-name apimService1 --sid testsub
"""

helps['apimgmt subscription list'] = """
    type: command
    short-summary: list a apimgmt subscription.
    examples:
# list -- list
      - name: ApiManagementCreateSubscription
        text: apimgmt subscription list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateSubscription
        text: apimgmt subscription list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteSubscription
        text: apimgmt subscription list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt subscription show'] = """
    type: command
    short-summary: show a apimgmt subscription.
    examples:
# get -- show
      - name: ApiManagementCreateSubscription
        text: apimgmt subscription show  --resource-group rg1 --service-name apimService1 --sid testsub
      - name: ApiManagementUpdateSubscription
        text: apimgmt subscription show  --resource-group rg1 --service-name apimService1 --sid testsub
      - name: ApiManagementDeleteSubscription
        text: apimgmt subscription show  --resource-group rg1 --service-name apimService1 --sid testsub
"""

helps['apimgmt user'] = """
    type: group
    short-summary: Commands to manage User.
"""

helps['apimgmt user create'] = """
    type: command
    short-summary: create a apimgmt user.
    examples:
# create_or_update -- create
      - name: ApiManagementCreateUser
        text: apimgmt user create  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b --email foobar@outlook.com --first-name foo --last-name bar --confirmation signup
      - name: ApiManagementUpdateUser
        text: apimgmt user create  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b --email foobar@outlook.com --first-name foo --last-name bar
      - name: ApiManagementDeleteUser
        text: apimgmt user create  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
"""

helps['apimgmt user update'] = """
    type: command
    short-summary: update a apimgmt user.
    examples:
# create_or_update -- update
      - name: ApiManagementCreateUser
        text: apimgmt user update  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b --email foobar@outlook.com --first-name foo --last-name bar --confirmation signup
      - name: ApiManagementUpdateUser
        text: apimgmt user update  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b --email foobar@outlook.com --first-name foo --last-name bar
      - name: ApiManagementDeleteUser
        text: apimgmt user update  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
"""

helps['apimgmt user delete'] = """
    type: command
    short-summary: delete a apimgmt user.
    examples:
# delete -- delete
      - name: ApiManagementCreateUser
        text: apimgmt user delete  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
      - name: ApiManagementUpdateUser
        text: apimgmt user delete  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
      - name: ApiManagementDeleteUser
        text: apimgmt user delete  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
"""

helps['apimgmt user list'] = """
    type: command
    short-summary: list a apimgmt user.
    examples:
# list_by_service -- list
      - name: ApiManagementCreateUser
        text: apimgmt user list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementUpdateUser
        text: apimgmt user list  --resource-group rg1 --service-name apimService1
      - name: ApiManagementDeleteUser
        text: apimgmt user list  --resource-group rg1 --service-name apimService1
"""

helps['apimgmt user show'] = """
    type: command
    short-summary: show a apimgmt user.
    examples:
# get -- show
      - name: ApiManagementCreateUser
        text: apimgmt user show  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
      - name: ApiManagementUpdateUser
        text: apimgmt user show  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
      - name: ApiManagementDeleteUser
        text: apimgmt user show  --resource-group rg1 --service-name apimService1 --user-id 5931a75ae4bbd512288c680b
"""