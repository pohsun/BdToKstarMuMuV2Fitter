#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

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
        }
        return cfg

    def _runPath(self):
        """Generate toy without mixing"""
        if not hasattr(self, 'pdf'):
            self.pdf = self.process.sourcemanager.get(self.cfg['pdf'])
        if not hasattr(self, 'argset'):
            self.argset = self.cfg['argset']
        self.data = self.pdf.generate(self.argset, ROOT.gRandom.Poisson(self.cfg['expectedYields'] * self.cfg['scale']), *self.cfg.get('generateOpt', []))
        self.logger.logINFO("ToyGenerator {0} generates based on {1} with {2} events.".format(self.name, self.pdf.GetName(), self.data.sumEntries()))

    def _addSource(self):
        """Mixing generated toy and update source"""
        if self.cfg['mixWith'] in self.process.sourcemanager:
            self.process.sourcemanager.get(self.cfg['mixWith']).append(self.data)
        else:
            self.cfg['source'][self.cfg['mixWith']] = self.data
        super(ToyGenerator, self)._addSource()
        pass
