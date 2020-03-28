#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os
from v2Fitter.FlowControl.Path import Path
import ROOT

class ToyGenerator(Path):
    """Create toy data from RooAbsPdf and mix with another RooDataSet"""

    def __init__(self, cfg):
        """Init"""
        super(ToyGenerator, self).__init__(cfg)
        self.reset()

    def reset(self):
        super(ToyGenerator, self).reset()
        self.pdf = None
        self.argset = None
        self.data = None

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "ToyGenerator",
            'pdf': None,
            'argset': None,
            'expectedYields': 0,
            'scale': 1,
            'generateOpt': [],
            'mixWith': "ToyGenerator.mixedToy",
            'saveAs': None,
            'preloadFiles': None,  # Fetch RooDataSet from a list of root files
        }
        return cfg

    def _runPath(self):
        """Generate toy without mixing"""
        if not hasattr(self, 'pdf'):
            self.pdf = self.process.sourcemanager.get(self.cfg['pdf'])
        if not hasattr(self, 'argset'):
            self.argset = self.cfg['argset']
        if self.cfg['preloadFiles'] and any([os.path.exists(f) for f in self.cfg['preloadFiles']]):
            for f in self.cfg['preloadFiles']:
                try:
                    fin = ROOT.TFile(f)
                    data = fin.Get("{0}Data".format(self.pdf.GetName()))
                    if not data == None:
                        if self.data is None:
                            self.data = data.emptyClone("{0}Data_preload".format(self.pdf.GetName()))
                        self.data.append(data)
                finally:
                    fin.Close()
        else:
            # Remark: 
            #   1. User is responsible for the positiveness of the PDF.
            #   2. Name of the generated dataset is pdf.GetName()+"Data"
            #   3. Generation time is linear to scale and depend on the PDF, so don't use large scale
            #       TODO: Parallel production with large scale
            if (self.cfg['scale'] > 100):
                self.logger.logWARNING("It may take longer time to generate a large sample. (Scale={0})".format(self.cfg['scale']))
            self.data = self.pdf.generate(self.argset, ROOT.gRandom.Poisson(self.cfg['expectedYields'] * self.cfg['scale']), *self.cfg.get('generateOpt', []))
        self.logger.logINFO("ToyGenerator {0} generates based on {1} with {2} events.".format(self.name, self.pdf.GetName(), self.data.sumEntries()))

    def _addSource(self):
        """Mixing generated toy and update source"""
        if self.cfg['saveAs'] and (not self.cfg['preloadFiles'] or not any([os.path.exists(f) for f in self.cfg['preloadFiles']])):
            ofile = ROOT.TFile(self.cfg['saveAs'], 'RECREATE')
            self.data.Write()
            ofile.Close()

        if self.cfg['mixWith'] in self.process.sourcemanager:
            self.process.sourcemanager.get(self.cfg['mixWith']).append(self.data)
        else:
            self.cfg['source'][self.cfg['mixWith']] = self.data
        super(ToyGenerator, self)._addSource()
