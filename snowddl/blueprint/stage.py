from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ident import SchemaObjectIdent


@dataclass
class StageWithPath:
    stage_name: "SchemaObjectIdent"
    path: str


@dataclass
class StageUploadFile:
    local_path: Path
    stage_path: str
