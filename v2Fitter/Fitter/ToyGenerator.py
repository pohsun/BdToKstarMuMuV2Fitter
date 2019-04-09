#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

from v2Fitter.FlowControl.Path import Path

class ToyGenerator(Path):
    """Create toy data from RooAbsPdf and mix with another RooDataSet"""

    def __init__(self, cfg):
        """Init"""
        super(ToyGenerator, self).__init__(cfg)

    def reset(self):
        super(ToyGenerator, self).reset()
        self.pdf = None
        self.argset = None
        self.data = None

    @classmethod
    def templateConfig(cls):
        cfg = super(ToyGenerator, cls).templateConfig()
        cfg.update({
            'name': "ToyGenerator",
            'pdf': None,
            'argset': None,
            'generateOpt': [],
            'mixWith': "ToyGenerator.Toy",
        })
        return cfg

    def _runPath(self):
        """Generate toy without mixing"""
        self.pdf = self.process.sourcemanager.get(self.cfg['pdf'])
        self.argset = self.cfg['argset']
        self.data = self.pdf.generate(self.argset, *self.cfg.get('generateOpt', []))
        pass

    def _addSource(self):
        """Mixing generated toy and update source"""
        if self.process.sourcemanager.has_key(self.cfg['mixWith']):
            self.process.sourcemanager.get(self.cfg['mixWith']).append(self.data)
        else:
            self.cfg['source'][self.cfg['mixWith']] = self.data
        super(ToyGenerator, self)._addSource()
        pass

