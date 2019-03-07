#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

import re
import functools
import itertools
from copy import copy
from array import array
import math

from anaSetup import q2bins, bMassRegions, cuts
from varCollection import dataArgs, CosThetaL, CosThetaK

from v2Fitter.Fitter.DataReader import DataReader
from v2Fitter.Fitter.ObjProvider import ObjProvider

import ROOT
from ROOT import TFile, TChain
from ROOT import TEfficiency, TH2D
from ROOT import RooArgList
from ROOT import RooDataHist

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels


CFG = {
    'name': "DataReaderTemplate",
    'ifile': [],
    'isData': True,
    'argset': dataArgs,
    'dataset':[]
}

# dataReader
CFG['name'] = "dataReader"
CFG['ifile'] = ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/*.root"]
dataReader = DataReader(copy(CFG))

# sigMCReader
CFG['name'] = "sigMCReader"
CFG['ifile'] = ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/SIG/*.root"]
CFG['isData'] = False
sigMCReader = DataReader(copy(CFG))

# effiHistReader
accXEffThetaLBins = array('d', [-1, -0.7, -0.3, 0., 0.3, 0.7, 1.])
accXEffThetaKBins = array('d', [-1, -0.7, 0., 0.4, 0.8, 1.])
def buildAccXRecEffiHist(self, targetBinKey, forceRebuild=False):
    """Build efficiency histogram for later fitting/plotting"""
    fin = self.process.filemanager.open("buildAccXRecEffiHist", "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/data/accXrecEffHists_Run2012.root", "UPDATE")
    for binKey in q2bins.keys():
        if binKey in ['test', 'jpsi', 'psi2s', 'peaks']: continue
        h2_accXrec = fin.Get("h2_accXrec_{0}".format(q2bins[binKey]['label']))

        if h2_accXrec == None or forceRebuild:
            h2_acc = fin.Get("h2_acc_{0}".format(q2bins[binKey]['label']))
            h2_rec = fin.Get("h2_rec_{0}".format(q2bins[binKey]['label']))

            # Fill histograms
            setupEfficiencyBuildProcedure = {}
            setupEfficiencyBuildProcedure['acc'] = {
                'ifiles': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/unfilteredSIG_genonly/*.root",],
                'baseString': re.sub("Mumumass", "sqrt(genQ2)", q2bins[binKey]['cutString']),
                'cutString': "fabs(genMupEta)<2.3 && fabs(genMumEta)<2.3 && genMupPt>2.8 && genMumPt>2.8",
                'fillXY': "genCosThetaK:genCosThetaL" # Y:X
            }
            setupEfficiencyBuildProcedure['rec'] = {
                'ifiles': sigMCReader.cfg['ifile'],
                'baseString': "{0}".format(setupEfficiencyBuildProcedure['acc']['baseString']),
                'cutString': "Bmass > 0.5 && ({0})".format(cuts[-1]),
                'fillXY': "genCosThetaK:genCosThetaL" # Y:X
            }
            for h2, label in (h2_acc, 'acc'), (h2_rec, 'rec'):
                if h2 == None or forceRebuild:
                    treein = TChain("tree")
                    for f in setupEfficiencyBuildProcedure[label]['ifiles']:
                        treein.Add(f)

                    treein.Draw(">>totEvtList", setupEfficiencyBuildProcedure[label]['baseString'])
                    totEvtList = ROOT.gDirectory.Get("totEvtList")
                    treein.SetEventList(totEvtList)
                    treein.Draw(">>accEvtList", setupEfficiencyBuildProcedure[label]['cutString'])
                    accEvtList = ROOT.gDirectory.Get("accEvtList")

                    h2_total      = TH2D("h2_{0}_{1}_total".format(label, q2bins[binKey]['label']), "", len(accXEffThetaLBins)-1, accXEffThetaLBins, len(accXEffThetaKBins)-1, accXEffThetaKBins)
                    h2_passed     = h2_total.Clone("h2_{0}_{1}_passed".format(label, q2bins[binKey]['label']))

                    h2_fine_total = TH2D("h2_{0}_fine_{1}_total".format(label, q2bins[binKey]['label']), "", 20, -1, 1, 20, -1, 1)
                    h2_fine_passed= h2_fine_total.Clone("h2_{0}_fine_{1}_passed".format(label, q2bins[binKey]['label']))

                    treein.SetEventList(totEvtList)
                    for hist in h2_total, h2_fine_total:
                        treein.Draw("{0}>>{1}".format(setupEfficiencyBuildProcedure[label]['fillXY'], hist.GetName()), "", "goff")

                    treein.SetEventList(accEvtList)
                    for hist in h2_passed, h2_fine_passed:
                        treein.Draw("{0}>>{1}".format(setupEfficiencyBuildProcedure[label]['fillXY'], hist.GetName()), "", "goff")

                    h2_eff = TEfficiency(h2_passed, h2_total)
                    h2_eff_fine = TEfficiency(h2_fine_passed, h2_fine_total)

                    fin.cd()
                    for proj, var in [("ProjectionX", CosThetaL), ("ProjectionY", CosThetaK)]:
                        proj_fine_total  = getattr(h2_fine_total, proj)(0,-1,"e")
                        proj_fine_passed = getattr(h2_fine_passed, proj)(0,-1,"e")
                        h_eff = TEfficiency(proj_fine_passed, proj_fine_total)
                        h_eff.Write("h_{0}_fine_{1}_{2}".format(label, q2bins[binKey]['label'], proj), ROOT.TObject.kOverwrite)

                    h2_eff.Write("h2_{0}_{1}".format(label, q2bins[binKey]['label']), ROOT.TObject.kOverwrite)
                    h2_eff_fine.Write("h2_{0}_fine_{1}".format(label, q2bins[binKey]['label']), ROOT.TObject.kOverwrite)

            # Merge acc and rec to accXrec
            fin.cd()
            for proj in ["ProjectionX", "ProjectionY"]:
                h_acc_fine = fin.Get("h_acc_fine_{0}_{1}".format(q2bins[binKey]['label'], proj))
                h_rec_fine = fin.Get("h_rec_fine_{0}_{1}".format(q2bins[binKey]['label'], proj))
                h_accXrec_fine = h_acc_fine.GetPassedHistogram().Clone("h_accXrec_fine_{0}_{1}".format(q2bins[binKey]['label'], proj))
                h_accXrec_fine.Reset("ICESM")
                for b in range(1, h_accXrec_fine.GetNbinsX()+1):
                    h_accXrec_fine.SetBinContent(b, h_acc_fine.GetEfficiency(b)*h_rec_fine.GetEfficiency(b))
                    h_accXrec_fine.SetBinError(b, h_accXrec_fine.GetBinContent(b)*math.sqrt(1/h_acc_fine.GetTotalHistogram().GetBinContent(b)+1/h_acc_fine.GetPassedHistogram().GetBinContent(b)+1/h_rec_fine.GetTotalHistogram().GetBinContent(b)+1/h_rec_fine.GetPassedHistogram().GetBinContent(b)))
                h_accXrec_fine.Write("h_accXrec_{0}_{1}".format(q2bins[binKey]['label'], proj), ROOT.TObject.kOverwrite)

            h2_acc = fin.Get("h2_acc_{0}".format(q2bins[binKey]['label']))
            h2_rec = fin.Get("h2_rec_{0}".format(q2bins[binKey]['label']))
            h2_accXrec = h2_acc.GetPassedHistogram().Clone("h2_accXrec_{0}".format(q2bins[binKey]['label']))
            h2_accXrec.Reset("ICESM")
            for iL, iK in itertools.product(range(1, len(accXEffThetaLBins)), range(1, len(accXEffThetaKBins))):
                if h2_rec.GetTotalHistogram().GetBinContent(iL, iK) == 0 or h2_rec.GetPassedHistogram().GetBinContent(iL, iK) == 0:
                    h2_accXrec.SetBinContent(iL, iK, 0)
                    h2_accXrec.SetBinError(iL, iK, 1)
                else:
                    iLK = h2_acc.GetGlobalBin(iL, iK)
                    h2_accXrec.SetBinContent(iL, iK, h2_acc.GetEfficiency(iLK)*h2_rec.GetEfficiency(iLK))
                    h2_accXrec.SetBinError(iL, iK, h2_accXrec.GetBinContent(iL, iK)*math.sqrt(1/h2_acc.GetTotalHistogram().GetBinContent(iLK)+1/h2_acc.GetPassedHistogram().GetBinContent(iLK)+1/h2_rec.GetTotalHistogram().GetBinContent(iLK)+1/h2_rec.GetPassedHistogram().GetBinContent(iLK)))
            h2_accXrec.SetXTitle("cos#theta_{l}")
            h2_accXrec.SetYTitle("cos#theta_{K}")
            h2_accXrec.SetZTitle("Overall efficiency")

            h2_accXrec.Write("h2_accXrec_{0}".format(q2bins[binKey]['label']), ROOT.TObject.kOverwrite)
            self.logger.logINFO("Overall efficiency is built.")

        if binKey == targetBinKey:
            self.cfg['source']['effiHistReader.h2_accXrec'] = h2_accXrec
            self.cfg['source']['effiHistReader.accXrec'] = RooDataHist("accXrec", "", RooArgList(CosThetaL, CosThetaK), ROOT.RooFit.Import(h2_accXrec))
            self.cfg['source']['effiHistReader.h_accXrec_fine_ProjectionX'] = fin.Get("h_accXrec_{0}_ProjectionX".format(q2bins[binKey]['label']))
            self.cfg['source']['effiHistReader.h_accXrec_fine_ProjectionY'] = fin.Get("h_accXrec_{0}_ProjectionY".format(q2bins[binKey]['label']))

def customizeOne(reader, binKey, dumpBMassRegion = []):
    """Define datasets with arguments."""
    if not binKey in q2bins.keys():
        print("ERROR\t: Bin {0} is not defined.\n".format(binKey))
        reader.cfg['dataset'] = []
        raise AttributeError

    # With shallow copied CFG, have to bind cfg['dataset'] to a new object.
    reader.cfg['dataset'] = []
    for key, val in bMassRegions.items():
        if key in dumpBMassRegion:
            continue
        reader.cfg['dataset'].append(
            (
                "{0}.{1}".format(reader.cfg['name'], key),
                "({0}) && ({1}) && ({2})".format(
                    val['cutString'],
                    q2bins[binKey]['cutString'],
                    cuts[-1],
                )
            )
        )

def customize(binKey, dumpBMassRegion = []):
    customizeOne(dataReader, binKey, dumpBMassRegion)
    customizeOne(sigMCReader, binKey, dumpBMassRegion)

    customizedBuildAccXRecEffiHist = functools.partial(buildAccXRecEffiHist, **{'targetBinKey': binKey if binKey != 'test' else 'summary'})
    global effiHistReader
    effiHistReader = ObjProvider({
        'name': "effiHistReader",
        'obj': {
            'effiHist': [customizedBuildAccXRecEffiHist,],
        }
    })


if __name__ == '__main__':
    customize('test')
    p = Process("testDataReaders", "testProcess")
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
    # p.setSequence([dataReader])
    p.setSequence([effiHistReader])
    p.beginSeq()
    p.runSeq()
    print(p.sourcemanager)
    p.endSeq()
