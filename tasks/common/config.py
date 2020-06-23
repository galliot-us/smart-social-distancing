"""
In order to invoke tasks, you should have `tasks/overrides.yaml` config file. For taking a look at available
configurable items and their default values, see `tasks/common/config.py`. You can start with editing this
template (don't forget to substitute `<YOUR_DOCKERHUB_USER_NAME>` with your dockerhub username in it):
```bash
cp tasks/overrides.yaml.template tasks/overrides.yaml
# now edit tasks/overrides.yaml. This file is in .gitignore
```
"""
from pathlib import Path
from . import constants

defaults = {
    'develop': {
        'host_username': NotImplemented,
        'host_ports': {
            'backend': 8000,
        },
    },
    'run': {
        # http://www.pyinvoke.org/faq.html#why-is-my-command-behaving-differently-under-invoke-versus-being-run-by-hand
        'pty': True,
    },
    'docker': {
        'image_name': 'neuralet/smart-social-distancing',
        'private_image_name': NotImplemented,
        'dockerfiles': {
            constants.D_FRONTEND: 'frontend.Dockerfile',
            constants.D_X86: 'x86.Dockerfile',
            constants.D_OPENVINO: 'x86-openvino.Dockerfile',
            constants.D_CORAL_DEV_BORAD: 'coral-dev-board.Dockerfile',
            constants.D_JETSON_NANO: 'jetson-nano.Dockerfile',
            constants.D_AMD64_USBTPU: 'amd64-usbtpu.Dockerfile',
            constants.D_JETSON_TX2: 'jetson-tx2.Dockerfile',
        },
        'tag_suffixes': {
            constants.D_FRONTEND: '-frontend',
            constants.D_X86: '-x86_64',
            constants.D_OPENVINO: '-x86_64_openvino',
            constants.D_CORAL_DEV_BORAD: '-coral-dev-board',
            constants.D_JETSON_NANO: '-jetson-nano',
            constants.D_AMD64_USBTPU: '-amd64',
            constants.D_JETSON_TX2: '-jetson-tx2',
        },
        'default_host': {
            constants.D_FRONTEND: 'gpu',
            constants.D_X86: 'gpu',
            constants.D_OPENVINO: 'gpu',
            constants.D_CORAL_DEV_BORAD: 'tpu',
            constants.D_JETSON_NANO: 'jetson',
            constants.D_AMD64_USBTPU: 'gpu'

        },
        'custom_targets': {},
        'custom_runtimes': {
            constants.D_JETSON_NANO: 'nvidia',
        },
    },
}


def get_config(c, key_path):
    config = c.config
    keys = key_path.split('.')
    for key in keys:
        config = config[key]
    if config is NotImplemented:
        config_file = Path('tasks/overrides.yaml')
        config_path = str(config_file.absolute())
        if not config_file.exists():
            c.run(f'touch {config_path}')
        raise RuntimeError(f"Please configure '{key_path}' in file: {config_path}")
    return config
