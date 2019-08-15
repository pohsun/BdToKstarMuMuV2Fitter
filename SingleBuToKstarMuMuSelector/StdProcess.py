#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 ft=python fdm=indent fdl=0 fdn=3 et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

from __future__ import print_function, division
from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels

import ROOT
ROOT.gROOT.SetBatch(True)

# Shared global settings
isDEBUG = True

# RooMsgService settings
# Suppress all message below error during minimization to keep short log file.
msgService = ROOT.RooMsgService.instance()
msgService.getStream(0).removeTopic(64)  # Eval
msgService.getStream(0).removeTopic(4)  # Plotting
msgService.getStream(0).removeTopic(2)  # Minimization
msgService.getStream(1).removeTopic(64)
msgService.getStream(1).removeTopic(4)
msgService.getStream(1).removeTopic(2)
msgService.addStream(4,
                     #  ROOT.RooFit.Topic(64),
                     ROOT.RooFit.Topic(4),
                     ROOT.RooFit.Topic(2))

# default configuration for Process
processCfg = {
    'isBatchJob': False,
}
p = Process("myProcess", "testProcess", processCfg)

# Developers Area
if isDEBUG:
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
