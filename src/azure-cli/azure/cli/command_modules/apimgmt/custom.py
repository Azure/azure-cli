# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
import json

# module equivalent: azure_rm_apimanagementapi
def create_apimgmt_api(cmd, client,
                       resource_group,
                       service_name,
                       api_id,
                       path,
                       description=None,
                       authentication_settings=None,
                       subscription_key_parameter_names=None,
                       type=None,
                       api_revision=None,
                       api_version=None,
                       is_current=None,
                       api_revision_description=None,
                       api_version_description=None,
                       api_version_set_id=None,
                       subscription_required=None,
                       source_api_id=None,
                       display_name=None,
                       service_url=None,
                       protocols=None,
                       api_version_set=None,
                       value=None,
                       format=None,
                       wsdl_selector=None,
                       api_type=None):
    body={}
    body['description'] = description # str
    body['authentication_settings'] = json.loads(authentication_settings) if isinstance(authentication_settings, str) else authentication_settings
    body['subscription_key_parameter_names'] = json.loads(subscription_key_parameter_names) if isinstance(subscription_key_parameter_names, str) else subscription_key_parameter_names
    body['type'] = type # str
    body['api_revision'] = api_revision # str
    body['api_version'] = api_version # str
    body['is_current'] = is_current # boolean
    body['api_revision_description'] = api_revision_description # str
    body['api_version_description'] = api_version_description # str
    body['api_version_set_id'] = api_version_set_id # str
    body['subscription_required'] = subscription_required # boolean
    body['source_api_id'] = source_api_id # str
    body['display_name'] = display_name # str
    body['service_url'] = service_url # str
    body['path'] = path # str
    body['protocols'] = json.loads(protocols) if isinstance(protocols, str) else protocols
    body['api_version_set'] = json.loads(api_version_set) if isinstance(api_version_set, str) else api_version_set
    body['value'] = value # str
    body['format'] = format # str
    body['wsdl_selector'] = json.loads(wsdl_selector) if isinstance(wsdl_selector, str) else wsdl_selector
    body['api_type'] = api_type # str
    return client.api.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, parameters=body)

# module equivalent: azure_rm_apimanagementapi
def update_apimgmt_api(cmd, client,
                       resource_group,
                       service_name,
                       api_id,
                       path,
                       description=None,
                       authentication_settings=None,
                       subscription_key_parameter_names=None,
                       type=None,
                       api_revision=None,
                       api_version=None,
                       is_current=None,
                       api_revision_description=None,
                       api_version_description=None,
                       api_version_set_id=None,
                       subscription_required=None,
                       source_api_id=None,
                       display_name=None,
                       service_url=None,
                       protocols=None,
                       api_version_set=None,
                       value=None,
                       format=None,
                       wsdl_selector=None,
                       api_type=None):
    body={}
    body['description'] = description # str
    body['authentication_settings'] = json.loads(authentication_settings) if isinstance(authentication_settings, str) else authentication_settings
    body['subscription_key_parameter_names'] = json.loads(subscription_key_parameter_names) if isinstance(subscription_key_parameter_names, str) else subscription_key_parameter_names
    body['type'] = type # str
    body['api_revision'] = api_revision # str
    body['api_version'] = api_version # str
    body['is_current'] = is_current # boolean
    body['api_revision_description'] = api_revision_description # str
    body['api_version_description'] = api_version_description # str
    body['api_version_set_id'] = api_version_set_id # str
    body['subscription_required'] = subscription_required # boolean
    body['source_api_id'] = source_api_id # str
    body['display_name'] = display_name # str
    body['service_url'] = service_url # str
    body['path'] = path # str
    body['protocols'] = json.loads(protocols) if isinstance(protocols, str) else protocols
    body['api_version_set'] = json.loads(api_version_set) if isinstance(api_version_set, str) else api_version_set
    body['value'] = value # str
    body['format'] = format # str
    body['wsdl_selector'] = json.loads(wsdl_selector) if isinstance(wsdl_selector, str) else wsdl_selector
    body['api_type'] = api_type # str
    return client.api.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, parameters=body)

# module equivalent: azure_rm_apimanagementapi
def delete_apimgmt_api(cmd, client,
                       resource_group,
                       service_name,
                       api_id):
    return client.api.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapi
def list_apimgmt_api(cmd, client,
                     resource_group,
                     service_name):
    if resource_group is not None and service_name is not None:
        return client.api.list_by_tags(resource_group_name=resource_group, service_name=service_name)
    else:
        return client.api.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementapi
def show_apimgmt_api(cmd, client,
                     resource_group,
                     service_name,
                     api_id):
    return client.api.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapirelease
def create_apimgmt_api_release(cmd, client,
                               resource_group,
                               service_name,
                               api_id,
                               release_id,
                               notes=None):
    body={}
    body['notes'] = notes # str
    return client.api_release.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, release_id=release_id, parameters=body)

# module equivalent: azure_rm_apimanagementapirelease
def update_apimgmt_api_release(cmd, client,
                               resource_group,
                               service_name,
                               api_id,
                               release_id,
                               notes=None):
    body={}
    body['notes'] = notes # str
    return client.api_release.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, release_id=release_id, parameters=body)

# module equivalent: azure_rm_apimanagementapirelease
def delete_apimgmt_api_release(cmd, client,
                               resource_group,
                               service_name,
                               api_id,
                               release_id):
    return client.api_release.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, release_id=release_id)

# module equivalent: azure_rm_apimanagementapirelease
def list_apimgmt_api_release(cmd, client,
                             resource_group,
                             service_name,
                             api_id):
    return client.api_release.list_by_service(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapirelease
def show_apimgmt_api_release(cmd, client,
                             resource_group,
                             service_name,
                             api_id,
                             release_id):
    return client.api_release.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, release_id=release_id)

# module equivalent: azure_rm_apimanagementapioperation
def create_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 service_name,
                                 api_id,
                                 operation_id,
                                 display_name,
                                 method,
                                 url_template,
                                 template_parameters=None,
                                 description=None,
                                 request=None,
                                 responses=None,
                                 policies=None):
    body={}
    body['template_parameters'] = json.loads(template_parameters) if isinstance(template_parameters, str) else template_parameters
    body['description'] = description # str
    body['request'] = json.loads(request) if isinstance(request, str) else request
    body['responses'] = json.loads(responses) if isinstance(responses, str) else responses
    body['policies'] = policies # str
    body['display_name'] = display_name # str
    body['method'] = method # str
    body['url_template'] = url_template # str
    return client.api_operation.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id, parameters=body)

# module equivalent: azure_rm_apimanagementapioperation
def update_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 service_name,
                                 api_id,
                                 operation_id,
                                 display_name,
                                 method,
                                 url_template,
                                 template_parameters=None,
                                 description=None,
                                 request=None,
                                 responses=None,
                                 policies=None):
    body={}
    body['template_parameters'] = json.loads(template_parameters) if isinstance(template_parameters, str) else template_parameters
    body['description'] = description # str
    body['request'] = json.loads(request) if isinstance(request, str) else request
    body['responses'] = json.loads(responses) if isinstance(responses, str) else responses
    body['policies'] = policies # str
    body['display_name'] = display_name # str
    body['method'] = method # str
    body['url_template'] = url_template # str
    return client.api_operation.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id, parameters=body)

# module equivalent: azure_rm_apimanagementapioperation
def delete_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 service_name,
                                 api_id,
                                 operation_id):
    return client.api_operation.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id)

# module equivalent: azure_rm_apimanagementapioperation
def list_apimgmt_api_operation(cmd, client,
                               resource_group,
                               service_name,
                               api_id):
    return client.api_operation.list_by_api(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapioperation
def show_apimgmt_api_operation(cmd, client,
                               resource_group,
                               service_name,
                               api_id,
                               operation_id):
    return client.api_operation.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id)

# module equivalent: azure_rm_apimanagementapioperationpolicy
def create_apimgmt_api_operation_policy(cmd, client,
                                        resource_group,
                                        service_name,
                                        api_id,
                                        operation_id,
                                        policy_id,
                                        value,
                                        format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.api_operation_policy.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementapioperationpolicy
def update_apimgmt_api_operation_policy(cmd, client,
                                        resource_group,
                                        service_name,
                                        api_id,
                                        operation_id,
                                        policy_id,
                                        value,
                                        format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.api_operation_policy.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementapioperationpolicy
def delete_apimgmt_api_operation_policy(cmd, client,
                                        resource_group,
                                        service_name,
                                        api_id,
                                        operation_id,
                                        policy_id):
    return client.api_operation_policy.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id, policy_id=policy_id)

# module equivalent: azure_rm_apimanagementapioperationpolicy
def list_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      operation_id):
    return client.api_operation_policy.list_by_operation(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id)

