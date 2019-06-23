# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_apimgmt_api(cmd, client,
                       resource_group,
                       name,
                       api_id,
                       properties=None,
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
                       path=None,
                       protocols=None,
                       api_version_set=None,
                       value=None,
                       format=None,
                       wsdl_selector=None,
                       api_type=None,
                       is_online=None,
                       id=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['authentication_settings'] = authentication_settings
    body['subscription_key_parameter_names'] = subscription_key_parameter_names
    body['type'] = type
    body['api_revision'] = api_revision
    body['api_version'] = api_version
    body['is_current'] = is_current
    body['api_revision_description'] = api_revision_description
    body['api_version_description'] = api_version_description
    body['api_version_set_id'] = api_version_set_id
    body['subscription_required'] = subscription_required
    body['source_api_id'] = source_api_id
    body['display_name'] = display_name
    body['service_url'] = service_url
    body['path'] = path
    body['protocols'] = protocols
    body['api_version_set'] = api_version_set
    body['value'] = value
    body['format'] = format
    body['wsdl_selector'] = wsdl_selector
    body['api_type'] = api_type
    body['is_online'] = is_online
    return client.api.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, parameters=body)


def update_apimgmt_api(cmd, client,
                       resource_group,
                       name,
                       api_id,
                       properties=None,
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
                       path=None,
                       protocols=None,
                       api_version_set=None,
                       value=None,
                       format=None,
                       wsdl_selector=None,
                       api_type=None,
                       is_online=None,
                       id=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['authentication_settings'] = authentication_settings
    body['subscription_key_parameter_names'] = subscription_key_parameter_names
    body['type'] = type
    body['api_revision'] = api_revision
    body['api_version'] = api_version
    body['is_current'] = is_current
    body['api_revision_description'] = api_revision_description
    body['api_version_description'] = api_version_description
    body['api_version_set_id'] = api_version_set_id
    body['subscription_required'] = subscription_required
    body['source_api_id'] = source_api_id
    body['display_name'] = display_name
    body['service_url'] = service_url
    body['path'] = path
    body['protocols'] = protocols
    body['api_version_set'] = api_version_set
    body['value'] = value
    body['format'] = format
    body['wsdl_selector'] = wsdl_selector
    body['api_type'] = api_type
    body['is_online'] = is_online
    return client.api.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, parameters=body)


def delete_apimgmt_api(cmd, client,
                       resource_group,
                       name,
                       api_id):
    return client.api.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, If-Match=If-Match)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id)


def show_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.get(resource_group_name=resource_group, service_name=name, api_id=api_id)


def show_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.get(resource_group_name=resource_group, service_name=name, api_id=api_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.list_by_tags(resource_group_name=resource_group, service_name=name, api_id=api_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api_revision.list_by_service()


def create_apimgmt_api_release(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               release_id,
                               properties=None,
                               notes=None,
                               created_date_time=None,
                               updated_date_time=None,
                               id=None,
                               type=None):
    body={}
    body['properties'] = properties
    body['notes'] = notes
    body['created_date_time'] = created_date_time
    body['updated_date_time'] = updated_date_time
    return client.api_release.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id, parameters=body)


def update_apimgmt_api_release(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               release_id,
                               properties=None,
                               notes=None,
                               created_date_time=None,
                               updated_date_time=None,
                               id=None,
                               type=None):
    body={}
    body['properties'] = properties
    body['notes'] = notes
    body['created_date_time'] = created_date_time
    body['updated_date_time'] = updated_date_time
    return client.api_release.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id, parameters=body)


def delete_apimgmt_api_release(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               release_id):
    return client.api_release.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id, If-Match=If-Match)


def list_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id)


def show_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.get(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id)


def show_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.get(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id)


def list_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, release_id=release_id)


def create_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 name,
                                 api_id,
                                 operation_id,
                                 properties=None,
                                 template_parameters=None,
                                 description=None,
                                 request=None,
                                 responses=None,
                                 policies=None,
                                 display_name=None,
                                 method=None,
                                 url_template=None,
                                 id=None,
                                 type=None):
    body={}
    body['properties'] = properties
    body['template_parameters'] = template_parameters
    body['description'] = description
    body['request'] = request
    body['responses'] = responses
    body['policies'] = policies
    body['display_name'] = display_name
    body['method'] = method
    body['url_template'] = url_template
    return client.api_operation.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, parameters=body)


def update_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 name,
                                 api_id,
                                 operation_id,
                                 properties=None,
                                 template_parameters=None,
                                 description=None,
                                 request=None,
                                 responses=None,
                                 policies=None,
                                 display_name=None,
                                 method=None,
                                 url_template=None,
                                 id=None,
                                 type=None):
    body={}
    body['properties'] = properties
    body['template_parameters'] = template_parameters
    body['description'] = description
    body['request'] = request
    body['responses'] = responses
    body['policies'] = policies
    body['display_name'] = display_name
    body['method'] = method
    body['url_template'] = url_template
    return client.api_operation.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, parameters=body)


def delete_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 name,
                                 api_id,
                                 operation_id):
    return client.api_operation.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, If-Match=If-Match)


def list_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.list_by_api(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id)


def show_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.get(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id)


def show_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.get(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id)


def list_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.list_by_api(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id)


def create_apimgmt_api_operation_policy(cmd, client,
                                        resource_group,
                                        name,
                                        api_id,
                                        operation_id,
                                        policy_id,
                                        properties=None,
                                        value=None,
                                        format=None,
                                        id=None,
                                        type=None):
    body={}
    body['properties'] = properties
    body['value'] = value
    body['format'] = format
    return client.api_operation_policy.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, policy_id=policy_id, parameters=body)


def delete_apimgmt_api_operation_policy(cmd, client,
                                        resource_group,
                                        name,
                                        api_id,
                                        operation_id,
                                        policy_id):
    return client.api_operation_policy.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, policy_id=policy_id, If-Match=If-Match)


def list_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.list_by_operation(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, policy_id=policy_id)


def show_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.get(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, policy_id=policy_id)


def show_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.get(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, policy_id=policy_id)


def list_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.list_by_operation(resource_group_name=resource_group, service_name=name, api_id=api_id, operation_id=operation_id, policy_id=policy_id)


def create_apimgmt_tag(cmd, client,
                       resource_group,
                       name,
                       tag_id,
                       properties=None,
                       display_name=None,
                       id=None,
                       type=None):
    body={}
    body['properties'] = properties
    body['display_name'] = display_name
    return client.tag.create_or_update(resource_group_name=resource_group, service_name=name, tag_id=tag_id, parameters=body)


def update_apimgmt_tag(cmd, client,
                       resource_group,
                       name,
                       tag_id,
                       properties=None,
                       display_name=None,
                       id=None,
                       type=None):
    body={}
    body['properties'] = properties
    body['display_name'] = display_name
    return client.tag.create_or_update(resource_group_name=resource_group, service_name=name, tag_id=tag_id, parameters=body)


def delete_apimgmt_tag(cmd, client,
                       resource_group,
                       name,
                       tag_id):
    return client.tag.delete(resource_group_name=resource_group, service_name=name, tag_id=tag_id, If-Match=If-Match)


def list_apimgmt_tag(cmd, client,
                     resource_group,
                     name,
                     tag_id):
    return client.tag.list_by_service(resource_group_name=resource_group, service_name=name, tag_id=tag_id)


