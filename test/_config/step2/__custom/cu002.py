from snowddl import SnowDDLConfig, TableBlueprint


def handler(config: SnowDDLConfig):
    for full_name, bp in config.get_blueprints_by_type_and_pattern(TableBlueprint, "db1.sc1.cu002*").items():
        config.remove_blueprint(bp)
