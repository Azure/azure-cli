# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json

from azure.cli.core._profile import Profile
from azure.cli.core.util import send_raw_request
from azure.cli.core.auth.util import resource_to_scopes
from azure.cli.core.azclierror import AzCLIError
from knack.util import CLIError


class GraphClient:
    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.tenant = Profile(cli_ctx).get_login_credentials()[2]
        self.scopes = resource_to_scopes(cli_ctx.cloud.endpoints.microsoft_graph_resource_id)

        # https://graph.microsoft.com/ (AzureCloud)
        self.resource = cli_ctx.cloud.endpoints.microsoft_graph_resource_id

        # https://graph.microsoft.com/v1.0
        self.base_url = cli_ctx.cloud.endpoints.microsoft_graph_resource_id + 'v1.0'

    def _send(self, method, url, param=None, body=None):
        url = self.base_url + url

        if body:
            body = json.dumps(body)

        list_result = []
        is_list_result = False

        while True:
            try:
                r = send_raw_request(self.cli_ctx, method, url, resource=self.resource, uri_parameters=param, body=body)
            except CLIError as ex:
                raise GraphError(ex.response.json()['error']['message'], ex.response) from ex

            if r.text:
                dic = r.json()

                # The result is a list. Add value to list_result.
                if 'value' in dic:
                    is_list_result = True
                    list_result.extend(dic['value'])

                # Follow nextLink if available
                if '@odata.nextLink' in dic:
                    url = dic['@odata.nextLink']
                    continue

                # Result a list
                if is_list_result:
                    # 'value' can be empty list [], so we can't determine if the result is a list only by
                    # bool(list_result)
                    return list_result

                # Return a single object
                return r.json()
            else:
                return None

    # id is python built-in name: https://docs.python.org/3/library/functions.html#id
    # filter is python built-in name: https://docs.python.org/3/library/functions.html#filter

    def application_create(self, body):
        # https://docs.microsoft.com/en-us/graph/api/application-post-applications
        result = self._send("POST", "/applications", body=body)
        return result

    def application_get(self, id):
        # https://docs.microsoft.com/en-us/graph/api/application-get
        result = self._send("GET", "/applications/{id}".format(id=id))
        return result

    def application_list(self, filter=None):
        # https://docs.microsoft.com/en-us/graph/api/application-list
        result = self._send("GET", "/applications" + _filter_to_query(filter))
        return result

    def application_delete(self, id):
        # https://docs.microsoft.com/en-us/graph/api/application-delete
        result = self._send("DELETE", "/applications/{id}".format(id=id))
        return result

    def application_patch(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/application-update
        result = self._send("PATCH", "/applications/{id}".format(id=id), body=body)
        return result

    def application_owner_add(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/application-post-owners
        result = self._send("POST", "/applications/{id}/owners/$ref".format(id=id), body=body)
        return result

    def application_owner_list(self, id):
        # https://docs.microsoft.com/en-us/graph/api/application-list-owners
        result = self._send("GET", "/applications/{id}/owners".format(id=id))
        return result

    def application_owner_remove(self, id, owner_id):
        # https://docs.microsoft.com/en-us/graph/api/application-delete-owners
        result = self._send("DELETE", "/applications/{id}/owners/{owner_id}/$ref".format(id=id, owner_id=owner_id))
        return result

    def application_add_password(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/application-addpassword
        # 'addPassword' appears in the API, so we keep its name, instead of using application_password_add
        result = self._send("POST", "/applications/{id}/addPassword".format(id=id), body=body)
        return result

    def application_remove_password(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/application-removepassword
        result = self._send("POST", "/applications/{id}/removePassword".format(id=id), body=body)
        return result

    def service_principal_create(self, body):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-post-serviceprincipals
        result = self._send("POST", "/servicePrincipals", body=body)
        return result

    def service_principal_get(self, id):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-get
        result = self._send("GET", "/servicePrincipals/{id}".format(id=id))
        return result

    def service_principal_list(self, filter=None):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-list
        result = self._send("GET", "/servicePrincipals" + _filter_to_query(filter))
        return result

    def service_principal_delete(self, id):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-delete
        result = self._send("DELETE", "/servicePrincipals/{id}".format(id=id))
        return result

    def service_principal_patch(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-update
        result = self._send("PATCH", "/servicePrincipals/{id}".format(id=id), body=body)
        return result

    def service_principal_add_password(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-addpassword
        result = self._send("POST", "/servicePrincipals/{id}/addPassword".format(id=id), body=body)
        return result

    def service_principal_remove_password(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-removepassword
        result = self._send("POST", "/servicePrincipals/{id}/removePassword".format(id=id), body=body)
        return result

    def service_principal_owner_list(self, id):
        # https://docs.microsoft.com/en-us/graph/api/serviceprincipal-list-owners
        result = self._send("GET", "/servicePrincipals/{id}/owners".format(id=id))
        return result

    def owned_objects_list(self):
        # https://docs.microsoft.com/en-us/graph/api/user-list-ownedobjects
        result = self._send("GET", "/me/ownedObjects")
        return result

    def signed_in_user_get(self):
        # https://docs.microsoft.com/en-us/graph/api/user-get
        result = self._send("GET", "/me")
        return result

    def directory_object_get_by_ids(self, body):
        # https://docs.microsoft.com/en-us/graph/api/directoryobject-getbyids
        result = self._send("POST", "/directoryObjects/getByIds", body=body)
        return result

    def directory_object_check_member_groups(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/directoryobject-checkmembergroups
        result = self._send("POST", "/directoryObjects/{id}/checkMemberGroups".format(id=id), body=body)
        return result

    def directory_object_get_member_groups(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/directoryobject-getmembergroups
        result = self._send("POST", "/groups/{id}/getMemberGroups".format(id=id), body=body)
        return result

    def group_create(self, body):
        # https://docs.microsoft.com/en-us/graph/api/group-post-groups
        result = self._send("POST", "/groups", body=body)
        return result

    def group_get(self, id):
        # https://docs.microsoft.com/en-us/graph/api/group-get
        result = self._send("GET", "/groups/{id}".format(id=id))
        return result

    def group_list(self, filter=None):
        # https://docs.microsoft.com/en-us/graph/api/group-list
        result = self._send("GET", "/groups" + _filter_to_query(filter))
        return result

    def group_delete(self, id):
        # https://docs.microsoft.com/en-us/graph/api/group-delete
        result = self._send("DELETE", "/groups/{id}".format(id=id))
        return result

    def group_owner_list(self, id):
        # https://docs.microsoft.com/en-us/graph/api/group-list-owners
        result = self._send("GET", "/groups/{id}/owners".format(id=id))
        return result

    def group_owner_add(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/group-post-owners
        result = self._send("POST", "/groups/{id}/owners/$ref".format(id=id), body=body)
        return result

    def group_owner_remove(self, id, owner_id):
        # https://docs.microsoft.com/en-us/graph/api/group-delete-owners
        result = self._send("DELETE", "/groups/{id}/owners/{owner_id}/$ref".format(id=id, owner_id=owner_id))
        return result

    def group_member_list(self, id):
        # https://docs.microsoft.com/en-us/graph/api/group-list-members
        result = self._send("GET", '/groups/{id}/members'.format(id=id))
        return result

    def group_member_add(self, id, body):
        # https://docs.microsoft.com/en-us/graph/api/group-post-members
        result = self._send("POST", "/groups/{id}/members/$ref".format(id=id), body=body)
        return result

    def group_member_remove(self, id, member_id):
        # https://docs.microsoft.com/en-us/graph/api/group-delete-members
        result = self._send("DELETE", "/groups/{id}/members/{member_id}/$ref".format(id=id, member_id=member_id))
        return result

    def user_create(self, body):
        # https://docs.microsoft.com/graph/api/user-post-users
        result = self._send("POST", "/users", body=body)
        return result

    def user_get(self, id):
        # https://docs.microsoft.com/graph/api/user-get

        # MSGraph known issues regarding '$' and '#' https://docs.microsoft.com/en-us/graph/known-issues#users
        if '@' in id and '#' in id:
            id = id.replace('#', '%23')
        if id.startswith('$'):
            result = self._send("GET", "/users('{}')".format(id))
        else:
            result = self._send("GET", "/users/{}".format(id))
        return result

    def user_list(self, filter):
        # https://docs.microsoft.com/graph/api/user-list
        result = self._send("GET", "/users" + _filter_to_query(filter))
        return result

    def user_delete(self, id):
        # https://docs.microsoft.com/graph/api/user-delete
        result = self._send("DELETE", "/users/{}".format(id))
        return result

    def user_patch(self, id, body):
        # https://docs.microsoft.com/graph/api/user-update
        result = self._send("PATCH", "/users/{}".format(id), body=body)
        return result

    def user_member_of_list(self, id):
        # https://docs.microsoft.com/graph/api/user-list-memberof
        result = self._send("GET", "/users/{}/memberOf".format(id))
        return result

    def oauth2_permission_grant_create(self, body):
        # https://docs.microsoft.com/en-us/graph/api/oauth2permissiongrant-post
        result = self._send("POST", "/oauth2PermissionGrants", body=body)
        return result

    def oauth2_permission_grant_list(self, filter=None):
        # https://docs.microsoft.com/en-us/graph/api/oauth2permissiongrant-list
        result = self._send("GET", "/oauth2PermissionGrants" + _filter_to_query(filter))
        return result

    def oauth2_permission_grant_delete(self, id):
        # https://docs.microsoft.com/en-us/graph/api/oauth2permissiongrant-delete
        result = self._send("DELETE", "/oAuth2PermissionGrants/{id}".format(id=id))
        return result


def _filter_to_query(filter):
    if filter is not None:
        return "?$filter={}".format(filter)
    return ''


class GraphError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response
