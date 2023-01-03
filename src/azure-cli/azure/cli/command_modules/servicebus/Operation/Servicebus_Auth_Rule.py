def cli_namespaceautho_create(cmd, client, resource_group_name, namespace_name, name, rights=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        from azure.cli.command_modules.servicebus._utils import accessrights_converter
        return client.create_or_update_authorization_rule(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            authorization_rule_name=name,
            parameters={'rights': accessrights_converter(rights)})


# Namespace Authorization rule:
def cli_namespaceautho_update(cmd, instance, rights):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        from azure.cli.command_modules.servicebus._utils import accessrights_converter
        instance.rights = accessrights_converter(rights)
        return instance


def cli_keys_renew(client, resource_group_name, namespace_name, name, key_type, key=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.authorization_rule import Regenerate_key

    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type, 'key': key}
    )