# module equivalent: azure_rm_apimanagementapioperationpolicy
def show_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      operation_id,
                                      policy_id,
                                      format=None):
    return client.api_operation_policy.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, operation_id=operation_id, format=format, policy_id=policy_id)

# module equivalent: azure_rm_apimanagementtag
def create_apimgmt_tag(cmd, client,
                       resource_group,
                       service_name,
                       tag_id,
                       display_name):
    body={}
    body['display_name'] = display_name # str
    return client.tag.create_or_update(resource_group_name=resource_group, service_name=service_name, tag_id=tag_id, parameters=body)

# module equivalent: azure_rm_apimanagementtag
def update_apimgmt_tag(cmd, client,
                       resource_group,
                       service_name,
                       tag_id,
                       display_name):
    body={}
    body['display_name'] = display_name # str
    return client.tag.create_or_update(resource_group_name=resource_group, service_name=service_name, tag_id=tag_id, parameters=body)

# module equivalent: azure_rm_apimanagementtag
def delete_apimgmt_tag(cmd, client,
                       resource_group,
                       service_name,
                       tag_id):
    return client.tag.delete(resource_group_name=resource_group, service_name=service_name, tag_id=tag_id)

# module equivalent: azure_rm_apimanagementtag
def list_apimgmt_tag(cmd, client,
                     resource_group,
                     service_name):
    if resource_group is not None and service_name is not None:
        return client.tag.list_by_operation(resource_group_name=resource_group, service_name=service_name)
    elif resource_group is not None and service_name is not None:
        return client.tag.list_by_product(resource_group_name=resource_group, service_name=service_name)
    elif resource_group is not None and service_name is not None:
        return client.tag.list_by_api(resource_group_name=resource_group, service_name=service_name)
    else:
        return client.tag.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementtag
def show_apimgmt_tag(cmd, client,
                     resource_group,
                     service_name,
                     tag_id):
    return client.tag.get(resource_group_name=resource_group, service_name=service_name, tag_id=tag_id)

# module equivalent: azure_rm_apimanagementapipolicy
def create_apimgmt_api_policy(cmd, client,
                              resource_group,
                              service_name,
                              api_id,
                              policy_id,
                              value,
                              format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.api_policy.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementapipolicy
def update_apimgmt_api_policy(cmd, client,
                              resource_group,
                              service_name,
                              api_id,
                              policy_id,
                              value,
                              format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.api_policy.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementapipolicy
def delete_apimgmt_api_policy(cmd, client,
                              resource_group,
                              service_name,
                              api_id,
                              policy_id):
    return client.api_policy.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, policy_id=policy_id)

# module equivalent: azure_rm_apimanagementapipolicy
def list_apimgmt_api_policy(cmd, client,
                            resource_group,
                            service_name,
                            api_id):
    return client.api_policy.list_by_api(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapipolicy
def show_apimgmt_api_policy(cmd, client,
                            resource_group,
                            service_name,
                            api_id,
                            policy_id,
                            format=None):
    return client.api_policy.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, policy_id=policy_id, format=format)

# module equivalent: azure_rm_apimanagementapischema
def create_apimgmt_api_schema(cmd, client,
                              resource_group,
                              service_name,
                              api_id,
                              schema_id,
                              content_type,
                              document=None):
    body={}
    body['content_type'] = content_type # str
    body['document'] = json.loads(document) if isinstance(document, str) else document
    return client.api_schema.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, schema_id=schema_id, parameters=body)

# module equivalent: azure_rm_apimanagementapischema
def update_apimgmt_api_schema(cmd, client,
                              resource_group,
                              service_name,
                              api_id,
                              schema_id,
                              content_type,
                              document=None):
    body={}
    body['content_type'] = content_type # str
    body['document'] = json.loads(document) if isinstance(document, str) else document
    return client.api_schema.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, schema_id=schema_id, parameters=body)

# module equivalent: azure_rm_apimanagementapischema
def delete_apimgmt_api_schema(cmd, client,
                              resource_group,
                              service_name,
                              api_id,
                              schema_id):
    return client.api_schema.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, schema_id=schema_id)

# module equivalent: azure_rm_apimanagementapischema
def list_apimgmt_api_schema(cmd, client,
                            resource_group,
                            service_name,
                            api_id):
    return client.api_schema.list_by_api(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapischema
def show_apimgmt_api_schema(cmd, client,
                            resource_group,
                            service_name,
                            api_id,
                            schema_id):
    return client.api_schema.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, schema_id=schema_id)

# module equivalent: azure_rm_apimanagementapidiagnostic
def create_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  service_name,
                                  api_id,
                                  diagnostic_id,
                                  logger_id,
                                  always_log=None,
                                  sampling=None,
                                  frontend=None,
                                  backend=None,
                                  enable_http_correlation_headers=None):
    body={}
    body['always_log'] = always_log # str
    body['logger_id'] = logger_id # str
    body['sampling'] = json.loads(sampling) if isinstance(sampling, str) else sampling
    body['frontend'] = json.loads(frontend) if isinstance(frontend, str) else frontend
    body['backend'] = json.loads(backend) if isinstance(backend, str) else backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers # boolean
    return client.api_diagnostic.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, diagnostic_id=diagnostic_id, parameters=body)

# module equivalent: azure_rm_apimanagementapidiagnostic
def update_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  service_name,
                                  api_id,
                                  diagnostic_id,
                                  logger_id,
                                  always_log=None,
                                  sampling=None,
                                  frontend=None,
                                  backend=None,
                                  enable_http_correlation_headers=None):
    body={}
    body['always_log'] = always_log # str
    body['logger_id'] = logger_id # str
    body['sampling'] = json.loads(sampling) if isinstance(sampling, str) else sampling
    body['frontend'] = json.loads(frontend) if isinstance(frontend, str) else frontend
    body['backend'] = json.loads(backend) if isinstance(backend, str) else backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers # boolean
    return client.api_diagnostic.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, diagnostic_id=diagnostic_id, parameters=body)

# module equivalent: azure_rm_apimanagementapidiagnostic
def delete_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  service_name,
                                  api_id,
                                  diagnostic_id):
    return client.api_diagnostic.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, diagnostic_id=diagnostic_id)

# module equivalent: azure_rm_apimanagementapidiagnostic
def list_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                service_name,
                                api_id):
    return client.api_diagnostic.list_by_service(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapidiagnostic
def show_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                service_name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, diagnostic_id=diagnostic_id)

# module equivalent: azure_rm_apimanagementapiissue
def create_apimgmt_api_issue(cmd, client,
                             resource_group,
                             service_name,
                             api_id,
                             issue_id,
                             title,
                             description,
                             user_id,
                             created_date=None,
                             state=None):
    body={}
    body['created_date'] = created_date # datetime
    body['state'] = state # str
    body['title'] = title # str
    body['description'] = description # str
    body['user_id'] = user_id # str
    return client.api_issue.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiissue
def update_apimgmt_api_issue(cmd, client,
                             resource_group,
                             service_name,
                             api_id,
                             issue_id,
                             title,
                             description,
                             user_id,
                             created_date=None,
                             state=None):
    body={}
    body['created_date'] = created_date # datetime
    body['state'] = state # str
    body['title'] = title # str
    body['description'] = description # str
    body['user_id'] = user_id # str
    return client.api_issue.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiissue
def delete_apimgmt_api_issue(cmd, client,
                             resource_group,
                             service_name,
                             api_id,
                             issue_id):
    return client.api_issue.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id)

# module equivalent: azure_rm_apimanagementapiissue
def list_apimgmt_api_issue(cmd, client,
                           resource_group,
                           service_name,
                           api_id):
    return client.api_issue.list_by_service(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapiissue
def show_apimgmt_api_issue(cmd, client,
                           resource_group,
                           service_name,
                           api_id,
                           issue_id):
    return client.api_issue.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id)

# module equivalent: azure_rm_apimanagementapiissuecomment
def create_apimgmt_api_issue_comment(cmd, client,
                                     resource_group,
                                     service_name,
                                     api_id,
                                     issue_id,
                                     comment_id,
                                     text,
                                     user_id,
                                     created_date=None):
    body={}
    body['text'] = text # str
    body['created_date'] = created_date # datetime
    body['user_id'] = user_id # str
    return client.api_issue_comment.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, comment_id=comment_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiissuecomment
def update_apimgmt_api_issue_comment(cmd, client,
                                     resource_group,
                                     service_name,
                                     api_id,
                                     issue_id,
                                     comment_id,
                                     text,
                                     user_id,
                                     created_date=None):
    body={}
    body['text'] = text # str
    body['created_date'] = created_date # datetime
    body['user_id'] = user_id # str
    return client.api_issue_comment.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, comment_id=comment_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiissuecomment
