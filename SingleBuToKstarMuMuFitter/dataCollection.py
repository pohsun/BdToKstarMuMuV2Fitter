#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=0 fdn=2 ft=python et:

import re
import types
import functools
import itertools
from array import array
from copy import copy
import math

import SingleBuToKstarMuMuFitter.cpp

from v2Fitter.Fitter.DataReader import DataReader
from v2Fitter.Fitter.ObjProvider import ObjProvider
from SingleBuToKstarMuMuFitter.varCollection import dataArgs, Bmass, CosThetaL, CosThetaK, Kshortmass, dataArgsGEN
from SingleBuToKstarMuMuFitter.anaSetup import q2bins, bMassRegions, cuts, cuts_noResVeto, cuts_antiResVeto, cut_kshortWindow, modulePath

import ROOT
from ROOT import TChain
from ROOT import TEfficiency, TH2D
from ROOT import RooArgList
from ROOT import RooDataHist

from SingleBuToKstarMuMuFitter.StdProcess import p

CFG = DataReader.templateConfig()
CFG.update({
    'argset': dataArgs,
    'lumi': -1,  # Keep a record, useful for mixing simulations samples
    'ifriendIndex': ["Bmass", "Mumumass"],
})

# dataReader
def customizeOne(self, targetBMassRegion=None, extraCuts=None):
    """Define datasets with arguments."""
    if targetBMassRegion is None:
        targetBMassRegion = []
    if not self.process.cfg['binKey'] in q2bins.keys():
        self.logger.logERROR("Bin {0} is not defined.\n".format(self.process.cfg['binKey']))
        raise ValueError

    # With shallow copied CFG, have to bind cfg['dataset'] to a new object.
    self.cfg['dataset'] = []
    for key, val in bMassRegions.items():
        if any([re.match(pat, key) for pat in targetBMassRegion]):
            self.cfg['dataset'].append(
                (
                    "{0}.{1}".format(self.cfg['name'], key),
                    "({0}) && ({1}) && ({2}) && ({3})".format(
                        val['cutString'],
                        q2bins[self.process.cfg['binKey']]['cutString'],
                        cuts[-1],
                        "1" if not extraCuts else extraCuts,
                    )
                )
            )

    # Additional Fit_noResVeto, Fit_antiResVeto for resonance
    if "noResVeto" in targetBMassRegion:
            self.cfg['dataset'].append(
                (
                    "{0}.Fit_noResVeto".format(self.cfg['name'], key),
                    "({0}) && ({1}) && ({2}) && ({3})".format(
                        bMassRegions['Fit']['cutString'],
                        q2bins[self.process.cfg['binKey']]['cutString'],
                        cuts_noResVeto,
                        "1" if not extraCuts else extraCuts,
                    )
                )
            )

    if "antiResVeto" in targetBMassRegion:
            self.cfg['dataset'].append(
                (
                    "{0}.Fit_antiResVeto".format(self.cfg['name'], key),
                    "({0}) && ({1}) && ({2}) && ({3})".format(
                        bMassRegions['Fit']['cutString'],
                        q2bins[self.process.cfg['binKey']]['cutString'],
                        cuts_antiResVeto,
                        "1" if not extraCuts else extraCuts,
                    )
                )
            )
    
    # Customize preload TFile
    if self.cfg['preloadFile']:
        self.cfg['preloadFile'] = self.cfg['preloadFile'].format(binLabel=q2bins[self.process.cfg['binKey']]['label'])

dataReaderCfg = copy(CFG)
dataReaderCfg.update({
    'name': "dataReader",
    'ifile': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/ANv21/DATA/sel_*.root"],
    #  'ifriend': ["/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/script/plotMatchCandPreSelector.root"],
    'preloadFile': modulePath + "/data/preload_dataReader_{binLabel}.root",
    'lumi': 19.98,
})
dataReader = DataReader(dataReaderCfg)
customizeData = functools.partial(customizeOne, targetBMassRegion=['.*', 'noResVeto', 'antiResVeto'], extraCuts=cut_kshortWindow)
dataReader.customize = types.MethodType(customizeData, dataReader)

# sigMCReader
sigMCReaderCfg = copy(CFG)
sigMCReaderCfg.update({
    'name': "sigMCReader",
    'ifile': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/ANv21/SIG/sel_*.root"],
    'preloadFile': modulePath + "/data/preload_sigMCReader_{binLabel}.root",
    'lumi': 16281.440 + 21097.189,
})
sigMCReader = DataReader(sigMCReaderCfg)
customizeSigMC = functools.partial(customizeOne, targetBMassRegion=['^Fit$'])  # Assuming cut_kshortWindow makes no impact
sigMCReader.customize = types.MethodType(customizeSigMC, sigMCReader)

