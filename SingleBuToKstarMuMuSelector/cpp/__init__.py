#!/usr/bin/env python

import os
import ROOT

modulePath = os.path.abspath(os.path.dirname(__file__))
for cls in ["SingleBuToKstarMuMuSelector.C", "StdOptimizerPlugin.C"]:
    if os.path.exists(modulePath + '/' + cls.replace('.', '_') + '.so'):
        ROOT.gROOT.ProcessLineSync(".L {0}/{1}.so".format(modulePath, cls.replace('.', '_')))
    else:
        ROOT.gROOT.ProcessLineSync(".L {0}/{1}+".format(modulePath, cls))
