#!/usr/bin/env python

import os

from lsst.daf.butler import Butler


def main():
    if "CI_HSC_GEN3_DIR" not in os.environ:
        raise RuntimeError("ci_hsc_gen3 is not setup.")
    repo_root = os.path.join(os.environ["CI_HSC_GEN3_DIR"], "DATA")
    butler = Butler(repo_root)
    os.makedirs("DATA", exist_ok=False)
    with butler.export(directory="DATA", filename="ci_hsc.yaml", transfer="link") as exporter:
        for element in butler.registry.dimensions.getStaticElements():
            if element.hasTable() and element.viewOf is None:
                exporter.saveDimensionData(
                    element,
                    butler.registry.queryDimensionRecords(element),
                )
        for collection in butler.registry.queryCollections(...):
            exporter.saveCollection(collection)
        exporter.saveDatasets(
            butler.registry.queryDatasets(..., collections=...)
        )


if __name__ == "__main__":
    main()
