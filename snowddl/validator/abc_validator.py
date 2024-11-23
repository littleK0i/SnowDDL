from abc import ABC, abstractmethod

from snowddl import SnowDDLConfig


class AbstractValidator(ABC):
    def __init__(self, config: SnowDDLConfig):
        self.config = config

    @abstractmethod
    def validate(self):
        pass