def show_apimgmt_tag(cmd, client,
                     resource_group,
                     name,
                     tag_id):
    return client.tag.get(resource_group_name=resource_group, service_name=name, tag_id=tag_id)


def list_apimgmt_tag_api_product_operation(cmd, client,
                                           resource_group,
                                           name,
                                           tag_id,
                                           api_id,
                                           product_id,
                                           operation_id):
    return client.tag.list_by_operation(resource_group_name=resource_group, service_name=name, tag_id=tag_id)


def show_apimgmt_tag_api_product_operation(cmd, client,
                                           resource_group,
                                           name,
                                           tag_id,
                                           api_id,
                                           product_id,
                                           operation_id):
    return client.tag.get(resource_group_name=resource_group, service_name=name, tag_id=tag_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api_product.list_by_apis()


def create_apimgmt_api_policy(cmd, client,
                              resource_group,
                              name,
                              api_id,
                              policy_id,
                              properties=None,
                              value=None,
                              format=None,
                              id=None,
                              type=None):
    body={}
    body['properties'] = properties
    body['value'] = value
    body['format'] = format
    return client.api_policy.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, policy_id=policy_id, parameters=body)


def delete_apimgmt_api_policy(cmd, client,
                              resource_group,
                              name,
                              api_id,
                              policy_id):
    return client.api_policy.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, policy_id=policy_id, If-Match=If-Match)


def list_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.list_by_api(resource_group_name=resource_group, service_name=name, api_id=api_id, policy_id=policy_id)


def show_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.get(resource_group_name=resource_group, service_name=name, api_id=api_id, policy_id=policy_id)


def show_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.get(resource_group_name=resource_group, service_name=name, api_id=api_id, policy_id=policy_id)


def list_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.list_by_api(resource_group_name=resource_group, service_name=name, api_id=api_id, policy_id=policy_id)


def create_apimgmt_api_schema(cmd, client,
                              resource_group,
                              name,
                              api_id,
                              schema_id,
                              properties=None,
                              content_type=None,
                              document=None,
                              id=None,
                              type=None):
    body={}
    body['properties'] = properties
    body['content_type'] = content_type
    body['document'] = document
    return client.api_schema.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, schema_id=schema_id, parameters=body)


def delete_apimgmt_api_schema(cmd, client,
                              resource_group,
                              name,
                              api_id,
                              schema_id):
    return client.api_schema.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, schema_id=schema_id, If-Match=If-Match)


def list_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.list_by_api(resource_group_name=resource_group, service_name=name, api_id=api_id, schema_id=schema_id)


def show_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.get(resource_group_name=resource_group, service_name=name, api_id=api_id, schema_id=schema_id)


def show_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.get(resource_group_name=resource_group, service_name=name, api_id=api_id, schema_id=schema_id)


def list_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.list_by_api(resource_group_name=resource_group, service_name=name, api_id=api_id, schema_id=schema_id)


def create_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  name,
                                  api_id,
                                  diagnostic_id,
                                  properties=None,
                                  always_log=None,
                                  logger_id=None,
                                  sampling=None,
                                  frontend=None,
                                  backend=None,
                                  enable_http_correlation_headers=None,
                                  id=None,
                                  type=None):
    body={}
    body['properties'] = properties
    body['always_log'] = always_log
    body['logger_id'] = logger_id
    body['sampling'] = sampling
    body['frontend'] = frontend
    body['backend'] = backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers
    return client.api_diagnostic.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id, parameters=body)


def update_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  name,
                                  api_id,
                                  diagnostic_id,
                                  properties=None,
                                  always_log=None,
                                  logger_id=None,
                                  sampling=None,
                                  frontend=None,
                                  backend=None,
                                  enable_http_correlation_headers=None,
                                  id=None,
                                  type=None):
    body={}
    body['properties'] = properties
    body['always_log'] = always_log
    body['logger_id'] = logger_id
    body['sampling'] = sampling
    body['frontend'] = frontend
    body['backend'] = backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers
    return client.api_diagnostic.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id, parameters=body)


def delete_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  name,
                                  api_id,
                                  diagnostic_id):
    return client.api_diagnostic.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id, If-Match=If-Match)


def list_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id)


def show_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.get(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id)


def show_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.get(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id)


def list_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, diagnostic_id=diagnostic_id)


def create_apimgmt_api_issue(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             issue_id,
                             properties=None,
                             created_date=None,
                             state=None,
                             title=None,
                             description=None,
                             user_id=None,
                             id=None,
                             type=None):
    body={}
    body['properties'] = properties
    body['created_date'] = created_date
    body['state'] = state
    body['title'] = title
    body['description'] = description
    body['user_id'] = user_id
    return client.api_issue.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, parameters=body)


def update_apimgmt_api_issue(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             issue_id,
                             properties=None,
                             created_date=None,
                             state=None,
                             title=None,
                             description=None,
                             user_id=None,
                             id=None,
                             type=None):
    body={}
    body['properties'] = properties
    body['created_date'] = created_date
    body['state'] = state
    body['title'] = title
    body['description'] = description
    body['user_id'] = user_id
    return client.api_issue.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, parameters=body)


def delete_apimgmt_api_issue(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             issue_id):
    return client.api_issue.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, If-Match=If-Match)


def list_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id)


def show_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.get(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id)


def show_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.get(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id)


def list_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id)


def create_apimgmt_api_issue_comment(cmd, client,
                                     resource_group,
                                     name,
                                     api_id,
                                     issue_id,
                                     comment_id,
                                     properties=None,
                                     text=None,
                                     created_date=None,
                                     user_id=None,
                                     id=None,
                                     type=None):
    body={}
    body['properties'] = properties
    body['text'] = text
    body['created_date'] = created_date
    body['user_id'] = user_id
    return client.api_issue_comment.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, comment_id=comment_id, parameters=body)


def delete_apimgmt_api_issue_comment(cmd, client,
                                     resource_group,
                                     name,
                                     api_id,
                                     issue_id,
                                     comment_id):
    return client.api_issue_comment.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, comment_id=comment_id, If-Match=If-Match)


def list_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, comment_id=comment_id)


def show_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.get(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, comment_id=comment_id)


def show_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.get(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, comment_id=comment_id)


def list_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, comment_id=comment_id)


def create_apimgmt_api_issue_attachment(cmd, client,
                                        resource_group,
                                        name,
                                        api_id,
                                        issue_id,
                                        attachment_id,
                                        properties=None,
                                        title=None,
                                        content_format=None,
                                        content=None,
                                        id=None,
                                        type=None):
    body={}
    body['properties'] = properties
    body['title'] = title
    body['content_format'] = content_format
    body['content'] = content
    return client.api_issue_attachment.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id, parameters=body)


def delete_apimgmt_api_issue_attachment(cmd, client,
                                        resource_group,
                                        name,
                                        api_id,
                                        issue_id,
                                        attachment_id):
    return client.api_issue_attachment.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id, If-Match=If-Match)


def list_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id)


def show_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.get(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id)


def show_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.get(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id)


def list_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, issue_id=issue_id, attachment_id=attachment_id)


