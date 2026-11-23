#!/usr/bin/env python3
"""Build a twoyi.rootfs.v1 manifest from an extracted Android rootfs.

Usage: make_manifest.py ROOT_DIR OUT.json
Prints the tree hash to stdout so callers can patch the launch contract.
"""
import hashlib
import json
import os
import stat
import sys


def sha256_file(path):
    h = hashlib.sha256()
    mode = os.stat(path).st_mode
    try:
        f = open(path, 'rb')
    except PermissionError:
        os.chmod(path, mode | stat.S_IRUSR)
        f = open(path, 'rb')
    with f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main(root, out):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # os.walk lists symlinks-to-directories in dirnames; handle them as links.
        for name in list(dirnames):
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                dirnames.remove(name)
                filenames.append(name)
        for name in sorted(dirnames + filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if rel == '.':
                continue
            st = os.lstat(p)
            mode = oct(stat.S_IMODE(st.st_mode))[2:].zfill(4)
            # Extraction by an unprivileged CI user loses ownership; an Android
            # rootfs is root-owned regardless of who unpacked the archive.
            e = {'path': rel, 'mode': mode, 'uid': 0, 'gid': 0}
            if stat.S_ISLNK(st.st_mode):
                e.update(type='symlink', target=os.readlink(p))
            elif stat.S_ISDIR(st.st_mode):
                e['type'] = 'directory'
            elif stat.S_ISCHR(st.st_mode):
                e.update(type='char_device', major=os.major(st.st_rdev), minor=os.minor(st.st_rdev))
            elif stat.S_ISREG(st.st_mode):
                e.update(type='file', bytes=st.st_size, sha256=sha256_file(p))
            else:
                continue
            entries.append(e)

    entries.sort(key=lambda e: e['path'])
    # Deterministic logical-tree digest. All in-app metadata is patched to this
    # value by patch_metadata.py, so the pair stays self-consistent.
    h = hashlib.sha256()
    for e in entries:
        payload = '\0'.join(str(e.get(k, '')) for k in
                           ('path', 'type', 'mode', 'uid', 'gid', 'bytes', 'target', 'sha256'))
        h.update(payload.encode() + b'\n')
    tree = h.hexdigest()

    manifest = {
        'schema': 'twoyi.rootfs.v1',
        'metadata_policy': {'hardlinks': 'reject', 'xattrs': 'reject',
                            'capabilities': 'reject', 'selinux_labels': 'reject'},
        'tree_sha256': tree,
        'entries': entries,
    }
    with open(out, 'w') as f:
        json.dump(manifest, f, indent=1)
        f.write('\n')
    print(tree)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
