#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=0 fdn=1 et:

import os
import sys
import re
import math
import shelve
import types
import functools
import itertools
from datetime import datetime
from copy import copy, deepcopy

from SingleBuToKstarMuMuFitter.anaSetup import q2bins
import SingleBuToKstarMuMuFitter.StdFitter as StdFitter
import v2Fitter.Batch.AbsBatchTaskWrapper as AbsBatchTaskWrapper

from SingleBuToKstarMuMuFitter.StdProcess import p
import ROOT
import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.toyCollection as toyCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection
import v2Fitter.Fitter.AbsToyStudier as AbsToyStudier

# Define toyStudier and profilers
# Ref:
#   https://root.cern.ch/how/how-write-ttree-python
#   https://github.com/root-project/root/blob/master/tutorials/pyroot/staff.py
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

class ProfiledFCToyStudier(AbsToyStudier.AbsToyStudier):
    """"""
    def getSubDataEntries(self, setIdx):
        expectedYield = 0
        try:
            db = shelve.open(self.process.dbplayer.odbfile)
            expectedYield += db['nSig']['getVal']
            expectedYield += db['nBkgComb']['getVal']
        finally:
            db.close()
        yields = ROOT.gRandom.Poisson(expectedYield)
        self.logger.logINFO("SubDataSet has expected yields {0} in set {1}".format(yields, setIdx))
        return yields

    def _preSetsLoop(self):
        """ Just build a tree to keep information of each set of toy """
        self.otree = ROOT.TTree("tree", "")
        self.treeContent = ROOT.MyTreeContent()
        self.otree.Branch("fl", AddressOf(self.treeContent, 'fl'), 'fl/D')
        self.otree.Branch("afb", AddressOf(self.treeContent, 'afb'), 'afb/D')
        self.otree.Branch("fs", AddressOf(self.treeContent, 'fs'), 'fs/D')
        self.otree.Branch("transAs", AddressOf(self.treeContent, 'transAs'), 'as/D')
        self.otree.Branch("nSig", AddressOf(self.treeContent, 'nSig'), 'nSig/D')
        self.otree.Branch("nBkgComb", AddressOf(self.treeContent, 'nBkgComb'), 'nBkgComb/D')
        self.otree.Branch("nll", AddressOf(self.treeContent, 'nll'), 'nll/D')

    def _preRunFitSteps(self, setIdx):
        # Do nothing, there's no need to reset input db file.
        # It should be fine enough to start from previous fit result.
        pass

    def _postRunFitSteps(self, setIdx):
        """ Fill information to otree """
        if math.fabs(self.fitter._nll.getVal()) < 1e20:
            unboundAfb = self.fitter.args.find('unboundAfb').getVal()
            unboundFl = self.fitter.args.find('unboundFl').getVal()
            self.treeContent.fl = StdFitter.unboundFlToFl(unboundFl)
            self.treeContent.afb = StdFitter.unboundAfbToAfb(unboundAfb, self.treeContent.fl)
            self.treeContent.fs = self.fitter.args.find('fs').getVal()
            self.treeContent.transAs = self.fitter.args.find('transAs').getVal()
            self.treeContent.nSig = self.fitter.args.find('nSig').getVal()
            self.treeContent.nBkgComb = self.fitter.args.find('nBkgComb').getVal()
            self.treeContent.nll = self.fitter._nll.getVal()
            self.otree.Fill()

    def _runSetsLoop(self):
        """Customization: No force reset initial db file"""
        # Check if profiling gives valid result
        self.process.dbplayer.resetDB(False)
        for iSet in range(self.cfg['nSetOfToys']):
            self.fitter.hookProcess(self.process)
            self.fitter.customize()
            self.currentSubDataEntries = self.getSubDataEntries(iSet)
            self.fitter.pdf = self.process.sourcemanager.get(self.fitter.cfg['pdf'])
            self.fitter.data = self.getSubData().next()
            self.fitter._bookMinimizer()
            self.fitter._preFitSteps()
            self.fitter._runFitSteps()  # Don't run fitter._postRunFitSteps, db will be overwritten
            self._postRunFitSteps(iSet)
            self.fitter.reset()

    def _postSetsLoop(self):
        """ Write otree to a file """
        ofile = ROOT.TFile("setSummary_{0}.root".format(q2bins[self.process.cfg['binKey']]['label']), 'RECREATE')
        ofile.cd()
        self.otree.Write()
        ofile.Close()

    getSubData = AbsToyStudier.getSubData_random

