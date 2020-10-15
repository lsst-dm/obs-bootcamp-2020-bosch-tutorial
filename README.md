Middleware tutorial for Rubin Observatory Operations Bootcamp, 2020
===================================================================

This repository includes two _mostly_ independent tutorials:

 - `command-line-tutorial.md` introduces "collection" concepts and demonstrates usage of the `pipetask` tool, and should be read as speaker's notes and a (predicted) transcript for a live demo.
 - `butler-python-tutorial.ipynb` is a Jupyter notebook (a streamlined, updated version of one presented at the July 2020 DESC meeting) on using the `Butler` class in Python to access and explore data repositories.

It also contains some supporting files to set up an environment to make all of the demo'd code actually work:

 - `scripts/export-ci_hsc.py`: export everything from a setup, built copy of `ci_hsc_gen3` to the `DATA` directory here.
 - `scripts/setup-repo.py`: create a new Gen3 repository in `DATA` and import all of that in-place.
 - `ups/bootcamp.table`: an EUPS table file for setting up all dependencies.  Paths to `testdata_ci_hsc` and `ci_hsc_gen3` will need to be hand-edited to be usable.
 - `pipelines/example.yaml`: the Pipeline definition actually used in the command-line tutorial.
 - a `daf_butler` git submodule containing the exact version used here, which includes some customizations to preview not-yet-merged functionality.

As the middleware is under _heavy_ development and considerable churn at the time of this tutorial, my long-term plan for this content is to migrate it to Sphinx documentation that lives with (and is more easily updated with) the code, rather than attempt to maintain this repo in its current form.
