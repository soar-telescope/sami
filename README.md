# The SAMI Pipeline

[![Build Status](https://travis-ci.org/soar-telescope/sami.svg?branch=master)](https://travis-ci.org/soar-telescope/sami)
[![Coverage Status](https://coveralls.io/repos/github/soar-telescope/sami/badge.svg?branch=master)](https://coveralls.io/github/soar-telescope/sami?branch=master)

This is a new pipeline for the SAM Imager using pure Python and
libraries created by [B. Quint](https://github.com/b1quint) and
further improved by [F. Navarete](https://github.com/navarete).
At the moment, this pipeline is intended to be used locally
so a installation have to be performed. As this is an active project,
you will  find that several features are still to be implemented.

## Install

  The simplest way to use the SAMI Data-Reduction Pipeline is using [astroconda](https://astroconda.readthedocs.io/en/latest/),
  since it contains most of the packages needed.
  Once you have it installed, you can create a new virtual environment. As an example, we will create the environment ```sami_pipeline```:
  ```
  $ conda create --name sami_pipeline
  ```

  Then, activate the `astroconda` virtual environment by typing: 

  ```
  $ source activate sami_pipeline
  ```
  
  Once logged into the new conda environment, install the Python packages `astropy:ccdproc:pandas` using the following command:

  ```
  (sami_pipeline) $ conda install -c astropy ccdproc pandas
  ```

  Once you are done, you can download the [SAMI Data-Reduction Pipeline](https://github.com/soar-telescope/sami/archive/master.zip)
  and extract it somewhere into your computer.
  Go to the directory where you extracted it and check if you have all the required packages by typing:

  ```
  (sami_pipeline) path_to_the_samidr $ python setup.py test
  ```

  If you receive no error, you can install the package using `pip`:

  ```
  (sami_pipeline) path_to_the_samidr $ pip install .
  ```

  If you are updating the SAMI Data-Reduction Pipeline, you must type:

  ```
  (sami_pipeline) path_to_the_samidr $ pip install --upgrade .
  ```

## Use

  Once installed, the SAMI Data-Reduction Pipeline can be run using a terminal
  by the following command:

  ```
  (sami_pipeline) $ reduce_sami $path_to_data --outfolder $path_to_reduced_data
  ```

  Where `$path_to_data` is the path to the directory that contains SAMI data and
  `$path_to_reduced_data` is the directory to save the processed data
  (this is useful in case you are not allowed to modify the path containing the raw data).

  Note that the pipeline does not perform any type of data quality at the moment
  so you might check your files to avoid bad data like saturated or empty
  images.

## Features

* Data Reduction
* Data Quality

### Data Reduction

 Once installed, you can call the data reduction software using a
 terminal by typing `reduce_sami $PATH`, where `$PATH` is a directory
 containing raw files. The processed data will be stored into a new
 folder called `$PATH\RED`. Now, you can also define the directory that will
 contain the processed data by typing `reduce_sami $PATH --outfolder $PATH_RED`,
 where `$PATH_RED` is the new directory with the processed data.
 Each file will receive a prefix accordingly
 to the corrections applied.

 Here are the data reduction processed steps:

 1) Overscan correction: `reduce_sami` sum each overscan row and fit a
 3rd degree polynomial function to the result. This fit is then subtracted
 from each column on each extension.

 2) Move the overscan region to the outer edges of the detector and
 merge the four data arrays into a single one.

 3) ZERO images are combined using the average and minmax clip with the
 default thresholds.

 4) ZERO subtraction is performed using simple subtraction operation.

 5) FLAT images are scaled by the inverse of their median values, 
 and median combined using sigma clip with the default thresholds
 (`sigma_clip_low_thresh=3, sigma_clip_high_thresh=3`).
 The master flat is normalized using 10% of the
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