def create_apimgmt_api_tagdescription(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      tag_id,
                                      properties=None,
                                      description=None,
                                      external_docs_url=None,
                                      external_docs_description=None,
                                      display_name=None,
                                      id=None,
                                      type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['external_docs_url'] = external_docs_url
    body['external_docs_description'] = external_docs_description
    body['display_name'] = display_name
    return client.api_tag_description.create_or_update(resource_group_name=resource_group, service_name=name, api_id=api_id, tag_id=tag_id, parameters=body)


def delete_apimgmt_api_tagdescription(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      tag_id):
    return client.api_tag_description.delete(resource_group_name=resource_group, service_name=name, api_id=api_id, tag_id=tag_id, If-Match=If-Match)


def list_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, tag_id=tag_id)


def show_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.get(resource_group_name=resource_group, service_name=name, api_id=api_id, tag_id=tag_id)


def show_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.get(resource_group_name=resource_group, service_name=name, api_id=api_id, tag_id=tag_id)


def list_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.list_by_service(resource_group_name=resource_group, service_name=name, api_id=api_id, tag_id=tag_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.operation.list_by_tags()


def create_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 name,
                                 version_set_id,
                                 properties=None,
                                 description=None,
                                 version_query_name=None,
                                 version_header_name=None,
                                 display_name=None,
                                 versioning_scheme=None,
                                 id=None,
                                 type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['version_query_name'] = version_query_name
    body['version_header_name'] = version_header_name
    body['display_name'] = display_name
    body['versioning_scheme'] = versioning_scheme
    return client.api_version_set.create_or_update(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id, parameters=body)


def update_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 name,
                                 version_set_id,
                                 properties=None,
                                 description=None,
                                 version_query_name=None,
                                 version_header_name=None,
                                 display_name=None,
                                 versioning_scheme=None,
                                 id=None,
                                 type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['version_query_name'] = version_query_name
    body['version_header_name'] = version_header_name
    body['display_name'] = display_name
    body['versioning_scheme'] = versioning_scheme
    return client.api_version_set.create_or_update(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id, parameters=body)


def delete_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 name,
                                 version_set_id):
    return client.api_version_set.delete(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id, If-Match=If-Match)


def list_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.list_by_service(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id)


def show_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.get(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id)


def show_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.get(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id)


def list_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.list_by_service(resource_group_name=resource_group, service_name=name, version_set_id=version_set_id)


def create_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       name,
                                       authsid,
                                       properties=None,
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
                                       resource_owner_password=None,
                                       display_name=None,
                                       client_registration_endpoint=None,
                                       authorization_endpoint=None,
                                       grant_types=None,
                                       client_id=None,
                                       id=None,
                                       type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['authorization_methods'] = authorization_methods
    body['client_authentication_method'] = client_authentication_method
    body['token_body_parameters'] = token_body_parameters
    body['token_endpoint'] = token_endpoint
    body['support_state'] = support_state
    body['default_scope'] = default_scope
    body['bearer_token_sending_methods'] = bearer_token_sending_methods
    body['client_secret'] = client_secret
    body['resource_owner_username'] = resource_owner_username
    body['resource_owner_password'] = resource_owner_password
    body['display_name'] = display_name
    body['client_registration_endpoint'] = client_registration_endpoint
    body['authorization_endpoint'] = authorization_endpoint
    body['grant_types'] = grant_types
    body['client_id'] = client_id
    return client.authorization_server.create_or_update(resource_group_name=resource_group, service_name=name, authsid=authsid, parameters=body)


def update_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       name,
                                       authsid,
                                       properties=None,
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
                                       resource_owner_password=None,
                                       display_name=None,
                                       client_registration_endpoint=None,
                                       authorization_endpoint=None,
                                       grant_types=None,
                                       client_id=None,
                                       id=None,
                                       type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['authorization_methods'] = authorization_methods
    body['client_authentication_method'] = client_authentication_method
    body['token_body_parameters'] = token_body_parameters
    body['token_endpoint'] = token_endpoint
    body['support_state'] = support_state
    body['default_scope'] = default_scope
    body['bearer_token_sending_methods'] = bearer_token_sending_methods
    body['client_secret'] = client_secret
    body['resource_owner_username'] = resource_owner_username
    body['resource_owner_password'] = resource_owner_password
    body['display_name'] = display_name
    body['client_registration_endpoint'] = client_registration_endpoint
    body['authorization_endpoint'] = authorization_endpoint
    body['grant_types'] = grant_types
    body['client_id'] = client_id
    return client.authorization_server.create_or_update(resource_group_name=resource_group, service_name=name, authsid=authsid, parameters=body)


def delete_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       name,
                                       authsid):
    return client.authorization_server.delete(resource_group_name=resource_group, service_name=name, authsid=authsid, If-Match=If-Match)


def list_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.list_by_service(resource_group_name=resource_group, service_name=name, authsid=authsid)


def show_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.get(resource_group_name=resource_group, service_name=name, authsid=authsid)


def show_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.get(resource_group_name=resource_group, service_name=name, authsid=authsid)


def list_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.list_by_service(resource_group_name=resource_group, service_name=name, authsid=authsid)


def create_apimgmt_backend(cmd, client,
                           resource_group,
                           name,
                           backend_id,
                           properties=None,
                           title=None,
                           description=None,
                           resource_id=None,
                           service_fabric_cluster=None,
                           credentials=None,
                           proxy=None,
                           tls=None,
                           url=None,
                           protocol=None,
                           id=None,
                           type=None):
    body={}
    body['properties'] = properties
    body['title'] = title
    body['description'] = description
    body['resource_id'] = resource_id
    body['service_fabric_cluster'] = service_fabric_cluster
    body['credentials'] = credentials
    body['proxy'] = proxy
    body['tls'] = tls
    body['url'] = url
    body['protocol'] = protocol
    return client.backend.create_or_update(resource_group_name=resource_group, service_name=name, backend_id=backend_id, parameters=body)


def update_apimgmt_backend(cmd, client,
                           resource_group,
                           name,
                           backend_id,
                           properties=None,
                           title=None,
                           description=None,
                           resource_id=None,
                           service_fabric_cluster=None,
                           credentials=None,
                           proxy=None,
                           tls=None,
                           url=None,
                           protocol=None,
                           id=None,
                           type=None):
    body={}
    body['properties'] = properties
    body['title'] = title
    body['description'] = description
    body['resource_id'] = resource_id
    body['service_fabric_cluster'] = service_fabric_cluster
    body['credentials'] = credentials
    body['proxy'] = proxy
    body['tls'] = tls
    body['url'] = url
    body['protocol'] = protocol
    return client.backend.create_or_update(resource_group_name=resource_group, service_name=name, backend_id=backend_id, parameters=body)


def delete_apimgmt_backend(cmd, client,
                           resource_group,
                           name,
                           backend_id):
    return client.backend.delete(resource_group_name=resource_group, service_name=name, backend_id=backend_id, If-Match=If-Match)


def list_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.list_by_service(resource_group_name=resource_group, service_name=name, backend_id=backend_id)


def show_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.get(resource_group_name=resource_group, service_name=name, backend_id=backend_id)


def show_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.get(resource_group_name=resource_group, service_name=name, backend_id=backend_id)


def list_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.list_by_service(resource_group_name=resource_group, service_name=name, backend_id=backend_id)


