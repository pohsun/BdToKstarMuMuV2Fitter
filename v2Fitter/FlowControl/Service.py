#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 20 Feb 2019 19:12 

from __future__ import print_function

class Service:
    def __init__(self):
        self.process = None
        self.logger  = None
        pass

    def __repr__(self):
        return "<{klass} at 0x{id:x}>".format(
            klass=self.__class__.__name__,
            id=id(self) & 0xFFFFFFF
        )

    def _beginSeq(self):
        """Function to be triggered before running Paths."""
        pass

    def _endSeq(self):
        """Function to be triggered after running Paths."""
        pass
