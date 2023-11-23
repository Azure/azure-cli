from azure.mgmt.cdn.models import (
    RuleIsCompressionEnabled, RequestMethodOperator
)

def create_condition(match_variable, operator, match_values=None, selector=None, negate_condition=None, transforms=None):
    from azure.cli.core.aaz import AAZObjectArg, AAZListArg, AAZBoolArg, AAZStrArg
    condition = AAZObjectArg()
    if match_variable == 'RemoteAddress':
        condition.remote_address = AAZObjectArg()
        condition.remote_address.parameters = AAZObjectArg()
        condition.remote_address.parameters.match_values = AAZListArg()
        condition.remote_address.parameters.match_values.Element= AAZStrArg()
        condition.remote_address.parameters.negate_condition = AAZBoolArg()
        condition.remote_address.parameters.operator = AAZStrArg()
        condition.remote_address.parameters.transforms = AAZListArg()
        condition.remote_address.parameters.transforms.Element= AAZStrArg()
        condition.remote_address.parameters.match_values = match_values
        condition.remote_address.parameters.negate_condition = negate_condition
        condition.remote_address.parameters.operator = operator
        condition.remote_address.parameters.transforms = transforms
    if match_variable == 'RequestMethod':
        condition.request_method = AAZObjectArg()
        condition.request_method.parameters = AAZObjectArg()
        condition.request_method.parameters.match_values = AAZListArg()
        condition.request_method.parameters.match_values.Element= AAZStrArg()
        condition.request_method.parameters.negate_condition = AAZBoolArg()
        condition.request_method.parameters.operator = AAZStrArg()
        condition.request_method.parameters.match_values = match_values
        condition.request_method.parameters.negate_condition = negate_condition
        condition.request_method.parameters.operator = RequestMethodOperator.EQUAL
    if match_variable == 'QueryString':
        condition.query_string = AAZObjectArg()
        condition.query_string.parameters = AAZObjectArg()
        condition.query_string.parameters.match_values = AAZListArg()
        condition.query_string.parameters.match_values.Element= AAZStrArg()
        condition.query_string.parameters.negate_condition = AAZBoolArg()
        condition.query_string.parameters.operator = AAZStrArg()
        condition.query_string.parameters.transforms = AAZListArg()
        condition.query_string.parameters.transforms.Element= AAZStrArg()
        condition.query_string.parameters.match_values = match_values
        condition.query_string.parameters.negate_condition = negate_condition
        condition.query_string.parameters.operator = operator
        condition.query_string.parameters.transforms = transforms
    if match_variable == 'PostArgs':
        condition.post_args = AAZObjectArg()
        condition.post_args.parameters = AAZObjectArg()
        condition.post_args.parameters.match_values = AAZListArg()
        condition.post_args.parameters.match_values.Element= AAZStrArg()
        condition.post_args.parameters.negate_condition = AAZBoolArg()
        condition.post_args.parameters.operator = AAZStrArg()
        condition.post_args.parameters.transforms = AAZListArg()
        condition.post_args.parameters.transforms.Element= AAZStrArg()
        condition.post_args.parameters.selector = AAZStrArg()
        condition.post_args.parameters.match_values = match_values
        condition.post_args.parameters.negate_condition = negate_condition
        condition.post_args.parameters.operator = operator
        condition.post_args.parameters.transforms = transforms
        condition.post_args.parameters.selector = selector
    if match_variable == 'RequestHeader':
        condition.request_header = AAZObjectArg()
        condition.request_header.parameters = AAZObjectArg()
        condition.request_header.parameters.match_values = AAZListArg()
        condition.request_header.parameters.match_values.Element= AAZStrArg()
        condition.request_header.parameters.negate_condition = AAZBoolArg()
        condition.request_header.parameters.operator = AAZStrArg()
        condition.request_header.parameters.transforms = AAZListArg()
        condition.request_header.parameters.transforms.Element= AAZStrArg()
        condition.request_header.parameters.selector = AAZStrArg()
        condition.request_header.parameters.match_values = match_values
        condition.request_header.parameters.negate_condition = negate_condition
        condition.request_header.parameters.operator = operator
        condition.request_header.parameters.transforms = transforms
        condition.request_header.parameters.selector = selector
    if match_variable == 'RequestUri':
        condition.request_uri = AAZObjectArg()
        condition.request_uri.parameters = AAZObjectArg()
        condition.request_uri.parameters.match_values = AAZListArg()
        condition.request_uri.parameters.match_values.Element= AAZStrArg()
        condition.request_uri.parameters.negate_condition = AAZBoolArg()
        condition.request_uri.parameters.operator = AAZStrArg()
        condition.request_uri.parameters.transforms = AAZListArg()
        condition.request_uri.parameters.transforms.Element= AAZStrArg()
        condition.request_uri.parameters.match_values = match_values
        condition.request_uri.parameters.negate_condition = negate_condition
        condition.request_uri.parameters.operator = operator
        condition.request_uri.parameters.transforms = transforms
    if match_variable == 'RequestBody':
        condition.request_body = AAZObjectArg()
        condition.request_body.parameters = AAZObjectArg()
        condition.request_body.parameters.match_values = AAZListArg()
        condition.request_body.parameters.match_values.Element= AAZStrArg()
        condition.request_body.parameters.negate_condition = AAZBoolArg()
        condition.request_body.parameters.operator = AAZStrArg()
        condition.request_body.parameters.transforms = AAZListArg()
        condition.request_body.parameters.transforms.Element= AAZStrArg()
        condition.request_body.parameters.match_values = match_values
        condition.request_body.parameters.negate_condition = negate_condition
        condition.request_body.parameters.operator = operator
        condition.request_body.parameters.transforms = transforms
    if match_variable == 'RequestScheme':
        condition.request_scheme = AAZObjectArg()   
        condition.request_scheme.parameters = AAZObjectArg()
        condition.request_scheme.parameters.match_values = AAZListArg()
        condition.request_scheme.parameters.match_values = AAZStrArg()
        condition.request_scheme.parameters.negate_condition = AAZBoolArg()
        condition.request_scheme.parameters.operator = AAZStrArg()
        condition.request_scheme.parameters.match_values = match_values
        condition.request_scheme.parameters.negate_condition = negate_condition
        condition.request_scheme.parameters.operator = RequestMethodOperator.EQUAL
    if match_variable == 'UrlPath':
        condition.url_path = AAZObjectArg()
        condition.url_path.parameters = AAZObjectArg()
        condition.url_path.parameters.match_values = AAZListArg(      )
        condition.url_path.parameters.match_values.Element= AAZStrArg()
        condition.url_path.parameters.negate_condition = AAZBoolArg()
        condition.url_path.parameters.operator = AAZStrArg()
        condition.url_path.parameters.transforms = AAZListArg()
        condition.url_path.parameters.transforms.Element= AAZStrArg()
        condition.url_path.parameters.match_values = match_values
        condition.url_path.parameters.negate_condition = negate_condition
        condition.url_path.parameters.operator = operator
        condition.url_path.parameters.transforms = transforms
    if match_variable == 'UrlFileExtension':
        condition.url_file_extension = AAZObjectArg()
        condition.url_file_extension.parameters = AAZObjectArg()
        condition.url_file_extension.parameters.match_values = AAZListArg()
        condition.url_file_extension.parameters.match_values.Element= AAZStrArg()
        condition.url_file_extension.parameters.negate_condition = AAZBoolArg()
        condition.url_file_extension.parameters.operator = AAZStrArg()
        condition.url_file_extension.parameters.transforms = AAZListArg()
        condition.url_file_extension.parameters.transforms.Element= AAZStrArg()
        condition.url_file_extension.parameters.match_values = match_values
        condition.url_file_extension.parameters.negate_condition = negate_condition
        condition.url_file_extension.parameters.operator = operator
        condition.url_file_extension.parameters.transforms = transforms
    if match_variable == 'UrlFileName':
        condition.url_file_name = AAZObjectArg()
        condition.url_file_name.parameters = AAZObjectArg()
        condition.url_file_name.parameters.match_values = AAZListArg()
        condition.url_file_name.parameters.match_values.Element= AAZStrArg()
        condition.url_file_name.parameters.negate_condition = AAZBoolArg(   )
        condition.url_file_name.parameters.operator = AAZStrArg()
        condition.url_file_name.parameters.transforms = AAZListArg()
        condition.url_file_name.parameters.transforms.Element= AAZStrArg()
        condition.url_file_name.parameters.match_values = match_values
        condition.url_file_name.parameters.negate_condition = negate_condition
        condition.url_file_name.parameters.operator = operator
        condition.url_file_name.parameters.transforms = transforms
    if match_variable == 'HttpVersion':
        condition.http_version = AAZObjectArg()
        condition.http_version.parameters = AAZObjectArg()
        condition.http_version.parameters.match_values = AAZListArg()
        condition.http_version.parameters.match_values.Element= AAZStrArg()
        condition.http_version.parameters.negate_condition = AAZBoolArg()
        condition.http_version.parameters.operator = AAZStrArg()
        condition.http_version.parameters.transforms = AAZListArg()
        condition.http_version.parameters.transforms.Element= AAZStrArg()
        condition.http_version.parameters.match_values = match_values
        condition.http_version.parameters.negate_condition = negate_condition
        condition.http_version.parameters.operator = operator
        condition.http_version.parameters.transforms = transforms
    if match_variable == 'IsDevice':
        condition.is_device = AAZObjectArg()
        condition.is_device.parameters = AAZObjectArg()
        condition.is_device.parameters.match_values = AAZListArg()
        condition.is_device.parameters.match_values.Element= AAZStrArg()
        condition.is_device.parameters.negate_condition = AAZBoolArg()
        condition.is_device.parameters.operator = AAZStrArg()
        condition.is_device.parameters.transforms = AAZListArg()
        condition.is_device.parameters.transforms.Element= AAZStrArg()
        condition.is_device.parameters.match_values = match_values
        condition.is_device.parameters.negate_condition = negate_condition
        condition.is_device.parameters.operator = operator
        condition.is_device.parameters.transforms = transforms
    if match_variable == 'Cookies':
        condition.cookies = AAZObjectArg()
        condition.cookies.parameters = AAZObjectArg()
        condition.cookies.parameters.match_values = AAZListArg()
        condition.cookies.parameters.match_values.Element= AAZStrArg()
        condition.cookies.parameters.negate_condition = AAZBoolArg()
        condition.cookies.parameters.operator = AAZStrArg()
        condition.cookies.parameters.transforms = AAZListArg()
        condition.cookies.parameters.transforms.Element= AAZStrArg()
        condition.cookies.parameters.selector = AAZStrArg()
        condition.cookies.parameters.match_values = match_values
        condition.cookies.parameters.negate_condition = negate_condition
        condition.cookies.parameters.operator = operator
        condition.cookies.parameters.transforms = transforms
        condition.cookies.parameters.selector = selector
    if match_variable == 'SocketAddr':
        condition.socket_addr = AAZObjectArg()
        condition.socket_addr.parameters = AAZObjectArg()
        condition.socket_addr.parameters.match_values = AAZListArg(     )
        condition.socket_addr.parameters.match_values.Element= AAZStrArg()
        condition.socket_addr.parameters.negate_condition = AAZBoolArg()
        condition.socket_addr.parameters.operator = AAZStrArg()
        condition.socket_addr.parameters.transforms = AAZListArg(   )
        condition.socket_addr.parameters.transforms.Element= AAZStrArg()
        condition.socket_addr.parameters.match_values = match_values
        condition.socket_addr.parameters.negate_condition = negate_condition
        condition.socket_addr.parameters.operator = operator
        condition.socket_addr.parameters.transforms = transforms
    if match_variable == 'ClientPort':
        condition.client_port = AAZObjectArg()
        condition.client_port.parameters = AAZObjectArg()
        condition.client_port.parameters.match_values = AAZListArg()
        condition.client_port.parameters.match_values.Element= AAZStrArg()
        condition.client_port.parameters.negate_condition = AAZBoolArg()
        condition.client_port.parameters.operator = AAZStrArg()
        condition.client_port.parameters.transforms = AAZListArg()
        condition.client_port.parameters.transforms.Element= AAZStrArg()
        condition.client_port.parameters.match_values = match_values
        condition.client_port.parameters.negate_condition = negate_condition
        condition.client_port.parameters.operator = operator
        condition.client_port.parameters.transforms = transforms
    if match_variable == 'ServerPort':
        condition.server_port = AAZObjectArg()
        condition.server_port.parameters = AAZObjectArg()
        condition.server_port.parameters.match_values = AAZListArg()
        condition.server_port.parameters.match_values.Element= AAZStrArg()
        condition.server_port.parameters.negate_condition = AAZBoolArg(  )
        condition.server_port.parameters.operator = AAZStrArg()
        condition.server_port.parameters.transforms = AAZListArg()
        condition.server_port.parameters.transforms.Element= AAZStrArg()
        condition.server_port.parameters.match_values = match_values
        condition.server_port.parameters.negate_condition = negate_condition
        condition.server_port.parameters.operator = operator
        condition.server_port.parameters.transforms = transforms
    if match_variable == 'HostName':
        condition.host_name = AAZObjectArg()
        condition.host_name.parameters = AAZObjectArg()
        condition.host_name.parameters.match_values = AAZListArg(   )
        condition.host_name.parameters.match_values.Element= AAZStrArg()
        condition.host_name.parameters.negate_condition = AAZBoolArg()
        condition.host_name.parameters.operator = AAZStrArg(        )
        condition.host_name.parameters.transforms = AAZListArg()
        condition.host_name.parameters.transforms.Element= AAZStrArg()
        condition.host_name.parameters.match_values = match_values
        condition.host_name.parameters.negate_condition = negate_condition
        condition.host_name.parameters.operator = operator
        condition.host_name.parameters.transforms = transforms
    if match_variable == 'SslProtocol':
        condition.ssl_protocol = AAZObjectArg()
        condition.ssl_protocol.parameters = AAZObjectArg()
        condition.ssl_protocol.parameters.match_values = AAZListArg()
        condition.ssl_protocol.parameters.match_values.Element= AAZStrArg()
        condition.ssl_protocol.parameters.negate_condition = AAZBoolArg()
        condition.ssl_protocol.parameters.operator = AAZStrArg()
        condition.ssl_protocol.parameters.transforms = AAZListArg()
        condition.ssl_protocol.parameters.transforms.Element= AAZStrArg()
        condition.ssl_protocol.parameters.match_values = match_values
        condition.ssl_protocol.parameters.negate_condition = negate_condition
        condition.ssl_protocol.parameters.operator = operator
        condition.ssl_protocol.parameters.transforms = transforms
    return condition

