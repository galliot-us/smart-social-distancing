from pydantic import BaseSettings
from libs.config_engine import ConfigEngine


class Settings:
    instance = None

    class __Settings(BaseSettings):
        config: ConfigEngine = None

    def __init__(self, config: ConfigEngine = None):
        if not Settings.instance:
            if not config:
                raise RuntimeError("Settings can not be initied without config")
            Settings.instance = Settings.__Settings(config=config)
        elif config:
            # Config file was updated.
            Settings.instance.config = config

    def __getattr__(self, name):
        return getattr(self.instance, name)