def delete_apimgmt_api_issue_comment(cmd, client,
                                     resource_group,
                                     service_name,
                                     api_id,
                                     issue_id,
                                     comment_id):
    return client.api_issue_comment.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, comment_id=comment_id)

# module equivalent: azure_rm_apimanagementapiissuecomment
def list_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   service_name,
                                   api_id,
                                   issue_id):
    return client.api_issue_comment.list_by_service(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id)

# module equivalent: azure_rm_apimanagementapiissuecomment
def show_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   service_name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, comment_id=comment_id)

# module equivalent: azure_rm_apimanagementapiissueattachment
def create_apimgmt_api_issue_attachment(cmd, client,
                                        resource_group,
                                        service_name,
                                        api_id,
                                        issue_id,
                                        attachment_id,
                                        title,
                                        content_format,
                                        content):
    body={}
    body['title'] = title # str
    body['content_format'] = content_format # str
    body['content'] = content # str
    return client.api_issue_attachment.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiissueattachment
def update_apimgmt_api_issue_attachment(cmd, client,
                                        resource_group,
                                        service_name,
                                        api_id,
                                        issue_id,
                                        attachment_id,
                                        title,
                                        content_format,
                                        content):
    body={}
    body['title'] = title # str
    body['content_format'] = content_format # str
    body['content'] = content # str
    return client.api_issue_attachment.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiissueattachment
def delete_apimgmt_api_issue_attachment(cmd, client,
                                        resource_group,
                                        service_name,
                                        api_id,
                                        issue_id,
                                        attachment_id):
    return client.api_issue_attachment.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id)

# module equivalent: azure_rm_apimanagementapiissueattachment
def list_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      issue_id):
    return client.api_issue_attachment.list_by_service(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id)

# module equivalent: azure_rm_apimanagementapiissueattachment
def show_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id)

# module equivalent: azure_rm_apimanagementapitagdescription
def create_apimgmt_api_tagdescription(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      tag_id,
                                      description=None,
                                      external_docs_url=None,
                                      external_docs_description=None):
    body={}
    body['description'] = description # str
    body['external_docs_url'] = external_docs_url # str
    body['external_docs_description'] = external_docs_description # str
    return client.api_tag_description.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, tag_id=tag_id, parameters=body)

# module equivalent: azure_rm_apimanagementapitagdescription
def update_apimgmt_api_tagdescription(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      tag_id,
                                      description=None,
                                      external_docs_url=None,
                                      external_docs_description=None):
    body={}
    body['description'] = description # str
    body['external_docs_url'] = external_docs_url # str
    body['external_docs_description'] = external_docs_description # str
    return client.api_tag_description.create_or_update(resource_group_name=resource_group, service_name=service_name, api_id=api_id, tag_id=tag_id, parameters=body)

# module equivalent: azure_rm_apimanagementapitagdescription
def delete_apimgmt_api_tagdescription(cmd, client,
                                      resource_group,
                                      service_name,
                                      api_id,
                                      tag_id):
    return client.api_tag_description.delete(resource_group_name=resource_group, service_name=service_name, api_id=api_id, tag_id=tag_id)

# module equivalent: azure_rm_apimanagementapitagdescription
def list_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    service_name,
                                    api_id):
    return client.api_tag_description.list_by_service(resource_group_name=resource_group, service_name=service_name, api_id=api_id)

# module equivalent: azure_rm_apimanagementapitagdescription
def show_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    service_name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.get(resource_group_name=resource_group, service_name=service_name, api_id=api_id, tag_id=tag_id)

# module equivalent: azure_rm_apimanagementapiversionset
def create_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 service_name,
                                 version_set_id,
                                 display_name,
                                 versioning_scheme,
                                 description=None,
                                 version_query_name=None,
                                 version_header_name=None):
    body={}
    body['description'] = description # str
    body['version_query_name'] = version_query_name # str
    body['version_header_name'] = version_header_name # str
    body['display_name'] = display_name # str
    body['versioning_scheme'] = versioning_scheme # str
    return client.api_version_set.create_or_update(resource_group_name=resource_group, service_name=service_name, version_set_id=version_set_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiversionset
def update_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 service_name,
                                 version_set_id,
                                 display_name,
                                 versioning_scheme,
                                 description=None,
                                 version_query_name=None,
                                 version_header_name=None):
    body={}
    body['description'] = description # str
    body['version_query_name'] = version_query_name # str
    body['version_header_name'] = version_header_name # str
    body['display_name'] = display_name # str
    body['versioning_scheme'] = versioning_scheme # str
    return client.api_version_set.create_or_update(resource_group_name=resource_group, service_name=service_name, version_set_id=version_set_id, parameters=body)

# module equivalent: azure_rm_apimanagementapiversionset
def delete_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 service_name,
                                 version_set_id):
    return client.api_version_set.delete(resource_group_name=resource_group, service_name=service_name, version_set_id=version_set_id)

# module equivalent: azure_rm_apimanagementapiversionset
def list_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               service_name):
    return client.api_version_set.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementapiversionset
def show_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               service_name,
                               version_set_id):
    return client.api_version_set.get(resource_group_name=resource_group, service_name=service_name, version_set_id=version_set_id)

# module equivalent: azure_rm_apimanagementauthorizationserver
def create_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       service_name,
                                       authsid,
                                       display_name,
                                       client_registration_endpoint,
                                       authorization_endpoint,
                                       grant_types,
                                       client_id,
                                       description=None,
                                       authorization_methods=None,
                                       client_authentication_method=None,
                                       token_body_parameters=None,
                                       token_endpoint=None,
                                       support_state=None,
                                       default_scope=None,
                                       bearer_token_sending_methods=None,
                                       client_secret=None,
                                       resource_owner_username=None,
                                       resource_owner_password=None):
    body={}
    body['description'] = description # str
    body['authorization_methods'] = json.loads(authorization_methods) if isinstance(authorization_methods, str) else authorization_methods
    body['client_authentication_method'] = json.loads(client_authentication_method) if isinstance(client_authentication_method, str) else client_authentication_method
    body['token_body_parameters'] = json.loads(token_body_parameters) if isinstance(token_body_parameters, str) else token_body_parameters
    body['token_endpoint'] = token_endpoint # str
    body['support_state'] = support_state # boolean
    body['default_scope'] = default_scope # str
    body['bearer_token_sending_methods'] = json.loads(bearer_token_sending_methods) if isinstance(bearer_token_sending_methods, str) else bearer_token_sending_methods
    body['client_secret'] = client_secret # str
    body['resource_owner_username'] = resource_owner_username # str
    body['resource_owner_password'] = resource_owner_password # str
    body['display_name'] = display_name # str
    body['client_registration_endpoint'] = client_registration_endpoint # str
    body['authorization_endpoint'] = authorization_endpoint # str
    body['grant_types'] = json.loads(grant_types) if isinstance(grant_types, str) else grant_types
    body['client_id'] = client_id # str
    return client.authorization_server.create_or_update(resource_group_name=resource_group, service_name=service_name, authsid=authsid, parameters=body)

# module equivalent: azure_rm_apimanagementauthorizationserver
def update_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       service_name,
                                       authsid,
                                       display_name,
                                       client_registration_endpoint,
                                       authorization_endpoint,
                                       grant_types,
                                       client_id,
                                       description=None,
                                       authorization_methods=None,
                                       client_authentication_method=None,
                                       token_body_parameters=None,
                                       token_endpoint=None,
                                       support_state=None,
                                       default_scope=None,
                                       bearer_token_sending_methods=None,
                                       client_secret=None,
                                       resource_owner_username=None,
                                       resource_owner_password=None):
    body={}
    body['description'] = description # str
    body['authorization_methods'] = json.loads(authorization_methods) if isinstance(authorization_methods, str) else authorization_methods
    body['client_authentication_method'] = json.loads(client_authentication_method) if isinstance(client_authentication_method, str) else client_authentication_method
    body['token_body_parameters'] = json.loads(token_body_parameters) if isinstance(token_body_parameters, str) else token_body_parameters
    body['token_endpoint'] = token_endpoint # str
    body['support_state'] = support_state # boolean
    body['default_scope'] = default_scope # str
    body['bearer_token_sending_methods'] = json.loads(bearer_token_sending_methods) if isinstance(bearer_token_sending_methods, str) else bearer_token_sending_methods
    body['client_secret'] = client_secret # str
    body['resource_owner_username'] = resource_owner_username # str
    body['resource_owner_password'] = resource_owner_password # str
    body['display_name'] = display_name # str
    body['client_registration_endpoint'] = client_registration_endpoint # str
    body['authorization_endpoint'] = authorization_endpoint # str
    body['grant_types'] = json.loads(grant_types) if isinstance(grant_types, str) else grant_types
    body['client_id'] = client_id # str
    return client.authorization_server.create_or_update(resource_group_name=resource_group, service_name=service_name, authsid=authsid, parameters=body)