def create_apimgmt_cache(cmd, client,
                         resource_group,
                         name,
                         cache_id,
                         properties=None,
                         description=None,
                         connection_string=None,
                         resource_id=None,
                         id=None,
                         type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['connection_string'] = connection_string
    body['resource_id'] = resource_id
    return client.cache.create_or_update(resource_group_name=resource_group, service_name=name, cache_id=cache_id, parameters=body)


def update_apimgmt_cache(cmd, client,
                         resource_group,
                         name,
                         cache_id,
                         properties=None,
                         description=None,
                         connection_string=None,
                         resource_id=None,
                         id=None,
                         type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['connection_string'] = connection_string
    body['resource_id'] = resource_id
    return client.cache.create_or_update(resource_group_name=resource_group, service_name=name, cache_id=cache_id, parameters=body)


def delete_apimgmt_cache(cmd, client,
                         resource_group,
                         name,
                         cache_id):
    return client.cache.delete(resource_group_name=resource_group, service_name=name, cache_id=cache_id, If-Match=If-Match)


def list_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.list_by_service(resource_group_name=resource_group, service_name=name, cache_id=cache_id)


def show_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.get(resource_group_name=resource_group, service_name=name, cache_id=cache_id)


def show_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.get(resource_group_name=resource_group, service_name=name, cache_id=cache_id)


def list_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.list_by_service(resource_group_name=resource_group, service_name=name, cache_id=cache_id)


def create_apimgmt_certificate(cmd, client,
                               resource_group,
                               name,
                               certificate_id,
                               properties=None,
                               data=None,
                               password=None,
                               subject=None,
                               thumbprint=None,
                               expiration_date=None,
                               id=None,
                               type=None):
    body={}
    body['properties'] = properties
    body['data'] = data
    body['password'] = password
    body['subject'] = subject
    body['thumbprint'] = thumbprint
    body['expiration_date'] = expiration_date
    return client.certificate.create_or_update(resource_group_name=resource_group, service_name=name, certificate_id=certificate_id, parameters=body)


def delete_apimgmt_certificate(cmd, client,
                               resource_group,
                               name,
                               certificate_id):
    return client.certificate.delete(resource_group_name=resource_group, service_name=name, certificate_id=certificate_id, If-Match=If-Match)


def list_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.list_by_service(resource_group_name=resource_group, service_name=name, certificate_id=certificate_id)


def show_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.get(resource_group_name=resource_group, service_name=name, certificate_id=certificate_id)


def show_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.get(resource_group_name=resource_group, service_name=name, certificate_id=certificate_id)


def list_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.list_by_service(resource_group_name=resource_group, service_name=name, certificate_id=certificate_id)


def list_(cmd, client):
    return client.api_management_operations.list()


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service_skus.list_available_service_skus()


def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   tags=None,
                   properties=None,
                   notification_sender_email=None,
                   hostname_configurations=None,
                   virtual_network_configuration=None,
                   additional_locations=None,
                   custom_properties=None,
                   certificates=None,
                   enable_client_certificate=None,
                   virtual_network_type=None,
                   publisher_email=None,
                   publisher_name=None,
                   provisioning_state=None,
                   target_provisioning_state=None,
                   created_at_utc=None,
                   gateway_url=None,
                   gateway_regional_url=None,
                   portal_url=None,
                   management_api_url=None,
                   scm_url=None,
                   public_ip_addresses=None,
                   private_ip_addresses=None,
                   sku=None,
                   identity=None,
                   location=None,
                   id=None,
                   type=None,
                   etag=None):
    body={}
    body['tags'] = tags
    body['properties'] = properties
    body['notification_sender_email'] = notification_sender_email
    body['hostname_configurations'] = hostname_configurations
    body['virtual_network_configuration'] = virtual_network_configuration
    body['additional_locations'] = additional_locations
    body['custom_properties'] = custom_properties
    body['certificates'] = certificates
    body['enable_client_certificate'] = enable_client_certificate
    body['virtual_network_type'] = virtual_network_type
    body['publisher_email'] = publisher_email
    body['publisher_name'] = publisher_name
    body['provisioning_state'] = provisioning_state
    body['target_provisioning_state'] = target_provisioning_state
    body['created_at_utc'] = created_at_utc
    body['gateway_url'] = gateway_url
    body['gateway_regional_url'] = gateway_regional_url
    body['portal_url'] = portal_url
    body['management_api_url'] = management_api_url
    body['scm_url'] = scm_url
    body['public_ip_addresses'] = public_ip_addresses
    body['private_ip_addresses'] = private_ip_addresses
    body['sku'] = sku
    body['identity'] = identity
    body['location'] = location
    return client.api_management_service.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   tags=None,
                   properties=None,
                   notification_sender_email=None,
                   hostname_configurations=None,
                   virtual_network_configuration=None,
                   additional_locations=None,
                   custom_properties=None,
                   certificates=None,
                   enable_client_certificate=None,
                   virtual_network_type=None,
                   publisher_email=None,
                   publisher_name=None,
                   provisioning_state=None,
                   target_provisioning_state=None,
                   created_at_utc=None,
                   gateway_url=None,
                   gateway_regional_url=None,
                   portal_url=None,
                   management_api_url=None,
                   scm_url=None,
                   public_ip_addresses=None,
                   private_ip_addresses=None,
                   sku=None,
                   identity=None,
                   location=None,
                   id=None,
                   type=None,
                   etag=None):
    body={}
    body['tags'] = tags
    body['properties'] = properties
    body['notification_sender_email'] = notification_sender_email
    body['hostname_configurations'] = hostname_configurations
    body['virtual_network_configuration'] = virtual_network_configuration
    body['additional_locations'] = additional_locations
    body['custom_properties'] = custom_properties
    body['certificates'] = certificates
    body['enable_client_certificate'] = enable_client_certificate
    body['virtual_network_type'] = virtual_network_type
    body['publisher_email'] = publisher_email
    body['publisher_name'] = publisher_name
    body['provisioning_state'] = provisioning_state
    body['target_provisioning_state'] = target_provisioning_state
    body['created_at_utc'] = created_at_utc
    body['gateway_url'] = gateway_url
    body['gateway_regional_url'] = gateway_regional_url
    body['portal_url'] = portal_url
    body['management_api_url'] = management_api_url
    body['scm_url'] = scm_url
    body['public_ip_addresses'] = public_ip_addresses
    body['private_ip_addresses'] = private_ip_addresses
    body['sku'] = sku
    body['identity'] = identity
    body['location'] = location
    return client.api_management_service.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def delete_apimgmt(cmd, client,
                   resource_group,
                   name):
    return client.api_management_service.delete(resource_group_name=resource_group, service_name=name)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.list(resource_group_name=resource_group, service_name=name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.get(resource_group_name=resource_group, service_name=name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.get(resource_group_name=resource_group, service_name=name)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.list_by_resource_group(resource_group_name=resource_group, service_name=name)


def create_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              name,
                              diagnostic_id,
                              properties=None,
                              always_log=None,
                              logger_id=None,
                              sampling=None,
                              frontend=None,
                              backend=None,
                              enable_http_correlation_headers=None,
                              id=None,
                              type=None):
    body={}
    body['properties'] = properties
    body['always_log'] = always_log
    body['logger_id'] = logger_id
    body['sampling'] = sampling
    body['frontend'] = frontend
    body['backend'] = backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers
    return client.diagnostic.create_or_update(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id, parameters=body)


def update_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              name,
                              diagnostic_id,
                              properties=None,
                              always_log=None,
                              logger_id=None,
                              sampling=None,
                              frontend=None,
                              backend=None,
                              enable_http_correlation_headers=None,
                              id=None,
                              type=None):
    body={}
    body['properties'] = properties
    body['always_log'] = always_log
    body['logger_id'] = logger_id
    body['sampling'] = sampling
    body['frontend'] = frontend
    body['backend'] = backend
    body['enable_http_correlation_headers'] = enable_http_correlation_headers
    return client.diagnostic.create_or_update(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id, parameters=body)


