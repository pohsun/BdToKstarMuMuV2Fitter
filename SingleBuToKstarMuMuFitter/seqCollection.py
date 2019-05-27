#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels

from SingleBuToKstarMuMuFitter.anaSetup import processCfg
import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection
#  import SingleBuToKstarMuMuFitter.plotCollection as plotCollection

predefined_sequence = {}
predefined_sequence['loadData'] = [dataCollection.dataReader]
predefined_sequence['buildAllPdfs'] = [dataCollection.dataReader, pdfCollection.stdWspaceReader, pdfCollection.stdPDFBuilder]
predefined_sequence['buildEfficiecyHist'] = [dataCollection.effiHistReader]
predefined_sequence['fitEfficiency'] = [dataCollection.effiHistReader, pdfCollection.stdWspaceReader, fitCollection.effiFitter]
predefined_sequence['fitSigM'] = [dataCollection.sigMCReader, pdfCollection.stdWspaceReader, fitCollection.sigMFitter]
predefined_sequence['fitBkgCombA'] = [dataCollection.dataReader, pdfCollection.stdWspaceReader, fitCollection.bkgCombAFitter]
predefined_sequence['fitFinal3D'] = [dataCollection.dataReader, pdfCollection.stdWspaceReader, fitCollection.finalFitter]

# For fitter validation
predefined_sequence['fitSig2D'] = [dataCollection.sigMCReader, pdfCollection.stdWspaceReader, fitCollection.sig2DFitter]
predefined_sequence['fitSigMCGEN'] = [dataCollection.sigMCGENReader, pdfCollection.stdWspaceReader, fitCollection.sigAFitter]

# For systematics

p = Process("testSeqCollection", "testProcess", processCfg)
#  p.cfg['binKey'] = "belowJpsi"
#  p.cfg['binKey'] = "betweenPeaks"
#  p.cfg['binKey'] = "abovePsi2s"
p.logger.verbosityLevel = VerbosityLevels.DEBUG

#  p.setSequence(predefined_sequence['loadData'])

#  p.setSequence(predefined_sequence['buildEfficiecyHist'])
#  p.setSequence(predefined_sequence['buildAllPdfs'])

p.setSequence(predefined_sequence['fitEfficiency'])
#  p.setSequence(predefined_sequence['fitSigM'])
#  p.setSequence(predefined_sequence['fitBkgCombA'])
#  p.setSequence(predefined_sequence['fitFinal3D'])

#  p.setSequence(predefined_sequence['fitSigMCGEN'])  # Without efficiency correction
#  p.setSequence(predefined_sequence['fitSig2D'])  # With efficiency correction

if __name__ == '__main__':
    try:
        p.beginSeq()
        p.runSeq()
    finally:
        p.endSeq()
