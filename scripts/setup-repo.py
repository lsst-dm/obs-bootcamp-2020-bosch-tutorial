#!/usr/bin/env python

from  lsst.daf.butler import Butler, CollectionType
import shutil
import os

for filename in ("butler.yaml", "gen3.sqlite3"):
    if os.path.exists(os.path.join("DATA", filename)):
        os.remove(os.path.join("DATA", filename))

Butler.makeRepo("DATA")
butler = Butler("DATA", writeable=True)
butler.import_(filename="DATA/ci_hsc.yaml", transfer=None)
butler.registry.registerCollection("HSC/defaults", type=CollectionType.CHAINED)
butler.registry.setCollectionChain(
    "HSC/defaults",
    [
        "HSC/raw/all",
        "HSC/calib",
        "HSC/masks",
        "refcats",
        "skymaps"
    ]
)