def delete_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              name,
                              diagnostic_id):
    return client.diagnostic.delete(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id, If-Match=If-Match)


def list_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.list_by_service(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id)


def show_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.get(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id)


def show_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.get(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id)


def list_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.list_by_service(resource_group_name=resource_group, service_name=name, diagnostic_id=diagnostic_id)


def create_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name,
                            properties=None,
                            subject=None,
                            title=None,
                            description=None,
                            body=None,
                            parameters=None,
                            is_default=None,
                            id=None,
                            type=None):
    body={}
    body['properties'] = properties
    body['subject'] = subject
    body['title'] = title
    body['description'] = description
    body['body'] = body
    body['parameters'] = parameters
    body['is_default'] = is_default
    return client.email_template.create_or_update(resource_group_name=resource_group, service_name=service_name, template_name=name, parameters=body)


def update_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name,
                            properties=None,
                            subject=None,
                            title=None,
                            description=None,
                            body=None,
                            parameters=None,
                            is_default=None,
                            id=None,
                            type=None):
    body={}
    body['properties'] = properties
    body['subject'] = subject
    body['title'] = title
    body['description'] = description
    body['body'] = body
    body['parameters'] = parameters
    body['is_default'] = is_default
    return client.email_template.create_or_update(resource_group_name=resource_group, service_name=service_name, template_name=name, parameters=body)


def delete_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name):
    return client.email_template.delete(resource_group_name=resource_group, service_name=service_name, template_name=name, If-Match=If-Match)


def list_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.list_by_service(resource_group_name=resource_group, service_name=service_name, template_name=name)


def show_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.get(resource_group_name=resource_group, service_name=service_name, template_name=name)


def show_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.get(resource_group_name=resource_group, service_name=service_name, template_name=name)


def list_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.list_by_service(resource_group_name=resource_group, service_name=service_name, template_name=name)


def create_apimgmt_group(cmd, client,
                         resource_group,
                         name,
                         group_id,
                         properties=None,
                         display_name=None,
                         description=None,
                         type=None,
                         external_id=None,
                         built_in=None,
                         id=None):
    body={}
    body['properties'] = properties
    body['display_name'] = display_name
    body['description'] = description
    body['type'] = type
    body['external_id'] = external_id
    body['built_in'] = built_in
    return client.group.create_or_update(resource_group_name=resource_group, service_name=name, group_id=group_id, parameters=body)


def update_apimgmt_group(cmd, client,
                         resource_group,
                         name,
                         group_id,
                         properties=None,
                         display_name=None,
                         description=None,
                         type=None,
                         external_id=None,
                         built_in=None,
                         id=None):
    body={}
    body['properties'] = properties
    body['display_name'] = display_name
    body['description'] = description
    body['type'] = type
    body['external_id'] = external_id
    body['built_in'] = built_in
    return client.group.create_or_update(resource_group_name=resource_group, service_name=name, group_id=group_id, parameters=body)


def delete_apimgmt_group(cmd, client,
                         resource_group,
                         name,
                         group_id):
    return client.group.delete(resource_group_name=resource_group, service_name=name, group_id=group_id, If-Match=If-Match)


def list_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.list_by_service(resource_group_name=resource_group, service_name=name, group_id=group_id)


def show_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.get(resource_group_name=resource_group, service_name=name, group_id=group_id)


def show_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.get(resource_group_name=resource_group, service_name=name, group_id=group_id)


def list_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.list_by_service(resource_group_name=resource_group, service_name=name, group_id=group_id)


def create_apimgmt_group_user(cmd, client,
                              resource_group,
                              name,
                              group_id,
                              user_id,
                              id=None,
                              type=None,
                              properties=None,
                              state=None,
                              note=None,
                              identities=None,
                              first_name=None,
                              last_name=None,
                              email=None,
                              registration_date=None,
                              groups=None):
    body={}
    body['state'] = state
    body['note'] = note
    body['identities'] = identities
    body['first_name'] = first_name
    body['last_name'] = last_name
    body['email'] = email
    body['registration_date'] = registration_date
    body['groups'] = groups
    return client.group_user.create(resource_group_name=resource_group, service_name=name, group_id=group_id, user_id=user_id)


def delete_apimgmt_group_user(cmd, client,
                              resource_group,
                              name,
                              group_id,
                              user_id):
    return client.group_user.delete(resource_group_name=resource_group, service_name=name, group_id=group_id, user_id=user_id)


def list_apimgmt_group_user(cmd, client,
                            resource_group,
                            name,
                            group_id,
                            user_id):
    return client.group_user.list()


def list_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group_user.list()


def create_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name,
                                    properties=None,
                                    type=None,
                                    allowed_tenants=None,
                                    authority=None,
                                    signup_policy_name=None,
                                    signin_policy_name=None,
                                    profile_editing_policy_name=None,
                                    password_reset_policy_name=None,
                                    client_id=None,
                                    client_secret=None,
                                    id=None):
    body={}
    body['properties'] = properties
    body['type'] = type
    body['allowed_tenants'] = allowed_tenants
    body['authority'] = authority
    body['signup_policy_name'] = signup_policy_name
    body['signin_policy_name'] = signin_policy_name
    body['profile_editing_policy_name'] = profile_editing_policy_name
    body['password_reset_policy_name'] = password_reset_policy_name
    body['client_id'] = client_id
    body['client_secret'] = client_secret
    return client.identity_provider.create_or_update(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name, parameters=body)


def update_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name,
                                    properties=None,
                                    type=None,
                                    allowed_tenants=None,
                                    authority=None,
                                    signup_policy_name=None,
                                    signin_policy_name=None,
                                    profile_editing_policy_name=None,
                                    password_reset_policy_name=None,
                                    client_id=None,
                                    client_secret=None,
                                    id=None):
    body={}
    body['properties'] = properties
    body['type'] = type
    body['allowed_tenants'] = allowed_tenants
    body['authority'] = authority
    body['signup_policy_name'] = signup_policy_name
    body['signin_policy_name'] = signin_policy_name
    body['profile_editing_policy_name'] = profile_editing_policy_name
    body['password_reset_policy_name'] = password_reset_policy_name
    body['client_id'] = client_id
    body['client_secret'] = client_secret
    return client.identity_provider.create_or_update(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name, parameters=body)


def delete_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name):
    return client.identity_provider.delete(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name, If-Match=If-Match)


def list_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.list_by_service(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name)


def show_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.get(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name)


def show_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.get(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name)


def list_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.list_by_service(resource_group_name=resource_group, service_name=service_name, identity_provider_name=name)