# peakBkgMCReader
bkgJpsiMCReaderCfg = copy(CFG)
bkgJpsiMCReaderCfg.update({
    'name': "bkgJpsiMCReader",
    'ifile': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/ANv21/JPSI/sel_*.root"],
    'preloadFile': modulePath + "/data/preload_bkgJpsiMCReader_{binLabel}.root",
    'lumi': 295.761,
})
bkgJpsiMCReader = DataReader(bkgJpsiMCReaderCfg)
customizeBkgPeakMC = functools.partial(customizeOne, targetBMassRegion=['^Fit$', 'noResVeto', 'antiResVeto'])
bkgJpsiMCReader.customize = types.MethodType(customizeBkgPeakMC, bkgJpsiMCReader)

bkgPsi2sMCReaderCfg = copy(CFG)
bkgPsi2sMCReaderCfg.update({
    'name': "bkgPsi2sMCReader",
    'ifile': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/ANv21/PSIP/sel_*.root"],
    'preloadFile': modulePath + "/data/preload_bkgPsi2sMCReader_{binLabel}.root",
    'lumi': 218.472,
})
bkgPsi2sMCReader = DataReader(bkgPsi2sMCReaderCfg)
bkgPsi2sMCReader.customize = types.MethodType(customizeBkgPeakMC, bkgPsi2sMCReader)

# sigMCGENReader
def customizeGEN(self):
    """Define datasets with arguments."""
    if not self.process.cfg['binKey'] in q2bins.keys():
        print("ERROR\t: Bin {0} is not defined.\n".format(self.process.cfg['binKey']))
        raise AttributeError

    # With shallow copied CFG, have to bind cfg['dataset'] to a new object.
    self.cfg['dataset'] = []
    self.cfg['dataset'].append(
        (
            "{0}.Fit".format(self.cfg['name']),
            re.sub("Mumumass", "sqrt(genQ2)", q2bins[self.process.cfg['binKey']]['cutString'])
        )
    )

    # Customize preload TFile
    if self.cfg['preloadFile']:
        self.cfg['preloadFile'] = self.cfg['preloadFile'].format(binLabel=q2bins[self.process.cfg['binKey']]['label'])

sigMCGENReaderCfg = copy(CFG)
sigMCGENReaderCfg.update({
    'name': "sigMCGENReader",
    'ifile': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/unfilteredSIG_genonly/sel_*.root"],
    'preloadFile': modulePath + "/data/preload_sigMCGENReader_{binLabel}.root",
    'argset': dataArgsGEN,
})
sigMCGENReader = DataReader(sigMCGENReaderCfg)
sigMCGENReader.customize = types.MethodType(customizeGEN, sigMCGENReader)

