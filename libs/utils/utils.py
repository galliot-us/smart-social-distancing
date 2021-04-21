import os
from pathlib import Path

BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                  '0': False, 'no': False, 'false': False, 'off': False}


def validate_file_exists_and_is_not_empty(file_path):
    if os.path.exists(file_path) \
       and Path(file_path).is_file() \
       and Path(file_path).stat().st_size != 0:
        return True
    else:
        return False


def is_list_recursively_empty(lst):
    return all(is_list_recursively_empty(i) if isinstance(i, list) else False for i in lst)


def config_to_boolean(value):
    if isinstance(value, bool):
        return value
    if value.lower() not in BOOLEAN_STATES:
        raise ValueError("Invalid boolean value")
    return BOOLEAN_STATES[value.lower()]
