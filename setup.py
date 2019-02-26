#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Write search path to user site-package, which will be collected to sys.path
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 23 Feb 2019 14:29 00:33

import os
import site

SITEPKG_PATH = site.USER_SITE
MODULENAMES = ["v2Fitter",]

for m in MODULENAMES:
    with open("{0}/{1}.pth".format(SITEPKG_PATH, m), "w") as f:
        f.write(os.path.dirname(os.path.abspath(__file__)))
    f.close()
