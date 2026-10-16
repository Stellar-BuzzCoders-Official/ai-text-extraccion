from abc import ABC, abstractmethod

class JsonPort(ABC):
    @abstractmethod
    def to_escaped_string(self, json_string: str):
        pass