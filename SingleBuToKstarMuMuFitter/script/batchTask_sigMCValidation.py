#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 et:

import os
import sys
import shelve
import math
import glob
from subprocess import call
from copy import copy, deepcopy

from SingleBuToKstarMuMuFitter.anaSetup import q2bins
import SingleBuToKstarMuMuFitter.StdFitter as StdFitter
import v2Fitter.Batch.AbsBatchTaskWrapper as AbsBatchTaskWrapper

from SingleBuToKstarMuMuFitter.StdProcess import p
import ROOT
import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection
import v2Fitter.Fitter.AbsToyStudier as AbsToyStudier

# Define
ROOT.gROOT.ProcessLine(
"""struct MyTreeContent {
   Double_t     fl;
   Double_t     afb;
   Double_t     fs;
   Double_t     transAs;
   Double_t     nSig;
   Double_t     nBkgComb;
   Double_t     nll;
};""")
from ROOT import AddressOf

class SigMCStudier(AbsToyStudier.AbsToyStudier):
    """"""
    def getSubDataEntries(self, setIdx):
        try:
            db = shelve.open(self.process.dbplayer.odbfile)
            expectedYield = db['nSig']['getVal']
        finally:
            db.close()
        yields = ROOT.gRandom.Poisson(expectedYield)
        self.logger.logINFO("SubDataSet has expected yields {0} in set {1}".format(yields, setIdx))
        return yields

    def _preSetsLoop(self):
        self.otree = ROOT.TTree("tree", "")
        self.treeContent = ROOT.MyTreeContent()
        self.otree.Branch("fl", AddressOf(self.treeContent, 'fl'), 'fl/D')
        self.otree.Branch("afb", AddressOf(self.treeContent, 'afb'), 'afb/D')
        self.otree.Branch("fs", AddressOf(self.treeContent, 'fs'), 'fs/D')
        self.otree.Branch("transAs", AddressOf(self.treeContent, 'transAs'), 'as/D')
        self.otree.Branch("nSig", AddressOf(self.treeContent, 'nSig'), 'nSig/D')
        self.otree.Branch("nBkgComb", AddressOf(self.treeContent, 'nBkgComb'), 'nBkgComb/D')
        self.otree.Branch("nll", AddressOf(self.treeContent, 'nll'), 'nll/D')
        pass

    def _preRunFitSteps(self, setIdx):
        self.process.dbplayer.resetDB(True)  # Force same starting point

    def _postRunFitSteps(self, setIdx):
        if math.fabs(self.fitter._nll.getVal()) < 1e20:
            self.treeContent.fl = self.process.sourcemanager.get('fl').getVal()
            self.treeContent.afb = self.process.sourcemanager.get('afb').getVal()
            self.treeContent.fs = self.fitter.args.find('fs').getVal()
            self.treeContent.transAs = self.fitter.args.find('transAs').getVal()
            self.treeContent.nSig = 0
            self.treeContent.nBkgComb = 0
            self.treeContent.nll = self.fitter._nll.getVal()
            self.otree.Fill()

    def _postSetsLoop(self):
        ofile = ROOT.TFile("setSummary_{0}.root".format(q2bins[self.process.cfg['binKey']]['label']), 'RECREATE')
        ofile.cd()
        self.otree.Write()
        ofile.Close()

    getSubData = AbsToyStudier.getSubData_random

# Define Process
setupSigMCStudier = deepcopy(AbsToyStudier.AbsToyStudier.templateConfig())
setupSigMCStudier.update({
    'name': "sigMCStudier",
    'data': "sigMCReader.Fit",
    'fitter': fitCollection.sig2DFitter,
    'nSetOfToys': 100,
})
sigMCStudier = SigMCStudier(setupSigMCStudier)
fitCollection.sig2DFitter.cfg['data'] = "sigMCReader.Fit"

# Customize batch task

