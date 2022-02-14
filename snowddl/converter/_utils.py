from yaml import Dumper, add_representer


class FoldedStr(str):
    pass

class LiteralStr(str):
    pass

def folded_str_presenter(dumper: Dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")

def literal_str_presenter(dumper: Dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

add_representer(FoldedStr, folded_str_presenter)
add_representer(LiteralStr, literal_str_presenter)
