import os

import yaml


def load_yaml_from_file(path):
    if path is None or not os.path.isfile(path):
        raise Exception('Should specify an existing file with a spec, given "%s"' % path)

    with open(path, 'rt', encoding='utf-8') as f:
        yaml_data = f.read()

    return load_yaml_from_data(yaml_data)


def load_yaml_from_data(data):
    try:
        return yaml.load(data)
    except Exception as e:
        raise Exception('This is not a valid object specification:\n%s' % str(e))
