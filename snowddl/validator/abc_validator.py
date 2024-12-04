from abc import ABC, abstractmethod
from logging import getLogger, NullHandler
from traceback import TracebackException
from typing import Dict

from snowddl.blueprint import AbstractBlueprint
from snowddl.config import SnowDDLConfig


logger = getLogger(__name__)
logger.addHandler(NullHandler())


class AbstractValidator(ABC):
    def __init__(self, config: SnowDDLConfig):
        self.config = config
        self.env_prefix = config.env_prefix

        self.logger = logger
        self.errors: Dict[str, Exception] = {}

    def validate(self):
        for full_name, bp in self.get_blueprints().items():
            try:
                self.validate_blueprint(bp)
            except Exception as exc:
                traceback = "".join(TracebackException.from_exception(exc).format())
                logger.warning(f"Failed to validate config for [{bp.__class__.__name__}] with name [{full_name}]\n{traceback}")
                self.errors[full_name] = exc

    @abstractmethod
    def validate_blueprint(self, bp: AbstractBlueprint):
        pass

    @abstractmethod
    def get_blueprints(self) -> Dict[str, AbstractBlueprint]:
        pass
