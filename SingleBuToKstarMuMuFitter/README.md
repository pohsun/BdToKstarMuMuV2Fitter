# SingleBuToKstarMuMuFitter

## Overview of the design

* [`StdProcess.py`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/StdProcess.py)
* [`anaSetup.pu`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/anaSetup.py)
* [`seqCollection.py`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/seqCollection.py)

# How to run?

## Standard fitting procedure

Select a pre-defined sequence in [`seqCollection.py`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/seqCollection.py), and then just

```sh
python seqCollection.py
```

## Validation

* [`script/batchTask_simpleToyValidation.py`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/script/batchTask_simpleToyValidation.py)

## Statistical error

Due to low statistics, Feldman-Cousins method is suggested to estimate statistical uncertainties.
Two scripts are prepared for this procedure.
* Step1 - fitting to profiled toys with [`script/batchTask_profiledFeldmanCousins.py`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/script/batchTask_profiledFeldmanCousins.py)

* Step2 - harvest fit results and calculate error with [`script/postporcess_profiledFeldmanCousins.py`](https://github.com/pohsun/BuToKstarMuMuV2Fitter/blob/master/SingleBuToKstarMuMuFitter/script/postporcess_profiledFeldmanCousins.py)

## Systematics error
