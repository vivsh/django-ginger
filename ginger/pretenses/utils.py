
import os
from os import path


__all__ = ['collect_files']


def collect_files(folders, extensions=None):
    _images = []
    if not isinstance(folders, (tuple, list)):
        folders = (folders, )
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for f in files:
                _, ext = path.splitext(f)
                ext = ext.strip(".").lower()
                if extensions is None or ext in extensions:
                    filename = path.join(root, f)
                    _images.append(filename)
    return _images