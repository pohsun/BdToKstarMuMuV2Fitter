#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

import abc
from v2Fitter.FlowControl.Path import Path

class SelectorCore(Path):
    """A selecter object acts as a path, to be queued in a process.
Following functions to be overloaded to customize the full procedure...
    _preSelectSteps
    _runSelectSteps
    _postSelectSteps
"""
    def __init__(self, cfg):
        super(SelectorCore, self).__init__(cfg)
        self.reset()

    def reset(self):
        super(SelectorCore, self).reset()

    def _preSelectSteps(self):
        """Abstract: Do something before main selection step"""
        pass

    def _postSelectSteps(self):
        """Abstract: Do something after main selection step"""
        pass

    @abc.abstractmethod
    def _runSelectSteps(self):
        """Standard selecting procedure to be overwritten. 
        It's strongly recommanded to handle the tree with cpp."""
        raise NotImplementedError

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "SelectorCore",
            'itreeName': 'tree',
            'ifile': [],
            'ifriend': [],
            'ifriendIndex': ["Run", "Event"],
            'otreeName': 'tree',
            'ofilename': None,
            'oIsFriend': False,
            'ofriendIndex': ["Run", "Event"],
        }
        return cfg

    def _runPath(self):
        """Stardard fitting procedure to be overlaoded."""
        self.customize()
        self._preSelectSteps()
        self._runSelectSteps()
        self._postSelectSteps()
