def get_area_config_directory(config):
    return f"{config.get_sections('App')['EntityConfigDirectory']}/areas"


def get_source_config_directory(config):
    return f"{config.get_sections('App')['EntityConfigDirectory']}/sources"