setupProfiledFCToyStudier = deepcopy(AbsToyStudier.AbsToyStudier.templateConfig())
setupProfiledFCToyStudier.update({
    'name': "profiledFCToyStudier",
    'data': "ToyGenerator.mixedToy",
    'fitter': fitCollection.finalFitter,
    'nSetOfToys': 100,  # Typically 100 Toys * 5 submissions for acceptable precision, in proportion to generating time.
})
profiledFCToyStudier = ProfiledFCToyStudier(setupProfiledFCToyStudier)

setupProfiler = deepcopy(fitCollection.setupFinalFitter)
profiler = StdFitter.StdFitter(setupProfiler)
profiler.name = "profiler"

# Customize batch task

class BatchTaskWrapper(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
JobBatchName = "{JobBatchName}_{binKey}"
arguments = --binKey {binKey} run $(Process)
queue {nJobs}
""".format(
        JobBatchName="FCBatch",
        binKey=parser_args.binKey, 
        nJobs=self.cfg['nJobs'])
        return jdl

setupBatchTask = deepcopy(BatchTaskWrapper.templateCfg())
setupBatchTask.update({
    'nJobs': 1,  # Fix to 1 for profiledFCToyStudier.cfg['nSetOfToys'] sets of toys
    'queue': "workday",
})

class BatchTaskWrapperProfile(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
JobBatchName = "{JobBatchName}_{binKey}"
arguments = --binKey {binKey} run_profile $(Process)
queue {nJobs}
""".format(
        JobBatchName="FCProfile",
        binKey=parser_args.binKey, 
        nJobs=self.cfg['nJobs'])
        return jdl

setupBatchTaskProfile = deepcopy(BatchTaskWrapper.templateCfg())
setupBatchTaskProfile.update({
    'nJobs': 1,
    'queue': "espresso",
})

class BatchTaskWrapperBestFit(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
JobBatchName = "{JobBatchName}_{binKey}"
arguments = --binKey {binKey} run_bestFit $(Process)
queue {nJobs}
""".format(
        JobBatchName="FCBest",
        binKey=parser_args.binKey,
        nJobs=self.cfg['nJobs'])
        return jdl

setupBatchTaskBestFit = deepcopy(BatchTaskWrapper.templateCfg())
setupBatchTaskBestFit.update({
    'nJobs': 1,  # Fix to 1 for profiledFCToyStudier.cfg['nSetOfToys'] sets of toys
    'queue': "workday",
})

if __name__ == '__main__':
    # First create all profiling point...
    task_dir = "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/batchTask_profiledFeldmanCousins"

    for iAfbSet in range(150):
        try:
            os.makedirs("{0}/afb{1:+.3f}".format(task_dir, 0.01 * iAfbSet - 0.745))
        except OSError:
            pass
    for iFlSet in range(100):
        try:
            os.makedirs("{0}/fl{1:+.3f}".format(task_dir, 0.01 * iFlSet + 0.005))
        except OSError:
            pass
    profilePoints = [d for d in os.listdir(task_dir) if re.match(r"^(afb|fl)[+-]0\.\d{3}$", d)]

    parser = AbsBatchTaskWrapper.BatchTaskParser
    parser.add_argument(
        '--binKey',
        dest="binKey",
        default="summary",
        help="Select q2 bin with binKey"
    )

    BatchTaskSubparserSubmitProfile = AbsBatchTaskWrapper.copyAndRegSubparser(AbsBatchTaskWrapper.BatchTaskSubparsers, 'submit', 'submit_profile')
    BatchTaskSubparserSubmitProfile.set_defaults(func=AbsBatchTaskWrapper.submitTask)

    BatchTaskSubparserRunProfile = AbsBatchTaskWrapper.copyAndRegSubparser(AbsBatchTaskWrapper.BatchTaskSubparsers, 'run', 'run_profile')
    BatchTaskSubparserRunProfile.set_defaults(func=AbsBatchTaskWrapper.runJob)

    BatchTaskSubparserSubmitBestFit = AbsBatchTaskWrapper.copyAndRegSubparser(AbsBatchTaskWrapper.BatchTaskSubparsers, 'submit', 'submit_bestFit')
    BatchTaskSubparserSubmitBestFit.set_defaults(func=AbsBatchTaskWrapper.submitTask)
    
    BatchTaskSubparserRunBestFit = AbsBatchTaskWrapper.copyAndRegSubparser(AbsBatchTaskWrapper.BatchTaskSubparsers, 'run', 'run_bestFit')
    BatchTaskSubparserRunBestFit.set_defaults(func=AbsBatchTaskWrapper.runJob)

    args = parser.parse_args()
    p.cfg['binKey'] = args.binKey

    if args.Function_name in ["submit_profile", "run_profile"]:
        if args.Function_name == "run_profile":
            print("INFO\t: Profiling job {1} with {0}".format(profilePoints[args.jobId], args.jobId))
            parseProfilePoint = re.match(r'(afb|fl)([+-]0\.\d{3})', profilePoints[args.jobId])
            constrained_var, constrained_val = parseProfilePoint.group(1), float(parseProfilePoint.group(2))
            print(constrained_var, constrained_val)

            @StdFitter.decorator_bookMinimizer_addGausConstraints([constrained_var], [constrained_val])
            def customized_bookMinimizer(self):
                StdFitter.StdFitter._bookMinimizer(self)
            profiler._bookMinimizer = types.MethodType(customized_bookMinimizer, profiler)

            def customized_preFitSteps_preFit(self, var, val):
                """ Set proper initial value to reasonable region."""
                unboundAfb = self.args.find("unboundAfb")
                unboundFl = self.args.find("unboundFl")
                if var == "afb":
                    for iFl in range(1, 20):
                        unboundAfb.setVal(StdFitter.afbToUnboundAfb(val, (1. - 1.33 * math.fabs(val)) / 20. * (20. - iFl)))
                        unboundFl.setVal(StdFitter.flToUnboundFl((1. - 1.33 * math.fabs(val)) / 20. * (20. - iFl)))
                        self.FitMigrad()
                        if math.fabs(self._nll.getVal()) < 1e20:
                            break
                elif var == "fl":
                    unboundFl.setVal(StdFitter.flToUnboundFl(val))
                    unboundFl.setConstant(True)
                    for iAfb in list(itertools.chain(*[(i, -i) for i in range(-9, 0)])):
                        unboundAfb.setVal(StdFitter.afbToUnboundAfb(0.75 * (1. - val) / 10. * iAfb, val))
                        self.FitMigrad()
                        if math.fabs(self._nll.getVal()) < 1e20:
                            break
            profiler._preFitSteps_preFit = types.MethodType(functools.partial(customized_preFitSteps_preFit, var=constrained_var, val=constrained_val), profiler)


            def customized_postFitSteps(self):
                """ Leave a log file for skipping failed profiling """
                StdFitter.StdFitter._postFitSteps(self)
                self.process.sourcemanager.get('afb').Print()
                self.process.sourcemanager.get('fl').Print()
                if self.fitResult['profiler.migrad']['status'] != 0 or math.fabs(self.fitResult['profiler.minos']['nll']) > 1e20:
                    with open("failed_in_profile_{0}.txt".format(q2bins[self.process.cfg['binKey']]['label']), 'w') as f:
                        try:
                            db = shelve.open(self.process.dbplayer.odbfile)
                            f.write(db.__repr__().replace("}", "\n"))
                        finally:
                            db.close()
            profiler._postFitSteps = types.MethodType(customized_postFitSteps, profiler)

            plotCollection.plotter.cfg['switchPlots'] = ['simpleBLK']
            plotCollection.plotter.cfg['plots']['simpleBLK']['kwargs'].update({
                'dataPlots': [["dataReader.Fit", ()], ],
                'pdfPlots': [["f_final", plotCollection.plotterCfg_allStyle],
                             ["f_final", (ROOT.RooFit.Components('f_sig3D'), ) + plotCollection.plotterCfg_sigStyle],
                             ["f_final", (ROOT.RooFit.Components('f_bkgComb'), ) + plotCollection.plotterCfg_bkgStyle],
                             ],
                'marks': [],
            })
        p.setSequence([
            dataCollection.dataReader,
            pdfCollection.stdWspaceReader,
            profiler,
            plotCollection.plotter
        ])
        setupBatchTaskProfile['work_dir'] = profilePoints
        setupBatchTaskProfile['nJobs'] = len(profilePoints)
        wrappedTask = BatchTaskWrapperProfile(
            "myBatchTask",
            "{0}".format(task_dir),
            cfg=setupBatchTaskProfile)
    elif args.Function_name in ["submit", "run"]:
        p.setSequence([
            pdfCollection.stdWspaceReader,
            toyCollection.sigToyGenerator,
            toyCollection.bkgCombToyGenerator,
            profiledFCToyStudier,
        ])
        setupBatchTask['nJobs'] = len(profilePoints)
        wrappedTask = BatchTaskWrapper(
            "myBatchTask",
            "{0}".format(task_dir),
            cfg=setupBatchTask)
        if args.Function_name == "run":
            wrappedTask.task_dir = "{0}/{1}".format(task_dir, profilePoints[args.jobId])
            p.dbplayer.absInputDir = wrappedTask.task_dir
            wrappedTask.cfg['work_dir'] = ['toys_{0}'.format(datetime.utcnow().strftime("UTC-%Y%m%d-%H%M%S"))] * len(profilePoints)

            toyCollection.sigToyGenerator.cfg.update({
                'scale': profiledFCToyStudier.cfg['nSetOfToys'] * 5,
                'db': "{0}/fitResults_{{binLabel}}.db".format(wrappedTask.task_dir),
                'saveAs': "sigToyGenerator_{0}.root".format(q2bins[args.binKey]['label']),
                'preloadFiles': ["{0}/sigToyGenerator_{1}.root".format(wrappedTask.task_dir, q2bins[args.binKey]['label'])],
            })
            toyCollection.bkgCombToyGenerator.cfg.update({
                'scale': profiledFCToyStudier.cfg['nSetOfToys'] * 5,
                'db': "{0}/fitResults_{{binLabel}}.db".format(wrappedTask.task_dir),
                'saveAs': "bkgCombToyGenerator_{0}.root".format(q2bins[args.binKey]['label']),
                'preloadFiles': ["{0}/bkgCombToyGenerator_{1}.root".format(wrappedTask.task_dir, q2bins[args.binKey]['label'])],
            })

            # No run if failed in profiling
            if os.path.exists(wrappedTask.task_dir + "/failed_in_profile_{0}.txt".format(q2bins[args.binKey]['label'])):
                print("INFO\t: Failed in profile step. Abort.\n")
                sys.exit()
        else:
            print("Each submit creates {0} toys. Please do submit many times to ensure sufficient accuracy.".format(profiledFCToyStudier.cfg['nSetOfToys']))
    elif args.Function_name in ['submit_bestFit', 'run_bestFit']:
        nBestFitJobs = 20
        p.setSequence([
            pdfCollection.stdWspaceReader,
            toyCollection.sigToyGenerator,
            toyCollection.bkgCombToyGenerator,
            profiledFCToyStudier,
        ])
        wrappedTask = BatchTaskWrapperBestFit(
            "myBatchTask",
            "{0}/bestFit".format(task_dir),
            cfg=setupBatchTaskBestFit)
        if args.Function_name == "run_bestFit":
            wrappedTask.cfg['work_dir'] = ['toys_{0}'.format(datetime.utcnow().strftime("UTC-%Y%m%d-%H%M%S"))] * nBestFitJobs
            toyCollection.sigToyGenerator.cfg.update({
                'scale': profiledFCToyStudier.cfg['nSetOfToys'] * 5,
                'saveAs': "sigToyGenerator_{0}.root".format(q2bins[args.binKey]['label']),
                'preloadFiles': ["{0}/sigToyGenerator_{1}.root".format(wrappedTask.task_dir, q2bins[args.binKey]['label'])],
            })
            toyCollection.bkgCombToyGenerator.cfg.update({
                'scale': profiledFCToyStudier.cfg['nSetOfToys'] * 5,
                'saveAs': "bkgCombToyGenerator_{0}.root".format(q2bins[args.binKey]['label']),
                'preloadFiles': ["{0}/bkgCombToyGenerator_{1}.root".format(wrappedTask.task_dir, q2bins[args.binKey]['label'])],
            })
        else:
            if args.nJobs:
                print("WARNING\t: Force nJobs={0} in coverage test.".format(nBestFitJobs))
            wrappedTask.cfg['nJobs'] = nBestFitJobs
    else:
        raise ValueError("Unknown function '{0}'".format(args.Function_name))

    parser.set_defaults(
        wrapper=wrappedTask,
        process=p
    )

    args = parser.parse_args()
    args.func(args)

    sys.exit()
