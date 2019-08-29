#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.toyCollection as toyCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection

from SingleBuToKstarMuMuFitter.StdProcess import p

# Standard fitting procedures
predefined_sequence = {}
predefined_sequence['loadData'] = [dataCollection.dataReader]
predefined_sequence['buildAllPdfs'] = [dataCollection.dataReader, pdfCollection.stdWspaceReader, pdfCollection.stdPDFBuilder]
predefined_sequence['buildEfficiecyHist'] = [dataCollection.effiHistReader]

predefined_sequence['fitEfficiency'] = [dataCollection.effiHistReader, pdfCollection.stdWspaceReader, fitCollection.effiFitter]
predefined_sequence['fitSigM'] = [dataCollection.sigMCReader, pdfCollection.stdWspaceReader, fitCollection.sigMFitter]
predefined_sequence['fitBkgCombA'] = [dataCollection.dataReader, pdfCollection.stdWspaceReader, fitCollection.bkgCombAFitter]
predefined_sequence['fitFinal3D'] = [dataCollection.dataReader, pdfCollection.stdWspaceReader, fitCollection.finalFitter]

predefined_sequence['stdFit'] = [dataCollection.effiHistReader, dataCollection.sigMCReader, dataCollection.dataReader, pdfCollection.stdWspaceReader, fitCollection.effiFitter, fitCollection.sigMFitter, fitCollection.bkgCombAFitter, fitCollection.sig2DFitter, fitCollection.finalFitter]

# For fitter validation and syst
predefined_sequence['fitSig2D'] = [dataCollection.sigMCReader, pdfCollection.stdWspaceReader, fitCollection.sig2DFitter]
predefined_sequence['fitSigMCGEN'] = [dataCollection.sigMCGENReader, pdfCollection.stdWspaceReader, fitCollection.sigAFitter]

if __name__ == '__main__':
    #  p.cfg['binKey'] = "belowJpsi"
    #  p.cfg['binKey'] = "betweenPeaks"
    #  p.cfg['binKey'] = "abovePsi2s"
    #  p.setSequence(predefined_sequence['fitEfficiency'])
    #  p.setSequence(predefined_sequence['fitBkgCombA'])
    #  p.setSequence(predefined_sequence['fitFinal3D'])
    p.setSequence(predefined_sequence['stdFit'])

    #  p.setSequence(predefined_sequence['fitSig2D'])
    #  p.setSequence(predefined_sequence['fitSigMCGEN'])
    try:
        p.beginSeq()
        p.runSeq()
    finally:
        p.endSeq()
