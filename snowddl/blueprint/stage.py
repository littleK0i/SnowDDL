from pathlib import Path

from .ident import SchemaObjectIdent
from ..model import BaseModelWithConfig


class StageWithPath(BaseModelWithConfig):
    stage_name: SchemaObjectIdent
    path: str


class StageUploadFile(BaseModelWithConfig):
    local_path: Path
    stage_path: str
