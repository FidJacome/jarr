import tomllib

import tomli_w


def set_config(config, *keys, value):
    current_position = config
    for key in keys:
        current_position[key] = keys[i + 1]
        if i == len(keys):
            current_position[keys[i]] = value
        current_position = config[keys[i]]
