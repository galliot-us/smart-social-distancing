import os
from pathlib import Path
# INVOKE_RUNTIME_CONFIG environment variable should be set before importing invoke
os.environ.setdefault('INVOKE_RUNTIME_CONFIG', str(Path(__file__).parent / 'overrides.yaml'))

from invoke import Collection
from .common.config import defaults
from . import release, develop

ns = Collection()
ns.configure(defaults)
for module in [release, develop]:
    ns.add_collection(Collection.from_module(module))