# module equivalent: azure_rm_apimanagementauthorizationserver
def delete_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       service_name,
                                       authsid):
    return client.authorization_server.delete(resource_group_name=resource_group, service_name=service_name, authsid=authsid)

# module equivalent: azure_rm_apimanagementauthorizationserver
def list_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     service_name):
    return client.authorization_server.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementauthorizationserver
def show_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     service_name,
                                     authsid):
    return client.authorization_server.get(resource_group_name=resource_group, service_name=service_name, authsid=authsid)

# module equivalent: azure_rm_apimanagementbackend
def create_apimgmt_backend(cmd, client,
                           resource_group,
                           service_name,
                           backend_id,
                           url,
                           protocol,
                           title=None,
                           description=None,
                           resource_id=None,
                           service_fabric_cluster=None,
                           credentials=None,
                           proxy=None,
                           tls=None):
    body={}
    body['title'] = title # str
    body['description'] = description # str
    body['resource_id'] = resource_id # str
    body['service_fabric_cluster'] = json.loads(service_fabric_cluster) if isinstance(service_fabric_cluster, str) else service_fabric_cluster
    body['credentials'] = json.loads(credentials) if isinstance(credentials, str) else credentials
    body['proxy'] = json.loads(proxy) if isinstance(proxy, str) else proxy
    body['tls'] = json.loads(tls) if isinstance(tls, str) else tls
    body['url'] = url # str
    body['protocol'] = protocol # str
    return client.backend.create_or_update(resource_group_name=resource_group, service_name=service_name, backend_id=backend_id, parameters=body)

# module equivalent: azure_rm_apimanagementbackend
def update_apimgmt_backend(cmd, client,
                           resource_group,
                           service_name,
                           backend_id,
                           url,
                           protocol,
                           title=None,
                           description=None,
                           resource_id=None,
                           service_fabric_cluster=None,
                           credentials=None,
                           proxy=None,
                           tls=None):
    body={}
    body['title'] = title # str
    body['description'] = description # str
    body['resource_id'] = resource_id # str
    body['service_fabric_cluster'] = json.loads(service_fabric_cluster) if isinstance(service_fabric_cluster, str) else service_fabric_cluster
    body['credentials'] = json.loads(credentials) if isinstance(credentials, str) else credentials
    body['proxy'] = json.loads(proxy) if isinstance(proxy, str) else proxy
    body['tls'] = json.loads(tls) if isinstance(tls, str) else tls
    body['url'] = url # str
    body['protocol'] = protocol # str
    return client.backend.create_or_update(resource_group_name=resource_group, service_name=service_name, backend_id=backend_id, parameters=body)

# module equivalent: azure_rm_apimanagementbackend
def delete_apimgmt_backend(cmd, client,
                           resource_group,
                           service_name,
                           backend_id):
    return client.backend.delete(resource_group_name=resource_group, service_name=service_name, backend_id=backend_id)

# module equivalent: azure_rm_apimanagementbackend
def list_apimgmt_backend(cmd, client,
                         resource_group,
                         service_name):
    return client.backend.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementbackend
def show_apimgmt_backend(cmd, client,
                         resource_group,
                         service_name,
                         backend_id):
    return client.backend.get(resource_group_name=resource_group, service_name=service_name, backend_id=backend_id)

# module equivalent: azure_rm_apimanagementcache
def create_apimgmt_cache(cmd, client,
                         resource_group,
                         service_name,
                         cache_id,
                         connection_string,
                         description=None,
                         resource_id=None):
    body={}
    body['description'] = description # str
    body['connection_string'] = connection_string # str
    body['resource_id'] = resource_id # str
    return client.cache.create_or_update(resource_group_name=resource_group, service_name=service_name, cache_id=cache_id, parameters=body)

# module equivalent: azure_rm_apimanagementcache
def update_apimgmt_cache(cmd, client,
                         resource_group,
                         service_name,
                         cache_id,
                         connection_string,
                         description=None,
                         resource_id=None):
    body={}
    body['description'] = description # str
    body['connection_string'] = connection_string # str
    body['resource_id'] = resource_id # str
    return client.cache.create_or_update(resource_group_name=resource_group, service_name=service_name, cache_id=cache_id, parameters=body)

# module equivalent: azure_rm_apimanagementcache
def delete_apimgmt_cache(cmd, client,
                         resource_group,
                         service_name,
                         cache_id):
    return client.cache.delete(resource_group_name=resource_group, service_name=service_name, cache_id=cache_id)

# module equivalent: azure_rm_apimanagementcache
def list_apimgmt_cache(cmd, client,
                       resource_group,
                       service_name):
    return client.cache.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementcache
def show_apimgmt_cache(cmd, client,
                       resource_group,
                       service_name,
                       cache_id):
    return client.cache.get(resource_group_name=resource_group, service_name=service_name, cache_id=cache_id)

# module equivalent: azure_rm_apimanagementcertificate
def create_apimgmt_certificate(cmd, client,
                               resource_group,
                               service_name,
                               certificate_id,
                               data,
                               password):
    body={}
    body['data'] = data # str
    body['password'] = password # str
    return client.certificate.create_or_update(resource_group_name=resource_group, service_name=service_name, certificate_id=certificate_id, parameters=body)

# module equivalent: azure_rm_apimanagementcertificate
def update_apimgmt_certificate(cmd, client,
                               resource_group,
                               service_name,
                               certificate_id,
                               data,
                               password):
    body={}
    body['data'] = data # str
    body['password'] = password # str
    return client.certificate.create_or_update(resource_group_name=resource_group, service_name=service_name, certificate_id=certificate_id, parameters=body)

# module equivalent: azure_rm_apimanagementcertificate
def delete_apimgmt_certificate(cmd, client,
                               resource_group,
                               service_name,
                               certificate_id):
    return client.certificate.delete(resource_group_name=resource_group, service_name=service_name, certificate_id=certificate_id)

# module equivalent: azure_rm_apimanagementcertificate
def list_apimgmt_certificate(cmd, client,
                             resource_group,
                             service_name):
    return client.certificate.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementcertificate
def show_apimgmt_certificate(cmd, client,
                             resource_group,
                             service_name,
                             certificate_id):
    return client.certificate.get(resource_group_name=resource_group, service_name=service_name, certificate_id=certificate_id)

# module equivalent: azure_rm_apimanagementservice
def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   publisher_email,
                   publisher_name,
                   sku_name,
                   location,
                   tags=None,
                   notification_sender_email=None,
                   hostname_configurations=None,
                   virtual_network_configuration=None,
                   additional_locations=None,
                   custom_properties=None,
                   certificates=None,
                   enable_client_certificate=None,
                   virtual_network_type=None,
                   sku_capacity=None,
                   identity=None):
    body={}
    body['tags'] = tags # dictionary
    body['notification_sender_email'] = notification_sender_email # str
    body['hostname_configurations'] = json.loads(hostname_configurations) if isinstance(hostname_configurations, str) else hostname_configurations
    body['virtual_network_configuration'] = json.loads(virtual_network_configuration) if isinstance(virtual_network_configuration, str) else virtual_network_configuration
    body['additional_locations'] = json.loads(additional_locations) if isinstance(additional_locations, str) else additional_locations
    body['custom_properties'] = custom_properties # dictionary
    body['certificates'] = json.loads(certificates) if isinstance(certificates, str) else certificates
    body['enable_client_certificate'] = enable_client_certificate # boolean
    body['virtual_network_type'] = virtual_network_type # str
    body['publisher_email'] = publisher_email # str
    body['publisher_name'] = publisher_name # str
    body.setdefault('sku', {})['name'] = sku_name # str
    body.setdefault('sku', {})['capacity'] = sku_capacity # number
    body['identity'] = json.loads(identity) if isinstance(identity, str) else identity
    body['location'] = location # str
    return client.api_management_service.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementservice
def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   publisher_email,
                   publisher_name,
                   sku_name,
                   location,
                   tags=None,
                   notification_sender_email=None,
                   hostname_configurations=None,
                   virtual_network_configuration=None,
                   additional_locations=None,
                   custom_properties=None,
                   certificates=None,
                   enable_client_certificate=None,
                   virtual_network_type=None,
                   sku_capacity=None,
                   identity=None):
    body={}
    body['tags'] = tags # dictionary
    body['notification_sender_email'] = notification_sender_email # str
    body['hostname_configurations'] = json.loads(hostname_configurations) if isinstance(hostname_configurations, str) else hostname_configurations
    body['virtual_network_configuration'] = json.loads(virtual_network_configuration) if isinstance(virtual_network_configuration, str) else virtual_network_configuration
    body['additional_locations'] = json.loads(additional_locations) if isinstance(additional_locations, str) else additional_locations
    body['custom_properties'] = custom_properties # dictionary
    body['certificates'] = json.loads(certificates) if isinstance(certificates, str) else certificates
    body['enable_client_certificate'] = enable_client_certificate # boolean
    body['virtual_network_type'] = virtual_network_type # str
    body['publisher_email'] = publisher_email # str
    body['publisher_name'] = publisher_name # str
    body.setdefault('sku', {})['name'] = sku_name # str
    body.setdefault('sku', {})['capacity'] = sku_capacity # number
    body['identity'] = json.loads(identity) if isinstance(identity, str) else identity
    body['location'] = location # str
    return client.api_management_service.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementservice
def delete_apimgmt(cmd, client,
                   resource_group,
                   name):
    return client.api_management_service.delete(resource_group_name=resource_group, service_name=name)

# module equivalent: azure_rm_apimanagementservice
def list_apimgmt(cmd, client,
                 resource_group):
    if resource_group is not None:
        return client.api_management_service.list_by_resource_group(resource_group_name=resource_group)
    else:
        return client.api_management_service.list()

# module equivalent: azure_rm_apimanagementservice
def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.get(resource_group_name=resource_group, service_name=name)

# module equivalent: azure_rm_apimanagementdiagnostic
def create_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              service_name,
                              diagnostic_id,
                              logger_id,
                              always_log=None,
                              sampling=None,
                              frontend=None,
                              backend=None,
                              enable_http_correlation_headers=None):
    body={}
    body['always_log'] = always_log # str
    body['logger_id'] = logger_id # str
    body['sampling'] = json.loads(sampling) if isinstance(sampling, str) else sampling
    body['frontend'] = json.loads(frontend) if isinstance(frontend, str) else frontend
    body['backend'] = json.loads(backend) if isinstance(backend, str) else backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers # boolean
    return client.diagnostic.create_or_update(resource_group_name=resource_group, service_name=service_name, diagnostic_id=diagnostic_id, parameters=body)

# module equivalent: azure_rm_apimanagementdiagnostic
def update_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              service_name,
                              diagnostic_id,
                              logger_id,
                              always_log=None,
                              sampling=None,
                              frontend=None,
                              backend=None,
                              enable_http_correlation_headers=None):
    body={}
    body['always_log'] = always_log # str
    body['logger_id'] = logger_id # str
    body['sampling'] = json.loads(sampling) if isinstance(sampling, str) else sampling
    body['frontend'] = json.loads(frontend) if isinstance(frontend, str) else frontend
    body['backend'] = json.loads(backend) if isinstance(backend, str) else backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers # boolean
    return client.diagnostic.create_or_update(resource_group_name=resource_group, service_name=service_name, diagnostic_id=diagnostic_id, parameters=body)

# module equivalent: azure_rm_apimanagementdiagnostic
def delete_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              service_name,
                              diagnostic_id):
    return client.diagnostic.delete(resource_group_name=resource_group, service_name=service_name, diagnostic_id=diagnostic_id)

# module equivalent: azure_rm_apimanagementdiagnostic
def list_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            service_name):
    return client.diagnostic.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementdiagnostic
def show_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            service_name,
                            diagnostic_id):
    return client.diagnostic.get(resource_group_name=resource_group, service_name=service_name, diagnostic_id=diagnostic_id)

# module equivalent: azure_rm_apimanagementemailtemplate
def create_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name,
                            subject=None,
                            title=None,
                            description=None,
                            body=None):
    body={}
    body['parameters'] = parameters # placeholder
    body['subject'] = subject # str
    body['title'] = title # str
    body['description'] = description # str
    body['body'] = body # str
    return client.email_template.create_or_update(resource_group_name=resource_group, service_name=service_name, template_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementemailtemplate
def update_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name,
                            subject=None,
                            title=None,
                            description=None,
                            body=None):
    body={}
    body['parameters'] = parameters # placeholder
    body['subject'] = subject # str
    body['title'] = title # str
    body['description'] = description # str
    body['body'] = body # str
    return client.email_template.create_or_update(resource_group_name=resource_group, service_name=service_name, template_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementemailtemplate
def delete_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name):
    return client.email_template.delete(resource_group_name=resource_group, service_name=service_name, template_name=name)

# module equivalent: azure_rm_apimanagementemailtemplate
def list_apimgmt_template(cmd, client,
                          resource_group,
                          service_name):
    return client.email_template.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementemailtemplate
def show_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.get(resource_group_name=resource_group, service_name=service_name, template_name=name)

# module equivalent: azure_rm_apimanagementgroup
def create_apimgmt_group(cmd, client,
                         resource_group,
                         service_name,
                         group_id,
                         display_name,
                         description=None,
                         type=None,
                         external_id=None):
    body={}
    body['display_name'] = display_name # str
    body['description'] = description # str
    body['type'] = type # str
    body['external_id'] = external_id # str
    return client.group.create_or_update(resource_group_name=resource_group, service_name=service_name, group_id=group_id, parameters=body)

# module equivalent: azure_rm_apimanagementgroup
def update_apimgmt_group(cmd, client,
                         resource_group,
                         service_name,
                         group_id,
                         display_name,
                         description=None,
                         type=None,
                         external_id=None):
    body={}
    body['display_name'] = display_name # str
    body['description'] = description # str
    body['type'] = type # str
    body['external_id'] = external_id # str
    return client.group.create_or_update(resource_group_name=resource_group, service_name=service_name, group_id=group_id, parameters=body)

# module equivalent: azure_rm_apimanagementgroup
def delete_apimgmt_group(cmd, client,
                         resource_group,
                         service_name,
                         group_id):
    return client.group.delete(resource_group_name=resource_group, service_name=service_name, group_id=group_id)

# module equivalent: azure_rm_apimanagementgroup
def list_apimgmt_group(cmd, client,
                       resource_group,
                       service_name):
    return client.group.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementgroup
def show_apimgmt_group(cmd, client,
                       resource_group,
                       service_name,
                       group_id):
    return client.group.get(resource_group_name=resource_group, service_name=service_name, group_id=group_id)

# module equivalent: azure_rm_apimanagementgroupuser
def create_apimgmt_group_user(cmd, client,
                              resource_group,
                              service_name,
                              group_id,
                              user_id,
                              state=None,
                              note=None,
                              identities=None,
                              first_name=None,
                              last_name=None,
                              email=None,
                              registration_date=None,
                              groups=None):
    body={}
    body['state'] = state # str
    body['note'] = note # str
    body['identities'] = json.loads(identities) if isinstance(identities, str) else identities
    body['first_name'] = first_name # str
    body['last_name'] = last_name # str
    body['email'] = email # str
    body['registration_date'] = registration_date # datetime
    body['groups'] = json.loads(groups) if isinstance(groups, str) else groups
    return client.group_user.create(resource_group_name=resource_group, service_name=service_name, group_id=group_id, user_id=user_id)

# module equivalent: azure_rm_apimanagementgroupuser
def delete_apimgmt_group_user(cmd, client,
                              resource_group,
                              service_name,
                              group_id,
                              user_id):
    return client.group_user.delete(resource_group_name=resource_group, service_name=service_name, group_id=group_id, user_id=user_id)

# module equivalent: azure_rm_apimanagementgroupuser
def list_apimgmt_group_user(cmd, client,
                            resource_group,
                            service_name,
                            group_id):
    return client.group_user.list(resource_group_name=resource_group, service_name=service_name, group_id=group_id)

# module equivalent: azure_rm_apimanagementidentityprovider
def create_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name,
                                    client_id,
                                    client_secret,
                                    type=None,
                                    allowed_tenants=None,
                                    authority=None,
                                    signup_policy_name=None,
                                    signin_policy_name=None,
                                    profile_editing_policy_name=None,
                                    password_reset_policy_name=None):
    body={}
    body['type'] = type # str
    body['allowed_tenants'] = json.loads(allowed_tenants) if isinstance(allowed_tenants, str) else allowed_tenants
    body['authority'] = authority # str
    body['signup_policy_name'] = signup_policy_name # str
    body['signin_policy_name'] = signin_policy_name # str
    body['profile_editing_policy_name'] = profile_editing_policy_name # str
    body['password_reset_policy_name'] = password_reset_policy_name # str
    body['client_id'] = client_id # str
    body['client_secret'] = client_secret # str
    return client.identity_provider.create_or_update(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementidentityprovider
def update_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name,
                                    client_id,
                                    client_secret,
                                    type=None,
                                    allowed_tenants=None,
                                    authority=None,
                                    signup_policy_name=None,
                                    signin_policy_name=None,
                                    profile_editing_policy_name=None,
                                    password_reset_policy_name=None):
    body={}
    body['type'] = type # str
    body['allowed_tenants'] = json.loads(allowed_tenants) if isinstance(allowed_tenants, str) else allowed_tenants
    body['authority'] = authority # str
    body['signup_policy_name'] = signup_policy_name # str
    body['signin_policy_name'] = signin_policy_name # str
    body['profile_editing_policy_name'] = profile_editing_policy_name # str
    body['password_reset_policy_name'] = password_reset_policy_name # str
    body['client_id'] = client_id # str
    body['client_secret'] = client_secret # str
    return client.identity_provider.create_or_update(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementidentityprovider
def delete_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name):
    return client.identity_provider.delete(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name)

