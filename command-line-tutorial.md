Tutorial: Running `pipetask` and understanding collections
==========================================================

Basic nomenclature
------------------

A "dataset" is best thought of as "mostly like but not necessarily a file", or the persisted form of some arbitrary in-memory Python object.
It's a little dangerous to think of it as _a_ file, because it could be multiple files, or just part of one, or not even backed by a filesystem of any kind, but it's a good starting analogy.
_Don't_ think about a dataset as a large collection of files like "HSC PDR2" - that is _not_ what dataset means in butler, even though it's common usage elsewhere.

A "data ID" is a set of key-value pairs that (partly) identify a dataset.
It's a dict or dict-like object in Python, with keys like "visit" and "band" and values like 903334 and "r".

A "dataset type" is a named definition (e.g. `flat`, `raw`, `src`) that controls what Python type its dataset correspond to, what keys the data IDs have, and a few other things that are out of scope for now.

A "collection" is just a set of datasets.
Collections are defined entirely within a SQL database ("the Registry"), and they come in several types.
Those types all behave more or less the same way for reading datasets - you're not supposed to care most of the time what kind of collection you're reading from - but they're quite different in how they are populated with datasets.

A fundamental organizational principle of the butler is that a dataset type, a data ID with all of the keys for that dataset type, and a collection are sufficient to uniquely identify a dataset.
We'll often search an ordered sequence of collections rather than just one, selecting the dataset from the first one with a match.


Exploring types of collections
------------------------------

If "file" is an okay analogy for "dataset", then "directory" is an okay analogy for "collection" - just be aware that any actual directories you see that seem to correspond to collections are _not_ the source of truth for the contents of those collections.
Different types of collections can be thought of as different kinds of directory contents.

We'll start by querying collections on the repo I've set up.

    $ butler query-collections DATA
    collections:
    - HSC/calib
    - HSC/calib/unbounded
    - HSC/calib/curated/1970-01-01T00:00:00
    - HSC/calib/curated/2013-01-31T00:00:00
    - HSC/calib/curated/2014-04-03T00:00:00
    - HSC/calib/curated/2014-06-01T00:00:00
    - HSC/calib/curated/2015-11-06T00:00:00
    - HSC/calib/curated/2016-04-01T00:00:00
    - HSC/calib/curated/2016-11-22T00:00:00
    - HSC/calib/curated/2016-12-23T00:00:00
    - skymaps
    - HSC/raw/all
    - HSC/calib/gen2/2013-06-17
    - HSC/calib/gen2/2013-11-03
    - HSC/calib/gen2/2014-07-14
    - HSC/calib/gen2/2014-11-12
    - HSC/external
    - HSC/masks
    - refcats
    - shared/ci_hsc_output/20201011T20h12m55s
    - shared/ci_hsc_output
    - HSC/defaults

Some of these hold raws, some hold calibrations, others hold various auxilliary data; they're at slightly self-descriptive.
The shared/ci_hsc_output ones hold processing outputs, but we'll ignore those for now.

Let's focus on `HSC/defaults`, which is a collection I've created for just this repo to hold all of the inputs for the processing we're going to do.
All Gen3 repos should get umbrella collections like this in the not-too-distant future, but we're still working out the details and you won't see them elsewhere yet.

`HSC/defaults` is a `CHAINED`-type collection, which means it's really just an ordered list of other collections to search.
We can expand that list with `--flatten-chains`:

    $ butler query-collections DATA --flatten-chains HSC/defaults
    collections:
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

In our filesytem analogy, a `CHAINED` collection is a directory full of symbolic links to other directories.
`CHAINED` collections can be nested to arbitrary depth (but `--flatten-chains` above flattens those hierarchies out, as the name suggests).

We don't have a great way to directly show the type of a collection from the command-line right now, but you can filter on collection type.
Let's see if the first collection, `HSC/raw/all` is a `RUN`-type collection:

    $ butler query-collections DATA --collection-type RUN HSC/raw/all
    collections:
    - HSC/raw/all

What a lucky guess!

`RUN`-type collections (or just "runs") are the most fundamental type of collection - every dataset is added to exactly one run when it is first added to the data repository, and it remains in that run unless it is deleted entirely.
A dataset can never belong to more than one run, and a run can never be deleted without deleting all of the datasets in it.
So unlike all other types of collections, a dataset's `RUN`-type collection _is_ intrinsic to it, just like its dataset type and data ID.

The filesystem analog for a `RUN` collection is a just directory full of actual "files", with no links of any kind.