def show_apimgmt_issue(cmd, client,
                       resource_group,
                       name,
                       issue_id):
    return client.issue.get(resource_group_name=resource_group, service_name=name, issue_id=issue_id)


def list_apimgmt_issue(cmd, client,
                       resource_group,
                       name,
                       issue_id):
    return client.issue.list_by_service(resource_group_name=resource_group, service_name=name, issue_id=issue_id)


def create_apimgmt_logger(cmd, client,
                          resource_group,
                          name,
                          logger_id,
                          properties=None,
                          logger_type=None,
                          description=None,
                          credentials=None,
                          is_buffered=None,
                          resource_id=None,
                          id=None,
                          type=None):
    body={}
    body['properties'] = properties
    body['logger_type'] = logger_type
    body['description'] = description
    body['credentials'] = credentials
    body['is_buffered'] = is_buffered
    body['resource_id'] = resource_id
    return client.logger.create_or_update(resource_group_name=resource_group, service_name=name, logger_id=logger_id, parameters=body)


def update_apimgmt_logger(cmd, client,
                          resource_group,
                          name,
                          logger_id,
                          properties=None,
                          logger_type=None,
                          description=None,
                          credentials=None,
                          is_buffered=None,
                          resource_id=None,
                          id=None,
                          type=None):
    body={}
    body['properties'] = properties
    body['logger_type'] = logger_type
    body['description'] = description
    body['credentials'] = credentials
    body['is_buffered'] = is_buffered
    body['resource_id'] = resource_id
    return client.logger.create_or_update(resource_group_name=resource_group, service_name=name, logger_id=logger_id, parameters=body)


def delete_apimgmt_logger(cmd, client,
                          resource_group,
                          name,
                          logger_id):
    return client.logger.delete(resource_group_name=resource_group, service_name=name, logger_id=logger_id, If-Match=If-Match)


def list_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.list_by_service(resource_group_name=resource_group, service_name=name, logger_id=logger_id)


def show_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.get(resource_group_name=resource_group, service_name=name, logger_id=logger_id)


def show_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.get(resource_group_name=resource_group, service_name=name, logger_id=logger_id)


def list_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.list_by_service(resource_group_name=resource_group, service_name=name, logger_id=logger_id)


def list_apimgmt_location(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.network_status.list_by_location()


def create_apimgmt_notification(cmd, client,
                                resource_group,
                                service_name,
                                name,
                                id=None,
                                type=None,
                                properties=None,
                                title=None,
                                description=None,
                                recipients=None):
    body={}
    body['title'] = title
    body['description'] = description
    body['recipients'] = recipients
    return client.notification.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=name)


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.list_by_service(resource_group_name=resource_group, service_name=service_name, notification_name=name)


def show_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.get(resource_group_name=resource_group, service_name=service_name, notification_name=name)


def show_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.get(resource_group_name=resource_group, service_name=service_name, notification_name=name)


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.list_by_service(resource_group_name=resource_group, service_name=service_name, notification_name=name)


def create_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              name,
                                              user_id,
                                              id=None,
                                              type=None,
                                              properties=None):
    body={}
    return client.notification_recipient_user.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=name, user_id=user_id)


def delete_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              name,
                                              user_id):
    return client.notification_recipient_user.delete(resource_group_name=resource_group, service_name=service_name, notification_name=name, user_id=user_id)


def list_apimgmt_notification_recipientuser(cmd, client,
                                            resource_group,
                                            service_name,
                                            name,
                                            user_id):
    return client.notification_recipient_user.list_by_notification()


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification_recipient_user.list_by_notification()


def create_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               name,
                                               email,
                                               id=None,
                                               type=None,
                                               properties=None):
    body={}
    return client.notification_recipient_email.create_or_update(resource_group_name=resource_group, service_name=service_name, notification_name=name, email=email)


def delete_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               name,
                                               email):
    return client.notification_recipient_email.delete(resource_group_name=resource_group, service_name=service_name, notification_name=name, email=email)


def list_apimgmt_notification_recipientemail(cmd, client,
                                             resource_group,
                                             service_name,
                                             name,
                                             email):
    return client.notification_recipient_email.list_by_notification()


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification_recipient_email.list_by_notification()


def create_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         name,
                                         opid,
                                         properties=None,
                                         display_name=None,
                                         description=None,
                                         metadata_endpoint=None,
                                         client_id=None,
                                         client_secret=None,
                                         id=None,
                                         type=None):
    body={}
    body['properties'] = properties
    body['display_name'] = display_name
    body['description'] = description
    body['metadata_endpoint'] = metadata_endpoint
    body['client_id'] = client_id
    body['client_secret'] = client_secret
    return client.open_id_connect_provider.create_or_update(resource_group_name=resource_group, service_name=name, opid=opid, parameters=body)


def update_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         name,
                                         opid,
                                         properties=None,
                                         display_name=None,
                                         description=None,
                                         metadata_endpoint=None,
                                         client_id=None,
                                         client_secret=None,
                                         id=None,
                                         type=None):
    body={}
    body['properties'] = properties
    body['display_name'] = display_name
    body['description'] = description
    body['metadata_endpoint'] = metadata_endpoint
    body['client_id'] = client_id
    body['client_secret'] = client_secret
    return client.open_id_connect_provider.create_or_update(resource_group_name=resource_group, service_name=name, opid=opid, parameters=body)


def delete_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         name,
                                         opid):
    return client.open_id_connect_provider.delete(resource_group_name=resource_group, service_name=name, opid=opid, If-Match=If-Match)


def list_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.list_by_service(resource_group_name=resource_group, service_name=name, opid=opid)


def show_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.get(resource_group_name=resource_group, service_name=name, opid=opid)


def show_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.get(resource_group_name=resource_group, service_name=name, opid=opid)


def list_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.list_by_service(resource_group_name=resource_group, service_name=name, opid=opid)


def create_apimgmt_policy(cmd, client,
                          resource_group,
                          name,
                          policy_id,
                          properties=None,
                          value=None,
                          format=None,
                          id=None,
                          type=None):
    body={}
    body['properties'] = properties
    body['value'] = value
    body['format'] = format
    return client.policy.create_or_update(resource_group_name=resource_group, service_name=name, policy_id=policy_id, parameters=body)


def delete_apimgmt_policy(cmd, client,
                          resource_group,
                          name,
                          policy_id):
    return client.policy.delete(resource_group_name=resource_group, service_name=name, policy_id=policy_id, If-Match=If-Match)


def list_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.list_by_service(resource_group_name=resource_group, service_name=name, policy_id=policy_id)


def show_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.get(resource_group_name=resource_group, service_name=name, policy_id=policy_id)


def show_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.get(resource_group_name=resource_group, service_name=name, policy_id=policy_id)


def list_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.list_by_service(resource_group_name=resource_group, service_name=name, policy_id=policy_id)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.policy_snippet.list_by_service()


