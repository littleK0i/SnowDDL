from snowddl import SnowDDLConfig, TableBlueprint, IdentPattern


def handler(config: SnowDDLConfig):
    for full_name, bp in config.get_blueprints_by_type_and_pattern(TableBlueprint, IdentPattern("db1.sc1.cu002*")).items():
        config.remove_blueprint(bp)
