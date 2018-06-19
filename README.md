# The SAMI Pipeline

[![Build Status](https://travis-ci.org/soar-telescope/sami.svg?branch=master)](https://travis-ci.org/soar-telescope/sami)
[![Coverage Status](https://coveralls.io/repos/github/soar-telescope/sami/badge.svg?branch=master)](https://coveralls.io/github/soar-telescope/sami?branch=master)


This is a new pipeline for the SAM Imager using pure Python and
libraries. At the moment, this pipeline is intended to be used locally
so a installation have to be performed.

## Features

    * Data Reduction

### Data Reduction

 Once installed, you can call the data reduction software using a
 terminal by typing `sreduce-sami $PATH`, where `$PATH` is a directory
 containing raw files. The processed data will be stored into a new
 folder called `$PATH\RED`. Each file will receive a prefix accordingly
 to the corrections applied.

 Here are the data reduction processed steps:

 1) Overscan correction: reduce-sami sum each overscan row and fit a
 3rd degree polynomium to the result. This polynomium is then subtracted
 from each column on each extension.

 2) Move the overscan region to the outer edges of the detector and
 merge the four data arrays into a single one.

 3) ZERO images are combined using the average and minmax clip with the
 default thresholds.

 4) ZERO subtraction is performed using simple subtraction operation.

 5) FLAT images are combined using the median and sigma clip with the
 default thresholds. The master flat is normalized using 10% of the
 image size centered in the middle of the merged image.

 6) FLAT correction is performed using common division.

 7) Cosmic rays are cleaned using LaCosmic
 [(Dokkun, 2001)](http://www.astro.yale.edu/dokkum/lacosmic/) with the
 default parameters.

 The prefixes on the processed data are:

 * m : image was **m**erged.
 * z : image was **z**ero subtracted.
 * r : **r**emoved cosmic rays form image.
 * f : image was **f**lat fielded.

## Install

  The simplest way to use the SAMI Data-Reduction Pipeline is using
  [astroconda](https://astroconda.readthedocs.io/en/latest/), since it
  contains most of the packages needed.

  You will still need `astropy:ccdproc`. To do so, activate the
  `astroconda` virtual environment and install it using the following
  command:

  ```
  ```

  Once you have everything, check if you have all the required packages
  by typing:

  ```
  ```

  If you receive no error, you can install the package using `pip`:

  ```
  $ pip install .
  ```

  If you are updating the SAMI Data-Reduction Pipeline, you must type:

  ```
  $ pip install --upgrade .
  ```


## Missing features?

  If you require new features, please, use the
  [GitHub Issues Page](https://github.com/soar-telescope/sami/issues).
  With that, we can have control of the progress of the pipeline.