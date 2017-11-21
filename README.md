# The SAMI Pipeline

[![Build Status](https://travis-ci.org/soar-telescope/sami.svg?branch=master)](https://travis-ci.org/soar-telescope/sami)
[![Coverage Status](https://coveralls.io/repos/github/soar-telescope/sami/badge.svg?branch=master)](https://coveralls.io/github/soar-telescope/sami?branch=master)


This is a new pipeline for the SAM Imager using pure Python and libraries. At the moment, this pipeline is intended to 
be used locally so a installation have to be performed. The SAMI Pipeline is now in an early development state and it 
is not realiable at all. 

## Pipeline Structure

The SAMI pipeline will be divided into five main routines. The idea is that they are independent but relie on each 
other.  

*[ ] Data Watcher
*[ ] Data Classifier
*[ ] Data Quality
*[ ] Data Reduction
*[ ] Data Display

### Data Receiver

An online or offline database constructor. It will be used to feed a database that will be used further in the pipeline. 
For now, we will priorize the offline version and for the database we will use SQLite.

### Data Classifier

Once we have a database with the relevant information (i.e., metadata extracted from the FITS headers), we can classify 
them. This should be straightforward considering the small number of different configurations at SAMI but still has to 
be done.

### Data Quality

This will be one of the trickiest part. How do we know that the metadata is actually right? How do we know if a FLAT
image was not actually an OBJECT image and vice-e-versa? 

### Data Process

Once we have our data pre-analysed and classified we can perform the data reduction. This, again, is straightforward 
considering that the [AstroPy]() and [ccdproc]() packages have most of the required routines.

### Data Display

This is the very last past of the pipeline. We want to run a local aplication where the data can be easily found. Think 
of it as a local archive used to read and update night logs and display the data.
       