from azure.mgmt.cdn.models import (
    RuleIsCompressionEnabled, RequestMethodOperator
)
from msrestazure.tools import is_valid_resource_id
from azure.cli.core.aaz._base import has_value

def create_condition(match_variable, operator, match_values=None, selector=None, negate_condition=None, transforms=None):
    if match_variable == 'RemoteAddress':
        condition = {
            "remote_address": {
                "parameters": {
                    "type_name": "DeliveryRuleRemoteAddressConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'RequestMethod':
        condition = {
            "request_method": {
                "parameters": {
                    "type_name": "DeliveryRuleRequestMethodConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": RequestMethodOperator.EQUAL
                    }
                }
            }
    if match_variable == 'QueryString':
        condition = {
            "query_string": {
                "parameters": {
                    "type_name": "DeliveryRuleQueryStringConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'PostArgs':
        condition = {
            "post_args": {
                "parameters": {
                    "type_name": "DeliveryRulePostArgsConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms,
                    "selector": selector
                    }
                }
            }
    if match_variable == 'RequestHeader':
        condition = {
            "request_header": {
                "parameters": {
                    "type_name": "DeliveryRuleRequestHeaderConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms,
                    "selector": selector
                    }
                }
            }
    if match_variable == 'RequestUri':
        condition = {
            "request_uri": {
                "parameters": {
                    "type_name": "DeliveryRuleRequestUriConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'RequestBody':
        condition = {
            "request_body": {
                "parameters": {
                    "type_name": "DeliveryRuleRequestBodyConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'RequestScheme':
        condition = {
            "request_scheme": {
                "parameters": {
                    "type_name": "DeliveryRuleRequestSchemeConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": RequestMethodOperator.EQUAL
                    }
                }
            }
    if match_variable == 'UrlPath':
        condition = {
            "url_path": {
                "parameters": {
                    "type_name": "DeliveryRuleUrlPathMatchConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'UrlFileExtension':
        condition = {
            "url_file_extension": {
                "parameters": {
                    "type_name": "DeliveryRuleUrlFileExtensionMatchConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'UrlFileName':
        condition = {
            "url_file_name": {
                "parameters": {
                    "type_name": "DeliveryRuleUrlFilenameConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'HttpVersion':
        condition = {
            "http_version": {
                "parameters": {
                    "type_name": "DeliveryRuleHttpVersionConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator
                    }
                }
            }
    if match_variable == 'IsDevice':
        condition = {
            "is_device": {
                "parameters": {
                    "type_name": "DeliveryRuleIsDeviceConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'Cookies':
        condition = {
            "cookies": {
                "parameters": {
                    "type_name": "DeliveryRuleCookiesConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms,
                    "selector": selector
                    }
                }
            }
    if match_variable == 'SocketAddr':
        condition = {
            "socket_addr": {
                "parameters": {
                    "type_name": "DeliveryRuleSocketAddrConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'ClientPort':
        condition = {
            "client_port": {
                "parameters": {
                    "type_name": "DeliveryRuleClientPortConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'ServerPort':
        condition = {
            "server_port": {
                "parameters": {
                    "type_name": "DeliveryRuleServerPortConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'HostName':
        condition = {
            "host_name": {
                "parameters": {
                    "type_name": "DeliveryRuleHostNameConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms
                    }
                }
            }
    if match_variable == 'SslProtocol':
        condition = {
            "ssl_protocol": {
                "parameters": {
                    "type_name": "DeliveryRuleSslProtocolConditionParameters",
                    "match_values": match_values,
                    "negate_condition": negate_condition,
                    "operator": operator,
                    "transforms": transforms,
                    }
                }
            }
    return condition

def create_action(action_name, cache_behavior=None, cache_duration=None, header_action=None,
                  header_name=None, header_value=None, query_string_behavior=None, query_parameters=None,
                  redirect_type=None, redirect_protocol=None, custom_hostname=None, custom_path=None,
                  custom_querystring=None, custom_fragment=None, source_pattern=None, destination=None,
                  preserve_unmatched_path=None, sub_id=None, resource_group_name=None, profile_name=None,
                  endpoint_name=None, origin_group=None, query_string_caching_behavior=None,
                  enable_compression=None, enable_caching=None, forwarding_protocol=None):
    if action_name == "CacheExpiration":
        action = {
            "cache_expiration" : {
                "parameters": {
                    "type_name": "DeliveryRuleCacheExpirationActionParameters",
                    "cache_behavior": cache_behavior,
                    "cache_duration": cache_duration
                }
            }
        }
        return action
    if action_name in ('RequestHeader', 'ModifyRequestHeader'):
        action = {
            "modify_request_header": {
                "parameters": {
                    "type_name": "DeliveryRuleHeaderActionParameters",
                    "header_action": header_action,
                    "header_name": header_name,
                    "value": header_value
                }
            }
        }
        return action
    if action_name in ('ResponseHeader', 'ModifyResponseHeader'):
        action = {
            "modify_response_header": {
                "parameters": {
                    "type_name": "DeliveryRuleHeaderActionParameters",
                    "header_action": header_action,
                    "header_name": header_name,
                    "value": header_value
                }
            }
        }
        return action
    if action_name == "CacheKeyQueryString":
        action = {
            "cache_key_query_string": {
                "parameters": {
                    "type_name" "DeliveryRuleCacheKeyQueryStringBehaviorActionParameters"
                    "query_string_behavior": query_string_behavior,
                    "query_parameters": query_parameters
                }
            }
        }
        return action
    if action_name == "UrlRedirect":
        action = {
            "url_redirect": {
                "parameters": {
                    "type_name": "DeliveryRuleUrlRedirectActionParameters",
                    "custom_fragment": custom_fragment,
                    "custom_hostname": custom_hostname,
                    "custom_path": custom_path,
                    "custom_querystring": custom_querystring,
                    "destination_protocol": redirect_protocol,
                    "redirect_type": redirect_type
                }
            }
        }
        return action
    if action_name == "UrlRewrite":
        action = {
            "url_rewrite": {
                "parameters": {
                    "type_name": "DeliveryRuleUrlRewriteActionParameters",
                    "destination": destination,
                    "preserve_unmatched_path": preserve_unmatched_path,
                    "source_pattern": source_pattern
                }
            }
        }
        return action
    if action_name == "OriginGroupOverride":
        if not is_valid_resource_id(origin_group):
            # Ideally we should use resource_id but Auzre FrontDoor portal extension has some case-sensitive issues
            # that prevent it from displaying correctly in portal.
            origin_group = f'/subscriptions/{sub_id}/resourcegroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/endpoints/{endpoint_name}' \
                           f'/origingroups/{origin_group}'
            
        action = {
            "origin_group_override": {
                "parameters": {
                    "type_name": "DeliveryRuleOriginGroupOverrideActionParameters",
                    "origin_group": {
                        "id": origin_group
                    }
                }
            }
        }
        return action
    if action_name == "RouteConfigurationOverride":
        origin_group_override = None
        if has_value(origin_group):
            if is_valid_resource_id(origin_group.to_serialized_data()):
                origin_group_override = {
                    "origin_group": {
                        "id": origin_group
                    },
                    "forwarding_protocol": forwarding_protocol
                }
            else:
                origin_group_refernce = f'/subscriptions/{sub_id}/resourcegroups/' \
                                        f'{resource_group_name}/providers/Microsoft.Cdn/profiles/{profile_name}/' \
                                        f'origingroups/{origin_group}'
                origin_group_override = {
                    "origin_group": {
                        "id": origin_group_refernce
                    },
                    "forwarding_protocol": forwarding_protocol
                }
            
        action = {
            "route_configuration_override": {
                "parameters": {
                    "type_name": "DeliveryRuleRouteConfigurationOverrideActionParameters",
                    "origin_group_override": origin_group_override,
                    "cache_configuration": {
                        "query_string_caching_behavior": query_string_caching_behavior,
                        "query_parameters": query_parameters,
                        "cache_behavior": cache_behavior,
                        "cache_duration": cache_duration,
                        "is_compression_enabled": RuleIsCompressionEnabled.ENABLED.value if enable_compression else RuleIsCompressionEnabled.DISABLED.value
                        } if enable_caching else None
                    },
                }
            }
        return action