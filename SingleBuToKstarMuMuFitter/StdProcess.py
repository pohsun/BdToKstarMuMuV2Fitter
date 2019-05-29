#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

from __future__ import print_function, division
import os
import ROOT
ROOT.gROOT.SetBatch(True)

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer

# Shared global settings
isDEBUG = True

# default configuration for Process
processCfg = {
    'isBatchJob': False,
    'binKey': 'summary',
}
p = Process("myProcess", "testProcess", processCfg)

dbplayer = FitDBPlayer(inputDir=os.path.join(anaSetup.modulePath, "input", "selected"))
p.addService("dbplayer", dbplayer)

# Developers Area
if isDEBUG:
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
