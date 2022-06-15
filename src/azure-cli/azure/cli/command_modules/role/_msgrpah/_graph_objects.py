# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# property_map is a map from CLI argument name to API property name, such as display_name -> displayName.

# https://docs.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0
_application_property_map = {
    # base properties
    'display_name': 'displayName',
    'identifier_uris': 'identifierUris',
    'is_fallback_public_client': 'isFallbackPublicClient',
    'sign_in_audience': 'signInAudience',
    'key_credentials': 'keyCredentials',
    # web
    'web_home_page_url': ['web', 'homePageUrl'],
    'web_redirect_uris': ['web', 'redirectUris'],
    'enable_id_token_issuance': ['web', 'implicitGrantSettings', 'enableIdTokenIssuance'],
    'enable_access_token_issuance': ['web', 'implicitGrantSettings', 'enableAccessTokenIssuance'],
    # publicClient
    'public_client_redirect_uris': ['publicClient', 'redirectUris'],
    # JSON properties
    'app_roles': 'appRoles',
    'optional_claims': 'optionalClaims',
    'required_resource_accesses': 'requiredResourceAccess',
}

# https://docs.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0#properties
_user_property_map = {
    # base properties
    'account_enabled': 'accountEnabled',
    'display_name': 'displayName',
    'mail_nickname': 'mailNickname',
    'user_principal_name': 'userPrincipalName',
    'immutable_id': 'onPremisesImmutableId',
    'password': ['passwordProfile', 'password'],
    'force_change_password_next_sign_in': ['passwordProfile', 'forceChangePasswordNextSignIn']
}

# https://docs.microsoft.com/en-us/graph/api/resources/group?view=graph-rest-1.0#properties
_group_property_map = {
    'display_name': 'displayName',
    'mail_nickname': 'mailNickname',
    'mail_enabled': 'mailEnabled',
    'security_enabled': 'securityEnabled',
    'description': 'description'
}


_object_type_to_property_map = {
    'application': _application_property_map,
    'user': _user_property_map,
    'group': _group_property_map
}


def set_object_properties(object_type, graph_object, **kwargs):
    """Set properties of the graph object according to its property map.

    :param object_type: String representation of the object type. One of 'application', 'user', 'group'.
    :param graph_object: Dict representing the graph object.
    :param kwargs: CLI argument name-value pairs.
    """
    # This design of passing the string representation of the object type mimics Azure Python SDK:
    #   body_content = self._serialize.body(parameters, 'ApplicationCreateParameters')
    property_map = _object_type_to_property_map[object_type]
    for arg, value in kwargs.items():
        if value is not None:
            property_path = property_map[arg]
            # If property path is a list, such as web/implicitGrantSettings/enableIdTokenIssuance,
            # create intermediate sub-objects if not present
            if isinstance(property_path, list):
                sub_object = graph_object
                for property_name in property_path[0:-1]:
                    sub_object = sub_object.setdefault(property_name, {})
                sub_object[property_path[-1]] = value
            else:
                graph_object[property_path] = value
