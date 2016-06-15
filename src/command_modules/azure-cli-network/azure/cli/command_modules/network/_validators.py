def _process_nic_namespace(namespace):
    namespace.network_security_group_type = 'existing' \
        if namespace.network_security_group_name else 'none'
