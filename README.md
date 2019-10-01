# BdToKsrarMuMuV2Fitter

This fitter package is designed for ![](http://latex.codecogs.com/svg.latex?B^{+}\rightarrow{K^{*+}\mu\mu}) angular analysis with CMS Run2012 data.

* `v2Fitter`: The core of the fitting procedure, i.e. parts not for this particular analysis. It may be re-used for future works. 

* `SingleBuToKstarMuMuFitter`: The customized fitting code for btosll analysis.

* `SingleBuToKstarMuMuSelector`: The single candidate ntuple maker for btosll analysis.

* `EvtGen`: Unfiltered GEN level MC production without CMSSW.

# Setup

The package depends on python2.7 and pyROOT.

On lxplus, just run

```bash
source setup_ROOTEnv.sh
```

For the first time, you may need to install following pre-requisites with

```bash
pip install --user enum34
```