# module equivalent: azure_rm_apimanagementidentityprovider
def list_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name):
    return client.identity_provider.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementidentityprovider
def show_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.get(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name)

# module equivalent: azure_rm_apimanagementlogger
def create_apimgmt_logger(cmd, client,
                          resource_group,
                          service_name,
                          logger_id,
                          logger_type,
                          credentials,
                          description=None,
                          is_buffered=None,
                          resource_id=None):
    body={}
    body['logger_type'] = logger_type # str
    body['description'] = description # str
    body['credentials'] = credentials # dictionary
    body['is_buffered'] = is_buffered # boolean
    body['resource_id'] = resource_id # str
    return client.logger.create_or_update(resource_group_name=resource_group, service_name=service_name, logger_id=logger_id, parameters=body)

# module equivalent: azure_rm_apimanagementlogger
def update_apimgmt_logger(cmd, client,
                          resource_group,
                          service_name,
                          logger_id,
                          logger_type,
                          credentials,
                          description=None,
                          is_buffered=None,
                          resource_id=None):
    body={}
    body['logger_type'] = logger_type # str
    body['description'] = description # str
    body['credentials'] = credentials # dictionary
    body['is_buffered'] = is_buffered # boolean
    body['resource_id'] = resource_id # str
    return client.logger.create_or_update(resource_group_name=resource_group, service_name=service_name, logger_id=logger_id, parameters=body)

# module equivalent: azure_rm_apimanagementlogger
def delete_apimgmt_logger(cmd, client,
                          resource_group,
                          service_name,
                          logger_id):
    return client.logger.delete(resource_group_name=resource_group, service_name=service_name, logger_id=logger_id)

# module equivalent: azure_rm_apimanagementlogger
def list_apimgmt_logger(cmd, client,
                        resource_group,
                        service_name):
    return client.logger.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementlogger
def show_apimgmt_logger(cmd, client,
                        resource_group,
                        service_name,
                        logger_id):
    return client.logger.get(resource_group_name=resource_group, service_name=service_name, logger_id=logger_id)

# module equivalent: azure_rm_apimanagementnotification
def create_apimgmt_notification(cmd, client,
                                resource_group,
                                service_name,
                                name,
                                title,
                                description=None,
                                recipients=None):
    body={}
    body['title'] = title # str
    body['description'] = description # str
    body['recipients'] = json.loads(recipients) if isinstance(recipients, str) else recipients
    return client.notification.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=name)

# module equivalent: azure_rm_apimanagementnotification
def update_apimgmt_notification(cmd, client,
                                resource_group,
                                service_name,
                                name,
                                title,
                                description=None,
                                recipients=None):
    body={}
    body['title'] = title # str
    body['description'] = description # str
    body['recipients'] = json.loads(recipients) if isinstance(recipients, str) else recipients
    return client.notification.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=name)

# module equivalent: azure_rm_apimanagementnotification
def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name):
    return client.notification.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementnotification
def show_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.get(resource_group_name=resource_group, service_name=service_name, notification_name=name)

# module equivalent: azure_rm_apimanagementnotificationrecipientuser
def create_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              notification_name,
                                              user_id):
    body={}
    return client.notification_recipient_user.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name, user_id=user_id)

# module equivalent: azure_rm_apimanagementnotificationrecipientuser
def update_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              notification_name,
                                              user_id):
    body={}
    return client.notification_recipient_user.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name, user_id=user_id)

# module equivalent: azure_rm_apimanagementnotificationrecipientuser
def delete_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              notification_name,
                                              user_id):
    return client.notification_recipient_user.delete(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name, user_id=user_id)

# module equivalent: azure_rm_apimanagementnotificationrecipientuser
def list_apimgmt_notification_recipientuser(cmd, client,
                                            resource_group,
                                            service_name,
                                            notification_name):
    return client.notification_recipient_user.list_by_notification(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name)

# module equivalent: azure_rm_apimanagementnotificationrecipientemail
def create_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               notification_name,
                                               email):
    body={}
    return client.notification_recipient_email.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name, email=email)

# module equivalent: azure_rm_apimanagementnotificationrecipientemail
def update_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               notification_name,
                                               email):
    body={}
    return client.notification_recipient_email.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name, email=email)

# module equivalent: azure_rm_apimanagementnotificationrecipientemail
def delete_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               notification_name,
                                               email):
    return client.notification_recipient_email.delete(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name, email=email)

# module equivalent: azure_rm_apimanagementnotificationrecipientemail
def list_apimgmt_notification_recipientemail(cmd, client,
                                             resource_group,
                                             service_name,
                                             notification_name):
    return client.notification_recipient_email.list_by_notification(resource_group_name=resource_group, service_name=service_name, notification_name=notification_name)

# module equivalent: azure_rm_apimanagementopenidconnectprovider
def create_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         service_name,
                                         opid,
                                         display_name,
                                         metadata_endpoint,
                                         client_id,
                                         description=None,
                                         client_secret=None):
    body={}
    body['display_name'] = display_name # str
    body['description'] = description # str
    body['metadata_endpoint'] = metadata_endpoint # str
    body['client_id'] = client_id # str
    body['client_secret'] = client_secret # str
    return client.open_id_connect_provider.create_or_update(resource_group_name=resource_group, service_name=service_name, opid=opid, parameters=body)

# module equivalent: azure_rm_apimanagementopenidconnectprovider
def update_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         service_name,
                                         opid,
                                         display_name,
                                         metadata_endpoint,
                                         client_id,
                                         description=None,
                                         client_secret=None):
    body={}
    body['display_name'] = display_name # str
    body['description'] = description # str
    body['metadata_endpoint'] = metadata_endpoint # str
    body['client_id'] = client_id # str
    body['client_secret'] = client_secret # str
    return client.open_id_connect_provider.create_or_update(resource_group_name=resource_group, service_name=service_name, opid=opid, parameters=body)

# module equivalent: azure_rm_apimanagementopenidconnectprovider
def delete_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         service_name,
                                         opid):
    return client.open_id_connect_provider.delete(resource_group_name=resource_group, service_name=service_name, opid=opid)

# module equivalent: azure_rm_apimanagementopenidconnectprovider
def list_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       service_name):
    return client.open_id_connect_provider.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementopenidconnectprovider
def show_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       service_name,
                                       opid):
    return client.open_id_connect_provider.get(resource_group_name=resource_group, service_name=service_name, opid=opid)

