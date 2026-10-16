# src/ports/yaml_port.py
from abc import ABC, abstractmethod

class YamlPort(ABC):
    @abstractmethod
    def to_escaped_string(self, yaml_string: str) -> str:
        pass