#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 et:

import sys

from copy import copy, deepcopy
import v2Fitter.Batch.AbsBatchTaskWrapper as AbsBatchTaskWrapper

from SingleBuToKstarMuMuFitter.anaSetup import q2bins
from SingleBuToKstarMuMuFitter.StdProcess import p
import ROOT
import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.toyCollection as toyCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection

# Define Process

# Customize batch task

class BatchTaskWrapper(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
arguments = --binKey {binKey} {func} $(Process)
queue {nJobs}
""".format(nJobs=self.cfg['nJobs'],
           binKey=parser_args.binKey,
           func=parser_args.Function_name.replace('submit', 'run'))
        return jdl

class BatchTaskWrapperSummary(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
arguments = {func} $(Process)
queue {nJobs}
""".format(nJobs=self.cfg['nJobs'],
           func=parser_args.Function_name.replace('submit', 'run'))
        return jdl

setupBatchTask = deepcopy(BatchTaskWrapper.templateCfg())
setupBatchTask.update({
    'nJobs': 20,
    'queue': "espresso",
})

# Customize taskSubmitter and jobRunner if needed

if __name__ == '__main__':
    parser = AbsBatchTaskWrapper.BatchTaskParser
    parser.add_argument(
        '--binKey',
        dest="binKey",
        default="summary",
        help="Select q2 bin with binKey"
    )

    BatchTaskSubparserSubSummary = copy(AbsBatchTaskWrapper.BatchTaskSubparserSubmit)
    AbsBatchTaskWrapper.BatchTaskSubparsers.choices['submit_summary'] = BatchTaskSubparserSubSummary

    BatchTaskSubparserRunSummary = copy(AbsBatchTaskWrapper.BatchTaskSubparserRun)
    AbsBatchTaskWrapper.BatchTaskSubparsers.choices['run_summary'] = BatchTaskSubparserRunSummary

    args = parser.parse_args()
    p.cfg['binKey'] = args.binKey

    if args.Function_name in ['run', 'submit']:
        toyCollection.sigToyGenerator.cfg.update({
            'saveAs': None,
        })
        toyCollection.bkgCombToyGenerator.cfg.update({
            'saveAs': None,
        })
        fitCollection.finalFitter.cfg['data'] = "ToyGenerator.mixedToy"
        plotCollection.plotter.cfg['plots']['simpleBLK']['kwargs'].update({
            'pltName': "angular3D_final",
            'dataPlots': [["ToyGenerator.mixedToy", plotCollection.plotterCfg_styles['dataStyle'], "Toy"]],
            'pdfPlots': [
                ["f_final", plotCollection.plotterCfg_styles['allStyle'], None, "Total fit"],
                ["f_final", (ROOT.RooFit.Components('f_sig3D'),) + plotCollection.plotterCfg_styles['sigStyle'], None, "Signal"],
                ["f_final", (ROOT.RooFit.Components('f_bkgComb'),) + plotCollection.plotterCfg_styles['bkgStyle'], None, "Background"],
            ],
            'marks': ['toy'],
        })

        plotCollection.plotter.cfg['switchPlots'] = [
            'simpleBLK',
        ]
        p.setSequence([
            pdfCollection.stdWspaceReader,
            toyCollection.sigToyGenerator,
            toyCollection.bkgCombToyGenerator,
            fitCollection.finalFitter,
            plotCollection.plotter
        ])
        wrappedTask = BatchTaskWrapper(
            "myBatchTask",
            "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/batchTask_simpleToyValidation",
            cfg=setupBatchTask)
    elif args.Function_name in ['run_summary', 'submit_summary']:
        plotCollection.plotter.cfg['plots']['angular3D_summary']['kwargs']['drawSM'] = False
        plotCollection.plotter.cfg['plots']['angular3D_summary']['kwargs']['dbSetup'] = [{
            'title': "Toy Data",
            'dbPat': "fitResults_{binLabel}.db",
            'legendOpt': "LPE"
        }]
        plotCollection.plotter.cfg['plots']['angular3D_summary']['kwargs']['marks'] = ['toy']
        plotCollection.plotter.cfg['switchPlots'] = ['angular3D_summary']
        p.setSequence([
            plotCollection.plotter
        ])
        wrappedTask = BatchTaskWrapperSummary(
            "myBatchTask",
            "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/batchTask_simpleToyValidation",
            cfg=setupBatchTask)
    else:
        raise ValueError("Unknown function name")

    parser.set_defaults(
        wrapper=wrappedTask,
        process=p
    )

    args = parser.parse_args()
    args.func(args)

    sys.exit()
