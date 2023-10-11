from pathlib import Path
from yaml import SafeLoader, Node, add_constructor


class SnowDDLLoader(SafeLoader):
    pass


def include_constructor(loader: SnowDDLLoader, node: Node):
    yaml_path = Path(loader.name)

    if not yaml_path.is_file():
        raise ValueError(f"Cannot process !include YAML tag in non-file stream with name [{yaml_path}]")

    include_path = yaml_path.parent / str(node.value)

    if not include_path.is_file():
        raise ValueError(f"File [{include_path}] mentioned in !include YAML tag does not exist")

    if not include_path.is_relative_to(yaml_path.parent):
        raise ValueError(
            f"File [{include_path}] mentioned in !include YAML tag is outside of original YAML file directory [{yaml_path.parent}]"
        )

    return include_path.read_text(encoding="utf-8")


add_constructor("!include", include_constructor, Loader=SnowDDLLoader)