We don't actually have an example of a `TAGGED` collection in this repository.
If a `CHAINED` collection is like a directory containing directory symlinks, and a `RUN` collection is like a directory contaiing files, a `TAGGED` collection is like a directory containing file symlinks: each dataset "in" a `TAGGED` collection can be "in" any number of other collections (and always exactly one `RUN`), and the associations are per-dataset.

`HSC/calib` is a `CALIBRATION` collection:

    $ butler query-collections DATA --collection-type CALIBRATION HSC/calib
    collections:
    - HSC/calib

A `CALIBRATION` collection associates each of its datasets with a temporal validity range, so they're actually a slight exception to our fundamental organizing principle - to uniquely identify a dataset within a `CALIBRATION` collection, one needs to provide not just a dataset type and a data ID, but a point or span in time as well.
Usually, this all happens behind the scenes, because the `Registry` database holds knows when observations occurred, and it can automatically join that information to the calibration collection query to associate the `flat`, `bias`, `dark` (etc) datasets in a `CALIBRATION` collection with the `raw` datasets they should be used with.

Just like `TAGGED` collections, datasets in `CALIBRATION` collections can be in other collections, too (and are always in exactly one run).
Our naming conventions makes it fairly clear in this small repository what those contributing runs are:

    $ butler query-collections DATA --collection-type RUN HSC/calib/*
    collections:
    - HSC/calib/unbounded
    - HSC/calib/curated/1970-01-01T00:00:00
    - HSC/calib/curated/2013-01-31T00:00:00
    - HSC/calib/curated/2014-04-03T00:00:00
    - HSC/calib/curated/2014-06-01T00:00:00
    - HSC/calib/curated/2015-11-06T00:00:00
    - HSC/calib/curated/2016-04-01T00:00:00
    - HSC/calib/curated/2016-11-22T00:00:00
    - HSC/calib/curated/2016-12-23T00:00:00
    - HSC/calib/gen2/2013-06-17
    - HSC/calib/gen2/2013-11-03
    - HSC/calib/gen2/2014-07-14
    - HSC/calib/gen2/2014-11-12

It's important to note that this is just a convention, though - there is no collection-level relationship between the `HSC/calib` `CALIBRATION` collection and these `RUN` collections whose names _happen_ to start with `HSC/calib`.
The associations between datasets and `CALIBRATION` collections are - like `TAGGED` collection associations - strictly at the individual-dataset level.

Running pipelines, as simple as possible
----------------------------------------

I've put a little pipeline file in the git repo for this tutorial file, in part to avoid some subject-to-change conventions for how we organize the pipeline definitions across our main software git repos.
It's called "example.yaml", and it runs three single-epoch processing steps (`isr`, `charImage`, and `calibrate`, and then warps images for coaddition `makeWarp`).

Let's kick it off now in the simplest possible way, using that `HSC/defaults` collection as the only input collection:

    $ pipetask run -b DATA -p pipelines/example.yaml -i HSC/defaults -o u/jbosch/bootcamp/1 -d "instrument='HSC' AND visit=903344 AND detector=5"
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 15 quanta for 4 tasks
    conda.common.io INFO: overtaking stderr and stdout
    conda.common.io INFO: stderr and stdout yielding back
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    isr INFO: Converting exposure to floating point values.
    isr INFO: Assembling CCD from amplifiers.
    isr INFO: Applying bias correction.
    isr INFO: Applying linearizer.
    isr INFO: Applying crosstalk correction.
    isr.crosstalk INFO: Applying crosstalk correction.
    isr INFO: Masking defects.
    isr INFO: Masking NAN value pixels.
    isr INFO: Widening saturation trails.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying brighter fatter correction using kernel type <class 'numpy.ndarray'> / gains <class 'NoneType'>.
    isr INFO: Finished brighter fatter correction in 3 iterations.
    isr INFO: Ensuring image edges are masked as SUSPECT to the brighter-fatter kernel size.
    isr INFO: Growing masks to account for brighter-fatter kernel convolution.
    isr INFO: Applying dark correction.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying flat correction.
    isr INFO: Applying fringe correction after flat.
    isr.fringe INFO: Filter not found in FringeTaskConfig.filters. Skipping fringe correction.
    isr INFO: Constructing Vignette polygon.
    isr INFO: Adding transmission curves.
    isr INFO: Set 232863 BAD pixels to 178.167053.
    isr INFO: Interpolating masked pixels.
    isr INFO: Setting rough magnitude zero point: 32.692803
    isr INFO: Measuring background level.
    isr INFO: Flattened sky level: 178.161118 +/- 7.345197.
    isr INFO: Measuring sky levels in 8x16 grids: 177.987633.
    isr INFO: Sky flatness in 8x16 grids - pp: 0.026886 rms: 0.004539.
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 57 cosmic rays.
    characterizeImage.detection INFO: Detected 957 positive peaks in 272 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    ^C
    Aborted!

I've killed it early, because it'll be more interesting to play with partial results than complete ones.
But before we get to that, there's a lot to unpack in that command and those outputs.

First off, I've run this with no parallelization (I could have used `-j4`, just like with `make`, to use all four of my middle-aged laptop's four cores).

There's also a very important first step that happens before any pipeline code is actually run, and you can see when it finishes in this one log message:

    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 326 quanta for 4 tasks

That "QuantumGraph" is a directed-acyclic graph (DAG) that describes all of the processing steps we want to run ("quanta", because from the perspective of the middleware they are the smallest useful unit of processing) and their dependencies via the datasets they produce and consume.
Computing that graph can take a long time on its own for large processing runs, but we're working hard to fix that.
Here it's quite fast, though I noticed a disturbingly long pause between that and the apparent start of execution, and that's something I'll make sure we look into after this week - I suspect it's something looking up all of the versions of all of the Python packages we have installed so we can save them for provenance.

Anyhow, after QuantumGraph generation ("QG gen"), you can see from the log messages that it ran `isr` and then started `characterizeImage` before I killed it.

Let's take a quick look at what the collections in the repo look like now:

    $ butler query-collections DATA
    collections:
    - HSC/calib
    - HSC/calib/unbounded
    - HSC/calib/curated/1970-01-01T00:00:00
    - HSC/calib/curated/2013-01-31T00:00:00
    - HSC/calib/curated/2014-04-03T00:00:00
    - HSC/calib/curated/2014-06-01T00:00:00
    - HSC/calib/curated/2015-11-06T00:00:00
    - HSC/calib/curated/2016-04-01T00:00:00
    - HSC/calib/curated/2016-11-22T00:00:00
    - HSC/calib/curated/2016-12-23T00:00:00
    - skymaps
    - HSC/raw/all
    - HSC/calib/gen2/2013-06-17
    - HSC/calib/gen2/2013-11-03
    - HSC/calib/gen2/2014-07-14
    - HSC/calib/gen2/2014-11-12
    - HSC/external
    - HSC/masks
    - refcats
    - shared/ci_hsc_output/20201011T20h12m55s
    - shared/ci_hsc_output
    - HSC/defaults
    - u/jbosch/bootcamp/1/20201013T14h04m17s
    - u/jbosch/bootcamp/1

We got _two_ new collections at the end there:
 - the one we specified on the command-line, `u/jbosch/bootcamp/1`
 - another one that combines that name with a timestamp: `u/jbosch/bootcamp/1/20201013T12h51m38s`

The first of these is a `CHAINED` collection, and the second is a `RUN`.
The `RUN` contains all of the direct outputs of the processing, while the `CHAINED` collection aggregates those with the inputs:

    $ butler query-collections DATA --flatten-chains u/jbosch/bootcamp/1
    collections:
    - u/jbosch/bootcamp/1/20201013T14h04m17s
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

The outputs are at the top of this list, and that means they're searched first.

We can also look for the datasets directly; I happen to know that the only output dataset type for ISR is `postISRCCD`, so we'll look specifically for that (this sidesteps an issue that should be resolved in the next few weeks):

    $ butler query-datasets DATA postISRCCD --collections u/jbosch/bootcamp/1 --find-first

       type                     run                    id  instrument detector exposure
    ---------- -------------------------------------- ---- ---------- -------- --------
    postISRCCD u/jbosch/bootcamp/1/20201013T14h09m42s 1745        HSC        5   903344

I've used `--find-first` because I only want the first matching dataset for each dataset type and data ID.
That doesn't matter yet, but it will later.

Running pipelines again
-----------------------

Let's imagine now that I killed this job because I realized I forgot to add the `--long-log` option, and try running this again with that:

    $ pipetask run -b DATA -p pipelines/example.yaml -i HSC/defaults -o u/jbosch/bootcamp/1 -d "instrument='HSC' AND visit=903344 AND detector=5"
    Error: An error occurred during command execution:
    Traceback (most recent call last):
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/daf_butler/19.0.0-172-gc4bef2ce+ff10c6d78d/python/lsst/daf/butler/cli/utils.py", line 446, in cli_handle_exception
        return func(*args, **kwargs)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cli/script/qgraph.py", line 133, in qgraph
        qgraph = f.makeGraph(pipelineObj, args)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cmdLineFwk.py", line 555, in makeGraph
        registry, collections, run = _ButlerFactory.makeRegistryAndCollections(args)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cmdLineFwk.py", line 326, in makeRegistryAndCollections
        butler, inputs, self = cls._makeReadParts(args)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cmdLineFwk.py", line 266, in _makeReadParts
        self.check(args)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cmdLineFwk.py", line 228, in check
        raise ValueError("Cannot use --output with existing collection with --inputs.")
    ValueError: Cannot use --output with existing collection with --inputs.

It's not happy, because:
 - the output collection already exists, and it's a `CHAINED` collection that already includes the inputs we passed last time;
 - we also passed inputs this time;
 - it's not smart enough to notice that those inputs are identical.

We've got a ticket to make it smart enough, but note that it will _always_ complain if the inputs have indeed changed.
So, let's try again, this time without the `-i` option:

    $ pipetask --long-log run -b DATA -p pipelines/example.yaml -o u/jbosch/bootcamp/1 -d "instrument='HSC' AND visit=903344 AND detector=5"
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 15 quanta for 4 tasks
    conda.common.io INFO: overtaking stderr and stdout
    conda.common.io INFO: stderr and stdout yielding back
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    isr INFO: Converting exposure to floating point values.
    isr INFO: Assembling CCD from amplifiers.
    isr INFO: Applying bias correction.
    isr INFO: Applying linearizer.
    isr INFO: Applying crosstalk correction.
    isr.crosstalk INFO: Applying crosstalk correction.
    isr INFO: Masking defects.
    isr INFO: Masking NAN value pixels.
    isr INFO: Widening saturation trails.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying brighter fatter correction using kernel type <class 'numpy.ndarray'> / gains <class 'NoneType'>.
    isr INFO: Finished brighter fatter correction in 3 iterations.
    isr INFO: Ensuring image edges are masked as SUSPECT to the brighter-fatter kernel size.
    isr INFO: Growing masks to account for brighter-fatter kernel convolution.
    isr INFO: Applying dark correction.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying flat correction.
    isr INFO: Applying fringe correction after flat.
    isr.fringe INFO: Filter not found in FringeTaskConfig.filters. Skipping fringe correction.
    isr INFO: Constructing Vignette polygon.
    isr INFO: Adding transmission curves.
    isr INFO: Set 232863 BAD pixels to 178.167053.
    isr INFO: Interpolating masked pixels.
    isr INFO: Setting rough magnitude zero point: 32.692803
    isr INFO: Measuring background level.
    isr INFO: Flattened sky level: 178.161118 +/- 7.345197.
    isr INFO: Measuring sky levels in 8x16 grids: 177.987633.
    isr INFO: Sky flatness in 8x16 grids - pp: 0.026886 rms: 0.004539.
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 57 cosmic rays.
    characterizeImage.detection INFO: Detected 957 positive peaks in 272 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    characterizeImage.measurement INFO: Measuring 272 sources (272 parents, 0 children)
    ^C
    Aborted!

It worked!  Except the `--long-log` option didn't do anything.
We've got a ticket for that, too; let's move on.

Let's look at the collections again (I'll start using a glob now to filter out irrelevant ones):

    $ butler query-collections DATA u/jbosch/bootcamp/*
    collections:
    - u/jbosch/bootcamp/1/20201013T14h04m17s
    - u/jbosch/bootcamp/1
    - u/jbosch/bootcamp/1/20201013T14h09m42s

So, we've now got two `RUN` collections with timestamp-based names, and the same `CHAINED` collection.
What does that `CHAINED` collection look like now?

    $ butler query-collections DATA --flatten-chains u/jbosch/bootcamp/1
    collections:
    - u/jbosch/bootcamp/1/20201013T14h09m42s
    - u/jbosch/bootcamp/1/20201013T14h04m17s
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

It includes _both_ `RUN` collections, with the most recent one first.
So with the way we've run `pipetask`, the outputs of earlier runs are automatically considered as inputs to later runs.
They weren't actually used here, because the outputs of ISR aren't used as the inputs of ISR, and that's the only task we've run, but if the pipeline had changed, they could have been.

The outputs of the first invocation are still there, too, if we look _without_ `--find-first`:

    $ butler query-datasets DATA postISRCCD --collections u/jbosch/bootcamp/1

    type                     run                    id  instrument detector exposure
    ---------- -------------------------------------- ---- ---------- -------- --------
    postISRCCD u/jbosch/bootcamp/1/20201013T14h09m42s 1745        HSC        5   903344
    postISRCCD u/jbosch/bootcamp/1/20201013T14h04m17s 1736        HSC        5   903344

But if we search with `--find-first` (which is the logic `Butler.get` would use internally to actually load this dataset in Python), we only see the new one; it "shadows" the previous one:

    $ butler query-datasets DATA postISRCCD --collections u/jbosch/bootcamp/1 --find-first

    type                     run                    id  instrument detector exposure
    ---------- -------------------------------------- ---- ---------- -------- --------
    postISRCCD u/jbosch/bootcamp/1/20201013T14h09m42s 1745        HSC        5   903344


Now, let's imagine that I didn't actually want to stop processing there, and now I want to pick up where I left off, and go straight to running `characterizeImage` on the ISR outputs.
I can do that by adding `--extend-run --skip-existing` to my `pipetask` invocation:

    $ $ pipetask run -b DATA -p pipelines/example.yaml -o u/jbosch/bootcamp/1 -d "instrument='HSC' AND visit=903344 AND detector=5" --extend-run --skip-existing
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 14 quanta for 4 tasks
    conda.common.io INFO: overtaking stderr and stdout
    conda.common.io INFO: stderr and stdout yielding back
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 57 cosmic rays.
    characterizeImage.detection INFO: Detected 957 positive peaks in 272 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    characterizeImage.measurement INFO: Measuring 272 sources (272 parents, 0 children)
    characterizeImage.measurePsf INFO: Measuring PSF
    characterizeImage.measurePsf INFO: PSF star selector found 147 candidates
    characterizeImage.measurePsf.reserve INFO: Reserved 29/147 sources
    characterizeImage.measurePsf INFO: Sending 118 candidates to PSF determiner
    characterizeImage.measurePsf.psfDeterminer WARN: NOT scaling kernelSize by stellar quadrupole moment, but using absolute value
    characterizeImage.measurePsf INFO: PSF determination using 116/118 stars.
    characterizeImage INFO: iter 1; PSF sigma=1.76, dimensions=(41, 41); median background=177.88
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 52 cosmic rays.
    characterizeImage.detection INFO: Detected 872 positive peaks in 273 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    characterizeImage.measurement INFO: Measuring 273 sources (273 parents, 0 children)
    characterizeImage.measurePsf INFO: Measuring PSF
    characterizeImage.measurePsf INFO: PSF star selector found 149 candidates
    characterizeImage.measurePsf.reserve INFO: Reserved 30/149 sources
    characterizeImage.measurePsf INFO: Sending 119 candidates to PSF determiner
    characterizeImage.measurePsf.psfDeterminer WARN: NOT scaling kernelSize by stellar quadrupole moment, but using absolute value
    characterizeImage.measurePsf INFO: PSF determination using 117/119 stars.
    characterizeImage INFO: iter 2; PSF sigma=1.76, dimensions=(41, 41); median background=177.86
    characterizeImage.repair INFO: Identified 55 cosmic rays.
    characterizeImage.measurement INFO: Measuring 273 sources (273 parents, 0 children)
    characterizeImage.measureApCorr INFO: Measuring aperture corrections for 23 flux fields
    characterizeImage.measureApCorr.sourceSelector INFO: Selected 53/273 sources
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_0_kron: RMS 0.002149 from 48
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_3_4_5: RMS 0.007855 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for modelfit_CModel_initial: RMS 0.005734 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for base_PsfFlux: RMS 0.004999 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_1_3_3: RMS 0.013698 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_3_3_3: RMS 0.031499 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_3_6_0: RMS 0.005099 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for modelfit_CModel_exp: RMS 0.005012 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for base_GaussianFlux: RMS 0.005589 from 49
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_0_6_0: RMS 0.004412 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_1_4_5: RMS 0.005466 from 49
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_3_kron: RMS 0.003018 from 51
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_0_3_3: RMS 0.011327 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for modelfit_CModel_dev: RMS 0.005386 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_1_kron: RMS 0.002000 from 48
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_2_4_5: RMS 0.006810 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_0_4_5: RMS 0.005146 from 49
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_1_6_0: RMS 0.004481 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_2_6_0: RMS 0.004736 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_photometryKron_KronFlux: RMS 0.002149 from 48
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_2_3_3: RMS 0.021317 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for ext_convolved_ConvolvedFlux_2_kron: RMS 0.001897 from 50
    characterizeImage.measureApCorr INFO: Aperture correction for modelfit_CModel: RMS 0.005219 from 50
    characterizeImage.applyApCorr INFO: Applying aperture corrections to 23 instFlux fields
    calibrate.detection INFO: Detected 1814 positive peaks in 1020 footprints and 27 negative peaks in 25 footprints to 5 sigma
    calibrate.detection INFO: Resubtracting the background after object detection
    calibrate.skySources INFO: Added 100 of 100 requested sky sources (100%)
    calibrate.deblend INFO: Deblending 1120 sources
    calibrate.deblend WARN: Parent 775966608882401524: skipping large footprint (area: 16639)
    calibrate.deblend WARN: Parent 775966608882401883: skipping large footprint (area: 10848)
    calibrate.deblend WARN: Parent 775966608882401887: skipping large footprint (area: 53868)
    calibrate.deblend WARN: Parent 775966608882401998: skipping large footprint (area: 22200)
    calibrate.deblend WARN: Parent 775966608882402114: skipping large footprint (area: 10975)
    calibrate.deblend INFO: Deblended: of 1120 sources, 94 were deblended, creating 370 children, total 1490 sources
    calibrate.measurement INFO: Measuring 1490 sources (1120 parents, 370 children)
    ^C
    Aborted!

The `--extend-run` option says to just add more datasets to the last `RUN`-type collection instead of creating a new one, and as expected, we still have the same collections we had before:

    $ butler query-collections DATA --flatten-chains u/jbosch/bootcamp/1
    collections:
    - u/jbosch/bootcamp/1/20201013T14h09m42s
    - u/jbosch/bootcamp/1/20201013T14h04m17s
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

But now we have some new datasets:

    $ butler query-datasets DATA icExp icSrc --collections u/jbosch/bootcamp/1 --find-first

    type                  run                    id  instrument detector visit
    ----- -------------------------------------- ---- ---------- -------- ------
    icSrc u/jbosch/bootcamp/1/20201013T14h09m42s 1747        HSC        5 903344

    type                  run                    id  instrument detector visit
    ----- -------------------------------------- ---- ---------- -------- ------
    icExp u/jbosch/bootcamp/1/20201013T14h09m42s 1749        HSC        5 903344

As the name implies, `--skip-existing` says to skip quanta (task executions) that would generate outputs that already exist in the output run.
Right now, it just doesn't work to pass either of `--extend-run` or `--skip-existing` on its own, for reasons I don't want to get into, and we may merge them in the future.

Running modified pipelines
--------------------------

Passing `--extend-run` comes with an important constraint: we automatically write all configuration options and a list of software versions to each `RUN` collection as special datasets, and when you use `--extend-run`, we demand that none of those have changed:

    $ pipetask run -b DATA -p pipelines/example.yaml -o u/jbosch/bootcamp/1 -d "instrument='HSC' AND visit=903344 AND detector=5" --extend-run --skip-existing -c isr:doDark=False
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 13 quanta for 4 tasks
    ctrl.mpexec.preExecInit FATAL: Comparing configuration: Inequality in doDark: False != True
    Error: An error occurred during command execution:
    Traceback (most recent call last):
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/daf_butler/19.0.0-172-gc4bef2ce+ff10c6d78d/python/lsst/daf/butler/cli/utils.py", line 446, in cli_handle_exception
        return func(*args, **kwargs)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cli/script/run.py", line 173, in run
        f.runPipeline(qgraphObj, taskFactory, args)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/cmdLineFwk.py", line 632, in runPipeline
        saveVersions=not args.no_versions)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/preExecInit.py", line 90, in initialize
        self.saveConfigs(graph)
    File "/home/jbosch/LSST/lsstsw/stack/cb4e2dc/Linux64/ctrl_mpexec/20.0.0-31-g5eb8f13+6f95832be2/python/lsst/ctrl/mpexec/preExecInit.py", line 239, in saveConfigs
        f"Config does not match existing task config {configName!r} in butler; "
    TypeError: Config does not match existing task config 'isr_config' in butler; tasks configurations must be consistent within the same run collection

Those of you familiar with the Gen2 middleware are now probably shouting in your heads, "use `--clobber-config`!"
But `--clobber-config` doesn't exist in Gen3, and I don't think it needs to: just don't pass `--extend-run`, and `pipetask` will happily put your outputs in a new `RUN` with new configuration files, while creating an umbrella `CHAINED` collection that searches both the new collection and the old one.

If you want to go a step further and just redefine the `CHAINED` collection to have _only_ the new collection, you can use `--replace-run`.
Before we demo that, let's start over with a brand-new output `CHAINED` collection (note the `/2` suffix, and the fact that we had to add `-i HSC/defaults` back in):

    $ pipetask run -b DATA -p pipelines/example.yaml -o u/jbosch/bootcamp/2 -i HSC/defaults -d "instrument='HSC' AND visit=903344 AND detector=5"
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 15 quanta for 4 tasks
    conda.common.io INFO: overtaking stderr and stdout
    conda.common.io INFO: stderr and stdout yielding back
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    isr INFO: Converting exposure to floating point values.
    isr INFO: Assembling CCD from amplifiers.
    isr INFO: Applying bias correction.
    isr INFO: Applying linearizer.
    isr INFO: Applying crosstalk correction.
    isr.crosstalk INFO: Applying crosstalk correction.
    isr INFO: Masking defects.
    isr INFO: Masking NAN value pixels.
    isr INFO: Widening saturation trails.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying brighter fatter correction using kernel type <class 'numpy.ndarray'> / gains <class 'NoneType'>.
    isr INFO: Finished brighter fatter correction in 3 iterations.
    isr INFO: Ensuring image edges are masked as SUSPECT to the brighter-fatter kernel size.
    isr INFO: Growing masks to account for brighter-fatter kernel convolution.
    isr INFO: Applying dark correction.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying flat correction.
    isr INFO: Applying fringe correction after flat.
    isr.fringe INFO: Filter not found in FringeTaskConfig.filters. Skipping fringe correction.
    isr INFO: Constructing Vignette polygon.
    isr INFO: Adding transmission curves.
    isr INFO: Set 232863 BAD pixels to 178.167053.
    isr INFO: Interpolating masked pixels.
    isr INFO: Setting rough magnitude zero point: 32.692803
    isr INFO: Measuring background level.
    isr INFO: Flattened sky level: 178.161118 +/- 7.345197.
    isr INFO: Measuring sky levels in 8x16 grids: 177.987633.
    isr INFO: Sky flatness in 8x16 grids - pp: 0.026886 rms: 0.004539.
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 57 cosmic rays.
    characterizeImage.detection INFO: Detected 957 positive peaks in 272 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    ^C
    Aborted!

As expected, we get a new `u/jbosch/bootcamp/2` `CHAINED` collection that starts with a new `RUN` collection that holds the direct outputs:

    $ butler query-collections DATA --flatten-chains u/jbosch/bootcamp/2
    collections:
    - u/jbosch/bootcamp/2/20201013T18h15m39s
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

And now we'll we'll run again with `--replace-run` (while dropping `-i HSC/defaults`):

    $ pipetask run -b DATA -p pipelines/example.yaml -o u/jbosch/bootcamp/2 --replace-run -d "instrument='HSC' AND visit=903344 AND detector=5"
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 15 quanta for 4 tasks
    conda.common.io INFO: overtaking stderr and stdout
    conda.common.io INFO: stderr and stdout yielding back
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    isr INFO: Converting exposure to floating point values.
    isr INFO: Assembling CCD from amplifiers.
    isr INFO: Applying bias correction.
    isr INFO: Applying linearizer.
    isr INFO: Applying crosstalk correction.
    isr.crosstalk INFO: Applying crosstalk correction.
    isr INFO: Masking defects.
    isr INFO: Masking NAN value pixels.
    isr INFO: Widening saturation trails.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying brighter fatter correction using kernel type <class 'numpy.ndarray'> / gains <class 'NoneType'>.
    isr INFO: Finished brighter fatter correction in 3 iterations.
    isr INFO: Ensuring image edges are masked as SUSPECT to the brighter-fatter kernel size.
    isr INFO: Growing masks to account for brighter-fatter kernel convolution.
    isr INFO: Applying dark correction.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying flat correction.
    isr INFO: Applying fringe correction after flat.
    isr.fringe INFO: Filter not found in FringeTaskConfig.filters. Skipping fringe correction.
    isr INFO: Constructing Vignette polygon.
    isr INFO: Adding transmission curves.
    isr INFO: Set 232863 BAD pixels to 178.167053.
    isr INFO: Interpolating masked pixels.
    isr INFO: Setting rough magnitude zero point: 32.692803
    isr INFO: Measuring background level.
    isr INFO: Flattened sky level: 178.161118 +/- 7.345197.
    isr INFO: Measuring sky levels in 8x16 grids: 177.987633.
    isr INFO: Sky flatness in 8x16 grids - pp: 0.026886 rms: 0.004539.
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 57 cosmic rays.
    characterizeImage.detection INFO: Detected 957 positive peaks in 272 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    characterizeImage.measurement INFO: Measuring 272 sources (272 parents, 0 children)
    ^C
    Aborted!

As promised, the `CHAINED` collection now points at a new `RUN` collection:

    $ butler query-collections DATA --flatten-chains u/jbosch/bootcamp/2
    collections:
    - u/jbosch/bootcamp/2/20201013T21h16m50s
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

but the old one hasn't gone away; it's just been shunted off to the side:

    $ butler query-collections DATA u/jbosch/bootcamp/2/*
    collections:
    - u/jbosch/bootcamp/2/20201013T18h15m39s
    - u/jbosch/bootcamp/2/20201013T21h16m50s

So, if you're debugging a problem with a task or pipeline, you can:

1. prep an output `CHAINED` collection with one "regular" `pipetask` run (with `-i` but without `--replace-run`);
2. change some code and/or configuration;
3. run `pipetask` with the most of same arguments, but without `-i` and with `--replace-run`;
4. repeat steps 2 and 3 until you're done debugging;
5. go back and delete those displaced runs to clean up.

The last step (5) is a little clunky right now, because you can only delete them one at a time and you have to type out the full name, e.g.

    $ butler prune-collection DATA --purge --unstore --collection u/jbosch/bootcamp/2/20201013T18h15m39s

But we'll get that fixed (and, as mentioned earlier, make it okay to keep passing `-i` as long as the inputs don't change).
If you're not super constrained by disk space, that's the workflow we'd recommend - better to have those displaced runs and not need them.

But if you want to live on the edge and blow them away immediately, you can add `--prune-replaced=purge` as well to do that.

    $ pipetask run -b DATA -p pipelines/example.yaml -o u/jbosch/bootcamp/2 --replace-run --prune-replaced=purge -d "instrument='HSC' AND visit=903344 AND detector=5"
    ctrl.mpexec.cmdLineFwk INFO: QuantumGraph contains 15 quanta for 4 tasks
    conda.common.io INFO: overtaking stderr and stdout
    conda.common.io INFO: stderr and stdout yielding back
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    afw.image.MaskedImageFitsReader WARN: Expected extension type not found: IMAGE
    isr INFO: Converting exposure to floating point values.
    isr INFO: Assembling CCD from amplifiers.
    isr INFO: Applying bias correction.
    isr INFO: Applying linearizer.
    isr INFO: Applying crosstalk correction.
    isr.crosstalk INFO: Applying crosstalk correction.
    isr INFO: Masking defects.
    isr INFO: Masking NAN value pixels.
    isr INFO: Widening saturation trails.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying brighter fatter correction using kernel type <class 'numpy.ndarray'> / gains <class 'NoneType'>.
    isr INFO: Finished brighter fatter correction in 3 iterations.
    isr INFO: Ensuring image edges are masked as SUSPECT to the brighter-fatter kernel size.
    isr INFO: Growing masks to account for brighter-fatter kernel convolution.
    isr INFO: Applying dark correction.
    isr WARN: darkExposure.getInfo().getVisitInfo() does not exist. Using darkScale = 1.0.
    isr INFO: Applying flat correction.
    isr INFO: Applying fringe correction after flat.
    isr.fringe INFO: Filter not found in FringeTaskConfig.filters. Skipping fringe correction.
    isr INFO: Constructing Vignette polygon.
    isr INFO: Adding transmission curves.
    isr INFO: Set 232863 BAD pixels to 178.167053.
    isr INFO: Interpolating masked pixels.
    isr INFO: Setting rough magnitude zero point: 32.692803
    isr INFO: Measuring background level.
    isr INFO: Flattened sky level: 178.161118 +/- 7.345197.
    isr INFO: Measuring sky levels in 8x16 grids: 177.987633.
    isr INFO: Sky flatness in 8x16 grids - pp: 0.026886 rms: 0.004539.
    characterizeImage WARN: Source catalog detected and measured with placeholder or default PSF
    characterizeImage.repair INFO: Identified 57 cosmic rays.
    characterizeImage.detection INFO: Detected 957 positive peaks in 272 footprints and 0 negative peaks in 0 footprints to 50 sigma
    characterizeImage.detection INFO: Resubtracting the background after object detection
    ^C
    Aborted!

Voila!  One new run in `u/jbosch/bootcamp/2`:

    $ butler query-collections DATA --flatten-chains u/jbosch/bootcamp/2
    collections:
    - u/jbosch/bootcamp/2/20201013T21h37m22s
    - HSC/raw/all
    - HSC/calib
    - HSC/masks
    - refcats
    - skymaps

and no old run anywhere:

    $ butler query-collections DATA u/jbosch/bootcamp/2/*
    collections:
    - u/jbosch/bootcamp/2/20201013T21h37m22s

There's also an intermediate option: `--prune-replaced=unstore`, which is supposed to let you just delete the actual files, while retaining all of the provenance information you'd need to reconstruct them in the database.
But we don't yet save enough provenance for that to actually be useful, so it's best ignored for now.

There are a _lot_ more `pipetask` options than I've shown here (and entirely different modes of running it), and a lot of concepts I've just glossed over.
There's also a completely separate Batch Production Service (BPS) tool for running at scale.
We're looking for feedback as people try these out on their day-to-day work, and we expect that to eventually lead to command-line interface changes, beyond just the known rough edges I've pointed out in this tutorial and our long-term vision of integrating BPS and `pipetask` more closely.
In the meantime, I hope this is enough to get everyone started, and provide enough of a conceptual background to make it easy to learn more.
