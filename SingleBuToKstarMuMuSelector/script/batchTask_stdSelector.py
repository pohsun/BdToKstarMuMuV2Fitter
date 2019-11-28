#!/usr/bin/env python

import sys

import v2Fitter.Batch.AbsBatchTaskWrapper as AbsBatchTaskWrapper
import SingleBuToKstarMuMuSelector.StdSelector as StdSelector

from SingleBuToKstarMuMuSelector.StdProcess import p
from copy import copy

class BatchTaskWrapper(AbsBatchTaskWrapper.AbsBatchTaskWrapper):
    def createJdl(self, parser_args):
        jdl = self.createJdlBase()
        jdl += """
arguments = run $(Process)
queue {nJobs}
""".format(nJobs=self.cfg['nJobs'])
        return jdl

jobIdToDataset = StdSelector.datasets.keys()
setupBatchTask = copy(BatchTaskWrapper.templateCfg())
setupBatchTask.update({
    'queue': "workday", # Next level: tomorrow
    'work_dir': jobIdToDataset,
    'nJobs': len(jobIdToDataset)
})
wrappedTask = BatchTaskWrapper(
    "myBatchTask",
    "/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuSelector/batchTask_StdSelector",
    cfg=setupBatchTask)

if __name__ == '__main__':
    parser = AbsBatchTaskWrapper.BatchTaskParser
    parser.set_defaults(
        wrapper=wrappedTask,
        process=p
    )

    args = parser.parse_args()
    if args.Function_name == "run":
        selector = StdSelector.StdSelector(StdSelector.datasets[jobIdToDataset[args.jobId]])
        p.setSequence([selector])

    args.func(args)
    sys.exit()
