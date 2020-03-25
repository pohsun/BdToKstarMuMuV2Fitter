#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.toyCollection as toyCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
from SingleBuToKstarMuMuFitter.StdProcess import p
from argparse import ArgumentParser

# Standard fitting procedures
predefined_sequence = {}
predefined_sequence['loadData'] = [dataCollection.dataReader]
predefined_sequence['buildAllPdfs'] = [dataCollection.dataReader, dataCollection.effiHistReader, pdfCollection.stdWspaceReader, pdfCollection.stdPDFBuilder]
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
    parser = ArgumentParser(prog='seqCollection')
    parser.add_argument('-b', '--binKey', dest='binKey', type=str, default=p.cfg['binKey'])
    parser.add_argument('-s', '--seq', dest='seqKey', type=str, default=None)
    args = parser.parse_args()

    if args.binKey in anaSetup.q2bins.keys():
        p.cfg['binKey'] = args.binKey
    else:
        raise KeyError("Unknown binKey. Pick from {0}".format(anaSetup.q2bins.keys()))

    if args.seqKey is not None:
        if args.seqKey in predefined_sequence.keys():
            p.setSequence(predefined_sequence[args.seqKey])
        else:
            raise KeyError("Unknown setSequence. Pick from {0}".format(predefined_sequence.keys()))
    else:
        if args.binKey not in ['jpsi', 'psi2s']:
            p.setSequence(predefined_sequence['stdFit'])
        else:
            p.setSequence([dataCollection.effiHistReader, dataCollection.bkgJpsiMCReader, dataCollection.bkgPsi2sMCReader, dataCollection.dataReader, pdfCollection.stdWspaceReader, fitCollection.effiFitter])

    try:
        p.beginSeq()
        p.runSeq()
    finally:
        p.endSeq()
