def get_area_config_directory(config):
    return f"{config.get_section_dict('App')['EntityConfigDirectory']}/areas"


def get_source_config_directory(config):
    return f"{config.get_section_dict('App')['EntityConfigDirectory']}/sources"
