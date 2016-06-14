import argparse

class LBDNSNameAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        dns_value = values

        if dns_value:
            namespace.dns_name_type = 'new'

        namespace.dns_name_for_public_ip = dns_value

class PublicIpDnsNameAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        dns_name = values

        # if dns-name supplied, add the appropriate parameter to the namespace
        if dns_name:
            namespace.public_ip_address_type = 'dns'

        namespace.dns_name = dns_name
