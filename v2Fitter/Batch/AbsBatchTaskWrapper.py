#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os
import abc
import __main__
import tempfile
from subprocess import call

import v2Fitter.Batch.batchConfig as batchConfig
from v2Fitter.FlowControl.Logger import Logger

from argparse import ArgumentParser

# NOTE:
#   Two steps to keep in mind:
#       * Job submittion (with generator), on Host (lxplus)
#       * Processing, on computing nodes.
#   The two steps should completely separated.

class AbsBatchTaskWrapper:
    """"""
    def __init__(self, name="myBatchTask", task_dir="testBatchTask", cfg=None):
        """Create process from """
        self.name = name
        self.task_dir = task_dir
        if not os.path.exists(self.task_dir):
            os.makedirs(self.task_dir)
        self.cwd = os.getcwd()
        self.cfg = cfg if cfg is not None else self.templateCfg()

        self.logger = Logger("task.log")
        self.logger.setAbsLogfileDir(os.path.abspath(self.task_dir))

    @classmethod
    def templateCfg(cls):
        cfg = {
            'nJobs': 500,
            'queue': batchConfig.BATCH_QUEUE,
        }
        return cfg

    def createSubScriptBase(self):
        """ Base of submit script to be futher decorated in makeSubScript """
        """"""
        templateSubScritpt = """
getenv      = True
log         = condor.log
output      = condor.out
error       = condor.err
+JobFlavour = {JobFlavour}

initialdir           = {initialdir}
executable           = {executable}
""".format(initialdir=self.task_dir,
            JobFlavour=self.cfg['queue'],
            executable=os.path.abspath(__main__.__file__),)
        return templateSubScritpt

    @abc.abstractmethod
    def makeSubScript(self, parser_args):
        """ To be customized by users. Start from createSubScriptBase. """
        raise NotImplementedError

    def getWrappedProcess(self, process, jobId, **kwargs):
        """ To be customized by users. """
        return process

    def runWrappedProcess(self, process, jobId, wrapper_kwargs=None):
        """ Serve as 'main' to be called on computing nodes """
        if wrapper_kwargs is None:
            wrapper_kwargs = {}
        p = self.getWrappedProcess(process, jobId, **wrapper_kwargs)
        p.work_dir = os.path.join(self.task_dir, "job{0:04d}".format(int(jobId)))
        try:
            p.beginSeq()
            p.runSeq()
        finally:
            p.endSeq()


# Followings are pre-defined procedure to reduce routine

BatchTaskParser = ArgumentParser(
    description="""
Routine to run a batch task on HTCondor.
Users must complete following step(s):
    * Set the task wrapper with
        BatchTaskParser.set_defaults(
            wrapper=YOUR_WRAPPER_INSTANCE,
            process=YOUR_PROCESS_INSTANCE
            )
Optional customization:
    * Customize and hook a submit function with BatchTaskSubparserSubmit.set_defaults(func=?)
    * Customize and hook a run function with BatchTaskSubparserRun.set_defaults(func=?)
""")

BatchTaskSubparsers = BatchTaskParser.add_subparsers(help='Functions')
BatchTaskSubparserSubmit = BatchTaskSubparsers.add_parser('submit')
BatchTaskSubparserSubmit.add_argument(
    "-q", "--queue",
    dest="queue",
    help="JobFlavour of HTCondor.")
BatchTaskSubparserSubmit.add_argument(
    "-n", "--nJobs",
    dest="nJobs",
    help="Number of jobs.")
BatchTaskSubparserSubmit.add_argument(
    "-s", "--submit",
    dest="doSubmit",
    action="store_true",
    default=False,
    help="Submit the jobs. By default only show submit script to stdout.")

def submitTask(args):
    if args.queue:
        args.wrapper.cfg['queue'] = args.queue
    if args.nJobs:
        args.wrapper.cfg['nJobs'] = args.nJobs
    subScript = args.wrapper.makeSubScript(parser_args=args)

    if args.doSubmit:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(subScript)
            tmp.flush()
            call("condor_submit {0}".format(tmp.name), shell=True)
    else:
        print(subScript)

BatchTaskSubparserSubmit.set_defaults(func=submitTask)

BatchTaskSubparserRun = BatchTaskSubparsers.add_parser('run')
BatchTaskSubparserRun.add_argument(
    dest="jobId",
    help="JobId is used to specify which work_dir to go."
)

def runJob(args):
    args.wrapper.runWrappedProcess(process=args.process, jobId=args.jobId)
    pass

BatchTaskSubparserRun.set_defaults(func=runJob)
