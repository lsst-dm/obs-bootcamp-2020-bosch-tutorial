#!/usr/bin/env python

from  lsst.daf.butler import Butler, CollectionType
import shutil
import os

Butler.makeRepo("DATA")
butler = Butler("DATA", writeable=True)
butler.import_(filename="DATA/ci_hsc.yaml", transfer=None)
