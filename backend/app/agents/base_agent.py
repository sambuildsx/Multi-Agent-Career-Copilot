from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run(self, state: dict) -> dict:
        pass
