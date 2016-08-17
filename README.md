
### v0.7.2

[![PyPi Version](https://img.shields.io/pypi/v/pynastran.svg)](https://pypi.python.org/pypi/pyNastran)
[![PyPi Downloads](https://img.shields.io/pypi/dm/pynastran.svg)](https://pypi.python.org/pypi/pyNastran)

<!--- [![Github Downloads](	https://img.shields.io/github/downloads/SteveDoyle2/pyNastran/latest/total.svg)  --->
<!--- [![All Downloads](https://img.shields.io/github/downloads/SteveDoyle2/pyNastran/total.svg)  --->
<!--- [![Total PyPi Downloads](https://img.shields.io/github/downloads/atom/atom/latest/pynastran.svg)]  --->
<!--- [![v0.7.2 Downloads](https://img.shields.io/github/downloads/atom/atom/v0.7.2/total.svg)]  --->

[Documentation] (http://pynastran-git.readthedocs.org/en/v0.7.2/index.html)

### Master

[![Build Status](https://travis-ci.org/SteveDoyle2/pyNastran.png)](https://travis-ci.org/SteveDoyle2/pyNastran)

[Doumentation](http://pynastran-git.readthedocs.org/en/latest/index.html)

Also, check out the:
  * [Wiki](https://github.com/SteveDoyle2/pynastran/wiki)
  * [Discussion forum](http://groups.google.com/group/pynastran-discuss)
  * [Developer forum](http://groups.google.com/group/pynastran-dev)

for more detailed information.

<!--- this isn't setup... -->
<!--- http://stevedoyle2.github.io/pyNastran/ --->

# News

### pyNastran v0.8 GUI demo (8/16/2016)

  [Download](https://sourceforge.net/projects/pynastran/files/?source=navbar)

# Overview

pyNastran is an interface library to the various Nastran file formats (BDF, OP2, OP4).  Using the BDF interface, you can read/edit/write Nastran geometry without worrying about field formatting.  Many checks are also performed to verify that your model is correct.  Using the OP2 interface, you can read very large result files very quckly and very efficiently.  Additionally, you can also extract a subset of the result data and write F06 result files.

Using the pyNastran GUI, you can read in Nastran models and quickly view results for a model.  While it's no FEMAP/Patran, it can replace many tasks that would otherwise require a commercial program.
![GUI](https://github.com/SteveDoyle2/pynastran/blob/v0.7/pyNastran/gui/caero.png)


<!--- Ripped off meshio  --->
<!--- [![Build Status](https://travis-ci.org/SteveDoyle2/pyNastran.svg?branch=master)](https://travis-ci.org/SteveDoyle2/pyNastran)  --->
<!--- [![codecov.io](https://codecov.io/github/SteveDoyle2/pyNastran/coverage.svg?branch=master)](https://codecov.io/github/SteveDoyle2/pyNastran?branch=master)  --->


## pyNastran v0.8 progress (8/16/2016)
 - BDF
   - 278 cards supported
   - simplifed method to add cards
     - grid = GRID(nid, cp, xyz, cd, ps, eid, comment)
   - lots of optimization work
   - bdf equivalence, renumber, deck merging
   - element quality
 - OP2
   - improved SOL 200 support
   - transform displacement/eigenvectors/spc/mpc/applied loads to global coordinate system
   - transform stresses/forces to material coordinate system
   - geometry can be read directly from op2 (not perfect, but when it works, it's much faster)
 - GUI
   - area, max interior angle, skew angle, aspect ratio results
   - improved SOL 200 support
   - aero models now support sideslip coordinate systems
   - more legend control
 - OP4
  - fixed sparse ASCII BIGMAT bug

## pyNastran v0.8 progress (~2/2016)
 - BDF
   - supports unicode
   - 270 cards supported
 - OP2
   - ~500x faster than v0.7.2
     - non-vectorized OP2 option has being removed
   - Matrix support
   - [Pandas](http://pandas.pydata.org/) DataFrame support for use in the [Jupyter/iPython](http://jupyter.org/index.html) Notebook
 - GUI
   - nodal and centroidal results supported at the same time
   - deflection plot support

## pyNastran v0.7.2 has been Released (4/25/2015)

[Download pyNastran v0.7] (https://github.com/SteveDoyle2/pyNastran/releases)

Highlights:
 * OP2
   * superelement support
   * vectorized support (uses much less memory; Element Forces not vectorized yet)
   * additional results (e.g. grid point weight, eigenvalues)
   * `PARAM,POST,-2` support
   * catching of most FATAL errors without needing to read the F06
 * F06
   * removed
 * BDF
   * 238 BDF cards
   * large field format and double precision writing
 * GUI
   * much improved GUI with transient support (real only), a results sidebar, logging, and scripting support
 * Other
   * additional readers/converters to/from various other formats (e.g. STL, Cart3d, Panair) as well as GUI support
   * autogenerated online documentation for pyNastran using [readthedocs](https://rwww.readthedocs.org) and [Sphinx](http://sphinx-doc.org/)

Most op2 object were changed in order to eliminate errors, and be more consistent.  For example, `plateStress` has been replaced by `ctria3_stress`, `cquad4_stress`, `ctria6_stress`, etc.  Also, plate centroids now have a `node_id` of `0`.  This greatly simplifies F06 writing and vectorized data extraction.

### Version 0.6.1 has been released (6/2013)
**Version 0.6** improves BDF reading.  The reader is more robust and also requires proper BDF field formatting (e.g. a integer field can't be a float).  Additionally, cards also have a comment() method.

Marcin Gąsiorek participated in the latest pyNastran under the European Space Agency's (ESA) "Summer of Code In Space" [SOCIS](http://sophia.estec.esa.int/socis2012/?q=node/13) program.  The program provides a stipend to students to work on open-source projects.
He did a great job of simplifying code and creating nicer documentation.

## Additional Info

If anyone makes any specific requests I'll try to incorporate them.  They need to be specific, such as read these cards from the BDF, read these results from this OP2, or write these results to an OP2.  <b>Any sample problems that you have (to test the software with) would be appreciated.  I need small examples that are comprehensive that I can add as demo problems.</b>
