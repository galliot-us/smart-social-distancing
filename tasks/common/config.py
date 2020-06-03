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
        },
        'tag_suffixes': {
            constants.D_FRONTEND: '-frontend',
            constants.D_X86: '-x86_64',
            constants.D_OPENVINO: '-x86_64_openvino',
            constants.D_CORAL_DEV_BORAD: '-coral-dev-board',
            constants.D_JETSON_NANO: '-jetson-nano',
            constants.D_AMD64_USBTPU: '-amd64',
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