def create_action(action_name, cache_behavior=None, cache_duration=None, header_action=None,
                  header_name=None, header_value=None, query_string_behavior=None, query_parameters=None,
                  redirect_type=None, redirect_protocol=None, custom_hostname=None, custom_path=None,
                  custom_query_string=None, custom_fragment=None, source_pattern=None, destination=None,
                  preserve_unmatched_path=None, cmd=None, resource_group_name=None, profile_name=None,
                  endpoint_name=None, origin_group=None, query_string_caching_behavior=None,
                  is_compression_enabled=None, enable_caching=None, forwarding_protocol=None):
    from azure.cli.core.aaz import AAZObjectArg
    action = AAZObjectArg()
    if action_name == "CacheExpiration":
        action.cache_expiration.parameters.cache_duration = cache_duration
        action.cache_expiration.parameters.cache_behavior = cache_behavior
        return action
    if action_name in ('RequestHeader', 'ModifyRequestHeader'):
        action.modify_request_header.parameters.header_action = header_action
        action.modify_request_header.parameters.header_name = header_name
        action.modify_request_header.parameters.value = header_value
        return action
    if action_name in ('ResponseHeader', 'ModifyResponseHeader'):
        action.modify_response_header.parameters.header_action = header_action
        action.modify_response_header.parameters.header_name = header_name
        action.modify_response_header.parameters.value = header_value
        return action
    if action_name == "CacheKeyQueryString":
        action.cache_key_query_string.parameters.query_string_behavior = query_string_behavior
        action.cache_key_query_string.parameters.query_parameters = query_parameters
        return action
    if action_name == "UrlRedirect":
        action.url_redirect.parameters.custom_host = custom_hostname
        action.url_redirect.parameters.custom_path = custom_path
        action.url_redirect.parameters.custom_query_string = custom_query_string
        action.url_redirect.parameters.custom_fragment = custom_fragment
        action.url_redirect.parameters.destination_protocol = redirect_protocol
        action.url_redirect.parameters.redirect_type = redirect_type
        return action
    if action_name == "UrlRewrite":
        action.url_rewrite.parameters.destination = destination
        action.url_rewrite.parameters.preserve_unmatched_path = preserve_unmatched_path
        action.url_rewrite.parameters.source_pattern = source_pattern
        return action
    if action_name == "OriginGroupOverride":
        if not is_valid_resource_id(origin_group):
            # Ideally we should use resource_id but Auzre FrontDoor portal extension has some case-sensitive issues
            # that prevent it from displaying correctly in portal.
            origin_group = f'/subscriptions/{get_subscription_id(cmd.cli_ctx)}/resourcegroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/endpoints/{endpoint_name}' \
                           f'/origingroups/{origin_group.lower()}'
        action.origin_group_override.parameters.origin_group.id = origin_group
        return action
    if action_name == "RouteConfigurationOverride":
        if not is_valid_resource_id(origin_group):
            # Ideally we should use resource_id but Auzre FrontDoor portal extension has some case-sensitive issues
            # that prevent it from displaying correctly in portal.
            origin_group = f'/subscriptions/{get_subscription_id(cmd.cli_ctx)}/resourcegroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/endpoints/{endpoint_name}' \
                           f'/origingroups/{origin_group.lower()}'
        action.route_configuration_override.parameters.cache_configuration.query_string_caching_behavior = query_string_caching_behavior
        action.route_configuration_override.parameters.cache_configuration.query_parameters = query_parameters
        action.route_configuration_override.parameters.cache_configuration.cache_behavior = cache_behavior
        action.route_configuration_override.parameters.cache_configuration.cache_duration = cache_duration
        action.route_configuration_override.parameters.cache_configuration.is_compression_enable = RuleIsCompressionEnabled.ENABLED.value if is_compression_enabled else RuleIsCompressionEnabled.DISABLED.value,
        action.route_configuration_override.parameters.origin_group_override.forwarding_protocol = forwarding_protocol
        action.route_configuration_override.parameters.origin_group_override.origin_group.id = origin_group
        return action if enable_caching else None
    return action
