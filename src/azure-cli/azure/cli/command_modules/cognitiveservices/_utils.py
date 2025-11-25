# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.mgmt.cognitiveservices.models import ConnectionCategory, \
    ResourceIdentityType as IdentityType, Identity, UserAssignedIdentity

from os import PathLike
from typing import IO, Any, AnyStr, Dict, Optional, Union


def compose_identity(
    system_assigned: bool,
    user_assigned_identity: Optional[str]
):
    identity_type = None
    user_identities = None
    if user_assigned_identity is not None:
        user_identities = {user_assigned_identity: UserAssignedIdentity()}

    if system_assigned is not None and user_assigned_identity is not None:
        identity_type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED
    elif system_assigned:
        identity_type = IdentityType.SYSTEM_ASSIGNED
    elif user_assigned_identity is not None:
        identity_type = IdentityType.USER_ASSIGNED

    return Identity(type=identity_type, user_assigned_identities=user_identities) if identity_type is not None else None


def snake_to_camel(name):
    import re
    return re.sub(r"(?:^|_)([a-z])", lambda x: x.group(1).upper(), name)


def get_auth_model_connection_properties(connection_category: str, auth_type: str | None, auth_params: Dict[str, Any]):
    from azure.mgmt.cognitiveservices.models import (
        PATAuthTypeConnectionProperties,
        SASAuthTypeConnectionProperties,
        UsernamePasswordAuthTypeConnectionProperties,
        ManagedIdentityAuthTypeConnectionProperties,
        OAuth2AuthTypeConnectionProperties,
        ServicePrincipalAuthTypeConnectionProperties,
        AccessKeyAuthTypeConnectionProperties,
        ApiKeyAuthConnectionProperties,
        NoneAuthTypeConnectionProperties,
        AccountKeyAuthTypeConnectionProperties,
        AADAuthTypeConnectionProperties,
        ConnectionPersonalAccessToken,
        ConnectionSharedAccessSignature,
        ConnectionUsernamePassword,
        ConnectionAccessKey,
        ConnectionApiKey,
        ConnectionAccountKey,
        ConnectionServicePrincipal,
        ConnectionManagedIdentity,
        ConnectionOAuth2
    )
    # These categories were using None auth type with AzCLI ML connections
    CAN_USE_NONE_AUTH = [ConnectionCategory.GIT, ConnectionCategory.PYTHON_FEED]
    auth_model = None
    match snake_to_camel(auth_type):
        case "PersonalAccessToken" | "Pat":
            auth_model = PATAuthTypeConnectionProperties(
                credentials=ConnectionPersonalAccessToken(**auth_params))
        case "SasToken" | "Sas":
            auth_model = SASAuthTypeConnectionProperties(
                credentials=ConnectionSharedAccessSignature(**auth_params))
        case "UsernamePassword":
            auth_model = UsernamePasswordAuthTypeConnectionProperties(
                credentials=ConnectionUsernamePassword(**auth_params))
        case "ManagedIdentity":
            auth_model = ManagedIdentityAuthTypeConnectionProperties(
                credentials=ConnectionManagedIdentity(**auth_params))
        case "ServicePrincipal":
            auth_model = ServicePrincipalAuthTypeConnectionProperties(
                credentials=ConnectionServicePrincipal(**auth_params))
        case "AccessKey":
            auth_model = AccessKeyAuthTypeConnectionProperties(
                credentials=ConnectionAccessKey(**auth_params))
        case "ApiKey":
            auth_model = ApiKeyAuthConnectionProperties(
                credentials=ConnectionApiKey(**auth_params))
        case "OAuth2":
            auth_model = OAuth2AuthTypeConnectionProperties(
                credentials=ConnectionOAuth2(**auth_params))
        case "None":
            if connection_category in CAN_USE_NONE_AUTH:
                auth_model = NoneAuthTypeConnectionProperties()
            else:
                auth_model = AADAuthTypeConnectionProperties()
        case "AccountKey":
            auth_model = AccountKeyAuthTypeConnectionProperties(
                credentials=ConnectionAccountKey(**auth_params))
        case "Aad":
            auth_model = AADAuthTypeConnectionProperties()

    return auth_model

# --------------------------------------------------------------------------------------------
# Connection utilities
# --------------------------------------------------------------------------------------------


def _get_connection_alternate_target_names():
    return ["target", "api_base", "url", "azure_endpoint", "endpoint"]


def _get_valid_connection_types():
    return [conn_type.value for conn_type in ConnectionCategory]