# effiHistReader
accXEffThetaLBins = array('d', [-1, -0.7, -0.3, 0., 0.3, 0.7, 1.])
accXEffThetaKBins = array('d', [-1, -0.7, 0., 0.4, 0.8, 1.])
rAccXEffThetaLBins= ROOT.RooBinning(6, accXEffThetaLBins, "rAccXEffThetaLBins")
rAccXEffThetaKBins= ROOT.RooBinning(5, accXEffThetaKBins, "rAccXEffThetaKBins")
def buildAccXRecEffiHist(self):
    """Build efficiency histogram for later fitting/plotting"""
    targetBins = ['belowJpsi', 'betweenPeaks', 'abovePsi2s', 'summary', 'jpsi']
    if self.process.cfg['binKey'] not in targetBins:
        return

    fin = self.process.filemanager.open("buildAccXRecEffiHist", modulePath + "/data/accXrecEffHists_Run2012.root", "UPDATE")

    # Build acceptance, reco efficiency, and accXrec
    forceRebuild = False

    binKey = self.process.cfg['binKey']
    h2_accXrec = fin.Get("h2_accXrec_{0}".format(binKey))
    if h2_accXrec == None or forceRebuild:
        h2_acc = fin.Get("h2_acc_{0}".format(binKey))
        h2_rec = fin.Get("h2_rec_{0}".format(binKey))

        # Fill histograms
        setupEfficiencyBuildProcedure = {}
        setupEfficiencyBuildProcedure['acc'] = {
            'ifiles': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/unfilteredJPSI_genonly/*.root", ] if binKey in ['jpsi', 'psi2s'] else ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/unfilteredSIG_genonly/*.root", ],
            'baseString': re.sub("Mumumass", "sqrt(genQ2)", q2bins[binKey]['cutString']),
            'cutString': "fabs(genMupEta)<2.3 && fabs(genMumEta)<2.3 && genMupPt>2.8 && genMumPt>2.8",
            'fillXY': "genCosThetaK:genCosThetaL",  # Y:X
            'weight': None
        }
        setupEfficiencyBuildProcedure['rec'] = {
            'ifiles': {'jpsi': bkgJpsiMCReader.cfg['ifile'], 'psi2s': bkgPsi2sMCReader.cfg['ifile']}.get(binKey, sigMCReader.cfg['ifile']),
            'baseString': "{0}".format(setupEfficiencyBuildProcedure['acc']['baseString']),
            'cutString': "Bmass > 0.5 && ({0})".format(cuts_antiResVeto if binKey in ['jpsi', 'psi2s'] else cuts[-1]),
            'fillXY': "genCosThetaK:genCosThetaL",  # Y:X
            'weight': None
        }
        for h2, label in (h2_acc, 'acc'), (h2_rec, 'rec'):
            if h2 == None or forceRebuild:
                treein = TChain("tree")
                for f in setupEfficiencyBuildProcedure[label]['ifiles']:
                    treein.Add(f)

                if setupEfficiencyBuildProcedure[label]['weight'] is None:
                    df_tot = ROOT.RDataFrame(treein).Define('weight', "1").Filter(setupEfficiencyBuildProcedure[label]['baseString'])
                else:
                    df_tot = ROOT.RDataFrame(treein).Define('weight', *setupEfficiencyBuildProcedure[label]['weight']).Filter(setupEfficiencyBuildProcedure[label]['baseString'])
                df_acc = df_tot.Filter(setupEfficiencyBuildProcedure[label]['cutString'])

                fillXY = setupEfficiencyBuildProcedure[label]['fillXY'].split(':')
                h2_total_config = ("h2_{0}_{1}_total".format(label, binKey), "", len(accXEffThetaLBins) - 1, accXEffThetaLBins, len(accXEffThetaKBins) - 1, accXEffThetaKBins)
                h2_passed_config  = ("h2_{0}_{1}_passed".format(label, binKey), "", len(accXEffThetaLBins) - 1, accXEffThetaLBins, len(accXEffThetaKBins) - 1, accXEffThetaKBins)
                h2_fine_total_config = ("h2_{0}_fine_{1}_total".format(label, binKey), "", 20, -1, 1, 20, -1, 1)
                h2_fine_passed_config = ("h2_{0}_fine_{1}_passed".format(label, binKey), "", 20, -1, 1, 20, -1, 1)

                h2ptr_total = df_tot.Histo2D(h2_total_config, fillXY[1], fillXY[0], "weight")
                h2ptr_passed = df_acc.Histo2D(h2_passed_config, fillXY[1], fillXY[0], "weight")
                h2ptr_fine_total = df_tot.Histo2D(h2_fine_total_config, fillXY[1], fillXY[0], "weight")
                h2ptr_fine_passed = df_acc.Histo2D(h2_fine_passed_config, fillXY[1], fillXY[0], "weight")

                h2_total = h2ptr_total.GetValue()
                h2_passed = h2ptr_passed.GetValue()
                h2_fine_total = h2ptr_fine_total.GetValue()
                h2_fine_passed = h2ptr_fine_passed.GetValue()

                print("{0}/{1}".format(df_acc.Count().GetValue(), df_tot.Count().GetValue()))
                h2_eff = TEfficiency(h2_passed, h2_total)
                h2_eff_fine = TEfficiency(h2_fine_passed, h2_fine_total)

                fin.cd()
                for proj, var in [("ProjectionX", CosThetaL), ("ProjectionY", CosThetaK)]:
                    proj_fine_total = getattr(h2_fine_total, proj)("{0}_{1}".format(h2_fine_total.GetName(), proj), 0, -1, "e")
                    proj_fine_passed = getattr(h2_fine_passed, proj)("{0}_{1}".format(h2_fine_passed.GetName(), proj), 0, -1, "e")
                    h_eff = TEfficiency(proj_fine_passed, proj_fine_total)
                    h_eff.Write("h_{0}_fine_{1}_{2}".format(label, binKey, proj), ROOT.TObject.kOverwrite)

                h2_eff.Write("h2_{0}_{1}".format(label, binKey), ROOT.TObject.kOverwrite)
                h2_eff_fine.Write("h2_{0}_fine_{1}".format(label, binKey), ROOT.TObject.kOverwrite)

                del df_acc, df_tot

        # Merge acc and rec to accXrec
        fin.cd()
        for proj in ["ProjectionX", "ProjectionY"]:
            h_acc_fine = fin.Get("h_acc_fine_{0}_{1}".format(binKey, proj))
            h_rec_fine = fin.Get("h_rec_fine_{0}_{1}".format(binKey, proj))
            h_accXrec_fine = h_acc_fine.GetPassedHistogram().Clone("h_accXrec_fine_{0}_{1}".format(binKey, proj))
            h_accXrec_fine.Reset("ICESM")
            for b in range(1, h_accXrec_fine.GetNbinsX() + 1):
                h_accXrec_fine.SetBinContent(b, h_acc_fine.GetEfficiency(b) * h_rec_fine.GetEfficiency(b))
                h_accXrec_fine.SetBinError(b, h_accXrec_fine.GetBinContent(b) * math.sqrt(1 / h_acc_fine.GetTotalHistogram().GetBinContent(b) + 1 / h_acc_fine.GetPassedHistogram().GetBinContent(b) + 1 / h_rec_fine.GetTotalHistogram().GetBinContent(b) + 1 / h_rec_fine.GetPassedHistogram().GetBinContent(b)))
            h_accXrec_fine.Write("h_accXrec_{0}_{1}".format(binKey, proj), ROOT.TObject.kOverwrite)

        h2_acc = fin.Get("h2_acc_{0}".format(binKey))
        h2_rec = fin.Get("h2_rec_{0}".format(binKey))
        h2_accXrec = h2_acc.GetPassedHistogram().Clone("h2_accXrec_{0}".format(binKey))
        h2_accXrec.Reset("ICESM")
        for iL, iK in itertools.product(range(1, len(accXEffThetaLBins)), range(1, len(accXEffThetaKBins))):
            if h2_rec.GetTotalHistogram().GetBinContent(iL, iK) == 0 or h2_rec.GetPassedHistogram().GetBinContent(iL, iK) == 0:
                h2_accXrec.SetBinContent(iL, iK, 0)
                h2_accXrec.SetBinError(iL, iK, 1)
            else:
                iLK = h2_acc.GetGlobalBin(iL, iK)
                h2_accXrec.SetBinContent(iL, iK, h2_acc.GetEfficiency(iLK) * h2_rec.GetEfficiency(iLK))
                h2_accXrec.SetBinError(iL, iK, h2_accXrec.GetBinContent(iL, iK) * math.sqrt(1 / h2_acc.GetTotalHistogram().GetBinContent(iLK) + 1 / h2_acc.GetPassedHistogram().GetBinContent(iLK) + 1 / h2_rec.GetTotalHistogram().GetBinContent(iLK) + 1 / h2_rec.GetPassedHistogram().GetBinContent(iLK)))
        h2_accXrec.SetXTitle("cos#theta_{l}")
        h2_accXrec.SetYTitle("cos#theta_{K}")
        h2_accXrec.SetZTitle("Overall efficiency")

        h2_accXrec.Write("h2_accXrec_{0}".format(binKey), ROOT.TObject.kOverwrite)
        self.logger.logINFO("Overall efficiency is built.")

    # Register the chosen one to sourcemanager
    #  h2_accXrec = fin.Get("h2_accXrec_{0}".format(self.process.cfg['binKey']))
    self.cfg['source'][self.name + '.h2_accXrec'] = h2_accXrec
    self.cfg['source'][self.name + '.accXrec'] = RooDataHist("accXrec", "", RooArgList(CosThetaL, CosThetaK), ROOT.RooFit.Import(h2_accXrec))
    self.cfg['source'][self.name + '.h_accXrec_fine_ProjectionX'] = fin.Get("h_accXrec_{0}_ProjectionX".format(self.process.cfg['binKey']))
    self.cfg['source'][self.name + '.h_accXrec_fine_ProjectionY'] = fin.Get("h_accXrec_{0}_ProjectionY".format(self.process.cfg['binKey']))

effiHistReader = ObjProvider({
    'name': "effiHistReader",
    'obj': {
        'effiHistReader.h2_accXrec': [buildAccXRecEffiHist, ],
    }
})

if __name__ == '__main__':
    # p.setSequence([dataReader])
    # p.setSequence([sigMCReader])
    # p.setSequence([effiHistReader])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
