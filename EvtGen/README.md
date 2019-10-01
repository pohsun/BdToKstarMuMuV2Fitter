# Unfiltered MC generation with [`EvtGen`](https://evtgen.hepforge.org)

This purpose of this package is generating private **unfiltered** MC at GEN level.

Although it's completely okay to generate with standard CMSSW procedure, however...

* CMSSW is too heavy and what we want is just a small piece of function.

* Given the needed content is simple at GEN level, `TTree` post-processing procedure could be skipped with proper design.

Don't touch `evt.pdl` and `*.DEC`, they're copied from `CMSSW_5_3_X`, so the same configuration as CMS official is kept.

## Setup

The installation is tested on a clean lxplus session with `SCRAM_ARCH=slc7_amd64_gcc700`.

Just copy `setupEvtGen-R01-03-00.sh` to `${HOME}/local/EvtGen130/` and run the script to launch installation.

`EvtGen R01-03-00` will be installed, which is the official version used in recent CMSSW releases.

## Compile and Run

Just run `make` in commandline and the excutable `evtgen130_btokstarmumu` will be at hand.

* Heres are the implemented channels...

    * Generate 30M BToKstarMuMu events with `./evtgen130_btokstarmumu kstarll 30000000` 
    * Generate 30M BToKstarJpsi events with `./evtgen130_btokstarmumu kstarjpsi 30000000`

* It's better to use HTCondor service on lxplus for mass production with `condor_submit submit.jdl`.
