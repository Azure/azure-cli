#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['network dns record-set create'] = """
            type: command
            parameters:
                - name: --type
                  short-summary: The type of DNS records in the record set.
                - name: --ttl
                  short-summary: Record set TTL (time-to-live).
"""

for t in ['add', 'remove']:
    helps['network dns record aaaa {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --ipv6-address
                      short-summary: IPV6 address in string notation.
    """

    helps['network dns record a {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --ipv4-address
                      short-summary: IPV4 address in string notation.
    """

    helps['network dns record cname {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --cname
                      short-summary: Canonical name.
    """

    helps['network dns record mx {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --exchange
                      short-summary: Exchange metric
                    - name: --preference
                      short-summary: preference metric
    """

    helps['network dns record ns {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --dname
                      short-summary: Name server domain name.
    """

    helps['network dns record ptr {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --dname
                      short-summary: PTR target domain name.
    """

    helps['network dns record soa {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --host
                      short-summary: domain name of the authoritative name server
                    - name: --email
                      short-summary: Email address.
                    - name: --serial-number
                      short-summary: Serial number.
                    - name: --refresh-time
                      short-summary: Refresh value (seconds).
                    - name: --retry-time
                      short-summary: Retry time (seconds).
                    - name: --expire-time
                      short-summary: Expire time (seconds).
                    - name: --minimum-ttl
                      short-summary: Minimum TTL (time-to-live, seconds).
    """

    helps['network dns record srv {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --priority
                      short-summary: Priority metric.
                    - name: --weight
                      short-summary: Weight metric.
                    - name: --port
                      short-summary: Service port.
                    - name: --target
                      short-summary: Target domain name.
    """

    helps['network dns record txt {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --value
                      short-summary: List of text values.
    """

