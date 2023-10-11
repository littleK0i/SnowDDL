from abc import ABC
from pydantic import BaseModel, ConfigDict


class BaseModelWithConfig(BaseModel, ABC):
    model_config = ConfigDict(
        allow_inf_nan=False,
        arbitrary_types_allowed=True,
        extra="forbid",
        validate_assignment=True,
    )