class BatchTaskWrapper(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
arguments = --binKey {binKey} run $(Process)
queue {nJobs}
""".format(binKey=parser_args.binKey, nJobs=self.cfg['nJobs'])
        return jdl

setupBatchTask = deepcopy(BatchTaskWrapper.templateCfg())
setupBatchTask.update({
    'nJobs': 20,
    'queue': "longlunch",
})

# Customize taskSubmitter and jobRunner if needed

# Postproc fit results.
def func_postproc(args):
    """ Fit to fit result and make plots """
    os.chdir(args.wrapper.task_dir)

    ifilename = "setSummary_{0}.root".format(q2bins[args.binKey]['label'])
    if not os.path.exists(ifilename) or args.forceHadd:
        call(["hadd", "-f", ifilename] + glob.glob('*/setSummary_{0}.root'.format(q2bins[args.binKey]['label'])))
    ifile = ROOT.TFile(ifilename)
    tree = ifile.Get("tree")

    binWidth = 0.01
    h_setSummary_afb = ROOT.TH1F("h_setSummary_afb", "", int(1.5 / binWidth), -0.75, 0.75)
    h_setSummary_fl = ROOT.TH1F("h_setSummary_fl", "", int(1. / binWidth), 0., 1.)

    tree.Draw("afb>>h_setSummary_afb")
    tree.Draw("fl>>h_setSummary_fl")

    f_setSummary_afb = ROOT.TF1("f_setSummary_afb", "gaus", -0.75 + binWidth, 0.75 - binWidth)
    h_setSummary_afb.Fit("f_setSummary_afb", "RL")

    f_setSummary_fl = ROOT.TF1("f_setSummary_fl", "gaus", binWidth, 1 - binWidth)
    h_setSummary_fl.Fit("f_setSummary_fl", "RL")

    # Draw
    db = shelve.open(os.path.join(p.dbplayer.absInputDir, "fitResults_{0}.db".format(q2bins[args.binKey]['label'])))
    fl_GEN = StdFitter.unboundFlToFl(db['unboundFl_GEN']['getVal'])
    afb_GEN = StdFitter.unboundAfbToAfb(db['unboundAfb_GEN']['getVal'], fl_GEN)
    line = ROOT.TLine()
    line.SetLineWidth(2)
    line.SetLineColor(2)
    line.SetLineStyle(10)
    plotCollection.Plotter.canvas.cd()

    h_setSummary_afb.SetXTitle("A_{FB}")
    h_setSummary_afb.SetYTitle("Number of test samples")
    h_setSummary_afb.SetFillColor(3)
    h_setSummary_afb.GetYaxis().SetRangeUser(0., 1.5 * h_setSummary_afb.GetMaximum())
    h_setSummary_afb.Draw()
    if args.drawGEN:
        line.DrawLine(afb_GEN, 0, afb_GEN, h_setSummary_afb.GetMaximum())
    plotCollection.Plotter.latexDataMarks(['sim'])
    plotCollection.Plotter.latexQ2(args.binKey)
    plotCollection.Plotter.latexLumi()
    plotCollection.Plotter.canvas.Print("h_setSummary_sigMCValidation_afb_{0}.pdf".format(q2bins[args.binKey]['label']))

    h_setSummary_fl.SetXTitle("F_{L}")
    h_setSummary_fl.SetYTitle("Number of test samples")
    h_setSummary_fl.SetFillColor(3)
    h_setSummary_fl.GetYaxis().SetRangeUser(0., 1.5 * h_setSummary_fl.GetMaximum())
    h_setSummary_fl.Draw()
    if args.drawGEN:
        line.DrawLine(fl_GEN, 0, fl_GEN, h_setSummary_fl.GetMaximum())
    plotCollection.Plotter.latexDataMarks(['sim'])
    plotCollection.Plotter.latexQ2(args.binKey)
    plotCollection.Plotter.latexLumi()
    plotCollection.Plotter.canvas.Print("h_setSummary_sigMCValidation_fl_{0}.pdf".format(q2bins[args.binKey]['label']))

    db.close()

if __name__ == '__main__':
    wrappedTask = BatchTaskWrapper(
        "myBatchTask",
        "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/batchTask_sigMCValidation",
        cfg=setupBatchTask)

    parser = AbsBatchTaskWrapper.BatchTaskParser
    parser.add_argument(
        '--binKey',
        dest="binKey",
        default="summary",
        help="Select q2 bin with binKey"
    )

    BatchTaskSubparserPostproc = AbsBatchTaskWrapper.BatchTaskSubparsers.add_parser('postproc')
    BatchTaskSubparserPostproc.add_argument(
        '--forceHadd',
        dest='forceHadd',
        action='store_true',
        help="Force recreate summary root file."
    )
    BatchTaskSubparserPostproc.add_argument(
        '--drawGEN',
        dest='drawGEN',
        action='store_false',
        help="Draw a line for GEN level value"
    )
    BatchTaskSubparserPostproc.set_defaults(
        func=func_postproc,
    )

    args = parser.parse_args()
    p.cfg['binKey'] = args.binKey
    if args.Function_name in ['run', 'submit']:
        p.setSequence([
            pdfCollection.stdWspaceReader,
            dataCollection.sigMCReader,
            sigMCStudier,
        ])
        wrappedTask = BatchTaskWrapper(
            "myBatchTask",
            "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/batchTask_sigMCValidation",
            cfg=setupBatchTask)
    else:
        wrapper = None

    parser.set_defaults(
        wrapper=wrappedTask,
        process=p
    )

    args = parser.parse_args()
    args.func(args)

    sys.exit()
