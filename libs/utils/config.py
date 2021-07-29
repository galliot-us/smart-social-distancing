def get_source_config_directory(config):
    return f"{config.get_section_dict('App')['EntityConfigDirectory']}/sources"
