#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 et:

import sys

from copy import deepcopy
import v2Fitter.Batch.AbsBatchTaskWrapper as AbsBatchTaskWrapper

from SingleBuToKstarMuMuFitter.StdProcess import p
import ROOT
import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.toyCollection as toyCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection

# Define Process
fitCollection.finalFitter.cfg['data'] = "ToyGenerator.mixedToy"
plotCollection.plotter.cfg['plots']['simpleBLK']['kwargs'].update({
    'pltName': "angular3D_final",
    'dataPlots': [["ToyGenerator.mixedToy", ()], ],
    'pdfPlots': [
        ["f_final", plotCollection.plotterCfg_allStyle],
        ["f_final", (ROOT.RooFit.Components('f_sig3D'),) + plotCollection.plotterCfg_sigStyle],
        ["f_final", (ROOT.RooFit.Components('f_bkgComb'),) + plotCollection.plotterCfg_bkgStyle],
    ],
    'marks': ['toy'],
})
plotCollection.plotter.cfg['switchPlots'] = [
    'simpleBLK'
]
p.setSequence([
    pdfCollection.stdWspaceReader,
    toyCollection.sigToyGenerator,
    toyCollection.bkgCombToyGenerator,
    fitCollection.finalFitter,
    plotCollection.plotter
])

# Customize batch task

class BatchTaskWrapper(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
arguments = run $(Process)
queue {nJobs}
""".format(nJobs=self.cfg['nJobs'])
        return jdl

setupBatchTask = deepcopy(BatchTaskWrapper.templateCfg())
setupBatchTask.update({
    'nJobs': 20,
    'queue': "espresso",
})

# Customize taskSubmitter and jobRunner if needed

if __name__ == '__main__':
    wrappedTask = BatchTaskWrapper(
        "myBatchTask",
        "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/batchTask_simpleToyValidation",
        cfg=setupBatchTask)

    parser = AbsBatchTaskWrapper.BatchTaskParser
    parser.set_defaults(
        wrapper=wrappedTask,
        process=p
    )

    args = parser.parse_args()
    args.func(args)

    sys.exit()
