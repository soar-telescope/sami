# The SAMI Pipeline

[![Build Status](https://travis-ci.org/soar-telescope/sami.svg?branch=master)](https://travis-ci.org/soar-telescope/sami)
[![Coverage Status](https://coveralls.io/repos/github/soar-telescope/sami/badge.svg?branch=master)](https://coveralls.io/github/soar-telescope/sami?branch=master)

This is a new pipeline for the SAM Imager using pure Python and
libraries. At the moment, this pipeline is intended to be used locally
so a installation have to be performed. As this is an active project, you mind
find that several features are still to be implemented.

## Install

  The simplest way to use the SAMI Data-Reduction Pipeline is using [astroconda](https://astroconda.readthedocs.io/en/latest/), since it contains most of the packages needed. Once you have it installed, you can activate the virtual environment by typing:
  
  ```
  $ source activate my_virtual_env
  ```
  
  [astroconda](https://astroconda.readthedocs.io/en/latest/) contains almost all the packages you need to run the SAMI Data-Reduction Pipeline but you will still need `astropy:ccdproc`. To solve this, activate the `astroconda` virtual environment and install it using the following command:

  ```
  (my_virtual_env) $ conda install -c astropy ccdproc
  ```

  Once you are done, you can download the [SAMI Data-Reduction Pipeline](https://github.com/soar-telescope/sami/archive/master.zip) and extract it somewhere into your computer. Go to where you extracted it and check if you have all the required packages by typing:

  ```
  (my_virtual_env) path_to_the_samidr $ python setup.py test
  ```

  If you receive no error, you can install the package using `pip`:

  ```
  (my_virtual_env) path_to_the_samidr $ pip install .
  ```

  If you are updating the SAMI Data-Reduction Pipeline, you must type:

  ```
  (my_virtual_env) path_to_the_samidr $ pip install --upgrade .
  ```

## Use

  Once installed, the SAMI Data-Reduction Pipeline can be run using a terminal
  by the following command:

  ```
  (my_virtual_env) $ reduce_sami $path_to_data
  ```

  Where `$path_to_data` is the path to the directory that contains SAMI data.

  Note that the pipeline does not perform any type of data quality at the moment
  so you might check your files to avoid bad data like saturated or empty
  images.

## Features

* Data Reduction
* Data Quality

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
 * _ (no prefix) : means that the data was flagged as bad data.

### Data Quality

 Very basic data quality is performed. At the moment, we know that when some images
 are completely saturated, they had standard deviation equal to zero. We also know
 that, sometimes, SAMI cannot write an image and tries again. The first image is
 also flagged as bad.

 Our experience says that saturated images can have different behaviours. We also know
 that the images may contain no data where they should. These cases are still not controlled.

### Missing features?

If you require new features, please, use the [GitHub Issues Page](https://github.com/soar-telescope/sami/issues). With that, we can have control of the progress of the pipeline.
