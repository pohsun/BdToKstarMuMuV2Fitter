#!/usr/bin/env python

import os
import ROOT
from SingleBuToKstarMuMuFitter.anaSetup import modulePath

for cls in ["EfficiencyFitter.cc", "StdFitter.cc", "RooBtosllModel.cxx"]:
    if os.path.exists(modulePath + '/cpp/' + cls.replace('.', '_') + '.so'):
        ROOT.gROOT.ProcessLineSync(".L {0}/cpp/{1}.so".format(modulePath, cls.replace('.', '_')))
    else:
        ROOT.gROOT.ProcessLineSync(".L {0}/cpp/{1}+".format(modulePath, cls))
