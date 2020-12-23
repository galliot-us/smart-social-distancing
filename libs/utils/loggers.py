def get_area_log_directory(config):
    loggers_names = [x for x in config.get_sections() if x.startswith("AreaLogger_")]
    for l_name in loggers_names:
        logger_section = config.get_section_dict(l_name)
        if logger_section["Name"] == "file_system_logger":
            return logger_section["LogDirectory"]


def get_source_log_directory(config):
    loggers_names = [x for x in config.get_sections() if x.startswith("SourceLogger_")]
    for l_name in loggers_names:
        logger_section = config.get_section_dict(l_name)
        if logger_section["Name"] == "file_system_logger":
            return logger_section["LogDirectory"]


def get_source_logging_interval(config):
    loggers_names = [x for x in config.get_sections() if x.startswith("SourceLogger_")]
    for l_name in loggers_names:
        logger_section = config.get_section_dict(l_name)
        if logger_section["Name"] == "file_system_logger":
            return float(logger_section["TimeInterval"])


def get_screenshots_directory(config):
    loggers_names = [x for x in config.get_sections() if x.startswith("SourceLogger_")]
    for l_name in loggers_names:
        logger_section = config.get_section_dict(l_name)
        if logger_section["Name"] == "file_system_logger":
            return logger_section["ScreenshotsDirectory"]
