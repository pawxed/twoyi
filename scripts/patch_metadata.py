#!/usr/bin/env python3
"""Point a stock Twoyi IPA at the replacement Android 8.1 rootfs.

Usage: patch_metadata.py APP_DIR TREE_SHA256
Mutates the small JSON files in Payload/Twoyi.app; the EROFS image itself is
built by the workflow. AOT is disabled: the shipped AOT units were translated
from Android 13 code and cannot describe an 8.1 rootfs.
"""
import hashlib
import json
import os
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main(app, tree):
    rom = os.path.join(app, 'rom')
    image = os.path.join(rom, 'system.erofs')
    image_sha, image_bytes = sha256_file(image), os.path.getsize(image)

    launch = load(os.path.join(rom, 'launch.json'))
    launch['rootfs_tree_sha256'] = tree
    save(os.path.join(rom, 'launch.json'), launch)

    lock = load(os.path.join(rom, 'baseline.lock.json'))
    lock['schema'] = 2
    lock['android_tag'] = 'android-8.1.0'
    lock['variant'] = 'twoyi-8.1.0'
    lock['logical_tree_sha256'] = tree
    lock['rootfs_archive'] = {'name': 'twoyi-8.1.0/rootfs.tar', 'sha256': tree,
                              'bytes': image_bytes}
    lock['build'] = {'batch': 'twoyi-8.1.0 (Android 8.1 rootfs from twoyi 0.5.4)',
                     'build_config_commit': 'local', 'frameworks_base': 'local',
                     'system_core': 'local', 'twoyi_launcher': 'local'}
    save(os.path.join(rom, 'baseline.lock.json'), lock)
    save(os.path.join(app, 'baseline.lock.json'), lock)

    ilock = load(os.path.join(rom, 'image.lock.json'))
    ilock['tree'] = tree
    ilock['name'] = 'twoyi-8.1.0/system.erofs'
    ilock['sha256'] = image_sha
    ilock['bytes'] = image_bytes
    save(os.path.join(rom, 'image.lock.json'), ilock)

    runtime = load(os.path.join(app, 'runtime-build.json'))
    runtime['aot'] = False
    runtime['default_aot'] = False
    runtime['default_engine'] = 'step'
    runtime['engines'] = ['step']
    runtime['translation_index'] = False
    save(os.path.join(app, 'runtime-build.json'), runtime)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
