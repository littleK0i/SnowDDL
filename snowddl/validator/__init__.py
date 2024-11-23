from .abc_validator import AbstractValidator
from .user import UserValidator

default_validate_sequence = [
    UserValidator
]