def _extract_connection_target(conn_dict: Dict[str, Any]) -> str | None:
    connection_target = None
    for target_name in _get_connection_alternate_target_names():
        if target_name in conn_dict:
            connection_target = conn_dict[target_name]
            break
    return connection_target


def _extract_auth_type_and_params(conn_dict: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    auth_type = "None"
    auth_params = {}
    if 'credentials' in conn_dict:
        auth_type = conn_dict['credentials'].get('type', None)
        auth_params = {k: v for k, v in conn_dict['credentials'].items() if k != 'type'}
    elif 'api_key' in conn_dict:
        auth_type = 'ApiKey'
        auth_params = {'key': conn_dict['api_key']}
    return (auth_type, auth_params)


def get_connection_category(connection_type: str):
    connection_category = None
    normalized_name = snake_to_camel(connection_type)
    try:
        connection_category = ConnectionCategory(normalized_name)
    except ValueError:
        from . _ml_utils import _ML_CONNECTION_TYPE_TO_COGNITIVE_SERVICES_CONNECTION_TYPE
        connection_category = _ML_CONNECTION_TYPE_TO_COGNITIVE_SERVICES_CONNECTION_TYPE.get(normalized_name, None)
    return connection_category


def compose_connection(
    connection_type: str,
    target: str | None,
    auth_type: str,
    auth_params: Dict[str, Any],
    metadata: Optional[Dict[str, str]] = None
):
    connection_category = get_connection_category(connection_type)
    if connection_category is None:
        raise InvalidArgumentValueError(
            f"Invalid connection type '{connection_type}'. ",
            recommendation=[
                "Verify that the connection type property is set to one of the following values:",
                ', '.join(_get_valid_connection_types())])

    connection = get_auth_model_connection_properties(connection_category, auth_type, auth_params)
    if connection is None:
        raise InvalidArgumentValueError(
            f"Invalid or unsupported auth type '{auth_type}' for connection type '{connection_type}'. ",
            recommendation=[
                "Verify that the auth type property is set to a valid value supported for this connection type."
            ])
    connection.category = connection_category
    connection.target = target
    connection.metadata = metadata or {}

    return connection


def _load_connection_from_dict(conn_dict: Dict[str, Any]):
    connection_type = conn_dict.get("type", None)
    if connection_type is None:
        raise InvalidArgumentValueError(
            "Connection type is required but not found in the provided data.",
            recommendation=[
                "Ensure that the 'type' property is specified in the connection definition."
            ]
        )
    target = _extract_connection_target(conn_dict)
    auth_type, auth_params = _extract_auth_type_and_params(conn_dict)
    return compose_connection(
        connection_type=connection_type,
        target=target,
        auth_type=auth_type,
        auth_params=auth_params,
        metadata=conn_dict.get("metadata", {})
    )


def load_connection_from_source(source: Union[str, PathLike, IO[AnyStr]]):
    """
    Load a connection from a JSON or YAML file or string.
    """
    conn_dict = _load_source_as_dict(source)
    return _load_connection_from_dict(conn_dict)


def _get_as_streamed_context_manager(source: Union[str, PathLike, IO[AnyStr]]):
    from pathlib import Path
    from contextlib import nullcontext
    from io import StringIO
    if isinstance(source, PathLike):
        return open(source, 'r', encoding='utf-8')
    if isinstance(source, str):
        if Path(source).is_file():
            return open(source, 'r', encoding='utf-8')
        return nullcontext(StringIO(source))
    return nullcontext(StringIO(""))


def _load_source_as_dict(source: Union[str, PathLike, IO[AnyStr]]) -> dict:
    import json
    loaded_dict = None
    load_errors = []
    try:
        with _get_as_streamed_context_manager(source) as data_stream:
            loaded_dict = json.load(data_stream)
    except (json.JSONDecodeError) as json_error:
        load_errors.append(str(json_error))
        import yaml
        try:
            with _get_as_streamed_context_manager(source) as data_stream:
                loaded_dict = yaml.safe_load(data_stream)
        except yaml.YAMLError as yaml_error:
            load_errors.append(str(yaml_error))

    if isinstance(loaded_dict, dict):
        return loaded_dict
    if len(load_errors) > 0:
        error_messages = "\n".join(load_errors)
        exception_error_message = f"Errors encountered while loading data source:\n{error_messages}"
    else:
        exception_error_message = "Unknown error encountered while loading data source."
    raise InvalidArgumentValueError(exception_error_message,
                                    recommendation="Check the format of data and/or file.")