# module equivalent: azure_rm_apimanagementpolicy
def create_apimgmt_policy(cmd, client,
                          resource_group,
                          service_name,
                          policy_id,
                          value,
                          format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.policy.create_or_update(resource_group_name=resource_group, service_name=service_name, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementpolicy
def update_apimgmt_policy(cmd, client,
                          resource_group,
                          service_name,
                          policy_id,
                          value,
                          format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.policy.create_or_update(resource_group_name=resource_group, service_name=service_name, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementpolicy
def delete_apimgmt_policy(cmd, client,
                          resource_group,
                          service_name,
                          policy_id):
    return client.policy.delete(resource_group_name=resource_group, service_name=service_name, policy_id=policy_id)

# module equivalent: azure_rm_apimanagementpolicy
def list_apimgmt_policy(cmd, client,
                        resource_group,
                        service_name):
    return client.policy.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementpolicy
def show_apimgmt_policy(cmd, client,
                        resource_group,
                        service_name,
                        policy_id,
                        format=None):
    return client.policy.get(resource_group_name=resource_group, service_name=service_name, policy_id=policy_id, format=format)

# module equivalent: azure_rm_apimanagementsigninsetting
def create_apimgmt_portalsetting(cmd, client,
                                 resource_group,
                                 name,
                                 enabled=None):
    body={}
    body['enabled'] = enabled # boolean
    return client.sign_in_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementsigninsetting
def update_apimgmt_portalsetting(cmd, client,
                                 resource_group,
                                 name,
                                 enabled=None):
    body={}
    body['enabled'] = enabled # boolean
    return client.sign_in_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementsigninsetting
def show_apimgmt_portalsetting(cmd, client,
                               resource_group,
                               name):
    return client.sign_in_settings.get(resource_group_name=resource_group, service_name=name)

# module equivalent: azure_rm_apimanagementsignupsetting
def create_apimgmt_portalsetting(cmd, client,
                                 resource_group,
                                 name,
                                 enabled=None,
                                 terms_of_service=None):
    body={}
    body['enabled'] = enabled # boolean
    body['terms_of_service'] = json.loads(terms_of_service) if isinstance(terms_of_service, str) else terms_of_service
    return client.sign_up_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementsignupsetting
def update_apimgmt_portalsetting(cmd, client,
                                 resource_group,
                                 name,
                                 enabled=None,
                                 terms_of_service=None):
    body={}
    body['enabled'] = enabled # boolean
    body['terms_of_service'] = json.loads(terms_of_service) if isinstance(terms_of_service, str) else terms_of_service
    return client.sign_up_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementsignupsetting
def show_apimgmt_portalsetting(cmd, client,
                               resource_group,
                               name):
    return client.sign_up_settings.get(resource_group_name=resource_group, service_name=name)

# module equivalent: azure_rm_apimanagementdelegationsetting
def create_apimgmt_portalsetting(cmd, client,
                                 resource_group,
                                 name,
                                 url=None,
                                 validation_key=None,
                                 subscriptions=None,
                                 user_registration=None):
    body={}
    body['url'] = url # str
    body['validation_key'] = validation_key # str
    body['subscriptions'] = json.loads(subscriptions) if isinstance(subscriptions, str) else subscriptions
    body['user_registration'] = json.loads(user_registration) if isinstance(user_registration, str) else user_registration
    return client.delegation_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementdelegationsetting
def update_apimgmt_portalsetting(cmd, client,
                                 resource_group,
                                 name,
                                 url=None,
                                 validation_key=None,
                                 subscriptions=None,
                                 user_registration=None):
    body={}
    body['url'] = url # str
    body['validation_key'] = validation_key # str
    body['subscriptions'] = json.loads(subscriptions) if isinstance(subscriptions, str) else subscriptions
    body['user_registration'] = json.loads(user_registration) if isinstance(user_registration, str) else user_registration
    return client.delegation_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)

# module equivalent: azure_rm_apimanagementdelegationsetting
def show_apimgmt_portalsetting(cmd, client,
                               resource_group,
                               name):
    return client.delegation_settings.get(resource_group_name=resource_group, service_name=name)

# module equivalent: azure_rm_apimanagementproduct
def create_apimgmt_product(cmd, client,
                           resource_group,
                           service_name,
                           product_id,
                           display_name,
                           description=None,
                           terms=None,
                           subscription_required=None,
                           approval_required=None,
                           subscriptions_limit=None,
                           state=None):
    body={}
    body['description'] = description # str
    body['terms'] = terms # str
    body['subscription_required'] = subscription_required # boolean
    body['approval_required'] = approval_required # boolean
    body['subscriptions_limit'] = subscriptions_limit # number
    body['state'] = state # str
    body['display_name'] = display_name # str
    return client.product.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, parameters=body)

# module equivalent: azure_rm_apimanagementproduct
def update_apimgmt_product(cmd, client,
                           resource_group,
                           service_name,
                           product_id,
                           display_name,
                           description=None,
                           terms=None,
                           subscription_required=None,
                           approval_required=None,
                           subscriptions_limit=None,
                           state=None):
    body={}
    body['description'] = description # str
    body['terms'] = terms # str
    body['subscription_required'] = subscription_required # boolean
    body['approval_required'] = approval_required # boolean
    body['subscriptions_limit'] = subscriptions_limit # number
    body['state'] = state # str
    body['display_name'] = display_name # str
    return client.product.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, parameters=body)

# module equivalent: azure_rm_apimanagementproduct
def delete_apimgmt_product(cmd, client,
                           resource_group,
                           service_name,
                           product_id):
    return client.product.delete(resource_group_name=resource_group, service_name=service_name, product_id=product_id)

# module equivalent: azure_rm_apimanagementproduct
def list_apimgmt_product(cmd, client,
                         resource_group,
                         service_name):
    if resource_group is not None and service_name is not None:
        return client.product.list_by_tags(resource_group_name=resource_group, service_name=service_name)
    else:
        return client.product.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementproduct
def show_apimgmt_product(cmd, client,
                         resource_group,
                         service_name,
                         product_id):
    return client.product.get(resource_group_name=resource_group, service_name=service_name, product_id=product_id)

# module equivalent: azure_rm_apimanagementproductapi
def create_apimgmt_product_api(cmd, client,
                               resource_group,
                               service_name,
                               product_id,
                               api_id,
                               path,
                               description=None,
                               authentication_settings=None,
                               subscription_key_parameter_names=None,
                               type=None,
                               api_revision=None,
                               api_version=None,
                               is_current=None,
                               is_online=None,
                               api_revision_description=None,
                               api_version_description=None,
                               api_version_set_id=None,
                               subscription_required=None,
                               source_api_id=None,
                               display_name=None,
                               service_url=None,
                               protocols=None,
                               api_version_set=None):
    body={}
    body['description'] = description # str
    body['authentication_settings'] = json.loads(authentication_settings) if isinstance(authentication_settings, str) else authentication_settings
    body['subscription_key_parameter_names'] = json.loads(subscription_key_parameter_names) if isinstance(subscription_key_parameter_names, str) else subscription_key_parameter_names
    body['type'] = type # str
    body['api_revision'] = api_revision # str
    body['api_version'] = api_version # str
    body['is_current'] = is_current # boolean
    body['is_online'] = is_online # boolean
    body['api_revision_description'] = api_revision_description # str
    body['api_version_description'] = api_version_description # str
    body['api_version_set_id'] = api_version_set_id # str
    body['subscription_required'] = subscription_required # boolean
    body['source_api_id'] = source_api_id # str
    body['display_name'] = display_name # str
    body['service_url'] = service_url # str
    body['path'] = path # str
    body['protocols'] = json.loads(protocols) if isinstance(protocols, str) else protocols
    body['api_version_set'] = json.loads(api_version_set) if isinstance(api_version_set, str) else api_version_set
    return client.product_api.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, api_id=api_id)

# module equivalent: azure_rm_apimanagementproductapi
def update_apimgmt_product_api(cmd, client,
                               resource_group,
                               service_name,
                               product_id,
                               api_id,
                               path,
                               description=None,
                               authentication_settings=None,
                               subscription_key_parameter_names=None,
                               type=None,
                               api_revision=None,
                               api_version=None,
                               is_current=None,
                               is_online=None,
                               api_revision_description=None,
                               api_version_description=None,
                               api_version_set_id=None,
                               subscription_required=None,
                               source_api_id=None,
                               display_name=None,
                               service_url=None,
                               protocols=None,
                               api_version_set=None):
    body={}
    body['description'] = description # str
    body['authentication_settings'] = json.loads(authentication_settings) if isinstance(authentication_settings, str) else authentication_settings
    body['subscription_key_parameter_names'] = json.loads(subscription_key_parameter_names) if isinstance(subscription_key_parameter_names, str) else subscription_key_parameter_names
    body['type'] = type # str
    body['api_revision'] = api_revision # str
    body['api_version'] = api_version # str
    body['is_current'] = is_current # boolean
    body['is_online'] = is_online # boolean
    body['api_revision_description'] = api_revision_description # str
    body['api_version_description'] = api_version_description # str
    body['api_version_set_id'] = api_version_set_id # str
    body['subscription_required'] = subscription_required # boolean
    body['source_api_id'] = source_api_id # str
    body['display_name'] = display_name # str
    body['service_url'] = service_url # str
    body['path'] = path # str
    body['protocols'] = json.loads(protocols) if isinstance(protocols, str) else protocols
    body['api_version_set'] = json.loads(api_version_set) if isinstance(api_version_set, str) else api_version_set
    return client.product_api.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, api_id=api_id)

# module equivalent: azure_rm_apimanagementproductapi
def delete_apimgmt_product_api(cmd, client,
                               resource_group,
                               service_name,
                               product_id,
                               api_id):
    return client.product_api.delete(resource_group_name=resource_group, service_name=service_name, product_id=product_id, api_id=api_id)

# module equivalent: azure_rm_apimanagementproductapi
def list_apimgmt_product_api(cmd, client,
                             resource_group,
                             service_name,
                             product_id):
    return client.product_api.list_by_product(resource_group_name=resource_group, service_name=service_name, product_id=product_id)

# module equivalent: azure_rm_apimanagementproductgroup
def create_apimgmt_product_group(cmd, client,
                                 resource_group,
                                 service_name,
                                 product_id,
                                 group_id,
                                 display_name,
                                 description=None,
                                 built_in=None,
                                 type=None,
                                 external_id=None):
    body={}
    body['display_name'] = display_name # str
    body['description'] = description # str
    body['built_in'] = built_in # boolean
    body['type'] = type # str
    body['external_id'] = external_id # str
    return client.product_group.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, group_id=group_id)

