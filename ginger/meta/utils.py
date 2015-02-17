
import os
from os import path


__all__ = ['create_dir', 'create_dirs', 'create_file']


def create_dir(dir_name):
    try:
        os.makedirs(dir_name)
    except OSError:
        return False
    else:
        return True


def create_dirs(*dir_names):
    return map(create_dir, dir_names)


def create_file(filename, content):
    create_dir(path.dirname(filename))
    if not path.exists(filename) or not open(filename).read().strip():
        with open(filename, "w") as fh:
            fh.write(content)
        return True
    else:
        return False
    return filename

