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
    return client.api.create(resource_group, name, api_id, body)


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
    return client.api.update(resource_group, name, api_id, body)


def delete_apimgmt_api(cmd, client,
                       resource_group,
                       name,
                       api_id):
    return client.api.delete(resource_group, name, api_id, If-Match)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.list(resource_group, name, api_id)


def show_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.show(resource_group, name, api_id)


def show_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.show(resource_group, name, api_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api.list(resource_group, name, api_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api_revision.list()


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
    return client.api_release.create(resource_group, name, api_id, release_id, body)


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
    return client.api_release.update(resource_group, name, api_id, release_id, body)


def delete_apimgmt_api_release(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               release_id):
    return client.api_release.delete(resource_group, name, api_id, release_id, If-Match)


def list_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.list(resource_group, name, api_id, release_id)


def show_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.show(resource_group, name, api_id, release_id)


def show_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.show(resource_group, name, api_id, release_id)


def list_apimgmt_api_release(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             release_id):
    return client.api_release.list(resource_group, name, api_id, release_id)


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
    return client.api_operation.create(resource_group, name, api_id, operation_id, body)


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
    return client.api_operation.update(resource_group, name, api_id, operation_id, body)


def delete_apimgmt_api_operation(cmd, client,
                                 resource_group,
                                 name,
                                 api_id,
                                 operation_id):
    return client.api_operation.delete(resource_group, name, api_id, operation_id, If-Match)


def list_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.list(resource_group, name, api_id, operation_id)


def show_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.show(resource_group, name, api_id, operation_id)


def show_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.show(resource_group, name, api_id, operation_id)


def list_apimgmt_api_operation(cmd, client,
                               resource_group,
                               name,
                               api_id,
                               operation_id):
    return client.api_operation.list(resource_group, name, api_id, operation_id)


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
    return client.api_operation_policy.create(resource_group, name, api_id, operation_id, policy_id, body)


def delete_apimgmt_api_operation_policy(cmd, client,
                                        resource_group,
                                        name,
                                        api_id,
                                        operation_id,
                                        policy_id):
    return client.api_operation_policy.delete(resource_group, name, api_id, operation_id, policy_id, If-Match)


def list_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.list(resource_group, name, api_id, operation_id, policy_id)


def show_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.show(resource_group, name, api_id, operation_id, policy_id)


def show_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.show(resource_group, name, api_id, operation_id, policy_id)


def list_apimgmt_api_operation_policy(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      operation_id,
                                      policy_id):
    return client.api_operation_policy.list(resource_group, name, api_id, operation_id, policy_id)


def create_apimgmt_tag(cmd, client,
                       resource_group,
                       name,
                       tag_id,
                       properties=None,
                       display_name=None,
                       id=None,
                       type=None):
    return client.tag.create(resource_group, name, tag_id, body)


def update_apimgmt_tag(cmd, client,
                       resource_group,
                       name,
                       tag_id,
                       properties=None,
                       display_name=None,
                       id=None,
                       type=None):
    return client.tag.update(resource_group, name, tag_id, body)


def delete_apimgmt_tag(cmd, client,
                       resource_group,
                       name,
                       tag_id):
    return client.tag.delete(resource_group, name, tag_id, If-Match)


def list_apimgmt_tag(cmd, client,
                     resource_group,
                     name,
                     tag_id):
    return client.tag.list(resource_group, name, tag_id)


def show_apimgmt_tag(cmd, client,
                     resource_group,
                     name,
                     tag_id):
    return client.tag.show(resource_group, name, tag_id)


def list_apimgmt_tag_api_product_operation(cmd, client,
                                           resource_group,
                                           name,
                                           tag_id,
                                           api_id,
                                           product_id,
                                           operation_id):
    return client.tag.list(resource_group, name, tag_id)


def show_apimgmt_tag_api_product_operation(cmd, client,
                                           resource_group,
                                           name,
                                           tag_id,
                                           api_id,
                                           product_id,
                                           operation_id):
    return client.tag.show(resource_group, name, tag_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.api_product.list()


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
    return client.api_policy.create(resource_group, name, api_id, policy_id, body)


def delete_apimgmt_api_policy(cmd, client,
                              resource_group,
                              name,
                              api_id,
                              policy_id):
    return client.api_policy.delete(resource_group, name, api_id, policy_id, If-Match)


def list_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.list(resource_group, name, api_id, policy_id)


def show_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.show(resource_group, name, api_id, policy_id)


def show_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.show(resource_group, name, api_id, policy_id)


def list_apimgmt_api_policy(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            policy_id):
    return client.api_policy.list(resource_group, name, api_id, policy_id)


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
    return client.api_schema.create(resource_group, name, api_id, schema_id, body)


def delete_apimgmt_api_schema(cmd, client,
                              resource_group,
                              name,
                              api_id,
                              schema_id):
    return client.api_schema.delete(resource_group, name, api_id, schema_id, If-Match)


def list_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.list(resource_group, name, api_id, schema_id)


def show_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.show(resource_group, name, api_id, schema_id)


def show_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.show(resource_group, name, api_id, schema_id)


def list_apimgmt_api_schema(cmd, client,
                            resource_group,
                            name,
                            api_id,
                            schema_id):
    return client.api_schema.list(resource_group, name, api_id, schema_id)


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
    return client.api_diagnostic.create(resource_group, name, api_id, diagnostic_id, body)


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
    return client.api_diagnostic.update(resource_group, name, api_id, diagnostic_id, body)


def delete_apimgmt_api_diagnostic(cmd, client,
                                  resource_group,
                                  name,
                                  api_id,
                                  diagnostic_id):
    return client.api_diagnostic.delete(resource_group, name, api_id, diagnostic_id, If-Match)


def list_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.list(resource_group, name, api_id, diagnostic_id)


def show_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.show(resource_group, name, api_id, diagnostic_id)


def show_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.show(resource_group, name, api_id, diagnostic_id)


def list_apimgmt_api_diagnostic(cmd, client,
                                resource_group,
                                name,
                                api_id,
                                diagnostic_id):
    return client.api_diagnostic.list(resource_group, name, api_id, diagnostic_id)


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
    return client.api_issue.create(resource_group, name, api_id, issue_id, body)


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
    return client.api_issue.update(resource_group, name, api_id, issue_id, body)


def delete_apimgmt_api_issue(cmd, client,
                             resource_group,
                             name,
                             api_id,
                             issue_id):
    return client.api_issue.delete(resource_group, name, api_id, issue_id, If-Match)


def list_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.list(resource_group, name, api_id, issue_id)


def show_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.show(resource_group, name, api_id, issue_id)


def show_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.show(resource_group, name, api_id, issue_id)


def list_apimgmt_api_issue(cmd, client,
                           resource_group,
                           name,
                           api_id,
                           issue_id):
    return client.api_issue.list(resource_group, name, api_id, issue_id)


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
    return client.api_issue_comment.create(resource_group, name, api_id, issue_id, comment_id, body)


def delete_apimgmt_api_issue_comment(cmd, client,
                                     resource_group,
                                     name,
                                     api_id,
                                     issue_id,
                                     comment_id):
    return client.api_issue_comment.delete(resource_group, name, api_id, issue_id, comment_id, If-Match)


def list_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.list(resource_group, name, api_id, issue_id, comment_id)


def show_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.show(resource_group, name, api_id, issue_id, comment_id)


def show_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.show(resource_group, name, api_id, issue_id, comment_id)


def list_apimgmt_api_issue_comment(cmd, client,
                                   resource_group,
                                   name,
                                   api_id,
                                   issue_id,
                                   comment_id):
    return client.api_issue_comment.list(resource_group, name, api_id, issue_id, comment_id)


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
    return client.api_issue_attachment.create(resource_group, name, api_id, issue_id, attachment_id, body)


def delete_apimgmt_api_issue_attachment(cmd, client,
                                        resource_group,
                                        name,
                                        api_id,
                                        issue_id,
                                        attachment_id):
    return client.api_issue_attachment.delete(resource_group, name, api_id, issue_id, attachment_id, If-Match)


def list_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.list(resource_group, name, api_id, issue_id, attachment_id)


def show_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.show(resource_group, name, api_id, issue_id, attachment_id)


def show_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.show(resource_group, name, api_id, issue_id, attachment_id)


def list_apimgmt_api_issue_attachment(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      issue_id,
                                      attachment_id):
    return client.api_issue_attachment.list(resource_group, name, api_id, issue_id, attachment_id)


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
    return client.api_tag_description.create(resource_group, name, api_id, tag_id, body)


def delete_apimgmt_api_tagdescription(cmd, client,
                                      resource_group,
                                      name,
                                      api_id,
                                      tag_id):
    return client.api_tag_description.delete(resource_group, name, api_id, tag_id, If-Match)


def list_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.list(resource_group, name, api_id, tag_id)


def show_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.show(resource_group, name, api_id, tag_id)


def show_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.show(resource_group, name, api_id, tag_id)


def list_apimgmt_api_tagdescription(cmd, client,
                                    resource_group,
                                    name,
                                    api_id,
                                    tag_id):
    return client.api_tag_description.list(resource_group, name, api_id, tag_id)


def list_apimgmt_api(cmd, client,
                     resource_group,
                     name,
                     api_id):
    return client.operation.list()


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
    return client.api_version_set.create(resource_group, name, version_set_id, body)


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
    return client.api_version_set.update(resource_group, name, version_set_id, body)


def delete_apimgmt_apiversionset(cmd, client,
                                 resource_group,
                                 name,
                                 version_set_id):
    return client.api_version_set.delete(resource_group, name, version_set_id, If-Match)


def list_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.list(resource_group, name, version_set_id)


def show_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.show(resource_group, name, version_set_id)


def show_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.show(resource_group, name, version_set_id)


def list_apimgmt_apiversionset(cmd, client,
                               resource_group,
                               name,
                               version_set_id):
    return client.api_version_set.list(resource_group, name, version_set_id)


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
    return client.authorization_server.create(resource_group, name, authsid, body)


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
    return client.authorization_server.update(resource_group, name, authsid, body)


def delete_apimgmt_authorizationserver(cmd, client,
                                       resource_group,
                                       name,
                                       authsid):
    return client.authorization_server.delete(resource_group, name, authsid, If-Match)


def list_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.list(resource_group, name, authsid)


def show_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.show(resource_group, name, authsid)


def show_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.show(resource_group, name, authsid)


def list_apimgmt_authorizationserver(cmd, client,
                                     resource_group,
                                     name,
                                     authsid):
    return client.authorization_server.list(resource_group, name, authsid)


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
    return client.backend.create(resource_group, name, backend_id, body)


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
    return client.backend.update(resource_group, name, backend_id, body)


def delete_apimgmt_backend(cmd, client,
                           resource_group,
                           name,
                           backend_id):
    return client.backend.delete(resource_group, name, backend_id, If-Match)


def list_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.list(resource_group, name, backend_id)


def show_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.show(resource_group, name, backend_id)


def show_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.show(resource_group, name, backend_id)


def list_apimgmt_backend(cmd, client,
                         resource_group,
                         name,
                         backend_id):
    return client.backend.list(resource_group, name, backend_id)


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
    return client.cache.create(resource_group, name, cache_id, body)


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
    return client.cache.update(resource_group, name, cache_id, body)


def delete_apimgmt_cache(cmd, client,
                         resource_group,
                         name,
                         cache_id):
    return client.cache.delete(resource_group, name, cache_id, If-Match)


def list_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.list(resource_group, name, cache_id)


def show_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.show(resource_group, name, cache_id)


def show_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.show(resource_group, name, cache_id)


def list_apimgmt_cache(cmd, client,
                       resource_group,
                       name,
                       cache_id):
    return client.cache.list(resource_group, name, cache_id)


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
    return client.certificate.create(resource_group, name, certificate_id, body)


def delete_apimgmt_certificate(cmd, client,
                               resource_group,
                               name,
                               certificate_id):
    return client.certificate.delete(resource_group, name, certificate_id, If-Match)


def list_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.list(resource_group, name, certificate_id)


def show_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.show(resource_group, name, certificate_id)


def show_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.show(resource_group, name, certificate_id)


def list_apimgmt_certificate(cmd, client,
                             resource_group,
                             name,
                             certificate_id):
    return client.certificate.list(resource_group, name, certificate_id)


def list_(cmd, client):
    return client.api_management_operations.list()


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service_skus.list()


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
    return client.api_management_service.create(resource_group, name, body)


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
    return client.api_management_service.update(resource_group, name, body)


def delete_apimgmt(cmd, client,
                   resource_group,
                   name):
    return client.api_management_service.delete(resource_group, name)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.list(resource_group, name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.show(resource_group, name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.show(resource_group, name)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.api_management_service.list(resource_group, name)


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
    return client.diagnostic.create(resource_group, name, diagnostic_id, body)


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
    return client.diagnostic.update(resource_group, name, diagnostic_id, body)


def delete_apimgmt_diagnostic(cmd, client,
                              resource_group,
                              name,
                              diagnostic_id):
    return client.diagnostic.delete(resource_group, name, diagnostic_id, If-Match)


def list_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.list(resource_group, name, diagnostic_id)


def show_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.show(resource_group, name, diagnostic_id)


def show_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.show(resource_group, name, diagnostic_id)


def list_apimgmt_diagnostic(cmd, client,
                            resource_group,
                            name,
                            diagnostic_id):
    return client.diagnostic.list(resource_group, name, diagnostic_id)


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
    return client.email_template.create(resource_group, service_name, name, body)


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
    return client.email_template.update(resource_group, service_name, name, body)


def delete_apimgmt_template(cmd, client,
                            resource_group,
                            service_name,
                            name):
    return client.email_template.delete(resource_group, service_name, name, If-Match)


def list_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.list(resource_group, service_name, name)


def show_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.show(resource_group, service_name, name)


def show_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.show(resource_group, service_name, name)


def list_apimgmt_template(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.email_template.list(resource_group, service_name, name)


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
    return client.group.create(resource_group, name, group_id, body)


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
    return client.group.update(resource_group, name, group_id, body)


def delete_apimgmt_group(cmd, client,
                         resource_group,
                         name,
                         group_id):
    return client.group.delete(resource_group, name, group_id, If-Match)


def list_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.list(resource_group, name, group_id)


def show_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.show(resource_group, name, group_id)


def show_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.show(resource_group, name, group_id)


def list_apimgmt_group(cmd, client,
                       resource_group,
                       name,
                       group_id):
    return client.group.list(resource_group, name, group_id)


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
    return client.group_user.create(resource_group, name, group_id, user_id)


def delete_apimgmt_group_user(cmd, client,
                              resource_group,
                              name,
                              group_id,
                              user_id):
    return client.group_user.delete(resource_group, name, group_id, user_id)


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
    return client.identity_provider.create(resource_group, service_name, name, body)


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
    return client.identity_provider.update(resource_group, service_name, name, body)


def delete_apimgmt_identityprovider(cmd, client,
                                    resource_group,
                                    service_name,
                                    name):
    return client.identity_provider.delete(resource_group, service_name, name, If-Match)


def list_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.list(resource_group, service_name, name)


def show_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.show(resource_group, service_name, name)


def show_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.show(resource_group, service_name, name)


def list_apimgmt_identityprovider(cmd, client,
                                  resource_group,
                                  service_name,
                                  name):
    return client.identity_provider.list(resource_group, service_name, name)


def show_apimgmt_issue(cmd, client,
                       resource_group,
                       name,
                       issue_id):
    return client.issue.show(resource_group, name, issue_id)


def list_apimgmt_issue(cmd, client,
                       resource_group,
                       name,
                       issue_id):
    return client.issue.list(resource_group, name, issue_id)


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
    return client.logger.create(resource_group, name, logger_id, body)


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
    return client.logger.update(resource_group, name, logger_id, body)


def delete_apimgmt_logger(cmd, client,
                          resource_group,
                          name,
                          logger_id):
    return client.logger.delete(resource_group, name, logger_id, If-Match)


def list_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.list(resource_group, name, logger_id)


def show_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.show(resource_group, name, logger_id)


def show_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.show(resource_group, name, logger_id)


def list_apimgmt_logger(cmd, client,
                        resource_group,
                        name,
                        logger_id):
    return client.logger.list(resource_group, name, logger_id)


def list_apimgmt_location(cmd, client,
                          resource_group,
                          service_name,
                          name):
    return client.network_status.list()


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
    return client.notification.create(resource_group, service_name, name)


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.list(resource_group, service_name, name)


def show_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.show(resource_group, service_name, name)


def show_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.show(resource_group, service_name, name)


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification.list(resource_group, service_name, name)


def create_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              name,
                                              user_id,
                                              id=None,
                                              type=None,
                                              properties=None):
    return client.notification_recipient_user.create(resource_group, service_name, name, user_id)


def delete_apimgmt_notification_recipientuser(cmd, client,
                                              resource_group,
                                              service_name,
                                              name,
                                              user_id):
    return client.notification_recipient_user.delete(resource_group, service_name, name, user_id)


def list_apimgmt_notification_recipientuser(cmd, client,
                                            resource_group,
                                            service_name,
                                            name,
                                            user_id):
    return client.notification_recipient_user.list()


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification_recipient_user.list()


def create_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               name,
                                               email,
                                               id=None,
                                               type=None,
                                               properties=None):
    return client.notification_recipient_email.create(resource_group, service_name, name, email)


def delete_apimgmt_notification_recipientemail(cmd, client,
                                               resource_group,
                                               service_name,
                                               name,
                                               email):
    return client.notification_recipient_email.delete(resource_group, service_name, name, email)


def list_apimgmt_notification_recipientemail(cmd, client,
                                             resource_group,
                                             service_name,
                                             name,
                                             email):
    return client.notification_recipient_email.list()


def list_apimgmt_notification(cmd, client,
                              resource_group,
                              service_name,
                              name):
    return client.notification_recipient_email.list()


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
    return client.open_id_connect_provider.create(resource_group, name, opid, body)


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
    return client.open_id_connect_provider.update(resource_group, name, opid, body)


def delete_apimgmt_openidconnectprovider(cmd, client,
                                         resource_group,
                                         name,
                                         opid):
    return client.open_id_connect_provider.delete(resource_group, name, opid, If-Match)


def list_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.list(resource_group, name, opid)


def show_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.show(resource_group, name, opid)


def show_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.show(resource_group, name, opid)


def list_apimgmt_openidconnectprovider(cmd, client,
                                       resource_group,
                                       name,
                                       opid):
    return client.open_id_connect_provider.list(resource_group, name, opid)


def create_apimgmt_policy(cmd, client,
                          resource_group,
                          name,
                          policy_id,
                          properties=None,
                          value=None,
                          format=None,
                          id=None,
                          type=None):
    return client.policy.create(resource_group, name, policy_id, body)


def delete_apimgmt_policy(cmd, client,
                          resource_group,
                          name,
                          policy_id):
    return client.policy.delete(resource_group, name, policy_id, If-Match)


def list_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.list(resource_group, name, policy_id)


def show_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.show(resource_group, name, policy_id)


def show_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.show(resource_group, name, policy_id)


def list_apimgmt_policy(cmd, client,
                        resource_group,
                        name,
                        policy_id):
    return client.policy.list(resource_group, name, policy_id)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.policy_snippet.list()


def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   id=None,
                   type=None):
    return client.sign_in_settings.create(resource_group, name, body)


def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   id=None,
                   type=None):
    return client.sign_in_settings.update(resource_group, name, body)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_in_settings.show(resource_group, name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_in_settings.show(resource_group, name)


def create_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   terms_of_service=None,
                   id=None,
                   type=None):
    return client.sign_up_settings.create(resource_group, name, body)


def update_apimgmt(cmd, client,
                   resource_group,
                   name,
                   properties=None,
                   enabled=None,
                   terms_of_service=None,
                   id=None,
                   type=None):
    return client.sign_up_settings.update(resource_group, name, body)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_up_settings.show(resource_group, name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.sign_up_settings.show(resource_group, name)


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
    return client.delegation_settings.create(resource_group, name, body)


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
    return client.delegation_settings.update(resource_group, name, body)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.delegation_settings.show(resource_group, name)


def show_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.delegation_settings.show(resource_group, name)


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
    return client.product.create(resource_group, name, product_id, body)


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
    return client.product.update(resource_group, name, product_id, body)


def delete_apimgmt_product(cmd, client,
                           resource_group,
                           name,
                           product_id):
    return client.product.delete(resource_group, name, product_id, If-Match)


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.list(resource_group, name, product_id)


def show_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.show(resource_group, name, product_id)


def show_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.show(resource_group, name, product_id)


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product.list(resource_group, name, product_id)


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
    return client.product_api.create(resource_group, name, product_id, api_id)


def delete_apimgmt_product_api(cmd, client,
                               resource_group,
                               name,
                               product_id,
                               api_id):
    return client.product_api.delete(resource_group, name, product_id, api_id)


def list_apimgmt_product_api(cmd, client,
                             resource_group,
                             name,
                             product_id,
                             api_id):
    return client.product_api.list()


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product_api.list()


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
    return client.product_group.create(resource_group, name, product_id, group_id)


def delete_apimgmt_product_group(cmd, client,
                                 resource_group,
                                 name,
                                 product_id,
                                 group_id):
    return client.product_group.delete(resource_group, name, product_id, group_id)


def list_apimgmt_product_group(cmd, client,
                               resource_group,
                               name,
                               product_id,
                               group_id):
    return client.product_group.list()


def list_apimgmt_product(cmd, client,
                         resource_group,
                         name,
                         product_id):
    return client.product_group.list()


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
    return client.product_policy.create(resource_group, name, product_id, policy_id, body)


def delete_apimgmt_product_policy(cmd, client,
                                  resource_group,
                                  name,
                                  product_id,
                                  policy_id):
    return client.product_policy.delete(resource_group, name, product_id, policy_id, If-Match)


def list_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.list(resource_group, name, product_id, policy_id)


def show_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.show(resource_group, name, product_id, policy_id)


def show_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.show(resource_group, name, product_id, policy_id)


def list_apimgmt_product_policy(cmd, client,
                                resource_group,
                                name,
                                product_id,
                                policy_id):
    return client.product_policy.list(resource_group, name, product_id, policy_id)


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
    return client.property.create(resource_group, name, prop_id, body)


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
    return client.property.update(resource_group, name, prop_id, body)


def delete_apimgmt_property(cmd, client,
                            resource_group,
                            name,
                            prop_id):
    return client.property.delete(resource_group, name, prop_id, If-Match)


def list_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.list(resource_group, name, prop_id)


def show_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.show(resource_group, name, prop_id)


def show_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.show(resource_group, name, prop_id)


def list_apimgmt_property(cmd, client,
                          resource_group,
                          name,
                          prop_id):
    return client.property.list(resource_group, name, prop_id)


def list_apimgmt_quota(cmd, client,
                       resource_group,
                       name,
                       quota_counter_key):
    return client.quota_by_counter_keys.list()


def show_apimgmt_quota_period(cmd, client,
                              resource_group,
                              name,
                              quota_counter_key,
                              quota_period_key):
    return client.quota_by_period_keys.show(resource_group, name, quota_counter_key, quota_period_key)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.region.list()


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.reports.list()


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
    return client.subscription.create(resource_group, name, sid, body)


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
    return client.subscription.update(resource_group, name, sid, body)


def delete_apimgmt_subscription(cmd, client,
                                resource_group,
                                name,
                                sid):
    return client.subscription.delete(resource_group, name, sid, If-Match)


def list_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.list(resource_group, name, sid)


def show_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.show(resource_group, name, sid)


def list_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.list(resource_group, name, sid)


def show_apimgmt_subscription(cmd, client,
                              resource_group,
                              name,
                              sid):
    return client.subscription.show(resource_group, name, sid)


def list_apimgmt(cmd, client,
                 resource_group,
                 name):
    return client.tag_resource.list()


def show_apimgmt_tenant(cmd, client,
                        resource_group,
                        service_name,
                        name):
    return client.tenant_access.show(resource_group, service_name, name)


def show_apimgmt_tenant(cmd, client,
                        resource_group,
                        service_name,
                        name):
    return client.tenant_access_git.show(resource_group, service_name, name)


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
    return client.user.create(resource_group, name, user_id, body)


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
    return client.user.update(resource_group, name, user_id, body)


def delete_apimgmt_user(cmd, client,
                        resource_group,
                        name,
                        user_id):
    return client.user.delete(resource_group, name, user_id, If-Match)


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.list(resource_group, name, user_id)


def show_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.show(resource_group, name, user_id)


def show_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.show(resource_group, name, user_id)


def list_apimgmt_user(cmd, client,
                      resource_group,
                      name,
                      user_id):
    return client.user.list(resource_group, name, user_id)


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
    return client.api_export.show(resource_group, name, api_id, format, export)