#!/usr/bin/env python3
"""Rebind the bundled writable-store seed to the replacement guest image.

The stock metadata.sqlite records the Android 13 tree identity and a frozen
launch contract. With a different system.erofs the runtime rejects the store
with errno=22 ("system image is not the one this store was made for").

Usage: patch_store.py APP_DIR TREE_SHA256
"""
import json
import os
import sqlite3
import sys
import uuid


def main(app, tree):
    db = os.path.join(app, 'rom', 'metadata.sqlite')
    with open(os.path.join(app, 'rom', 'launch.json')) as f:
        launch = json.load(f)

    con = sqlite3.connect(db)
    con.execute("UPDATE properties SET value=? WHERE key='tree'", (tree,))
    con.execute("UPDATE properties SET value=? WHERE key='launch'",
                (json.dumps(launch, separators=(',', ':')),))
    con.execute("UPDATE properties SET value=? WHERE key='instance'", (str(uuid.uuid4()),))
    con.commit()
    con.close()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
