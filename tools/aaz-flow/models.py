from dataclasses import dataclass

@dataclass
class AAZRequest:
    extension_or_module_name: str
    swagger_module_path: str
    resource_provider: str
    swagger_tag: str
