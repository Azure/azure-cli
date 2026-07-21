import re
from pycomposefile.compose_element import ComposeElement, ComposeStringOrListElement


class Port(ComposeElement):
    element_keys = {
        "target": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-2"),
        "host_ip": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-2"),
        "published": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-2"),
        "protocol": ((str, ['tcp', 'udp']), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-2"),
        "mode": ((str, ['host', 'ingress']), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-2"),
    }

    def __init__(self, port_definition, key=None, compose_path=""):
        if isinstance(port_definition, str):
            self.parse_string(port_definition)
        else:
            super().__init__(port_definition, compose_path)

    def parse_string(self, port_definition):
        port_matcher = re.compile(r'(?P<HostIp>((\d+\.\d+\.\d+\.\d+:)|))(?P<HostPort>(\d+:)|)(?P<ContainerPort>\d+)(?P<Protocol>((/(tcp|udp))|))')
        matches = port_matcher.search(port_definition)
        host_ip = matches.group('HostIp')
        if host_ip == '':
            host_ip = None
        else:
            host_ip = host_ip.rstrip(":")
        host_port = matches.group('HostPort')
        if host_port == '':
            host_port = None
        else:
            host_port = host_port.rstrip(":")
        container_port = matches.group('ContainerPort')
        protocol = matches.group('Protocol')
        if protocol == '':
            protocol = 'tcp'

        self.__setattr__('host_ip', host_ip)
        self.__setattr__('published', host_port)
        self.__setattr__('target', container_port)
        self.__setattr__('protocol', protocol)
        self.__setattr__('mode', 'host')

    def __str__(self) -> str:
        port = ''
        if self.host_ip is not None:
            port += f"{self.host_ip}:"
        if self.published is not None:
            port += f"{self.published}:"
        port += f"{self.target}/{self.protocol}"
        return port


class Ports(ComposeStringOrListElement):
    transform = Port