# module equivalent: azure_rm_apimanagementproductgroup
def update_apimgmt_product_group(cmd, client,
                                 resource_group,
                                 service_name,
                                 product_id,
                                 group_id,
                                 display_name,
                                 description=None,
                                 built_in=None,
                                 type=None,
                                 external_id=None):
    body={}
    body['display_name'] = display_name # str
    body['description'] = description # str
    body['built_in'] = built_in # boolean
    body['type'] = type # str
    body['external_id'] = external_id # str
    return client.product_group.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, group_id=group_id)

# module equivalent: azure_rm_apimanagementproductgroup
def delete_apimgmt_product_group(cmd, client,
                                 resource_group,
                                 service_name,
                                 product_id,
                                 group_id):
    return client.product_group.delete(resource_group_name=resource_group, service_name=service_name, product_id=product_id, group_id=group_id)

# module equivalent: azure_rm_apimanagementproductgroup
def list_apimgmt_product_group(cmd, client,
                               resource_group,
                               service_name,
                               product_id):
    return client.product_group.list_by_product(resource_group_name=resource_group, service_name=service_name, product_id=product_id)

# module equivalent: azure_rm_apimanagementproductpolicy
def create_apimgmt_product_policy(cmd, client,
                                  resource_group,
                                  service_name,
                                  product_id,
                                  policy_id,
                                  value,
                                  format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.product_policy.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementproductpolicy
def update_apimgmt_product_policy(cmd, client,
                                  resource_group,
                                  service_name,
                                  product_id,
                                  policy_id,
                                  value,
                                  format=None):
    body={}
    body['value'] = value # str
    body['format'] = format # str
    return client.product_policy.create_or_update(resource_group_name=resource_group, service_name=service_name, product_id=product_id, policy_id=policy_id, parameters=body)

# module equivalent: azure_rm_apimanagementproductpolicy
def delete_apimgmt_product_policy(cmd, client,
                                  resource_group,
                                  service_name,
                                  product_id,
                                  policy_id):
    return client.product_policy.delete(resource_group_name=resource_group, service_name=service_name, product_id=product_id, policy_id=policy_id)

# module equivalent: azure_rm_apimanagementproductpolicy
def list_apimgmt_product_policy(cmd, client,
                                resource_group,
                                service_name,
                                product_id):
    return client.product_policy.list_by_product(resource_group_name=resource_group, service_name=service_name, product_id=product_id)

# module equivalent: azure_rm_apimanagementproductpolicy
def show_apimgmt_product_policy(cmd, client,
                                resource_group,
                                service_name,
                                product_id,
                                policy_id,
                                format=None):
    return client.product_policy.get(resource_group_name=resource_group, service_name=service_name, product_id=product_id, policy_id=policy_id, format=format)

# module equivalent: azure_rm_apimanagementproperty
def create_apimgmt_property(cmd, client,
                            resource_group,
                            service_name,
                            prop_id,
                            display_name,
                            value,
                            tags=None,
                            secret=None):
    body={}
    body['tags'] = json.loads(tags) if isinstance(tags, str) else tags
    body['secret'] = secret # boolean
    body['display_name'] = display_name # str
    body['value'] = value # str
    return client.property.create_or_update(resource_group_name=resource_group, service_name=service_name, prop_id=prop_id, parameters=body)

# module equivalent: azure_rm_apimanagementproperty
def update_apimgmt_property(cmd, client,
                            resource_group,
                            service_name,
                            prop_id,
                            display_name,
                            value,
                            tags=None,
                            secret=None):
    body={}
    body['tags'] = json.loads(tags) if isinstance(tags, str) else tags
    body['secret'] = secret # boolean
    body['display_name'] = display_name # str
    body['value'] = value # str
    return client.property.create_or_update(resource_group_name=resource_group, service_name=service_name, prop_id=prop_id, parameters=body)

# module equivalent: azure_rm_apimanagementproperty
def delete_apimgmt_property(cmd, client,
                            resource_group,
                            service_name,
                            prop_id):
    return client.property.delete(resource_group_name=resource_group, service_name=service_name, prop_id=prop_id)

# module equivalent: azure_rm_apimanagementproperty
def list_apimgmt_property(cmd, client,
                          resource_group,
                          service_name):
    return client.property.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementproperty
def show_apimgmt_property(cmd, client,
                          resource_group,
                          service_name,
                          prop_id):
    return client.property.get(resource_group_name=resource_group, service_name=service_name, prop_id=prop_id)

# module equivalent: azure_rm_apimanagementsubscription
def create_apimgmt_subscription(cmd, client,
                                resource_group,
                                service_name,
                                sid,
                                scope,
                                display_name,
                                notify=None,
                                owner_id=None,
                                primary_key=None,
                                secondary_key=None,
                                state=None,
                                allow_tracing=None):
    body={}
    body['owner_id'] = owner_id # str
    body['scope'] = scope # str
    body['display_name'] = display_name # str
    body['primary_key'] = primary_key # str
    body['secondary_key'] = secondary_key # str
    body['state'] = state # str
    body['allow_tracing'] = allow_tracing # boolean
    return client.subscription.create_or_update(resource_group_name=resource_group, service_name=service_name, sid=sid, parameters=body, notify=notify)

# module equivalent: azure_rm_apimanagementsubscription
def update_apimgmt_subscription(cmd, client,
                                resource_group,
                                service_name,
                                sid,
                                scope,
                                display_name,
                                notify=None,
                                owner_id=None,
                                primary_key=None,
                                secondary_key=None,
                                state=None,
                                allow_tracing=None):
    body={}
    body['owner_id'] = owner_id # str
    body['scope'] = scope # str
    body['display_name'] = display_name # str
    body['primary_key'] = primary_key # str
    body['secondary_key'] = secondary_key # str
    body['state'] = state # str
    body['allow_tracing'] = allow_tracing # boolean
    return client.subscription.create_or_update(resource_group_name=resource_group, service_name=service_name, sid=sid, parameters=body, notify=notify)

# module equivalent: azure_rm_apimanagementsubscription
def delete_apimgmt_subscription(cmd, client,
                                resource_group,
                                service_name,
                                sid):
    return client.subscription.delete(resource_group_name=resource_group, service_name=service_name, sid=sid)

# module equivalent: azure_rm_apimanagementsubscription
def list_apimgmt_subscription(cmd, client,
                              resource_group,
                              service_name):
    return client.subscription.list(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementsubscription
def show_apimgmt_subscription(cmd, client,
                              resource_group,
                              service_name,
                              sid):
    return client.subscription.get(resource_group_name=resource_group, service_name=service_name, sid=sid)

# module equivalent: azure_rm_apimanagementuser
def create_apimgmt_user(cmd, client,
                        resource_group,
                        service_name,
                        user_id,
                        email,
                        first_name,
                        last_name,
                        state=None,
                        note=None,
                        identities=None,
                        password=None,
                        confirmation=None):
    body={}
    body['state'] = state # str
    body['note'] = note # str
    body['identities'] = json.loads(identities) if isinstance(identities, str) else identities
    body['email'] = email # str
    body['first_name'] = first_name # str
    body['last_name'] = last_name # str
    body['password'] = password # str
    body['confirmation'] = confirmation # str
    return client.user.create_or_update(resource_group_name=resource_group, service_name=service_name, user_id=user_id, parameters=body)

# module equivalent: azure_rm_apimanagementuser
def update_apimgmt_user(cmd, client,
                        resource_group,
                        service_name,
                        user_id,
                        email,
                        first_name,
                        last_name,
                        state=None,
                        note=None,
                        identities=None,
                        password=None,
                        confirmation=None):
    body={}
    body['state'] = state # str
    body['note'] = note # str
    body['identities'] = json.loads(identities) if isinstance(identities, str) else identities
    body['email'] = email # str
    body['first_name'] = first_name # str
    body['last_name'] = last_name # str
    body['password'] = password # str
    body['confirmation'] = confirmation # str
    return client.user.create_or_update(resource_group_name=resource_group, service_name=service_name, user_id=user_id, parameters=body)

# module equivalent: azure_rm_apimanagementuser
def delete_apimgmt_user(cmd, client,
                        resource_group,
                        service_name,
                        user_id):
    return client.user.delete(resource_group_name=resource_group, service_name=service_name, user_id=user_id)

# module equivalent: azure_rm_apimanagementuser
def list_apimgmt_user(cmd, client,
                      resource_group,
                      service_name):
    return client.user.list_by_service(resource_group_name=resource_group, service_name=service_name)

# module equivalent: azure_rm_apimanagementuser
def show_apimgmt_user(cmd, client,
                      resource_group,
                      service_name,
                      user_id):
    return client.user.get(resource_group_name=resource_group, service_name=service_name, user_id=user_id)