def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   id=None,
                   type=None):
    body={}
    body['properties'] = properties
    body['enabled'] = enabled
    return client.sign_in_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   id=None,
                   type=None):
    body={}
    body['properties'] = properties
    body['enabled'] = enabled
    return client.sign_in_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_in_settings.get(resource_group_name=resource_group, service_name=name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_in_settings.get(resource_group_name=resource_group, service_name=name)


def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   terms_of_service=None,
                   id=None,
                   type=None):
    body={}
    body['properties'] = properties
    body['enabled'] = enabled
    body['terms_of_service'] = terms_of_service
    return client.sign_up_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   terms_of_service=None,
                   id=None,
                   type=None):
    body={}
    body['properties'] = properties
    body['enabled'] = enabled
    body['terms_of_service'] = terms_of_service
    return client.sign_up_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_up_settings.get(resource_group_name=resource_group, service_name=name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_up_settings.get(resource_group_name=resource_group, service_name=name)


def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   url=None,
                   validation_key=None,
                   subscriptions=None,
                   user_registration=None,
                   id=None,
                   type=None):
    body={}
    body['properties'] = properties
    body['url'] = url
    body['validation_key'] = validation_key
    body['subscriptions'] = subscriptions
    body['user_registration'] = user_registration
    return client.delegation_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   url=None,
                   validation_key=None,
                   subscriptions=None,
                   user_registration=None,
                   id=None,
                   type=None):
    body={}
    body['properties'] = properties
    body['url'] = url
    body['validation_key'] = validation_key
    body['subscriptions'] = subscriptions
    body['user_registration'] = user_registration
    return client.delegation_settings.create_or_update(resource_group_name=resource_group, service_name=name, parameters=body)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.delegation_settings.get(resource_group_name=resource_group, service_name=name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.delegation_settings.get(resource_group_name=resource_group, service_name=name)


def create_apimgmt_product(cmd, client,
                           resource_group,
                           name,
                           product_id,
                           properties=None,
                           description=None,
                           terms=None,
                           subscription_required=None,
                           approval_required=None,
                           subscriptions_limit=None,
                           state=None,
                           display_name=None,
                           id=None,
                           type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['terms'] = terms
    body['subscription_required'] = subscription_required
    body['approval_required'] = approval_required
    body['subscriptions_limit'] = subscriptions_limit
    body['state'] = state
    body['display_name'] = display_name
    return client.product.create_or_update(resource_group_name=resource_group, service_name=name, product_id=product_id, parameters=body)


def update_apimgmt_product(cmd, client,
                           resource_group,
                           name,
                           product_id,
                           properties=None,
                           description=None,
                           terms=None,
                           subscription_required=None,
                           approval_required=None,
                           subscriptions_limit=None,
                           state=None,
                           display_name=None,
                           id=None,
                           type=None):
    body={}
    body['properties'] = properties
    body['description'] = description
    body['terms'] = terms
    body['subscription_required'] = subscription_required
    body['approval_required'] = approval_required
    body['subscriptions_limit'] = subscriptions_limit
    body['state'] = state
    body['display_name'] = display_name
    return client.product.create_or_update(resource_group_name=resource_group, service_name=name, product_id=product_id, parameters=body)


def delete_apimgmt_product(cmd, client,
                           resource_group,
                           name,
                           product_id):
    return client.product.delete(resource_group_name=resource_group, service_name=name, product_id=product_id, If-Match=If-Match)


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.list_by_service(resource_group_name=resource_group, service_name=name, product_id=product_id)


def show_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.get(resource_group_name=resource_group, service_name=name, product_id=product_id)


def show_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.get(resource_group_name=resource_group, service_name=name, product_id=product_id)


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.list_by_tags(resource_group_name=resource_group, service_name=name, product_id=product_id)


def create_apimgmt_product_api(cmd, client,
                               resource_group,
                               name,
                               product_id,
                               api_id,
                               id=None,
                               type=None,
                               properties=None,
                               description=None,
                               authentication_settings=None,
                               subscription_key_parameter_names=None,
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
                               path=None,
                               protocols=None,
                               api_version_set=None):
    body={}
    body['description'] = description
    body['authentication_settings'] = authentication_settings
    body['subscription_key_parameter_names'] = subscription_key_parameter_names
    body['api_revision'] = api_revision
    body['api_version'] = api_version
    body['is_current'] = is_current
    body['is_online'] = is_online
    body['api_revision_description'] = api_revision_description
    body['api_version_description'] = api_version_description
    body['api_version_set_id'] = api_version_set_id
    body['subscription_required'] = subscription_required
    body['source_api_id'] = source_api_id
    body['display_name'] = display_name
    body['service_url'] = service_url
    body['path'] = path
    body['protocols'] = protocols
    body['api_version_set'] = api_version_set
    return client.product_api.create_or_update(resource_group_name=resource_group, service_name=name, product_id=product_id, api_id=api_id)


def delete_apimgmt_product_api(cmd, client,
                               resource_group,
                               name,
                               product_id,
                               api_id):
    return client.product_api.delete(resource_group_name=resource_group, service_name=name, product_id=product_id, api_id=api_id)


def list_apimgmt_product_api(cmd, client,
                             resource_group,
                             name,
                             product_id,
                             api_id):
    return client.product_api.list_by_product()


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product_api.list_by_product()


def create_apimgmt_product_group(cmd, client,
                                 resource_group,
                                 name,
                                 product_id,
                                 group_id,
                                 id=None,
                                 type=None,
                                 properties=None,
                                 display_name=None,
                                 description=None,
                                 built_in=None,
                                 external_id=None):
    body={}
    body['display_name'] = display_name
    body['description'] = description
    body['built_in'] = built_in
    body['external_id'] = external_id
    return client.product_group.create_or_update(resource_group_name=resource_group, service_name=name, product_id=product_id, group_id=group_id)


def delete_apimgmt_product_group(cmd, client,
                                 resource_group,
                                 name,
                                 product_id,
                                 group_id):
    return client.product_group.delete(resource_group_name=resource_group, service_name=name, product_id=product_id, group_id=group_id)


def list_apimgmt_product_group(cmd, client,
                               resource_group,
                               name,
                               product_id,
                               group_id):
    return client.product_group.list_by_product()


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product_group.list_by_product()


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product_subscriptions.list()


def create_apimgmt_product_policy(cmd, client,
                                  resource_group,
                                  name,
                                  product_id,
                                  policy_id,
                                  properties=None,
                                  value=None,
                                  format=None,
                                  id=None,
                                  type=None):
    body={}
    body['properties'] = properties
    body['value'] = value
    body['format'] = format
    return client.product_policy.create_or_update(resource_group_name=resource_group, service_name=name, product_id=product_id, policy_id=policy_id, parameters=body)


def delete_apimgmt_product_policy(cmd, client,
                                  resource_group,
                                  name,
                                  product_id,
                                  policy_id):
    return client.product_policy.delete(resource_group_name=resource_group, service_name=name, product_id=product_id, policy_id=policy_id, If-Match=If-Match)


def list_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.list_by_product(resource_group_name=resource_group, service_name=name, product_id=product_id, policy_id=policy_id)


def show_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.get(resource_group_name=resource_group, service_name=name, product_id=product_id, policy_id=policy_id)


def show_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.get(resource_group_name=resource_group, service_name=name, product_id=product_id, policy_id=policy_id)


def list_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.list_by_product(resource_group_name=resource_group, service_name=name, product_id=product_id, policy_id=policy_id)


def create_apimgmt_property(cmd, client,
                            resource_group,
                            name,
                            prop_id,
                            properties=None,
                            tags=None,
                            secret=None,
                            display_name=None,
                            value=None,
                            id=None,
                            type=None):
    body={}
    body['properties'] = properties
    body['tags'] = tags
    body['secret'] = secret
    body['display_name'] = display_name
    body['value'] = value
    return client.property.create_or_update(resource_group_name=resource_group, service_name=name, prop_id=prop_id, parameters=body)


def update_apimgmt_property(cmd, client,
                            resource_group,
                            name,
                            prop_id,
                            properties=None,
                            tags=None,
                            secret=None,
                            display_name=None,
                            value=None,
                            id=None,
                            type=None):
    body={}
    body['properties'] = properties
    body['tags'] = tags
    body['secret'] = secret
    body['display_name'] = display_name
    body['value'] = value
    return client.property.create_or_update(resource_group_name=resource_group, service_name=name, prop_id=prop_id, parameters=body)


def delete_apimgmt_property(cmd, client,
                            resource_group,
                            name,
                            prop_id):
    return client.property.delete(resource_group_name=resource_group, service_name=name, prop_id=prop_id, If-Match=If-Match)


def list_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.list_by_service(resource_group_name=resource_group, service_name=name, prop_id=prop_id)


def show_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.get(resource_group_name=resource_group, service_name=name, prop_id=prop_id)


def show_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.get(resource_group_name=resource_group, service_name=name, prop_id=prop_id)


def list_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.list_by_service(resource_group_name=resource_group, service_name=name, prop_id=prop_id)


def list_apimgmt_quota(cmd, client,
                       resource_group,
                       name,
                       quota_counter_key):
    return client.quota_by_counter_keys.list_by_service()


def show_apimgmt_quota_period(cmd, client,
                              resource_group,
                              name,
                              quota_counter_key,
                              quota_period_key):
    return client.quota_by_period_keys.get(resource_group_name=resource_group, service_name=name, quota_counter_key=quota_counter_key, quota_period_key=quota_period_key)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.region.list_by_service()


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.reports.list_by_api()


def create_apimgmt_subscription(cmd, client,
                                resource_group,
                                name,
                                sid,
                                properties=None,
                                owner_id=None,
                                scope=None,
                                display_name=None,
                                primary_key=None,
                                secondary_key=None,
                                state=None,
                                allow_tracing=None,
                                created_date=None,
                                start_date=None,
                                expiration_date=None,
                                end_date=None,
                                notification_date=None,
                                state_comment=None,
                                notify=None,
                                id=None,
                                type=None):
    body={}
    body['properties'] = properties
    body['owner_id'] = owner_id
    body['scope'] = scope
    body['display_name'] = display_name
    body['primary_key'] = primary_key
    body['secondary_key'] = secondary_key
    body['state'] = state
    body['allow_tracing'] = allow_tracing
    body['created_date'] = created_date
    body['start_date'] = start_date
    body['expiration_date'] = expiration_date
    body['end_date'] = end_date
    body['notification_date'] = notification_date
    body['state_comment'] = state_comment
    return client.subscription.create_or_update(resource_group_name=resource_group, service_name=name, sid=sid, parameters=body)


def update_apimgmt_subscription(cmd, client,
                                resource_group,
                                name,
                                sid,
                                properties=None,
                                owner_id=None,
                                scope=None,
                                display_name=None,
                                primary_key=None,
                                secondary_key=None,
                                state=None,
                                allow_tracing=None,
                                created_date=None,
                                start_date=None,
                                expiration_date=None,
                                end_date=None,
                                notification_date=None,
                                state_comment=None,
                                notify=None,
                                id=None,
                                type=None):
    body={}
    body['properties'] = properties
    body['owner_id'] = owner_id
    body['scope'] = scope
    body['display_name'] = display_name
    body['primary_key'] = primary_key
    body['secondary_key'] = secondary_key
    body['state'] = state
    body['allow_tracing'] = allow_tracing
    body['created_date'] = created_date
    body['start_date'] = start_date
    body['expiration_date'] = expiration_date
    body['end_date'] = end_date
    body['notification_date'] = notification_date
    body['state_comment'] = state_comment
    return client.subscription.create_or_update(resource_group_name=resource_group, service_name=name, sid=sid, parameters=body)


def delete_apimgmt_subscription(cmd, client,
                                resource_group,
                                name,
                                sid):
    return client.subscription.delete(resource_group_name=resource_group, service_name=name, sid=sid, If-Match=If-Match)


def list_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.list(resource_group_name=resource_group, service_name=name, sid=sid)


def show_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.get(resource_group_name=resource_group, service_name=name, sid=sid)


def list_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.list(resource_group_name=resource_group, service_name=name, sid=sid)


def show_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.get(resource_group_name=resource_group, service_name=name, sid=sid)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.tag_resource.list_by_service()


def show_apimgmt_tenant(cmd, client,
                        resource_group,
                        service_name,
                        name):
    return client.tenant_access.get(resource_group_name=resource_group, service_name=service_name, access_name=name)


def show_apimgmt_tenant(cmd, client,
                        resource_group,
                        service_name,
                        name):
    return client.tenant_access_git.get(resource_group_name=resource_group, service_name=service_name, access_name=name)


def create_apimgmt_user(cmd, client,
                        resource_group,
                        name,
                        user_id,
                        properties=None,
                        state=None,
                        note=None,
                        identities=None,
                        email=None,
                        first_name=None,
                        last_name=None,
                        password=None,
                        confirmation=None,
                        registration_date=None,
                        groups=None,
                        id=None,
                        type=None):
    body={}
    body['properties'] = properties
    body['state'] = state
    body['note'] = note
    body['identities'] = identities
    body['email'] = email
    body['first_name'] = first_name
    body['last_name'] = last_name
    body['password'] = password
    body['confirmation'] = confirmation
    body['registration_date'] = registration_date
    body['groups'] = groups
    return client.user.create_or_update(resource_group_name=resource_group, service_name=name, user_id=user_id, parameters=body)


def update_apimgmt_user(cmd, client,
                        resource_group,
                        name,
                        user_id,
                        properties=None,
                        state=None,
                        note=None,
                        identities=None,
                        email=None,
                        first_name=None,
                        last_name=None,
                        password=None,
                        confirmation=None,
                        registration_date=None,
                        groups=None,
                        id=None,
                        type=None):
    body={}
    body['properties'] = properties
    body['state'] = state
    body['note'] = note
    body['identities'] = identities
    body['email'] = email
    body['first_name'] = first_name
    body['last_name'] = last_name
    body['password'] = password
    body['confirmation'] = confirmation
    body['registration_date'] = registration_date
    body['groups'] = groups
    return client.user.create_or_update(resource_group_name=resource_group, service_name=name, user_id=user_id, parameters=body)


def delete_apimgmt_user(cmd, client,
                        resource_group,
                        name,
                        user_id):
    return client.user.delete(resource_group_name=resource_group, service_name=name, user_id=user_id, If-Match=If-Match)


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.list_by_service(resource_group_name=resource_group, service_name=name, user_id=user_id)


def show_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.get(resource_group_name=resource_group, service_name=name, user_id=user_id)


def show_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.get(resource_group_name=resource_group, service_name=name, user_id=user_id)


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.list_by_service(resource_group_name=resource_group, service_name=name, user_id=user_id)


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user_group.list()


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user_subscription.list()


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user_identities.list()


def show_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api_export.get(resource_group_name=resource_group, service_name=name, api_id=api_id, format=format, export=export)